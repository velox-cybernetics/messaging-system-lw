#IMPORTS

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


#GLOBALS

#every calendar date and drop off day is read in the shops own timezone
SHOP_TIMEZONE = ZoneInfo("America/Denver")

#open drop off days in the next 3 weeks go out 3 at a time, soonest first, starting tomorrow
DATES_TO_PROPOSE: int = 3

DAYS_TO_SEARCH: int = 21

#each turned down set means a fresh search, this many before a person steps in
MAX_RESEARCHES: int = 3

#film for a wrap or colored ppf takes 2 to 5 days to show up, so drop off waits this long
COLOR_LEAD_DAYS: int = 5

#jobs per week by the week the car drops off, a rough draft to tune later
WEEKLY_LIMITS: dict[str, float] = {"tint": 3, "wrap": 3, "full_body_ppf": 1}

#the weekly limit each service counts toward, a front end shares the full body ppf limit
SLOT_NAMES: dict[str, str] = {"tint": "tint", "wrap": "wrap", "full_body_ppf": "full_body_ppf", "front_ppf": "full_body_ppf"}

#how much of its weekly limit each service takes, 2 front ends fill the same spot as 1 full body
SLOT_UNITS: dict[str, float] = {"tint": 1, "wrap": 1, "full_body_ppf": 1, "front_ppf": 0.5}

#monday is 0, tint drops off tuesday through friday, everything else monday through thursday
DROP_OFF_DAYS: dict[str, list[int]] = {"tint": [1, 2, 3, 4], "wrap": [0, 1, 2, 3], "full_body_ppf": [0, 1, 2, 3], "front_ppf": [0, 1, 2, 3], "coating": [0, 1, 2, 3], "add_on": [0, 1, 2, 3]}


#WEEKS

#the monday of the week a day is in, every week counts from its monday
def week_start(day):
    return day - timedelta(days=day.weekday())

#a week with nothing used up from any weekly limit yet
def empty_week() -> dict[str, float]:
    return {"tint": 0, "wrap": 0, "full_body_ppf": 0}


#JOB TYPES

#whether a service is a front end or full body ppf, empty when its not ppf
def ppf_type(name: str) -> str:
    if("ppf" not in name and "paint protection" not in name and "clear bra" not in name):
        return ""

    #the windshield skin is a small job like the front end, so it takes a front ends spot
    if("front" in name or "windshield" in name):
        return "front_ppf"

    return "full_body_ppf"

#the kind of job a service name is, which sets its drop off days and its weekly limit
def service_type(service_name: str) -> str:
    name: str = service_name.lower()

    #tint goes first, so ceramic tint never gets mistaken for a ceramic coating
    if("tint" in name):
        return "tint"

    #a coating on a wrap or ppf says wrap or ppf too, so coating gets checked before them
    if("coating" in name):
        return "coating"

    ppf: str = ppf_type(name)

    if(ppf != ""):
        return ppf

    if("wrap" in name):
        return "wrap"

    #anything else, like blacked out emblems, rides along with the job its added to
    return "add_on"

#a wrap or colored ppf waits on its film, so its first open day gets pushed out
def color_pick_job(service_names: list[str]) -> bool:
    for service_name in service_names:
        name: str = service_name.lower()

        if(service_type(service_name) == "wrap" or ("color" in name and ppf_type(name) != "")):
            return True

    return False

#open days only care about the kinds of job and the film wait, never a color or a price
def job_kinds(service_names: list[str]) -> list[str]:
    kinds: list[str] = []

    for service_name in service_names:
        kind: str = service_type(service_name)

        if(kind not in kinds):
            kinds.append(kind)

    #a film wait moves the first open day too, so it counts as its own kind
    if(color_pick_job(service_names)):
        kinds.append("color_pick")

    return sorted(kinds)


#WEEK USAGE

#the day a calendar event is on, None when it has no start date
def event_date(event: dict):
    start: dict = event.get("start", {})

    #an all day event only has a date
    if("date" in start):
        return date.fromisoformat(start["date"])

    #a timed event gets read in the shops own timezone
    if("dateTime" in start):
        start_time = datetime.fromisoformat(start["dateTime"])

        return start_time.astimezone(SHOP_TIMEZONE).date()

    return None

#every job a calendar events title names that counts toward a weekly limit
def title_service_types(title: str) -> list[str]:
    name: str = title.lower()

    service_types: list[str] = []

    #one event can hold a few jobs, like a wrap plus tint, so every service in the title counts
    if("tint" in name):
        service_types.append("tint")

    ppf: str = ppf_type(name)

    if(ppf != ""):
        service_types.append(ppf)

    if("wrap" in name):
        service_types.append("wrap")

    return service_types

#how much of each weekly limit is used up, by the monday of each week with jobs on the calendar
def week_usage(events: list[dict]) -> dict:
    usage: dict = {}

    for event in events:
        day = event_date(event)

        if(day is None):
            continue

        monday = week_start(day)

        if(monday not in usage):
            usage[monday] = empty_week()

        for service in title_service_types(event.get("summary", "")):
            slot: str = SLOT_NAMES[service]

            usage[monday][slot] += SLOT_UNITS[service]

    return usage


#OPEN DATES

#start and end of the calendar stretch to read, whole weeks so a job early in a week still counts
def calendar_window(today) -> tuple:
    first_monday = week_start(today)

    last_day = today + timedelta(days=DAYS_TO_SEARCH)

    end_monday = week_start(last_day) + timedelta(days=7)

    window_start = datetime.combine(first_monday, time(0, 0), SHOP_TIMEZONE)

    window_end = datetime.combine(end_monday, time(0, 0), SHOP_TIMEZONE)

    return (window_start, window_end)

#every open day in the next 3 weeks, soonest first, so a set to offer can be picked from them
def open_drop_off_dates(service_names: list[str], events: list[dict], today) -> list:
    open_dates: list = []

    #nothing confirmed means theres no job to fit anywhere
    if(len(service_names) == 0):
        return open_dates

    usage: dict = week_usage(events)

    #what this job takes from each weekly limit
    job_units: dict[str, float] = empty_week()

    job_types: list[str] = []

    for service_name in service_names:
        service: str = service_type(service_name)

        #tint on the sides and the windshield is still one tint job
        if(service in job_types):
            continue

        job_types.append(service)

        if(service in SLOT_NAMES):
            job_units[SLOT_NAMES[service]] += SLOT_UNITS[service]

    #a film wait pushes the first day out, everything else can go the next day
    first_day: int = 1

    if(color_pick_job(service_names)):
        first_day = COLOR_LEAD_DAYS

    for day_number in range(first_day, DAYS_TO_SEARCH + 1):
        day = today + timedelta(days=day_number)

        #the drop off day has to work for every service in the job
        day_allowed: bool = True

        for service in job_types:
            if(day.weekday() not in DROP_OFF_DAYS[service]):
                day_allowed = False

        if(not day_allowed):
            continue

        week_used: dict[str, float] = usage.get(week_start(day), empty_week())

        #it only fits when every limit it touches still has room that week
        job_fits: bool = True

        for slot, weekly_limit in WEEKLY_LIMITS.items():
            if(job_units[slot] > 0 and week_used[slot] + job_units[slot] > weekly_limit):
                job_fits = False

        if(not job_fits):
            continue

        open_dates.append(day)

    return open_dates
