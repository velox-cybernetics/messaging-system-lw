#**********IMPORTS**********
#python's tools, the web server, the dashboard, the journal that keeps every waiting message, and the core that answers each instagram message
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
from helpers.chains import color_chains
from helpers.channels import username
from helpers.terminal import prints



#**********GLOBALS**********
#the web server, the instagram keys, and the memory that holds each customer's waiting messages


#LOAD ENV
load_dotenv()


#APP
#no docs pages, app.py serves this router and they would come along with it
APP: FastAPI = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


#VERIFY TOKEN
#the verify token typed into the meta app dashboard when the webhook is subscribed
INSTAGRAM_VERIFY_TOKEN: str = os.environ["IG_VERIFY_TOKEN"]


#INSTAGRAM SECRET
#the instagram app secret (instagram > api setup with instagram login in the meta app dashboard), meta signs every instagram event with it
#getenv so the other webhooks still start before it is in .env, every event is refused until it is
INSTAGRAM_APP_SECRET: str | None = os.getenv("IG_APP_SECRET")


#MESSAGE BATCHES
#each id's countdown till their batch gets answered
BATCH_COUNTDOWNS: dict[str, asyncio.Task] = {}

#the messages each id sent that wait on that countdown
MESSAGE_BATCHES: dict[str, list] = {}

#each of those messages' entries in the journal, cleared once their batch is answered
BATCH_ENTRIES: dict[str, list[str]] = {}


#CUSTOMER LOCKS
#one lock per id, so only one of their batches gets answered at a time
CUSTOMER_LOCKS: dict[str, asyncio.Lock] = {}


#NEWS TIMERS
#what the owner found for each customer, waiting a few seconds on anything they're still sending before it goes out on its own
NEWS_TIMERS: dict[str, asyncio.Task] = {}



#**********TIMINGS**********
#how long each wait lasts and how big a webhook may be before it gets refused


#BATCH TIMES
INSTAGRAM_BATCH_TIME: int = 20

#they can take a while to find the pic and send it, so a batch still waiting on an asked-for pic gets this much longer
INSTAGRAM_PIC_WAIT_TIME: int = 75


#WEBHOOK LIMITS
#a real webhook is a few kilobytes, so a bigger body is refused before it can fill the instance's memory
MAX_BODY_BYTES: int = 1024 * 1024

#meta retries a delivery it thinks failed for up to 36 hours, so an id is kept for 48 hours
SEEN_TTL_SECONDS: int = 172800



#**********WEBHOOK SAFETY**********
#keeps out giant, forged and repeated deliveries so each real message gets answered once


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


#META SIGNED
#meta signs the body with the app secret, sent as "sha256=<hex>" in X-Hub-Signature-256
def meta_signed(body: bytes, signature: str, secret: str) -> bool:
    expected: str = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    #compare_digest so the response time does not leak how close a guess was
    return hmac.compare_digest(signature.encode(), f"sha256={expected}".encode())


#FIRST SEEN
#set nx is one atomic step, so two copies of a delivery can never both get through
def first_seen(message_id: str) -> bool:
    seen: bool | None = REDIS_CLIENT.set(f"seen_ig_{message_id}", "1", nx=True, ex=SEEN_TTL_SECONDS)

    return bool(seen)


#NEW MESSAGE
#meta resends a delivery it thinks was missed, an id already seen was already batched
async def new_message(message_id: str | None) -> bool:
    if(not message_id):
        return True

    try:
        if(not await asyncio.to_thread(first_seen, message_id)):
            print(f"DUPLICATE WEBHOOK SKIPPED: ig {message_id}")

            print()

            return False

    #redis down must not drop the message, it is answered without the dedupe
    except Exception as error:
        print(f"DEDUPE ERROR: {error}")

    return True



#**********PIC WAITING**********
#gives a pic the shop asked for time to land, so it goes out in the same batch as its message


