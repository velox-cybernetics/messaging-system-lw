#**********IMPORTS**********
#the branches that write replies, plus what's on file about the customer and their booking
from helpers.chains import booking_chains
from helpers.response import greeting
from helpers.response import repeats
from helpers.response import spacing
from helpers.state import owner
from helpers.state import log
from src import branches
from src import temp_booking



#**********GLOBALS**********
#the words good news opens with when it follows an answer


#NEWS OPENER
#"Also have some good news" only follows an answer, so good news that opens the reply starts with "Good news"
ALSO_GOOD_NEWS: str = "Also have some good news, "



#**********BOOKING CHECKS**********
#holds a booking back until a price went out, the vehicle is known and any color is confirmed


#VEHICLE CHECK
#their make or model is on file
def vehicle_on_file(critical_info: dict[str, str]) -> bool:
    make: str | None = critical_info.get("make")

    model: str | None = critical_info.get("model")

    #the same make and model check the pricing branch makes before asking for what's missing
    return make is not None or model is not None


#BOOKING READY
#a price went out to them and their vehicle is on file
def booking_ready(id: str) -> bool:
    #on file once a reply with a $ in it went out to them
    price_sent: dict[str, str] = log.read_info(f"price_sent_{id}")

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    return len(price_sent) > 0 and vehicle_on_file(critical_info)


#COLOR READY
#a wrap or colored PPF only gets booked once the shop can get the color they want
def color_ready(state: dict, id: str) -> bool:
    if(owner.color_check_status(id) == owner.APPROVED_STATUS):
        return True

    #the whole conversation decides it, so a tint question in between never lets a waiting wrap through
    return not branches.conversation_color_job(state)


#BOOKING GUARD
#the route a booking ask really takes, the pricing branch first when the price, the vehicle, the color or the job isn't settled
def booking_guard(state: dict, id: str) -> str:
    if(not booking_ready(id)):
        print("BOOKING HELD: no price went out yet or no make and model on file, so the s_p branch answers first")

        #the reply with their price ends on the schedule question, so their yes to it is what books them
        log.write_info(f"booking_held_{id}", ["held"], ["status"])

        return "service_pricing"

    if(not color_ready(state, id)):
        print("BOOKING HELD: the exact color for the wrap or colored PPF isn't confirmed yet, so the s_p branch asks for it")

        #the pricing branch goes on the color job, so its reply asks for the route or the exact color
        branches.turn_color_job_on(id)

        log.write_info(f"booking_held_{id}", ["held"], ["status"])

        return "service_pricing"

    #every service they want with the price the shop quoted for it, the job the open days go out naming
    booked_services: dict[str, str] = branches.extract_services_pricing(state, "")

    #nothing they want came out of the conversation, so the pricing branch clears up the job first
    if(len(booked_services) == 0):
        print("BOOKING HELD: no service they want came out of the conversation, so the s_p branch answers first")

        return "service_pricing"

    #kept so the days, the deposit and the invoice all go by the job the days went out naming
    log.write_state(f"s_p_confirmed_{id}", booked_services)

    log.clear_info(f"booking_held_{id}", ["status"])

    return "booking_service_acknowledge"


#COLOR WAITING
#the exact color they want is on file and the owner hasn't been asked about it yet
def color_check_waiting(id: str) -> bool:
    color_job_on: bool = len(branches.color_job_on_file(id)) > 0

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    color_check: str = owner.color_check_status(id)

    return branches.color_check_due(color_job_on, critical_info, color_check)


#PRICE NEEDS MORE
#the vehicle, the route, a pic of it or the exact color still missing, read off file after the branch ran since the route it just took in isn't in what core read before it
def price_needs_more(id: str) -> bool:
    color_job_on: bool = len(branches.color_job_on_file(id)) > 0

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    color_check: str = owner.color_check_status(id)

    return branches.pricing_interrogator(color_job_on, critical_info, color_check) is not None


#HELD BOOKING
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

    #their price is out, so the schedule question is what it ends on and their yes to it books them
    return spacing.end_on_booking_question(system_response)



#**********MADE UP DAYS**********
#only the booking chain reads the calendar, so drop off days any other branch writes never go out


