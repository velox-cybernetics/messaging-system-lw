#IMPORTS

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from helpers.state import log


#GLOBALS

load_dotenv()

#the shops private integration token, for contacts and their conversations
GHL_API_KEY: str = os.environ["GHL_API_KEY"]

#the shops sub account, where every contact gets looked up and made
GHL_LOCATION_ID: str = os.environ["GHL_LOCATION_ID"]

GHL_BASE_URL: str = "https://services.leadconnectorhq.com"

#contacts, conversations and the apps sub account token each answer to their own version
CONTACTS_VERSION: str = "2021-07-28"

CONVERSATIONS_VERSION: str = "2021-04-15"

OAUTH_VERSION: str = "2021-07-28"

#every call runs off the reply path, so it can wait a little
REQUEST_TIMEOUT: int = 10

#a text the shop sent them, and one they sent the shop
OUTBOUND: str = "outbound"

INBOUND: str = "inbound"

#one worker keeps every log in order, so a slow call never scrambles there conversation
WORKER = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ghl")

#getenv so the system still runs before the shops ghl app exists, the app just won't work
GHL_APP_CLIENT_ID: str = os.getenv("GHL_APP_CLIENT_ID", "")

GHL_APP_CLIENT_SECRET: str = os.getenv("GHL_APP_CLIENT_SECRET", "")

#the apps conversation provider, blooio texts log under it so his normal numbers stay apart
GHL_PROVIDER_ID: str = os.getenv("GHL_PROVIDER_ID", "")

#where the apps tokens stay on file, and how early before running out the access token renews
APP_TOKENS_KEY: str = "ghl_app_tokens"

APP_TOKEN_FIELDS: list[str] = ["access_token", "refresh_token", "expires_at"]

TOKEN_MARGIN_SECONDS: int = 300

#a refresh token only works once, so two of his texts at the same moment never both refresh it
TOKEN_LOCK = threading.Lock()

#ghls do not disturb on texts reads one of these once they texted STOP
STOP_STATUSES: list[str] = ["active", "permanent"]


#REQUESTS

#ghls json answer, raises with what ghl said, private token unless a call needs the apps
def ghl_request(method: str, path: str, version: str, token: str = GHL_API_KEY, params: dict | None = None, data: dict | None = None, json: dict | None = None) -> dict:
    headers: dict[str, str] = {"Authorization": f"Bearer {token}", "Version": version, "Accept": "application/json"}

    response = requests.request(method, f"{GHL_BASE_URL}{path}", headers=headers, timeout=REQUEST_TIMEOUT, params=params, data=data, json=json)

    if(response.status_code >= 400):
        raise ValueError(f"{response.status_code} {response.text[:300]}")

    return response.json()


#PROVIDER APP

#the apps tokens for an install code or a refresh token, a refused one raises with what ghl said
def token_request(fields: dict[str, str]) -> dict:
    form: dict[str, str] = {"client_id": GHL_APP_CLIENT_ID, "client_secret": GHL_APP_CLIENT_SECRET, "user_type": "Location"}

    for key, value in fields.items():
        form[key] = value

    response = requests.post(f"{GHL_BASE_URL}/oauth/token", data=form, headers={"Accept": "application/json"}, timeout=REQUEST_TIMEOUT)

    if(response.status_code >= 400):
        raise ValueError(f"{response.status_code} {response.text[:300]}")

    return response.json()

#the new access token goes on file with its fresh refresh token, the old one is dead now
def save_app_tokens(answer: dict) -> str:
    expires_at: float = time.time() + float(answer.get("expires_in", 0))

    log.write_info(APP_TOKENS_KEY, [answer["access_token"], answer["refresh_token"], str(expires_at)], APP_TOKEN_FIELDS)

    return answer["access_token"]

#an agency install hands back an agency token, which trades for the shops sub account tokens
def location_token(agency_answer: dict) -> dict:
    form: dict[str, str] = {"companyId": agency_answer.get("companyId", ""), "locationId": GHL_LOCATION_ID}

    return ghl_request("post", "/oauth/locationToken", OAUTH_VERSION, token=agency_answer["access_token"], data=form)

