#**********IMPORTS**********
#python's json, the saved state and hand offs, the open days on the calendar and the reply writers
import json

from helpers.calendar import open_dates
from helpers.models import models
from helpers.response import spacing
from helpers.state import owner
from helpers.state import log
from src import branches



#**********SIDE QUESTIONS**********
#answers a price or shop question asked mid booking and puts the booking question after it


#ANSWER ONLY
#the answer with its questions and any days it offered taken off, so the booking question after it is the only one
def answer_only(answer: str) -> str:
    kept_answer: str = ""

    #the days go on the end with their own question, so the answer's questions and any days it made up come off
    for sentence in spacing.split_sentences(spacing.drop_day_offers(answer)):
        if(not sentence.strip().endswith("?")):
            kept_answer = f"{kept_answer}{sentence}"

    return kept_answer.strip()


#BRANCH ANSWER
#a pricing or business question answered by its branch, a flagged answer or something bigger she said she'd ask the owner about hands them to him
def branch_answer(state: dict, id: str, branch: str) -> str:
    branch_return: tuple = ()

    if(branch == "service_pricing"):
        critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

        branch_return = branches.pricing_reply(state, critical_info, id)

    else:
        branch_return = branches.business_reply(state, id)

    #something small goes to the developer on the side, a flag or anything bigger goes to the owner
    answer: str = branches.hand_off(branch_return, state, id, branch)

    return answer_only(answer)


#JOIN REPLY
#the answer first, then the booking question that follows it
def join_reply(answer: str, follow_up: str) -> str:
    #the answer can end without a mark, so it ends its sentence before the follow up goes on after it
    full_reply: str = f"{spacing.end_sentence(answer)} {follow_up}"

    return full_reply.strip()



#**********DATE CHAIN**********
#offers them open drop off days and handles their pick, a no, a price change or a question


#PENDING DATES
#the days offered, in the order they went out (date_1, date_2, ...)
def pending_dates(date_pending: dict[str, str]) -> list[str]:
    offered_dates: list[str] = []

    date_number: int = 1

    while(f"date_{date_number}" in date_pending):
        offered_dates.append(date_pending[f"date_{date_number}"])

        date_number += 1

    return offered_dates


#ASK CONTACT
#they picked a day, so the date chain ends and their name, number and email get asked for the invoice
def ask_contact(state: dict, id: str, date_pending: dict[str, str], offered_dates: list[str]) -> str:
    #the day they picked out of the ones offered, it's the day the invoice locks in
    drop_off_date: str = branches.picked_date(state, offered_dates)

    #the days offered go in, so the day they picked is said as just its weekday when no other one could be meant
    system_response: str = branches.contact_ask_reply(state, id, drop_off_date, offered_dates, branches.CONTACT_FIELDS, "")

    log.clear_info(f"date_pending_{id}", list(date_pending.keys()))

    #a new booking starts with nothing given, so a past booking's info never carries into this one
    log.clear_info(f"contact_pending_{id}", list(log.read_info(f"contact_pending_{id}").keys()))

    #the day they picked is kept with the pending flag, the owner gets texted it with the confirmed services
    log.write_info(f"contact_pending_{id}", ["pending", drop_off_date], ["status", "drop_off_date"])

    return system_response


#SAVE DAYS
#the days going out go on file in place of the old ones, so the next message reads them as the ones offered
def save_offered_days(id: str, date_pending: dict[str, str], offered_dates: list[str], turned_down_dates: list[str], researches: int) -> None:
    #the days going out are kept with the pending flag, with every day turned down and the research count
    field_names: list[str] = ["status", "turned_down", "researches"]

    values: list[str] = ["pending", json.dumps(turned_down_dates), str(researches)]

    for date_number, offered_date in enumerate(offered_dates, start=1):
        field_names.append(f"date_{date_number}")

        values.append(offered_date)

    log.write_info(f"date_pending_{id}", values, field_names)

    #a day left over from a bigger set before this one comes off, only the days just sent get offered again
    stale_field_names: list[str] = []

    for field_name in date_pending:
        if(field_name not in field_names):
            stale_field_names.append(field_name)

    log.clear_info(f"date_pending_{id}", stale_field_names)


#RESEARCH DAYS
#none of the days work, so a fresh set goes out, and once the researches run out a person finds them a day
def research_days(state: dict, id: str, date_pending: dict[str, str], offered_dates: list[str]) -> str:
    researches: int = int(date_pending.get("researches", "0"))

    #every day they turned down so far, the ones just turned down included, so a fresh set never repeats one
    turned_down_dates: list[str] = json.loads(date_pending.get("turned_down", "[]")) + offered_dates

    research_return: tuple = ("", [])

    #the calendar gets searched again for days they haven't turned down, up to 3 times
    if(researches < open_dates.MAX_RESEARCHES):
        research_return = branches.booking_date_research(state, id, turned_down_dates, offered_dates)

    research_dates: list[str] = research_return[1]

    #3 fresh sets went out already or nothing new is open in 3 weeks, so a person finds them a day and the bot goes silent for them
    if(len(research_dates) == 0):
        print(f"DATE RESEARCH RAN OUT: {researches} researches, {len(turned_down_dates)} days turned down")

        system_response: str = branches.booking_date_ack_reply(state, offered_dates, "")

        owner.restrict_booking(id, owner.REASONS["days_ran_out"])

        return system_response

    #the fresh days replace the ones they turned down, and this research is counted
    save_offered_days(id, date_pending, research_dates, turned_down_dates, researches + 1)

    return research_return[0]


