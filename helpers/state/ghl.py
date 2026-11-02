#**********IMPORTS**********
#the env keys, the one background worker, the clock each text is stamped with, the shape a text is logged in, and web requests that log each text in the shop's ghl
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import TypeAlias

import requests
from dotenv import load_dotenv



#**********GLOBALS**********
#the shop's ghl sub-account every text the bot sends or a customer sends in gets logged in, and the worker that logs them


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
#contacts and conversations each answer to their own version
CONTACTS_VERSION: str = "2021-07-28"

CONVERSATIONS_VERSION: str = "2021-04-15"


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



#**********REQUESTS**********
#every call to ghl goes out the same way


#GHL REQUEST
#the json ghl answered with, a refused call raises with its status and what ghl said, so the print shows why
def ghl_request(method: str, path: str, version: str, **options) -> dict:
    headers: dict[str, str] = {"Authorization": f"Bearer {GHL_API_KEY}", "Version": version, "Accept": "application/json"}

    response: requests.Response = requests.request(method, f"{GHL_BASE_URL}{path}", headers=headers, timeout=REQUEST_TIMEOUT, **options)

    if(response.status_code >= 400):
        raise ValueError(f"{response.status_code} {response.text[:300]}")

    return response.json()



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
#every text the bot sends a customer over blooio, and every text they send it there, goes in their conversation in ghl, since ghl never sees blooio


#LOG TEXT
#one text goes in their conversation, as one the shop sent or one they sent, with its pics and the moment it went out or came in
#the inbound route only adds it to the conversation, sending it through ghl would text them a second time
def log_text(contact: str, text_entry: SENT, direction: str) -> None:
    text, pics, logged_at = text_entry

    message: dict = {"type": "SMS", "contactId": contact, "message": text, "direction": direction, "date": datetime.fromtimestamp(logged_at, timezone.utc).isoformat()}

    if(len(pics) > 0):
        message["attachments"] = pics

    ghl_request("post", "/conversations/messages/inbound", CONVERSATIONS_VERSION, json=message)


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
