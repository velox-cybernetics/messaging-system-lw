#IMPORTS

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
from src.reply_checks import booking_silent
from src import followup
from src import spam
from helpers.chains import color_chains
from helpers.terminal import prints
from servers import instagram, messenger


#GLOBALS

load_dotenv()

#no docs, redoc or openapi pages, nobody gets a free map of the webhook
APP = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#blooio signs every delivery with it
BLOOIO_WEBHOOK_SECRET: str | None = os.getenv("BLOOIO_WEBHOOK_SECRET")

#each numbers countdown till there batch gets answered
BATCH_COUNTDOWNS: dict = {}

#the texts each number sent that wait on that countdown
MESSAGE_BATCHES: dict[str, list] = {}

#where each of those texts sits in the journal, cleared once there batch is answered
BATCH_ENTRIES: dict[str, list[str]] = {}

#one lock per number, so only one of their batches gets answered at a time
CUSTOMER_LOCKS: dict = {}

#closest material pics landing for each of his Ms, by check number, the newest M last
OWNER_PICS: dict[str, list[str]] = {}

#each customers few second wait before the owners news goes out on its own
NEWS_TIMERS: dict = {}


#TIMINGS

BLOOIO_BATCH_TIME: int = 45

#a pic can land over a minute after its text, so a batch waiting on one gets this much longer
BLOOIO_PIC_WAIT_TIME: int = 75

#the bubble goes up for a random few seconds at a time, so it looks like someone typing
TYPING_BURST_SECONDS: tuple[int, int] = (5, 12)

#and comes down for a moment between, like they stopped to think
TYPING_PAUSE_SECONDS: tuple[int, int] = (2, 4)

#a real webhook is a few kilobytes, so a bigger body is refused before it can eat the memory
MAX_BODY_BYTES: int = 1024 * 1024

#blooios replay window, a signed delivery older than this is a captured one sent again
BLOOIO_MAX_AGE_SECONDS: int = 300

#blooio retries for about 15 minutes and a replay comes later, so an id is kept 48 hours
SEEN_TTL_SECONDS: int = 172800

#his closest material pics get this long to land after his M, big pics take their sweet time
OWNER_PICS_WAIT_TIME: int = 120


#WEBHOOK SAFETY

#the raw body for the signature check, None once its over the size cap
async def read_body(request) -> bytes | None:
    chunks: list[bytes] = []

    size: int = 0

    #streamed so a giant body is dropped at the cap instead of read in full first
    async for chunk in request.stream():
        size += len(chunk)

        if(size > MAX_BODY_BYTES):
            return None

        chunks.append(chunk)

    return b"".join(chunks)

#blooio signs the timestamp, a dot and the body, its header hands over t and the v1 hex
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

    #int only ever sees a signed timestamp, and anything outside the window is a replay
    return abs(time.time() - int(timestamp)) <= BLOOIO_MAX_AGE_SECONDS

#set nx is one atomic step, so two copies of a delivery can never both get through
def first_seen(message_id: str) -> bool:
    seen: bool | None = REDIS_CLIENT.set(f"seen_blooio_{message_id}", "1", nx=True, ex=SEEN_TTL_SECONDS)

    return bool(seen)

#blooio resends a delivery it thinks was missed, an id already seen was already batched
async def new_message(message_id: str | None) -> bool:
    if(not message_id):
        return True

    try:
        if(not await asyncio.to_thread(first_seen, message_id)):
            print(f"DUPLICATE WEBHOOK SKIPPED: blooio {message_id}")

            print()

            return False
    except Exception as error:
        #redis down must not drop the message, it is answered without the dedupe
        print(f"DEDUPE ERROR: {error}")

    return True


#PIC WAITING

#true when the shops last reply asked for a pic and the batch still has none
def pic_pending(id: str, message_batch: list) -> bool:
    #a list with anything in it is a pic
    for message in message_batch:
        if(isinstance(message, list) and message != []):
            return False

    return spacing.asks_for_pic(spacing.last_sent_reply(message_history_form(id)))

