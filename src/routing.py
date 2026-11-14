#IMPORTS

from helpers.chains import booking_chains
from helpers.response import greeting
from helpers.response import repeats
from helpers.response import spacing
from helpers.state import owner
from helpers.state import log
from src import branches
from src import temp_booking


#GLOBALS

#only follows an answer, a reply that opens with it gets a plain good news instead
ALSO_GOOD_NEWS: str = "Also have some good news, "


#BOOKING CHECKS

#their make or model is on file
def vehicle_on_file(critical_info: dict[str, str]) -> bool:
    make: str | None = critical_info.get("make")

    model: str | None = critical_info.get("model")

    #the same make and model check the pricing branch makes before asking for whats missing
    return make is not None or model is not None

#a price went out to them and their vehicle is on file
def booking_ready(id: str) -> bool:
    #on file once a reply with a dollar sign in it went out to them
    price_sent: dict[str, str] = log.read_info(f"price_sent_{id}")

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    return len(price_sent) > 0 and vehicle_on_file(critical_info)

#a wrap or colored PPF only gets booked once the shop can get the color they want
def color_ready(state: dict, id: str) -> bool:
    if(owner.color_check_status(id) == owner.APPROVED_STATUS):
        return True

    #the whole conversation decides, so a tint question in between never sneaks a wrap through
    return not branches.conversation_color_job(state)

#where a booking ask really goes, pricing first till price, vehicle, color and job are settled
def booking_guard(state: dict, id: str) -> str:
    if(not booking_ready(id)):
        print("BOOKING HELD: no price went out yet or no make and model on file, so the s_p branch answers first")

        #there price reply ends on the schedule question, so there yes to it books them
        log.write_info(f"booking_held_{id}", ["held"], ["status"])

        return "service_pricing"

    if(not color_ready(state, id)):
        print("BOOKING HELD: the exact color for the wrap or colored PPF isn't confirmed yet, so the s_p branch asks for it")

        #the pricing branch goes on the color job, so it asks for the route or the exact color
        branches.turn_color_job_on(id)

        log.write_info(f"booking_held_{id}", ["held"], ["status"])

        return "service_pricing"

    #every service they want with its quoted price, the job the open days go out naming
    booked_services: dict[str, str] = branches.extract_services_pricing(state, "")

    #nothing they want came out of the conversation, so the pricing branch clears up the job first
    if(len(booked_services) == 0):
        print("BOOKING HELD: no service they want came out of the conversation, so the s_p branch answers first")

        return "service_pricing"

    #kept so the days, the deposit and the invoice all go by the job the days went out naming
    log.write_state(f"s_p_confirmed_{id}", booked_services)

    log.clear_info(f"booking_held_{id}", ["status"])

    return "booking_service_acknowledge"

#the exact color they want is on file and the owner hasn't been asked about it yet
def color_check_waiting(id: str) -> bool:
    color_job_on: bool = len(branches.color_job_on_file(id)) > 0

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    color_check: str = owner.color_check_status(id)

    return branches.color_check_due(color_job_on, critical_info, color_check, id)

#anything the price still misses, read off file fresh since the branch just took in a route
def price_needs_more(id: str) -> bool:
    color_job_on: bool = len(branches.color_job_on_file(id)) > 0

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    color_check: str = owner.color_check_status(id)

    return branches.pricing_interrogator(color_job_on, critical_info, color_check, id) is not None

#a held booking ends on the schedule question once a price that needs nothing else goes out
def held_booking_question(system_response: str, id: str) -> str:
    #the reply already asks it, so the hold is answered
    if(spacing.asks_booking_question(system_response)):
        log.clear_info(f"booking_held_{id}", ["status"])

        return system_response

    #the hold stays on until a price goes out that needs nothing else
    if("$" not in system_response or price_needs_more(id)):
        return system_response

    log.clear_info(f"booking_held_{id}", ["status"])

    #there price is out, so the schedule question is what it ends on and there yes to it books them
    return spacing.end_on_booking_question(system_response)


#INVENTED DAYS

#made up days come off and the schedule question takes there place, unless a person has them
def cut_made_up_days(system_response: str, id: str) -> str:
    kept_reply: str = spacing.drop_day_offers(system_response)

    if(kept_reply == system_response):
        return system_response

    #a person books them, and with nothing left to send the owner gets texted again
    if(log.read_state(f"restricted_{id}")):
        if(kept_reply == ""):
            owner.restrict(id, owner.REASONS["restricted"])

        return kept_reply

    #core ends a held bookings reply on the schedule question once the price is all their
    log.write_info(f"booking_held_{id}", ["held"], ["status"])

    #only the days were in it, so the schedule question goes out in their place
    if(kept_reply == ""):
        return spacing.BOOKING_QUESTION

    return kept_reply


