#**********IMPORTS**********
#python's clock, the helpers that build the state, run each branch, fix the wording and send the reply, the dashboard's switch, and the follow ups
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
from src import routing



#**********FORM REPEATS**********
#a quote form sent again before they ever texted back is the same lead, so it never gets a second reply


#FORM WINDOW
#a form sent again within this long of the last one, with nothing from them in between, is a repeat
FORM_REPEAT_HOURS: int = 24


#FORM REPEATED
#True when this form came in while their last one is still waiting on them, a text of theirs opens them up to a new one
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
#a reply written while the owner's answer on their color lands never goes out, so their batch gets answered again carrying it


#NEWS LANDING
#True while the owner's answer on their color check is landing for them
#a form lead is answered once with nothing to answer it again, so it never waits on the owner
def news_landing(id: str, channel: str) -> bool:
    return channel not in state_form.FORM_CHANNELS and owner.news_landing(id)


#REPLY HELD
#their message comes back off file, so the batch answered again reads the same history this one did
def reply_held(id: str, channel: str) -> bool:
    if(not news_landing(id, channel)):
        return False

    log.remove_last_message(f"usermsg_{id}")

    print("REPLY HELD: the owner answered their color check while this reply was being written, so it gets written again carrying what he found")

    return True



#**********FOLDED REPLIES**********
#a reply written while they kept sending never goes out, so its batch joins the one carrying what they sent since and one reply answers it all


#FOLD WINDOW
#the path a folded batch started from stays on file this long, the batch it joined gets answered well before then
FOLD_MINUTES: int = 30


#FOLDED PATH
#the restricted state the folded batch's reply started from, "" for the main path, None when no batch was folded into this one, taken off once it's read
def folded_path(id: str) -> str | None:
    folded: dict | str = log.read_state(f"folded_{id}")

    if(not isinstance(folded, dict) or "restricted" not in folded):
        return None

    log.clear_state(f"folded_{id}")

    return folded["restricted"]


#PATH KEPT
#the reply only answered them or handed them to a person, so answering it all again from the path it started on writes the same way
#a reply that started a booking step, wrapped them up, made a side ask or took the restriction off with their pick goes out, what it did is already on file
def path_kept(id: str, restricted_start: str) -> bool:
    if(log.read_info(f"date_pending_{id}") or log.read_info(f"contact_pending_{id}")):
        return False

    if(log.read_state(f"convo_ended_{id}") or log.read_info(f"side_ask_notify_{id}")):
        return False

    return restricted_start == "" or bool(log.read_state(f"restricted_{id}"))


#REPLY FOLDED
#they sent more while this reply was written, so it never goes out: their message comes back off file and the path it started from goes on file for the batch carrying what they sent
#sent_since is None for a channel that never folds, like a lead form, and a reply with nothing to send never folds, nothing of it would go out
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
#each one builds the state, gets its branch's reply, fixes the wording, then sends it


#MAIN REPLY
#the router picks the branch, and the owner's good news about their color rides along when it's due, False when it was held for his answer or folded into the batch carrying what they sent since
def main_reply(current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str, sent_since: Callable[[], bool] | None) -> bool:
    try:
        branch_parts: tuple[dict, dict[str, str]] = state_build.branch_state(user_message, message_history, id, current_message_batch)

        state: dict = branch_parts[0]

        critical_info: dict[str, str] = branch_parts[1]

        #the models the vehicle check read, the form intro names each one
        vehicle_models: list[str] = state_build.vehicle_models(critical_info)

        system_response: str = retry.run_chain(routing.main_route, state, id, [], channel, "CORE ERROR")

        #a reply saying the color books are getting checked always has a check the owner gets texted about
        color_chains.check_missed_color(system_response, id, current_message_batch)

        #a booking held for its price or vehicle asks the schedule question no matter how many replies went out
        booking_held: dict[str, str] = log.read_info(f"booking_held_{id}")

        if(booking_held):
            system_response = routing.held_booking_question(system_response, id)

        good_news_sent: bool = False

        #the owner made sure the shop can get the exact color they sent, so this reply carries the good news
        if(routing.good_news_fits(system_response, id)):
            good_news_parts: tuple[str, bool] = color_chains.good_news_reply(system_response, state, id, channel)

            system_response = good_news_parts[0]

            good_news_sent = good_news_parts[1]

        system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, vehicle_models)

        #the owner's answer on their color landed while this was written, so it gets written again carrying what he found
        if(reply_held(id, channel)):
            return False

        #they sent more while this was written, so the batch carrying it answers this one with it
        if(reply_folded(id, system_response.strip() != "", "", sent_since)):
            return False

        replies.send_response(id, system_response, channel)

        #the good news only goes out once, and its schedule question answers a booking held for the color
        if(good_news_sent):
            owner.news_given(id)

            log.clear_info(f"booking_held_{id}", ["status"])

        notify.notify_hand_off(id, channel, user_message)

    except Exception as error:
        print(f"CRITICAL INFO READ ERROR: {error}")

        notify.notify_failure(id, channel, user_message, f"CRITICAL INFO READ ERROR: {error}")

    return True