#DAYS CUT
#a reply that offered days was booking them, so the schedule question takes their place, unless a person has them
def cut_made_up_days(system_response: str, id: str) -> str:
    kept_reply: str = spacing.drop_day_offers(system_response)

    if(kept_reply == system_response):
        return system_response

    #a person books them, and with nothing left to send they hear nothing and the owner gets texted again
    if(log.read_state(f"restricted_{id}")):
        if(kept_reply == ""):
            owner.restrict(id, owner.REASONS["restricted"])

        return kept_reply

    #core ends a held booking's reply on the schedule question once a price that needs nothing else is in it
    log.write_info(f"booking_held_{id}", ["held"], ["status"])

    #only the days were in it, so the schedule question goes out in their place
    if(kept_reply == ""):
        return spacing.BOOKING_QUESTION

    return kept_reply



#**********OFF LIST ASKS**********
#a reply only ends on one of the shop's own questions, so asking what else they want to know never goes out, and the schedule question takes its place once it's due


#SCHEDULE DUE
#the job has its price and nothing it or the booking needs is missing, so the schedule question is what the reply ends on, unless a person has them
def schedule_due(system_response: str, id: str) -> bool:
    if(log.read_state(f"restricted_{id}")):
        return False

    #a price in this reply, or one that already went out to them
    price_out: bool = "$" in system_response or len(log.read_info(f"price_sent_{id}")) > 0

    return price_out and not price_needs_more(id)


#OFF LIST CUT
#an ask for what else they want to know comes off ("Any other questions on the front end?"), with the schedule question in its place when it's due
def cut_off_list_asks(system_response: str, id: str) -> str:
    off_list: list[str] = spacing.off_list_asks(system_response)

    if(len(off_list) == 0):
        return system_response

    kept_reply: str = repeats.drop_questions(system_response, off_list)

    #one of the shop's own asks is still in it, so it ends on that one, and with none the schedule question goes on once it's due
    keeps_own_ask: bool = len(repeats.question_sentences(kept_reply)) > 0 or spacing.asks_for_pic(kept_reply)

    due: bool = not keeps_own_ask and schedule_due(system_response, id)

    #nothing else went out with it and nothing can take its place, so it stays rather than the reply going out empty
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



#**********INFO ACKS**********
#they nodded along to what we told them, so the chat goes to booking instead of fizzling out


#ACK BOOKING
#"alright sounds good" to info ends on the schedule question once it's due, the one they'd have gotten if they'd asked nothing
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



#**********EARLY COLOR ASKS**********
#the questions the exact price needs go out first and the color they want only after them, whichever branch wrote the reply


#EARLY COLOR CUT
#an ask for the color they want comes off a reply written while the exact price still waits on something, and the ask for that goes on in its place
#a color they already named stays taken in, only the ask for it comes off
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

    #the pic of their vehicle is already asked for, like the few words when they said they'll send it, so that ask stands as is
    if(branches.COLOR_NOW_NEED in needs and spacing.asks_for_pic(kept_reply)):
        return kept_reply

    #the ask for what the price waits on is the one question the reply ends on
    kept_reply = repeats.drop_questions(kept_reply, repeats.question_sentences(kept_reply))

    price_ask: str = branches.price_ask(critical_info, needs, state["message_history"])

    print(f"PRICE ASK IN ITS PLACE: {price_ask}")

    if(kept_reply == ""):
        return price_ask

    return f"{spacing.end_sentence(kept_reply)} {price_ask}"



#**********GOOD NEWS**********
#works the owner's good news about their exact color into the reply that goes out


#NEWS FITS
#the good news only goes on a reply the bot sends, never an empty one or one that handed them to a person
def good_news_fits(system_response: str, id: str) -> bool:
    if(system_response == "" or not owner.news_due(id) or owner.color_check_status(id) != owner.APPROVED_STATUS):
        return False

    return not log.read_state(f"restricted_{id}")


#NEWS WRITTEN
#a reply the generator wrote without the good news in it never goes out in its place
def written_good_news(reply: str) -> bool:
    return "good news" in reply.lower()


#NEWS START
#good news that opens the reply starts with "Good news", since there's no answer for it to follow
def good_news_opener(reply: str) -> str:
    if(not reply.startswith(ALSO_GOOD_NEWS)):
        return reply

    rest: str = reply[len(ALSO_GOOD_NEWS):]

    return f"Good news, {rest}"