#STRAY ASKS

#priced with nothing missing and nobody has them, so the schedule question is due
def schedule_due(system_response: str, id: str) -> bool:
    if(log.read_state(f"restricted_{id}")):
        return False

    #a price in this reply, or one that already went out to them
    price_out: bool = "$" in system_response or len(log.read_info(f"price_sent_{id}")) > 0

    return price_out and not price_needs_more(id)

#what else do you want to know asks come off, the schedule question goes in when its due
def cut_off_list_asks(system_response: str, id: str) -> str:
    off_list: list[str] = spacing.off_list_asks(system_response)

    if(len(off_list) == 0):
        return system_response

    kept_reply: str = repeats.drop_questions(system_response, off_list)

    #a shop ask still in it gets the last word, otherwise the schedule question once its due
    keeps_own_ask: bool = len(repeats.question_sentences(kept_reply)) > 0 or spacing.asks_for_pic(kept_reply)

    due: bool = not keeps_own_ask and schedule_due(system_response, id)

    #nothing else in it and nothing to replace it, so it stays rather than going out empty
    if(kept_reply == "" and not due):
        print(f"OFF LIST ASK KEPT, NOTHING ELSE IN THE REPLY: {system_response}")

        return system_response

    for sentence in off_list:
        print(f"OFF LIST ASK CUT: {sentence}")

    if(not due):
        return kept_reply

    print(f"SCHEDULE QUESTION IN ITS PLACE: {spacing.BOOKING_QUESTION}")

    if(kept_reply == ""):
        return spacing.BOOKING_QUESTION

    return f"{spacing.end_sentence(kept_reply)} {spacing.BOOKING_QUESTION}"


#INFO ACKS

#a sounds good to info ends on the schedule question once its due
def ack_booking_question(state: dict, id: str, system_response: str) -> str:
    #nothing going out, or it already asks something, so no second question piled on top
    if(system_response.strip() == "" or len(repeats.question_sentences(system_response)) > 0 or spacing.asks_for_pic(system_response)):
        return system_response

    #our last reply already asked them something, so this one gets the every other reply breather
    if(branches.asked_last_reply(state["message_history"])):
        return system_response

    #cheap checks first, jev only gets bugged when the schedule question could actually go out
    if(not schedule_due(system_response, id) or not branches.acks_info(state)):
        return system_response

    print(f"INFO ACKED, SCHEDULE QUESTION ON THE END: {spacing.BOOKING_QUESTION}")

    return f"{spacing.end_sentence(system_response)} {spacing.BOOKING_QUESTION}"


#EARLY COLOR

#a color ask waits till the exact price has what it needs, the price ask goes on instead
def cut_early_color_ask(state: dict, id: str, system_response: str) -> str:
    color_asks: list[str] = spacing.color_want_asks(system_response)

    if(len(color_asks) == 0):
        return system_response

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    needs: list[str] = branches.price_needs(critical_info, id)

    #the exact price has what it needs, so the color they want is what comes next
    if(len(needs) == 0):
        return system_response

    for sentence in color_asks:
        print(f"EARLY COLOR ASK CUT: {sentence}")

    kept_reply: str = repeats.drop_questions(system_response, color_asks)

    #the color now ask is already in, the pic once they said a saturated color, so it stands as is
    if(branches.COLOR_NOW_NEED in needs and branches.color_now_asked(kept_reply, critical_info)):
        return kept_reply

    #the ask for what the price waits on is the one question the reply ends on
    kept_reply = repeats.drop_questions(kept_reply, repeats.question_sentences(kept_reply))

    price_ask: str = branches.price_ask(critical_info, needs, state["message_history"])

    print(f"PRICE ASK IN ITS PLACE: {price_ask}")

    if(kept_reply == ""):
        return price_ask

    return f"{spacing.end_sentence(kept_reply)} {price_ask}"


#GOOD NEWS

#good news only rides a reply the system sends, never an empty one or a hand off to a person
def good_news_fits(system_response: str, id: str) -> bool:
    if(system_response == "" or not owner.news_due(id) or owner.color_check_status(id) != owner.APPROVED_STATUS):
        return False

    return not log.read_state(f"restricted_{id}")

#a reply the generator wrote without the good news in it never goes out in its place
def written_good_news(reply: str) -> bool:
    return "good news" in reply.lower()

#good news that opens the reply drops the also, theres no answer for it to follow
def good_news_opener(reply: str) -> str:
    if(not reply.startswith(ALSO_GOOD_NEWS)):
        return reply

    rest: str = reply[len(ALSO_GOOD_NEWS):]

    return f"Good news, {rest}"

