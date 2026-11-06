#**********IMPORTS**********
#python's clock and patterns, the shop's timezone, the reply writer and its final check, the senders, the form name check, the conversation on file, the dashboard's switch and follow ups page, ghl for the sms ones, the held prints, the early color ask cut, the asked again check, and the follow up and sms prompts
import re
import time
from datetime import date, datetime, timedelta

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



#**********GLOBALS**********
#when the follow ups get picked and sent, how many each channel gets, what kind each one is, and how each one gets written


#FOLLOW UP TIMES
#every night at this hour in the shop's time the quiet conversations get checked
PREP_HOUR: int = 22

#and the next morning at this hour the ones picked get their follow up, with the shop open to answer them
FOLLOWUP_HOUR: int = 10

#this many minutes before the morning's send, everyone the night's check never read as they are now gets checked, so a text in the night never costs anyone their follow up
RECHECK_MINUTES: int = 10


#QUIET TIME
#a follow up only goes to a conversation that's been quiet this long when it goes out, so the morning's check takes in a text from the night, up till 6AM, and never one from someone still texting that morning
QUIET_SECONDS: int = 4 * 3600


#NIGHT PICK
#when the night's check last started, so the morning's check skips everyone it already read as they are now, never named followup_ so it's never taken for a conversation
NIGHT_PICK_KEY: str = "followups_night_pick"

#a night's check older than this didn't run last night, like the server being down for it, so the morning's check reads everyone it didn't pick
NIGHT_PICK_SECONDS: int = 24 * 3600


#FOLLOW UPS PER CHANNEL
#how many follow ups in a row a channel gets with no answer, instagram only ever gets one, a channel not here gets one every day till they answer
CHANNEL_FOLLOWUPS: dict[str, int] = {"ig": 1}


#BLOOIO FOLLOW UPS
#how many follow ups in a row a text or form lead gets over blooio with no answer, every one after that goes by sms from the shop's ghl number
BLOOIO_FOLLOWUPS: int = 3


#META WINDOW
#instagram and messenger refuse any message sent more than a day after the customer's last one, so a follow up there only goes out inside it
META_WINDOW_SECONDS: int = 24 * 3600


#NOT INTERESTED
#a yes over this means they're done with the shop for good, over half so a customer the check is torn on still gets their follow up
NOT_INTERESTED_THRESHOLD: float = 0.5


#SPAM
#a yes over this means nobody looking to get work done was ever on the other end, like a business texting ads, alerts or links, so they never get one
SPAM_THRESHOLD: float = 0.5


#FOLLOW UP KINDS
#three flavors of quiet: just went quiet, waiting on something with a date on it, or pushed back then ghosted
QUIET_KIND: str = "quiet"

EVENT_KIND: str = "event"

OBJECTION_KIND: str = "objection"


#EVENT CHANCE
#even a meh lean towards waiting gets its date read, missing one means texting them the next morning, the one thing they asked us not to do
EVENT_THRESHOLD: float = 0.25


#EVENT TIMING
#the follow up lands the morning before the big day
EVENT_DAYS_BEFORE: int = 1

#and never the very next morning, no matter how close the big day is
EVENT_MIN_DAYS: int = 2

#a date more than a year out is the extractor daydreaming, nobody waits that long out loud
EVENT_MAX_DAYS: int = 366


#EVENT DATES
#how the extractor writes the day, how the follow up reads it, "Thursday, November 12, 2026", and how the prints show off when it goes out
EVENT_DATE_FORMAT: str = "%Y-%m-%d"

EVENT_DAY_FORMAT: str = "%A, %B %d, %Y"

EVENT_SEND_FORMAT: str = "%A, %B %d at %I:%M %p"

#the extractor's line, EVENT: <what they're waiting on> | DATE: <YYYY-MM-DD>
EVENT_EXTRACTOR_FIELDS: list[str] = ["event", "date"]


#FOLLOW UP LIMITS
FOLLOWUP_MAX_TOKENS: int = 10*100

FOLLOWUP_EFFORT: str = "high"


#SMS FOLLOW UP LIMITS
#flashx writes the middle of the sms at high, and a middle that can't go out gets written again, up to SMS_TRIES in all
SMS_MAX_TOKENS: int = 10*100

