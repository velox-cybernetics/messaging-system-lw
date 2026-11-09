#IMPORTS

import asyncio
import hashlib
import hmac
import json
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from helpers.state.log import REDIS_CLIENT
from helpers.state import owner
from helpers.state import dashboard
from helpers.state import journal
from helpers.state.state_form import message_history_form
from helpers.response import spacing
from src.core import core
from src import spam
from helpers.chains import color_chains
from helpers.channels import username
from helpers.terminal import prints


#GLOBALS

load_dotenv()

#no docs, redoc or openapi pages, nobody gets a free map of the webhook
APP = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#the verify token typed into the meta app dashboard when the webhook is subscribed
MESSENGER_VERIFY_TOKEN: str = os.environ["MESSENGER_VERIFY_TOKEN"]

#the app secret from basic app settings, getenv so missing it only refuses events
MESSENGER_APP_SECRET: str | None = os.getenv("MESSENGER_APP_SECRET")

#each ids countdown till their batch gets answered
BATCH_COUNTDOWNS: dict = {}

#the messages each id sent that wait on that countdown
MESSAGE_BATCHES: dict[str, list] = {}

#where each of those messages sits in the journal, cleared once there batch is answered
BATCH_ENTRIES: dict[str, list[str]] = {}

#one lock per id, so only one of their batches gets answered at a time
CUSTOMER_LOCKS: dict = {}

#each customers few second wait before the owners news goes out on its own
NEWS_TIMERS: dict = {}


#TIMINGS

MESSENGER_BATCH_TIME: int = 20

#they can take a while to dig up the pic, so a batch waiting on one gets this much longer
MESSENGER_PIC_WAIT_TIME: int = 75

#a real webhook is a few kilobytes, so a bigger body is refused before it can eat the memory
MAX_BODY_BYTES: int = 1024 * 1024

#meta retries a delivery it thinks failed for up to 36 hours, so an id is kept for 48 hours
SEEN_TTL_SECONDS: int = 172800


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

#meta signs the body with the app secret, its header carries the sha256 hex
def meta_signed(body: bytes, signature: str, secret: str) -> bool:
    expected: str = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    #compare_digest so the response time does not leak how close a guess was
    return hmac.compare_digest(signature.encode(), f"sha256={expected}".encode())

#set nx is one atomic step, so two copies of a delivery can never both get through
def first_seen(message_id: str) -> bool:
    seen: bool | None = REDIS_CLIENT.set(f"seen_messenger_{message_id}", "1", nx=True, ex=SEEN_TTL_SECONDS)

    return bool(seen)

#meta resends a delivery it thinks was missed, an id already seen was already batched
async def new_message(message_id: str | None) -> bool:
    if(not message_id):
        return True

    try:
        if(not await asyncio.to_thread(first_seen, message_id)):
            print(f"DUPLICATE WEBHOOK SKIPPED: messenger {message_id}")

            print()

            return False
    except Exception as error:
        #redis down must not drop the message, it is answered without the dedupe
        print(f"DEDUPE ERROR: {error}")

    return True


#MESSENGER EVENTS

#text, attachments and referral out of one event, None when theres nothing to answer
def event_message(event: dict) -> list | None:
    message: dict | None = event.get("message")

    if(not message):
        message = {}

    postback: dict | None = event.get("postback")

    if(not postback):
        postback = {}

    #echoes are the pages own sends, from this system or the owner replying in the inbox
    if(message.get("is_echo")):
        return None

    text: str | None = message.get("text")

    #a postback is a get started, icebreaker or menu tap, its title is what they tapped
    if(not text):
        text = postback.get("title")

    if(not text):
        text = None

    attachments: list = []

    all_attachments: list | None = message.get("attachments")

    if(not all_attachments):
        all_attachments = []

    #stickers like the thumbs up have nothing to describe or answer
    for attachment in all_attachments:
        if(attachment.get("type") != "sticker"):
            attachments.append(attachment)

    #an ad click comes in the message, on its own for an old thread, or with a get started tap
    referral: dict | None = message.get("referral")

    if(not referral):
        referral = event.get("referral")

    if(not referral):
        referral = postback.get("referral")

    if(not referral):
        referral = {}

    #only an ad referral carries context, m dot me links and shop products don't
    if(referral.get("source") != "ADS"):
        referral = {}

    if(not text and not attachments and not referral):
        return None

    return [text, attachments, referral]

