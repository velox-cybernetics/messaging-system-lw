#IMPORTS

import re
import time
from datetime import datetime, timedelta

from helpers.calendar import open_dates
from helpers.channels import replies
from helpers.channels import senders
from helpers.models import models
from helpers.models import retry
from helpers.response import greeting
from helpers.response import spacing
from helpers.response import wording
from helpers.state import dashboard
from helpers.state import ghl
from helpers.state import log
from helpers.state import state_build
from helpers.state import state_form
from helpers.terminal import prints
from src import routing
from src import branches
from src.prompts.followup import analyzer_examples as followup_examples
from src.prompts.followup import generator as followup_generator
from src.prompts.followup import sms_generator as sms_prompt


#GLOBALS

#every night at this hour in the shops time the quiet conversations get checked
PREP_HOUR: int = 22

#the picked ones get theirs next morning at this hour, with the shop open to answer them
FOLLOWUP_HOUR: int = 10

#the morning recheck runs this many minutes early, so a text in the night costs nobody theirs
RECHECK_MINUTES: int = 10

#quiet this long when it goes out, so someone still texting that morning never gets one
QUIET_SECONDS: int = 4 * 3600

#days between follow ups in a row, so after the first they land on day 3, 7, 14 and 30
FOLLOWUP_GAP_DAYS: list[int] = [2, 4, 7, 16]

#past those its one every this many days, so someone long quiet only hears from the shop monthly
FOLLOWUP_LATER_GAP_DAYS: int = 30

DAY_SECONDS: int = 24 * 3600

#when the nights check last started, not named followup_ so its never read as a conversation
NIGHT_PICK_KEY: str = "followups_night_pick"

#a night pick older than this means last night never ran, so the morning reads everyone
NIGHT_PICK_SECONDS: int = 24 * 3600

#follow ups in a row with no answer, instagram gets one, other channels never run out
CHANNEL_FOLLOWUPS: dict[str, int] = {"ig": 1}

#blooio follow ups in a row with no answer, after that its sms from the shops ghl number
BLOOIO_FOLLOWUPS: int = 3

#instagram and messenger refuse anything a day past their last message, metas rules not ours
META_WINDOW_SECONDS: int = 24 * 3600

#over this they're done with the shop for good, torn ones still get their follow up
NOT_INTERESTED_THRESHOLD: float = 0.5

#over this nobody looking for work was ever on the other end, just a business texting ads
SPAM_THRESHOLD: float = 0.5

#three flavors of quiet, just went quiet, waiting on a date, or pushed back then ghosted
QUIET_KIND: str = "quiet"

EVENT_KIND: str = "event"

OBJECTION_KIND: str = "objection"

#even a meh lean gets its date read, missing one means pestering them the next morning
EVENT_THRESHOLD: float = 0.25

#the follow up lands the morning before the big day
EVENT_DAYS_BEFORE: int = 1

#and never the very next morning, no matter how close the big day is
EVENT_MIN_DAYS: int = 2

#a date more than a year out is the extractor daydreaming, nobody waits that long out loud
EVENT_MAX_DAYS: int = 366

#how the extractor writes the day, how the follow up reads it, and how the prints show it
EVENT_DATE_FORMAT: str = "%Y-%m-%d"

EVENT_DAY_FORMAT: str = "%A, %B %d, %Y"

EVENT_SEND_FORMAT: str = "%A, %B %d at %I:%M %p"

#the extractors line holds what they're waiting on and the date, in that order
EVENT_EXTRACTOR_FIELDS: list[str] = ["event", "date"]

FOLLOWUP_MAX_TOKENS: int = 10*100

FOLLOWUP_EFFORT: str = "high"

#flashx writes the sms middle at high, redone up to SMS_TRIES times when it can't go out
SMS_MAX_TOKENS: int = 10*100

SMS_EFFORT: str = "high"

SMS_TRIES: int = 3

#the middle stays one short sentence
SMS_MAIN_MAX_LENGTH: int = 160

#the shops ghl number only texts us and canada numbers, never an imessage email
SMS_NUMBER_PATTERN = re.compile(r"\+1\d{10}")

#a phone number written into the middle, which only the set call to text hazel ever has
SMS_PHONE_PATTERN = re.compile(r"\d{3}\D{0,2}\d{3}\D?\d{4}")

#the intro already greets them, so the middle never opens with one of these
SMS_GREETINGS: list[str] = ["hey", "heyy", "hi", "hello", "yo"]

