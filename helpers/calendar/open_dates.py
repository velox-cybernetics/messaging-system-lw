#**********IMPORTS**********
#dates, times and the shop's timezone
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo



#**********GLOBALS**********
#the booking rules: how far ahead to look, how many jobs fit a week, which days cars drop off


#SHOP TIMEZONE
#every calendar date and drop off day is read in the shop's own timezone
SHOP_TIMEZONE: ZoneInfo = ZoneInfo("America/Denver")


#SEARCH LIMITS
#the open drop off days in the next 3 weeks get offered 3 at a time, soonest first, starting tomorrow
DATES_TO_PROPOSE: int = 3

DAYS_TO_SEARCH: int = 21

#each turned down set sends a new search for days not offered yet, at most this many before a person steps in
MAX_RESEARCHES: int = 3


#COLOR LEAD
#film for a wrap or colored ppf takes 2 to 5 days to come in after the color is picked, so drop off waits this long
COLOR_LEAD_DAYS: int = 5


#WEEKLY LIMITS
#how many of each job the shop takes in a week, counted by the week the car drops off, a rough draft to tune later
WEEKLY_LIMITS: dict[str, float] = {"tint": 3, "wrap": 3, "full_body_ppf": 1}


#SLOT NAMES
#the weekly limit each service counts toward, a front end shares the full body ppf limit
SLOT_NAMES: dict[str, str] = {"tint": "tint", "wrap": "wrap", "full_body_ppf": "full_body_ppf", "front_ppf": "full_body_ppf"}


#SLOT UNITS
#how much of its weekly limit each service takes, 2 front ends fill the same spot as 1 full body
SLOT_UNITS: dict[str, float] = {"tint": 1, "wrap": 1, "full_body_ppf": 1, "front_ppf": 0.5}


#DROP DAYS
#weekday numbers where monday is 0, tint drops off tuesday through friday and every other job monday through thursday
DROP_OFF_DAYS: dict[str, list[int]] = {"tint": [1, 2, 3, 4], "wrap": [0, 1, 2, 3], "full_body_ppf": [0, 1, 2, 3], "front_ppf": [0, 1, 2, 3], "coating": [0, 1, 2, 3], "add_on": [0, 1, 2, 3]}



#**********WEEKS**********
#the shop counts its weekly limits by week, monday to sunday


#WEEK START
#the monday of the week a day is in
def week_start(day: date) -> date:
    #every week is counted from its monday
    return day - timedelta(days=day.weekday())


#EMPTY WEEK
#a week with nothing used up from any weekly limit yet
def empty_week() -> dict[str, float]:
    return {"tint": 0, "wrap": 0, "full_body_ppf": 0}



#**********JOB TYPES**********
#reads the service names to tell what kind of job it is: tint, wrap, ppf, coating or a small add on


#PPF TYPE
#whether a service is a front end or full body ppf, empty when it's not ppf
def ppf_type(name: str) -> str:
    if("ppf" not in name and "paint protection" not in name and "clear bra" not in name):
        return ""

    #the windshield skin is a small job like the front end, so it takes a front end's spot
    if("front" in name or "windshield" in name):
        return "front_ppf"

    return "full_body_ppf"


#SERVICE TYPE
#the kind of job a service name is, which tells its drop off days and its weekly limit
def service_type(service_name: str) -> str:
    name: str = service_name.lower()

    #tint comes first, so ceramic tint is never read as a ceramic coating
    if("tint" in name):
        return "tint"

    #a coating on top of a wrap or ppf says wrap or ppf too, so the coating is checked before them
    if("coating" in name):
        return "coating"

    ppf: str = ppf_type(name)

    if(ppf != ""):
        return ppf

    if("wrap" in name):
        return "wrap"

    #anything else, like blacked out emblems, rides along with the job it's added to
    return "add_on"


#COLOR PICK
#a wrap or colored ppf waits on its film, so its first open day is pushed out by the color lead days
def color_pick_job(service_names: list[str]) -> bool:
    for service_name in service_names:
        name: str = service_name.lower()

        if(service_type(service_name) == "wrap" or ("color" in name and ppf_type(name) != "")):
            return True

    return False


#JOB KINDS
#the open days only depend on the kinds of job in it and whether one waits on its film, never on a color or a price
def job_kinds(service_names: list[str]) -> list[str]:
    kinds: list[str] = []

    for service_name in service_names:
        kind: str = service_type(service_name)

        if(kind not in kinds):
            kinds.append(kind)

    #a wrap or colored ppf can't drop off until its film comes in, so it moves the first open day too
    if(color_pick_job(service_names)):
        kinds.append("color_pick")

    return sorted(kinds)