SMS_EFFORT: str = "high"

SMS_TRIES: int = 3

#the middle stays one short sentence
SMS_MAIN_MAX_LENGTH: int = 160


#SMS NUMBER
#the shop's number in ghl only texts us and canada numbers, never an imessage email or a number from another country
SMS_NUMBER_PATTERN: re.Pattern = re.compile(r"\+1\d{10}")


#SMS CHARACTERS
#one curly quote, long dash or emoji turns the whole sms into the kind that splits every 70 characters, so they become plain ones or come off
SMS_PLAIN_CHARACTERS: dict[str, str] = {"’": "'", "‘": "'", "“": '"', "”": '"', "—": "-", "–": "-", "…": "..."}

SMS_EMOJI_PATTERN: re.Pattern = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]")


#SMS PHONE NUMBER
#a phone number written into the middle, which only the set call to text hazel ever has
SMS_PHONE_PATTERN: re.Pattern = re.compile(r"\d{3}\D{0,2}\d{3}\D?\d{4}")


#SMS GREETINGS
#the intro already greets them, so the middle never opens with one of these
SMS_GREETINGS: list[str] = ["hey", "heyy", "hi", "hello", "yo"]


#SMS CAPITALS
#the middle goes on from the intro's comma in lowercase, except for these words that always keep their capital
SMS_KEEP_CAPITALS: list[str] = ["I", "I'm", "I'll", "I've", "I'd"]


#FOLLOW UP FIELDS
#what each conversation keeps on file for its follow ups: the channel it goes out on, when they last wrote in, and how many went out since
FOLLOWUP_FIELDS: list[str] = ["channel", "last_message", "count"]

#when the night or the morning's check picked them, only on file till the morning's follow up takes it off
PICKED_FIELD: str = "prepped"

#when blooio turned one down because the chat used up the texts it takes with no answer, on file till they text back or react, and none get written for them till then
HELD_FIELD: str = "held"

#when blooio stopped taking texts to them before its follow ups ran out, on file till they text back or react, and every follow up till then goes by sms
SMS_FIELD: str = "sms"

#when ghl showed they texted STOP to the shop's sms number, on file till they write in again, and no follow up goes out till then
STOPPED_FIELD: str = "stopped"

#the kind they got read as and the last message it was read for, so one read covers the whole quiet stretch and a new text gets a fresh look
KIND_FIELD: str = "kind"

NOTED_FIELD: str = "noted"

#what they're waiting on and when, only kept around while they're an event
EVENT_FIELDS: list[str] = ["event", "event_date"]



#**********ON FILE**********
#what each conversation keeps on file for its follow ups, written every time they message


#FOLLOW UP KEY
#named <what it is>_<id> like every key of theirs
def followup_key(id: str) -> str:
    return f"followup_{id}"


#NOTE MESSAGE
#they wrote in, so the channel and the time go on file, the count starts over, a follow up picked for them is off, a STOP from before no longer keeps theirs off, and a text to the shop lifts blooio's hold on them
def note_message(id: str, channel: str) -> None:
    try:
        log.write_info(followup_key(id), [channel, str(time.time()), "0"], FOLLOWUP_FIELDS)

        #a follow up picked for them comes off the dashboard's follow ups page too
        if(log.take_info(followup_key(id), PICKED_FIELD)):
            dashboard.log_followup_dropped(id)

        #writing in starts them over, and a STOP that still stands in ghl stops them again when an sms comes up
        log.clear_info(followup_key(id), [STOPPED_FIELD])

        #a form they filled in again never reached blooio, so only a text lifts its hold
        if(channel not in state_form.FORM_CHANNELS):
            release_followups(id)

    #a note that fails only costs them a follow up, their reply still goes out
    except Exception as error:
        print(f"FOLLOW UP NOTE ERROR: {error}")


#RELEASE FOLLOW UPS
#they texted back or reacted, which blooio counts as an answer, so it takes texts to them again and their follow ups pick back up there
def release_followups(id: str) -> None:
    #blooio takes texts to them again, so follow ups go back to it till its own run out
    log.clear_info(followup_key(id), [SMS_FIELD])

    if(log.take_info(followup_key(id), HELD_FIELD)):
        dashboard.log_followup_released(id)

        print(f"FOLLOW UP RELEASED: {id} answered, so blooio takes their follow ups again")