#the middle starts lowercase after the intros comma, except these words
SMS_KEEP_CAPITALS: list[str] = ["I", "I'm", "I'll", "I've", "I'd"]

#the channel it goes out on, when they last wrote in, and how many went out since
FOLLOWUP_FIELDS: list[str] = ["channel", "last_message", "count"]

#when a check picked them, only on file till the mornings follow up takes it off
PICKED_FIELD: str = "prepped"

#blooio turned one down for the chats cap, nothing gets written till they text back or react
HELD_FIELD: str = "held"

#blooio quit taking texts early, so every follow up goes by sms till they text back or react
SMS_FIELD: str = "sms"

#they texted STOP to the shops sms number, so nothing goes out till they write in again
STOPPED_FIELD: str = "stopped"

#when there last follow up went out, the next one counts its gap from here
SENT_FIELD: str = "last_followup"

#the kind they got read as and the message it was read for, a new text gets a fresh look
KIND_FIELD: str = "kind"

NOTED_FIELD: str = "noted"

#what they're waiting on and when, only kept around while they're an event
EVENT_FIELDS: list[str] = ["event", "event_date"]


#ON FILE

#named like every key of theirs, what it is then there id
def followup_key(id: str) -> str:
    return f"followup_{id}"

#they wrote in, so the clock and the count start over and any pick or STOP comes off
def note_message(id: str, channel: str) -> None:
    try:
        log.write_info(followup_key(id), [channel, str(time.time()), "0"], FOLLOWUP_FIELDS)

        #a follow up picked for them comes off the dashboards follow ups page too
        if(log.take_info(followup_key(id), PICKED_FIELD)):
            dashboard.log_followup_dropped(id)

        #a STOP still standing in ghl stops them again when an sms comes up, and the gaps start fresh
        log.clear_info(followup_key(id), [STOPPED_FIELD, SENT_FIELD])

        #a form they filled in again never reached blooio, so only a text lifts its hold
        if(channel not in state_form.FORM_CHANNELS):
            release_followups(id)
    except Exception as error:
        #a note that fails only costs them a follow up, there reply still goes out
        print(f"FOLLOW UP NOTE ERROR: {error}")

#they answered by text or reaction, so blooio takes theirs again
def release_followups(id: str) -> None:
    #blooio takes texts to them again, so follow ups go back to it till its own run out
    log.clear_info(followup_key(id), [SMS_FIELD])

    if(log.take_info(followup_key(id), HELD_FIELD)):
        dashboard.log_followup_released(id)

        print(f"FOLLOW UP RELEASED: {id} answered, so blooio takes their follow ups again")

#a reaction lifts blooios hold like a text does, the count stays since they wrote nothing
def note_reaction(id: str) -> None:
    try:
        release_followups(id)
    except Exception as error:
        #a release that fails only keeps their follow ups held till they text
        print(f"FOLLOW UP REACTION ERROR: {error}")

#every conversation with follow ups on file, never the owners, he only answers color checks
def followup_ids() -> list[str]:
    ids: list[str] = []

    for key in log.matching_keys("followup_*"):
        id: str = key.removeprefix("followup_")

        #an old file of his from before he only answered color checks never gets one
        if(id != senders.OWNER_NUMBER):
            ids.append(id)

    return ids

#the booking guard saves the job on a yes to the schedule, so a job on file means booking
def went_to_booking(id: str) -> bool:
    return bool(log.read_state(f"s_p_confirmed_{id}"))

#a person has the conversation, so the system never reaches out to them on its own
def person_has_them(id: str) -> bool:
    return bool(log.read_state(f"restricted_{id}"))

#numbers need a real form name, spam texts never give one, meta chats always come with a name
def name_attached(id: str, channel: str) -> bool:
    if(channel in senders.META_CHANNELS):
        return True

    names: list[str] = log.read_info(f"lead_{id}").get("name", "").split()

    return len(names) > 0 and greeting.real_name(names[0])


#SPACING

#the shop day a moment falls on, so a gap counts mornings and never trips over a few minutes
def shop_day(moment: float):
    return datetime.fromtimestamp(moment, open_dates.SHOP_TIMEZONE).date()

#when there last follow up went out, ones from before the gaps went daily so its count days in
def last_followup_time(record: dict[str, str]) -> float:
    if(SENT_FIELD in record):
        return float(record[SENT_FIELD])

    return float(record.get("last_message", "0")) + int(record.get("count", "0")) * DAY_SECONDS