#the pic the shop asked for gets time to land first, so it joins the batch with its text
async def wait_for_pic(id: str) -> None:
    try:
        #a copy, since the batch keeps growing while a worker thread reads the history
        waiting: bool = await asyncio.to_thread(pic_pending, id, list(MESSAGE_BATCHES[id]))
    except Exception as error:
        #redis down never holds the batch up, it just goes out on the usual countdown
        print(f"PIC WAIT ERROR: {error}")

        return

    if(waiting):
        print(f"WAITING ON PIC: {id} gets {BLOOIO_PIC_WAIT_TIME}s more for the pic the shop asked for")

        await asyncio.sleep(BLOOIO_PIC_WAIT_TIME)


#TYPING

#the batch waits out its time with the bubble going up and down, like someone typing for real
async def natural_typing(id: str) -> None:
    end: float = time.monotonic() + BLOOIO_BATCH_TIME

    #a person fitting them in keeps the system silent, so the wait goes by with no bubble at all
    silent: bool = await asyncio.to_thread(booking_silent, id)

    #an sms has no bubble either, one would only pop up over on hazels line
    if(not silent):
        silent = await asyncio.to_thread(senders.on_sms_line, id)

    if(silent):
        await asyncio.sleep(max(0.0, end - time.monotonic()))

        return

    while(time.monotonic() < end):
        await asyncio.to_thread(senders.start_blooio_typing, id)

        typing_seconds: float = random.uniform(TYPING_BURST_SECONDS[0], TYPING_BURST_SECONDS[1])

        #a burst or pause that runs past the end is cut short, so the batch still closes on time
        await asyncio.sleep(min(typing_seconds, end - time.monotonic()))

        await asyncio.to_thread(senders.stop_blooio_typing, id)

        pause_seconds: float = random.uniform(TYPING_PAUSE_SECONDS[0], TYPING_PAUSE_SECONDS[1])

        await asyncio.sleep(min(pause_seconds, end - time.monotonic()))


#CUSTOMER LOCKS

#their lock, made the first time they need one
def customer_lock(id: str):
    if(id not in CUSTOMER_LOCKS):
        CUSTOMER_LOCKS[id] = asyncio.Lock()

    return CUSTOMER_LOCKS[id]

#any batch of theirs still counting down gets answered first, a restarted one included
async def incoming_batch_answered(id: str) -> None:
    while(id in BATCH_COUNTDOWNS):
        await asyncio.wait([BATCH_COUNTDOWNS[id]])


#COLOR NEWS

#their news wait is called off, if one is running
def stop_news_timer(id: str) -> None:
    timer = NEWS_TIMERS.pop(id, None)

    if(timer is not None):
        timer.cancel()

#a few seconds for a text they're still sending, then any batch of theirs gets to carry it
async def news_wait(id: str) -> None:
    await asyncio.sleep(owner.NEWS_WAIT_SECONDS)

    #done waiting, so nothing cancels it from here, a newer owner answer gets its own wait
    if(NEWS_TIMERS.get(id) is asyncio.current_task()):
        del NEWS_TIMERS[id]

    while(True):
        #a batch of theirs counting down or being answered carries it with its reply
        await incoming_batch_answered(id)

        async with customer_lock(id):
            #anything they sent while this waited on the lock starts a batch, which carries it
            if(id in BATCH_COUNTDOWNS):
                continue

            #a reply that carried it leaves nothing to send
            if(await asyncio.to_thread(owner.news_due, id)):
                held_token = prints.hold()

                try:
                    print(f"COLOR NEWS: nothing from {id} is being answered, so what the owner found goes out on its own")

                    print()

                    await asyncio.to_thread(color_chains.send_color_news, id)
                finally:
                    prints.release(held_token)

            return

#a newer answer from the owner restarts their news wait
def start_news_timer(id: str) -> None:
    stop_news_timer(id)

    NEWS_TIMERS[id] = asyncio.create_task(news_wait(id))


#OWNER ANSWERS

