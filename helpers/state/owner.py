#IMPORTS

import json
import re
from datetime import datetime, timedelta, timezone

from helpers.state import log


#GLOBALS

#what the owners text says for each way a conversation gets handed to a person
REASONS: dict[str, str] = {}

REASONS["service_pricing"] = "The service details have no answer for what they asked, the reply told them Hazel would ask you"

REASONS["business_operations"] = "The business details have no answer for what they asked, the reply told them Hazel would ask you"

REASONS["services_req_humans"] = "A custom job has everything its price needs, it's ready for you to price"

REASONS["escalation"] = "A refund, a complaint, financing trouble, upset with the shop, a specific deal they saw, a job at the shop or someone selling to the shop"

REASONS["phone_call"] = "They want to talk on the phone, the reply gave them the shop's number and told them to ask for you"

REASONS["no_open_days"] = "No open drop off day in the next 3 weeks for the services they want to book"

REASONS["days_ran_out"] = "None of the drop off days offered work for them"

REASONS["contact_refused"] = "They won't give their name, number or email for the invoice, want it some other way or called it off, so it waits on you"

REASONS["spam_harass"] = "Spam or harassment while asked for their info for the invoice, nothing was sent back"

REASONS["restricted"] = "They messaged while restricted about something the system doesn't answer, so it waits on you"

REASONS["no_material"] = "None of the closest materials you sent work for them, so it waits on you"

REASONS["at_shop"] = "They're at the shop right now while restricted, the reply told them to come on in and ask for you"

REASONS["color_check_missed"] = "The reply told them we'd check the color books, but nothing came with their message for you to check, so it waits on you"

REASONS["price_hold"] = "Every reply written for their first message gave a price they never asked for, so it waits on you"

REASONS["owner_ask"] = "Part of what they asked has no answer in the details and isn't something small, the reply answered the rest and told them Hazel would ask you"

REASONS["side_ask"] = "They asked again about something small the details have no answer for, after the reply told them Hazel would ask you"

REASONS["booking_hold"] = "They messaged while you're fitting them a day on the schedule, nothing went back to them, so it waits on you"

#days a small ask stays open, asking about it again in that time hands them to the owner
SIDE_ASK_DAYS: int = 7

#everything the owner needs to send the estimate by hand, kept until his text goes out
ESTIMATE_FIELDS: list[str] = ["services", "drop_off_date", "name", "number", "email"]

#the job they want on the schedule, kept until the owners text about it goes out
SCHEDULE_REQUEST_FIELDS: list[str] = ["services"]

#a wrap or colored ppf waits on the owner checking the shop can get that exact color
COLOR_CHECK_FIELDS: list[str] = ["status", "code", "want", "media", "links", "route", "channel", "news", "materials"]

#every color check code still waiting on the owner, each one pointing to its customer
COLOR_CHECK_CODES: str = "color_check_codes"

#y 12 is the exact color, m 12 is the closest materials, a bare answer works when only one waits
COLOR_ANSWER_PATTERN = re.compile(r"^\s*(y|yes|yep|yeah|m|n|no|nope)\s*#?\s*(\d+)?\s*[.!]*\s*$", re.IGNORECASE)

#his answers, by the letter they start with
EXACT_ANSWER: str = "y"

MATERIALS_ANSWER: str = "m"

NO_ANSWER: str = "n"

#waiting on him, exact color approved, or picking from the closest materials
PENDING_STATUS: str = "pending"

APPROVED_STATUS: str = "approved"

MATERIALS_STATUS: str = "materials"

#the owners news waits this long in case they're mid message, pics are slow, then it goes out
NEWS_WAIT_SECONDS: int = 10

#owner answers landing on each customer right now, a reply in progress waits for every one
NEWS_LANDING: dict[str, int] = {}

#blooio lets 4 texts into his thread till he texts back or reacts, an older thread gets more
OWNER_LINE_CAP: int = 4

#hils stay out of his thread once only this many spots are left, color checks can't wait on him
COLOR_CHECK_ROOM: int = 2

#texts that went in his blooio thread since he last texted back or reacted
OWNER_LINE_STREAK: str = "owner_line_streak"

#what the newest text in his thread was, a hil or a color check one
OWNER_LINE_LAST: str = "owner_line_last"

HIL_TEXT: str = "hil"

CHECK_TEXT: str = "check"

#replaces HIL after a hold reply, so there next message waits and the one after it gets one
HELD_STATE: str = "HIL HELD"

