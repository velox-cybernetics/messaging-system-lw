#**********IMPORTS**********
#python's json, clock and pattern matching, plus the saved state where hand offs, side asks and color checks are kept
import json
import re
from datetime import datetime, timedelta, timezone

from helpers.state import log



#**********GLOBALS**********
#why a conversation goes to a person, and the fields, codes and answers a color check is kept with


#REASONS
#what the owner's text says for each way a conversation gets handed to a person
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


#SIDE ASK DAYS
#a small thing the new girl said she'd ask the owner about stays open this long, so asking about it again hands them to him
SIDE_ASK_DAYS: int = 7


#ESTIMATE FIELDS
#everything the owner needs to send the estimate by hand, kept until his text goes out
ESTIMATE_FIELDS: list[str] = ["services", "drop_off_date", "name", "number", "email"]


#SCHEDULE FIELDS
#the job they want on the schedule, kept until the owner's text about it goes out
SCHEDULE_REQUEST_FIELDS: list[str] = ["services"]


#CHECK FIELDS
#a wrap or colored ppf waits on the owner making sure the shop can get the exact color they sent before it's booked
COLOR_CHECK_FIELDS: list[str] = ["status", "code", "want", "media", "links", "route", "channel", "news", "materials"]


#CHECK CODES
#the codes of every color check still waiting on the owner, each one pointing to its customer
COLOR_CHECK_CODES: str = "color_check_codes"


#ANSWER PATTERN
#"Y 12" means the shop has that exact color, "M 12" comes with the closest materials, a bare one when only one waits
COLOR_ANSWER_PATTERN: re.Pattern = re.compile(r"^\s*(y|yes|yep|yeah|m|n|no|nope)\s*#?\s*(\d+)?\s*[.!]*\s*$", re.IGNORECASE)


#OWNER ANSWERS
#his answers, by the letter they start with
EXACT_ANSWER: str = "y"

MATERIALS_ANSWER: str = "m"

NO_ANSWER: str = "n"


#CHECK STATUSES
#waiting on him, the shop can get the color they want, or they're picking from the closest materials it can order
PENDING_STATUS: str = "pending"

APPROVED_STATUS: str = "approved"

MATERIALS_STATUS: str = "materials"


#NEWS WAIT
#what the owner found gets this long for a message they're still sending to land, a pic takes a moment, then goes out on its own
NEWS_WAIT_SECONDS: int = 10


#NEWS LANDING
#how many of the owner's answers are landing on each customer right now, a reply of theirs being written holds off for every one
NEWS_LANDING: dict[str, int] = {}


#HELD STATE
#on file in place of "HIL" once a hold reply went out for their last message, so their next one waits and the one after it gets one
HELD_STATE: str = "HIL HELD"


#BOOKING STATE
#on file in place of "HIL" while a person fits them a day on the schedule, so nothing from the bot goes out to them till it comes off
BOOKING_STATE: str = "HIL BOOKING"



#**********HAND OFFS**********
#hands a conversation to the owner and keeps what his text needs until it goes out


#RESTRICT
#a person takes the conversation from here, the reason is kept so the owner gets texted once the reply goes out
def restrict(id: str, reason: str) -> None:
    #the plain string "HIL" on file means a person (the owner) has the chat, so their messages take the restricted route till it comes off
    log.write_state(f"restricted_{id}", "HIL")

    #kept until the owner's text goes out, so a chain that runs again after a timeout never texts them twice
    log.write_info(f"hil_notify_{id}", [reason], ["reason"])


#HOLD
#a hold reply went out while a person has them, so the next message they send waits for the one after it
def hold(id: str) -> None:
    #write_state keeps the time a schedule hold ends at
    log.write_state(f"restricted_{id}", HELD_STATE)


#HELD
#True when the last message they sent while a person has them got a hold reply
def held(id: str) -> bool:
    return log.read_state(f"restricted_{id}") == HELD_STATE


