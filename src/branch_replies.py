#IMPORTS

from helpers.chains import color_chains
from helpers.channels import notify
from helpers.channels import replies
from helpers.models import retry
from helpers.response import spacing
from helpers.response import wording
from helpers.state import log
from helpers.state import owner
from helpers.state import state_build
from src import reply_checks
from src import routing


#BRANCH REPLIES

#build the state, get the reply, fix the wording, send it, False means held or folded
def main_reply(current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str, sent_since) -> bool:
    try:
        branch_parts: tuple[dict, dict[str, str]] = state_build.branch_state(user_message, message_history, id, current_message_batch)

        state: dict = branch_parts[0]

        critical_info: dict[str, str] = branch_parts[1]

        vehicle_models: list[str] = state_build.vehicle_models(critical_info)

        system_response: str = retry.run_chain(routing.main_route, state, id, [], channel, "CORE ERROR")

        #promised a color check in the reply, so the owner better actually hear about it
        color_chains.check_missed_color(system_response, id, current_message_batch)

        booking_held: dict[str, str] = log.read_info(f"booking_held_{id}")

        #a held booking always asks the schedule question, no matter how many replies went out
        if(booking_held):
            system_response = routing.held_booking_question(system_response, id)

        good_news_sent: bool = False

        #owner found there exact color, time to share the good news
        if(routing.good_news_fits(system_response, id)):
            good_news_parts: tuple[str, bool] = color_chains.good_news_reply(system_response, state, id, channel)

            system_response = good_news_parts[0]

            good_news_sent = good_news_parts[1]

        system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, vehicle_models)

        if(reply_checks.reply_held(id, channel)):
            return False

        if(reply_checks.reply_folded(id, system_response.strip() != "", "", sent_since)):
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

#a person has them, so the system only takes the easy questions, False means held or folded
def restricted_reply(current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str, restricted_start: str, sent_since) -> bool:
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

        #new exact color mid check, so the owner gets a fresh one to look at
        color_swapped: bool = color_checked and color_status == ""

        #the closest materials the owner sent ride along with this reply
        materials_due: bool = color_status == owner.MATERIALS_STATUS and owner.news_due(id)

        system_response: str = ""

        #they already saw the materials, so figure out which one they picked
        if(color_status == owner.MATERIALS_STATUS and not materials_due):
            system_response = retry.run_chain(routing.material_pick_route, state, id, [held], channel, "MATERIAL PICK CHAIN ERROR")
        else:
            #empty back means they already got a hold reply, so nothing goes out
            system_response = retry.run_chain(routing.restricted_route, state, id, [color_swapped, held or materials_due], channel, "RESTRICTED CHAIN ERROR")

        #promised a color check in the reply, so the owner better actually hear about it
        color_chains.check_missed_color(system_response, id, current_message_batch)

        #a person books them, so lose the schedule question unless there pick just freed them
        if(log.read_state(f"restricted_{id}")):
            system_response = spacing.drop_booking_question(system_response)

        if(reply_checks.reply_held(id, channel)):
            return False

        #the materials reply polishes its own wording, no double coat
        if(not materials_due):
            system_response = wording.wording_rules(system_response, channel, message_history, current_message_batch, vehicle_models)

        if(reply_checks.reply_folded(id, materials_due or system_response.strip() != "", restricted_start, sent_since)):
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

#they're mid booking, either picking a day or handing over their info
def pending_reply(chain, extra_inputs: list, step_name: str, current_message_batch: list, user_message: dict, message_history: dict, id: str, channel: str) -> None:
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

#a person is fitting them in, so an empty reply goes on file to keep their spot in line
def booking_hold_reply(user_message: dict, id: str, channel: str) -> None:
    print("BOOKING HOLD: a person is fitting them a day on the schedule, so nothing goes back to them and the owner gets texted what they sent")

    replies.write_message(f"systemres_{id}", "")

    owner.note_booking_message(id)

    notify.notify_hand_off(id, channel, user_message)