#the install code from ghl, only an install on the shops own sub account goes on file
def connect_app(code: str, redirect_uri: str) -> None:
    answer: dict = token_request({"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri})

    #an agency admins install is for the agency, so it gets traded for the shops sub account
    if(answer.get("userType") == "Company"):
        answer = location_token(answer)

    if(answer.get("locationId") != GHL_LOCATION_ID):
        raise ValueError(f"the app was installed on {answer.get('locationId')}, not the shop's sub-account")

    save_app_tokens(answer)

#the apps access token, refreshed first when its about to run out
def app_token() -> str:
    with TOKEN_LOCK:
        tokens: dict[str, str] = log.read_info(APP_TOKENS_KEY)

        if(not tokens.get("refresh_token")):
            raise ValueError("the ghl app was never installed on the shop's sub-account")

        if(time.time() < float(tokens.get("expires_at", "0")) - TOKEN_MARGIN_SECONDS):
            return tokens["access_token"]

        answer: dict = token_request({"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]})

        return save_app_tokens(answer)

#ghl shows the text he sent as delivered or failed, failed with the reason why
def mark_status(message_id: str, delivered: bool, reason: str = "") -> None:
    status: dict = {"status": "delivered"}

    if(not delivered):
        status = {"status": "failed", "error": {"code": "1", "type": "saas", "message": reason}}

    ghl_request("put", f"/conversations/messages/{message_id}/status", CONVERSATIONS_VERSION, token=app_token(), json=status)


#CONTACTS

#nothing when ghl has no contact on that number or email
def find_contact(id: str) -> str | None:
    if("@" in id):
        search_field: str = "email"
    else:
        search_field = "number"

    found: dict = ghl_request("get", "/contacts/search/duplicate", CONTACTS_VERSION, params={"locationId": GHL_LOCATION_ID, search_field: id})

    contact: dict | None = found.get("contact")

    if(contact is None):
        return None

    return contact["id"]

#a customer ghl never had gets a contact on the number or email they text from
def make_contact(id: str) -> str:
    if("@" in id):
        contact_field: str = "email"
    else:
        contact_field = "phone"

    made: dict = ghl_request("post", "/contacts/", CONTACTS_VERSION, json={"locationId": GHL_LOCATION_ID, contact_field: id})

    return made["contact"]["id"]

#there ghl contact, made the first time someone new texts in or gets a text from the system
def contact_id(id: str) -> str:
    found: str | None = find_contact(id)

    if(found is None):
        return make_contact(id)

    return found


#LOGGING

#logs a text, pics and time on the apps token, the inbound route so ghl never texts them twice
def log_text(contact: str, text_entry: tuple, direction: str) -> None:
    text: str = text_entry[0]

    pics: list[str] = text_entry[1]

    logged_at: float = text_entry[2]

    message: dict = {"type": "Custom", "conversationProviderId": GHL_PROVIDER_ID, "contactId": contact, "message": text, "direction": direction, "date": datetime.fromtimestamp(logged_at, timezone.utc).isoformat()}

    if(len(pics) > 0):
        message["attachments"] = pics

    ghl_request("post", "/conversations/messages/inbound", CONVERSATIONS_VERSION, token=app_token(), json=message)

#one contact lookup, then each text alone so one refusal never sinks the rest, failures just print
def write_texts(id: str, texts: list[tuple], direction: str) -> None:
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

#sent texts go to ghl off the reply path, ghl never gets to slow down or break a reply
def log_sent(id: str, sent: list[tuple]) -> None:
    if(len(sent) == 0):
        return

    WORKER.submit(write_texts, id, sent, OUTBOUND)

#where each pic or video they sent lives, blooio puts the url on each attachment
def attachment_urls(attachments: list | None) -> list[str]:
    urls: list[str] = []

    if(not attachments):
        attachments = []

    for attachment in attachments:
        if(isinstance(attachment, str)):
            urls.append(attachment)
        elif(isinstance(attachment, dict) and attachment.get("url")):
            urls.append(attachment["url"])

    return urls

#there text goes to ghl off the webhook, on the reply worker so it all reads in order
def log_received(id: str, text: str | None, attachments: list | None) -> None:
    pics: list[str] = attachment_urls(attachments)

    if(not text):
        text = ""

    #nothing to show, like a delivery with no text and no pic
    if(text.strip() == "" and len(pics) == 0):
        return

    WORKER.submit(write_texts, id, [(text, pics, time.time())], INBOUND)


#SMS

#one text from the shops default ghl number, which logs itself, a refused one raises
def send_sms(contact: str, text: str) -> None:
    ghl_request("post", "/conversations/messages", CONVERSATIONS_VERSION, json={"type": "SMS", "contactId": contact, "message": text})

#everything ghl has on the contact, like there first name and whether they texted STOP
def contact_details(contact: str) -> dict:
    answer: dict = ghl_request("get", f"/contacts/{contact}", CONTACTS_VERSION)

    contact_found: dict | None = answer.get("contact")

    if(not contact_found):
        contact_found = {}

    return contact_found

#they texted STOP, so ghls do not disturb is on for texts or everything, no sms goes out
def sms_stopped(details: dict) -> bool:
    if(details.get("dnd") is True):
        return True

    dnd_settings: dict | None = details.get("dndSettings")

    if(not dnd_settings):
        dnd_settings = {}

    sms_setting: dict | None = dnd_settings.get("SMS")

    if(not sms_setting):
        sms_setting = {}

    return sms_setting.get("status") in STOP_STATUSES