#NOTE REACTION
#they reacted to a text, which lifts blooio's hold the same as a text, the count stays since they wrote nothing
def note_reaction(id: str) -> None:
    try:
        release_followups(id)

    #a release that fails only keeps their follow ups held till they text
    except Exception as error:
        print(f"FOLLOW UP REACTION ERROR: {error}")


#FOLLOW UP IDS
#every conversation with follow ups on file, never the owner's number, which only answers color checks, so nothing he texts back would ever stop them
def followup_ids() -> list[str]:
    ids: list[str] = []

    for key in log.matching_keys("followup_*"):
        id: str = key.removeprefix("followup_")

        #a conversation of his on file from before his number only answered color checks never gets one
        if(id != senders.OWNER_NUMBER):
            ids.append(id)

    return ids


#WENT TO BOOKING
#the booking guard saves the job the moment they say yes to getting on the schedule, so a job on file means they went to booking
def went_to_booking(id: str) -> bool:
    return bool(log.read_state(f"s_p_confirmed_{id}"))


#PERSON HAS THEM
#a person has the conversation, so the bot never reaches out to them on its own
def person_has_them(id: str) -> bool:
    return bool(log.read_state(f"restricted_{id}"))


#NAME ATTACHED
#a number only gets a follow up with a real name on file from their quote form, someone who only ever texted the shop's number never gave one, and that's where spam texts come from
#instagram and messenger chats always come with the name they go by there
def name_attached(id: str, channel: str) -> bool:
    if(channel in senders.META_CHANNELS):
        return True

    names: list[str] = log.read_info(f"lead_{id}").get("name", "").split()

    return len(names) > 0 and greeting.real_name(names[0])



#**********WHO GETS ONE**********
#the checks that need no model, then the not interested and spam checks the decisions model makes on the whole conversation, with the kind of follow up riding along on the same call


#WINDOW OPEN
#instagram and messenger only take a message inside a day of their last one, every other channel always takes one
def window_open(channel: str, last_message: float, send_time: float) -> bool:
    if(channel not in senders.META_CHANNELS):
        return True

    return send_time - last_message < META_WINDOW_SECONDS


#SMS REACHABLE
#only a us or canada number takes a text from the shop's ghl number, never an imessage email or a number from another country
def sms_reachable(id: str) -> bool:
    return SMS_NUMBER_PATTERN.fullmatch(id) is not None


#GOES BY SMS
#a text or form lead past blooio's follow ups, or one blooio stopped taking texts to before those ran out
def goes_by_sms(record: dict[str, str]) -> bool:
    if(senders.service_of(record.get("channel", "")) != "blooio"):
        return False

    return SMS_FIELD in record or int(record.get("count", "0")) >= BLOOIO_FOLLOWUPS


#FOLLOW UP ALLOWED
#True when nothing on file rules a follow up out: they never went to booking, nobody has them, a number has a name on file, blooio isn't holding their chat, they never texted STOP, a lead past blooio's follow ups can get an sms, their channel's count isn't used up, they've been quiet long enough and meta's window is still open when it goes out
def followup_allowed(id: str, record: dict[str, str], booked: bool, restricted: bool, named: bool, send_time: float) -> bool:
    channel: str = record.get("channel", "")

    if(channel == "" or booked or restricted or not named):
        return False

    #blooio turned their last one down for the chat's cap, so nothing gets written for them till they text back or react
    if(HELD_FIELD in record):
        return False

    #they texted STOP to the shop's sms number, so nothing goes out till they write in again
    if(STOPPED_FIELD in record):
        return False

    #blooio's follow ups are done and the shop's ghl number can't text them, so theirs end there
    if(goes_by_sms(record) and not sms_reachable(id)):
        return False

    channel_limit: int | None = CHANNEL_FOLLOWUPS.get(channel)

    if(channel_limit is not None and int(record.get("count", "0")) >= channel_limit):
        return False

    last_message: float = float(record.get("last_message", "0"))

    #still texting the morning it would go out, so theirs waits for the next one
    if(send_time - last_message < QUIET_SECONDS):
        return False

    return window_open(channel, last_message, send_time)


