#**********IMPORTS**********
#python's tools, the web server, the shop's state, the dashboard and the journal that keeps every waiting message, ghl that logs every text a customer sends, senders and reply chains, the kept pics, and the instagram and messenger servers
import asyncio
import hashlib
import hmac
import json
import os
import random
import time

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from helpers.state.log import REDIS_CLIENT
from helpers.state import owner
from helpers.state import dashboard
from helpers.state import ghl
from helpers.state import journal
from helpers.state.state_form import message_history_form, media_urls
from helpers.response import spacing
from helpers.media import media_host
from helpers.channels import senders
from helpers.channels.senders import OWNER_NUMBER
from src.core import core
from helpers.chains import color_chains
from helpers.terminal import prints
from servers import instagram, messenger



#**********GLOBALS**********
#the web server, the blooio secret, and the memory that holds each customer's waiting messages


#LOAD ENV
load_dotenv()


#APP
#no /docs, /redoc, or /openapi.json, so nobody can pull up a map of the webhook
APP: FastAPI = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


#BLOOIO SECRET
#blooio signs every delivery with it
BLOOIO_WEBHOOK_SECRET: str | None = os.getenv("BLOOIO_WEBHOOK_SECRET")


#MESSAGE BATCHES
#each number's countdown till their batch gets answered
BATCH_COUNTDOWNS: dict[str, asyncio.Task] = {}

#the texts each number sent that wait on that countdown
MESSAGE_BATCHES: dict[str, list] = {}

#each of those texts' entries in the journal, cleared once their batch is answered
BATCH_ENTRIES: dict[str, list[str]] = {}


#CUSTOMER LOCKS
#one lock per number, so only one of their batches gets answered at a time
CUSTOMER_LOCKS: dict[str, asyncio.Lock] = {}


#OWNER PICS
#the closest material pics coming in for each M the owner sent, by its check number, the newest last
OWNER_PICS: dict[str, list[str]] = {}


#NEWS TIMERS
#what the owner found for each customer, waiting a few seconds on anything they're still sending before it goes out on its own
NEWS_TIMERS: dict[str, asyncio.Task] = {}



#**********TIMINGS**********
#how long each wait lasts and how big a webhook may be before it gets refused


#BATCH TIMES
BLOOIO_BATCH_TIME: int = 45

#a pic can land over a minute after its text, so a batch still waiting on an asked-for pic gets this much longer
BLOOIO_PIC_WAIT_TIME: int = 75


#TYPING BUBBLE
#while a batch waits the bubble goes up a few seconds at a time, a random amount so it looks like someone typing
TYPING_BURST_SECONDS: tuple[int, int] = (5, 12)

#and comes down for a moment between, like they stopped to think
TYPING_PAUSE_SECONDS: tuple[int, int] = (2, 4)


#WEBHOOK LIMITS
#a real webhook is a few kilobytes, so a bigger body is refused before it can fill the instance's memory
MAX_BODY_BYTES: int = 1024 * 1024

#blooio's own replay window, a signed delivery older than this is someone resending a captured one
BLOOIO_MAX_AGE_SECONDS: int = 300

#blooio retries a delivery for about 15 minutes and a replay resends it later, so an id is kept for 48 hours
SEEN_TTL_SECONDS: int = 172800


#PICS WAIT
#his closest material pics get this long to land after his M, a big pic can come in over a minute after its text
OWNER_PICS_WAIT_TIME: int = 120



#**********WEBHOOK SAFETY**********
#keeps out giant, forged, replayed and repeated deliveries so each real text gets answered once


#READ BODY
#nothing comes back when the body is over the size cap, the signature is checked against these exact bytes
async def read_body(request: Request) -> bytes | None:
    chunks: list[bytes] = []

    size: int = 0

    #streamed so a giant body is dropped at the cap instead of read in full first
    async for chunk in request.stream():
        size += len(chunk)

        if(size > MAX_BODY_BYTES):
            return None

        chunks.append(chunk)

    return b"".join(chunks)


