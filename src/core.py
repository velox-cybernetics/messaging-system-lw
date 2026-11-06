#**********IMPORTS**********
#the usual suspects, plus python's clock
from collections.abc import Callable
from datetime import datetime, timedelta

from helpers.calendar import open_dates
from helpers.chains import booking_chains
from helpers.chains import color_chains
from helpers.channels import notify
from helpers.channels import replies
from helpers.channels import senders
from helpers.models import retry
from helpers.response import spacing
from helpers.response import wording
from helpers.state import owner
from helpers.state import dashboard
from helpers.state import log
from helpers.state import state_build
from helpers.state import state_form
from src import followup
from src import in_conversation
from src import routing



#**********FORM REPEATS**********
#same form twice before they ever texted back? that's a repeat, not a new lead


#FORM WINDOW
#a repeat form inside this many hours gets no second reply
FORM_REPEAT_HOURS: int = 24


#FORM REPEATED
#a text from them resets things, so a fresh form after that counts again
def form_repeated(id: str, channel: str) -> bool:
    if(channel not in state_form.FORM_CHANNELS):
        log.clear_state(f"form_sent_{id}")

        return False

    if(log.read_state(f"form_sent_{id}")):
        print(f"FORM REPEATED: {id} sent the quote form again before texting back, so it gets no second reply")

        return True

    log.write_state(f"form_sent_{id}", "sent")

    log.expire_at(f"form_sent_{id}", datetime.now(open_dates.SHOP_TIMEZONE) + timedelta(hours=FORM_REPEAT_HOURS))

    return False



#**********HELD REPLIES**********
#a reply written while the owner's color answer lands gets tossed and redone with it


#NEWS LANDING
#form leads never wait on the owner, they only get the one reply anyway
def news_landing(id: str, channel: str) -> bool:
    return channel not in state_form.FORM_CHANNELS and owner.news_landing(id)


#REPLY HELD
#put their message back so the redo reads the same history this one did
def reply_held(id: str, channel: str) -> bool:
    if(not news_landing(id, channel)):
        return False

    log.remove_last_message(f"usermsg_{id}")

    print("REPLY HELD: the owner answered their color check while this reply was being written, so it gets written again carrying what he found")

    return True



#**********FOLDED REPLIES**********
#they kept typing while we wrote, so one reply answers the whole pile


#FOLD WINDOW
#way more time than needed, the next batch shows up long before this runs out
FOLD_MINUTES: int = 30


#FOLDED PATH
#"" means the main path, None means nothing got folded in, read it once and it's gone
def folded_path(id: str) -> str | None:
    folded: dict | str = log.read_state(f"folded_{id}")

    if(not isinstance(folded, dict) or "restricted" not in folded):
        return None

    log.clear_state(f"folded_{id}")

    return folded["restricted"]


#PATH KEPT
#only safe to redo a reply that didn't already put a step on file
def path_kept(id: str, restricted_start: str) -> bool:
    if(log.read_info(f"date_pending_{id}") or log.read_info(f"contact_pending_{id}")):
        return False

    if(log.read_state(f"convo_ended_{id}") or log.read_info(f"side_ask_notify_{id}")):
        return False

    return restricted_start == "" or bool(log.read_state(f"restricted_{id}"))


#REPLY FOLDED
#lead forms pass None here since they never fold
def reply_folded(id: str, has_reply: bool, restricted_start: str, sent_since: Callable[[], bool] | None) -> bool:
    if(sent_since is None or not has_reply or not sent_since()):
        return False

    if(not path_kept(id, restricted_start)):
        print("REPLY NOT FOLDED: they sent more while it was written, but it started a step that's already on file, so it goes out as written")

        return False

    log.remove_last_message(f"usermsg_{id}")

    log.write_state(f"folded_{id}", {"restricted": restricted_start})

    log.expire_at(f"folded_{id}", datetime.now(open_dates.SHOP_TIMEZONE) + timedelta(minutes=FOLD_MINUTES))

    print("REPLY FOLDED: they sent more while this reply was written, so it never goes out and their next batch answers it all at once")

    return True



#**********BRANCH REPLIES**********
#build the state, get the reply, fix the wording, send it, rinse and repeat