#PIC PENDING
#true when the shop's last reply asked for a pic and none is in the batch yet, a list with anything in it is a pic or a shared post
def pic_pending(id: str, message_batch: list) -> bool:
    for message in message_batch:
        if(isinstance(message, list) and message != []):
            return False

    return spacing.asks_for_pic(spacing.last_sent_reply(message_history_form(id)))


#PIC WAIT
#the pic the shop asked for gets time to land before the countdown starts, so it goes out in the same batch as its message
async def wait_for_pic(id: str) -> None:
    try:
        #a copy, the batch keeps growing in the event loop while the history gets read in a worker thread
        waiting: bool = await asyncio.to_thread(pic_pending, id, list(MESSAGE_BATCHES[id]))

    #redis down never holds the batch up, it just goes out on the usual countdown
    except Exception as error:
        print(f"PIC WAIT ERROR: {error}")

        return

    if(waiting):
        user_name: str = await asyncio.to_thread(username.username, id, "ig")

        print(f"WAITING ON PIC: {user_name} gets {INSTAGRAM_PIC_WAIT_TIME}s more for the pic the shop asked for")

        await asyncio.sleep(INSTAGRAM_PIC_WAIT_TIME)



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
#sends what the owner found on its own when no reply to a message of theirs carries it


#STOP TIMER
#their news wait is called off, if one is running
def stop_news_timer(id: str) -> None:
    timer: asyncio.Task | None = NEWS_TIMERS.pop(id, None)

    if(timer is not None):
        timer.cancel()


#NEWS WAIT
#a few seconds for a message they're still sending to land, then any batch of theirs goes first so its reply carries it
async def news_wait(id: str) -> None:
    await asyncio.sleep(owner.NEWS_WAIT_SECONDS)

    #done waiting, so nothing cancels it from here, a newer answer from the owner gets its own wait
    if(NEWS_TIMERS.get(id) is asyncio.current_task()):
        del NEWS_TIMERS[id]

    while(True):
        #a batch of theirs counting down or being answered carries it with its reply
        await incoming_batch_answered(id)

        async with customer_lock(id):
            #a message that came in while this waited on their lock starts a batch that carries it too
            if(id in BATCH_COUNTDOWNS):
                continue

            #a reply that carried it leaves nothing to send
            if(await asyncio.to_thread(owner.news_due, id)):
                with prints.held():
                    user_name: str = await asyncio.to_thread(username.username, id, "ig")

                    print(f"COLOR NEWS: nothing from {user_name} is being answered, so what the owner found goes out on its own")

                    print()

                    await asyncio.to_thread(color_chains.send_color_news, id)

            return


#START TIMER
#a newer answer from the owner restarts their news wait
def start_news_timer(id: str) -> None:
    stop_news_timer(id)

    NEWS_TIMERS[id] = asyncio.create_task(news_wait(id))



#**********OWNER ANSWERS**********
#the owner answers color checks over his texts, so the text server hands his answer for an instagram customer to here


#OWNER ANSWER
#a reply of theirs being written holds off at the send till his answer is on file, so it goes out again carrying what he found
async def owner_answer(customer: str, answer: tuple, materials: list[dict[str, str]]) -> None:
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



#**********MESSAGE BATCHING**********
#holds their messages until they stop sending, then answers them all at once