#WITH NEWS
#the reply keeps its answer and ends on the good news, empty when the good news didn't get written
def with_good_news(state: dict, id: str, system_response: str) -> str:
    #the open days just went out, so the good news goes in front of them
    if(log.read_info(f"date_pending_{id}")):
        good_news: str = branches.color_approved_reply(state, "", True)

        if(not written_good_news(good_news)):
            return ""

        #the good news acknowledges them, so the days' own opener comes off ("Perfect, so what day" -> "What day")
        days_reply: str = greeting.remove_opener(system_response)

        return booking_chains.join_reply(good_news, days_reply)

    reply: str = branches.color_approved_reply(state, system_response, False)

    if(not written_good_news(reply)):
        return ""

    return good_news_opener(reply)



#**********ROUTING**********
#sends their message to the branch that answers it, while they're free, restricted or picking


#MAIN ROUTE
#the router picks the branch for a customer nobody has yet, and that branch writes the reply
def main_route(state: dict, id: str) -> str:
    system_response: str = ""

    #they wrapped up for now and the shop took it in, so only a message that asks about something again gets a reply, and nobody takes them over
    if(log.read_state(f"convo_ended_{id}")):
        if(not branches.reopens_conversation(state)):
            print("CONVERSATION ENDED: they wrapped up for now and this only closes it out, so it gets no reply")

            return system_response

        print("CONVERSATION REOPENED: they asked about something again, so the router picks it back up")

        log.clear_state(f"convo_ended_{id}")

    #they asked about the small thing again after she said she'd ask the owner, so her line goes out once more and the owner takes it from here
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

    #the pricing branch and a torn booking both go by whether their message asks to get on the books, asked once for both
    booking_asked: bool = (route_result == "service_pricing" or torn_booking) and branches.booking_intent(state)

    #the router leaned booking and only missed the cutoff, so asking to get on the schedule books them the same as a clear pick ("Maybe. What is your schedule like right now?")
    if(torn_booking and booking_asked):
        print("TORN BOOKING: the router leaned booking and they asked to get on the schedule, so the booking guard takes it")

        route_result = "booking_service_acknowledge"

    #wanting to book before a price went out or before the job is clear goes to the pricing branch first
    if(route_result == "booking_service_acknowledge"):
        route_result = booking_guard(state, id)

    #a booking ask that came with a question about the job, so the reply with its price ends on the schedule question
    elif(route_result == "service_pricing" and booking_asked):
        print("BOOKING HELD: they asked to get on the books along with the job, so the reply with its price ends on the schedule question")

        log.write_info(f"booking_held_{id}", ["held"], ["status"])

    #a pic of the exact color sent with "oh shoot wrong one" reads like small talk, so the color never waits on it
    elif(route_result == "general_text" and color_check_waiting(id)):
        print("COLOR CHECK DUE: the exact color they want is on file and the owner hasn't been asked about it, so the s_p branch takes it in and sends him the check")

        route_result = "service_pricing"

    if(route_result == "service_pricing"):
        #the vehicle on file decides whether the reply asks for it before a price that needs it goes out
        critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

        service_return: tuple = branches.pricing_reply(state, critical_info, id)

        system_response = branches.hand_off(service_return, state, id, route_result)

    elif(route_result == "business_operations"):
        business_return: tuple = branches.business_reply(state, id)

        system_response = branches.hand_off(business_return, state, id, route_result)

    #once everything the price needs is on file, the ack goes out and a person takes it from here
    elif(route_result == "services_req_humans"):
        custom_return: tuple = branches.custom_reply(state, id)

        system_response = branches.hand_off(custom_return, state, id, route_result)

    #TEMP BOOKING: the ack lets them know the schedule is getting checked and a person fits them a day
    #booking_chains.offer_days(state, id, "") goes back here once the temp booking flow comes out
    elif(route_result == "booking_service_acknowledge"):
        system_response = temp_booking.schedule_check(state, id)

    #a problem with the shop, a deal they saw, a job at the shop or someone selling to it goes to a person after the ack
    elif(route_result == "escalation"):
        escalation_return: tuple = branches.escalation_reply(state, id)

        system_response = branches.hand_off(escalation_return, state, id, route_result)

    #small talk gets answered and brought back to what they need
    elif(route_result == "general_text"):
        system_response = branches.general_text_reply(state, id)

    #they want to talk on the phone, so the ack gives them the number and a person takes it from here
    elif(route_result == "phone_call"):
        phone_return: tuple = branches.phone_call_reply(state)

        system_response = branches.hand_off(phone_return, state, id, route_result)

    #they're wrapping up for now, so the reply takes it in and leaves the door open, and nothing after it gets a reply until they ask about something again
    elif(route_result == "end_conversation"):
        system_response = branches.end_conversation_reply(state)

        #on file once the reply is written, so a chain that runs again after a timeout still writes it
        log.write_state(f"convo_ended_{id}", "ended")

    #only the shop's own questions end a pricing or small talk reply, so asking what else they want to know comes off, with the schedule question in its place once it's due
    if(route_result in ["service_pricing", "general_text"]):
        system_response = cut_off_list_asks(system_response, id)

        #they just nodded along to what we told them, so it goes to booking instead of a dead end
        system_response = ack_booking_question(state, id, system_response)

    #the color they want only gets asked once the exact price has what it needs, whichever branch wrote the reply
    system_response = cut_early_color_ask(state, id, system_response)

    #only the booking chain reads the calendar, so drop off days any other branch offered are made up and come off
    #the wrap up reply never offers one, and a day it names is the one they already booked, so it stays
    if(route_result not in ["booking_service_acknowledge", "end_conversation"]):
        system_response = cut_made_up_days(system_response, id)

    #the color books getting checked goes out once, so a reply only says they're still getting checked when they ask about the color, whichever branch wrote it
    system_response = branches.repeated_check_reply(state, system_response)

    #a question the shop already asked never goes out again in those words, whichever branch wrote the reply
    return branches.asked_again_reply(state, system_response)