#QUIET STATE
#the conversation and the shop's time with nothing new from them, what the check and the follow up both read
def quiet_state(id: str) -> dict:
    empty_message: dict = {"user_media": {}, "user_text": ""}

    return state_build.state_formulation(empty_message, state_build.message_history_read(id))


#NIGHT QUESTIONS
#done for good and spam rule them out, the kind only gets asked when we don't already have it for their last message
def night_questions(kind_asked: bool) -> dict:
    questions: dict = {}

    questions["not_interested"] = {"type": "noul", "instructions": f"Is the customer completely not interested, done with the shop for good going by the whole conversation in `message_history`?\n{followup_examples.not_interested_examples()}"}

    questions["spam"] = {"type": "noul", "instructions": f"Is this conversation spam, with nobody looking to get work done on a vehicle ever on the other end, going by every message of theirs in `message_history`?\n{followup_examples.spam_examples()}"}

    if(kind_asked):
        questions["kind"] = {"type": "choice", "instructions": f"Which kind of follow up fits where the customer left the conversation, going by every message of theirs in `message_history`?\n{followup_examples.kind_examples()}", "criteria": followup_examples.kind_criteria()}

    return questions


#NIGHT READ
#one call does it all: why they're ruled out, done for good or spam ("" when neither), and the kind's answer ({} when we didn't ask)
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



#**********KIND**********
#which follow up they get, read once per quiet stretch: the regular one, one the morning before what they're waiting on, or a real check in after they pushed back


#KIND NOTED
#already read for their last message, so it stands till they text again
def kind_noted(record: dict[str, str]) -> bool:
    return record.get(NOTED_FIELD, "") != "" and record.get(NOTED_FIELD) == record.get("last_message")


#NOTED EVENT
#what they're waiting on and when, dressed up for the follow up to read, empty unless they're an event
def noted_event(record: dict[str, str]) -> dict[str, str]:
    if(record.get(KIND_FIELD) != EVENT_KIND or record.get("event", "") == ""):
        return {}

    day: datetime = datetime.strptime(record["event_date"], EVENT_DATE_FORMAT)

    return {"event": record["event"], "date": day.strftime(EVENT_DAY_FORMAT)}


#EVENT INPUT
#the quiet chat, when their newest message came in, and the day we noted last time, so a date they gave never drifts just because they texted again
def event_input(state: dict, record: dict[str, str]) -> str:
    last_message_at: str = datetime.fromtimestamp(float(record.get("last_message", "0")), open_dates.SHOP_TIMEZONE).strftime(state_form.CURRENT_DATE_TIME_FORMAT)

    event_text: str = f"STATE: {state_form.state_to_text(state)}\nLAST_MESSAGE_AT: {last_message_at}"

    noted: dict[str, str] = noted_event(record)

    if(noted):
        event_text += f"\nNOTED_EVENT: {noted['event']} on {noted['date']}"

    return event_text


#EVENT DAY
#the day the extractor gave, None when it's not a day or couldn't be one they said, before their newest message or way out past EVENT_MAX_DAYS
def event_day(date_text: str, last_message: float) -> date | None:
    try:
        day: date = datetime.strptime(date_text, EVENT_DATE_FORMAT).date()

    except ValueError:
        return None

    wrote_day: date = datetime.fromtimestamp(last_message, open_dates.SHOP_TIMEZONE).date()

    if(day < wrote_day or day > wrote_day + timedelta(days=EVENT_MAX_DAYS)):
        return None

    return day


#READ EVENT
#what they're waiting on and when, both empty when there's no date on the wait or the date makes no sense
def read_event(state: dict, record: dict[str, str]) -> tuple[str, str]:
    values: list[str] = models.extractor_values(models.extract_event(event_input(state, record)), EVENT_EXTRACTOR_FIELDS)

    if(len(values) < len(EVENT_EXTRACTOR_FIELDS) or values[0] == "" or event_day(values[1], float(record.get("last_message", "0"))) is None):
        return ("", "")

    return (values[0], values[1])