#his pics get read before any customer waits on them, then there reply holds for his answer
async def owner_answer(answer: tuple, pics: list[str]) -> None:
    customer: str = ""

    #an N was his no before there was an M, so it never answers a check
    if(answer[0] == "answer" and answer[1] != owner.NO_ANSWER):
        customer = await asyncio.to_thread(owner.color_check_customer, answer[2])

    held_token = prints.hold()

    try:
        print(f"OWNER COLOR CHECK ANSWER: {answer} with {len(pics)} pics")

        print()

        if(customer == ""):
            await asyncio.to_thread(color_chains.color_check_unmatched, answer)

            return

        #reading his pics is the slow part, so their batches keep getting answered meanwhile
        materials: list[dict[str, str]] | None = await asyncio.to_thread(color_chains.prepared_materials, customer, answer[1], answer[2], pics)

        if(materials is None):
            return

        channel: str = await asyncio.to_thread(owner.color_check_channel, customer)

        #an instagram or messenger customer lives on that server, so his answer goes there
        if(channel == "ig"):
            await instagram.owner_answer(customer, answer, materials)

            return

        if(channel == "messenger"):
            await messenger.owner_answer(customer, answer, materials)

            return

        #a reply core is writing for them right now gets held and redone with his answer
        owner.hold_for_news(customer)

        #a reply already underway when he answered means the news waits for their next reply
        replying: bool = customer_lock(customer).locked()

        news_due: bool = False

        try:
            async with customer_lock(customer):
                #a batch answered meanwhile can bring a new exact color and take this check off
                if(await asyncio.to_thread(owner.color_check_customer, answer[2]) != customer):
                    await asyncio.to_thread(color_chains.color_check_unmatched, answer)

                    return

                news_due = await asyncio.to_thread(color_chains.color_check_answered, customer, answer[1], answer[2], materials, replying)
        finally:
            owner.news_landed(customer)

        #nothing was underway, so it rides their next reply or goes out alone once they go quiet
        if(news_due and not replying):
            start_news_timer(customer)
    finally:
        prints.release(held_token)

#pics he sends while an M waits go to the newest one, true when one was open
def material_pics_added(pics: list[str]) -> bool:
    if(len(OWNER_PICS) == 0):
        return False

    newest_code: str = list(OWNER_PICS)[-1]

    OWNER_PICS[newest_code].extend(pics)

    return True

#once his pics had their time to land, the M goes out with every one that came in
async def material_pics_answer(answer: tuple) -> None:
    await asyncio.sleep(OWNER_PICS_WAIT_TIME)

    pics: list[str] = OWNER_PICS.pop(answer[2], [])

    await owner_answer(answer, pics)

#his M waits for its pics till times up, a repeat M on an open check just adds its pics
def collect_material_pics(answer: tuple, pics: list[str]) -> None:
    code: str = answer[2]

    if(code in OWNER_PICS):
        OWNER_PICS[code].extend(pics)

        return

    OWNER_PICS[code] = list(pics)

    asyncio.create_task(material_pics_answer(answer))

#true for anything from the owners number, hes never batched or answered like a customer
async def owner_checked(id: str, text: str | None, attachments: list | None) -> bool:
    if(id != OWNER_NUMBER):
        return False

    #anything he sends opens his thread back up on blooios end, answer or not
    await asyncio.to_thread(owner.line_answered)

    if(not attachments):
        attachments = []

    pics: list[str] = media_urls([attachments])

    answer: tuple | None = None

    if(text):
        answer = await asyncio.to_thread(owner.color_check_answer, text)

    if(answer is None):
        #an open M takes whatever he sends, otherwise it answers no check and goes nowhere
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


#MESSAGE BATCHING

#they texted again after their batch was taken, so its reply gets tossed for the next batch
def sent_since(id: str) -> bool:
    return id in MESSAGE_BATCHES

#a tossed batch goes in front of their newer texts, False when nothing of theirs is waiting
def fold_batch(id: str, current_message_batch: list, current_entries: list[str]) -> bool:
    if(id not in MESSAGE_BATCHES):
        return False

    MESSAGE_BATCHES[id][:0] = current_message_batch

    BATCH_ENTRIES[id][:0] = current_entries

    print(f"BATCH FOLDED: {id} texted again while their reply was being written, so their next batch answers it all at once")

    print()

    return True

