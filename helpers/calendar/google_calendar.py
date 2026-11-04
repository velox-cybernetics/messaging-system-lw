#**********IMPORTS**********
#the env keys, dates, url safe text, and the google login that reads the shop calendar
import os
from datetime import datetime
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account



#**********GLOBALS**********
#which calendar gets read, with what login, and how long to wait on google


#LOAD ENV
#reads the .env file, so the calendar keys below can be found
load_dotenv()


#GOOGLE CALENDAR
#the key of the service account the shop calendar is shared with, and that calendar's id
GOOGLE_SERVICE_ACCOUNT_FILE: str | None = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

GOOGLE_CALENDAR_ID: str | None = os.getenv("GOOGLE_CALENDAR_ID")


#CALENDAR ACCESS
#read only, the booking date step only looks at what's already on the schedule
CALENDAR_SCOPES: list[str] = ["https://www.googleapis.com/auth/calendar.readonly"]

#where google's calendar api lives
CALENDAR_URL: str = "https://www.googleapis.com/calendar/v3/calendars"

#seconds to wait on google before giving up
CALENDAR_TIMEOUT: int = 10

#3 weeks of jobs never come close to this, so the events come back in one page
CALENDAR_MAX_EVENTS: int = 2500



#**********READ CALENDAR**********
#pulls every job already on the shop calendar between two dates, so open drop off days can be found


#READ EVENTS
#every event on the shop calendar between the two dates, as google sends them back
def read_events(window_start: datetime, window_end: datetime) -> list[dict]:
    #without the key or the calendar id nothing can be read, so it says what's missing instead of failing vaguely
    if(GOOGLE_SERVICE_ACCOUNT_FILE is None or GOOGLE_CALENDAR_ID is None):
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_CALENDAR_ID have to be set in .env")

    credentials: service_account.Credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE, scopes=CALENDAR_SCOPES)

    session: AuthorizedSession = AuthorizedSession(credentials)

    #every event in the window, a repeating one comes back once for each day it's on
    params: dict = {"timeMin": window_start.isoformat(), "timeMax": window_end.isoformat(), "singleEvents": "true", "orderBy": "startTime", "maxResults": CALENDAR_MAX_EVENTS}

    events_url: str = f"{CALENDAR_URL}/{quote(GOOGLE_CALENDAR_ID)}/events"

    response: requests.Response = session.get(events_url, params=params, timeout=CALENDAR_TIMEOUT)

    response.raise_for_status()

    result: dict = response.json()

    events: list[dict] = result.get("items", [])

    print(f"CALENDAR EVENTS: {len(events)}")

    return events