#days the next one waits after the last, by how many already went out with no answer
def gap_days(count: int) -> int:
    if(count <= len(FOLLOWUP_GAP_DAYS)):
        return FOLLOWUP_GAP_DAYS[count - 1]

    return FOLLOWUP_LATER_GAP_DAYS

#the first one goes the next morning like always, every one after it waits out its gap
def spaced_out(record: dict[str, str], send_time: float) -> bool:
    count: int = int(record.get("count", "0"))

    if(count == 0):
        return True

    days_since: int = (shop_day(send_time) - shop_day(last_followup_time(record))).days

    return days_since >= gap_days(count)


#ELIGIBILITY

#instagram and messenger only take a message inside a day of their last one, others always do
def window_open(channel: str, last_message: float, send_time: float) -> bool:
    if(channel not in senders.META_CHANNELS):
        return True

    return send_time - last_message < META_WINDOW_SECONDS

#only a us or canada number takes a text from the shops ghl number
def sms_reachable(id: str) -> bool:
    return SMS_NUMBER_PATTERN.fullmatch(id) is not None

#a text or form lead past blooios follow ups, one blooio quit on, or one on the shops sms line
def goes_by_sms(id: str, record: dict[str, str]) -> bool:
    if(senders.service_of(record.get("channel", "")) != "blooio"):
        return False

    if(SMS_FIELD in record or int(record.get("count", "0")) >= BLOOIO_FOLLOWUPS):
        return True

    #the shops sms number is already their line, so theirs go out on it from the first one
    return senders.on_sms_line(id)

#the shop reached them on its sms number, a follow up from before the line got marked counts too
def sms_reply_expected(id: str) -> bool:
    if(senders.on_sms_line(id)):
        return True

    try:
        record: dict[str, str] = log.read_info(followup_key(id))
    except Exception as error:
        #a failed read leaves their sms with the owner, who sees it in ghl like always
        print(f"SMS LINE READ ERROR: {error}, so the sms from {id} stays with the owner")

        return False

    count: int = int(record.get("count", "0"))

    #past blooios follow ups at least one went out by sms, same when blooio quit on them early
    return count > BLOOIO_FOLLOWUPS or (SMS_FIELD in record and count > 0)

#true when nothing on file rules them out, the gauntlet every follow up runs before it goes
def followup_allowed(id: str, record: dict[str, str], booked: bool, restricted: bool, named: bool, send_time: float) -> bool:
    channel: str = record.get("channel", "")

    if(channel == "" or booked or restricted or not named):
        return False

    #blooio turned there last one down for the chats cap, nothing gets written till they answer
    if(HELD_FIELD in record):
        return False

    #they texted STOP to the shops sms number, so nothing goes out till they write in again
    if(STOPPED_FIELD in record):
        return False

    #blooios follow ups are done and the shops ghl number can't text them, so theirs end there
    if(goes_by_sms(id, record) and not sms_reachable(id)):
        return False

    channel_limit: int | None = CHANNEL_FOLLOWUPS.get(channel)

    if(channel_limit is not None and int(record.get("count", "0")) >= channel_limit):
        return False

    last_message: float = float(record.get("last_message", "0"))

    #still texting the morning it would go out, so theirs waits for the next one
    if(send_time - last_message < QUIET_SECONDS):
        return False

    #there last follow up went out too recently, so this one waits out its gap
    if(not spaced_out(record, send_time)):
        return False

    return window_open(channel, last_message, send_time)

#the conversation with nothing new from them, what the check and the follow up both read
def quiet_state(id: str) -> dict:
    empty_message: dict = {"user_media": {}, "user_text": ""}

    return state_build.state_formulation(empty_message, state_build.message_history_read(id))

#done for good and spam rule them out, the kind only gets asked when its not on file yet
def night_questions(kind_asked: bool) -> dict:
    questions: dict = {}

    questions["not_interested"] = {"type": "noul", "instructions": f"Is the customer completely not interested, done with the shop for good going by the whole conversation in `message_history`?\n{followup_examples.not_interested_examples()}"}

    questions["spam"] = {"type": "noul", "instructions": f"Is this conversation spam, with nobody looking to get work done on a vehicle ever on the other end, going by every message of theirs in `message_history`?\n{followup_examples.spam_examples()}"}

    if(kind_asked):
        questions["kind"] = {"type": "choice", "instructions": f"Which kind of follow up fits where the customer left the conversation, going by every message of theirs in `message_history`?\n{followup_examples.kind_examples()}", "criteria": followup_examples.kind_criteria()}

    return questions