#BLOOIO SIGNED
#blooio signs "<t>.<body>" with the webhook secret, sent as "t=<unix seconds>,v1=<hex>" in X-Blooio-Signature
def blooio_signed(body: bytes, signature: str, secret: str) -> bool:
    fields: dict[str, str] = {}

    for field in signature.split(","):
        pair: tuple[str, str, str] = field.strip().partition("=")

        fields[pair[0]] = pair[2]

    timestamp: str = fields.get("t", "")

    expected: str = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()

    #compare_digest so the response time does not leak how close a guess was
    if(not hmac.compare_digest(fields.get("v1", "").encode(), expected.encode())):
        return False

    #int() only ever sees a signed timestamp, and a delivery outside the window is a replay
    return abs(time.time() - int(timestamp)) <= BLOOIO_MAX_AGE_SECONDS


#FIRST SEEN
#set nx is one atomic step, so two copies of a delivery can never both get through
def first_seen(message_id: str) -> bool:
    seen: bool | None = REDIS_CLIENT.set(f"seen_blooio_{message_id}", "1", nx=True, ex=SEEN_TTL_SECONDS)

    return bool(seen)


#NEW MESSAGE
#blooio resends a delivery it thinks was missed, an id already seen was already batched
async def new_message(message_id: str | None) -> bool:
    if(not message_id):
        return True

    try:
        if(not await asyncio.to_thread(first_seen, message_id)):
            print(f"DUPLICATE WEBHOOK SKIPPED: blooio {message_id}")

            print()

            return False

    #redis down must not drop the message, it is answered without the dedupe
    except Exception as error:
        print(f"DEDUPE ERROR: {error}")

    return True



#**********PIC WAITING**********
#gives a pic the shop asked for time to land, so it goes out in the same batch as its text


#PIC PENDING
#true when the shop's last reply asked for a pic and none is in the batch yet, a list with anything in it is a pic
def pic_pending(id: str, message_batch: list) -> bool:
    for message in message_batch:
        if(isinstance(message, list) and message != []):
            return False

    return spacing.asks_for_pic(spacing.last_sent_reply(message_history_form(id)))


#PIC WAIT
#the pic the shop asked for gets time to land before the countdown starts, so it goes out in the same batch as its text
async def wait_for_pic(id: str) -> None:
    try:
        #a copy, the batch keeps growing in the event loop while the history gets read in a worker thread
        waiting: bool = await asyncio.to_thread(pic_pending, id, list(MESSAGE_BATCHES[id]))

    #redis down never holds the batch up, it just goes out on the usual countdown
    except Exception as error:
        print(f"PIC WAIT ERROR: {error}")

        return

    if(waiting):
        print(f"WAITING ON PIC: {id} gets {BLOOIO_PIC_WAIT_TIME}s more for the pic the shop asked for")

        await asyncio.sleep(BLOOIO_PIC_WAIT_TIME)



#**********TYPING**********
#shows the typing bubble while a batch waits, so the shop looks like a person writing back


#NATURAL TYPING
#the batch waits out its time with the bubble going up and down, so it looks like someone typing and stopping
async def natural_typing(id: str) -> None:
    end: float = time.monotonic() + BLOOIO_BATCH_TIME

    while(time.monotonic() < end):
        await asyncio.to_thread(senders.start_blooio_typing, id)

        typing_seconds: float = random.uniform(TYPING_BURST_SECONDS[0], TYPING_BURST_SECONDS[1])

        #a burst or pause that runs past the end is cut short, so the batch still closes on time
        await asyncio.sleep(min(typing_seconds, end - time.monotonic()))

        await asyncio.to_thread(senders.stop_blooio_typing, id)

        pause_seconds: float = random.uniform(TYPING_PAUSE_SECONDS[0], TYPING_PAUSE_SECONDS[1])

        await asyncio.sleep(min(pause_seconds, end - time.monotonic()))



#**********CUSTOMER LOCKS**********
#makes a customer's batches and the owner's news for them take turns, so only one gets answered at a time