#RESTRICT BOOKING
#a person fits them a day on the schedule from here, so the bot goes silent for them, and the reason is kept so the owner gets texted once the reply goes out
def restrict_booking(id: str, reason: str) -> None:
    #write_state keeps the time a schedule hold ends at
    log.write_state(f"restricted_{id}", BOOKING_STATE)

    #kept until the owner's text goes out, so a chain that runs again after a timeout never texts them twice
    log.write_info(f"hil_notify_{id}", [reason], ["reason"])


#BOOKING HELD
#True while a person is fitting them a day on the schedule, when the bot sends them nothing at all
def booking_held(id: str) -> bool:
    return log.read_state(f"restricted_{id}") == BOOKING_STATE


#BOOKING MESSAGE
#they wrote in while a person fits them a day, so the owner gets texted what they sent, and the booking hold stays as it was
def note_booking_message(id: str) -> None:
    log.write_info(f"hil_notify_{id}", [REASONS["booking_hold"]], ["reason"])


#NOTIFY REASON
#why they just got handed to a person, empty when nothing handed them off this time
def take_notify_reason(id: str) -> str:
    reason: str = log.read_info(f"hil_notify_{id}").get("reason", "")

    #taken off once it's read, so the next message never texts the owner about this one again
    log.clear_info(f"hil_notify_{id}", ["reason"])

    return reason


#READY ESTIMATE
#they gave their contact info for the invoice, so the owner gets texted the job and how to reach them
def ready_estimate(id: str, confirmed_services: dict, drop_off_date: str, contact: dict[str, str]) -> None:
    values: list[str] = [json.dumps(confirmed_services), drop_off_date, contact.get("name", ""), contact.get("number", ""), contact.get("email", "")]

    #kept until the owner's text goes out, so a chain that runs again after a timeout never texts him twice
    log.write_info(f"estimate_notify_{id}", values, ESTIMATE_FIELDS)


#ESTIMATE ALERT
#the estimate that still has to be texted to the owner, empty when none is, taken off once it's read
def take_estimate_alert(id: str) -> dict[str, str]:
    estimate: dict[str, str] = log.read_info(f"estimate_notify_{id}")

    log.clear_info(f"estimate_notify_{id}", ESTIMATE_FIELDS)

    return estimate


#READY SCHEDULE REQUEST
#they want to get on the schedule, so the owner gets texted the job to fit them a day once the reply goes out
def ready_schedule_request(id: str, confirmed_services: dict) -> None:
    #kept until the owner's text goes out, so a chain that runs again after a timeout never texts him twice
    log.write_info(f"schedule_request_notify_{id}", [json.dumps(confirmed_services)], SCHEDULE_REQUEST_FIELDS)


#SCHEDULE REQUEST ALERT
#the schedule request that still has to be texted to the owner, empty when none is, taken off once it's read
def take_schedule_request(id: str) -> dict[str, str]:
    schedule_request: dict[str, str] = log.read_info(f"schedule_request_notify_{id}")

    log.clear_info(f"schedule_request_notify_{id}", SCHEDULE_REQUEST_FIELDS)

    return schedule_request



#**********SIDE ASKS**********
#something small the details have no answer for, like the wifi or parking, goes to the developer on the side and nobody takes the chat


#SIDE ASK
#the reply that told them she'd ask the owner is kept until the developer's text goes out, and the ask stays open in case they ask about it again
def side_ask(id: str, reply: str) -> None:
    #kept until the developer's text goes out, so a chain that runs again after a timeout never texts him twice
    log.write_info(f"side_ask_notify_{id}", [reply], ["reply"])

    log.write_state(f"side_ask_open_{id}", reply)

    #an ask they never bring up again comes off file on its own
    log.expire_at(f"side_ask_open_{id}", datetime.now(timezone.utc) + timedelta(days=SIDE_ASK_DAYS))


#SIDE ASK OPEN
#True while a small thing the new girl said she'd ask the owner about is still open for them
def side_ask_open(id: str) -> bool:
    return log.read_state(f"side_ask_open_{id}") != {}