#replaces HIL while a person fits them a day, the system sends them nothing till it comes off
BOOKING_STATE: str = "HIL BOOKING"

#replaces HIL when the owner had them first, so the system stays a ghost for good
CONVO_STATE: str = "HIL CONVO"


#HAND OFFS

#a person takes the chat from here, the reason waits for the owners text after the reply
def restrict(id: str, reason: str) -> None:
    #plain HIL on file means the owner has the chat, restricted route till it comes off
    log.write_state(f"restricted_{id}", "HIL")

    #kept until the owners text goes out, so a rerun after a timeout never texts them twice
    log.write_info(f"hil_notify_{id}", [reason], ["reason"])

#a hold reply went out, so their next message waits for the one after it
def hold(id: str) -> None:
    #write_state keeps the time a schedule hold ends at
    log.write_state(f"restricted_{id}", HELD_STATE)

#true when there last message while a person has them got a hold reply
def held(id: str) -> bool:
    return log.read_state(f"restricted_{id}") == HELD_STATE

#a person fits them a day from here, so the system goes quiet and the owner gets the reason
def restrict_booking(id: str, reason: str) -> None:
    #write_state keeps the time a schedule hold ends at
    log.write_state(f"restricted_{id}", BOOKING_STATE)

    #kept until the owners text goes out, so a rerun after a timeout never texts them twice
    log.write_info(f"hil_notify_{id}", [reason], ["reason"])

#true while a person fits them a day, the system sends them nothing at all
def booking_held(id: str) -> bool:
    return log.read_state(f"restricted_{id}") == BOOKING_STATE

#they wrote in during the booking hold, so the owner gets texted and the hold stays put
def note_booking_message(id: str) -> None:
    log.write_info(f"hil_notify_{id}", [REASONS["booking_hold"]], ["reason"])

#they were the owners before the system showed up, so he keeps them and it never says a word
def restrict_convo(id: str) -> None:
    log.write_state(f"restricted_{id}", CONVO_STATE)

#true when they were the owners before the system showed up, so it sends nothing at all
def convo_held(id: str) -> bool:
    return log.read_state(f"restricted_{id}") == CONVO_STATE

#why they just got handed to a person, empty when nothing handed them off this time
def take_notify_reason(id: str) -> str:
    reason: str = log.read_info(f"hil_notify_{id}").get("reason", "")

    #taken off once its read, so the next message never texts the owner about this one again
    log.clear_info(f"hil_notify_{id}", ["reason"])

    return reason

#they gave their contact info for the invoice, so the owner gets the job and how to reach them
def ready_estimate(id: str, confirmed_services: dict, drop_off_date: str, contact: dict[str, str]) -> None:
    values: list[str] = [json.dumps(confirmed_services), drop_off_date, contact.get("name", ""), contact.get("number", ""), contact.get("email", "")]

    #kept until the owners text goes out, so a rerun after a timeout never texts him twice
    log.write_info(f"estimate_notify_{id}", values, ESTIMATE_FIELDS)

#the estimate still owed to the owner, empty when none is, taken off once its read
def take_estimate_alert(id: str) -> dict[str, str]:
    estimate: dict[str, str] = log.read_info(f"estimate_notify_{id}")

    log.clear_info(f"estimate_notify_{id}", ESTIMATE_FIELDS)

    return estimate

#they want on the schedule, so the owner gets texted the job once the reply goes out
def ready_schedule_request(id: str, confirmed_services: dict) -> None:
    #kept until the owners text goes out, so a rerun after a timeout never texts him twice
    log.write_info(f"schedule_request_notify_{id}", [json.dumps(confirmed_services)], SCHEDULE_REQUEST_FIELDS)

#the schedule request still owed to the owner, empty when none is, taken off once its read
def take_schedule_request(id: str) -> dict[str, str]:
    schedule_request: dict[str, str] = log.read_info(f"schedule_request_notify_{id}")

    log.clear_info(f"schedule_request_notify_{id}", SCHEDULE_REQUEST_FIELDS)

    return schedule_request


#SIDE ASKS

#the reply saying she'd ask the owner is kept for the developers text, and the ask stays open
def side_ask(id: str, reply: str) -> None:
    #kept until the developers text goes out, so a rerun after a timeout never texts him twice
    log.write_info(f"side_ask_notify_{id}", [reply], ["reply"])

    log.write_state(f"side_ask_open_{id}", reply)

    #an ask they never bring up again comes off file on its own
    log.expire_at(f"side_ask_open_{id}", datetime.now(timezone.utc) + timedelta(days=SIDE_ASK_DAYS))