#one call for why they're ruled out, empty string when they aren't, plus the kinds answer
def night_read(state: dict, kind_asked: bool) -> tuple[str, dict]:
    answers: dict = models.decision_answers(night_questions(kind_asked), state)

    not_interested_yes: float = answers["not_interested"]["noul"]

    spam_yes: float = answers["spam"]["noul"]

    kind_answer: dict = answers.get("kind", {})

    kind_text: str = ""

    if(kind_answer):
        kind_text = f" | KIND: {kind_answer['choice']}({kind_answer['confidence']:.2f})"

    print(f"NOT INTERESTED: {not_interested_yes:.2f} | SPAM: {spam_yes:.2f}{kind_text}")

    if(spam_yes > SPAM_THRESHOLD):
        return ("is spam, never a customer", kind_answer)

    if(not_interested_yes > NOT_INTERESTED_THRESHOLD):
        return ("is done with the shop for good", kind_answer)

    return ("", kind_answer)


#KIND

#already read for there last message, so it stands till they text again
def kind_noted(record: dict[str, str]) -> bool:
    return record.get(NOTED_FIELD, "") != "" and record.get(NOTED_FIELD) == record.get("last_message")

#what they're waiting on and when, dressed up for the follow up, empty unless they're an event
def noted_event(record: dict[str, str]) -> dict[str, str]:
    if(record.get(KIND_FIELD) != EVENT_KIND or record.get("event", "") == ""):
        return {}

    day = datetime.strptime(record["event_date"], EVENT_DATE_FORMAT)

    return {"event": record["event"], "date": day.strftime(EVENT_DAY_FORMAT)}

#the quiet chat, there newest messages time and the day noted last time, so a date never drifts
def event_input(state: dict, record: dict[str, str]) -> str:
    last_message_at: str = datetime.fromtimestamp(float(record.get("last_message", "0")), open_dates.SHOP_TIMEZONE).strftime(state_form.CURRENT_DATE_TIME_FORMAT)

    event_text: str = f"STATE: {state_form.state_to_text(state)}\nLAST_MESSAGE_AT: {last_message_at}"

    noted: dict[str, str] = noted_event(record)

    if(noted):
        event_text += f"\nNOTED_EVENT: {noted['event']} on {noted['date']}"

    return event_text

#the day they gave, None when its no real day, before there newest message or way too far out
def event_day(date_text: str, last_message: float):
    try:
        day = datetime.strptime(date_text, EVENT_DATE_FORMAT).date()
    except ValueError:
        return None

    wrote_day = datetime.fromtimestamp(last_message, open_dates.SHOP_TIMEZONE).date()

    if(day < wrote_day or day > wrote_day + timedelta(days=EVENT_MAX_DAYS)):
        return None

    return day

#what they're waiting on and when, both empty when the date is missing or makes no sense
def read_event(state: dict, record: dict[str, str]) -> tuple[str, str]:
    values: list[str] = models.extractor_values(models.extract_event(event_input(state, record)), EVENT_EXTRACTOR_FIELDS)

    if(len(values) < len(EVENT_EXTRACTOR_FIELDS) or values[0] == "" or event_day(values[1], float(record.get("last_message", "0"))) is None):
        return ("", "")

    return (values[0], values[1])

#an event only counts with a real date, otherwise whichever of the other two came out ahead
def note_kind(id: str, record: dict[str, str], state: dict, kind_answer: dict) -> dict[str, str]:
    probabilities: dict[str, float] = kind_answer["probabilities"]

    kind: str = kind_answer["choice"]

    event: tuple[str, str] = ("", "")

    if(kind == EVENT_KIND or probabilities.get(EVENT_KIND, 0.0) > EVENT_THRESHOLD):
        event = read_event(state, record)

        kind = EVENT_KIND

        if(event[0] == ""):
            kind = QUIET_KIND

            if(probabilities.get(OBJECTION_KIND, 0.0) > probabilities.get(QUIET_KIND, 0.0)):
                kind = OBJECTION_KIND

    log.write_info(followup_key(id), [kind, record.get("last_message", "")], [KIND_FIELD, NOTED_FIELD])

    if(kind == EVENT_KIND):
        log.write_info(followup_key(id), list(event), EVENT_FIELDS)
    else:
        log.clear_info(followup_key(id), EVENT_FIELDS)

    noted: dict[str, str] = log.read_info(followup_key(id))

    event_noted: dict[str, str] = noted_event(noted)

    if(event_noted):
        print(f"FOLLOW UP KIND: {id} is waiting on {event_noted['event']} on {event_noted['date']}")
    else:
        print(f"FOLLOW UP KIND: {id} gets the {kind} follow up")

    return noted

