#IMPORTS

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


#GLOBALS

load_dotenv()

#no docs or openapi pages, nobody gets a free map of the webhook
APP = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#where the dashboards send box posts, the api send file on the other end
TEXT_PATH: str = "/dashboard/text"

#same secret in render and vercel, unset just means the dashboard can't text yet
DASH_SEND_SECRET: str = os.getenv("DASH_SEND_SECRET", "")

#same cap as the dashboards text box, a novel can go in an email
TEXT_MAX: int = 2000


#WEBHOOK SAFETY

#compare_digest so a guess never learns how close it got
def from_dashboard(authorization: str) -> bool:
    return hmac.compare_digest(authorization.encode(), f"Bearer {DASH_SEND_SECRET}".encode())

#the id and the text out of the body, none when it isn't json or either one is missing
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


#SENDING

#true when blooio took it, a text that never reached them never goes on file either
def send_as_hazel(id: str, text: str) -> bool:
    if(not senders.send_dashboard_text(id, text)):
        return False

    replies.write_dashboard_text(id, text)

    print(f"DASHBOARD TEXT SENT to {id} as hazel, on file like she wrote it: {text}")

    return True


#DASHBOARD WEBHOOK

#the dashboard posts an id and a text with its secret, the system sends it unless its mid reply
async def dashboard_hook(request: Request):
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

    id: str = fields[0]

    text: str = fields[1]

    #the system is mid reply for them, so his text bounces instead of landing in the middle
    if(customer_lock(id).locked()):
        print(f"DASHBOARD TEXT BOUNCED: hazel is writing {id} a reply right now, so the owner sends his once it's out")

        return JSONResponse({"error": "Hazel's writing them a reply right now, send yours once it's out."}, status_code=409)

    #their lock stays held till its on file, so a batch closing right now reads it in there history
    async with customer_lock(id):
        sent: bool = await asyncio.to_thread(send_as_hazel, id, text)

    if(not sent):
        return JSONResponse({"error": "Blooio refused it."}, status_code=502)

    return {"status": "sent"}


#ROUTES

APP.add_api_route(TEXT_PATH, dashboard_hook, methods=["POST"], response_model=None)


#RUN

#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