#BATCH
#waits on an asked-for pic and the countdown, then answers the whole batch, again if its reply was held for the owner's answer
async def batch(id: str) -> None:
    #everything this batch prints, its countdown included, comes out in one block once its reply went out or it failed
    with prints.held():
        await wait_for_pic(id)

        await asyncio.sleep(INSTAGRAM_BATCH_TIME)

        #the name lookup is a web request, so it runs off the event loop, before the batch closes so a message landing meanwhile still joins it
        user_name: str = await asyncio.to_thread(username.username, id, "ig")

        current_message_batch: list = MESSAGE_BATCHES[id]

        current_entries: list[str] = BATCH_ENTRIES[id]

        #nothing waits from here to their lock, so what the owner found never goes out on its own in between
        del BATCH_COUNTDOWNS[id]

        del MESSAGE_BATCHES[id]

        del BATCH_ENTRIES[id]

        print(f"INCOMING MESSAGE BATCH FROM on ig from: {user_name}")

        print(f"Message batch: {current_message_batch}")

        print()

        answered: bool = False

        #a reply held for the owner's answer landing gets written again once his answer is on file, so it carries what he found
        while(not answered):
            #a batch closing while their last one is still being answered waits, so it sees that reply in the history
            async with customer_lock(id):
                #core runs in its own worker thread, so the server keeps taking webhooks while it works
                answered = await asyncio.to_thread(core, current_message_batch, id, "ig")

        #answered, so its messages come off the journal and a restart never answers them again
        await asyncio.to_thread(journal.clear, "ig", id, current_entries)


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



#**********INSTAGRAM WEBHOOK**********
#answers meta's verify check, then takes every message instagram delivers, checks it's real, and sends it to the batch


#INSTAGRAM VERIFY
#meta's subscribe check comes as a GET, it gets its challenge back only with the right verify token
@APP.get("/ig/webhook")
async def instagram_verify(request: Request) -> PlainTextResponse:
    mode: str = request.query_params.get("hub.mode", "")

    token: str = request.query_params.get("hub.verify_token", "")

    challenge: str = request.query_params.get("hub.challenge", "")

    #meta only gets its challenge back when the token matches the one set in the app dashboard, compare_digest so the response time does not leak how close a guess was
    if(mode == "subscribe" and hmac.compare_digest(token.encode(), INSTAGRAM_VERIFY_TOKEN.encode())):
        return PlainTextResponse(challenge)

    print("IG WEBHOOK VERIFY FAILED: mode or verify token did not match")

    return PlainTextResponse("Forbidden", status_code=403)


#INSTAGRAM HOOK
#every instagram message comes in here as a signed POST
@APP.post("/ig/webhook")
async def instagram_hook(request: Request) -> JSONResponse:
    if(not INSTAGRAM_APP_SECRET):
        print("IG WEBHOOK ERROR: IG_APP_SECRET is not set, event refused")

        return JSONResponse({"error": "ig webhook is not configured"}, status_code=503)

    body: bytes | None = await read_body(request)

    if(body is None):
        print("IG WEBHOOK REJECTED: body is over the size cap")

        return JSONResponse({"error": "body too large"}, status_code=413)

    #meta signs every event, so a forged message never reaches the batch
    if(not meta_signed(body, request.headers.get("X-Hub-Signature-256", ""), INSTAGRAM_APP_SECRET)):
        print("IG WEBHOOK REJECTED: wrong signature")

        return JSONResponse({"error": "unauthorized"}, status_code=401)

    data: dict = json.loads(body)

    #meta can group several entries and events into one POST, so every one of them is read
    for entry in data.get("entry") or []:
        for event in entry.get("messaging") or []:
            message: dict = event.get("message") or {}

            #check if its an incoming message from a user, echoes are the account's own sends
            if(not message or message.get("is_echo")):
                continue

            id: str = (event.get("sender") or {}).get("id")

            if(not id):
                continue

            #a message is text + attachments + referral
            if(await new_message(message.get("mid"))):
                incoming: list = [message.get("text"), message.get("attachments"), message.get("referral")]

                #every message shows in the dashboard, and only one from a customer switched on there gets batched
                if(await asyncio.to_thread(dashboard.take_in, id, "ig", incoming)):
                    #on file before it waits in the batch, so a restart while it waits never loses it
                    journal_entry: str = await asyncio.to_thread(journal.save, "ig", id, incoming)

                    queue_message(id, incoming, journal_entry)

    return JSONResponse({"status": "ok"})



#**********RUN**********
#starts this webhook server on its own when the file is run directly


#RUN SERVER
#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