#CLOSE SIDE ASK
#they asked about it again and the owner has it now, so it's never open twice
def close_side_ask(id: str) -> None:
    log.clear_state(f"side_ask_open_{id}")


#SIDE ASK ALERT
#the reply the developer still has to be texted about, empty when there's none, taken off once it's read
def take_side_ask_alert(id: str) -> str:
    reply: str = log.read_info(f"side_ask_notify_{id}").get("reply", "")

    log.clear_info(f"side_ask_notify_{id}", ["reply"])

    return reply



#**********COLOR CHECKS**********
#asks the owner if the shop can get the exact color they sent, and tracks the check till he answers


#CHECK STATUS
#empty before a check went out, then pending, approved, or materials while they pick from the closest ones
def color_check_status(id: str) -> str:
    return log.read_info(f"color_check_{id}").get("status", "")


#CLOSE CHECK
#the check comes off the ones waiting on the owner
def close_color_check(id: str) -> None:
    code: str = log.read_info(f"color_check_{id}").get("code", "")

    if(code != ""):
        log.clear_info(COLOR_CHECK_CODES, [code])


#CLEAR CHECK
#everything kept for the check comes off, so a new color starts a check of its own
def clear_color_check(id: str) -> None:
    close_color_check(id)

    log.clear_info(f"color_check_{id}", COLOR_CHECK_FIELDS)

    log.clear_info(f"color_check_notify_{id}", ["code"])


#WANTED COLOR
#the exact color they sent, with the pics and links it came in, kept until the owner gets texted about it
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


#REQUEST CHECK
#the route stays on the check so the job stays the same, and they're restricted till the owner answers
def request_color_check(id: str, route: str) -> str:
    color_ref: dict[str, str] = log.read_info(f"color_ref_{id}")

    code: str = str(log.next_count("color_check_counter"))

    check_values: list[str] = [PENDING_STATUS, code, color_ref.get("want", ""), color_ref.get("media", ""), color_ref.get("links", ""), route]

    check_fields: list[str] = ["status", "code", "want", "media", "links", "route"]

    log.write_info(f"color_check_{id}", check_values, check_fields)

    log.write_info(COLOR_CHECK_CODES, [id], [code])

    #kept until the owner's text goes out, so a chain that runs again after a timeout never texts them twice
    log.write_info(f"color_check_notify_{id}", [code], ["code"])

    #no hand off reason goes with it, the color check text already tells him why they're waiting on him
    log.write_state(f"restricted_{id}", "HIL")

    return code


#UNREAD CHECK
#their pics or links go to the owner with no color read off them, so he still checks the color books for what they sent
def request_unread_color_check(id: str, route: str, media: list[str], links: list[str]) -> str:
    log.clear_info(f"color_ref_{id}", ["want", "media", "links"])

    log.write_info(f"color_ref_{id}", ["\n".join(media), "\n".join(links)], ["media", "links"])

    return request_color_check(id, route)


#CHECK ALERT
#the check that still has to be texted to the owner, empty when none is, taken off once it's read
def take_color_check_alert(id: str, channel: str) -> dict[str, str]:
    notify: dict[str, str] = log.read_info(f"color_check_notify_{id}")

    if(len(notify) == 0):
        return {}

    log.clear_info(f"color_check_notify_{id}", ["code"])

    #the channel goes on file, so an error answering the owner's answer still names it for the developer
    log.write_info(f"color_check_{id}", [channel], ["channel"])

    return log.read_info(f"color_check_{id}")



#**********OWNER ANSWERS**********
#reads the owner's yes or materials answer to a color check and puts the conversation back on track


