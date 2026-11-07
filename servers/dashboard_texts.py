#**********IMPORTS**********
#python's tools, the web server, the env, the sender and the memory that make his text hazel's, and blooio's capped body read and customer locks
import asyncio
import hmac
import json
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from helpers.channels import replies
from helpers.channels import senders
from servers.blooio import customer_lock, read_body



#**********GLOBALS**********
#the web server the dashboard hands every text the owner types to, so it goes out as hazel and not some guy on a laptop


#LOAD ENV
load_dotenv()


#APP
#no /docs, /redoc, or /openapi.json, so nobody can pull up a map of the webhook
APP: FastAPI = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


#TEXT PATH
#where the dashboard's send box posts, api/send.ts on the other end
TEXT_PATH: str = "/dashboard/text"


#DASHBOARD SECRET
#the dashboard's bearer token, the same DASH_SEND_SECRET in render and vercel, unset just means the dashboard can't text yet
DASH_SEND_SECRET: str = os.getenv("DASH_SEND_SECRET", "")


#TEXT MAX
#same cap as the dashboard's text box, a novel can go in an email
TEXT_MAX: int = 2000



#**********WEBHOOK SAFETY**********
#only the dashboard gets to put words in hazel's mouth


#FROM DASHBOARD
#compare_digest so a guess never learns how close it got
def from_dashboard(authorization: str) -> bool:
    return hmac.compare_digest(authorization.encode(), f"Bearer {DASH_SEND_SECRET}".encode())


#TEXT FIELDS
#the id and the text out of the body, None when it isn't json or either one is missing
def text_fields(body: bytes) -> tuple[str, str] | None:
    try:
        data: object = json.loads(body)

    except ValueError:
        return None

    if(not isinstance(data, dict)):
        return None

    id: object = data.get("id")

    text: object = data.get("text")

    if(not isinstance(id, str) or not isinstance(text, str) or id == ""):
        return None

    #trimmed the way the dashboard trims it, so the cap counts the same on both ends
    trimmed: str = text.strip()

    if(trimmed == "" or len(trimmed) > TEXT_MAX):
        return None

    return (id, trimmed)



#**********SENDING**********
#his text goes out as hazel's and goes on file like she wrote it, and the bot stays on for them since that's the whole point


#SEND AS HAZEL
#True when blooio took it, a text that never reached them never goes on file either
def send_as_hazel(id: str, text: str) -> bool:
    if(not senders.send_dashboard_text(id, text)):
        return False

    replies.write_dashboard_text(id, text)

    print(f"DASHBOARD TEXT SENT to {id} as hazel, on file like she wrote it: {text}")

    return True



#**********DASHBOARD WEBHOOK**********
#every text the owner sends from the dashboard comes in here, one at a time per customer like everything else


#DASHBOARD HOOK
#the dashboard posts the id and the text with its secret, and hazel sends it unless she's mid-reply for them
@APP.post(TEXT_PATH, response_model=None)
async def dashboard_hook(request: Request) -> dict | JSONResponse:
    if(not DASH_SEND_SECRET):
        print("DASHBOARD TEXT REFUSED: DASH_SEND_SECRET is not set, so the dashboard can't text anyone yet")

        return JSONResponse({"error": "DASH_SEND_SECRET isn't set on the system."}, status_code=503)

    if(not from_dashboard(request.headers.get("Authorization", ""))):
        print("DASHBOARD TEXT REJECTED: the secret is missing or wrong")

        return JSONResponse({"error": "unauthorized"}, status_code=401)

    body: bytes | None = await read_body(request)

    if(body is None):
        return JSONResponse({"error": "body too large"}, status_code=413)

    fields: tuple[str, str] | None = text_fields(body)

    if(fields is None):
        return JSONResponse({"error": f"Send the conversation id and a text of 1 to {TEXT_MAX} characters."}, status_code=400)

    id, text = fields

    #hazel's mid-reply for them, so his text bounces back instead of landing in the middle of hers
    if(customer_lock(id).locked()):
        print(f"DASHBOARD TEXT BOUNCED: hazel is writing {id} a reply right now, so the owner sends his once it's out")

        return JSONResponse({"error": "Hazel's writing them a reply right now, send yours once it's out."}, status_code=409)

    #their lock stays held till it's on file, so a batch closing right now reads it in their history
    async with customer_lock(id):
        sent: bool = await asyncio.to_thread(send_as_hazel, id, text)

    if(not sent):
        return JSONResponse({"error": "Blooio refused it."}, status_code=502)

    return {"status": "sent"}



#**********RUN**********
#starts this webhook server on its own when the file is run directly


#RUN SERVER
#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
