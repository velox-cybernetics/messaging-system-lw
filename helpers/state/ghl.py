#**********IMPORTS**********
#the env keys, the one background worker, the lock on the app's token, the clock each text is stamped with, the shape a text is logged in, web requests that log each text in the shop's ghl, and the file the app's tokens stay on
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import TypeAlias

import requests
from dotenv import load_dotenv

from helpers.state import log



#**********GLOBALS**********
#the shop's ghl sub-account every text the bot sends or a customer sends in gets logged in, the worker that logs them, and the shop's own app that is the bot's channel in ghl


#LOAD ENV
load_dotenv()


#ACCESS TOKEN
#the shop's private integration token, it finds and makes contacts and adds messages to their conversations
GHL_API_KEY: str = os.environ["GHL_API_KEY"]


#LOCATION
#the shop's sub-account, where every contact gets looked up and made
GHL_LOCATION_ID: str = os.environ["GHL_LOCATION_ID"]


#API URL
GHL_BASE_URL: str = "https://services.leadconnectorhq.com"


#API VERSIONS
#contacts, conversations and the app's sub-account token each answer to their own version
CONTACTS_VERSION: str = "2021-07-28"

CONVERSATIONS_VERSION: str = "2021-04-15"

OAUTH_VERSION: str = "2021-07-28"


#REQUEST TIME
#every call runs off the reply path, so it can wait a little
REQUEST_TIMEOUT: int = 10


#SENT
#one text that went out or came in: what it said, the pics it carried, and when it went out or came in, in seconds
SENT: TypeAlias = tuple[str, list[str], float]


#DIRECTIONS
#a text the shop sent them, and one they sent the shop
OUTBOUND: str = "outbound"

INBOUND: str = "inbound"


#WORKER
#one worker logs everything in the order it went out or came in, so a slow call never puts their conversation out of order
WORKER: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ghl")


#APP KEYS
#the shop's own marketplace app adds the bot's number to ghl as its own channel, so a text he sends on it comes to the bot to go out over blooio
#getenv so the bot still runs before the app is made, nothing of the app works till they're in
GHL_APP_CLIENT_ID: str = os.getenv("GHL_APP_CLIENT_ID", "")

GHL_APP_CLIENT_SECRET: str = os.getenv("GHL_APP_CLIENT_SECRET", "")


#BOT CHANNEL
#the app's conversation provider, every text over blooio is logged under it, so his normal numbers stay on their own channel in ghl
GHL_PROVIDER_ID: str = os.getenv("GHL_PROVIDER_ID", "")


#APP TOKENS
#where the app's tokens stay on file, and how long before its access token runs out it gets a new one
APP_TOKENS_KEY: str = "ghl_app_tokens"

APP_TOKEN_FIELDS: list[str] = ["access_token", "refresh_token", "expires_at"]

TOKEN_MARGIN_SECONDS: int = 300


#TOKEN LOCK
#a refresh token only works once, so two of his texts at the same moment never both refresh it
TOKEN_LOCK: threading.Lock = threading.Lock()


#STOP STATUSES
#ghl's do not disturb on texts reads one of these once they texted STOP
STOP_STATUSES: list[str] = ["active", "permanent"]



#**********REQUESTS**********
#every call to ghl goes out the same way


#GHL REQUEST
#the json ghl answered with, a refused call raises with its status and what ghl said, so the print shows why
#every call goes out on the private integration token, except the ones only the app's own token is let to make
def ghl_request(method: str, path: str, version: str, token: str = GHL_API_KEY, **options) -> dict:
    headers: dict[str, str] = {"Authorization": f"Bearer {token}", "Version": version, "Accept": "application/json"}

    response: requests.Response = requests.request(method, f"{GHL_BASE_URL}{path}", headers=headers, timeout=REQUEST_TIMEOUT, **options)

    if(response.status_code >= 400):
        raise ValueError(f"{response.status_code} {response.text[:300]}")

    return response.json()



#**********PROVIDER APP**********
#the app's tokens, got once when it's installed on the shop's sub-account and refreshed as they run out, since only its token can add texts to its channel and say whether one he sent went out