#CUSTOMER LOCK
#their lock, made the first time they need one
def customer_lock(id: str) -> asyncio.Lock:
    if(id not in CUSTOMER_LOCKS):
        CUSTOMER_LOCKS[id] = asyncio.Lock()

    return CUSTOMER_LOCKS[id]


#INCOMING BATCH
#a batch of theirs still counting down gets answered first, and a restarted countdown keeps the wait on the new one
async def incoming_batch_answered(id: str) -> None:
    while(id in BATCH_COUNTDOWNS):
        await asyncio.wait([BATCH_COUNTDOWNS[id]])



#**********COLOR NEWS**********
#sends what the owner found on its own when no reply to a text of theirs carries it


#STOP TIMER
#their news wait is called off, if one is running
def stop_news_timer(id: str) -> None:
    timer: asyncio.Task | None = NEWS_TIMERS.pop(id, None)

    if(timer is not None):
        timer.cancel()


#NEWS WAIT
#a few seconds for a text they're still sending to land, then any batch of theirs goes first so its reply carries it
async def news_wait(id: str) -> None:
    await asyncio.sleep(owner.NEWS_WAIT_SECONDS)

    #done waiting, so nothing cancels it from here, a newer answer from the owner gets its own wait
    if(NEWS_TIMERS.get(id) is asyncio.current_task()):
        del NEWS_TIMERS[id]

    while(True):
        #a batch of theirs counting down or being answered carries it with its reply
        await incoming_batch_answered(id)

        async with customer_lock(id):
            #a text that came in while this waited on their lock starts a batch that carries it too
            if(id in BATCH_COUNTDOWNS):
                continue

            #a reply that carried it leaves nothing to send
            if(await asyncio.to_thread(owner.news_due, id)):
                with prints.held():
                    print(f"COLOR NEWS: nothing from {id} is being answered, so what the owner found goes out on its own")

                    print()

                    await asyncio.to_thread(color_chains.send_color_news, id)

            return


#START TIMER
#a newer answer from the owner restarts their news wait
def start_news_timer(id: str) -> None:
    stop_news_timer(id)

    NEWS_TIMERS[id] = asyncio.create_task(news_wait(id))



#**********OWNER ANSWERS**********
#picks up the owner's answer on a color check and his material pics and hands them over, anything else from his number goes nowhere


#OWNER ANSWER
#his pics get read once before any customer waits on them, then a reply of theirs being written holds off till his answer is on file
async def owner_answer(answer: tuple, pics: list[str]) -> None:
    customer: str = ""

    #an N was his no before there was an M, so it never answers a check
    if(answer[0] == "answer" and answer[1] != owner.NO_ANSWER):
        customer = await asyncio.to_thread(owner.color_check_customer, answer[2])

    with prints.held():
        print(f"OWNER COLOR CHECK ANSWER: {answer} with {len(pics)} pics")

        print()

        if(customer == ""):
            await asyncio.to_thread(color_chains.color_check_unmatched, answer)

            return

        #reading his material pics is the slow part, so their batches keep getting answered while it runs
        materials: list[dict[str, str]] | None = await asyncio.to_thread(color_chains.prepared_materials, customer, answer[1], answer[2], pics)

        if(materials is None):
            return

        channel: str = await asyncio.to_thread(owner.color_check_channel, customer)

        #an instagram or messenger customer's batches, lock and news wait are on that channel's server, so what he found goes there
        if(channel == "ig"):
            await instagram.owner_answer(customer, answer, materials)

            return

        if(channel == "messenger"):
            await messenger.owner_answer(customer, answer, materials)

            return

        #the reply core is writing for them right now, if there is one, gets held so their batch is answered again with it
        owner.hold_for_news(customer)

        #a reply of theirs being written or already going out when he answered means what he found waits for the next reply to them
        replying: bool = customer_lock(customer).locked()

        news_due: bool = False

        try:
            async with customer_lock(customer):
                #a batch answered in the meantime can send a different exact color, which takes this check off
                if(await asyncio.to_thread(owner.color_check_customer, answer[2]) != customer):
                    await asyncio.to_thread(color_chains.color_check_unmatched, answer)

                    return

                news_due = await asyncio.to_thread(color_chains.color_check_answered, customer, answer[1], answer[2], materials, replying)

        finally:
            owner.news_landed(customer)

        #nothing of theirs was being answered, so the reply to what they're sending carries it, or it goes out on its own once they go quiet
        if(news_due and not replying):
            start_news_timer(customer)