#true while a small thing she said she'd ask the owner about is still open
def side_ask_open(id: str) -> bool:
    return log.read_state(f"side_ask_open_{id}") != {}

#they asked about it again and the owner has it now, so its never open twice
def close_side_ask(id: str) -> None:
    log.clear_state(f"side_ask_open_{id}")

#the reply the developer still needs a text about, empty when none, taken off once its read
def take_side_ask_alert(id: str) -> str:
    reply: str = log.read_info(f"side_ask_notify_{id}").get("reply", "")

    log.clear_info(f"side_ask_notify_{id}", ["reply"])

    return reply


#COLOR CHECKS

#empty before a check, then pending, approved, or materials while they pick from the closest
def color_check_status(id: str) -> str:
    return log.read_info(f"color_check_{id}").get("status", "")

#the check comes off the ones waiting on the owner
def close_color_check(id: str) -> None:
    code: str = log.read_info(f"color_check_{id}").get("code", "")

    if(code != ""):
        log.clear_info(COLOR_CHECK_CODES, [code])

#everything kept for the check comes off, so a new color starts a check of its own
def clear_color_check(id: str) -> None:
    close_color_check(id)

    log.clear_info(f"color_check_{id}", COLOR_CHECK_FIELDS)

    log.clear_info(f"color_check_notify_{id}", ["code"])

#the exact color they sent, with its pics and links, kept until the owner gets texted about it
def note_wanted_color(id: str, want: str, media: list[str], links: list[str]) -> None:
    if(want == ""):
        return

    checked_want: str = log.read_info(f"color_check_{id}").get("want", "")

    #a different color than the one the owner checked needs its own check
    if(checked_want != "" and checked_want != want):
        clear_color_check(id)

    log.write_info(f"criticalInfo_{id}", [want], ["want"])

    log.clear_info(f"color_ref_{id}", ["media", "links"])

    log.write_info(f"color_ref_{id}", [want, "\n".join(media), "\n".join(links)], ["want", "media", "links"])

#the route stays on the check so the job stays the same, and they wait restricted on the owner
def request_color_check(id: str, route: str) -> str:
    color_ref: dict[str, str] = log.read_info(f"color_ref_{id}")

    code: str = str(log.next_count("color_check_counter"))

    check_values: list[str] = [PENDING_STATUS, code, color_ref.get("want", ""), color_ref.get("media", ""), color_ref.get("links", ""), route]

    check_fields: list[str] = ["status", "code", "want", "media", "links", "route"]

    log.write_info(f"color_check_{id}", check_values, check_fields)

    log.write_info(COLOR_CHECK_CODES, [id], [code])

    #kept until the owners text goes out, so a rerun after a timeout never texts them twice
    log.write_info(f"color_check_notify_{id}", [code], ["code"])

    #no hand off reason here, the color check text already tells him why they're waiting
    log.write_state(f"restricted_{id}", "HIL")

    return code

#pics or links with no color read off them, so the owner checks the color books himself
def request_unread_color_check(id: str, route: str, media: list[str], links: list[str]) -> str:
    log.clear_info(f"color_ref_{id}", ["want", "media", "links"])

    log.write_info(f"color_ref_{id}", ["\n".join(media), "\n".join(links)], ["media", "links"])

    return request_color_check(id, route)

#the check still owed to the owner, empty when none is, taken off once its read
def take_color_check_alert(id: str, channel: str) -> dict[str, str]:
    notify: dict[str, str] = log.read_info(f"color_check_notify_{id}")

    if(len(notify) == 0):
        return {}

    log.clear_info(f"color_check_notify_{id}", ["code"])

    #the channel goes on file, so an error answering his answer still names it for the developer
    log.write_info(f"color_check_{id}", [channel], ["channel"])

    return log.read_info(f"color_check_{id}")


#OWNER LINE

#a text made it into his blooio thread, so it counts toward blooios cap and its the newest one there
def line_sent(kind: str) -> None:
    try:
        log.next_count(OWNER_LINE_STREAK)

        log.write_state(OWNER_LINE_LAST, kind)
    except Exception as error:
        #the text still went out, a missed count only lets a hil take one spot too many
        print(f"OWNER LINE WRITE ERROR: {error}")

#he texted back or reacted, so blooio gives his thread all its room back
def line_answered() -> None:
    try:
        log.clear_state(OWNER_LINE_STREAK)
    except Exception as error:
        #his answer still gets read, hils just ride textbelt a bit longer than they need to
        print(f"OWNER LINE WRITE ERROR: {error}")