#TOKEN REQUEST
#the app's tokens for an install code or a refresh token, a refused one raises with what ghl said
def token_request(fields: dict[str, str]) -> dict:
    form: dict[str, str] = {"client_id": GHL_APP_CLIENT_ID, "client_secret": GHL_APP_CLIENT_SECRET, "user_type": "Location", **fields}

    response: requests.Response = requests.post(f"{GHL_BASE_URL}/oauth/token", data=form, headers={"Accept": "application/json"}, timeout=REQUEST_TIMEOUT)

    if(response.status_code >= 400):
        raise ValueError(f"{response.status_code} {response.text[:300]}")

    return response.json()


#SAVE TOKENS
#a new access token goes on file with the refresh token that came with it, the old refresh token never works again
def save_app_tokens(answer: dict) -> str:
    expires_at: float = time.time() + float(answer.get("expires_in", 0))

    log.write_info(APP_TOKENS_KEY, [answer["access_token"], answer["refresh_token"], str(expires_at)], APP_TOKEN_FIELDS)

    return answer["access_token"]


#LOCATION TOKEN
#an agency admin installing the app hands back an agency token, which trades for the shop's sub-account token and the refresh token that keeps it going
def location_token(agency_answer: dict) -> dict:
    form: dict[str, str] = {"companyId": agency_answer.get("companyId", ""), "locationId": GHL_LOCATION_ID}

    return ghl_request("post", "/oauth/locationToken", OAUTH_VERSION, token=agency_answer["access_token"], data=form)