#the morning before the big day, but never the very next morning after they last wrote
def event_send_time(record: dict[str, str]) -> float:
    coming = datetime.strptime(record["event_date"], EVENT_DATE_FORMAT).date()

    wrote_day = datetime.fromtimestamp(float(record.get("last_message", "0")), open_dates.SHOP_TIMEZONE).date()

    send_day = max(coming - timedelta(days=EVENT_DAYS_BEFORE), wrote_day + timedelta(days=EVENT_MIN_DAYS))

    return datetime(send_day.year, send_day.month, send_day.day, FOLLOWUP_HOUR, tzinfo=open_dates.SHOP_TIMEZONE).timestamp()

#true when they're waiting on a later morning, said once a night so the logs aren't a mystery
def event_wait(id: str, record: dict[str, str], booked: bool, restricted: bool, named: bool, send_time: float) -> bool:
    event: dict[str, str] = noted_event(record)

    if(not event):
        return False

    event_time: float = event_send_time(record)

    #the morning before it, or the server missed that one and its late, either way it goes now
    if(event_time <= send_time):
        return False

    when: str = datetime.fromtimestamp(event_time, open_dates.SHOP_TIMEZONE).strftime(EVENT_SEND_FORMAT)

    #metas window closes a day after there last message, so these can't wait it out
    if(not followup_allowed(id, record, booked, restricted, named, event_time)):
        print(f"FOLLOW UP SKIPPED: {id} is waiting on {event['event']} on {event['date']}, and {record.get('channel', '')} takes no follow up by {when}")

        return True

    print(f"FOLLOW UP WAITING: {id} is waiting on {event['event']} on {event['date']}, so theirs goes out {when}")

    return True


#NIGHTLY PICK

#the next time the hour and minute come around in the shops time, later today or else tomorrow
def next_run(hour: int, minute: int, now):
    run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if(run_time <= now):
        run_time = run_time + timedelta(days=1)

    return run_time

#seconds till that hour and minute in the shops time, timestamps keep daylight savings honest
def seconds_until(hour: int, minute: int) -> float:
    now = datetime.now(open_dates.SHOP_TIMEZONE)

    return next_run(hour, minute, now).timestamp() - now.timestamp()