#answers the whole batch once they stop, late texts join right up until it gets their lock
async def batch(id: str) -> None:
    #everything it prints comes out as one block at the end, sent or failed
    held_token = prints.hold()

    try:
        await wait_for_pic(id)

        await natural_typing(id)

        current_message_batch: list = []

        current_entries: list[str] = []

        taken: bool = False

        answered: bool = False

        #a reply held for the owners answer gets written again once its on file
        while(not answered):
            #their last batch finishes first, so this one sees that reply in the history
            async with customer_lock(id):
                #no waiting from here to core, so the owners news can't sneak out in between
                if(not taken):
                    current_message_batch = MESSAGE_BATCHES.pop(id)

                    current_entries = BATCH_ENTRIES.pop(id)

                    del BATCH_COUNTDOWNS[id]

                    taken = True

                    print(f"INCOMING MESSAGE BATCH FROM on blooio from: {id}")

                    print(f"Message batch: {current_message_batch}")

                    print()

                answered = await asyncio.to_thread(core, current_message_batch, id, "blooio", sent_since)

                #they texted mid reply, so their newer batch answers this one too
                if(not answered and fold_batch(id, current_message_batch, current_entries)):
                    return

        #answered, so its texts come off the journal and a restart never answers them again
        await asyncio.to_thread(journal.clear, "blooio", id, current_entries)
    finally:
        prints.release(held_token)

#every new message restarts there countdown, so the batch only goes out once they stop
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


#TAKING IN

#one text at a time through the spam check, sms_line is one they sent the shops own sms number
async def take_message(id: str, text: str | None, attachments: list | None, sms_line: bool = False) -> None:
    async with spam.intake_lock(id):
        #spam stops here, so it never shows in ghl or the dashboard and never gets a reply
        if(await asyncio.to_thread(spam.is_spam, id, text, "blooio")):
            return

        #an sms is already in ghl, a text on hazels line isn't and it moves them back onto her line
        if(not sms_line):
            await asyncio.to_thread(senders.close_sms_line, id)

            #ghl never sees blooio, so every text goes in there ghl convo, switched on or not
            ghl.log_received(id, text, attachments)

        #the dashboard shows it unless the owner had them first, only switched on ones get batched
        if(await asyncio.to_thread(dashboard.take_in, id, "blooio", [text, attachments])):
            #on file before it waits in the batch, so a restart while it waits never loses it
            journal_entry: str = await asyncio.to_thread(journal.save, "blooio", id, [text, attachments])

            queue_message(id, [text, attachments], journal_entry)


#BLOOIO WEBHOOK

#serves the customer pics in the owners texts, blooio can't pull them from instagrams links
async def hosted_pic(file_name: str):
    media: tuple[bytes, str] | None = await asyncio.to_thread(media_host.hosted_media, file_name)

    #a name never handed out or a day old is a 404
    if(media is None):
        return Response(status_code=404)

    return Response(content=media[0], media_type=media[1])

#every text and tapback blooio delivers comes in here as a signed POST
async def blooio_hook(request: Request):
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

        #message_id survives every retry and replay, the envelope id is blooios own dedupe key
        message_id: str | None = data.get("data").get("message_id")

        if(not message_id):
            message_id = data.get("id")

        if(await new_message(message_id)):
            #the owners number only answers color checks, everyone else gets taken in
            if(not await owner_checked(id, text, attachments)):
                await take_message(id, text, attachments)
    elif(data.get("type") == "message.reaction"):
        reaction: dict | None = data.get("data")

        if(not reaction):
            reaction = {}

        sender: str | None = reaction.get("sender")

        if(not sender):
            sender = ""

        #a tapback they put on in there own chat lifts the hold on their follow ups
        if(sender != "" and reaction.get("direction") == "inbound" and reaction.get("action", "add") == "add" and not reaction.get("is_group")):
            #his tapback opens his thread back up just like a text from him, and he has no follow ups
            if(sender == OWNER_NUMBER):
                await asyncio.to_thread(owner.line_answered)
            else:
                await asyncio.to_thread(followup.note_reaction, sender)
    elif(data.get("type") == "message.failed"):
        failed: dict = data.get("data")

        print(f"BLOOIO SEND FAILED to {failed.get('recipient')} over {failed.get('protocol')}: {failed.get('error')}")

        print(f"Failed text: {failed.get('text')}")

        print()

    return {"status": "ok"}


#ROUTES

APP.add_api_route(f"{media_host.MEDIA_PATH}/{{file_name}}", hosted_pic, methods=["GET"])

#it hands back a dict or a JSONResponse, so no response model
APP.add_api_route("/blooio/webhook", blooio_hook, methods=["POST"], response_model=None)


#RUN

#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