#CONNECT APP
#the code ghl hands back when the app gets installed, only an install on the shop's own sub-account puts its tokens on file
def connect_app(code: str, redirect_uri: str) -> None:
    answer: dict = token_request({"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri})

    #an agency admin's install is for the agency, so it gets traded for the shop's sub-account
    if(answer.get("userType") == "Company"):
        answer = location_token(answer)

    if(answer.get("locationId") != GHL_LOCATION_ID):
        raise ValueError(f"the app was installed on {answer.get('locationId')}, not the shop's sub-account")

    save_app_tokens(answer)


#APP TOKEN
#the app's access token, refreshed first when it's about to run out
def app_token() -> str:
    with TOKEN_LOCK:
        tokens: dict[str, str] = log.read_info(APP_TOKENS_KEY)

        if(not tokens.get("refresh_token")):
            raise ValueError("the ghl app was never installed on the shop's sub-account")

        if(time.time() < float(tokens.get("expires_at", "0")) - TOKEN_MARGIN_SECONDS):
            return tokens["access_token"]

        answer: dict = token_request({"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]})

        return save_app_tokens(answer)


#MARK STATUS
#ghl shows the text he sent as delivered or failed, failed with the reason why
def mark_status(message_id: str, delivered: bool, reason: str = "") -> None:
    status: dict = {"status": "delivered"}

    if(not delivered):
        status = {"status": "failed", "error": {"code": "1", "type": "saas", "message": reason}}

    ghl_request("put", f"/conversations/messages/{message_id}/status", CONVERSATIONS_VERSION, token=app_token(), json=status)



#**********CONTACTS**********
#finds the customer's contact in ghl by what they text from, a blooio chat is a phone number or the email an imessage came from


#FIND CONTACT
#None when ghl has no contact on that number or email
def find_contact(id: str) -> str | None:
    search_field: str = "email" if "@" in id else "number"

    found: dict = ghl_request("get", "/contacts/search/duplicate", CONTACTS_VERSION, params={"locationId": GHL_LOCATION_ID, search_field: id})

    contact: dict | None = found.get("contact")

    if(contact is None):
        return None

    return contact["id"]


#MAKE CONTACT
#a customer ghl never had gets a contact on the number or email they text from
def make_contact(id: str) -> str:
    contact_field: str = "email" if "@" in id else "phone"

    made: dict = ghl_request("post", "/contacts/", CONTACTS_VERSION, json={"locationId": GHL_LOCATION_ID, contact_field: id})

    return made["contact"]["id"]


#CONTACT
#their contact in ghl, made the first time someone ghl doesn't have yet texts in or gets a text from the bot
def contact_id(id: str) -> str:
    found: str | None = find_contact(id)

    if(found is None):
        return make_contact(id)

    return found



#**********LOGGING**********
#every text the bot sends a customer over blooio, and every text they send it there, goes in their conversation in ghl on the bot's channel, since ghl never sees blooio


#LOG TEXT
#one text goes in their conversation, as one the shop sent or one they sent, with its pics and the moment it went out or came in
#the inbound route only adds it to the conversation, sending it through ghl would text them a second time
#it goes in on the app's own token, the one ghl lets add texts to the app's channel
def log_text(contact: str, text_entry: SENT, direction: str) -> None:
    text, pics, logged_at = text_entry

    message: dict = {"type": "Custom", "conversationProviderId": GHL_PROVIDER_ID, "contactId": contact, "message": text, "direction": direction, "date": datetime.fromtimestamp(logged_at, timezone.utc).isoformat()}

    if(len(pics) > 0):
        message["attachments"] = pics

    ghl_request("post", "/conversations/messages/inbound", CONVERSATIONS_VERSION, token=app_token(), json=message)


#WRITE TEXTS
#their contact is found once, then each text goes in on its own, so one ghl refuses never keeps the rest out
#a failure is only printed, the texts already went out or came in
def write_texts(id: str, texts: list[SENT], direction: str) -> None:
    try:
        contact: str = contact_id(id)

    except Exception as error:
        print(f"[GHL] contact for {id} failed, so {len(texts)} {direction} texts never got logged: {error}")

        return

    for text_entry in texts:
        try:
            log_text(contact, text_entry, direction)

        except Exception as error:
            print(f"[GHL] logging an {direction} text for {id} failed: {error}")


#LOG SENT
#the texts a customer got go to ghl off the reply path, so ghl can never slow down or break a reply
def log_sent(id: str, sent: list[SENT]) -> None:
    if(len(sent) == 0):
        return

    WORKER.submit(write_texts, id, sent, OUTBOUND)


#ATTACHMENT URLS
#where each pic or video they sent lives, blooio puts the url on each attachment
def attachment_urls(attachments: list | None) -> list[str]:
    urls: list[str] = []

    for attachment in attachments or []:
        if(isinstance(attachment, str)):
            urls.append(attachment)

        elif(isinstance(attachment, dict) and attachment.get("url")):
            urls.append(attachment["url"])

    return urls


#LOG RECEIVED
#a text a customer sends in goes to ghl off the webhook, on the same worker as the replies, so their conversation there reads in order
def log_received(id: str, text: str | None, attachments: list | None) -> None:
    pics: list[str] = attachment_urls(attachments)

    #nothing to show, like a delivery with no text and no pic
    if((text or "").strip() == "" and len(pics) == 0):
        return

    WORKER.submit(write_texts, id, [(text or "", pics, time.time())], INBOUND)



#**********SMS**********
#the follow ups that go out from the shop's own number in ghl once blooio is done with them, and what ghl knows about who gets them


#SEND SMS
#one text from the shop's default number in ghl, which keeps it in their conversation there on its own, a refused one raises with what ghl said
def send_sms(contact: str, text: str) -> None:
    ghl_request("post", "/conversations/messages", CONVERSATIONS_VERSION, json={"type": "SMS", "contactId": contact, "message": text})


#CONTACT DETAILS
#everything ghl has on the contact, like their first name and whether they texted STOP
def contact_details(contact: str) -> dict:
    answer: dict = ghl_request("get", f"/contacts/{contact}", CONTACTS_VERSION)

    return answer.get("contact") or {}


#SMS STOPPED
#they texted STOP, so ghl has them on do not disturb for texts or for everything, and an sms to them never goes out
def sms_stopped(details: dict) -> bool:
    if(details.get("dnd") is True):
        return True

    sms_setting: dict = (details.get("dndSettings") or {}).get("SMS") or {}

    return sms_setting.get("status") in STOP_STATUSES