#true while a hil can go in his thread and still leave the color checks their spots
def hil_room() -> bool:
    try:
        streak: int = log.read_count(OWNER_LINE_STREAK)
    except Exception as error:
        #no telling how full it is, so the hil goes over textbelt like it always did
        print(f"OWNER LINE READ ERROR: {error}")

        return False

    return streak < OWNER_LINE_CAP - COLOR_CHECK_ROOM

#true when a hil is the newest text in his thread, so a bare yes might be him answering it
def hil_last() -> bool:
    return log.read_state(OWNER_LINE_LAST) == HIL_TEXT


#OWNER ANSWERS

#answer with its letter and code, which when a bare one has many waiting, unsure when a hil came after, None when its not one
def color_check_answer(text: str) -> tuple | None:
    match = COLOR_ANSWER_PATTERN.match(text)

    if(match is None):
        return None

    letter: str = match.group(1)[0].lower()

    code: str | None = match.group(2)

    if(not code):
        code = ""

    waiting: dict[str, str] = log.read_info(COLOR_CHECK_CODES)

    #a bare answer with nothing waiting is just a text from him, so its dropped
    if(code == "" and len(waiting) == 0):
        return None

    if(code == "" and len(waiting) > 1):
        return ("which",)

    #a bare answer with one check waiting is for that one
    if(code == ""):
        waiting_codes: list[str] = list(waiting.keys())

        code = waiting_codes[0]

        #a hil landed in his thread after the check, so a bare yes could be him answering the hil
        if(hil_last()):
            return ("unsure", letter, code)

    return ("answer", letter, code)

#the customer the check with this number is for, empty when no check with it is waiting
def color_check_customer(code: str) -> str:
    return log.read_info(COLOR_CHECK_CODES).get(code, "")

#where they wrote in when the check went out, so his answer goes back to the right server
def color_check_channel(id: str) -> str:
    return log.read_info(f"color_check_{id}").get("channel", "blooio")

#the shop has the exact color, so the restriction comes off and the good news is due
def answer_exact(id: str) -> None:
    close_color_check(id)

    log.write_info(f"color_check_{id}", [APPROVED_STATUS, "due"], ["status", "news"])

    log.clear_state(f"restricted_{id}")

#the shop can't get that color, so the closest materials go out and they stay restricted
def answer_materials(id: str, materials: list[dict[str, str]]) -> None:
    close_color_check(id)

    log.write_info(f"color_check_{id}", [MATERIALS_STATUS, "due", json.dumps(materials)], ["status", "news", "materials"])

    log.write_state(f"restricted_{id}", "HIL")


#PICKS

#the closest materials, in the order the owner sent them
def color_materials(id: str) -> list[dict[str, str]]:
    return json.loads(log.read_info(f"color_check_{id}").get("materials", "[]"))

#the exact color they sent that the owner checked, empty when none got read off what they sent
def checked_want(id: str) -> str:
    return log.read_info(f"color_check_{id}").get("want", "")

#their pick is the color they want now and the shop can get it, so the system picks it back up
def pick_material(id: str, material: dict[str, str]) -> None:
    name: str = material.get("name", "")

    log.write_info(f"color_check_{id}", [APPROVED_STATUS, name], ["status", "want"])

    log.clear_info(f"color_check_{id}", ["materials"])

    #the booking names the jobs color from criticalInfo, so the pick has to land their too
    log.write_info(f"criticalInfo_{id}", [name], ["want"])

    log.clear_state(f"restricted_{id}")

#what the owner found hasn't gone out yet, the good news or the closest materials to pick from
def news_due(id: str) -> bool:
    return log.read_info(f"color_check_{id}").get("news", "") == "due"

#it went out, so nothing after it says it again or waits on them for it
def news_given(id: str) -> None:
    log.clear_info(f"color_check_{id}", ["news"])


#NEWS LANDING

#the reply being written now waits at the send, then their batch runs again with his answer
def hold_for_news(id: str) -> None:
    NEWS_LANDING[id] = NEWS_LANDING.get(id, 0) + 1

#his answer is on file, so the next reply written for them carries it
def news_landed(id: str) -> None:
    landing: int = NEWS_LANDING.get(id, 0) - 1

    if(landing > 0):
        NEWS_LANDING[id] = landing
    else:
        NEWS_LANDING.pop(id, None)

#true while any of the owners answers is still landing on them
def news_landing(id: str) -> bool:
    return NEWS_LANDING.get(id, 0) > 0