#NOTE KIND
#the kind goes on file with the message it was read for, an event only counts with a real date, otherwise whichever of the other two came out ahead
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


#EVENT SEND TIME
#the morning before the big day, but never sooner than the second morning after they last wrote, the next morning is off the table
def event_send_time(record: dict[str, str]) -> float:
    coming: date = datetime.strptime(record["event_date"], EVENT_DATE_FORMAT).date()

    wrote_day: date = datetime.fromtimestamp(float(record.get("last_message", "0")), open_dates.SHOP_TIMEZONE).date()

    send_day: date = max(coming - timedelta(days=EVENT_DAYS_BEFORE), wrote_day + timedelta(days=EVENT_MIN_DAYS))

    return datetime(send_day.year, send_day.month, send_day.day, FOLLOWUP_HOUR, tzinfo=open_dates.SHOP_TIMEZONE).timestamp()


#EVENT WAIT
#True when they're waiting on something and theirs goes out a later morning, said once a night so the logs aren't a mystery
def event_wait(id: str, record: dict[str, str], booked: bool, restricted: bool, named: bool, send_time: float) -> bool:
    event: dict[str, str] = noted_event(record)

    if(not event):
        return False

    event_time: float = event_send_time(record)

    #this is the morning before it, or the server missed that morning and it's late, either way it goes now
    if(event_time <= send_time):
        return False

    when: str = datetime.fromtimestamp(event_time, open_dates.SHOP_TIMEZONE).strftime(EVENT_SEND_FORMAT)

    #instagram and messenger close the window a day after their last message, so these can't wait it out
    if(not followup_allowed(id, record, booked, restricted, named, event_time)):
        print(f"FOLLOW UP SKIPPED: {id} is waiting on {event['event']} on {event['date']}, and {record.get('channel', '')} takes no follow up by {when}")

        return True

    print(f"FOLLOW UP WAITING: {id} is waiting on {event['event']} on {event['date']}, so theirs goes out {when}")

    return True



#**********NIGHTLY PICK**********
#every night the quiet conversations that never went to booking get checked, and the ones still interested get picked for the next morning


#NEXT RUN
#the next time the hour and minute come around in the shop's time, later today or else tomorrow
def next_run(hour: int, minute: int, now: datetime) -> datetime:
    run_time: datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if(run_time <= now):
        run_time = run_time + timedelta(days=1)

    return run_time


#SECONDS UNTIL
#how long till the hour and minute come around in the shop's time, from timestamps so a daylight savings switch overnight still counts right
def seconds_until(hour: int, minute: int) -> float:
    now: datetime = datetime.now(open_dates.SHOP_TIMEZONE)

    return next_run(hour, minute, now).timestamp() - now.timestamp()


