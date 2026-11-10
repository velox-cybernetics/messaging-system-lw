#IMPORTS

import asyncio
import base64
import json
import os

import uvicorn
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from helpers.channels import senders
from helpers.state import dashboard
from helpers.state import ghl
from helpers.state.log import REDIS_CLIENT
from servers.blooio import read_body, take_message
from src import followup


#GLOBALS

load_dotenv()

#no docs or openapi pages, nobody gets a free map of the webhook
APP = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#ghl refuses any url with ghl or highlevel in it, so every path hides under crm
CALLBACK_PATH: str = "/crm/oauth/callback"

DELIVERY_PATH: str = "/crm/outbound"

#where the apps InboundMessage event lands, every text a customer writes the shop in ghl
INBOUND_PATH: str = "/crm/inbound"

INBOUND_EVENT: str = "InboundMessage"

#the exact redirect url saved on the app, ghl only trades an install code for tokens with it
REDIRECT_URI: str = f"{os.getenv('PUBLIC_BASE_URL', '').rstrip('/')}{CALLBACK_PATH}"

#ghls published ed25519 pem, same for every account, the real key is its last 32 bytes
GHL_PUBLIC_KEY_TEXT: str = "MCowBQYDK2VwAyEAi2HR1srL4o18O8BRa7gVJY7G7bupbN3H9AwJrHCDiOg="

GHL_PUBLIC_KEY = Ed25519PublicKey.from_public_bytes(base64.b64decode(GHL_PUBLIC_KEY_TEXT)[-32:])

#a text on the systems channel comes in as an sms or as the channels own custom type
TEXT_TYPES: list[str] = ["SMS", "Custom"]

#ghl resends anything it thinks got missed, so ids stick around 48 hours and texts go out once
SEEN_TTL_SECONDS: int = 172800

#the carriers opt out words, ghl stops their sms on its own so the system only notes it
STOP_WORDS: list[str] = ["stop", "stopall", "unsubscribe", "cancel", "end", "quit"]


#WEBHOOK SAFETY

#true when the base64 signature header is ghls ed25519 signature of the exact body bytes
def ghl_signed(body: bytes, signature: str) -> bool:
    #a signature that isn't even base64 raises a ValueError before it gets checked
    try:
        GHL_PUBLIC_KEY.verify(base64.b64decode(signature, validate=True), body)
    except (InvalidSignature, ValueError):
        return False

    return True

#set nx is one atomic step, so two copies of a delivery can never both go out
def first_seen(message_id: str) -> bool:
    seen: bool | None = REDIS_CLIENT.set(f"seen_ghl_{message_id}", "1", nx=True, ex=SEEN_TTL_SECONDS)

    return bool(seen)


#SENDING

#tells ghl how the text went, a refusal is only printed since the text is out or not anyway
def report_status(message_id: str, delivered: bool, reason: str) -> None:
    status: str = ""

    if(delivered):
        status = "delivered"
    else:
        status = "failed"

    try:
        ghl.mark_status(message_id, delivered, reason)
    except Exception as error:
        print(f"[GHL] marking {message_id} {status} failed: {error}")

#a text with a userId came from a person, so the system goes quiet for them, workflows don't count
def send_from_ghl(data: dict) -> None:
    message_id: str = data["messageId"]

    phone: str = data.get("phone")

    if(not phone):
        phone = ""

    text: str = data.get("message")

    if(not text):
        text = ""

    attachments: list[str] = data.get("attachments")

    if(not attachments):
        attachments = []

    if(phone == ""):
        print(f"[GHL] text {message_id} has no phone to go to, so it never went out")

        report_status(message_id, False, "The contact has no phone number to text.")

        return

    #a failed switch still lets his text out, the dashboard can switch them off by hand
    if(data.get("userId")):
        try:
            dashboard.switch_off(phone)

            print(f"SWITCHED OFF: the owner texted {phone} from ghl, so the bot stays quiet for them")
        except Exception as error:
            print(f"[GHL] switching {phone} off failed, the bot may still answer them: {error}")

    sent: bool = senders.send_ghl_text(phone, text, attachments)

    report_status(message_id, sent, "Blooio refused the text.")


#GHL WEBHOOKS

#installing the app on the shops account lands here with a code, traded once for tokens
async def ghl_install(code: str = ""):
    if(code == ""):
        return HTMLResponse("No install code came back from GHL.", status_code=400)

    try:
        await asyncio.to_thread(ghl.connect_app, code, REDIRECT_URI)
    except Exception as error:
        print(f"[GHL] connecting the app failed: {error}")

        return HTMLResponse(f"Connecting the GHL app failed: {error}", status_code=400)

    print("[GHL] the app is connected to the shop's sub-account")

    return HTMLResponse("Connected. The bot's number now shows in GHL's message box as its own channel, system-line.")

