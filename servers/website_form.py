#**********IMPORTS**********
#python's async tools, the web server, the dashboard, the journal that keeps every waiting form, and the core that answers each quote form
import asyncio

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from src.core import core
from helpers.channels.senders import OWNER_NUMBER
from helpers.state import dashboard
from helpers.state import journal
from helpers.terminal import prints



#**********GLOBALS**********
#the web server for the website's quote form and the memory holding each form's fields


#LOAD ENV
load_dotenv()


#APP
APP: FastAPI = FastAPI()


#FIELD BATCHES
#each id's countdown till their form gets answered
BATCH_COUNTDOWNS: dict[str, asyncio.Task] = {}

#the fields each id sent that wait on that countdown
FIELD_BATCHES: dict[str, list] = {}

#each of those forms' entries in the journal, cleared once their batch is answered
BATCH_ENTRIES: dict[str, list[str]] = {}



#**********TIMINGS**********
#how long a form's fields wait for more before they get answered


#BATCH TIME
QUOTE_FORM_BATCH_TIME: int = 12



#**********FORM FIELDS**********
#reads what the customer typed on the form


#FORM LINES
#the website's workflow sends the contact as json, so their name, email, phone and vehicle go in as the same labeled lines every quote form is read by, the rest of what it sends stays out
def form_lines(data: dict) -> list[str]:
    #the vehicle they typed comes in the custom data the workflow adds to its webhook
    vehicle: str = (data.get("customData") or {}).get("vehicle") or ""

    #a field they left empty comes in empty or not at all, either way its line stays empty
    return [f"First name: {data.get('first_name') or ''}", f"Last name: {data.get('last_name') or ''}", f"Email: {data.get('email') or ''}", f"Phone: {data.get('phone') or ''}", f"Vehicle Year/Make/Model: {vehicle}"]


#FORM PHONE
#the reply goes out over blooio, so core gets the number the customer typed on the form, not the webhook id
def form_phone(fields: list[str]) -> str:
    phone: str = ""

    for field in fields:
        if(field.lower().startswith("phone:")):
            phone = field[len("phone:"):].strip()

    return phone



#**********FORM BATCHING**********
#holds a form's fields until they stop coming, then answers them all on the number they typed


#BATCH
#waits out the countdown, then answers every field on the number they typed, or on the webhook id when there is none
async def batch(id: str) -> None:
    await asyncio.sleep(QUOTE_FORM_BATCH_TIME)

    current_message_batch: list = FIELD_BATCHES[id]

    current_entries: list[str] = BATCH_ENTRIES[id]

    del BATCH_COUNTDOWNS[id]

    del FIELD_BATCHES[id]

    del BATCH_ENTRIES[id]

    #everything this batch prints comes out in one block once its reply went out or it failed
    with prints.held():
        print("INCOMING MESSAGE BATCH FROM on Quote form")

        print(f"Message batch: {current_message_batch}")

        print()

        reply_number: str = form_phone(current_message_batch)

        #no number typed on the form, so the reply goes to the webhook id
        if(not reply_number):
            reply_number = id

        #the owner's number only ever answers color checks, so a form typed with it is never a lead, it gets no reply and never shows in the dashboard
        if(reply_number == OWNER_NUMBER):
            print(f"OWNER FORM DROPPED: {reply_number} is the owner's number, which only answers color checks, so its form gets no reply and no dashboard")

        #the form shows in the dashboard, and only a lead switched on there gets answered
        #core runs in its own worker thread, so the server keeps taking webhooks while it works
        elif(await asyncio.to_thread(dashboard.take_in, reply_number, "website-form", current_message_batch)):
            await asyncio.to_thread(core, current_message_batch, reply_number, "website-form")

        #answered or dropped, so its fields come off the journal and a restart never answers them again
        await asyncio.to_thread(journal.clear, "website-form", id, current_entries)


#QUEUE FIELDS
#every new form restarts the id's countdown, so all its fields go out together once they stop sending, journal_entry is where the form is on file
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



#**********WEBSITE FORM WEBHOOK**********
#takes each quote form the website's workflow sends and writes it out as its fields


#WEBSITE FORM HOOK
#every quote form the website sends comes in here as a POST from its workflow, it waits under the contact's id and the reply goes to the number they typed
@APP.post("/quote_website/webhook")
async def website_form_hook(request: Request) -> dict:
    data: dict = await request.json()

    id: str = data["contact_id"]

    fields: list[str] = form_lines(data)

    #on file before it waits in the batch, so a restart while it waits never loses it
    journal_entry: str = await asyncio.to_thread(journal.save, "website-form", id, fields)

    queue_fields(id, fields, journal_entry)

    return {"status": "ok"}



#**********RUN**********
#starts this webhook server on its own when the file is run directly


#RUN SERVER
#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