#the reply keeps its answer and ends on the good news, empty when the good news didn't get written
def with_good_news(state: dict, id: str, system_response: str) -> str:
    #the open days just went out, so the good news goes in front of them
    if(log.read_info(f"date_pending_{id}")):
        good_news: str = branches.color_approved_reply(state, "", True)

        if(not written_good_news(good_news)):
            return ""

        #the good news already acknowledges them, so the opener on the days comes off
        days_reply: str = greeting.remove_opener(system_response)

        return booking_chains.join_reply(good_news, days_reply)

    reply: str = branches.color_approved_reply(state, system_response, False)

    if(not written_good_news(reply)):
        return ""

    return good_news_opener(reply)


#ROUTING

#the router picks the branch for a customer nobody has yet, and that branch writes the reply
def main_route(state: dict, id: str) -> str:
    system_response: str = ""

    #they wrapped up and the shop took it in, so only a fresh question gets a reply
    if(log.read_state(f"convo_ended_{id}")):
        if(not branches.reopens_conversation(state)):
            print("CONVERSATION ENDED: they wrapped up for now and this only closes it out, so it gets no reply")

            return system_response

        print("CONVERSATION REOPENED: they asked about something again, so the router picks it back up")

        log.clear_state(f"convo_ended_{id}")

    #they asked about the small thing again after she said she'd ask, so the owner takes it
    if(owner.side_ask_open(id) and branches.side_ask_persists(state)):
        print("SIDE ASK PERSISTED: they asked about the small thing again, so the owner takes it from here")

        system_response = branches.business_lack_info(state, id)

        owner.close_side_ask(id)

        owner.restrict(id, owner.REASONS["side_ask"])

        return system_response

    routed: tuple[str, float, str] = branches.pick_route(state)

    route_result: str = routed[0]

    route_probability: float = routed[1]

    #a booking the router leaned towards but was torn on comes back as another branch
    torn_booking: bool = routed[2] == "booking_service_acknowledge" and route_result != routed[2]

    print("*" * 25)

    print(f"ROUTE RESULT: {route_result}({route_probability:.2f})")

    #pricing and a torn booking both care whether they asked to get on the books, so ask once
    booking_asked: bool = (route_result == "service_pricing" or torn_booking) and branches.booking_intent(state)

    #leaned booking but missed the cutoff, so asking for the schedule still books them
    if(torn_booking and booking_asked):
        print("TORN BOOKING: the router leaned booking and they asked to get on the schedule, so the booking guard takes it")

        route_result = "booking_service_acknowledge"

    #wanting to book before a price or a clear job goes to the pricing branch first
    if(route_result == "booking_service_acknowledge"):
        route_result = booking_guard(state, id)
    elif(route_result == "service_pricing" and booking_asked):
        #a booking ask with a job question, so the price reply ends on the schedule question
        print("BOOKING HELD: they asked to get on the books along with the job, so the reply with its price ends on the schedule question")

        log.write_info(f"booking_held_{id}", ["held"], ["status"])
    elif(route_result == "general_text" and color_check_waiting(id)):
        #a color pic with small talk attached still gets its check, it never waits on chatter
        print("COLOR CHECK DUE: the exact color they want is on file and the owner hasn't been asked about it, so the s_p branch takes it in and sends him the check")

        route_result = "service_pricing"

    if(route_result == "service_pricing"):
        #the vehicle on file decides whether the reply asks for it before the price
        critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

        service_return: tuple = branches.pricing_reply(state, critical_info, id)

        system_response = branches.hand_off(service_return, state, id, route_result)
    elif(route_result == "business_operations"):
        business_return: tuple = branches.business_reply(state, id)

        system_response = branches.hand_off(business_return, state, id, route_result)
    elif(route_result == "services_req_humans"):
        #once the price has everything, the ack goes out and a person takes it from here
        custom_return: tuple = branches.custom_reply(state, id)

        system_response = branches.hand_off(custom_return, state, id, route_result)
    elif(route_result == "booking_service_acknowledge"):
        #temp booking for now, a person fits them a day, offer_days comes back once thats gone
        system_response = temp_booking.schedule_check(state, id)
    elif(route_result == "escalation"):
        #shop problems, deals, job seekers and salespeople go to a person after the ack
        escalation_return: tuple = branches.escalation_reply(state, id)

        system_response = branches.hand_off(escalation_return, state, id, route_result)
    elif(route_result == "general_text"):
        #small talk gets answered and brought back to what they need
        system_response = branches.general_text_reply(state, id)
    elif(route_result == "phone_call"):
        #they want a call, so the ack gives them the number and a person takes it from here
        phone_return: tuple = branches.phone_call_reply(state)

        system_response = branches.hand_off(phone_return, state, id, route_result)
    elif(route_result == "end_conversation"):
        #they're wrapping up, so the reply leaves the door open and the system goes quiet
        system_response = branches.end_conversation_reply(state)

        #on file once the reply is written, so a rerun after a timeout still writes it
        log.write_state(f"convo_ended_{id}", "ended")

    #only the shops own questions end a pricing or small talk reply, schedule question once due
    if(route_result in ["service_pricing", "general_text"]):
        system_response = cut_off_list_asks(system_response, id)

        #they just nodded along to what we told them, so it goes to booking instead of a dead end
        system_response = ack_booking_question(state, id, system_response)

    #the color ask waits on the exact price, whichever branch wrote the reply
    system_response = cut_early_color_ask(state, id, system_response)

    #only booking reads the calendar, other branches make days up, the wrap up names a real one
    if(route_result not in ["booking_service_acknowledge", "end_conversation"]):
        system_response = cut_made_up_days(system_response, id)

    #the color books getting checked goes out once, then only when they ask about the color
    system_response = branches.repeated_check_reply(state, system_response)

    #a question the shop already asked never goes out again in those words
    return branches.asked_again_reply(state, system_response)

