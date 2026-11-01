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



#**********BRANCH REPLIES**********
#each one builds the state, gets its branch's reply, fixes the wording, then sends it


#MAIN REPLY
#the router picks the branch, and the owner's good news about their color rides along when it's due, False when it was held for his answer
def main_reply(current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str) -> bool:
    try:
        branch_parts: tuple[dict, dict[str, str]] = state_build.branch_state(user_message, message_history, id, current_message_batch)

        state: dict = branch_parts[0]

        critical_info: dict[str, str] = branch_parts[1]

        #the model the vehicle check read, the form intro names it
        model: str = critical_info.get("model", "")

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

        system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, model)

        #the owner's answer on their color landed while this was written, so it gets written again carrying what he found
        if(reply_held(id, channel)):
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
#a person has them, so only their service or shop questions get answered, or their pick of the materials, and the rest get a hold reply every other time, False when it was held for his answer
def restricted_reply(current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str) -> bool:
    try:
        #the owner is checking an exact color they sent, the vehicle check clears it when they send a different one
        color_checked: bool = owner.color_check_status(id) != ""

        #their last message got a hold reply, read before the chain runs so a timeout running it again holds them the same way
        held: bool = owner.held(id)

        branch_parts: tuple[dict, dict[str, str]] = state_build.branch_state(user_message, message_history, id, current_message_batch)

        state: dict = branch_parts[0]

        critical_info: dict[str, str] = branch_parts[1]

        model: str = critical_info.get("model", "")

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

        if(materials_due):
            color_chains.materials_reply(id, system_response, channel, message_history, current_message_batch, model)

        else:
            system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, model)

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

        model: str = critical_info.get("model", "")

        system_response: str = retry.run_chain(chain, state, id, extra_inputs, channel, f"{step_name} CHAIN ERROR")

        system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, model)

        replies.send_response(id, system_response, channel)

        notify.notify_hand_off(id, channel, user_message)

    except Exception as error:
        print(f"{step_name} PENDING ERROR: {error}")

        notify.notify_failure(id, channel, user_message, f"{step_name} PENDING ERROR: {error}")



#**********CORE**********
#takes one batch of their texts, picks which branch answers it, and sends the reply


#CORE
#True once their batch got its answer, False when its reply was held for the owner's answer landing, so the server answers it again
def core(current_message_batch: list, id: str, channel: str) -> bool:
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

    #the customer sees the typing bubble the whole time core works on the reply
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

        restricted: str | dict = log.read_state(f"restricted_{id}")

        date_pending: dict[str, str] = log.read_info(f"date_pending_{id}")

        contact_pending: dict[str, str] = log.read_info(f"contact_pending_{id}")

        #a person has them now, so the bot only answers what they ask about the services or the shop
        if(restricted):
            answered = restricted_reply(current_message_batch, user_message, message_history, id, channel)

        elif(date_pending):
            pending_reply(booking_chains.date_propose_chain, [], "DATE", current_message_batch, user_message, message_history, id, channel)

        #their name, number and email only text the owner once, so running this again after a timeout is safe
        elif(contact_pending):
            pending_reply(booking_chains.contact_chain, [channel], "CONTACT", current_message_batch, user_message, message_history, id, channel)

        else:
            answered = main_reply(current_message_batch, user_message, message_history, id, channel)

    except Exception as error:
        print(f"READ ERROR FOR READING PENDING|RESTRICTED: {error}")

        notify.notify_failure(id, channel, user_message, f"READ ERROR FOR READING PENDING|RESTRICTED: {error}")

    return answered