#OFFER DAYS
#the open drop off days for the job go out as a first set, a person finds them a day when none are open
def offer_days(state: dict, id: str, reply_before: str) -> str:
    #the open drop off days for the job they want get offered, or the ack goes out when none are open
    booking_return: tuple = branches.booking_date_reply(state, id, reply_before)

    offered_dates: list[str] = booking_return[1]

    #nothing is open in the next 3 weeks, so the ack went out and a person finds them a day, with the bot silent for them till then
    if(len(offered_dates) == 0):
        owner.restrict_booking(id, owner.REASONS["no_open_days"])

    #a first set starts with nothing turned down and no research, a past booking's days never carry over
    else:
        save_offered_days(id, log.read_info(f"date_pending_{id}"), offered_dates, [], 0)

    return booking_return[0]


#REBOOK DAYS
#what they said can change the job, so its services get pulled again with it, and the days go out for the job it is now
def rebook_days(state: dict, id: str, offered_dates: list[str], reply_before: str) -> str:
    #the job the days already went out for, saved when they went out
    booked_services: dict = log.read_state(f"s_p_confirmed_{id}")

    services_pricing: dict[str, str] = branches.extract_services_pricing(state, reply_before)

    #nothing came out of what they said, so the job stays the one the days already went out for
    if(len(services_pricing) == 0):
        services_pricing = booked_services

    log.write_state(f"s_p_confirmed_{id}", services_pricing)

    job_kinds_now: list[str] = open_dates.job_kinds(list(services_pricing.keys()))

    booked_job_kinds: list[str] = open_dates.job_kinds(list(booked_services.keys()))

    #the same kinds of job fit the same days, so the days already offered go out again with the job as it is now
    if(job_kinds_now == booked_job_kinds):
        return branches.date_propose_reply(state, offered_dates, [], id, reply_before)

    #a different kind of job can fit different days, so the open days get found again for it
    return offer_days(state, id, reply_before)


#DATE CHAIN
#the reply to a message while drop off days are waiting on them, it handles a pick, a no, a job or price change or a question
def date_propose_chain(state: dict, id: str) -> str:
    system_response: str = ""

    #the days offered, kept with the pending flag when they went out
    date_pending: dict[str, str] = log.read_info(f"date_pending_{id}")

    offered_dates: list[str] = pending_dates(date_pending)

    #jev decides if they picked one of the offered days, said yes to the job without picking one, or did neither
    agree_result: str = branches.date_agree_analyzer(state)

    if(agree_result == "agree_date"):
        return ask_contact(state, id, date_pending, offered_dates)

    #the job and its price are good with them, so the same days go out again asking which one works
    if(agree_result == "agree_job"):
        return branches.date_propose_reply(state, offered_dates, [], id, "")

    #jev decides if none of the days work, the job or a price is off, they said nevermind, or asked a shop question
    not_agree_result: str = branches.date_not_agree_analyzer(state)

    #none of the offered days work, so other open days get researched, a person steps in once that runs out
    if(not_agree_result == "not_agree_date"):
        system_response = research_days(state, id, date_pending, offered_dates)

    #the job or a price isn't right, so its services get pulled again with what they said and the days go out for it
    elif(not_agree_result == "not_agree_pricing"):
        system_response = rebook_days(state, id, offered_dates, "")

    #they called it off, so the chain ends here
    elif(not_agree_result == "nevermind"):
        system_response = branches.pricing_confirm_ack_reply(state)

        log.clear_info(f"date_pending_{id}", list(date_pending.keys()))

    #a pricing or business question gets answered first
    elif(not_agree_result == "service_pricing" or not_agree_result == "business_operations"):
        answer: str = branch_answer(state, id, not_agree_result)

        #what they asked can change the job, like a priced add on, so the days go out on the end for the job as it is
        follow_up_question: str = rebook_days(state, id, offered_dates, answer)

        system_response = join_reply(answer, follow_up_question)

    return system_response



#**********CONTACT CHAIN**********
#gets their name, number and email for the invoice, then books the job and texts the owner


#MISSING CONTACT
#the contact fields (name, number, email) still not given
def missing_contact(contact_pending: dict[str, str]) -> list[str]:
    missing: list[str] = []

    for field_name in branches.CONTACT_FIELDS:
        if(contact_pending.get(field_name, "") == ""):
            missing.append(field_name)

    return missing


