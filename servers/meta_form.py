#IMPORTS

import asyncio

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from src.core import core
from helpers.channels.senders import OWNER_NUMBER
from helpers.state import dashboard
from helpers.state import journal
from helpers.terminal import prints


#GLOBALS

load_dotenv()

APP = FastAPI()

#each ids countdown till their form gets answered
BATCH_COUNTDOWNS: dict = {}

#the fields each id sent that wait on that countdown
FIELD_BATCHES: dict[str, list] = {}

#each forms entries in the journal, cleared once there batch is answered
BATCH_ENTRIES: dict[str, list[str]] = {}


#TIMINGS

QUOTE_FORM_BATCH_TIME: int = 12


#FORM FIELDS

#metas contact json turned into the same labeled lines every quote form gets read by
def form_lines(data: dict) -> list[str]:
    services_needed: list = data.get("Services Needed")

    if(not services_needed):
        services_needed = []

    #every service they checked comes in a list, so they go in as one line
    services: str = ", ".join(services_needed)

    #the vehicle they typed rides in the custom data the workflow tacks on
    custom_data: dict = data.get("customData")

    if(not custom_data):
        custom_data = {}

    vehicle: str = custom_data.get("vehicle")

    if(not vehicle):
        vehicle = ""

    #a field they left empty comes in empty or not at all, either way its line stays empty
    full_name: str = data.get("full_name")

    if(not full_name):
        full_name = ""

    phone: str = data.get("phone")

    if(not phone):
        phone = ""

    return [f"Full name: {full_name}", f"Phone number: {phone}", f"Which service are you looking for? {services}", f"Vehicle Year/Make/Model: {vehicle}"]

#the number they typed on the form, since the reply goes over blooio and not to the webhook id
def form_phone(fields: list[str]) -> str:
    phone: str = ""

    for field in fields:
        if(field.lower().startswith("phone number:")):
            phone = field[len("phone number:"):].strip()

    return phone


#FORM BATCHING

#waits out the countdown, then answers the whole batch on the number they typed
async def batch(id: str) -> None:
    await asyncio.sleep(QUOTE_FORM_BATCH_TIME)

    current_message_batch: list = FIELD_BATCHES[id]

    current_entries: list[str] = BATCH_ENTRIES[id]

    del BATCH_COUNTDOWNS[id]

    del FIELD_BATCHES[id]

    del BATCH_ENTRIES[id]

    #everything this batch prints comes out in one block once its reply went out or it failed
    held_token = prints.hold()

    try:
        print("INCOMING MESSAGE BATCH FROM on Quote form")

        print(f"Message batch: {current_message_batch}")

        print()

        reply_number: str = form_phone(current_message_batch)

        #no number typed on the form, so the reply goes to the webhook id
        if(not reply_number):
            reply_number = id

        #the owners number only answers color checks, him filling a form is not a lead
        if(reply_number == OWNER_NUMBER):
            print(f"OWNER FORM DROPPED: {reply_number} is the owner's number, which only answers color checks, so its form gets no reply and no dashboard")
        elif(await asyncio.to_thread(dashboard.take_in, reply_number, "meta-form", current_message_batch)):
            #core gets its own thread so the server keeps taking webhooks while it thinks
            await asyncio.to_thread(core, current_message_batch, reply_number, "meta-form")

        #answered or dropped, its fields leave the journal so a restart never answers them twice
        await asyncio.to_thread(journal.clear, "meta-form", id, current_entries)
    finally:
        prints.release(held_token)

#every new form restarts the countdown, so all of an ids fields go out together
def queue_fields(id: str, fields: list[str], journal_entry: str) -> None:
    if(id not in BATCH_COUNTDOWNS):
        FIELD_BATCHES[id] = fields

        BATCH_ENTRIES[id] = [journal_entry]

        BATCH_COUNTDOWNS[id] = asyncio.create_task(batch(id))
    else:
        FIELD_BATCHES[id].extend(fields)

        BATCH_ENTRIES[id].append(journal_entry)

        BATCH_COUNTDOWNS[id].cancel()

        BATCH_COUNTDOWNS[id] = asyncio.create_task(batch(id))


#WEBHOOK

#every quote form off metas workflow lands here and waits under the contacts id
async def meta_form_hook(request: Request) -> dict:
    data: dict = await request.json()

    id: str = data["contact_id"]

    fields: list[str] = form_lines(data)

    #on file before it waits in the batch, so a restart while it waits never loses it
    journal_entry: str = await asyncio.to_thread(journal.save, "meta-form", id, fields)

    queue_fields(id, fields, journal_entry)

    return {"status": "ok"}


#ROUTES

APP.add_api_route("/quote_meta/webhook", meta_form_hook, methods=["POST"])


#RUN

#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