#MAIN REPLY
#False means held or folded, so the server takes another swing at it
def main_reply(current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str, sent_since: Callable[[], bool] | None) -> bool:
    try:
        branch_parts: tuple[dict, dict[str, str]] = state_build.branch_state(user_message, message_history, id, current_message_batch)

        state: dict = branch_parts[0]

        critical_info: dict[str, str] = branch_parts[1]

        vehicle_models: list[str] = state_build.vehicle_models(critical_info)

        system_response: str = retry.run_chain(routing.main_route, state, id, [], channel, "CORE ERROR")

        #promised a color check in the reply? then the owner better actually hear about it
        color_chains.check_missed_color(system_response, id, current_message_batch)

        #a held booking always asks the schedule question, no matter how many replies went out
        booking_held: dict[str, str] = log.read_info(f"booking_held_{id}")

        if(booking_held):
            system_response = routing.held_booking_question(system_response, id)

        good_news_sent: bool = False

        #owner found their exact color, time to share the good news
        if(routing.good_news_fits(system_response, id)):
            good_news_parts: tuple[str, bool] = color_chains.good_news_reply(system_response, state, id, channel)

            system_response = good_news_parts[0]

            good_news_sent = good_news_parts[1]

        system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, vehicle_models)

        #owner's answer landed mid-write, so toss this one and start over
        if(reply_held(id, channel)):
            return False

        #they kept typing, so the next batch answers this one too
        if(reply_folded(id, system_response.strip() != "", "", sent_since)):
            return False

        replies.send_response(id, system_response, channel)

        #good news only goes out once, nobody needs to hear it twice
        if(good_news_sent):
            owner.news_given(id)

            log.clear_info(f"booking_held_{id}", ["status"])

        notify.notify_hand_off(id, channel, user_message)

    except Exception as error:
        print(f"CRITICAL INFO READ ERROR: {error}")

        notify.notify_failure(id, channel, user_message, f"CRITICAL INFO READ ERROR: {error}")

    return True


#RESTRICTED REPLY
#a person has them, so the bot only takes the easy questions
def restricted_reply(current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str, restricted_start: str, sent_since: Callable[[], bool] | None) -> bool:
    try:
        #grab this now, the vehicle check wipes it if they send a new color
        color_checked: bool = owner.color_check_status(id) != ""

        #read before the chain runs so a retry holds them the exact same way
        held: bool = restricted_start == owner.HELD_STATE

        branch_parts: tuple[dict, dict[str, str]] = state_build.branch_state(user_message, message_history, id, current_message_batch)

        state: dict = branch_parts[0]

        critical_info: dict[str, str] = branch_parts[1]

        vehicle_models: list[str] = state_build.vehicle_models(critical_info)

        color_status: str = owner.color_check_status(id)

        #new exact color mid-check, so the owner gets a fresh one to look at
        color_swapped: bool = color_checked and color_status == ""

        #the closest materials the owner sent ride along with this reply
        materials_due: bool = color_status == owner.MATERIALS_STATUS and owner.news_due(id)

        system_response: str = ""

        #they already saw the materials, so figure out which one they picked
        if(color_status == owner.MATERIALS_STATUS and not materials_due):
            system_response = retry.run_chain(routing.material_pick_route, state, id, [held], channel, "MATERIAL PICK CHAIN ERROR")

        #empty back means they already got a hold reply, so nothing goes out
        else:
            system_response = retry.run_chain(routing.restricted_route, state, id, [color_swapped, held or materials_due], channel, "RESTRICTED CHAIN ERROR")

        #promised a color check in the reply? then the owner better actually hear about it
        color_chains.check_missed_color(system_response, id, current_message_batch)

        #a person books them, so lose the schedule question unless their pick just freed them
        if(log.read_state(f"restricted_{id}")):
            system_response = spacing.drop_booking_question(system_response)

        #owner's answer landed mid-write, so toss this one and start over
        if(reply_held(id, channel)):
            return False

        #the materials reply polishes its own wording, no double coat
        if(not materials_due):
            system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, vehicle_models)

        #they kept typing, so the next batch answers this one, materials and all
        if(reply_folded(id, materials_due or system_response.strip() != "", restricted_start, sent_since)):
            return False

        if(materials_due):
            color_chains.materials_reply(id, system_response, channel, message_history, current_message_batch, vehicle_models)

        else:
            replies.send_response(id, system_response, channel)

        notify.notify_hand_off(id, channel, user_message)

    except Exception as error:
        print(f"RESTRICTED REPLY ERROR: {error}")

        notify.notify_failure(id, channel, user_message, f"RESTRICTED REPLY ERROR: {error}")

    return True