#when the mornings check runs, RECHECK_MINUTES before the send
def recheck_time() -> tuple[int, int]:
    minutes: int = FOLLOWUP_HOUR * 60 - RECHECK_MINUTES

    return (minutes // 60, minutes % 60)

#every pick starts over, and the model only reads the ones nothing on file rules out
def prep_followup(id: str, send_time: float) -> None:
    log.clear_info(followup_key(id), [PICKED_FIELD])

    record: dict[str, str] = log.read_info(followup_key(id))

    named: bool = name_attached(id, record.get("channel", ""))

    booked: bool = went_to_booking(id)

    restricted: bool = person_has_them(id)

    if(not followup_allowed(id, record, booked, restricted, named, send_time)):
        #a missing name is the one rule out worth saying, so the night shows who it left out
        if(not named):
            print(f"FOLLOW UP SKIPPED: {id} has no name on file")

        return

    kind_asked: bool = not kind_noted(record)

    #already read and still waiting, so no model calls, just counting sleeps
    if(not kind_asked and event_wait(id, record, booked, restricted, named, send_time)):
        return

    state: dict = quiet_state(id)

    night_answer: tuple[str, dict] = night_read(state, kind_asked)

    if(night_answer[0] != ""):
        print(f"FOLLOW UP SKIPPED: {id} {night_answer[0]}")

        return

    if(kind_asked):
        record = note_kind(id, record, state, night_answer[1])

        if(event_wait(id, record, booked, restricted, named, send_time)):
            return

    log.write_info(followup_key(id), [str(time.time())], [PICKED_FIELD])

    #the dashboards follow ups page shows them getting it at the mornings send
    dashboard.log_followup_picked(id, record["channel"], int(record.get("count", "0")) + 1, send_time)

    print(f"FOLLOW UP PICKED: {id} gets their {record.get(KIND_FIELD, QUIET_KIND)} follow up on {record['channel']} in the morning")

#runs every night, and one conversation that breaks never stops the rest from getting picked
def prep_followups() -> None:
    #on file first, so a text landing mid run still gets read again by the mornings check
    log.write_state(NIGHT_PICK_KEY, {"at": time.time()})

    send_time: float = next_run(FOLLOWUP_HOUR, 0, datetime.now(open_dates.SHOP_TIMEZONE)).timestamp()

    #the dashboards pick starts over too, so a missed morning leaves nobody listed
    dashboard.clear_past_followups()

    ids: list[str] = followup_ids()

    print(f"FOLLOW UP PICK: checking {len(ids)} conversation(s) for the morning's follow ups")

    for id in ids:
        #each pick prints as its own block, so a live batch never lands in the middle of it
        held_token = prints.hold()

        try:
            prep_followup(id, send_time)
        except Exception as error:
            print(f"FOLLOW UP PICK ERROR: {id}, {error}")
        finally:
            prints.release(held_token)


#MORNING CHECK

#when the nights check last started, zero when it didn't run in the last day
def night_pick_time() -> float:
    night_pick: dict | str = log.read_state(NIGHT_PICK_KEY)

    if(not isinstance(night_pick, dict)):
        return 0.0

    picked_at: float = float(night_pick.get("at", 0))

    if(time.time() - picked_at > NIGHT_PICK_SECONDS):
        return 0.0

    return picked_at

#runs RECHECK_MINUTES before the send, one broken conversation never stops the rest
def recheck_followups() -> None:
    send_time: float = next_run(FOLLOWUP_HOUR, 0, datetime.now(open_dates.SHOP_TIMEZONE)).timestamp()

    picked_at: float = night_pick_time()

    ids: list[str] = followup_ids()

    print(f"FOLLOW UP RECHECK: checking {len(ids)} conversation(s) for anyone the night's pick missed before the morning's follow ups")

    for id in ids:
        #each check prints as its own block, so a live batch never lands in the middle of it
        held_token = prints.hold()

        try:
            record: dict[str, str] = log.read_info(followup_key(id))

            #the night picked them or already ruled them out, nothing of theirs came in after it
            if(PICKED_FIELD in record or float(record.get("last_message", "0")) < picked_at):
                continue

            prep_followup(id, send_time)
        except Exception as error:
            print(f"FOLLOW UP RECHECK ERROR: {id}, {error}")
        finally:
            prints.release(held_token)


#MORNING SEND

#the quiet chat plus which follow up in a row, what kind they are, and what they're waiting on
def followup_state(id: str, record: dict[str, str]) -> dict:
    state: dict = quiet_state(id)

    #which follow up in a row this is, so a later one never says an earlier one again
    state["followup_number"] = int(record.get("count", "0")) + 1

    #picked before kinds existed, so its a regular one
    state["followup_kind"] = record.get(KIND_FIELD, QUIET_KIND)

    event: dict[str, str] = noted_event(record)

    if(event):
        state["followup_event"] = event

    return state

#the follow up written from the quiet conversation, shaped for run_chain so it gets retries
def followup_chain(state: dict, id: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    followup_text: str = f"STATE: {state_as_text}"

    system_prompt: str = followup_generator.prompt()

    followup: str = models.generator("FOLLOW UP GENERATOR", system_prompt, followup_text, FOLLOWUP_MAX_TOKENS, FOLLOWUP_EFFORT, line_breaks=False)

    #it asks again what the last message asked, so never in the words that already went out
    return branches.asked_again_reply(state, followup)

#the follow up in the owners wording, empty when it couldn't be written or got stopped
def written_followup(id: str, channel: str, record: dict[str, str]) -> str:
    state: dict = followup_state(id, record)

    followup: str = retry.run_chain(followup_chain, state, id, [], channel, "FOLLOW UP CHAIN ERROR")

    if(followup == ""):
        return followup

    #never asks there color before what the exact price needs, same as every other reply
    followup = routing.cut_early_color_ask(state, id, followup)

    #a follow up picks the conversation back up, so hazels heyy stays on it
    followup = wording.wording_rules(followup, channel, state["message_history"], [], [], follow_up=True)

    return replies.cleared_reply(id, channel, followup)

#the follow up cut into texts, glued back into one over blooio since each text eats the cap
def followup_texts(followup: str, channel: str) -> list[str]:
    texts: list[str] = spacing.split_texts(followup)

    if(senders.service_of(channel) != "blooio"):
        return texts

    return [spacing.one_text(texts)]

#blooio turned theirs down for the chats cap, so they sit on hold till they text back or react
def hold_followups(id: str, channel: str) -> None:
    log.write_info(followup_key(id), [str(time.time())], [HELD_FIELD])

    dashboard.log_followup_held(id, channel)

    print(f"FOLLOW UP HELD: blooio takes no more texts to {id} till they text back or react, so theirs wait till then")

#they wrote in after the mornings send read them, so the reply to that answers them instead
def wrote_back(id: str, record: dict[str, str]) -> bool:
    return log.read_info(followup_key(id)).get("last_message") != record.get("last_message")

#only the run that takes the pick off file sends it, so nobody gets texted twice
def send_followup(id: str) -> None:
    if(not log.take_info(followup_key(id), PICKED_FIELD)):
        return

    record: dict[str, str] = log.read_info(followup_key(id))

    channel: str = record.get("channel", "")

    #booking, a person, no name, metas window or the dashboard switch can still call it off
    if(not followup_allowed(id, record, went_to_booking(id), person_has_them(id), name_attached(id, channel), time.time()) or not dashboard.switched_on(id, channel)):
        return

    count: int = int(record.get("count", "0"))

    #blooio is done with them, so this one goes by sms from the shops ghl number
    if(goes_by_sms(id, record)):
        send_sms_followup(id, channel, count, record)

        return

    followup: str = written_followup(id, channel, record)

    #they wrote back while it was being written, so the reply to that answers them instead
    if(followup == "" or wrote_back(id, record)):
        return

    texts: list[str] = followup_texts(followup, channel)

    delivery: tuple = senders.send_texts(id, channel, texts, is_followup=True)

    #what went out, and whether blooio held the rest back for the chats cap
    texts_sent: list[str] = delivery[0]

    capped: bool = delivery[2]

    #blooio quit on them before its follow ups ran out, so this one and the rest go by sms
    if(capped and len(texts_sent) == 0 and sms_reachable(id)):
        log.write_info(followup_key(id), [str(time.time())], [SMS_FIELD])

        print(f"FOLLOW UP MOVED TO SMS: blooio takes no more texts to {id}, so this one and the rest go by sms")

        send_sms_followup(id, channel, count, record)

        return

    #no sms for them either, so they wait on blooio till they text back or react
    if(capped):
        hold_followups(id, channel)

    if(len(texts_sent) == 0):
        #a hold already said why nothing went out
        if(not capped):
            print(f"FOLLOW UP NOT SENT: {senders.service_of(channel)} refused it for {id} on {channel}, so nothing of it goes on file")

        return

    #only what reached them goes on file, so the next one never assumes they read the rest
    went_out: str = followup

    if(len(texts_sent) < len(texts)):
        went_out = " ".join(texts_sent)

        print(f"FOLLOW UP PARTLY SENT to {id} on {channel}: {went_out}")
    else:
        print(f"FOLLOW UP SENT to {id} on {channel}: {followup}")

    #nothing of theirs came in before it, so it joins the shops last reply in their history
    log.add_to_last_message(f"systemres_{id}", went_out)

    #when it went out goes on file with the count, so the next one waits out its gap from here
    log.write_info(followup_key(id), [str(count + 1), str(time.time())], ["count", SENT_FIELD])

    #the dashboard moves them from the mornings list to the ones that went out
    dashboard.log_followup_sent(id, channel, count + 1)

#runs every morning, and one conversation that breaks never stops the rest from getting theirs
def send_followups() -> None:
    for id in followup_ids():
        #each follow up prints as its own block, so a live batch never lands in the middle of it
        held_token = prints.hold()

        try:
            send_followup(id)
        except Exception as error:
            print(f"FOLLOW UP SEND ERROR: {id}, {error}")
        finally:
            prints.release(held_token)

    #everyone picked went out or got called off by now, so the leftovers come off the list
    dashboard.clear_past_followups()


#SMS FOLLOWUPS

#the middle tidied to follow the intros comma, plain, unquoted, lowercase start, period end
def sms_main(written: str) -> str:
    main: str = senders.sms_plain(written).strip('"').strip()

    if(main == ""):
        return main

    first_word: str = main.split(" ", 1)[0]

    #a capital opener goes lowercase after the comma, but PPF or I'm keep their capitals
    if(first_word not in SMS_KEEP_CAPITALS and first_word[:1].isupper() and first_word[1:] == first_word[1:].lower()):
        main = main[0].lower() + main[1:]

    #a question keeps its mark, so the check turns it down instead of a period hiding it
    if(main[-1] not in ".!?"):
        main = f"{main}."

    return main

#why the written middle can't go out, empty when it can
def sms_main_problem(main: str) -> str:
    lowered: str = main.lower()

    if(main == ""):
        return "it's empty"

    if("?" in main):
        return "it asks a question, the text after it already says what to do"

    if(lowered.split(" ", 1)[0].strip(",.!") in SMS_GREETINGS):
        return "it greets them, the intro already does"

    if("lone wraps" in lowered or "hazel" in lowered):
        return "it names the shop or Hazel, the text around it already does"

    if(senders.LINK_PATTERN.search(main) or SMS_PHONE_PATTERN.search(main)):
        return "it has a link or a phone number, only the text after it gives Hazel's number"

    if(len(main) > SMS_MAIN_MAX_LENGTH):
        return f"it runs past {SMS_MAIN_MAX_LENGTH} characters, it has to be one short sentence"

    return ""

#flashx writes the middle, a bad one gets redone with why, up to SMS_TRIES, empty if none pass
def sms_main_chain(state: dict, id: str) -> str:
    system_prompt: str = sms_prompt.prompt()

    sms_input: str = f"STATE: {state_form.state_to_text(state)}"

    for attempt in range(1, SMS_TRIES + 1):
        written: str = models.generator("SMS FOLLOW UP GENERATOR", system_prompt, sms_input, SMS_MAX_TOKENS, SMS_EFFORT, line_breaks=False)

        main: str = sms_main(written)

        problem: str = sms_main_problem(main)

        if(problem == ""):
            return main

        print(f"SMS FOLLOW UP TRY {attempt} CAN'T GO OUT, {problem}: {written}")

        #the next try sees what broke and why, so it never writes the same one again
        sms_input += f"\nCAN'T GO OUT: {written.strip()} ({problem})"

    return ""

#the middle written from the quiet conversation, run like every chain so it gets retries
def written_sms_main(id: str, channel: str, record: dict[str, str]) -> str:
    return retry.run_chain(sms_main_chain, followup_state(id, record), id, [], channel, "SMS FOLLOW UP CHAIN ERROR")

#the first name off there form, else the one ghl has for them, empty when neither is a real name
def sms_name(id: str, details: dict) -> str:
    name: str = greeting.form_first_name({"name": log.read_info(f"lead_{id}").get("name", ""), "first_name": ""})

    if(name == ""):
        first_name: str | None = details.get("firstName")

        if(not first_name):
            first_name = ""

        name = greeting.form_first_name({"name": str(first_name), "first_name": ""})

    return name

#the set intro, the written middle, then the set call to text hazel and the opt out
def sms_text(name: str, main: str) -> str:
    intro: str = sms_prompt.INTRO_NO_NAME

    if(name != ""):
        intro = sms_prompt.INTRO.format(name=name)

    return f"{intro} {main} {sms_prompt.CTA} {sms_prompt.ENDING}"

#they texted STOP to the shops sms number, so none go out till they write in again
def stop_followups(id: str) -> None:
    log.write_info(followup_key(id), [str(time.time())], [STOPPED_FIELD])

    print(f"FOLLOW UP STOPPED: {id} texted STOP to the shop's sms number, so none go out till they write in again")

#a STOP in ghl calls it off before anything gets written, and only an sms that went out goes on file
def send_sms_followup(id: str, channel: str, count: int, record: dict[str, str]) -> None:
    contact: str = ghl.contact_id(id)

    details: dict = ghl.contact_details(contact)

    if(ghl.sms_stopped(details)):
        stop_followups(id)

        return

    main: str = written_sms_main(id, channel, record)

    if(main == ""):
        print(f"SMS FOLLOW UP NOT SENT: no middle for {id} could go out, so theirs tries again tomorrow")

        return

    #they wrote back while it was being written, so the reply to that answers them instead
    if(wrote_back(id, record)):
        return

    #the whole sms gets the same final check as every reply
    text: str = replies.cleared_reply(id, channel, sms_text(sms_name(id, details), main))

    if(text == ""):
        return

    if(not senders.send_sms_text(id, channel, contact, text)):
        print(f"SMS FOLLOW UP NOT SENT: ghl refused it for {id} on {channel}, so nothing of it goes on file")

        return

    print(f"SMS FOLLOW UP SENT to {id} on {channel}: {text}")

    #nothing of theirs came in before it, so it joins the shops last reply in there history
    log.add_to_last_message(f"systemres_{id}", text)

    #when it went out goes on file with the count, so the next one waits out its gap from here
    log.write_info(followup_key(id), [str(count + 1), str(time.time())], ["count", SENT_FIELD])

    #the shops number is their line now, so an sms back from them reaches hazel and gets her reply
    senders.open_sms_line(id)

    #the dashboard moves them to the ones that went out, in green
    dashboard.log_followup_sent(id, channel, count + 1, sms=True)