#RESTRICTED REPLY
#a person has them, so only their service or shop questions get answered, or their pick of the materials, and the rest get a hold reply every other time, False when it was held for his answer or folded into the batch carrying what they sent since
#restricted_start is the restricted state core picked this path from
def restricted_reply(current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str, restricted_start: str, sent_since: Callable[[], bool] | None) -> bool:
    try:
        #the owner is checking an exact color they sent, the vehicle check clears it when they send a different one
        color_checked: bool = owner.color_check_status(id) != ""

        #their last message got a hold reply, read before the chain runs so a timeout or a folded batch running it again holds them the same way
        held: bool = restricted_start == owner.HELD_STATE

        branch_parts: tuple[dict, dict[str, str]] = state_build.branch_state(user_message, message_history, id, current_message_batch)

        state: dict = branch_parts[0]

        critical_info: dict[str, str] = branch_parts[1]

        vehicle_models: list[str] = state_build.vehicle_models(critical_info)

        color_status: str = owner.color_check_status(id)

        #they sent a different exact color than the one being checked, so the pricing branch sends the owner a new check
        color_swapped: bool = color_checked and color_status == ""

        #the closest materials the owner sent go out with this reply
        materials_due: bool = color_status == owner.MATERIALS_STATUS and owner.news_due(id)

        system_response: str = ""

        #they already got the closest materials, so their message gets read for which one they picked first
        if(color_status == owner.MATERIALS_STATUS and not materials_due):
            system_response = retry.run_chain(routing.material_pick_route, state, id, [held], channel, "MATERIAL PICK CHAIN ERROR")

        #empty when what they asked waits on a person and their last message got a hold reply, then nothing goes out and the owner gets texted again
        #the materials going out are their reply, so no hold reply goes with them
        else:
            system_response = retry.run_chain(routing.restricted_route, state, id, [color_swapped, held or materials_due], channel, "RESTRICTED CHAIN ERROR")

        #a reply saying the color books are getting checked always has a check the owner gets texted about
        color_chains.check_missed_color(system_response, id, current_message_batch)

        #a person books them, so the schedule question comes off, unless their pick just took the restriction off
        if(log.read_state(f"restricted_{id}")):
            system_response = spacing.drop_booking_question(system_response)

        #the owner's answer on their color landed while this was written, so it gets written again carrying what he found
        if(reply_held(id, channel)):
            return False

        #the materials reply fixes the wording of its own answer
        if(not materials_due):
            system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, vehicle_models)

        #they sent more while this was written, so the batch carrying it answers this one with it, the materials going out with it too
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
#a booking step they're in the middle of (picking a day or giving their info) answers their message
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
#a person fitting them a day on the schedule has them, so nothing from the bot reaches them, the owner just hears what they sent


#BOOKING SILENT
#read before the typing bubble, so not even that goes up for them
#a batch folded into this one carries a reply that never went out, so it gets written on the path that reply started from
def booking_silent(id: str) -> bool:
    try:
        if(log.read_state(f"folded_{id}")):
            return False

        return owner.booking_held(id)

    #a read that fails never silences them, their batch goes the way it would have
    except Exception as error:
        print(f"BOOKING HOLD READ ERROR: {error}")

        return False