#PENDING REPLY
#they're mid booking, either picking a day or handing over their info
def pending_reply(chain: Callable[..., str], extra_inputs: list, step_name: str, current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str) -> None:
    try:
        branch_parts: tuple[dict, dict[str, str]] = state_build.branch_state(user_message, message_history, id, current_message_batch)

        state: dict = branch_parts[0]

        critical_info: dict[str, str] = branch_parts[1]

        vehicle_models: list[str] = state_build.vehicle_models(critical_info)

        system_response: str = retry.run_chain(chain, state, id, extra_inputs, channel, f"{step_name} CHAIN ERROR")

        system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, vehicle_models)

        replies.send_response(id, system_response, channel)

        notify.notify_hand_off(id, channel, user_message)

    except Exception as error:
        print(f"{step_name} PENDING ERROR: {error}")

        notify.notify_failure(id, channel, user_message, f"{step_name} PENDING ERROR: {error}")



#**********BOOKING SILENCE**********
#a person is fitting them in, so the bot keeps its mouth shut


#BOOKING SILENT
#a folded batch still owes them a reply, so that one doesn't count as silent
def booking_silent(id: str) -> bool:
    try:
        if(log.read_state(f"folded_{id}")):
            return False

        return owner.booking_held(id)

    #a broken read never silences anyone, better chatty than ghosting
    except Exception as error:
        print(f"BOOKING HOLD READ ERROR: {error}")

        return False


#BOOKING HOLD
#empty reply goes on file so their message keeps its place in line
def booking_hold_reply(user_message: dict, id: str, channel: str) -> None:
    print("BOOKING HOLD: a person is fitting them a day on the schedule, so nothing goes back to them and the owner gets texted what they sent")

    replies.write_message(f"systemres_{id}", "")

    owner.note_booking_message(id)

    notify.notify_hand_off(id, channel, user_message)



#**********CORE**********
#one batch in, one reply out, the brains of the whole operation


#CORE
#False means held or folded, so the server sends it around again
def core(current_message_batch: list, id: str, channel: str, sent_since: Callable[[], bool] | None = None) -> bool:
    #switched off in the dashboard, so hands off this batch entirely
    if(not dashboard.switched_on(id, channel)):
        print(f"SWITCHED OFF: {id} or their channel is off in the dashboard, so their batch gets no reply")

        return True

    #already the owner's from before the bot showed up, so it keeps its mouth shut
    if(in_conversation.owner_has_them(id)):
        return True

    if(form_repeated(id, channel)):
        return True

    #owner's answer is mid-landing, so hold the pen until it's on file
    if(news_landing(id, channel)):
        print("REPLY HELD: the owner's answer on their color check is landing, so their batch gets answered once it's on file")

        return False

    #a person is booking them, so not even a typing bubble goes up
    silent: bool = booking_silent(id)

    #nobody likes a typing bubble that never ends, so only show it when we'll actually reply
    if(not silent):
        senders.start_typing(id, channel)

    user_message: dict = state_build.user_message_form(current_message_batch, channel)

    message_history: dict = state_build.message_history_read(id)

    #first we've heard of them, so make sure it's not the owner's buddy picking back up before the bot butts in
    if(in_conversation.picks_up(user_message, message_history, id, channel)):
        return True

    replies.write_message(f"usermsg_{id}", user_message)

    #they wrote in, so the follow up count starts fresh
    followup.note_message(id, channel)

    #a broken reply still counts as answered, the dev already got texted about it
    answered: bool = True

    try:
        #form lead's name goes on file so the owner knows who's who
        if(channel in state_form.FORM_CHANNELS):
            notify.note_lead(current_message_batch, id)

        #a folded batch gets redone from the path its reply started on
        folded: str | None = None

        if(sent_since is not None):
            folded = folded_path(id)

        restricted: str | dict = ""

        if(folded is None):
            restricted = log.read_state(f"restricted_{id}")

        else:
            restricted = folded

        date_pending: dict[str, str] = log.read_info(f"date_pending_{id}")

        contact_pending: dict[str, str] = log.read_info(f"contact_pending_{id}")

        if(silent):
            booking_hold_reply(user_message, id, channel)

        elif(restricted):
            answered = restricted_reply(current_message_batch, user_message, message_history, id, channel, restricted, sent_since)

        elif(date_pending):
            pending_reply(booking_chains.date_propose_chain, [], "DATE", current_message_batch, user_message, message_history, id, channel)

        #their info only texts the owner once, so a retry here is harmless
        elif(contact_pending):
            pending_reply(booking_chains.contact_chain, [channel], "CONTACT", current_message_batch, user_message, message_history, id, channel)

        else:
            answered = main_reply(current_message_batch, user_message, message_history, id, channel, sent_since)

    except Exception as error:
        print(f"READ ERROR FOR READING PENDING|RESTRICTED: {error}")

        notify.notify_failure(id, channel, user_message, f"READ ERROR FOR READING PENDING|RESTRICTED: {error}")

    return answered