#a person has them, so the system only answers service or shop asks and holds them otherwise
def restricted_route(state: dict, id: str, color_swapped: bool, held: bool) -> str:
    system_response: str = ""

    #only pricing sends a color check, so a new exact color never waits on the restricted check
    route_result: str = "service_pricing"

    #the color swapped path skips the decision, so it has no chance to show
    route_probability: float | None = None

    if(color_swapped):
        print("COLOR SWAPPED: they sent a different exact color than the one the owner was checking, so the s_p branch takes it in and sends him its own check")
    else:
        routed: tuple[str, float | None] = branches.pick_restricted_route(state)

        route_result = routed[0]

        route_probability = routed[1]

    print("*" * 25)

    if(route_probability is not None):
        print(f"RESTRICTED ROUTE RESULT: {route_result}({route_probability:.2f})")
    else:
        print(f"RESTRICTED ROUTE RESULT: {route_result}")

    if(route_result == "service_pricing"):
        critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

        service_return: tuple = branches.pricing_reply(state, critical_info, id)

        system_response = branches.hand_off(service_return, state, id, route_result)
    elif(route_result == "business_operations"):
        business_return: tuple = branches.business_reply(state, id)

        system_response = branches.hand_off(business_return, state, id, route_result)
    elif(route_result == "at_shop"):
        #they're at the shop, so they hear come on in and the owner gets texted they're their
        owner.restrict(id, owner.REASONS["at_shop"])

        system_response = branches.hold_reply(state)

        owner.hold(id)
    else:
        #nothing to answer, the owner gets texted and a hold reply goes out unless one just did
        owner.restrict(id, owner.REASONS["restricted"])

        if(not held):
            system_response = branches.hold_reply(state)

            owner.hold(id)

    #only the shops own asks end a pricing reply, no schedule question while a person has them
    if(route_result == "service_pricing"):
        system_response = cut_off_list_asks(system_response, id)

    #pricing answers here too, so the color ask waits on the exact price the same way
    system_response = cut_early_color_ask(state, id, system_response)

    system_response = cut_made_up_days(system_response, id)

    #color books still getting checked only gets said when they ask about the color
    system_response = branches.repeated_check_reply(state, system_response)

    #a question the shop already asked never goes out again in those words
    return branches.asked_again_reply(state, system_response)

#a pick lifts the restriction with the schedule question, none working means the owner again
def material_pick_route(state: dict, id: str, held: bool) -> str:
    materials: list[dict[str, str]] = owner.color_materials(id)

    pick: tuple[str, bool] = branches.material_pick(state, materials)

    choice: str = pick[0]

    #no pick and nothing turned down, so it gets the usual restricted reply
    if(choice == branches.OTHER_PICK):
        return restricted_route(state, id, False, held)

    answer: str = ""

    #there side question gets answered first, no hold reply since the pick lands right after
    if(pick[1]):
        restricted_answer: str = restricted_route(state, id, False, True)

        answer = booking_chains.answer_only(restricted_answer)

    if(choice == branches.NO_PICK):
        owner.restrict(id, owner.REASONS["no_material"])

        return answer

    #a pick reads like material_2, the second pic the owner sent
    material_number: int = int(choice.removeprefix(branches.MATERIAL_PICK_PREFIX))

    material: dict[str, str] = materials[material_number - 1]

    #written before the pick goes on file, so a timeout rerun finds nothing changed yet
    reply: str = branches.color_picked_reply(state, id, answer, material.get("name", ""))

    #a made up drop off day comes off and the schedule question goes back on the end
    kept_reply: str = spacing.drop_day_offers(reply)

    if(kept_reply != reply):
        reply = spacing.end_on_booking_question(kept_reply).strip()

    owner.pick_material(id, material)

    #it ends on the schedule question, so it answers a booking held for the color
    log.clear_info(f"booking_held_{id}", ["status"])

    return reply
