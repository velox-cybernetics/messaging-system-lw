#**********IMPORTS**********
#the env keys, the one background worker, the clock each text is stamped with, the shape a sent text is logged in, and web requests that log each text in the shop's ghl
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import TypeAlias

import requests
from dotenv import load_dotenv



#**********GLOBALS**********
#the shop's ghl sub-account every text the bot sends gets logged in, and the worker that logs them


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
#one text that went out: what it said, the pics it carried, and when it went out in seconds
SENT: TypeAlias = tuple[str, list[str], float]


#WORKER
#one worker logs everything in the order it went out, so a slow call never puts their texts out of order
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
#their contact in ghl, made the first time the bot texts someone ghl doesn't have yet
def contact_id(id: str) -> str:
    found: str | None = find_contact(id)

    if(found is None):
        return make_contact(id)

    return found



#**********LOGGING**********
#every text the bot sends a customer over blooio goes in their conversation in ghl, since ghl never sees blooio


#LOG TEXT
#one text goes in their conversation as one the shop sent, with its pics and the moment it went out
#the inbound route only adds it to the conversation, sending it through ghl would text them a second time
def log_text(contact: str, sent_text: SENT) -> None:
    text, pics, sent_at = sent_text

    message: dict = {"type": "SMS", "contactId": contact, "message": text, "direction": "outbound", "date": datetime.fromtimestamp(sent_at, timezone.utc).isoformat()}

    if(len(pics) > 0):
        message["attachments"] = pics

    ghl_request("post", "/conversations/messages/inbound", CONVERSATIONS_VERSION, json=message)


#WRITE SENT
#their contact is found once, then each text goes in on its own, so one ghl refuses never keeps the rest out
#a failure is only printed, the customer already got the texts
def write_sent(id: str, sent: list[SENT]) -> None:
    try:
        contact: str = contact_id(id)

    except Exception as error:
        print(f"[GHL] contact for {id} failed, so {len(sent)} sent texts never got logged: {error}")

        return

    for sent_text in sent:
        try:
            log_text(contact, sent_text)

        except Exception as error:
            print(f"[GHL] logging a sent text to {id} failed: {error}")


#LOG SENT
#the texts a customer got go to ghl off the reply path, so ghl can never slow down or break a reply
def log_sent(id: str, sent: list[SENT]) -> None:
    if(len(sent) == 0):
        return

    WORKER.submit(write_sent, id, sent)
