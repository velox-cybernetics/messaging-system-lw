#**********IMPORTS**********
#python's async tools, the web server tools, the journal of waiting messages, the dashboard's heartbeat, the follow ups and the seven webhook servers that get joined into one
import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.routing import Route

from helpers.state import dashboard
from helpers.state import journal
from servers import blooio
from servers import dashboard_texts
from servers import ghl_provider
from servers import instagram
from servers import messenger
from servers import meta_form
from servers import website_form
from src import followup



#**********REPLAY**********
#every message still waiting on its reply when the server last stopped goes back in its batch, so a restart never loses one


#QUEUES
#where each channel's messages wait for their batch, by the channel their journal is under
QUEUES: dict[str, Callable[[str, list, str], None]] = {"blooio": blooio.queue_message, "ig": instagram.queue_message, "messenger": messenger.queue_message, "meta-form": meta_form.queue_fields, "website-form": website_form.queue_fields}


#REPLAY WAITING
#the journal gets read off the event loop, then each message goes back in its batch in the order it came in, keeping its entry so its batch clears it
async def replay_waiting() -> None:
    waiting: list[journal.WAITING] = await asyncio.to_thread(journal.pending)

    for conversation in waiting:
        queue: Callable[[str, list, str], None] | None = QUEUES.get(conversation[0])

        if(queue is None):
            print(f"REPLAY SKIPPED: no server takes {conversation[0]} messages anymore")

            continue

        print(f"REPLAY: {len(conversation[2])} message(s) from {conversation[1]} on {conversation[0]} were waiting when the server stopped, so they go back in their batch")

        for waiting_message in conversation[2]:
            queue(conversation[1], waiting_message[1], waiting_message[0])



#**********HEARTBEAT**********
#while the server runs, the dashboard hears from it every few minutes, so the overview can show whether the bot is up


#HEARTBEAT
#the first check in goes out the moment the server starts
async def heartbeat() -> None:
    while(True):
        dashboard.beat()

        await asyncio.sleep(dashboard.BEAT_SECONDS)



#**********FOLLOW UPS**********
#every night the quiet conversations get picked, right before the morning's send anyone the night missed gets checked, then each one picked gets its follow up


#DAILY
#runs the job every day at the hour and minute in the shop's time, in a worker thread so the webhooks never wait on it
async def daily(hour: int, minute: int, job: Callable[[], None]) -> None:
    while(True):
        await asyncio.sleep(followup.seconds_until(hour, minute))

        #a run that breaks is only printed, the next day's run still goes
        try:
            await asyncio.to_thread(job)

        except Exception as error:
            print(f"FOLLOW UP ERROR: {job.__name__} failed, {error}")



#**********LIFESPAN**********
#what starts with the server and stops with it


#LIFESPAN
#the messages a restart left waiting go back in their batches first, then the heartbeat and the follow ups start with the server and stop with it
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await replay_waiting()

    beating: asyncio.Task = asyncio.create_task(heartbeat())

    picking: asyncio.Task = asyncio.create_task(daily(followup.PREP_HOUR, 0, followup.prep_followups))

    recheck_time: tuple[int, int] = followup.recheck_time()

    rechecking: asyncio.Task = asyncio.create_task(daily(recheck_time[0], recheck_time[1], followup.recheck_followups))

    following_up: asyncio.Task = asyncio.create_task(daily(followup.FOLLOWUP_HOUR, 0, followup.send_followups))

    yield

    beating.cancel()

    picking.cancel()

    rechecking.cancel()

    following_up.cancel()



#**********GLOBALS**********
#the one web server every webhook comes in through


#APP
#one app serving every webhook on port 8000, so a single ngrok http 8000 tunnel covers blooio, instagram, messenger, both quote forms, ghl and the dashboard's texts
APP: FastAPI = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


#HEALTH CHECK
#render pings this to know the service is up
@APP.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}



#**********WEBHOOK ROUTES**********
#finds each server's webhook paths and points them at that server


#WEBHOOK PATHS
#every path a server answers webhooks on, each one once even when it takes more than one method
def webhook_paths(server_app: FastAPI) -> list[str]:
    paths: list[str] = []

    for route in server_app.routes:
        if(isinstance(route, APIRoute) and route.path not in paths):
            paths.append(route.path)

    return paths


#ADD ROUTES
#each webhook path is handed to the whole server it came from, so that server's own middleware still runs on it
def add_webhook_routes() -> None:
    for server in (blooio, instagram, messenger, meta_form, website_form, ghl_provider, dashboard_texts):
        for path in webhook_paths(server.APP):
            APP.router.routes.append(Route(path, endpoint=server.APP))



#**********ROUTE SETUP**********
#joins every webhook into the one app before it starts taking requests


#ROUTES
add_webhook_routes()



#**********RUN**********
#starts the joined server when the file is run directly


#RUN SERVER
#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