#PICS ADDED
#anything the owner sends while an M waits on its pics belongs to the newest one, true when one was open
def material_pics_added(pics: list[str]) -> bool:
    if(len(OWNER_PICS) == 0):
        return False

    newest_code: str = list(OWNER_PICS)[-1]

    OWNER_PICS[newest_code].extend(pics)

    return True


#PICS ANSWER
#once his pics had their time to land, the M goes out with every one that came in
async def material_pics_answer(answer: tuple) -> None:
    await asyncio.sleep(OWNER_PICS_WAIT_TIME)

    pics: list[str] = OWNER_PICS.pop(answer[2], [])

    await owner_answer(answer, pics)


#COLLECT PICS
#his M waits for every closest material pic he sends till time is up, a repeat M on an open check only adds its pics
def collect_material_pics(answer: tuple, pics: list[str]) -> None:
    code: str = answer[2]

    if(code in OWNER_PICS):
        OWNER_PICS[code].extend(pics)

        return

    OWNER_PICS[code] = list(pics)

    asyncio.create_task(material_pics_answer(answer))


#OWNER CHECK
#true for every text from the owner's number, which only ever answers color checks: his Y or M and the pics for his M get handled, anything else is dropped, so he's never batched or answered like a customer
async def owner_checked(id: str, text: str | None, attachments: list | None) -> bool:
    if(id != OWNER_NUMBER):
        return False

    if(not attachments):
        attachments = []

    pics: list[str] = media_urls([attachments])

    answer: tuple | None = None

    if(text):
        answer = await asyncio.to_thread(owner.color_check_answer, text)

    if(answer is None):
        #anything he sends while an M waits on its pics belongs to it, the rest answers no color check, so it goes nowhere
        if(not material_pics_added(pics)):
            print(f"OWNER TEXT DROPPED: {text!r} with {len(pics)} pics answers no color check, the owner's number only answers color checks")

            print()

        return True

    #an M waits on its pics first, the ones with it and the ones he sends right after it
    if(answer[0] == "answer" and answer[1] == owner.MATERIALS_ANSWER):
        collect_material_pics(answer, pics)

        return True

    asyncio.create_task(owner_answer(answer, []))

    return True



#**********MESSAGE BATCHING**********
#holds their texts until they stop sending, shows the typing bubble, then answers them all at once


#BATCH
#waits on an asked-for pic and the typing, then answers the whole batch, again if its reply was held for the owner's answer
async def batch(id: str) -> None:
    #everything this batch prints, its countdown included, comes out in one block once its reply went out or it failed
    with prints.held():
        await wait_for_pic(id)

        await natural_typing(id)

        current_message_batch: list = MESSAGE_BATCHES[id]

        current_entries: list[str] = BATCH_ENTRIES[id]

        #nothing waits from here to their lock, so what the owner found never goes out on its own in between
        del BATCH_COUNTDOWNS[id]

        del MESSAGE_BATCHES[id]

        del BATCH_ENTRIES[id]

        print(f"INCOMING MESSAGE BATCH FROM on blooio from: {id}")

        print(f"Message batch: {current_message_batch}")

        print()

        answered: bool = False

        #a reply held for the owner's answer landing gets written again once his answer is on file, so it carries what he found
        while(not answered):
            #a batch closing while their last one is still being answered waits, so it sees that reply in the history
            async with customer_lock(id):
                #core runs in its own worker thread, so the server keeps taking webhooks while it works
                answered = await asyncio.to_thread(core, current_message_batch, id, "blooio")

        #answered, so its texts come off the journal and a restart never answers them again
        await asyncio.to_thread(journal.clear, "blooio", id, current_entries)


