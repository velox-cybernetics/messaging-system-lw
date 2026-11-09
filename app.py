#IMPORTS

import asyncio
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


#REPLAY

#where each channels messages wait for there batch, keyed by the channel their journal is under
QUEUES: dict = {"blooio": blooio.queue_message, "ig": instagram.queue_message, "messenger": messenger.queue_message, "meta-form": meta_form.queue_fields, "website-form": website_form.queue_fields}

#a restarts leftovers go back in there batch in arrival order, the batch clears the journal entry
async def replay_waiting() -> None:
    waiting: list[tuple] = await asyncio.to_thread(journal.pending)

    for conversation in waiting:
        queue = QUEUES.get(conversation[0])

        if(queue is None):
            print(f"REPLAY SKIPPED: no server takes {conversation[0]} messages anymore")

            continue

        print(f"REPLAY: {len(conversation[2])} message(s) from {conversation[1]} on {conversation[0]} were waiting when the server stopped, so they go back in their batch")

        for waiting_message in conversation[2]:
            queue(conversation[1], waiting_message[1], waiting_message[0])


#HEARTBEAT

#the first check in goes out the moment the server starts
async def heartbeat() -> None:
    while(True):
        dashboard.beat()

        await asyncio.sleep(dashboard.BEAT_SECONDS)


#FOLLOW UPS

#runs the job daily at shop time, in a worker thread so the webhooks never wait on it
async def daily(hour: int, minute: int, job) -> None:
    while(True):
        await asyncio.sleep(followup.seconds_until(hour, minute))

        #a run that breaks only gets printed, tomorrows run still goes
        try:
            await asyncio.to_thread(job)
        except Exception as error:
            print(f"FOLLOW UP ERROR: {job.__name__} failed, {error}")


#LIFESPAN

#replays the waiting messages first, then heartbeat and follow ups live and die with the server
@asynccontextmanager
async def lifespan(app):
    await replay_waiting()

    beating = asyncio.create_task(heartbeat())

    picking = asyncio.create_task(daily(followup.PREP_HOUR, 0, followup.prep_followups))

    recheck_time: tuple[int, int] = followup.recheck_time()

    rechecking = asyncio.create_task(daily(recheck_time[0], recheck_time[1], followup.recheck_followups))

    following_up = asyncio.create_task(daily(followup.FOLLOWUP_HOUR, 0, followup.send_followups))

    yield

    beating.cancel()

    picking.cancel()

    rechecking.cancel()

    following_up.cancel()


#GLOBALS

#one app on port 8000 for every webhook, so a single ngrok tunnel covers the lot
APP = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

#render pings this to know the service is up
async def healthz() -> dict:
    return {"status": "ok"}


#WEBHOOK ROUTES

#every path a server answers webhooks on, once each even when it takes more than one method
def webhook_paths(server_app) -> list[str]:
    paths: list[str] = []

    for route in server_app.routes:
        if(isinstance(route, APIRoute) and route.path not in paths):
            paths.append(route.path)

    return paths

#each path goes to the whole server it came from, so that servers own middleware still runs
def add_webhook_routes() -> None:
    for server in (blooio, instagram, messenger, meta_form, website_form, ghl_provider, dashboard_texts):
        for path in webhook_paths(server.APP):
            APP.router.routes.append(Route(path, endpoint=server.APP))


#ROUTES

#healthz first, then every servers webhooks get joined in
APP.add_api_route("/healthz", healthz, methods=["GET"])

add_webhook_routes()


#RUN

#uvicorn only prints its warnings and errors, so the terminal is just the held blocks
if(__name__ == "__main__"):
    uvicorn.run(APP, port=8000, log_level="warning")
