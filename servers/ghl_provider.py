#**********IMPORTS**********
#python's tools, the web server, ghl's signing key, the shop's ghl app, the dashboard's switch, the sender that texts over blooio, and the capped body read every webhook goes through
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
from servers.blooio import read_body



#**********GLOBALS**********
#the web server ghl hands every text the owner sends on the bot's channel to, since the shop's ghl app is that channel


#LOAD ENV
load_dotenv()


#APP
#no /docs, /redoc, or /openapi.json, so nobody can pull up a map of the webhook
APP: FastAPI = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


#PATHS
#the app's install comes back to the callback, and the delivery url is where ghl posts every text sent from it
#ghl refuses any url with "ghl" or "highlevel" in it, so both go under /crm
CALLBACK_PATH: str = "/crm/oauth/callback"

DELIVERY_PATH: str = "/crm/outbound"


#REDIRECT URL
#the exact redirect url saved on the app, ghl only trades an install code for tokens with it
REDIRECT_URI: str = f"{os.getenv('PUBLIC_BASE_URL', '').rstrip('/')}{CALLBACK_PATH}"


#GHL KEY
#ghl signs every post to the delivery url with its ed25519 key, the same public key for every account
#this is the key ghl publishes as a pem, the key itself is its last 32 bytes
GHL_PUBLIC_KEY_TEXT: str = "MCowBQYDK2VwAyEAi2HR1srL4o18O8BRa7gVJY7G7bupbN3H9AwJrHCDiOg="

GHL_PUBLIC_KEY: Ed25519PublicKey = Ed25519PublicKey.from_public_bytes(base64.b64decode(GHL_PUBLIC_KEY_TEXT)[-32:])


#TEXT TYPES
#a text sent on the bot's channel can come in as an sms or as the channel's own custom type
TEXT_TYPES: list[str] = ["SMS", "Custom"]


#SEEN TIME
#ghl retries a delivery it thinks was missed, so a text's id is kept for 48 hours and it only ever goes out once
SEEN_TTL_SECONDS: int = 172800



#**********WEBHOOK SAFETY**********
#keeps out forged and repeated deliveries, so each text he sends goes out once and only when ghl sent it


#GHL SIGNED
#the signature is ghl's ed25519 signature of the exact body bytes, base64 in X-GHL-Signature
def ghl_signed(body: bytes, signature: str) -> bool:
    #a signature that isn't base64 at all raises a ValueError before it's ever checked
    try:
        GHL_PUBLIC_KEY.verify(base64.b64decode(signature, validate=True), body)

    except (InvalidSignature, ValueError):
        return False

    return True


#FIRST SEEN
#set nx is one atomic step, so two copies of a delivery can never both go out
def first_seen(message_id: str) -> bool:
    seen: bool | None = REDIS_CLIENT.set(f"seen_ghl_{message_id}", "1", nx=True, ex=SEEN_TTL_SECONDS)

    return bool(seen)



#**********SENDING**********
#his text goes out from the bot's number, the bot goes quiet for them when a person wrote it, and ghl hears whether it went out


#REPORT STATUS
#a status ghl refuses is only printed, the text already went out or didn't
def report_status(message_id: str, delivered: bool, reason: str) -> None:
    status: str = "delivered" if delivered else "failed"

    try:
        ghl.mark_status(message_id, delivered, reason)

    except Exception as error:
        print(f"[GHL] marking {message_id} {status} failed: {error}")


#SEND FROM GHL
#a person wrote it when it has a userId, so the bot is switched off for them before it goes out, a workflow's text leaves the bot on
def send_from_ghl(data: dict) -> None:
    message_id: str = data["messageId"]

    phone: str = data.get("phone") or ""

    text: str = data.get("message") or ""

    attachments: list[str] = data.get("attachments") or []

    if(phone == ""):
        print(f"[GHL] text {message_id} has no phone to go to, so it never went out")

        report_status(message_id, False, "The contact has no phone number to text.")

        return

    #a switch that fails still lets his text go out, the dashboard can switch them off by hand
    if(data.get("userId")):
        try:
            dashboard.switch_off(phone)

            print(f"SWITCHED OFF: the owner texted {phone} from ghl, so the bot stays quiet for them")

        except Exception as error:
            print(f"[GHL] switching {phone} off failed, the bot may still answer them: {error}")

    sent: bool = senders.send_ghl_text(phone, text, attachments)

    report_status(message_id, sent, "Blooio refused the text.")



#**********GHL WEBHOOKS**********
#the app's install and every text sent from ghl come in here


#GHL INSTALL
#installing the app on the shop's sub-account lands here with a code, traded once for the tokens that mark his texts delivered
@APP.get(CALLBACK_PATH, response_model=None)
async def ghl_install(code: str = "") -> HTMLResponse:
    if(code == ""):
        return HTMLResponse("No install code came back from GHL.", status_code=400)

    try:
        await asyncio.to_thread(ghl.connect_app, code, REDIRECT_URI)

    except Exception as error:
        print(f"[GHL] connecting the app failed: {error}")

        return HTMLResponse(f"Connecting the GHL app failed: {error}", status_code=400)

    print("[GHL] the app is connected to the shop's sub-account")

    return HTMLResponse("Connected. The bot's number now shows in GHL's message box as its own channel, system-line.")


#GHL HOOK
#every text sent on the bot's channel in ghl comes in here as a signed POST, a text for the shop's sub-account goes out over blooio
#it answers with a dict or a JSONResponse, so fastapi makes no response model from the annotation
@APP.post(DELIVERY_PATH, response_model=None)
async def ghl_hook(request: Request) -> dict | JSONResponse:
    body: bytes | None = await read_body(request)

    if(body is None):
        print("GHL DELIVERY REJECTED: body is over the size cap")

        return JSONResponse({"error": "body too large"}, status_code=413)

    if(not ghl_signed(body, request.headers.get("X-GHL-Signature", ""))):
        print("GHL DELIVERY REJECTED: signature is missing or wrong")

        return JSONResponse({"error": "unauthorized"}, status_code=401)

    data: dict = json.loads(body)

    #the app is only ever the bot's channel in the shop's own sub-account, and it only ever sends texts
    if(data.get("type") not in TEXT_TYPES or data.get("locationId") != ghl.GHL_LOCATION_ID):
        print(f"GHL DELIVERY SKIPPED: a {data.get('type')} for {data.get('locationId')}, only the shop's texts go out")

        return {"status": "ok"}

    message_id: str = data.get("messageId") or ""

    #a delivery ghl sends again goes out only the first time, and one with no id can't be told apart from a resend
    if(message_id == "" or not await asyncio.to_thread(first_seen, message_id)):
        return {"status": "ok"}

    await asyncio.to_thread(send_from_ghl, data)

    return {"status": "ok"}



#**********RUN**********
#starts this webhook server on its own when the file is run directly


#RUN SERVER
#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