#QUEUE MESSAGE
#every new message restarts the id's countdown, so the whole batch goes out once they stop sending, journal_entry is where the message is on file
def queue_message(id: str, message: list, journal_entry: str) -> None:
    if(id not in BATCH_COUNTDOWNS):
        MESSAGE_BATCHES[id] = message

        BATCH_ENTRIES[id] = [journal_entry]

        BATCH_COUNTDOWNS[id] = asyncio.create_task(batch(id))

    else:
        MESSAGE_BATCHES[id].extend(message)

        BATCH_ENTRIES[id].append(journal_entry)

        BATCH_COUNTDOWNS[id].cancel()

        BATCH_COUNTDOWNS[id] = asyncio.create_task(batch(id))



#**********BLOOIO WEBHOOK**********
#serves the owner's pics to blooio, and takes every text blooio delivers, checks it's real, and sends it to the owner or the batch


#HOSTED PIC
#the customer's pics the owner's texts carry are served from here, since blooio never gets them from instagram's links
#blooio fetches each one from its link here, a name never handed out or a day old is not found
@APP.get(f"{media_host.MEDIA_PATH}/{{file_name}}")
async def hosted_pic(file_name: str) -> Response:
    media: tuple[bytes, str] | None = await asyncio.to_thread(media_host.hosted_media, file_name)

    if(media is None):
        return Response(status_code=404)

    return Response(content=media[0], media_type=media[1])


#BLOOIO HOOK
#every text blooio delivers comes in here as a signed POST
#it answers with a dict or a JSONResponse, so fastapi makes no response model from the annotation
@APP.post("/blooio/webhook", response_model=None)
async def blooio_hook(request: Request) -> dict | JSONResponse:
    if(not BLOOIO_WEBHOOK_SECRET):
        print("BLOOIO WEBHOOK ERROR: BLOOIO_WEBHOOK_SECRET is not set, delivery refused")

        return JSONResponse({"error": "blooio webhook is not configured"}, status_code=503)

    body: bytes | None = await read_body(request)

    if(body is None):
        print("BLOOIO WEBHOOK REJECTED: body is over the size cap")

        return JSONResponse({"error": "body too large"}, status_code=413)

    #blooio signs every delivery, so a forged message never reaches the batch
    if(not blooio_signed(body, request.headers.get("X-Blooio-Signature", ""), BLOOIO_WEBHOOK_SECRET)):
        print("BLOOIO WEBHOOK REJECTED: signature is wrong or expired")

        return JSONResponse({"error": "unauthorized"}, status_code=401)

    data: dict = json.loads(body)

    if(data.get("type") == "message.received"):
        id: str = data.get("data").get("sender")

        text: str = data.get("data").get("text")

        attachments: list = data.get("data").get("attachments")

        #message_id is the same on every retry and replay, the envelope id is blooio's own dedupe key
        message_id: str | None = data.get("data").get("message_id")

        if(not message_id):
            message_id = data.get("id")

        #a message is its text and its attachments
        if(await new_message(message_id)):
            #the owner's number only ever answers color checks, so nothing from it goes in the batch, every customer's text does
            if(not await owner_checked(id, text, attachments)):
                #ghl never sees blooio, so every text a customer sends goes in their conversation there, switched on in the dashboard or not
                ghl.log_received(id, text, attachments)

                #every message shows in the dashboard, and only one from a customer switched on there gets batched
                if(await asyncio.to_thread(dashboard.take_in, id, "blooio", [text, attachments])):
                    #on file before it waits in the batch, so a restart while it waits never loses it
                    journal_entry: str = await asyncio.to_thread(journal.save, "blooio", id, [text, attachments])

                    queue_message(id, [text, attachments], journal_entry)

    elif(data.get("type") == "message.failed"):
        failed: dict = data.get("data")

        print(f"BLOOIO SEND FAILED to {failed.get('recipient')} over {failed.get('protocol')}: {failed.get('error')}")

        print(f"Failed text: {failed.get('text')}")

        print()

    return {"status": "ok"}



#**********RUN**********
#starts this webhook server on its own when the file is run directly


#RUN SERVER
#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