#RESTRICTED ROUTE
#while a person has them, the bot only answers what they ask about the services or the shop, and holds them the rest of the time
#held is True when their last message got a hold reply, so this one only gets one when they're at the shop
def restricted_route(state: dict, id: str, color_swapped: bool, held: bool) -> str:
    system_response: str = ""

    #only the pricing branch sends the owner a color check, so a new exact color never waits on the restricted check
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

    #they're at the shop, so they always hear to come on in, and the owner gets texted they're there
    elif(route_result == "at_shop"):
        owner.restrict(id, owner.REASONS["at_shop"])

        system_response = branches.hold_reply(state)

        owner.hold(id)

    #nothing the bot answers, so the owner gets texted again, and every other one of these gets a hold reply so they're never left on read
    else:
        owner.restrict(id, owner.REASONS["restricted"])

        if(not held):
            system_response = branches.hold_reply(state)

            owner.hold(id)

    #only the shop's own questions end a pricing reply, the same as on the main route, and nothing puts the schedule question on while a person has them
    if(route_result == "service_pricing"):
        system_response = cut_off_list_asks(system_response, id)

    #the pricing branch answers here too, so the color they want waits on what the exact price needs the same way
    system_response = cut_early_color_ask(state, id, system_response)

    system_response = cut_made_up_days(system_response, id)

    #a pricing, business or hold reply only says the color books are still getting checked when they ask about the color, the same as on the main route
    system_response = branches.repeated_check_reply(state, system_response)

    #a question the shop already asked never goes out again in those words, the same as on the main route
    return branches.asked_again_reply(state, system_response)


#MATERIAL PICK
#a pick takes the restriction off with the schedule question, and none of them working waits on the owner
def material_pick_route(state: dict, id: str, held: bool) -> str:
    materials: list[dict[str, str]] = owner.color_materials(id)

    pick: tuple[str, bool] = branches.material_pick(state, materials)

    choice: str = pick[0]

    #no pick and nothing turned down, so it gets the usual restricted reply
    if(choice == branches.OTHER_PICK):
        return restricted_route(state, id, False, held)

    answer: str = ""

    #what they asked along with their pick gets its answer first, with no hold reply since their pick gets taken in right after it
    if(pick[1]):
        restricted_answer: str = restricted_route(state, id, False, True)

        answer = booking_chains.answer_only(restricted_answer)

    if(choice == branches.NO_PICK):
        owner.restrict(id, owner.REASONS["no_material"])

        return answer

    #a pick reads like "material_2", the 2nd pic the owner sent
    material_number: int = int(choice.removeprefix(branches.MATERIAL_PICK_PREFIX))

    material: dict[str, str] = materials[material_number - 1]

    #the reply gets written before the pick goes on file, so a timeout runs this again with nothing changed yet
    reply: str = branches.color_picked_reply(state, id, answer, material.get("name", ""))

    #a drop off day it made up comes off, and the schedule question it was asked with goes back on the end
    kept_reply: str = spacing.drop_day_offers(reply)

    if(kept_reply != reply):
        reply = spacing.end_on_booking_question(kept_reply).strip()

    owner.pick_material(id, material)

    #it ends on the schedule question, so it answers a booking held for the color
    log.clear_info(f"booking_held_{id}", ["status"])

    return reply