#the id meta resends the event with, a lone ad click has no mid so sender and time stand in
def event_message_id(event: dict, id: str) -> str:
    message: dict | None = event.get("message")

    if(not message):
        message = {}

    postback: dict | None = event.get("postback")

    if(not postback):
        postback = {}

    message_id: str | None = message.get("mid")

    if(not message_id):
        message_id = postback.get("mid")

    if(not message_id):
        message_id = f"{id}_{event.get('timestamp')}"

    return message_id


#PIC WAITING

#true when the shops last reply asked for a pic and the batch still has none
def pic_pending(id: str, message_batch: list) -> bool:
    #a list with anything in it is a pic or a shared post
    for message in message_batch:
        if(isinstance(message, list) and message != []):
            return False

    return spacing.asks_for_pic(spacing.last_sent_reply(message_history_form(id)))

#the pic the shop asked for gets time to land first, so it joins the batch with its message
async def wait_for_pic(id: str) -> None:
    try:
        #a copy, since the batch keeps growing while a worker thread reads the history
        waiting: bool = await asyncio.to_thread(pic_pending, id, list(MESSAGE_BATCHES[id]))
    except Exception as error:
        #redis down never holds the batch up, it just goes out on the usual countdown
        print(f"PIC WAIT ERROR: {error}")

        return

    if(waiting):
        user_name: str = await asyncio.to_thread(username.username, id, "messenger")

        print(f"WAITING ON PIC: {user_name} gets {MESSENGER_PIC_WAIT_TIME}s more for the pic the shop asked for")

        await asyncio.sleep(MESSENGER_PIC_WAIT_TIME)


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

#there news wait is called off, if one is running
def stop_news_timer(id: str) -> None:
    timer = NEWS_TIMERS.pop(id, None)

    if(timer is not None):
        timer.cancel()

#a few seconds for a message they're still sending, then any batch of theirs gets to carry it
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
                    user_name: str = await asyncio.to_thread(username.username, id, "messenger")

                    print(f"COLOR NEWS: nothing from {user_name} is being answered, so what the owner found goes out on its own")

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

#his answer for a messenger customer, handed over by blooio since his texts land there
async def owner_answer(customer: str, answer: tuple, materials: list[dict[str, str]]) -> None:
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


#MESSAGE BATCHING

#they messaged again after there batch was taken, so its reply gets tossed for the next batch
def sent_since(id: str) -> bool:
    return id in MESSAGE_BATCHES

#a tossed batch goes in front of their newer messages, False when nothing of theirs is waiting
def fold_batch(id: str, user_name: str, current_message_batch: list, current_entries: list[str]) -> bool:
    if(id not in MESSAGE_BATCHES):
        return False

    MESSAGE_BATCHES[id][:0] = current_message_batch

    BATCH_ENTRIES[id][:0] = current_entries

    print(f"BATCH FOLDED: {user_name} messaged again while their reply was being written, so their next batch answers it all at once")

    print()

    return True

#answers the whole batch once they stop, late messages join right up until it gets there lock
async def batch(id: str) -> None:
    #everything it prints comes out as one block at the end, sent or failed
    held_token = prints.hold()

    try:
        await wait_for_pic(id)

        await asyncio.sleep(MESSENGER_BATCH_TIME)

        #the name lookup is slow, doing it before the batch closes lets late messages still join
        user_name: str = await asyncio.to_thread(username.username, id, "messenger")

        current_message_batch: list = []

        current_entries: list[str] = []

        taken: bool = False

        answered: bool = False

        #a reply held for the owners answer gets written again once its on file
        while(not answered):
            #there last batch finishes first, so this one sees that reply in the history
            async with customer_lock(id):
                #no waiting from here to core, so the owners news can't sneak out in between
                if(not taken):
                    current_message_batch = MESSAGE_BATCHES.pop(id)

                    current_entries = BATCH_ENTRIES.pop(id)

                    del BATCH_COUNTDOWNS[id]

                    taken = True

                    print(f"INCOMING MESSAGE BATCH FROM on messenger from: {user_name}")

                    print(f"Message batch: {current_message_batch}")

                    print()

                answered = await asyncio.to_thread(core, current_message_batch, id, "messenger", sent_since)

                #they messaged mid reply, so their newer batch answers this one too
                if(not answered and fold_batch(id, user_name, current_message_batch, current_entries)):
                    return

        #answered, so its messages come off the journal and a restart never answers them again
        await asyncio.to_thread(journal.clear, "messenger", id, current_entries)
    finally:
        prints.release(held_token)

