#IMPORTS

import json
from datetime import datetime, timedelta

from helpers.calendar import open_dates
from helpers.models import models
from helpers.state import log
from helpers.state import owner
from helpers.state import state_form
from src import branches
from src.prompts.temp_booking import ack as temp_booking_ack


#GLOBALS

#they stay restricted this long after the ack, then the system picks them back up on its own
BOOKING_HOLD_DAYS: int = 4

SCHEDULE_CHECK_MAX_TOKENS: int = 10*100

#flashx writes the ack at high like the drop off day replies
SCHEDULE_CHECK_EFFORT: str = "high"


#SCHEDULE CHECK

#answers what they asked, takes in the rest, then says the schedule is getting checked
def schedule_check_reply(state: dict, confirmed_services: dict) -> str:
    #worked out here and never by the generator, so the price they hear is the one the shop quoted
    total: str = branches.services_total(confirmed_services)

    deposit: str = branches.services_deposit(confirmed_services)

    pricing_text: str = json.dumps(confirmed_services, ensure_ascii=False)

    state_as_text: str = state_form.state_to_text(state)

    ack_text: str = f"SERVICES_PRICING: {pricing_text}\n TOTAL: {total}\n DEPOSIT: {deposit}\n STATE: {state_as_text}"

    system_prompt: str = temp_booking_ack.prompt()

    return models.generator("SCHEDULE CHECK GENERATOR", system_prompt, ack_text, SCHEDULE_CHECK_MAX_TOKENS, SCHEDULE_CHECK_EFFORT, line_breaks=False)

#a person has them till the hold runs out, a hand off in between keeps the same end
def hold_for_schedule(id: str) -> None:
    clear_time = datetime.now(open_dates.SHOP_TIMEZONE) + timedelta(days=BOOKING_HOLD_DAYS)

    #a person is fitting them a day, so the system stays quiet till it lifts, not even a hold reply
    log.write_state(f"restricted_{id}", owner.BOOKING_STATE)

    log.expire_at(f"restricted_{id}", clear_time)

#the ack with the hold on, temp till main_route goes back to offer_days in booking_chains
def schedule_check(state: dict, id: str) -> str:
    #the job they want, saved by the booking guard right before this
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    #ack first, nothing on file yet, so a timeout just runs this again from scratch
    reply: str = schedule_check_reply(state, confirmed_services)

    hold_for_schedule(id)

    #texted to the owner once the reply goes out, so he can fit them a day
    owner.ready_schedule_request(id, confirmed_services)

    return reply