#OWNER ANSWER
#("answer", letter, code) for his answer, ("which",) when a bare one has many checks waiting, None when it's not one
def color_check_answer(text: str) -> tuple | None:
    match: re.Match | None = COLOR_ANSWER_PATTERN.match(text)

    if(match is None):
        return None

    letter: str = match.group(1)[0].lower()

    code: str | None = match.group(2)

    if(not code):
        code = ""

    waiting: dict[str, str] = log.read_info(COLOR_CHECK_CODES)

    #a bare answer with no check waiting answers nothing, so it's dropped like anything else from his number
    if(code == "" and len(waiting) == 0):
        return None

    if(code == "" and len(waiting) > 1):
        return ("which",)

    #a bare answer with one check waiting is for that one
    if(code == ""):
        waiting_codes: list[str] = list(waiting.keys())

        code = waiting_codes[0]

    return ("answer", letter, code)


#CHECK CUSTOMER
#the customer the check with this number is for, empty when no check with it is waiting
def color_check_customer(code: str) -> str:
    return log.read_info(COLOR_CHECK_CODES).get(code, "")


#CHECK CHANNEL
#where they wrote in when the check went to the owner, so his answer goes back to the server that has them
def color_check_channel(id: str) -> str:
    return log.read_info(f"color_check_{id}").get("channel", "blooio")


#ANSWER EXACT
#the shop has that exact color, so the restriction comes off and the bot picks it back up with the good news due
def answer_exact(id: str) -> None:
    close_color_check(id)

    log.write_info(f"color_check_{id}", [APPROVED_STATUS, "due"], ["status", "news"])

    log.clear_state(f"restricted_{id}")


#ANSWER MATERIALS
#the shop can't get that exact color, so the closest materials go out to pick from and they stay restricted till then
def answer_materials(id: str, materials: list[dict[str, str]]) -> None:
    close_color_check(id)

    log.write_info(f"color_check_{id}", [MATERIALS_STATUS, "due", json.dumps(materials)], ["status", "news", "materials"])

    log.write_state(f"restricted_{id}", "HIL")



#**********PICKS AND NEWS**********
#keeps the material they picked and whether what he found has gone out yet


#COLOR MATERIALS
#the closest materials, in the order the owner sent them
def color_materials(id: str) -> list[dict[str, str]]:
    return json.loads(log.read_info(f"color_check_{id}").get("materials", "[]"))


#CHECKED COLOR
#the exact color they sent that the owner checked, empty when none got read off what they sent
def checked_want(id: str) -> str:
    return log.read_info(f"color_check_{id}").get("want", "")


#PICK MATERIAL
#the material they picked is the color they want now and one the shop can get, so the bot picks it back up
def pick_material(id: str, material: dict[str, str]) -> None:
    name: str = material.get("name", "")

    log.write_info(f"color_check_{id}", [APPROVED_STATUS, name], ["status", "want"])

    log.clear_info(f"color_check_{id}", ["materials"])

    #the booking names the job's color from it, and a pic whose color couldn't be read keeps the one they sent
    log.write_info(f"criticalInfo_{id}", [name], ["want"])

    log.clear_state(f"restricted_{id}")


#NEWS DUE
#what the owner found hasn't gone out yet, the good news or the closest materials to pick from
def news_due(id: str) -> bool:
    return log.read_info(f"color_check_{id}").get("news", "") == "due"


#NEWS GIVEN
#it went out, so nothing after it says it again or waits on them for it
def news_given(id: str) -> None:
    log.clear_info(f"color_check_{id}", ["news"])



#**********NEWS LANDING**********
#a reply of theirs being written while the owner's answer lands never goes out, it gets written again carrying what he found


#HOLD REPLIES
#the reply being written for them right now is held at the send, and their batch gets answered again once his answer is on file
def hold_for_news(id: str) -> None:
    NEWS_LANDING[id] = NEWS_LANDING.get(id, 0) + 1


#NEWS LANDED
#his answer is on file, so the next reply written for them carries it
def news_landed(id: str) -> None:
    landing: int = NEWS_LANDING.get(id, 0) - 1

    if(landing > 0):
        NEWS_LANDING[id] = landing

    else:
        NEWS_LANDING.pop(id, None)


#NEWS LANDING
#True while any of the owner's answers is still landing on them
def news_landing(id: str) -> bool:
    return NEWS_LANDING.get(id, 0) > 0