#every text sent on the systems channel in ghl lands here signed, the shops go out over blooio
async def ghl_hook(request: Request):
    body: bytes | None = await read_body(request)

    if(body is None):
        print("GHL DELIVERY REJECTED: body is over the size cap")

        return JSONResponse({"error": "body too large"}, status_code=413)

    if(not ghl_signed(body, request.headers.get("X-GHL-Signature", ""))):
        print("GHL DELIVERY REJECTED: signature is missing or wrong")

        return JSONResponse({"error": "unauthorized"}, status_code=401)

    data: dict = json.loads(body)

    #the app only ever lives in the shops own account, and it only ever sends texts
    if(data.get("type") not in TEXT_TYPES or data.get("locationId") != ghl.GHL_LOCATION_ID):
        print(f"GHL DELIVERY SKIPPED: a {data.get('type')} for {data.get('locationId')}, only the shop's texts go out")

        return {"status": "ok"}

    message_id: str = data.get("messageId")

    if(not message_id):
        message_id = ""

    #a resend only goes out the first time, and one with no id can't be told from a resend
    if(message_id == "" or not await asyncio.to_thread(first_seen, message_id)):
        return {"status": "ok"}

    await asyncio.to_thread(send_from_ghl, data)

    return {"status": "ok"}


#SMS LINE

#true for a customers sms to the shops own number, never a text logged on the systems channel
def inbound_sms(data: dict) -> bool:
    if(data.get("type") != INBOUND_EVENT or data.get("locationId") != ghl.GHL_LOCATION_ID):
        return False

    if(data.get("messageType") != "SMS" or data.get("direction") != ghl.INBOUND):
        return False

    provider: str | None = data.get("conversationProviderId")

    #blooio texts get logged in ghl under the apps provider, those already came in over blooio
    if(provider and provider == ghl.GHL_PROVIDER_ID):
        return False

    return True

#each sms goes by its id, or by who sent it and when on one that came without an id
def sms_key(data: dict) -> str:
    message_id: str | None = data.get("messageId")

    if(message_id):
        return message_id

    contact: str | None = data.get("contactId")

    sent_at: str | None = data.get("dateAdded")

    if(not contact or not sent_at):
        return ""

    return f"{contact}_{sent_at}"

#the pics on an sms the way blooio hands them over, so the batch reads them like any other pic
def sms_pics(attachments: list | None) -> list[dict]:
    pics: list[dict] = []

    for url in ghl.attachment_urls(attachments):
        pics.append({"url": url})

    return pics

#hazel only takes an sms from someone the system texted on that line, the rest stay the owners
async def take_sms(data: dict) -> None:
    phone: str | None = data.get("from")

    if(not phone):
        phone = ""

    text: str | None = data.get("body")

    if(not text):
        text = ""

    #his own number only ever answers color checks, and never over sms
    if(phone == "" or phone == senders.OWNER_NUMBER):
        return

    #nobody the system texted on this line, so its the owners own conversation and hazel stays out
    if(not await asyncio.to_thread(followup.sms_reply_expected, phone)):
        return

    #a follow up from before the line got marked gets its mark now, so her reply goes out on it
    await asyncio.to_thread(senders.open_sms_line, phone)

    #ghl stops their sms on its own, so the system only notes it and never texts back
    if(text.strip().lower() in STOP_WORDS):
        await asyncio.to_thread(followup.stop_followups, phone)

        return

    print(f"SMS LINE MESSAGE: {phone} texted the shop's sms number back, so hazel answers them on it")

    await take_message(phone, text, sms_pics(data.get("attachments")), True)

#every text a customer writes the shop in ghl lands here signed, only an sms on the follow up line counts
async def ghl_inbound_hook(request: Request):
    body: bytes | None = await read_body(request)

    if(body is None):
        print("GHL INBOUND REJECTED: body is over the size cap")

        return JSONResponse({"error": "body too large"}, status_code=413)

    if(not ghl_signed(body, request.headers.get("X-GHL-Signature", ""))):
        print("GHL INBOUND REJECTED: signature is missing or wrong")

        return JSONResponse({"error": "unauthorized"}, status_code=401)

    data: dict = json.loads(body)

    #calls, emails and the systems own channel land here too, hazel only wants the sms
    if(not inbound_sms(data)):
        return {"status": "ok"}

    key: str = sms_key(data)

    #a resend only gets taken the first time, and one with no key can't be told from a resend
    if(key == "" or not await asyncio.to_thread(first_seen, key)):
        return {"status": "ok"}

    await take_sms(data)

    return {"status": "ok"}


#ROUTES

#no response model for any of them, fastapi just sends back whatever they return
APP.add_api_route(CALLBACK_PATH, ghl_install, methods=["GET"], response_model=None)

APP.add_api_route(DELIVERY_PATH, ghl_hook, methods=["POST"], response_model=None)

APP.add_api_route(INBOUND_PATH, ghl_inbound_hook, methods=["POST"], response_model=None)


#RUN

#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