#SAVE CONTACT
#the name, number and email they just gave go on file next to the day they picked
def save_contact(state: dict, id: str, channel: str) -> None:
    user_text: str = state["current_user_message"].get("user_text", "")

    #the email comes straight out of their text, so the owner only ever gets one written out in full
    email: str = models.email_value(user_text)

    contact: dict[str, str] = branches.contact_values(state)

    number: str = contact["number"]

    #pointing to the number they're texting from is that number on blooio, and no number anywhere else
    if(number == branches.TEXTING_NUMBER and channel == "blooio"):
        number = id

    elif(number == branches.TEXTING_NUMBER):
        number = ""

    #a piece they didn't give this time is empty, and an empty one never wipes one they gave before
    log.write_info(f"contact_pending_{id}", [contact["name"], number, email], branches.CONTACT_FIELDS)


#NOTE BOOKED
#what they booked stays on file a few days past its drop off day, so every reply till then knows they just booked
def note_booked(state: dict, id: str, confirmed_services: dict, drop_off_date: str) -> None:
    log.write_info(f"booked_{id}", [json.dumps(confirmed_services), drop_off_date], ["services", "drop_off_date"])

    #it comes off file on its own, and a day already gone takes it off right away
    log.expire_at(f"booked_{id}", branches.booked_clear_time(drop_off_date, state["current_date_time"]))


#BOOK CONTACT
#everything for the invoice is in, so the owner gets texted the estimate and the booking goes on file
def book_contact(state: dict, id: str, contact_pending: dict[str, str]) -> str:
    drop_off_date: str = contact_pending.get("drop_off_date", "")

    #the services they confirmed by picking the day, saved when the days went out for them
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    #the ack gets written first, so a timeout writing it runs the chain again with nothing changed yet
    system_response: str = branches.contact_ack_reply(state, drop_off_date)

    #the owner gets texted everything he needs to send the estimate once the reply goes out
    owner.ready_estimate(id, confirmed_services, drop_off_date, contact_pending)

    note_booked(state, id, confirmed_services, drop_off_date)

    #they're out of the booking chain, so their next message goes through the router with what they booked in its state
    log.clear_info(f"contact_pending_{id}", list(contact_pending.keys()))

    return system_response


#ANSWER FIRST
#a pricing or business question gets answered, then what's still missing for the invoice gets asked for after it
def answer_then_ask_contact(state: dict, id: str, branch: str, missing: list[str], drop_off_date: str) -> str:
    answer: str = branch_answer(state, id, branch)

    #what the shop still needs gets asked for again on the end, the day isn't said again so no offered days go with it
    follow_up_question: str = branches.contact_ask_reply(state, id, drop_off_date, [], missing, answer)

    return join_reply(answer, follow_up_question)


#CONTACT CHAIN
#the reply to a message while their contact info is waiting on them, it saves what they gave or handles why they didn't
def contact_chain(state: dict, id: str, channel: str) -> str:
    system_response: str = ""

    #jev decides one of two things, they gave their name, number or email for the invoice, or they didn't
    contact_result: str = branches.contact_analyzer(state)

    if(contact_result == "contact_info"):
        save_contact(state, id, channel)

    #the day they picked and everything they gave so far, kept with the pending flag
    contact_pending: dict[str, str] = log.read_info(f"contact_pending_{id}")

    missing: list[str] = missing_contact(contact_pending)

    drop_off_date: str = contact_pending.get("drop_off_date", "")

    #all three are in, so the owner gets texted to send the estimate and they're out of the booking chain
    if(len(missing) == 0):
        return book_contact(state, id, contact_pending)

    #some of it came in, so only what's still missing gets asked for
    if(contact_result == "contact_info"):
        return branches.contact_ask_reply(state, id, drop_off_date, [], missing, "")

    #jev decides if they won't give it, are getting it, asked a pricing or business question, or sent spam
    no_contact_result: str = branches.no_contact_analyzer(state)

    #case 1, they won't give it, so the ack goes out and a person sorts out the invoice, with the bot silent for them from here
    if(no_contact_result == "wont_give_info"):
        system_response = branches.no_contact_ack_reply(state, no_contact_result, drop_off_date)

        owner.restrict_booking(id, owner.REASONS["contact_refused"])

    #case 2, they're getting it, so the ack goes out and the shop keeps waiting on their info
    elif(no_contact_result == "getting_info"):
        system_response = branches.no_contact_ack_reply(state, no_contact_result, drop_off_date)

    #case 3, a pricing or business question gets answered first
    elif(no_contact_result == "service_pricing" or no_contact_result == "business_operations"):
        system_response = answer_then_ask_contact(state, id, no_contact_result, missing, drop_off_date)

    #case 4, spam or harassment gets nothing back, a person takes it from here and the bot stays silent
    elif(no_contact_result == "spam_harass"):
        owner.restrict_booking(id, owner.REASONS["spam_harass"])

    return system_response