#BOOKING HOLD
#nothing goes back to them: the empty reply goes on file so their message keeps its place, and the owner gets texted what they sent
def booking_hold_reply(user_message: dict, id: str, channel: str) -> None:
    print("BOOKING HOLD: a person is fitting them a day on the schedule, so nothing goes back to them and the owner gets texted what they sent")

    replies.write_message(f"systemres_{id}", "")

    owner.note_booking_message(id)

    notify.notify_hand_off(id, channel, user_message)



#**********CORE**********
#takes one batch of their texts, picks which branch answers it, and sends the reply


#CORE
#True once their batch got its answer, False when its reply was held for the owner's answer landing or folded into the batch carrying what they sent since, so the server answers it again or with that batch
#sent_since is True once they sent more after this batch was taken, None on a lead form, which never folds
def core(current_message_batch: list, id: str, channel: str, sent_since: Callable[[], bool] | None = None) -> bool:
    #they or their whole channel got switched off in the dashboard while their batch waited, so nothing of it gets read, written or sent
    if(not dashboard.switched_on(id, channel)):
        print(f"SWITCHED OFF: {id} or their channel is off in the dashboard, so their batch gets no reply")

        return True

    #the quote form sent again before they texted back gets no second reply, and a text of theirs opens them up to a new one
    if(form_repeated(id, channel)):
        return True

    #the owner's answer on their color is landing, so nothing of their batch gets written till it's on file
    if(news_landing(id, channel)):
        print("REPLY HELD: the owner's answer on their color check is landing, so their batch gets answered once it's on file")

        return False

    #a person fitting them a day on the schedule keeps the bot silent, so not even the typing bubble goes up
    silent: bool = booking_silent(id)

    #the customer sees the typing bubble the whole time core works on the reply
    if(not silent):
        senders.start_typing(id, channel)

    user_message: dict = state_build.user_message_form(current_message_batch, channel)

    message_history: dict = state_build.message_history_read(id)

    replies.write_message(f"usermsg_{id}", user_message)

    #they wrote in, so the count of follow ups starts over and one picked for them is off
    followup.note_message(id, channel)

    #a reply that broke still counts as answered, the developer got texted about it
    answered: bool = True

    try:
        #a form lead's name and where they came in go on file, so the owner's texts say who it is
        if(channel in state_form.FORM_CHANNELS):
            notify.note_lead(current_message_batch, id)

        #a batch folded into this one gets answered from the path its reply started on, so a reply that handed them to a person gets written the same way again
        folded: str | None = folded_path(id) if sent_since is not None else None

        restricted: str | dict = log.read_state(f"restricted_{id}") if folded is None else folded

        date_pending: dict[str, str] = log.read_info(f"date_pending_{id}")

        contact_pending: dict[str, str] = log.read_info(f"contact_pending_{id}")

        #a person is fitting them a day on the schedule, so their message goes on file and the owner hears about it, with nothing sent back
        if(silent):
            booking_hold_reply(user_message, id, channel)

        #a person has them now, so the bot only answers what they ask about the services or the shop
        elif(restricted):
            answered = restricted_reply(current_message_batch, user_message, message_history, id, channel, restricted, sent_since)

        elif(date_pending):
            pending_reply(booking_chains.date_propose_chain, [], "DATE", current_message_batch, user_message, message_history, id, channel)

        #their name, number and email only text the owner once, so running this again after a timeout is safe
        elif(contact_pending):
            pending_reply(booking_chains.contact_chain, [channel], "CONTACT", current_message_batch, user_message, message_history, id, channel)

        else:
            answered = main_reply(current_message_batch, user_message, message_history, id, channel, sent_since)

    except Exception as error:
        print(f"READ ERROR FOR READING PENDING|RESTRICTED: {error}")

        notify.notify_failure(id, channel, user_message, f"READ ERROR FOR READING PENDING|RESTRICTED: {error}")

    return answered