#**********WEEK USAGE**********
#counts how much of each weekly limit the jobs already on the calendar have used up


#EVENT DATE
#the day a calendar event is on, None when it has no start date
def event_date(event: dict) -> date | None:
    start: dict = event.get("start", {})

    #an all day event only has a date
    if("date" in start):
        return date.fromisoformat(start["date"])

    #a timed event has a date and time, read in the shop's own timezone
    if("dateTime" in start):
        start_time: datetime = datetime.fromisoformat(start["dateTime"])

        return start_time.astimezone(SHOP_TIMEZONE).date()

    return None


#TITLE TYPES
#every job a calendar event's title names that counts toward a weekly limit
def title_service_types(title: str) -> list[str]:
    name: str = title.lower()

    service_types: list[str] = []

    #one calendar event can hold more than one job, like "Wrap + tint - Ram", so every service in its title counts
    if("tint" in name):
        service_types.append("tint")

    ppf: str = ppf_type(name)

    if(ppf != ""):
        service_types.append(ppf)

    if("wrap" in name):
        service_types.append("wrap")

    return service_types


#WEEK USAGE
#how much of each weekly limit is used up, by the monday of each week that has jobs on the calendar
def week_usage(events: list[dict]) -> dict[date, dict[str, float]]:
    usage: dict[date, dict[str, float]] = {}

    for event in events:
        day: date | None = event_date(event)

        if(day is None):
            continue

        monday: date = week_start(day)

        if(monday not in usage):
            usage[monday] = empty_week()

        for service in title_service_types(event.get("summary", "")):
            slot: str = SLOT_NAMES[service]

            usage[monday][slot] += SLOT_UNITS[service]

    return usage



#**********OPEN DATES**********
#finds the days a customer's car can drop off, going by the calendar and the shop's weekly limits


#CALENDAR WINDOW
#the start and end of the calendar stretch to read, whole weeks that cover every day searched
def calendar_window(today: date) -> tuple[datetime, datetime]:
    #whole weeks get read, so a job already in the first days of a week still counts toward that week
    first_monday: date = week_start(today)

    last_day: date = today + timedelta(days=DAYS_TO_SEARCH)

    end_monday: date = week_start(last_day) + timedelta(days=7)

    window_start: datetime = datetime.combine(first_monday, time(0, 0), SHOP_TIMEZONE)

    window_end: datetime = datetime.combine(end_monday, time(0, 0), SHOP_TIMEZONE)

    return (window_start, window_end)


#OPEN DATES
#every open day in the next 3 weeks, soonest first, so a set to offer can be picked from all of them
def open_drop_off_dates(service_names: list[str], events: list[dict], today: date) -> list[date]:
    open_dates: list[date] = []

    #nothing confirmed means there's no job to fit anywhere
    if(len(service_names) == 0):
        return open_dates

    usage: dict[date, dict[str, float]] = week_usage(events)

    #what this job takes from each weekly limit, and every service type in it
    job_units: dict[str, float] = empty_week()

    job_types: list[str] = []

    for service_name in service_names:
        service: str = service_type(service_name)

        #one car's tint in a few lines, like the sides and the windshield, is still one tint job
        if(service in job_types):
            continue

        job_types.append(service)

        if(service in SLOT_NAMES):
            job_units[SLOT_NAMES[service]] += SLOT_UNITS[service]

    #a wrap or colored ppf can't drop off until its film comes in, everything else can go the next day
    first_day: int = 1

    if(color_pick_job(service_names)):
        first_day = COLOR_LEAD_DAYS

    for day_number in range(first_day, DAYS_TO_SEARCH + 1):
        day: date = today + timedelta(days=day_number)

        #the drop off day has to work for every service in the job
        day_allowed: bool = True

        for service in job_types:
            if(day.weekday() not in DROP_OFF_DAYS[service]):
                day_allowed = False

        if(not day_allowed):
            continue

        week_used: dict[str, float] = usage.get(week_start(day), empty_week())

        #the job only fits when every weekly limit it uses still has room for it that week
        job_fits: bool = True

        for slot, weekly_limit in WEEKLY_LIMITS.items():
            if(job_units[slot] > 0 and week_used[slot] + job_units[slot] > weekly_limit):
                job_fits = False

        if(not job_fits):
            continue

        open_dates.append(day)

    return open_dates
