#**********IMPORTS**********
#python's clock, the shop's timezone, the reply writer and its final check, the senders, the conversation on file, the dashboard's switch and follow ups page, the held prints, the early color ask cut, the asked again check, and the follow up prompts
import time
from datetime import datetime, timedelta

from helpers.calendar import open_dates
from helpers.channels import replies
from helpers.channels import senders
from helpers.models import models
from helpers.models import retry
from helpers.response import spacing
from helpers.response import wording
from helpers.state import dashboard
from helpers.state import log
from helpers.state import state_build
from helpers.state import state_form
from helpers.terminal import prints
from src import routing
from src import branches
from src.prompts.followup import analyzer_examples as followup_examples
from src.prompts.followup import generator as followup_generator



#**********GLOBALS**********
#when the follow ups get picked and sent, how many each channel gets, and how each one gets written


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


#META WINDOW
#instagram and messenger refuse any message sent more than a day after the customer's last one, so a follow up there only goes out inside it
META_WINDOW_SECONDS: int = 24 * 3600


#NOT INTERESTED
#a yes over this means they're done with the shop for good, over half so a customer the check is torn on still gets their follow up
NOT_INTERESTED_THRESHOLD: float = 0.5


#FOLLOW UP LIMITS
FOLLOWUP_MAX_TOKENS: int = 10*100

FOLLOWUP_EFFORT: str = "high"


#FOLLOW UP FIELDS
#what each conversation keeps on file for its follow ups: the channel it goes out on, when they last wrote in, and how many went out since
FOLLOWUP_FIELDS: list[str] = ["channel", "last_message", "count"]

#when the night or the morning's check picked them, only on file till the morning's follow up takes it off
PICKED_FIELD: str = "prepped"



#**********ON FILE**********
#what each conversation keeps on file for its follow ups, written every time they message


#FOLLOW UP KEY
#named <what it is>_<id> like every key of theirs
def followup_key(id: str) -> str:
    return f"followup_{id}"


#NOTE MESSAGE
#they wrote in, so the channel and the time go on file, the count starts over, and a follow up picked for them is off
def note_message(id: str, channel: str) -> None:
    try:
        log.write_info(followup_key(id), [channel, str(time.time()), "0"], FOLLOWUP_FIELDS)

        #a follow up picked for them comes off the dashboard's follow ups page too
        if(log.take_info(followup_key(id), PICKED_FIELD)):
            dashboard.log_followup_dropped(id)

    #a note that fails only costs them a follow up, their reply still goes out
    except Exception as error:
        print(f"FOLLOW UP NOTE ERROR: {error}")


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



#**********WHO GETS ONE**********
#the checks that need no model, then the not interested check the decisions model makes on the whole conversation


#WINDOW OPEN
#instagram and messenger only take a message inside a day of their last one, every other channel always takes one
def window_open(channel: str, last_message: float, send_time: float) -> bool:
    if(channel not in senders.META_CHANNELS):
        return True

    return send_time - last_message < META_WINDOW_SECONDS


#FOLLOW UP ALLOWED
#True when nothing on file rules a follow up out: they never went to booking, nobody has them, their channel's count isn't used up, they've been quiet long enough and meta's window is still open when it goes out
def followup_allowed(record: dict[str, str], booked: bool, restricted: bool, send_time: float) -> bool:
    channel: str = record.get("channel", "")

    if(channel == "" or booked or restricted):
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


#NOT INTERESTED
#True when the whole conversation shows they're done with the shop for good, so no follow up goes out to them
def not_interested(state: dict) -> bool:
    not_interested_question: dict = {"type": "noul", "instructions": f"Is the customer completely not interested, done with the shop for good going by the whole conversation in `message_history`?\n{followup_examples.not_interested_examples()}"}

    probability_yes: float = models.decision_answer("not_interested", not_interested_question, state)["noul"]

    print(f"NOT INTERESTED: {probability_yes:.2f}")

    return probability_yes > NOT_INTERESTED_THRESHOLD



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
#every pick starts over, so they're only picked while they still get one, and the decisions model only reads the ones nothing on file rules out
def prep_followup(id: str, send_time: float) -> None:
    log.clear_info(followup_key(id), [PICKED_FIELD])

    record: dict[str, str] = log.read_info(followup_key(id))

    if(not followup_allowed(record, went_to_booking(id), person_has_them(id), send_time)):
        return

    if(not_interested(quiet_state(id))):
        print(f"FOLLOW UP SKIPPED: {id} is done with the shop for good")

        return

    log.write_info(followup_key(id), [str(time.time())], [PICKED_FIELD])

    #the dashboard's follow ups page shows them getting it at the morning's send
    dashboard.log_followup_picked(id, record["channel"], int(record.get("count", "0")) + 1, send_time)

    print(f"FOLLOW UP PICKED: {id} gets one on {record['channel']} in the morning")


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
def written_followup(id: str, channel: str, count: int) -> str:
    state: dict = quiet_state(id)

    #which follow up in a row this is, so a later one never says an earlier one again
    state["followup_number"] = count + 1

    followup: str = retry.run_chain(followup_chain, state, id, [], channel, "FOLLOW UP CHAIN ERROR")

    if(followup == ""):
        return followup

    #a follow up never asks the color they want before what the exact price needs, the same as every other reply
    followup = routing.cut_early_color_ask(state, id, followup)

    #a follow up picks the conversation back up, so hazel's heyy stays on it
    followup = wording.wording_rules(followup, channel, state["message_history"], [], "", follow_up=True)

    return replies.cleared_reply(id, channel, followup)


#SEND ONE
#only the run that takes the pick off file sends it, so a run that stops halfway and goes again never texts anyone twice
def send_followup(id: str) -> None:
    if(not log.take_info(followup_key(id), PICKED_FIELD)):
        return

    record: dict[str, str] = log.read_info(followup_key(id))

    channel: str = record.get("channel", "")

    #a booking, a person taking them or meta's window closing overnight calls it off, and so does the dashboard switching them off
    if(not followup_allowed(record, went_to_booking(id), person_has_them(id), time.time()) or not dashboard.switched_on(id, channel)):
        return

    count: int = int(record.get("count", "0"))

    followup: str = written_followup(id, channel, count)

    #they wrote back while it was being written, so the reply to that answers them instead
    if(followup == "" or log.read_info(followup_key(id)).get("last_message") != record.get("last_message")):
        return

    if(not senders.send_texts(id, channel, spacing.split_texts(followup))):
        print(f"FOLLOW UP NOT SENT: {channel} refused it for {id}, so nothing of it goes on file")

        return

    print(f"FOLLOW UP SENT to {id} on {channel}: {followup}")

    #nothing of theirs came in before it, so it joins the shop's last reply in their history
    log.add_to_last_message(f"systemres_{id}", followup)

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