#every new message restarts their countdown, so the batch only goes out once they stop
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

#one message at a time through the spam check, so the dashboard and the batch keep order
async def take_message(id: str, message: list) -> None:
    async with spam.intake_lock(id):
        #only its text can be spam, and spam never shows in the dashboard or gets a reply
        if(await asyncio.to_thread(spam.is_spam, id, message[0], "messenger")):
            return

        #the dashboard shows it unless the owner had them first, only switched on ones get batched
        if(await asyncio.to_thread(dashboard.take_in, id, "messenger", message)):
            #on file before it waits in the batch, so a restart while it waits never loses it
            journal_entry: str = await asyncio.to_thread(journal.save, "messenger", id, message)

            queue_message(id, message, journal_entry)


#MESSENGER WEBHOOK

#metas subscribe check is a GET, the challenge only goes back with the right verify token
async def messenger_verify(request: Request):
    mode: str = request.query_params.get("hub.mode", "")

    token: str = request.query_params.get("hub.verify_token", "")

    challenge: str = request.query_params.get("hub.challenge", "")

    #compare_digest so the response time does not leak how close a guess was
    if(mode == "subscribe" and hmac.compare_digest(token.encode(), MESSENGER_VERIFY_TOKEN.encode())):
        return PlainTextResponse(challenge)

    print("MESSENGER WEBHOOK VERIFY FAILED: mode or verify token did not match")

    return PlainTextResponse("Forbidden", status_code=403)

#every messenger message comes in here as a signed POST
async def messenger_hook(request: Request):
    if(not MESSENGER_APP_SECRET):
        print("MESSENGER WEBHOOK ERROR: MESSENGER_APP_SECRET is not set, event refused")

        return JSONResponse({"error": "messenger webhook is not configured"}, status_code=503)

    body: bytes | None = await read_body(request)

    if(body is None):
        print("MESSENGER WEBHOOK REJECTED: body is over the size cap")

        return JSONResponse({"error": "body too large"}, status_code=413)

    #meta signs every event, so a forged message never reaches the batch
    if(not meta_signed(body, request.headers.get("X-Hub-Signature-256", ""), MESSENGER_APP_SECRET)):
        print("MESSENGER WEBHOOK REJECTED: wrong signature")

        return JSONResponse({"error": "unauthorized"}, status_code=401)

    data: dict = json.loads(body)

    #messenger events always come as a page object
    if(data.get("object") != "page"):
        return JSONResponse({"status": "ok"})

    #meta can group several entries and events into one POST, so every one of them is read
    entries: list | None = data.get("entry")

    if(not entries):
        entries = []

    for entry in entries:
        events: list | None = entry.get("messaging")

        if(not events):
            events = []

        for event in events:
            sender: dict | None = event.get("sender")

            if(not sender):
                sender = {}

            id: str = sender.get("id")

            message: list | None = event_message(event)

            #reads, deliveries, reactions, echoes and sticker only messages have nothing to answer
            if(not id or message is None):
                continue

            if(await new_message(event_message_id(event, id))):
                await take_message(id, message)

    return JSONResponse({"status": "ok"})


#ROUTES

APP.add_api_route("/messenger/webhook", messenger_verify, methods=["GET"])

APP.add_api_route("/messenger/webhook", messenger_hook, methods=["POST"])


#RUN

#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
