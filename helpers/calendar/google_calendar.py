#IMPORTS

import os
from urllib.parse import quote

from dotenv import load_dotenv
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account


#GLOBALS

#pulls in the env file, so the calendar keys below can be found
load_dotenv()

#the key of the service account the shop calendar is shared with, and that calendars id
GOOGLE_SERVICE_ACCOUNT_FILE: str | None = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

GOOGLE_CALENDAR_ID: str | None = os.getenv("GOOGLE_CALENDAR_ID")

#read only, the booking date step only looks at whats already on the schedule
CALENDAR_SCOPES: list[str] = ["https://www.googleapis.com/auth/calendar.readonly"]

#where googles calendar api lives
CALENDAR_URL: str = "https://www.googleapis.com/calendar/v3/calendars"

#seconds to wait on google before giving up
CALENDAR_TIMEOUT: int = 10

#three weeks of jobs never come close to this, so the events come back in one page
CALENDAR_MAX_EVENTS: int = 2500


#READ CALENDAR

#every event on the shop calendar between the two dates, as google sends them back
def read_events(window_start, window_end) -> list[dict]:
    #no key or calendar id, so it names whats missing instead of failing vaguely
    if(GOOGLE_SERVICE_ACCOUNT_FILE is None or GOOGLE_CALENDAR_ID is None):
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_CALENDAR_ID have to be set in .env")

    credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE, scopes=CALENDAR_SCOPES)

    session = AuthorizedSession(credentials)

    #a repeating event comes back once for each day its on
    params: dict = {"timeMin": window_start.isoformat(), "timeMax": window_end.isoformat(), "singleEvents": "true", "orderBy": "startTime", "maxResults": CALENDAR_MAX_EVENTS}

    events_url: str = f"{CALENDAR_URL}/{quote(GOOGLE_CALENDAR_ID)}/events"

    response = session.get(events_url, params=params, timeout=CALENDAR_TIMEOUT)

    response.raise_for_status()

    result: dict = response.json()

    events: list[dict] = result.get("items", [])

    print(f"CALENDAR EVENTS: {len(events)}")

    return events