#RECHECK TIME
#the hour and minute the morning's check runs, RECHECK_MINUTES before the send, 9:50 for a 10AM send
def recheck_time() -> tuple[int, int]:
    minutes: int = FOLLOWUP_HOUR * 60 - RECHECK_MINUTES

    return (minutes // 60, minutes % 60)


#PICK ONE
#every pick starts over, the decisions model only reads the ones nothing on file rules out, and anyone waiting on something only gets picked the night before their morning
def prep_followup(id: str, send_time: float) -> None:
    log.clear_info(followup_key(id), [PICKED_FIELD])

    record: dict[str, str] = log.read_info(followup_key(id))

    named: bool = name_attached(id, record.get("channel", ""))

    booked: bool = went_to_booking(id)

    restricted: bool = person_has_them(id)

    if(not followup_allowed(id, record, booked, restricted, named, send_time)):
        #a number with no name is the one rule out that gets said, so the night's check shows who it left out for it
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

    #the dashboard's follow ups page shows them getting it at the morning's send
    dashboard.log_followup_picked(id, record["channel"], int(record.get("count", "0")) + 1, send_time)

    print(f"FOLLOW UP PICKED: {id} gets their {record.get(KIND_FIELD, QUIET_KIND)} follow up on {record['channel']} in the morning")


#PREP FOLLOW UPS
#runs every night, and one conversation that breaks never stops the rest from getting picked
def prep_followups() -> None:
    #on file before anyone gets read, so a text that lands while it runs still gets read again by the morning's check
    log.write_state(NIGHT_PICK_KEY, {"at": time.time()})

    send_time: float = next_run(FOLLOWUP_HOUR, 0, datetime.now(open_dates.SHOP_TIMEZONE)).timestamp()

    #every night's pick starts over on the dashboard too, so a morning the server missed leaves nobody listed as still getting one
    dashboard.clear_past_followups()

    ids: list[str] = followup_ids()

    print(f"FOLLOW UP PICK: checking {len(ids)} conversation(s) for the morning's follow ups")

    for id in ids:
        #each conversation's pick prints as its own block, so a live batch's block never lands in the middle of it
        with prints.held():
            try:
                prep_followup(id, send_time)

            except Exception as error:
                print(f"FOLLOW UP PICK ERROR: {id}, {error}")



#**********MORNING CHECK**********
#right before the morning's send, everyone the night's check never read as they are now gets checked, like someone who texted in the night after it ran


#NIGHT PICK TIME
#when the night's check last started, 0 when it didn't run in the last day, so the morning's check reads everyone it didn't pick
def night_pick_time() -> float:
    night_pick: dict | str = log.read_state(NIGHT_PICK_KEY)

    if(not isinstance(night_pick, dict)):
        return 0.0

    picked_at: float = float(night_pick.get("at", 0))

    if(time.time() - picked_at > NIGHT_PICK_SECONDS):
        return 0.0

    return picked_at


#RECHECK FOLLOW UPS
#runs every morning RECHECK_MINUTES before the send, and one conversation that breaks never stops the rest from getting checked
def recheck_followups() -> None:
    send_time: float = next_run(FOLLOWUP_HOUR, 0, datetime.now(open_dates.SHOP_TIMEZONE)).timestamp()

    picked_at: float = night_pick_time()

    ids: list[str] = followup_ids()

    print(f"FOLLOW UP RECHECK: checking {len(ids)} conversation(s) for anyone the night's pick missed before the morning's follow ups")

    for id in ids:
        #each conversation's check prints as its own block, so a live batch's block never lands in the middle of it
        with prints.held():
            try:
                record: dict[str, str] = log.read_info(followup_key(id))

                #the night picked them, or read them as they are now and ruled them out, since nothing of theirs came in after it
                if(PICKED_FIELD in record or float(record.get("last_message", "0")) < picked_at):
                    continue

                prep_followup(id, send_time)

            except Exception as error:
                print(f"FOLLOW UP RECHECK ERROR: {id}, {error}")



#**********MORNING SEND**********
#the next morning each conversation picked gets one follow up, written from the conversation and checked before it goes out


#FOLLOW UP STATE
#the quiet chat plus which follow up in a row it is, what kind they got read as, and what they're waiting on when that's a thing
def followup_state(id: str, record: dict[str, str]) -> dict:
    state: dict = quiet_state(id)

    #which follow up in a row this is, so a later one never says an earlier one again
    state["followup_number"] = int(record.get("count", "0")) + 1

    #picked before kinds existed, so it's a regular one
    state["followup_kind"] = record.get(KIND_FIELD, QUIET_KIND)

    event: dict[str, str] = noted_event(record)

    if(event):
        state["followup_event"] = event

    return state


#FOLLOW UP CHAIN
#the follow up written from the quiet conversation, in the shape run_chain takes so a slow model gets its retries
def followup_chain(state: dict, id: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    followup_text: str = f"STATE: {state_as_text}"

    system_prompt: str = followup_generator.prompt()

    followup: str = models.generator("FOLLOW UP GENERATOR", system_prompt, followup_text, FOLLOWUP_MAX_TOKENS, FOLLOWUP_EFFORT, line_breaks=False)

    #a follow up asks again what the shop's last message asked, so it never goes out in the words that ask already went out in
    return branches.asked_again_reply(state, followup)


#WRITTEN FOLLOW UP
#the follow up in the owner's wording, empty when it couldn't be written or the final check stopped it
def written_followup(id: str, channel: str, record: dict[str, str]) -> str:
    state: dict = followup_state(id, record)

    followup: str = retry.run_chain(followup_chain, state, id, [], channel, "FOLLOW UP CHAIN ERROR")

    if(followup == ""):
        return followup

    #a follow up never asks the color they want before what the exact price needs, the same as every other reply
    followup = routing.cut_early_color_ask(state, id, followup)

    #a follow up picks the conversation back up, so hazel's heyy stays on it
    followup = wording.wording_rules(followup, channel, state["message_history"], [], [], follow_up=True)

    return replies.cleared_reply(id, channel, followup)


#FOLLOW UP TEXTS
#the follow up cut into texts, and over blooio put back together as one, since every text counts toward the few a quiet chat takes before they answer
def followup_texts(followup: str, channel: str) -> list[str]:
    texts: list[str] = spacing.split_texts(followup)

    if(senders.service_of(channel) != "blooio"):
        return texts

    return [spacing.one_text(texts)]


#HOLD FOLLOW UPS
#blooio turned theirs down for the chat's cap, so none get written for them till they text back or react, and the dashboard shows them on hold
def hold_followups(id: str, channel: str) -> None:
    log.write_info(followup_key(id), [str(time.time())], [HELD_FIELD])

    dashboard.log_followup_held(id, channel)

    print(f"FOLLOW UP HELD: blooio takes no more texts to {id} till they text back or react, so theirs wait till then")


#WROTE BACK
#they wrote in after the morning's send read them, so the reply to that answers them instead
def wrote_back(id: str, record: dict[str, str]) -> bool:
    return log.read_info(followup_key(id)).get("last_message") != record.get("last_message")


#SEND ONE
#only the run that takes the pick off file sends it, so a run that stops halfway and goes again never texts anyone twice
def send_followup(id: str) -> None:
    if(not log.take_info(followup_key(id), PICKED_FIELD)):
        return

    record: dict[str, str] = log.read_info(followup_key(id))

    channel: str = record.get("channel", "")

    #a booking, a person taking them, a number with no name or meta's window closing overnight calls it off, and so does the dashboard switching them off
    if(not followup_allowed(id, record, went_to_booking(id), person_has_them(id), name_attached(id, channel), time.time()) or not dashboard.switched_on(id, channel)):
        return

    count: int = int(record.get("count", "0"))

    #blooio is done with them, so this one goes by sms from the shop's ghl number
    if(goes_by_sms(record)):
        send_sms_followup(id, channel, count, record)

        return

    followup: str = written_followup(id, channel, record)

    #they wrote back while it was being written, so the reply to that answers them instead
    if(followup == "" or wrote_back(id, record)):
        return

    texts: list[str] = followup_texts(followup, channel)

    delivery: senders.DELIVERY = senders.send_texts(id, channel, texts, is_followup=True)

    #what went out, and whether blooio held the rest back for the chat's cap
    texts_sent: list[str] = delivery[0]

    capped: bool = delivery[2]

    #blooio stopped taking texts to them before its follow ups ran out, so this one and the rest go by sms
    if(capped and len(texts_sent) == 0 and sms_reachable(id)):
        log.write_info(followup_key(id), [str(time.time())], [SMS_FIELD])

        print(f"FOLLOW UP MOVED TO SMS: blooio takes no more texts to {id}, so this one and the rest go by sms")

        send_sms_followup(id, channel, count, record)

        return

    #the shop's ghl number can't text them either, so they wait on blooio till they text back or react
    if(capped):
        hold_followups(id, channel)

    if(len(texts_sent) == 0):
        #a hold already said why nothing went out
        if(not capped):
            print(f"FOLLOW UP NOT SENT: {senders.service_of(channel)} refused it for {id} on {channel}, so nothing of it goes on file")

        return

    #only what reached them goes on file, so the next one never thinks they read a part that never went out
    went_out: str = followup

    if(len(texts_sent) < len(texts)):
        went_out = " ".join(texts_sent)

        print(f"FOLLOW UP PARTLY SENT to {id} on {channel}: {went_out}")

    else:
        print(f"FOLLOW UP SENT to {id} on {channel}: {followup}")

    #nothing of theirs came in before it, so it joins the shop's last reply in their history
    log.add_to_last_message(f"systemres_{id}", went_out)

    log.write_info(followup_key(id), [str(count + 1)], ["count"])

    #the dashboard's follow ups page moves them from the morning's list to the ones that went out
    dashboard.log_followup_sent(id, channel, count + 1)


#SEND FOLLOW UPS
#runs every morning, and one conversation that breaks never stops the rest from getting theirs
def send_followups() -> None:
    for id in followup_ids():
        #each conversation's follow up prints as its own block, so a live batch's block never lands in the middle of it
        with prints.held():
            try:
                send_followup(id)

            except Exception as error:
                print(f"FOLLOW UP SEND ERROR: {id}, {error}")

    #every one picked for this morning went out or got called off by now, so the ones called off come off the dashboard's list
    dashboard.clear_past_followups()



#**********SMS FOLLOW UP**********
#once blooio is done with them, the follow up goes by sms from the shop's ghl number: the set intro, a middle flashx writes, then the set call to text hazel and the opt out


#SMS PLAIN
#curly quotes and long dashes become plain ones and emoji come off, so the sms stays the cheap kind
def sms_plain(text: str) -> str:
    for fancy, plain in SMS_PLAIN_CHARACTERS.items():
        text = text.replace(fancy, plain)

    text = SMS_EMOJI_PATTERN.sub("", text)

    return " ".join(text.split())


#SMS MAIN
#the written middle tidied to go on from the intro's comma: plain characters, no quotes around it, a lowercase start and a period on the end
def sms_main(written: str) -> str:
    main: str = sms_plain(written).strip('"').strip()

    if(main == ""):
        return main

    first_word: str = main.split(" ", 1)[0]

    #"Just wanted to" goes on from the comma as "just wanted to", while PPF or I'm keep their capitals
    if(first_word not in SMS_KEEP_CAPITALS and first_word[:1].isupper() and first_word[1:] == first_word[1:].lower()):
        main = main[0].lower() + main[1:]

    #a question keeps its mark, so the check turns it down instead of a period hiding it
    if(main[-1] not in ".!?"):
        main = f"{main}."

    return main


#SMS MAIN PROBLEM
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


#SMS MAIN CHAIN
#flashx writes the middle, and one that can't go out gets written again with why, up to SMS_TRIES in all, empty when none could
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

        #the next try sees the line it wrote that broke a rule and why, so it never writes the same one again
        sms_input += f"\nCAN'T GO OUT: {written.strip()} ({problem})"

    return ""


#WRITTEN SMS MAIN
#the middle written from the quiet conversation, run the way every chain is so a slow model gets its retries
def written_sms_main(id: str, channel: str, record: dict[str, str]) -> str:
    return retry.run_chain(sms_main_chain, followup_state(id, record), id, [], channel, "SMS FOLLOW UP CHAIN ERROR")


#SMS NAME
#the first name off their form, else the one ghl has for them, empty when neither is a real name
def sms_name(id: str, details: dict) -> str:
    name: str = greeting.form_first_name({"name": log.read_info(f"lead_{id}").get("name", ""), "first_name": ""})

    if(name == ""):
        name = greeting.form_first_name({"name": str(details.get("firstName") or ""), "first_name": ""})

    return name


#SMS TEXT
#the set intro, the written middle, then the set call to text hazel and the opt out, so every sms reads the same around what got written
def sms_text(name: str, main: str) -> str:
    intro: str = sms_prompt.INTRO_NO_NAME

    if(name != ""):
        intro = sms_prompt.INTRO.format(name=name)

    return f"{intro} {main} {sms_prompt.CTA} {sms_prompt.ENDING}"


#STOP FOLLOW UPS
#they texted STOP to the shop's sms number, so none go out till they write in again
def stop_followups(id: str) -> None:
    log.write_info(followup_key(id), [str(time.time())], [STOPPED_FIELD])

    print(f"FOLLOW UP STOPPED: {id} texted STOP to the shop's sms number, so none go out till they write in again")


#SEND SMS FOLLOW UP
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

    #nothing of theirs came in before it, so it joins the shop's last reply in their history
    log.add_to_last_message(f"systemres_{id}", text)

    log.write_info(followup_key(id), [str(count + 1)], ["count"])

    #the dashboard's follow ups page moves them from the morning's list to the ones that went out, in green
    dashboard.log_followup_sent(id, channel, count + 1, sms=True)
