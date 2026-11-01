#**********IMPORTS**********
#python's json and clock, the saved state and hand offs, the reply writer and the temp ack prompt
import json
from datetime import datetime, timedelta

from helpers.calendar import open_dates
from helpers.models import models
from helpers.state import log
from helpers.state import owner
from helpers.state import state_form
from src import branches
from src.prompts.temp_booking import ack as temp_booking_ack



#**********GLOBALS**********
#how long a person has them while he fits them a day, and how long the ack can get


#HOLD DAYS
#they stay restricted this long after the ack goes out, then the bot picks them back up on its own
BOOKING_HOLD_DAYS: int = 4


#ACK LIMITS
SCHEDULE_CHECK_MAX_TOKENS: int = 10*100

#flashx writes the ack at high like the drop off day replies
SCHEDULE_CHECK_EFFORT: str = "high"



#**********SCHEDULE CHECK**********
#the temp booking flow: the ack goes out, a person has them for the hold, and the owner gets texted the job to fit them a day
#the open days, the date chain and the contact chain stay as they are, main_route goes back to booking_chains.offer_days once this comes out


#SCHEDULE ACK
#answers what they asked along with it and takes in the rest of their batch, then lets them know the schedule is getting checked
def schedule_check_reply(state: dict, confirmed_services: dict) -> str:
    #worked out here and never by the generator, so a price or deposit they ask about is the one the shop quoted
    total: str = branches.services_total(confirmed_services)

    deposit: str = branches.services_deposit(confirmed_services)

    pricing_text: str = json.dumps(confirmed_services, ensure_ascii=False)

    state_as_text: str = state_form.state_to_text(state)

    ack_text: str = f"SERVICES_PRICING: {pricing_text}\n TOTAL: {total}\n DEPOSIT: {deposit}\n STATE: {state_as_text}"

    system_prompt: str = temp_booking_ack.prompt()

    return models.generator("SCHEDULE CHECK GENERATOR", system_prompt, ack_text, SCHEDULE_CHECK_MAX_TOKENS, SCHEDULE_CHECK_EFFORT, line_breaks=False)


#SCHEDULE HOLD
#a person has them till the hold runs out, and a hand off in between keeps the same end since write_state keeps its time
def hold_for_schedule(id: str) -> None:
    clear_time: datetime = datetime.now(open_dates.SHOP_TIMEZONE) + timedelta(days=BOOKING_HOLD_DAYS)

    #the plain string "HIL" on file means a person has the chat, so their messages take the restricted route till it comes off
    log.write_state(f"restricted_{id}", "HIL")

    log.expire_at(f"restricted_{id}", clear_time)


#SCHEDULE CHECK
#the ack that goes out, with them restricted for the hold and the owner's schedule request waiting on the reply going out
def schedule_check(state: dict, id: str) -> str:
    #the job they want, saved by the booking guard right before this
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    #the ack gets written before anything goes on file, so a timeout runs this again with nothing changed yet
    reply: str = schedule_check_reply(state, confirmed_services)

    hold_for_schedule(id)

    #texted to the owner once the reply goes out, so he can fit them a day
    owner.ready_schedule_request(id, confirmed_services)

    return reply
