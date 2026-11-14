#IMPORTS

import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from helpers.models import models
from helpers.state import log
from helpers.state import owner
from helpers.response import greeting
from helpers.response import spacing
from helpers.response import repeats
from helpers.state import state_form
from helpers.calendar import google_calendar
from helpers.calendar import open_dates
from src.prompts.enforcers import question_enforcer as question_enforcer_prompt
from src.prompts.enforcers import tone_enforcer as tone_enforcer_prompt
from src.prompts.enforcers import leak_check as leak_check_prompt
from src.prompts.enforcers import price_hold_check as price_hold_check_prompt
from src.prompts.router import instructions as router_instructions
from src.prompts.router import examples as router_examples
from src.prompts.pricing import analyzer_examples as pricing_examples
from src.prompts.pricing import checker_instructions as pricing_checker
from src.prompts.pricing import generator as pricing_generator
from src.prompts.pricing import regenerator as pricing_regenerator
from src.prompts.pricing.lack_info import generator as pricing_lack_info_generator
from src.prompts.pricing.lack_info import regenerator as pricing_lack_info_regenerator
from src.prompts.pricing.interrogator import vehicle
from src.prompts.pricing.interrogator import vehicle_color
from src.prompts.pricing.interrogator import which_route
from src.prompts.pricing.interrogator import color_now
from src.prompts.pricing.interrogator import exact_color
from src.prompts.pricing.interrogator import color_checking
from src.prompts.pricing.interrogator import closest_materials
from src.prompts.pricing.interrogator import regenerator as interrogator_regenerator
from src.prompts.business import analyzer_examples as business_examples
from src.prompts.business import checker_instructions as business_checker
from src.prompts.business import generator as business_generator
from src.prompts.business import regenerator as business_regenerator
from src.prompts.business.lack_info import generator as business_lack_info_generator
from src.prompts.business.lack_info import regenerator as business_lack_info_regenerator
from src.prompts.custom import analyzer_examples as custom_examples
from src.prompts.custom.interrogator import wrap_type as custom_wrap_type
from src.prompts.custom.interrogator import vehicle_count as custom_vehicle_count
from src.prompts.custom.interrogator import make_model as custom_make_model
from src.prompts.custom.interrogator import vehicle_model as custom_vehicle_model
from src.prompts.custom.interrogator import logo_file as custom_logo_file
from src.prompts.custom.interrogator import photo as custom_photo
from src.prompts.custom.interrogator import removal as custom_removal
from src.prompts.custom.interrogator import commercial_regenerator
from src.prompts.custom import ack as custom_ack
from src.prompts.pricing_confirm import ack as pricing_confirm_ack
from src.prompts.booking_date import analyzer_instructions as booking_date_instructions
from src.prompts.booking_date import analyzer_examples as booking_date_examples
from src.prompts.booking_date import propose as booking_date_propose
from src.prompts.booking_date import ack as booking_date_ack
from src.prompts.contact import analyzer_instructions as contact_instructions
from src.prompts.contact import analyzer_examples as contact_examples
from src.prompts.contact import ask as contact_ask
from src.prompts.contact import ack as contact_ack
from src.prompts.contact import no_info as contact_no_info
from src.prompts.escalation import generator as escalation_generator
from src.prompts.escalation import regenerator as escalation_regenerator
from src.prompts.general_text import generator as general_text_generator
from src.prompts.general_text import regenerator as general_text_regenerator
from src.prompts.phone_call import ack as phone_call_ack
from src.prompts.end_conversation import ack as end_conversation_ack
from src.prompts.end_conversation import analyzer_examples as end_conversation_examples
from src.prompts.color_approved import generator as color_approved_generator
from src.prompts.color_materials import analyzer_examples as color_materials_examples
from src.prompts.color_materials.picked import generator as color_picked_generator
from src.prompts.color_materials.picked import regenerator as color_picked_regenerator
from src.prompts.restricted import analyzer_examples as restricted_examples
from src.prompts.restricted import hold as restricted_hold
from src.prompts.side_ask import analyzer_examples as side_ask_examples
from src.prompts.asked_again import generator as asked_again_generator


#DETAILS FILES

#reads one of the shops details files into a dict
def read_details(path: str) -> dict:
    with open(path, "r") as file:
        details: dict = json.load(file)

    return details

PRICING_DETAILS: dict = read_details("details_json/service_pricing_details.json")

BUSINESS_DETAILS: dict = read_details("details_json/business_operations_details.json")

CUSTOM_DETAILS: dict = read_details("details_json/custom_service_details.json")


#ANALYZER CODES

#a message about the services or the business in general, these carry every detail
PRICING_GENERAL_CODE: str = "s6"

BUSINESS_GENERAL_CODE: str = "b15"

#a color change in vinyl, and colored PPF, the other way to change the color
COLOR_CHANGE_CODE: str = "s1"

COLORED_PPF_CODE: str = "s3"

#the services whose price hangs on the color it is now
COLOR_CODES: list[str] = [COLOR_CHANGE_CODE, COLORED_PPF_CODE]

#clear PPF and ceramic don't change the color, so with them the wrap is the only route
PPF_CODE: str = "s2"

CERAMIC_COATING_CODE: str = "s5"


#COLOR PICKS

#the film they pick goes on file as the route, asked before any color question
WRAP_ROUTE: str = "wrap"

COLORED_PPF_ROUTE: str = "colored_ppf"

COLOR_ROUTES: list[str] = [WRAP_ROUTE, COLORED_PPF_ROUTE]

#what the route decision answers when they haven't picked or named either film yet
UNDECIDED_ROUTE: str = "undecided"

#a pick is this prefix plus the materials spot in the owners pics, counting from 1
MATERIAL_PICK_PREFIX: str = "material_"

#they don't want any of them
NO_PICK: str = "none"

#they neither picked one nor turned them all down
OTHER_PICK: str = "other"


#COLOR NOW

#pic asks with nothing back before we settle for the saturated color they typed, never a third
COLOR_PIC_ASK_LIMIT: int = 2

#marks a color now that came from their text, no pic means no bright_vehicle read
TYPED_COLOR_SOURCE: str = "text"

#what the typed color extractor pulls, the color now they typed, bright and neutral
TYPED_COLOR_FIELD_NAMES: list[str] = ["color", "bright", "neutral"]

#a typed color says so on file, plus whether its bright since no pic said it
TYPED_COLOR_INFO_NAMES: list[str] = ["color_from", "color_bright"]

#a saturated color they typed sits here while its pic gets asked for, so the asks know only the pic is missing
WAITING_COLOR_NAME: str = "waiting_color"


#PRICE FIRST

#what the exact price still waits on from them, in the order it gets asked
VEHICLE_NEED: str = "vehicle"

ROUTE_NEED: str = "route"

COLOR_NOW_NEED: str = "color_now"

#asked after every price need so its never one, but the job still waits on it
COLOR_WANT_NEED: str = "color_want"

#the owners first ask, then how he words it again, the color now always goes in words first
VEHICLE_COLOR_NOW_ASKS: list[str] = ["What car is it, and what color is it right now?", "What are you driving, and what color's it at right now?", "Which car is it, and what color's it at the moment?"]

#a saturated color came in with the job, so the car gets asked along with a pic of it
VEHICLE_PIC_ASKS: list[str] = ["What car is it? Send me a pic of it if you can", "What are you driving? Shoot me a quick pic of it when you get a sec"]

VEHICLE_ROUTE_ASKS: list[str] = ["What vehicle is it, and which route are you leaning towards?", "What are you driving, and are you leaning more towards the wrap or the colored PPF?"]

VEHICLE_ASKS: list[str] = ["What car is it?", "What are you driving?", "Which car is it?"]

ROUTE_ASKS: list[str] = ["Which route are you leaning towards?", "Are you leaning more towards the wrap or the colored PPF?"]

#the vehicle slot is the model on file, or just the make when thats all there is
COLOR_NOW_ASKS: list[str] = ["What color is the {vehicle} right now?", "What color's the {vehicle} at right now?", "What color is the {vehicle} at the moment?"]

#they already said a saturated color, so its just the pic of it now, softly, as a question so a repeat gets new words
COLOR_PIC_ASKS: list[str] = ["Can you send me a pic of the {vehicle} when you get a chance?", "When you get a sec, could you snap a quick pic of the {vehicle} and send it over, that way I can see the exact color on it?"]


#ASKED AGAIN

#after a tint law question the owner asks how dark again in his exact words, TINT rule 4
SAME_WORDS_ASKS: list[str] = ["Do you know how dark you're wanting to go?"]


#SIDE ASKS

#the sweat smile only goes out on her line, and her line always says she'll ask the owner
NEW_GIRL_EMOJI: str = "😅"

OWNER_ASK_WORDS: str = "ask the owner"

#flagged here means the lack info reply with her line, any other flag goes to the owner
LACK_INFO_BRANCHES: list[str] = ["service_pricing", "business_operations"]


#THRESHOLDS

#a route under this falls back to where its best guess points, see torn_route
ROUTE_THRESHOLD: float = 0.75

#lets the system answer a restricted customer, high since a wrong answer reaches them
RESTRICTED_THRESHOLD: float = 0.65

#reopens a wrapped up chat, low since ghosting a real ask costs more than one extra reply
REOPEN_THRESHOLD: float = 0.4

#over this a service or question counts as asked and its details get used, every analyzer
ANALYZER_THRESHOLD: float = 0.75

#holds the price for a pic, low since a held price beats one without the color
COLOR_JOB_THRESHOLD: float = 0.5

#they asked to book too, so the price reply ends on the schedule question
BOOKING_INTENT_THRESHOLD: float = 0.5

#they just nodded along to what we said, so the schedule question finally gets its shot
ACKS_INFO_THRESHOLD: float = 0.5

#lets a price into the first reply, over half since the owner never wants an unasked one their
PRICE_QUESTION_THRESHOLD: float = 0.6

#puts the route on file, high since a route on file never gets asked again
COLOR_ROUTE_THRESHOLD: float = 0.75

#the details can't answer it, low so a person gets it instead of a made up answer
CHECKER_THRESHOLD: float = 0.65

#how sure jev has to be a question rule broke, real breaks tested way above the noise
QUESTION_ENFORCER_THRESHOLD: float = 0.6

#same slack for tone, perfectly fine replies were scoring right up near this in testing
TONE_ENFORCER_THRESHOLD: float = 0.6

#same cutoff the old enforcer had, so notes in a draft get caught as often as before
LEAK_THRESHOLD: float = 0.7

#they asked for that open day, so it goes ahead of the next ones not turned down
ASKED_DATE_THRESHOLD: float = 0.5

#they asked more with their pick, over half since a miss just waits for their next text
MATERIAL_ASKS_THRESHOLD: float = 0.6

#her owner asks are all small, like wifi, so the dev gets them and the system keeps the chat
SMALL_ASK_THRESHOLD: float = 0.6

#they asked about that small thing again, so the owner takes it from here
SIDE_ASK_PERSIST_THRESHOLD: float = 0.6

#they asked about there color, so the still checking line stays, low since dodging costs more
COLOR_CHECK_ASKED_THRESHOLD: float = 0.4


#GENERATION LIMITS

#fix tries for a flagged reply, each fix gets checked like the first one
REGEN_MAX_ATTEMPTS: int = 2

#flashx rewords a repeat ask at high, a wording that repeats or drops the ask gets redone
ASKED_AGAIN_MAX_TOKENS: int = 10*100

ASKED_AGAIN_EFFORT: str = "high"

ASKED_AGAIN_MAX_ATTEMPTS: int = 3

#pricing token limits, and flashx writes lack info at high, a notch under max so its quicker
PRICING_MAX_TOKENS: int = 10*100

PRICING_EFFORT: str = "high"

PRICING_REGEN_MAX_TOKENS: int = 10*100

PRICING_REGEN_EFFORT: str = "high"

#kimi writes the main reply and its rewrite at max, the replies the most rides on
PRICING_MAIN_EFFORT: str = "max"

PRICING_MAIN_REGEN_EFFORT: str = "max"

#flashx writes every interrogator and its rewrite at high
PRICING_INTERROGATOR_EFFORT: str = "high"

PRICING_INTERROGATOR_REGEN_EFFORT: str = "high"

BUSINESS_MAX_TOKENS: int = 10*100

BUSINESS_EFFORT: str = "high"

BUSINESS_REGEN_MAX_TOKENS: int = 10*100

BUSINESS_REGEN_EFFORT: str = "high"

CUSTOM_MAX_TOKENS: int = 10*100

CUSTOM_EFFORT: str = "high"

CUSTOM_REGEN_MAX_TOKENS: int = 10*100

CUSTOM_REGEN_EFFORT: str = "high"

#flashx writes the commercial wrap interrogators and their rewrites at high
CUSTOM_COMMERCIAL_EFFORT: str = "high"

CUSTOM_COMMERCIAL_REGEN_EFFORT: str = "high"

#flashx writes the photo and removal interrogators at high too
CUSTOM_INTERROGATOR_EFFORT: str = "high"

PRICING_CONFIRM_MAX_TOKENS: int = 10*100

PRICING_CONFIRM_EFFORT: str = "high"

BOOKING_DATE_MAX_TOKENS: int = 10*100

#flashx writes the drop off day replies at high
BOOKING_DATE_EFFORT: str = "high"

CONTACT_MAX_TOKENS: int = 10*100

CONTACT_EFFORT: str = "high"

ESCALATION_MAX_TOKENS: int = 10*100

ESCALATION_EFFORT: str = "high"

ESCALATION_REGEN_MAX_TOKENS: int = 10*100

ESCALATION_REGEN_EFFORT: str = "high"

GENERAL_TEXT_MAX_TOKENS: int = 10*100

GENERAL_TEXT_EFFORT: str = "high"

GENERAL_TEXT_REGEN_MAX_TOKENS: int = 10*100

GENERAL_TEXT_REGEN_EFFORT: str = "high"

HOLD_MAX_TOKENS: int = 10*100

HOLD_EFFORT: str = "high"

PHONE_CALL_MAX_TOKENS: int = 10*100

PHONE_CALL_EFFORT: str = "high"

END_CONVERSATION_MAX_TOKENS: int = 10*100

END_CONVERSATION_EFFORT: str = "high"

COLOR_APPROVED_MAX_TOKENS: int = 10*100

COLOR_APPROVED_EFFORT: str = "high"

COLOR_PICKED_MAX_TOKENS: int = 10*100

COLOR_PICKED_EFFORT: str = "high"

COLOR_PICKED_REGEN_MAX_TOKENS: int = 10*100

COLOR_PICKED_REGEN_EFFORT: str = "high"


#SHOP HOURS

#copied from the business details, 9AM to 5PM weekdays, so an hours change goes here too
SHOP_OPENS = time(9, 0)

#a price promised in about 30 minutes has to land before the shop closes at 5PM
PRICE_BACK_CUTOFF = time(16, 30)

#the last day of the week the shop is open, datetime counts Monday as 0 so Friday is 4
LAST_OPEN_WEEKDAY: int = 4


#COMMERCIAL ASKS

#the fields on file each commercial ask fills, make and model come in together so they're one
COMMERCIAL_GROUP_FIELDS: dict[str, list[str]] = {}

COMMERCIAL_GROUP_FIELDS["wrap_type"] = ["wrap_type"]

COMMERCIAL_GROUP_FIELDS["car_amount"] = ["car_amount"]

COMMERCIAL_GROUP_FIELDS["vehicles"] = ["makes", "models"]

COMMERCIAL_GROUP_FIELDS["vector_files"] = ["vector_files"]

#words that give each ask away, so a pushed ask gets caught however its reworded
COMMERCIAL_GROUP_WORDS: dict[str, list[str]] = {}

COMMERCIAL_GROUP_WORDS["wrap_type"] = ["full wrap", "half wrap", "partial wrap", "decal", "decals", "kind of wrap", "type of wrap", "what wrap", "which job", "leaning towards", "leaning toward"]

COMMERCIAL_GROUP_WORDS["car_amount"] = ["how many", "just the one", "the only one", "have more", "any more", "more you want"]

COMMERCIAL_GROUP_WORDS["vehicles"] = ["make", "makes", "model", "models", "what van", "what vans", "what truck", "what trucks", "what car", "what cars", "what vehicle", "what vehicles", "which van", "which vans", "which truck", "which trucks", "what kind of van", "what kind of vans", "what kind of truck", "what kind of trucks", "the other", "how big", "dimensions", "how long and tall"]

COMMERCIAL_GROUP_WORDS["vector_files"] = ["vector", "logo file", "logo files", "ai file", "eps", "svg", "pdf", "artwork", "print files", "logo that goes", "just the lettering"]


#INVOICE

#the deposit that locks in their spot, a fifth of there confirmed services before tax
DEPOSIT_RATE = Decimal("0.2")

#a drop off day closer than this is just its weekday, further out it gets its date too
WEEKDAY_ONLY_DAYS: int = 7

#drop off days have no year, so one more than this many days behind today is next years
HALF_YEAR_DAYS: int = 182


#JUST BOOKED

#what they booked stays on file till this many days after its drop off day
BOOKED_KEEP_DAYS: int = 2


#CONTACT FIELDS

#all three come in before the owner gets texted to send the estimate
CONTACT_FIELDS: list[str] = ["name", "number", "email"]

#they pointed at the number they text from instead of typing one out
TEXTING_NUMBER: str = "texting"


#ROUTING

#the branch a route decision goes to when the router wasn't sure enough about its pick
def torn_route(category: str, probabilities: dict[str, float]) -> str:
    #torn, but its best guess is a branch that can take it on its own, so it goes there
    if(category in ["service_pricing", "business_operations", "services_req_humans", "escalation", "general_text", "phone_call", "end_conversation"]):
        return category

    #a booking only confirms on a clear pick, so when torn it counts toward the service
    service_probability: float = probabilities["service_pricing"] + probabilities["booking_service_acknowledge"]

    if(service_probability >= ROUTE_THRESHOLD):
        return "service_pricing"

    #torn between service and shop, pricing takes it since its replies carry the shops info too
    if(probabilities["services_req_humans"] < min(service_probability, probabilities["business_operations"])):
        return "service_pricing"

    return "general_text"

#the branch that answers, its chance, and the routers own pick, which differs only when torn
def pick_route(state: dict) -> tuple[str, float, str]:
    route_criteria: dict[str, str] = {}

    route_criteria["service_pricing"] = router_instructions.criteria("service_pricing")

    route_criteria["business_operations"] = router_instructions.criteria("business_operations")

    route_criteria["services_req_humans"] = router_instructions.criteria("services_req_humans")

    route_criteria["booking_service_acknowledge"] = router_instructions.criteria("booking_service_acknowledge")

    route_criteria["escalation"] = router_instructions.criteria("escalation")

    route_criteria["general_text"] = router_instructions.criteria("general_text")

    route_criteria["phone_call"] = router_instructions.criteria("phone_call")

    route_criteria["end_conversation"] = router_instructions.criteria("end_conversation")

    question_text: str = router_instructions.question()

    examples: str = router_examples.examples()

    route_question: dict = {"type": "choice", "instructions": f"{question_text}\n{examples}", "criteria": route_criteria}

    route_answer: dict = models.decision_answer("route", route_question, state)

    category: str = route_answer["choice"]

    confidence: float = route_answer["confidence"]

    probabilities: dict[str, float] = route_answer["probabilities"]

    if(confidence < ROUTE_THRESHOLD):
        user_text: str | None = state["current_user_message"].get("user_text")

        if(not user_text):
            user_text = ""

        #a schedule yes plus a question can land just under, the booking reply answers it
        if(category == "booking_service_acknowledge" and spacing.yes_to_booking_question(user_text, state["message_history"])):
            print(f"ROUTE: a yes to the schedule question, torn at {confidence:.2f}, so it books")

            return (category, probabilities[category], category)

        torn: str = torn_route(category, probabilities)

        print(f"ROUTE TORN: {category}({confidence:.2f}) goes to {torn}")

        return (torn, probabilities[torn], category)

    return (category, probabilities[category], category)


#RESTRICTED ROUTING

#yes or no questions on whether a restricted customer is still the systems to answer
def restricted_analyzer_questions() -> dict[str, dict]:
    questions: dict[str, dict] = {}

    questions["service_pricing"] = {"type": "noul", "instructions": f"Is the customer asking about one of the shop's regular services or what it costs in `current_user_message`, with nothing in it only a person at the shop can handle?\n{restricted_examples.service_pricing_examples()}"}

    questions["business_operations"] = {"type": "noul", "instructions": f"Is the customer asking about the shop itself in `current_user_message`, with nothing in it only a person at the shop can handle?\n{restricted_examples.business_operations_examples()}"}

    questions["at_shop"] = {"type": "noul", "instructions": f"Does the customer say in `current_user_message` that they're at the shop right now?\n{restricted_examples.at_shop_examples()}"}

    return questions

#the branch that answers and its chance, restricted gets None since no question picked it
def pick_restricted_route(state: dict) -> tuple[str, float | None]:
    #a person has the chat, so the system only takes what the details can answer alone
    classified: tuple[list[str], dict[str, float]] = models.classifier(restricted_analyzer_questions(), state, RESTRICTED_THRESHOLD)

    asked: list[str] = classified[0]

    probabilities: dict[str, float] = classified[1]

    print(f"RESTRICTED ANALYZER: {models.codes_with_probabilities(asked, probabilities)}")

    #service plus shop questions go to pricing, its replies carry the shops info too
    if("service_pricing" in asked):
        return ("service_pricing", probabilities["service_pricing"])

    if("business_operations" in asked):
        return ("business_operations", probabilities["business_operations"])

    #they're at the shop, so they always hear to come on in
    if("at_shop" in asked):
        return ("at_shop", probabilities["at_shop"])

    #anything else waits on a person
    return ("restricted", None)


#ENDED CONVERSATIONS

#true when they ask something new after wrapping up, a closing ok or thanks never counts
def reopens_conversation(state: dict) -> bool:
    reopen_question: dict = {"type": "noul", "instructions": f"Does the customer open the conversation back up in `current_user_message`, asking about something or bringing up something new for the shop to answer, after they wrapped it up for now?\n{end_conversation_examples.reopen_examples()}"}

    probability_yes: float = models.decision_answer("reopen", reopen_question, state)["noul"]

    print(f"CONVERSATION REOPENS: {probability_yes:.2f}")

    return probability_yes > REOPEN_THRESHOLD


#REPLY CHECKS

#one json line per detail, the way the generators like it
def details_text(analyzed_details: dict[str, dict], general_code: str | None) -> str:
    #the general code already holds every detail, so nothing goes in twice
    listed_details: dict[str, dict] = analyzed_details.get(general_code, analyzed_details)

    details: str = ""

    for detail in listed_details.values():
        details += f"{json.dumps(detail)}\n"

    return details


#ENFORCERS

#the last thing we asked them, digging back a reply at a time, empty if we never asked
def last_question_asked(message_history: dict) -> str:
    sent_replies: list[str] = spacing.sent_replies(message_history)

    for reply in reversed(sent_replies):
        questions: list[str] = repeats.question_sentences(reply)

        if(len(questions) > 0):
            return questions[-1]

    return ""

#our last reply asked them something, a pic ask counts, so the next one gets a breather
def asked_last_reply(message_history: dict) -> bool:
    last_reply: str = spacing.last_sent_reply(message_history)

    return len(repeats.question_sentences(last_reply)) > 0 or spacing.asks_for_pic(last_reply)

#colors the job still waits on, read like the color asks read them, empty without a color job
def color_needs(id: str) -> list[str]:
    needs: list[str] = []

    if(len(color_job_on_file(id)) == 0):
        return needs

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    #only a pic or link puts the color they want on file, a typed color is just the idea
    if(critical_info.get("want") is None):
        needs.append(COLOR_WANT_NEED)

    #the color now stops being needed once a pic came in or the pic asks ran out
    if(COLOR_NOW_NEED in price_needs(critical_info, id)):
        needs.append(COLOR_NOW_NEED)

    return needs

#the drafts asks for a color the job still needs, only the color ask logic may cut these
def needed_color_asks(draft_reply: str, needs: list[str]) -> list[str]:
    asks: list[str] = []

    if(COLOR_WANT_NEED in needs):
        for sentence in spacing.color_want_asks(draft_reply):
            asks.append(sentence)

    #color_now_asks already leaves the exact color ask out, so no sentence goes in twice
    if(COLOR_NOW_NEED in needs):
        for sentence in spacing.color_now_asks(draft_reply):
            asks.append(sentence)

    return asks

#the draft still asks something once its color asks come out, jev only ever judges questions
def asks_besides(draft_reply: str, color_asks: list[str]) -> bool:
    rest: str = repeats.drop_questions(draft_reply, color_asks)

    return len(repeats.question_sentences(rest)) > 0

#the draft asked for a needed color and the regen asks for none, so that regen gets tossed
def color_ask_dropped(draft_reply: str, regen_reply: str, needs: list[str]) -> bool:
    if(len(needed_color_asks(draft_reply, needs)) == 0):
        return False

    return len(needed_color_asks(regen_reply, needs)) == 0

#the question enforcers slice, our last question, the chat, their message, and the draft
def question_enforcer_state(state: dict, draft_reply: str) -> dict:
    last_question: str = last_question_asked(state["message_history"])

    return {"last_question_asked": last_question, "message_context": state["message_history"], "current_customer_message": state["current_user_message"], "draft_reply": draft_reply}

#tone only needs the chat and the draft, their latest message doesn't change how we sound
def tone_enforcer_state(state: dict, draft_reply: str) -> dict:
    return {"message_context": state["message_history"], "draft_reply": draft_reply}

#the rule jev leans on most, and how sure it is the draft broke anything at all
def broken_rule(answer: dict, follows_pick: str) -> tuple[str, float]:
    probabilities: dict[str, float] = answer["probabilities"]

    #anything jev didn't put on follows is it betting the draft broke something
    broke_probability: float = 1.0 - probabilities.get(follows_pick, 0.0)

    top_rule: str = ""

    top_probability: float = 0.0

    for rule_name, probability in probabilities.items():
        if(rule_name == follows_pick):
            continue

        if(probability > top_probability):
            top_rule = rule_name

            top_probability = probability

    return (top_rule, broke_probability)

#jev eyeballs the drafts questions, empty fix means fine, and color_asks are off limits
def question_enforcer(state: dict, draft_reply: str, color_asks: list[str]) -> tuple[str, float]:
    #all it asks for is a needed color, thats the color logics call, so jev sits this out
    if(len(color_asks) > 0 and not asks_besides(draft_reply, color_asks)):
        color_ask_text: str = " ".join(color_asks)

        print(f"QUESTION ENFORCER: SKIPPED, it only asks for a color the job still waits on: {color_ask_text}")

        return ("", 0.0)

    question: dict = {"type": "choice", "instructions": f"{question_enforcer_prompt.question()}\n{question_enforcer_prompt.examples()}", "criteria": question_enforcer_prompt.criteria()}

    enforcer_state: dict = question_enforcer_state(state, draft_reply)

    answer: dict = models.decision_answer("question_enforcer", question, enforcer_state)

    broken: tuple[str, float] = broken_rule(answer, question_enforcer_prompt.FOLLOWS)

    rule_name: str = broken[0]

    broke_probability: float = broken[1]

    #a blank rule name means jevs rounding ate every rule, so it counts as a pass
    if(broke_probability <= QUESTION_ENFORCER_THRESHOLD or rule_name == ""):
        print(f"QUESTION ENFORCER: False({broke_probability:.2f})")

        return ("", broke_probability)

    #asked again only counts right after the reply that asked, a nod since then frees it up
    if(rule_name == "schedule_asked_again" and not asked_last_reply(state["message_history"]) and acks_info(state)):
        print(f"QUESTION ENFORCER: False({broke_probability:.2f}) schedule_asked_again waved off, they just nodded along to our answer")

        return ("", broke_probability)

    print(f"QUESTION ENFORCER: True({broke_probability:.2f}) {rule_name}")

    fix: str = question_enforcer_prompt.fixes()[rule_name]

    return (f"QUESTION ({rule_name}): {fix}", broke_probability)

#jev listens to how the draft sounds, empty fix means it sounds like us
def tone_enforcer(state: dict, draft_reply: str) -> tuple[str, float]:
    question: dict = {"type": "choice", "instructions": f"{tone_enforcer_prompt.question()}\n{tone_enforcer_prompt.examples()}", "criteria": tone_enforcer_prompt.criteria()}

    enforcer_state: dict = tone_enforcer_state(state, draft_reply)

    answer: dict = models.decision_answer("tone_enforcer", question, enforcer_state)

    broken: tuple[str, float] = broken_rule(answer, tone_enforcer_prompt.FOLLOWS)

    rule_name: str = broken[0]

    broke_probability: float = broken[1]

    #a blank rule name means jevs rounding ate every rule, so it counts as a pass
    if(broke_probability <= TONE_ENFORCER_THRESHOLD or rule_name == ""):
        print(f"TONE ENFORCER: False({broke_probability:.2f})")

        return ("", broke_probability)

    print(f"TONE ENFORCER: True({broke_probability:.2f}) {rule_name}")

    fix: str = tone_enforcer_prompt.fixes()[rule_name]

    return (f"TONE ({rule_name}): {fix}", broke_probability)

#the old safety net, jev reads just the draft for notes the writer forgot to take out
def leak_check(draft_reply: str) -> tuple[str, float]:
    leak_question: dict = {"type": "noul", "instructions": f"{leak_check_prompt.question()}\n{leak_check_prompt.examples()}"}

    answer: dict = models.decision_answer("leak", leak_question, {"draft_reply": draft_reply})

    leak_probability: float = answer["noul"]

    print(f"LEAK CHECK: {leak_probability:.2f}")

    if(leak_probability <= LEAK_THRESHOLD):
        return ("", leak_probability)

    return (leak_check_prompt.fix(), leak_probability)

#runs every check, empty fix when clean, plus how worried the most worried check was
def enforce(state: dict, draft_reply: str, held: bool, needs: list[str]) -> tuple[str, float]:
    #no check ever gets to cut the asks for a color the job still needs
    color_asks: list[str] = needed_color_asks(draft_reply, needs)

    checks: list[tuple[str, float]] = []

    #a dollar sign on a first reply that holds every price is busted, no model needed
    if(held and "$" in draft_reply):
        print("PRICE HOLD BROKEN: the reply gave a price on the shop's first reply")

        checks.append((price_hold_check_prompt.fix(), 1.0))

    checks.append(question_enforcer(state, draft_reply, color_asks))

    checks.append(tone_enforcer(state, draft_reply))

    checks.append(leak_check(draft_reply))

    what_to_fix: str = ""

    worst_probability: float = 0.0

    for check in checks:
        fix: str = check[0]

        probability: float = check[1]

        if(fix == ""):
            continue

        what_to_fix = f"{what_to_fix}{fix}\n"

        if(probability > worst_probability):
            worst_probability = probability

    #whatever broke, the regen hears the color ask stays put while it fixes the rest
    if(what_to_fix != "" and len(color_asks) > 0):
        what_to_fix = f"{what_to_fix}{question_enforcer_prompt.keep_color_ask(color_asks)}\n"

    return (what_to_fix.strip(), worst_probability)

#same input as the draft, then the flagged draft, then what to fix last so its fresh in mind
def regen_text(text: str, response: str, what_to_fix: str, shop_last_reply: str | None) -> str:
    if(shop_last_reply is None):
        return f"{text}\n FLAGGED_RESPONSE: {response}\n WHAT_TO_FIX:\n{what_to_fix}"

    return f"{text}\n SHOP_LAST_REPLY: {shop_last_reply}\n FLAGGED_RESPONSE: {response}\n WHAT_TO_FIX:\n{what_to_fix}"

#checks and rewrites the draft, if every rewrite flunks too the least flagged one goes out
def enforced_reply(state: dict, id: str, text: str, response: str, regen_label: str, regen_prompt: str, regen_generator, max_tokens: int, effort: str, line_breaks: bool, shop_last_reply: str | None, held: bool = False) -> str:
    #the colors the job still waits on, nothing in here changes them so they're read once
    needs: list[str] = color_needs(id)

    #plan b, the draft the checks were least worried about
    least_flagged_reply: str = response

    least_flagged_probability: float = 1.0

    what_to_fix: str = ""

    for attempt in range(REGEN_MAX_ATTEMPTS + 1):
        if(attempt > 0):
            #shop_last_reply stays None for the regens that never read it
            regen_input: str = regen_text(text, response, what_to_fix, shop_last_reply)

            regen_response: str = regen_generator(regen_label, regen_prompt, regen_input, max_tokens, effort, line_breaks=line_breaks)

            #an empty regen never goes out, the next try fixes the same draft
            if(regen_response.strip() == ""):
                continue

            #the regen changed nothing, so checking the same words again is a wasted call
            if(regen_response.strip() == response.strip()):
                print(f"{regen_label} CAME BACK UNCHANGED")

                break

            #the regen tossed a needed color ask, so the regen gets tossed instead
            if(color_ask_dropped(response, regen_response, needs)):
                print(f"{regen_label} DROPPED THE COLOR ASK: {regen_response}")

                continue

            response = regen_response

        checked: tuple[str, float] = enforce(state, response, held, needs)

        what_to_fix = checked[0]

        broke_probability: float = checked[1]

        if(what_to_fix == ""):
            return response

        print(f"WHAT TO FIX: {what_to_fix}")

        if(broke_probability < least_flagged_probability):
            least_flagged_reply = response

            least_flagged_probability = broke_probability

    print(f"{regen_label} STILL FLAGGED, THE LEAST FLAGGED REPLY GOES OUT: {least_flagged_reply}")

    return least_flagged_reply


#HAND OFFS

#the reply has the new girls line, where she isn't sure and says she'll ask the owner
def owner_ask(reply: str) -> bool:
    return NEW_GIRL_EMOJI in reply or OWNER_ASK_WORDS in reply.lower()

#true when everything she'd ask the owner about is small, like the wifi or parking
def small_ask(state: dict, reply: str) -> bool:
    small_question: dict = {"type": "noul", "instructions": f"Is everything SYSTEM_RESPONSE says she isn't sure on and will ask the owner about something small about coming to the shop, like the wifi, the waiting area or parking?\n{side_ask_examples.small_ask_examples()}"}

    state_as_text: str = state_form.state_to_text(state)

    #the reply rides along with the chat, since what she'd ask the owner is what gets judged
    small_state: str = f"STATE: {state_as_text}\nSYSTEM_RESPONSE: {reply}"

    probability_yes: float = models.decision_answer("small_ask", small_question, small_state)["noul"]

    print(f"SMALL ASK: {probability_yes:.2f}")

    return probability_yes > SMALL_ASK_THRESHOLD

#true when they ask again about the small thing the new girl said she'd ask the owner
def side_ask_persists(state: dict) -> bool:
    persist_question: dict = {"type": "noul", "instructions": f"Is the customer asking again about, following up on or pushing for an answer on something small a system_response in `message_history` said she wasn't sure on and would ask the owner about, in `current_user_message`?\n{side_ask_examples.persist_examples()}"}

    probability_yes: float = models.decision_answer("side_ask_persists", persist_question, state)["noul"]

    print(f"SIDE ASK PERSISTS: {probability_yes:.2f}")

    return probability_yes > SIDE_ASK_PERSIST_THRESHOLD

#small asks go to the dev on the side, a flagged reply or anything bigger goes to the owner
def hand_off(branch_return: tuple[str, bool], state: dict, id: str, branch: str) -> str:
    reply: str = branch_return[0]

    flagged: bool = branch_return[1]

    #her line in an unflagged reply, or in the lack info reply a pricing or business flag writes
    asked_owner: bool = owner_ask(reply) and (not flagged or branch in LACK_INFO_BRANCHES)

    #small stuff like wifi goes to the dev on the side, and the system keeps the chat
    if(asked_owner and small_ask(state, reply)):
        print("SIDE ASK: the reply told them she'd ask the owner about something small, so the developer gets it on the side and nobody takes the chat")

        owner.side_ask(id, reply)

        return reply

    #flagged by the checker, so a person takes over and the owner gets texted why
    if(flagged):
        owner.restrict(id, owner.REASONS[branch])
    elif(asked_owner):
        #she said she'd ask the owner about something bigger, so he takes it from here
        owner.restrict(id, owner.REASONS["owner_ask"])

    return reply


#COLOR JOB

#true when a wrap or colored PPF is still the job they want, read from the whole chat
def conversation_color_job(state: dict) -> bool:
    color_job_question: dict = {"type": "noul", "instructions": f"Is a vinyl wrap, a color change or colored PPF the job the customer wants in this conversation, asked about in `current_user_message` or earlier in `message_history` and not moved off of or turned down?\n{pricing_examples.color_job_examples()}"}

    probability_yes: float = models.decision_answer("color_job", color_job_question, state)["noul"]

    color_job_now: bool = probability_yes > COLOR_JOB_THRESHOLD

    print(f"CONVERSATION COLOR JOB: {color_job_now}({probability_yes:.2f})")

    return color_job_now

#the services the analyzer named, the general code names none
def named_codes(codes: list[str]) -> list[str]:
    named: list[str] = []

    for code in codes:
        if(code != PRICING_GENERAL_CODE):
            named.append(code)

    return named

#the color codes on file, an old file with just the on flag means both
def color_codes_in(on_file: dict) -> list[str]:
    if("codes" not in on_file and on_file.get("on", False)):
        return COLOR_CODES

    return on_file.get("codes", [])

#the color codes the conversation is on, empty when it isn't on a wrap or colored PPF
def color_job_on_file(id: str) -> list[str]:
    return color_codes_in(log.read_state(f"s_p_color_job_{id}"))

#a color job still missing the color it is now, the only time the color or a pic of it gets asked for
def color_now_missing(id: str) -> bool:
    return len(color_job_on_file(id)) > 0 and log.read_info(f"criticalInfo_{id}").get("color") is None

#how many replies asked for a pic of there vehicle while the color it is now wasn't on file
def color_pic_asks(id: str) -> int:
    return log.read_count(f"color_pic_asks_{id}")

#a sent pic ask while the color now is missing is one more ask for it
def note_color_pic_ask(id: str, reply: str) -> None:
    if(not spacing.asks_for_pic(reply) or not color_now_missing(id)):
        return

    asks: int = log.next_count(f"color_pic_asks_{id}")

    print(f"COLOR PIC ASKS: {asks}")

#the color now is done once its on file or the pic asks ran out, either way the job moves on
def color_now_settled(critical_info: dict[str, str], id: str) -> bool:
    if(critical_info.get("color") is not None):
        return True

    return color_pic_asks(id) >= COLOR_PIC_ASK_LIMIT

#the color now they typed anywhere in the chat, plus bright and neutral, empty if never typed
def typed_color_read(user_message: dict, message_history: dict) -> tuple[str, bool, bool]:
    #the whole chat, since they may have typed the color before we ever asked
    conversation: dict = {"current_user_message": user_message, "message_history": message_history}

    typed_output: str = models.extract_typed_color(state_form.state_to_text(conversation))

    typed_values: list[str] = models.extractor_values(typed_output, TYPED_COLOR_FIELD_NAMES)

    neutral: bool = typed_values[TYPED_COLOR_FIELD_NAMES.index("neutral")].lower() == "yes"

    #a neutral color is never a bright one, whatever the bright read says
    bright: bool = typed_values[TYPED_COLOR_FIELD_NAMES.index("bright")].lower() == "yes" and not neutral

    return (typed_values[TYPED_COLOR_FIELD_NAMES.index("color")], bright, neutral)

#a typed neutral goes on file right away, any other color once the pic asks ran out
def typed_color_check(user_message: dict, message_history: dict, id: str) -> str:
    typed_read: tuple[str, bool, bool] = typed_color_read(user_message, message_history)

    typed_color: str = typed_read[0]

    #they never typed it, so it stays missing till a pic or the color comes
    if(typed_color == ""):
        return ""

    neutral: bool = typed_read[2]

    #till the pic asks run out only a neutral color goes by what they typed
    if(not neutral and color_pic_asks(id) < COLOR_PIC_ASK_LIMIT):
        print(f"TYPED COLOR: {typed_color} isn't neutral, so the pic of it still gets asked for")

        #kept so the asks know they already said it and only the pic is missing
        log.write_info(f"criticalInfo_{id}", [typed_color], [WAITING_COLOR_NAME])

        return ""

    bright: str = ""

    if(typed_read[1]):
        bright = "yes"
    else:
        bright = "no"

    log.write_info(f"criticalInfo_{id}", [typed_color, TYPED_COLOR_SOURCE, bright], ["color"] + TYPED_COLOR_INFO_NAMES)

    neutral_text: str = ""

    if(neutral):
        neutral_text = "yes"
    else:
        neutral_text = "no"

    print(f"TYPED COLOR: {typed_color} (bright: {bright}, neutral: {neutral_text}) goes on file in place of a pic of it")

    return typed_color

#a typed color goes in the state with its bright flag, so replies price it like a pic
def add_color_now(state: dict, critical_info: dict[str, str]) -> dict:
    if(critical_info.get("color_from") != TYPED_COLOR_SOURCE):
        return state

    state["color_now"] = {"color": critical_info.get("color", ""), "bright_vehicle": critical_info.get("color_bright", "no")}

    return state

#catches a color typed as the job first comes up, a failed read just leaves the pic ask
def first_color_fill(state: dict, id: str) -> None:
    if(not color_now_missing(id)):
        return

    try:
        typed_color_check(state["current_user_message"], state["message_history"], id)
    except Exception as error:
        print(f"TYPED COLOR ERROR: {error}")

        return

    add_color_now(state, log.read_info(f"criticalInfo_{id}"))

#a booking held for the color goes back to pricing on its job, both codes if none is named
def turn_color_job_on(id: str) -> None:
    codes: list[str] = color_job_on_file(id)

    if(len(codes) == 0):
        codes = COLOR_CODES

    log.write_state(f"s_p_color_job_{id}", {"codes": codes})

#works out which color jobs the chat is on and puts that on file
def color_job(codes: list[str], state: dict, id: str) -> list[str]:
    named: list[str] = named_codes(codes)

    color_codes: list[str] = []

    #kept as there latest message names the job
    if(len(named) > 0):
        for code in named:
            if(code in COLOR_CODES):
                color_codes.append(code)

        #another service on top of the job on file only ends it once they moved off it
        job_on_file: list[str] = color_job_on_file(id)

        if(len(color_codes) == 0 and len(job_on_file) > 0 and conversation_color_job(state)):
            return job_on_file
    else:
        #a follow up that names no service, like a pic or lets do it, keeps the job on file
        on_file: dict = log.read_state(f"s_p_color_job_{id}")

        if(len(on_file) > 0):
            return color_codes_in(on_file)

        #nothing on file yet, maybe another branch took the job ask, so read the chat
        if(conversation_color_job(state)):
            color_codes = COLOR_CODES

    log.write_state(f"s_p_color_job_{id}", {"codes": color_codes})

    #the route belongs to the color job, so moving off it clears the route too
    if(len(color_codes) == 0):
        log.clear_info(f"criticalInfo_{id}", ["route"])

    return color_codes


#COLOR ROUTE

#the route picked from the whole chat, how sure the model is, and its chance for that route
def decided_route(state: dict) -> tuple[str, float, float]:
    route_criteria: dict[str, str] = {}

    route_criteria[WRAP_ROUTE] = pricing_examples.wrap_route_criteria()

    route_criteria[COLORED_PPF_ROUTE] = pricing_examples.colored_ppf_route_criteria()

    route_criteria[UNDECIDED_ROUTE] = pricing_examples.undecided_route_criteria()

    question_text: str = pricing_examples.color_route_instructions()

    examples: str = pricing_examples.color_route_examples()

    route_question: dict = {"type": "choice", "instructions": f"{question_text}\n{examples}", "criteria": route_criteria}

    route_answer: dict = models.decision_answer("color_route", route_question, state)

    choice: str = route_answer["choice"]

    return (choice, route_answer["confidence"], route_answer["probabilities"][choice])

#the film they pick goes on file, so follow ups go by it and it never gets asked again
def color_route(state: dict, codes: list[str], id: str) -> None:
    #a wrap next to clear PPF or a coating is the only color change in play, nothing to decide
    wrap_only: bool = COLOR_CHANGE_CODE in codes and COLORED_PPF_CODE not in codes and (PPF_CODE in codes or CERAMIC_COATING_CODE in codes)

    if(wrap_only):
        picked: str = WRAP_ROUTE

        confidence: float = 1.0

        probability: float = 1.0
    else:
        decided: tuple[str, float, float] = decided_route(state)

        picked = decided[0]

        confidence = decided[1]

        probability = decided[2]

    print(f"COLOR ROUTE: {picked}({probability:.2f})")

    #only a clear pick goes on file, so a vague follow up never loses the one they picked
    if(picked in COLOR_ROUTES and confidence >= COLOR_ROUTE_THRESHOLD):
        log.write_info(f"criticalInfo_{id}", [picked], ["route"])

#vehicle, route, color now and exact color are in, and the owner hasn't been asked about it yet
def color_check_due(color_job_on: bool, critical_info: dict[str, str], color_check: str, id: str) -> bool:
    vehicle_known: bool = critical_info.get("make") is not None or critical_info.get("model") is not None

    #the owner checks the color in there picked film, so the check waits on the route too
    route_picked: bool = critical_info.get("route") is not None

    #the color now counts as in once the pic asks ran out, even with nothing typed
    exact_color_in: bool = color_now_settled(critical_info, id) and critical_info.get("want") is not None

    return color_job_on and vehicle_known and route_picked and exact_color_in and color_check == ""


#EARLY ASKS

#what the price still waits on in ask order, the color now drops out once the pic asks run out
def price_needs(critical_info: dict[str, str], id: str) -> list[str]:
    needs: list[str] = []

    if(critical_info.get("make") is None and critical_info.get("model") is None):
        needs.append(VEHICLE_NEED)

    #a color change with no film picked needs the route before any color question
    if(len(color_job_on_file(id)) > 0 and critical_info.get("route") is None):
        needs.append(ROUTE_NEED)

    if(not color_now_settled(critical_info, id)):
        needs.append(COLOR_NOW_NEED)

    return needs

#the ways to ask for the first thing the price waits on, grouped the way the owner asks them
def price_ask_words(needs: list[str], color_waiting: bool) -> list[str]:
    if(needs[0] == VEHICLE_NEED):
        #no film picked yet, so the vehicle ask comes with the route ask and the color waits
        if(ROUTE_NEED in needs):
            return VEHICLE_ROUTE_ASKS

        #they already said a saturated color, so the car gets asked with a pic of it
        if(COLOR_NOW_NEED in needs and color_waiting):
            return VEHICLE_PIC_ASKS

        if(COLOR_NOW_NEED in needs):
            return VEHICLE_COLOR_NOW_ASKS

        return VEHICLE_ASKS

    if(needs[0] == ROUTE_NEED):
        return ROUTE_ASKS

    #the color is already said, so its only the pic of it thats missing
    if(color_waiting):
        return COLOR_PIC_ASKS

    return COLOR_NOW_ASKS

#the price ask in words we haven't used yet, or the last wording once they're all used
def price_ask(critical_info: dict[str, str], needs: list[str], message_history: dict) -> str:
    vehicle: str | None = critical_info.get("model")

    if(not vehicle):
        vehicle = critical_info.get("make")

    if(not vehicle):
        vehicle = ""

    asks: list[str] = []

    color_waiting: bool = critical_info.get(WAITING_COLOR_NAME) is not None

    for ask in price_ask_words(needs, color_waiting):
        asks.append(ask.format(vehicle=vehicle))

    earlier_replies: list[str] = spacing.sent_replies(message_history)

    for ask in asks:
        if(len(repeats.repeated_questions(ask, earlier_replies)) == 0):
            return ask

    return asks[-1]

#the reply already asks what the color now waits on, the pic once they said a saturated color
def color_now_asked(reply: str, critical_info: dict[str, str]) -> bool:
    if(critical_info.get(WAITING_COLOR_NAME) is not None):
        return spacing.asks_for_pic(reply)

    return len(spacing.color_now_asks(reply)) > 0


#PRICE HOLD

#goes on a replys input while every price is held, the prompts and regens watch for it
PRICE_HOLD_LINE: str = "PRICE_HOLD: yes"

#true when they ask what something costs, the only way a price gets into the first reply
def price_question(state: dict) -> bool:
    question: dict = {"type": "noul", "instructions": f"Is the customer asking what something costs, or about its price, in `current_user_message`?\n{pricing_examples.price_question_examples()}"}

    probability_yes: float = models.decision_answer("price_question", question, state)["noul"]

    print(f"PRICE QUESTION: {probability_yes:.2f}")

    return probability_yes > PRICE_QUESTION_THRESHOLD

#true on the first reply unless they asked a price, the form intros reply counts as first too
def price_held(state: dict) -> bool:
    #a reply already went out, so every price goes by the rules like any other reply
    if(greeting.replied_before(state["message_history"])):
        return False

    held: bool = not price_question(state)

    print(f"PRICE HOLD: {held}")

    return held

#the replys input, with the hold line tacked on while every price is held
def held_text(text: str, held: bool) -> str:
    if(not held):
        return text

    return f"{text}\n {PRICE_HOLD_LINE}"

#a price that slipped past the hold gets cut with its sentence, all cut means a person answers
def held_price_cut(reply: str, held: bool, id: str) -> str:
    if(not held):
        return reply

    kept_reply: str = spacing.drop_prices(reply)

    if(kept_reply == "" and reply.strip() != ""):
        owner.restrict(id, owner.REASONS["price_hold"])

    return kept_reply


#PRICING

#the yes or no questions that find which services their message asks about, one code each
def pricing_analyzer_questions() -> dict[str, dict]:
    questions: dict[str, dict] = {}

    questions["s1"] = {"type": "noul", "instructions": f"Is the customer asking about a color change in `current_user_message`?\n{pricing_examples.color_change_examples()}"}

    questions["s2"] = {"type": "noul", "instructions": f"Is the customer asking about paint protection film (PPF) in `current_user_message`?\n{pricing_examples.ppf_examples()}"}

    questions["s3"] = {"type": "noul", "instructions": f"Is the customer asking about colored paint protection film (colored PPF, PPF in a color) in `current_user_message`?\n{pricing_examples.color_ppf_examples()}"}

    questions["s4"] = {"type": "noul", "instructions": f"Is the customer asking about window tint in `current_user_message`?\n{pricing_examples.window_tint_examples()}"}

    questions["s5"] = {"type": "noul", "instructions": f"Is the customer asking about a ceramic coating (a coating on the paint, a wrap or PPF, not ceramic window tint) or a paint correction in `current_user_message`?\n{pricing_examples.ceramic_coating_examples()}"}

    questions[PRICING_GENERAL_CODE] = {"type": "noul", "instructions": f"Is the customer asking about the shop's services in general, not one service in particular, in `current_user_message`?\n{pricing_examples.general_services_examples()}"}

    return questions

#the services the message is about, the job on file if it names none, and its color codes
def pricing_services(state: dict, id: str) -> tuple[list[str], list[str]]:
    classified: tuple[list[str], dict[str, float]] = models.classifier(pricing_analyzer_questions(), state, ANALYZER_THRESHOLD)

    codes: list[str] = classified[0]

    probabilities: dict[str, float] = classified[1]

    #runs before the check, so every analyzed message updates the job the chat is on
    color_codes: list[str] = color_job(codes, state, id)

    #a message no question picked up, like a bare pic, carries on with the job on file
    if(codes == []):
        if(len(color_codes) > 0):
            codes = color_codes
        else:
            codes = [PRICING_GENERAL_CODE]
    else:
        #another service asked mid color job gets the jobs details next to its own
        for code in color_codes:
            if(code not in codes):
                codes.append(code)

    print(f"ANALYZER: {models.codes_with_probabilities(codes, probabilities)}")

    return (codes, color_codes)

#the details have nothing on it, so she owns up and says she'll ask the owner
def pricing_lack_info(state: dict, id: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #nothing to answer from, so no details go in
    lack_info_text: str = f"STATE: {state_as_text}"

    system_prompt: str = pricing_lack_info_generator.prompt()

    response: str = models.generator("LACK INFO GENERATOR", system_prompt, lack_info_text, PRICING_MAX_TOKENS, PRICING_EFFORT, line_breaks=False)

    regen_prompt: str = pricing_lack_info_regenerator.prompt()

    return enforced_reply(state, id, lack_info_text, response, "LACK INFO REGEN", regen_prompt, models.generator, PRICING_REGEN_MAX_TOKENS, PRICING_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)

#the prompt that asks for what the price or booking still waits on, None when nothings missing
def pricing_interrogator(color_job_on: bool, critical_info: dict[str, str], color_check: str, id: str) -> str | None:
    make: str | None = critical_info.get("make")

    model: str | None = critical_info.get("model")

    want: str | None = critical_info.get("want")

    route: str | None = critical_info.get("route")

    #color changes go vinyl or colored PPF, and that pick comes before any color talk
    route_needed: bool = color_job_on and route is None

    #a wrap or colored PPF price waits on the color now till its on file or the pic asks ran out
    color_needed: bool = color_job_on and not color_now_settled(critical_info, id)

    if(make is None and model is None):
        #no car yet, so ask for it, with the color thrown in when the job needs that too
        if(color_needed):
            return vehicle_color.prompt()

        return vehicle.prompt()
    elif(route_needed):
        #both routes go out first and they pick one, colors can wait
        return which_route.prompt()
    elif(color_needed):
        return color_now.prompt()
    elif(color_job_on and want is None):
        #price can go out, but booking waits on a pic or link of the exact color
        return exact_color.prompt()
    elif(color_job_on and color_check in ["", owner.PENDING_STATUS]):
        #they sent it, now the owner makes sure we can actually get it
        return color_checking.prompt()
    elif(color_check == owner.MATERIALS_STATUS):
        #can't get that exact color, so they pick from the closest ones we can order
        return closest_materials.prompt()

    #nothing missing, the main generator takes it from here
    return None

#flashx writes the ask, held is True on a first reply that holds every price
def pricing_interrogate(state: dict, id: str, user_text: str, interrogator_prompt: str, held: bool) -> str:
    response: str = models.generator("INTERROGATOR", interrogator_prompt, user_text, PRICING_MAX_TOKENS, PRICING_INTERROGATOR_EFFORT, line_breaks=True)

    #the regen reads the shops last reply on its own, so nothing from it goes out twice
    shop_last_reply: str = spacing.last_sent_reply(state["message_history"])

    #the regen gets the whole interrogator prompt, so it knows whats missing too
    regen_prompt: str = interrogator_regenerator.prompt(interrogator_prompt)

    return enforced_reply(state, id, user_text, response, "INTERROGATOR REGEN", regen_prompt, models.generator, PRICING_REGEN_MAX_TOKENS, PRICING_INTERROGATOR_REGEN_EFFORT, line_breaks=True, shop_last_reply=shop_last_reply, held=held)

#a booking ask that landed here with a job question still ends on the schedule question
def booking_intent(state: dict) -> bool:
    booking_question: dict = {"type": "noul", "instructions": f"Is the customer asking to get on the schedule or the books, to book it, or when they can get in or bring it in, in `current_user_message`?\n{pricing_examples.booking_intent_examples()}"}

    probability_yes: float = models.decision_answer("booking_intent", booking_question, state)["noul"]

    print(f"BOOKING INTENT: {probability_yes:.2f}")

    return probability_yes > BOOKING_INTENT_THRESHOLD

#a sounds good to what we told them is a nod, not a dead end, so the booking question is next
def acks_info(state: dict) -> bool:
    ack_question: dict = {"type": "noul", "instructions": f"Is the customer only taking in or agreeing with what the shop's last reply told them in `current_user_message`, with nothing asked, picked, turned down or put off, and nothing in `message_history` saying they're still deciding, waiting on the vehicle or getting back to the shop?\n{pricing_examples.acks_info_examples()}"}

    probability_yes: float = models.decision_answer("acks_info", ack_question, state)["noul"]

    print(f"ACKS INFO: {probability_yes:.2f}")

    return probability_yes > ACKS_INFO_THRESHOLD

#the reply, plus whether the details came up empty, the lack info reply goes out then
def pricing_reply(state: dict, critical_info: dict[str, str], id: str) -> tuple:
    #the state build only grabbed a typed color if the color job was already going
    job_was_on: bool = len(color_job_on_file(id)) > 0

    services: tuple[list[str], list[str]] = pricing_services(state, id)

    service_details: dict[str, dict] = models.analyzed_details(services[0], PRICING_DETAILS, PRICING_GENERAL_CODE)

    color_job_on: bool = len(services[1]) > 0

    print(f"COLOR JOB: {color_job_on}")

    #a color change can go vinyl or colored PPF, so both sets of details ride along
    if(COLOR_CHANGE_CODE in service_details and COLORED_PPF_CODE not in service_details):
        service_details[COLORED_PPF_CODE] = PRICING_DETAILS[COLORED_PPF_CODE]

    #colored PPF brings the wraps details too, handy when it blows there budget
    if(COLORED_PPF_CODE in service_details and COLOR_CHANGE_CODE not in service_details):
        service_details[COLOR_CHANGE_CODE] = PRICING_DETAILS[COLOR_CHANGE_CODE]

    #there film pick goes on file first, so teh route gets asked before any color question
    if(color_job_on):
        color_route(state, services[0], id)

        #the job just came up, so a neutral color they typed goes on file right now
        if(not job_was_on):
            first_color_fill(state, id)

        critical_info = log.read_info(f"criticalInfo_{id}")

    state_as_text: str = state_form.state_to_text(state)

    details: str = details_text(service_details, PRICING_GENERAL_CODE)

    user_text: str = f"SERVICE_DETAILS: {details}\n STATE: {state_as_text}"

    check_rules: str = pricing_checker.instructions()

    check_question: str = f"Is everything the customer is asking for in current_user_message something SERVICE_DETAILS has no answer for, with no part of the message covered, per the rules defined here\n{check_rules}\n?"

    service_check: bool = models.checker(check_question, state, "SERVICE_DETAILS", details, CHECKER_THRESHOLD)

    if(service_check):
        return (pricing_lack_info(state, id), service_check)

    #the first reply holds every price unless they asked what something costs
    held: bool = price_held(state)

    user_text = held_text(user_text, held)

    color_check: str = owner.color_check_status(id)

    interrogator_prompt: str | None = pricing_interrogator(color_job_on, critical_info, color_check, id)

    #the owner gets the exact color they sent once, so he can see if we can get it
    if(color_check_due(color_job_on, critical_info, color_check, id)):
        owner.request_color_check(id, critical_info.get("route", ""))

    #somethings still missing, so the reply answers what it can and asks for the rest
    if(interrogator_prompt is not None):
        interrogated: str = pricing_interrogate(state, id, user_text, interrogator_prompt, held)

        return (held_price_cut(interrogated, held, id), service_check)

    system_prompt: str = pricing_generator.prompt()

    response: str = models.s_p_generator("MAIN GENERATOR", system_prompt, user_text, PRICING_MAX_TOKENS, PRICING_MAIN_EFFORT, line_breaks=True)

    #the regen reads the shops last reply on its own, so nothing from it goes out twice
    shop_last_reply: str = spacing.last_sent_reply(state["message_history"])

    regen_prompt: str = pricing_regenerator.prompt()

    reply: str = enforced_reply(state, id, user_text, response, "MAIN REGEN", regen_prompt, models.s_p_generator, PRICING_REGEN_MAX_TOKENS, PRICING_MAIN_REGEN_EFFORT, line_breaks=True, shop_last_reply=shop_last_reply, held=held)

    #a price that slipped past the hold never makes it out on the first reply
    return (held_price_cut(reply, held, id), service_check)


#BUSINESS

#the yes or no questions that find what their message asks about the shop, one code each
def business_analyzer_questions() -> dict[str, dict]:
    questions: dict[str, dict] = {}

    questions["b1"] = {"type": "noul", "instructions": f"Is the customer asking about the shop's hours in `current_user_message`?\n{business_examples.hours_examples()}"}

    questions["b2"] = {"type": "noul", "instructions": f"Is the customer asking how long the shop has been in business in `current_user_message`?\n{business_examples.years_in_business_examples()}"}

    questions["b3"] = {"type": "noul", "instructions": f"Is the customer asking about the shop's name in `current_user_message`?\n{business_examples.business_name_examples()}"}

    questions["b4"] = {"type": "noul", "instructions": f"Is the customer asking who owns the shop in `current_user_message`?\n{business_examples.owner_examples()}"}

    questions["b5"] = {"type": "noul", "instructions": f"Is the customer asking where the shop is or how getting the car there works in `current_user_message`?\n{business_examples.address_examples()}"}

    questions["b6"] = {"type": "noul", "instructions": f"Is the customer asking for the shop's phone number in `current_user_message`?\n{business_examples.phone_examples()}"}

    questions["b7"] = {"type": "noul", "instructions": f"Is the customer asking for the shop's email in `current_user_message`?\n{business_examples.email_examples()}"}

    questions["b8"] = {"type": "noul", "instructions": f"Is the customer asking about the shop's website in `current_user_message`?\n{business_examples.website_examples()}"}

    questions["b9"] = {"type": "noul", "instructions": f"Is the customer asking how many people work at the shop in `current_user_message`?\n{business_examples.employees_examples()}"}

    questions["b10"] = {"type": "noul", "instructions": f"Is the customer asking whether the shop is licensed, registered or insured in `current_user_message`?\n{business_examples.license_examples()}"}

    questions["b11"] = {"type": "noul", "instructions": f"Is the customer asking who they are talking to, or whether this is a bot or a real person, in `current_user_message`?\n{business_examples.person_talking_to_examples()}"}

    questions["b12"] = {"type": "noul", "instructions": f"Is the customer asking which payment methods the shop takes in `current_user_message`?\n{business_examples.payments_examples()}"}

    questions["b13"] = {"type": "noul", "instructions": f"Is the customer asking about the shop's social media in `current_user_message`?\n{business_examples.social_media_examples()}"}

    questions["b14"] = {"type": "noul", "instructions": f"Is the customer asking about financing or paying for the job over time in `current_user_message`?\n{business_examples.financing_examples()}"}

    questions[BUSINESS_GENERAL_CODE] = {"type": "noul", "instructions": f"Is the customer asking about the business in general, not one detail in particular, in `current_user_message`?\n{business_examples.general_business_examples()}"}

    return questions

#the business details have nothing on it, so she says she'll ask the owner
def business_lack_info(state: dict, id: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #nothing to answer from, so no details go in
    lack_info_text: str = f"STATE: {state_as_text}"

    system_prompt: str = business_lack_info_generator.prompt()

    response: str = models.generator("LACK INFO GENERATOR", system_prompt, lack_info_text, BUSINESS_MAX_TOKENS, BUSINESS_EFFORT, line_breaks=False)

    regen_prompt: str = business_lack_info_regenerator.prompt()

    return enforced_reply(state, id, lack_info_text, response, "LACK INFO REGEN", regen_prompt, models.generator, BUSINESS_REGEN_MAX_TOKENS, BUSINESS_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)

#the reply, plus whether the details came up empty, the lack info reply goes out then
def business_reply(state: dict, id: str) -> tuple:
    business_details: dict[str, dict] = models.analyzer(business_analyzer_questions(), state, BUSINESS_DETAILS, BUSINESS_GENERAL_CODE, ANALYZER_THRESHOLD)

    state_as_text: str = state_form.state_to_text(state)

    details: str = details_text(business_details, BUSINESS_GENERAL_CODE)

    user_text: str = f"BUSINESS_DETAILS: {details}\n STATE: {state_as_text}"

    check_rules: str = business_checker.instructions()

    check_question: str = f"Is everything the customer is asking for in current_user_message something BUSINESS_DETAILS has no answer for, with no part of the message covered, per the rules defined here\n{check_rules}\n?"

    business_check: bool = models.checker(check_question, state, "BUSINESS_DETAILS", details, CHECKER_THRESHOLD)

    if(business_check):
        return (business_lack_info(state, id), business_check)

    system_prompt: str = business_generator.prompt()

    response: str = models.generator("MAIN GENERATOR", system_prompt, user_text, BUSINESS_MAX_TOKENS, BUSINESS_EFFORT, line_breaks=False)

    regen_prompt: str = business_regenerator.prompt()

    reply: str = enforced_reply(state, id, user_text, response, "MAIN REGEN", regen_prompt, models.generator, BUSINESS_REGEN_MAX_TOKENS, BUSINESS_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)

    return (reply, business_check)


#CUSTOM INFO

#the values out of the extractors line, raises when it isn't the format
def custom_values(extractor_output: str, field_names: list[str]) -> list[str]:
    #only the first line is the format, anything the model adds under it is never info
    extracted_line: str = extractor_output.strip().splitlines()[0]

    extracted_values: list[str] = []

    for field_name, element in zip(field_names, extracted_line.split("|")):
        parts: list[str] = element.split(":", 1)

        label: str = parts[0].strip().lower()

        #a piece with no colon or the wrong label isn't the format, so nothing gets saved
        if(len(parts) < 2 or label != field_name):
            raise ValueError(f"not the {field_name} format, got {extractor_output}")

        extracted_values.append(parts[1].strip())

    return extracted_values

#a new vehicle count means the makes and models get asked again
def clear_stale_vehicles(id: str, extracted_values: list[str], field_names: list[str]) -> None:
    extracted_info: dict[str, str] = dict(zip(field_names, extracted_values))

    car_amount: str = extracted_info["car_amount"]

    #a new amount can outgrow the vehicles on file, so the ones it left empty come off
    if(car_amount != "" and car_amount != log.read_info(f"custom_service_{id}").get("car_amount")):
        stale_fields: list[str] = []

        for field_name in ["makes", "models"]:
            if(extracted_info[field_name] == ""):
                stale_fields.append(field_name)

        log.clear_info(f"custom_service_{id}", stale_fields)

#puts the custom job info the extractor pulled out of their message on file
def save_custom_info(id: str, extractor_output: str, field_names: list[str], commercial_wrap: bool) -> None:
    #extractor chatter saves nothing, the reply still asks for what isn't on file
    try:
        extracted_values: list[str] = custom_values(extractor_output, field_names)

        if(commercial_wrap and len(extracted_values) == len(field_names)):
            clear_stale_vehicles(id, extracted_values, field_names)

        log.write_info(f"custom_service_{id}", extracted_values, field_names)
    except Exception as error:
        print(f"C_S EXTRACTOR ERROR: {error}")

#saves what there message gave for the job and hands back the fields this job needs
def custom_extract_and_save(id: str, user_text: str, commercial_wrap: bool, removal: bool) -> list[str]:
    #a commercial wrap needs the wrap type, the vehicles and the logo files
    if(commercial_wrap):
        field_names: list[str] = ["wrap_type", "car_amount", "makes", "models", "vector_files"]

        extractor_output: str = models.extract_commercial_wrap(user_text)
    elif(removal):
        #old PPF or an old wrap coming off needs a photo and how long its been on
        field_names: list[str] = ["media", "time_on"]

        extractor_output: str = models.extract_removal(user_text)
    else:
        #every other custom job needs a photo
        field_names: list[str] = ["media"]

        extractor_output: str = models.extract_photo(user_text)

    save_custom_info(id, extractor_output, field_names, commercial_wrap)

    return field_names


#CUSTOM ACK

#when the owner gets back with the custom price, worked out from the shops hours
def custom_price_back(current_date_time: str) -> str:
    shop_time = datetime.strptime(current_date_time, state_form.CURRENT_DATE_TIME_FORMAT)

    weekday: int = shop_time.weekday()

    clock = shop_time.time()

    #open, and the 30 minutes lands before close
    if(weekday <= LAST_OPEN_WEEKDAY and SHOP_OPENS <= clock < PRICE_BACK_CUTOFF):
        return "in about 30 minutes"

    #a weekday before the shop opens
    if(weekday <= LAST_OPEN_WEEKDAY and clock < SHOP_OPENS):
        return "first thing this morning"

    #monday through thursday after hours, the next day is a weekday
    if(weekday < LAST_OPEN_WEEKDAY):
        return "first thing tomorrow morning"

    #friday after hours and the weekend
    return "Monday morning"

#the reply that lets them know a person prices the custom job and when they'll hear back
def custom_ack_reply(state: dict, user_text: str, custom_service_info: dict[str, str], field_names: list[str]) -> str:
    #only this jobs fields, so info on file for another custom job never gets read back
    info_on_file: dict[str, str] = {}

    for field_name in field_names:
        info_on_file[field_name] = custom_service_info[field_name]

    info_text: str = json.dumps(info_on_file, ensure_ascii=False)

    price_back: str = custom_price_back(state["current_date_time"])

    ack_text: str = f"{user_text}\n INFO_ON_FILE: {info_text}\n PRICE_BACK: {price_back}"

    system_prompt: str = custom_ack.prompt()

    return models.generator("ACK GENERATOR", system_prompt, ack_text, CUSTOM_MAX_TOKENS, CUSTOM_EFFORT, line_breaks=False)


#ASKED AGAIN

#the how dark question after a tint law ask is the one ask allowed out again word for word
def same_words_ask(question: str) -> bool:
    for ask in SAME_WORDS_ASKS:
        if(repeats.asked_words(question) == repeats.asked_words(ask)):
            return True

    return False

#new words still ask just what the ask did, pic and schedule asks match, and no new price
def keeps_ask(ask: str, wording: str) -> bool:
    if(wording == "" or "\n" in wording or len(repeats.question_sentences(wording)) == 0):
        return False

    if("$" in wording and "$" not in ask):
        return False

    if(spacing.asks_for_pic(wording) != spacing.asks_for_pic(ask)):
        return False

    return spacing.asks_booking_question(wording) == spacing.asks_booking_question(ask)

#the rewordings input, the chat, the reply with the ask, and every wording thats off limits
def asked_again_text(state: dict, reply: str, ask: str, used_wordings: list[str]) -> str:
    state_as_text: str = state_form.state_to_text(state)

    used_text: str = "\n".join(used_wordings)

    return f"STATE: {state_as_text}\n REPLY: {reply}\n ASK: {ask}\n ASKED_BEFORE:\n{used_text}"

#the ask in fresh words that still ask the same thing, empty string when every try flunks
def new_wording(state: dict, reply: str, ask: str, earlier_replies: list[str]) -> str:
    #asks we already sent plus each failed try, so the next try steers clear of them all
    used_wordings: list[str] = []

    for earlier_reply in earlier_replies:
        used_wordings.extend(repeats.asks(earlier_reply))

    system_prompt: str = asked_again_generator.prompt()

    for attempt in range(1, ASKED_AGAIN_MAX_ATTEMPTS + 1):
        asked_text: str = asked_again_text(state, reply, ask, used_wordings)

        wording: str = models.generator("ASKED AGAIN", system_prompt, asked_text, ASKED_AGAIN_MAX_TOKENS, ASKED_AGAIN_EFFORT, line_breaks=False).strip()

        if(keeps_ask(ask, wording) and len(repeats.repeated_questions(wording, earlier_replies)) == 0):
            return wording

        print(f"ASKED AGAIN TRY {attempt} CAN'T GO OUT: {wording}")

        if(wording != ""):
            used_wordings.append(wording)

    return ""

#repeat questions get new words, or get cut unless they're all the reply says
def asked_again_reply(state: dict, reply: str) -> str:
    earlier_replies: list[str] = spacing.sent_replies(state["message_history"])

    for question in repeats.repeated_questions(reply, earlier_replies):
        if(same_words_ask(question)):
            continue

        sentences: list[str] = spacing.split_sentences(reply)

        spot: tuple[int, int] | None = repeats.ask_spot(sentences, question)

        #the same question twice in the reply, and new words already went in for it
        if(spot is None):
            continue

        ask: str = "".join(sentences[spot[0]:spot[1]]).strip()

        print(f"ASKED AGAIN IN THE SAME WORDS: {ask}")

        wording: str = new_wording(state, reply, ask, earlier_replies)

        kept_reply: str = repeats.swap_ask(sentences, spot, wording)

        if(kept_reply == ""):
            print(f"ASKED AGAIN KEPT, NOTHING ELSE IN THE REPLY: {ask}")

            continue

        if(wording == ""):
            print(f"ASKED AGAIN CUT: {ask}")
        else:
            print(f"ASKED AGAIN IN NEW WORDS: {wording}")

        reply = kept_reply

    return reply


#CHECK REPEATS

#true when they ask about the exact color they sent, if we found it or when they'll hear back
def color_check_asked(state: dict) -> bool:
    asked_question: dict = {"type": "noul", "instructions": f"Is the customer asking about the exact color they sent over for their wrap or colored PPF, whether the shop found it or can get it, where the check on it stands or when they'll hear back on it, in `current_user_message`?\n{pricing_examples.color_check_asked_examples()}"}

    probability_yes: float = models.decision_answer("color_check_asked", asked_question, state)["noul"]

    print(f"COLOR CHECK ASKED: {probability_yes:.2f}")

    return probability_yes > COLOR_CHECK_ASKED_THRESHOLD

#drops the still checking line once they've heard it, unless they asked or its all their is
def repeated_check_reply(state: dict, reply: str) -> str:
    check_lines: list[str] = spacing.still_checking_lines(reply)

    if(len(check_lines) == 0):
        return reply

    #nobody told them the color books are getting checked yet, so this one stays
    if(not spacing.color_check_sent(state["message_history"])):
        return reply

    kept_reply: str = repeats.drop_questions(reply, check_lines)

    if(kept_reply == ""):
        print(f"STILL CHECKING KEPT, NOTHING ELSE IN THE REPLY: {reply}")

        return reply

    #they asked about the color they sent, so where it stands is there answer
    if(color_check_asked(state)):
        return reply

    for sentence in check_lines:
        print(f"STILL CHECKING CUT: {sentence}")

    #the shop never ends a text on a period, so the one the cut left behind comes off
    if(kept_reply.endswith(".") and not kept_reply.endswith("..")):
        kept_reply = kept_reply[:-1]

    return kept_reply


#REPEATED ASKS

#the commercial wrap detail our last reply asked for, None when it didn't ask for one
def last_asked_group(id: str, message_history: dict) -> str | None:
    asked: dict[str, str] = log.read_info(f"c_s_asked_{id}")

    group: str | None = asked.get("group")

    question: str | None = asked.get("question")

    if(group is None or question is None):
        return None

    #only counts when our last sent reply asked it, another branchs reply asked something else
    if(not repeats.asked_in(question, spacing.last_sent_reply(message_history))):
        return None

    return group

#files the replys last question with its detail, so the next reply can tell if it got dodged
def save_asked(id: str, group: str, response: str) -> None:
    questions: list[str] = repeats.question_sentences(response)

    #no question went out, so whatever the next reply asks is never a repeat
    if(len(questions) == 0):
        log.clear_info(f"c_s_asked_{id}", ["group", "question"])

        return

    log.write_info(f"c_s_asked_{id}", [group, questions[-1]], ["group", "question"])

#true when the question asks for that groups detail, going by its words
def asks_group(question: str, group: str) -> bool:
    plain_text: str = " ".join(repeats.plain_words(question))

    question_text: str = f" {plain_text} "

    for words in COMMERCIAL_GROUP_WORDS[group]:
        if(f" {words} " in question_text):
            return True

    return False

#the replys questions we already asked, plus ones still chasing the detail they skipped
def repeated_asks(response: str, earlier_replies: list[str], group: str, skipped_group: str) -> list[str]:
    repeated: list[str] = repeats.repeated_questions(response, earlier_replies)

    if(skipped_group == ""):
        return repeated

    #what they skipped waits for a later reply, so asking it now in other words still counts
    for question in repeats.question_sentences(response):
        if(asks_group(question, skipped_group) and not asks_group(question, group) and question not in repeated):
            repeated.append(question)

    return repeated

#the reply minus any question worded like one we already asked, rewritten when it repeats
def unrepeated_reply(state: dict, interrogator_text: str, response: str, regen_prompt: str, group: str, skipped_group: str) -> str:
    #every reply we sent so far, so no question goes out the same way twice
    earlier_replies: list[str] = spacing.sent_replies(state["message_history"])

    repeated: list[str] = repeated_asks(response, earlier_replies, group, skipped_group)

    if(len(repeated) == 0):
        return response

    #the enforcer let a repeat slip by, so the regen gets told which one
    print(f"REPEATED QUESTION: {repeated}")

    repeated_text: str = " ".join(repeated)

    regen_text: str = f"{interrogator_text}\n FLAGGED_RESPONSE: {response}\n REPEATED_QUESTION: {repeated_text}"

    regen_response: str = models.generator("REPEAT REGEN", regen_prompt, regen_text, CUSTOM_REGEN_MAX_TOKENS, CUSTOM_COMMERCIAL_REGEN_EFFORT, line_breaks=False)

    regen_repeated: list[str] = repeated_asks(regen_response, earlier_replies, group, skipped_group)

    #a regen that came back empty never goes out, the first replys rest does
    if(regen_response.strip() != "" and len(regen_repeated) == 0):
        return regen_response

    #the regen repeated it too, so cut it, the first replys rest goes when the regen has none
    for reply, reply_repeated in [(regen_response, regen_repeated), (response, repeated)]:
        kept_reply: str = repeats.drop_questions(reply, reply_repeated)

        if(kept_reply != ""):
            print(f"REPEATED QUESTION CUT: {reply_repeated}")

            return kept_reply

    #both replies were only the question, so it stays and something still goes out
    print(f"REPEATED QUESTION KEPT, NOTHING ELSE IN THE REPLY: {regen_response}")

    return regen_response


#COMMERCIAL WRAP

#how many vehicles are on file, said as a short add on to the make and model ask
def vehicle_count(car_amount: str | None) -> str:
    #no count on file when that ask got pushed to a later reply, so the line leaves it out
    if(car_amount is None):
        return ""

    return f", {car_amount} in all"

#what the price still needs in the owners order, each as its group, prompt and one line ask
def commercial_wrap_missing(custom_service_info: dict[str, str], services: str) -> list[tuple]:
    wrap_type: str | None = custom_service_info.get("wrap_type")

    car_amount: str | None = custom_service_info.get("car_amount")

    makes: str | None = custom_service_info.get("makes")

    vehicle_models: str | None = custom_service_info.get("models")

    vector_files: str | None = custom_service_info.get("vector_files")

    missing: list[tuple] = []

    if(wrap_type is None):
        missing.append(("wrap_type", custom_wrap_type.prompt, f"Whether the {services} is decals, a half wrap or a full wrap."))

    if(car_amount is None):
        missing.append(("car_amount", custom_vehicle_count.prompt, f"How many vehicles the {services} is for."))

    #make and model are one ask, and once every make is in the model gets asked on its own
    if(makes is None):
        missing.append(("vehicles", custom_make_model.prompt, f"The make and model of each vehicle the {services} is for{vehicle_count(car_amount)}."))
    elif(vehicle_models is None):
        missing.append(("vehicles", custom_vehicle_model.prompt, f"The model of each vehicle the {services} is for, makes on file: {makes}."))

    if(vector_files is None):
        missing.append(("vector_files", custom_logo_file.prompt, f"Whether they have the logo and artwork for the {services} as vector files (an AI, EPS, SVG or PDF file)."))

    return missing

#true when they filled in some other commercial wrap detail than the one we asked for
def gave_other_info(info_before: dict[str, str], info_after: dict[str, str], group: str) -> bool:
    for other_group, field_names in COMMERCIAL_GROUP_FIELDS.items():
        if(other_group == group):
            continue

        for field_name in field_names:
            value: str | None = info_after.get(field_name)

            #a field this message filled or changed, like how many when we asked which job
            if(value is not None and value != info_before.get(field_name)):
                return True

    return False

#the detail to ask now, what we already asked, and the one they skipped for something else
def commercial_ask(state: dict, id: str, missing: list[tuple], info_before: dict[str, str], custom_service_info: dict[str, str]) -> tuple:
    first: tuple = missing[0]

    #the last reply asked something else, so whats missing first gets asked as usual
    if(last_asked_group(id, state["message_history"]) != first[0]):
        return (first, "", "")

    #they wrote back without it, so it goes in as already asked and gets reworded
    already_asked: str = first[2]

    #they gave something else instead, so ask the next thing and circle back to this one later
    if(gave_other_info(info_before, custom_service_info, first[0]) and len(missing) > 1):
        print(f"ASKED AGAIN SKIPPED: {first[0]}, asking {missing[1][0]} instead")

        return (missing[1], already_asked, first[0])

    return (first, already_asked, "")

#asks for the next commercial wrap detail, held is True on a first reply that holds every price
def commercial_interrogate(state: dict, id: str, user_text: str, ask: tuple, already_asked: str, skipped_group: str, held: bool) -> str:
    interrogator_prompt: str = ask[1]()

    interrogator_text: str = f"{user_text}\n INFO_NEEDED: {ask[2]}"

    #what they skipped last time, so it never gets asked the same way twice in a row
    if(already_asked != ""):
        interrogator_text = f"{interrogator_text}\n ALREADY_ASKED: {already_asked}"

    response: str = models.generator("INTERROGATOR", interrogator_prompt, interrogator_text, CUSTOM_MAX_TOKENS, CUSTOM_COMMERCIAL_EFFORT, line_breaks=False)

    regen_prompt: str = commercial_regenerator.prompt(interrogator_prompt)

    response = enforced_reply(state, id, interrogator_text, response, "INTERROGATOR REGEN", regen_prompt, models.generator, CUSTOM_REGEN_MAX_TOKENS, CUSTOM_COMMERCIAL_REGEN_EFFORT, line_breaks=False, shop_last_reply=None, held=held)

    #the enforcers can miss a question asked twice in a row, so the code double checks
    return unrepeated_reply(state, interrogator_text, response, regen_prompt, ask[0], skipped_group)

#the next detail ask, or the ack once the price has everything it needs
def commercial_wrap_reply(state: dict, id: str, user_text: str, services: str, info_before: dict[str, str], custom_service_info: dict[str, str], field_names: list[str], held: bool) -> tuple:
    missing: list[tuple] = commercial_wrap_missing(custom_service_info, services)

    #the price has all it needs, so the ack goes out and a person takes it from here
    if(len(missing) == 0):
        log.clear_info(f"c_s_asked_{id}", ["group", "question"])

        return (custom_ack_reply(state, user_text, custom_service_info, field_names), True)

    ask: tuple = commercial_ask(state, id, missing, info_before, custom_service_info)

    response: str = commercial_interrogate(state, id, user_text, ask[0], ask[1], ask[2], held)

    save_asked(id, ask[0][0], response)

    return (response, False)


#CUSTOM

#the yes or no questions that find which custom job their message asks about, one code each
def custom_analyzer_questions() -> dict[str, dict]:
    questions: dict[str, dict] = {}

    questions["c1"] = {"type": "noul", "instructions": f"Is the customer asking about a commercial wrap (a wrap, logos, decals, lettering or graphics for a business) in `current_user_message`?\n{custom_examples.commercial_wrap_examples()}"}

    questions["c2"] = {"type": "noul", "instructions": f"Is the customer asking about a custom wrap on a personal vehicle (a partial, a two tone, a specialty film or a custom design, not for a business) in `current_user_message`?\n{custom_examples.custom_wrap_examples()}"}

    questions["c3"] = {"type": "noul", "instructions": f"Is the customer asking about PPF or clear bra that's already on the vehicle now getting taken off, redone or replaced in `current_user_message`?\n{custom_examples.ppf_removal_examples()}"}

    questions["c4"] = {"type": "noul", "instructions": f"Is the customer asking about a chrome delete (covering or blacking out the chrome) in `current_user_message`?\n{custom_examples.chrome_delete_examples()}"}

    questions["c5"] = {"type": "noul", "instructions": f"Is the customer asking about some other job the shop's services don't list, one that isn't a commercial wrap, a custom wrap, old PPF or an old wrap coming off or a chrome delete (body work, PPF on just one piece outside the front end or after the shop offered them the front end, a motorcycle, boat or RV and the like), in `current_user_message`?\n{custom_examples.other_job_examples()}"}

    questions["c6"] = {"type": "noul", "instructions": f"Is the customer asking about a vinyl wrap that's already on the vehicle now getting taken off, redone or replaced in `current_user_message`?\n{custom_examples.wrap_removal_examples()}"}

    return questions

#the custom services named in one line, or job when none could be named
def custom_services(custom_details: dict[str, dict]) -> str:
    service_names: list[str] = []

    for custom_detail in custom_details.values():
        service_names.append(custom_detail["service"])

    services: str = " and ".join(service_names)

    #no custom service could be named, so the one line is about the job as a whole
    if(services == ""):
        services = "job"

    return services

#the prompt and ask while a removal still needs its photo or how long the films been on
def removal_missing(custom_service_info: dict[str, str], services: str) -> tuple[str, str]:
    media_sent: str | None = custom_service_info.get("media")

    time_on: str | None = custom_service_info.get("time_on")

    interrogator_prompt: str = custom_removal.prompt()

    #the owner asks for both at once, then only for whichever one is still missing
    if(media_sent is None and time_on is None):
        return (interrogator_prompt, f"How long it's been on and a photo of it as it is now, for the {services}.")
    elif(time_on is None):
        return (interrogator_prompt, f"How long it's been on, for the {services}. The photo is on file.")
    elif(media_sent is None):
        return (interrogator_prompt, f"A photo of it as it is now, for the {services}. How long it's been on is on file: {time_on}.")

    #the photo and how long its been on are both on file
    return ("", "")

#the photo prompt and the ask while the custom job has no photo on file, empty once it does
def media_missing(custom_service_info: dict[str, str], services: str) -> tuple[str, str]:
    media_sent: str | None = custom_service_info.get("media")

    if(media_sent is None):
        return (custom_photo.prompt(), f"A photo of the vehicle or of what they want for the {services}.")

    #the photo is on file
    return ("", "")

#the interrogator prompt and its one line ask, both empty when nothing is missing
def custom_missing(custom_service_info: dict[str, str], services: str, removal: bool) -> tuple[str, str]:
    if(removal):
        return removal_missing(custom_service_info, services)

    return media_missing(custom_service_info, services)

#flashx writes the photo and removal asks, and they go out as written
def custom_interrogate(user_text: str, interrogator_prompt: str, info_needed: str) -> str:
    interrogator_text: str = f"{user_text}\n INFO_NEEDED: {info_needed}"

    return models.generator("INTERROGATOR", interrogator_prompt, interrogator_text, CUSTOM_MAX_TOKENS, CUSTOM_INTERROGATOR_EFFORT, line_breaks=False)

#the reply, and whether a person takes over, which happens once the price has all it needs
def custom_reply(state: dict, id: str) -> tuple:
    #a custom job has no general code
    custom_details: dict[str, dict] = models.analyzer(custom_analyzer_questions(), state, CUSTOM_DETAILS, None, ANALYZER_THRESHOLD)

    state_as_text: str = state_form.state_to_text(state)

    details: str = details_text(custom_details, None)

    user_text: str = f"CUSTOM_SERVICE_DETAILS: {details}\n STATE: {state_as_text}"

    commercial_wrap: bool = "c1" in custom_details

    #c3 or c6 removal, a commercial wraps own details already cover taking old decals off
    removal: bool = not commercial_wrap and ("c3" in custom_details or "c6" in custom_details)

    #what a commercial wrap had on file before this message, so what they just gave shows
    info_before: dict[str, str] = {}

    if(commercial_wrap):
        info_before = log.read_info(f"custom_service_{id}")

    field_names: list[str] = custom_extract_and_save(id, user_text, commercial_wrap, removal)

    services: str = custom_services(custom_details)

    custom_service_info: dict[str, str] = log.read_info(f"custom_service_{id}")

    #the first reply holds prices unless they asked one, the extractors above never see the hold
    held: bool = price_held(state)

    reply_text: str = held_text(user_text, held)

    if(commercial_wrap):
        custom_return: tuple = commercial_wrap_reply(state, id, reply_text, services, info_before, custom_service_info, field_names, held)
    else:
        missing: tuple[str, str] = custom_missing(custom_service_info, services, removal)

        interrogator_prompt: str = missing[0]

        info_needed: str = missing[1]

        #the price has all it needs, so the ack goes out and a person takes it from here
        if(info_needed == ""):
            custom_return = (custom_ack_reply(state, reply_text, custom_service_info, field_names), True)
        else:
            custom_return = (custom_interrogate(reply_text, interrogator_prompt, info_needed), False)

    #a price that got past the hold never goes out on the shops first reply
    return (held_price_cut(custom_return[0], held, id), custom_return[1])


#PRICE TOTALS

#the dollar amount in one extracted price, None if never quoted or not in the shops format
def price_amount(price: str):
    price_text: str = price.strip().lower()

    #the extractor writes every price as a dollar amount plus tax, anything else has no amount
    if(not price_text.startswith("$") or not price_text.endswith(" plus tax")):
        return None

    amount_text: str = price_text[len("$"):-len(" plus tax")].replace(",", "").strip()

    try:
        amount = Decimal(amount_text)
    except InvalidOperation:
        return None

    #a real quote is never negative, nan or infinite
    if(not amount.is_finite() or amount < 0):
        return None

    return amount

#every extracted price added up, None when nothing came up yet or one service was never quoted
def services_amount(services_pricing: dict[str, str]):
    if(len(services_pricing) == 0):
        return None

    total = Decimal(0)

    for price in services_pricing.values():
        amount = price_amount(price)

        if(amount is None):
            return None

        total += amount

    return total

#an amount the way the shop writes a price, cents only when there are some
def dollar_text(amount) -> str:
    if(amount == amount.to_integral_value()):
        return f"${int(amount)}"

    return f"${amount:.2f}"

#the total of every service they want, shop style, empty when it can't be added up
def services_total(services_pricing: dict[str, str]) -> str:
    total = services_amount(services_pricing)

    if(total is None):
        return ""

    return f"{dollar_text(total)} plus tax"

#the twenty percent deposit to the cent, None when theres no total
def deposit_amount(services_pricing: dict[str, str]):
    total = services_amount(services_pricing)

    if(total is None):
        return None

    #a fifth of the total, to the cent the way the invoice charges it
    return (total * DEPOSIT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

#the deposit written like the shop writes a price, empty when theres no total
def services_deposit(services_pricing: dict[str, str]) -> str:
    deposit = deposit_amount(services_pricing)

    if(deposit is None):
        return ""

    return dollar_text(deposit)

#the prices for every service they want, a price quoted in reply_before counts too
def extract_services_pricing(state: dict, reply_before: str) -> dict[str, str]:
    state_as_text: str = state_form.state_to_text(state)

    extractor_output: str = models.extract_services(f"REPLY_BEFORE: {reply_before}\n STATE: {state_as_text}")

    #service to its quoted price, for every service they want
    services_pricing: dict[str, str] = {}

    #extractor chatter is never used, so nothing gets booked off it
    try:
        services_pricing = models.services_pricing_values(extractor_output)
    except Exception as error:
        print(f"S_P EXTRACTOR ERROR: {error}")

    print(f"SERVICES PRICING: {services_pricing}")

    return services_pricing


#BOOKING DATES

#open drop off days in the next 3 weeks for the job on file, written like Monday, October 12
def pull_open_dates(state: dict, id: str) -> list[str]:
    #the job they want, saved when the open days first went out for it
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    #nothing on file, so no day can fit the job and the ack goes out for a person to find one
    if(len(confirmed_services) == 0):
        print("BOOKING DATE ERROR: no booked services on file, so no drop off day can be found")

    service_names: list[str] = list(confirmed_services.keys())

    shop_today = datetime.strptime(state["current_date_time"], state_form.CURRENT_DATE_TIME_FORMAT).date()

    calendar_window: tuple = open_dates.calendar_window(shop_today)

    events: list[dict] = google_calendar.read_events(calendar_window[0], calendar_window[1])

    #every open day in the next 3 weeks, soonest first
    open_days: list = open_dates.open_drop_off_dates(service_names, events, shop_today)

    #written like Monday, October 12, so the generator says it the way the owner texts it
    open_date_texts: list[str] = []

    for open_day in open_days:
        open_date_texts.append(f"{open_day.strftime('%A, %B')} {open_day.day}")

    print(f"OPEN DATES: {open_date_texts}")

    return open_date_texts

#the ack for when no day works, with the days they passed on, empty when none were open
def booking_date_ack_reply(state: dict, open_date_texts: list[str], reply_before: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    dates_text: str = json.dumps(open_date_texts)

    #reply_before goes out right before this, empty when the ack has to answer them itself
    ack_text: str = f"OPEN_DATES: {dates_text}\n REPLY_BEFORE: {reply_before}\n STATE: {state_as_text}"

    system_prompt: str = booking_date_ack.prompt()

    return models.generator("DATE ACK GENERATOR", system_prompt, ack_text, BOOKING_DATE_MAX_TOKENS, BOOKING_DATE_EFFORT, line_breaks=False)

#the reply offering the open drop off days, with the jobs total and deposit worked out here
def date_propose_reply(state: dict, open_date_texts: list[str], turned_down_texts: list[str], id: str, reply_before: str) -> str:
    #the job the days go out for, saved when they first went out for it
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    #math done here, never by the generator, so what they're quoted is what the invoice charges
    total: str = services_total(confirmed_services)

    deposit: str = services_deposit(confirmed_services)

    print(f"SERVICES TOTAL: {total} | DEPOSIT: {deposit}")

    state_as_text: str = state_form.state_to_text(state)

    dates_text: str = json.dumps(open_date_texts)

    #days they just turned down, empty on the first offer
    turned_down_text: str = json.dumps(turned_down_texts)

    pricing_text: str = json.dumps(confirmed_services, ensure_ascii=False)

    #total and deposit are empty if a service never got quoted, reply_before if nothing goes first
    propose_text: str = f"OPEN_DATES: {dates_text}\n TURNED_DOWN: {turned_down_text}\n SERVICES_PRICING: {pricing_text}\n TOTAL: {total}\n DEPOSIT: {deposit}\n REPLY_BEFORE: {reply_before}\n STATE: {state_as_text}"

    system_prompt: str = booking_date_propose.prompt()

    return models.generator("DATE PROPOSE GENERATOR", system_prompt, propose_text, BOOKING_DATE_MAX_TOKENS, BOOKING_DATE_EFFORT, line_breaks=False)

#offers the soonest open days, or the ack when nothings open, plus the days that went out
def booking_date_reply(state: dict, id: str, reply_before: str) -> tuple:
    open_date_texts: list[str] = pull_open_dates(state, id)[:open_dates.DATES_TO_PROPOSE]

    response: str = ""

    #nothing open in the next 3 weeks, so the ack says a person finds them a day
    if(len(open_date_texts) == 0):
        response = booking_date_ack_reply(state, open_date_texts, reply_before)
    else:
        #the open days go out, after answering anything they asked along with their yes
        response = date_propose_reply(state, open_date_texts, [], id, reply_before)

    return (response, open_date_texts)

#the open days they asked for by name, in calendar order
def asked_open_dates(state: dict, open_date_texts: list[str]) -> list[str]:
    #one yes or no per open day, so an asked day is found anywhere in the next 3 weeks
    asked_questions: dict[str, dict] = {}

    for date_number, open_date_text in enumerate(open_date_texts, start=1):
        question: str = f"Does the customer ask to drop the vehicle off on {open_date_text} in `current_user_message`?"

        asked_rules: str = booking_date_instructions.instructions("asked_date")

        examples: str = booking_date_examples.asked_date_analyze_examples()

        asked_questions[f"date_{date_number}"] = {"type": "noul", "instructions": f"{question}\n{asked_rules}\n{examples}"}

    classified: tuple[list[str], dict[str, float]] = models.classifier(asked_questions, state, ASKED_DATE_THRESHOLD)

    asked_codes: list[str] = classified[0]

    probabilities: dict[str, float] = classified[1]

    asked_date_texts: list[str] = []

    #each asked day with its chance next to it, for the terminal only
    asked_date_labels: list[str] = []

    for date_number, open_date_text in enumerate(open_date_texts, start=1):
        date_code: str = f"date_{date_number}"

        if(date_code in asked_codes):
            asked_date_texts.append(open_date_text)

            asked_date_labels.append(f"{open_date_text}({probabilities[date_code]:.2f})")

    print(f"ASKED DATES: {asked_date_labels}")

    return asked_date_texts

#a fresh set of open days after they turned the last ones down, with the reply offering them
def booking_date_research(state: dict, id: str, turned_down_texts: list[str], last_offered_texts: list[str]) -> tuple:
    #the calendar gets read again, so days that filled up drop out and new openings can go
    open_date_texts: list[str] = pull_open_dates(state, id)

    research_date_texts: list[str] = []

    #a day they asked for thats open goes out, even one they turned down before
    if(len(open_date_texts) > 0):
        research_date_texts = asked_open_dates(state, open_date_texts)[:open_dates.DATES_TO_PROPOSE]

    #otherwise the next open days they haven't turned down, soonest first
    if(len(research_date_texts) == 0):
        for open_date_text in open_date_texts:
            if(open_date_text not in turned_down_texts):
                research_date_texts.append(open_date_text)

            if(len(research_date_texts) == open_dates.DATES_TO_PROPOSE):
                break

    print(f"RESEARCH DATES: {research_date_texts}")

    #every open day in the next 3 weeks was turned down already, so nothing goes out from here
    if(len(research_date_texts) == 0):
        return ("", research_date_texts)

    #the days they just turned down go in too, so the reply offers these as other days
    response: str = date_propose_reply(state, research_date_texts, last_offered_texts, id, "")

    return (response, research_date_texts)


#DATE ANSWERS

#whether they picked an offered day, said yes to the job without a day, or neither
def date_agree_analyzer(state: dict) -> str:
    agree_criteria: dict[str, str] = {}

    agree_criteria["agree_date"] = booking_date_instructions.instructions("agree_date")

    agree_criteria["agree_job"] = booking_date_instructions.instructions("agree_job")

    agree_criteria["not_agree"] = booking_date_instructions.instructions("not_agree")

    question_text: str = booking_date_instructions.date_agree_instructions()

    examples: str = booking_date_examples.agree_date_analyze_examples()

    agree_question: dict = {"type": "choice", "instructions": f"{question_text}\n{examples}", "criteria": agree_criteria}

    agree_answer: dict = models.decision_answer("agree_date", agree_question, state)

    category: str = agree_answer["choice"]

    category_probability: float = agree_answer["probabilities"][category]

    print(f"DATE AGREE ANALYZER: {category}({category_probability:.2f})")

    return category

#there answer when it picks no day, none work, the job or price is off, nevermind, or a question
def date_not_agree_analyzer(state: dict) -> str:
    not_agree_criteria: dict[str, str] = {}

    not_agree_criteria["not_agree_date"] = booking_date_instructions.instructions("not_agree_date")

    not_agree_criteria["not_agree_pricing"] = booking_date_instructions.instructions("not_agree_pricing")

    not_agree_criteria["nevermind"] = booking_date_instructions.instructions("nevermind")

    not_agree_criteria["service_pricing"] = booking_date_instructions.instructions("service_pricing")

    not_agree_criteria["business_operations"] = booking_date_instructions.instructions("business_operations")

    question_text: str = booking_date_instructions.date_not_agree_instructions()

    examples: str = booking_date_examples.not_agree_date_analyze_examples()

    not_agree_question: dict = {"type": "choice", "instructions": f"{question_text}\n{examples}", "criteria": not_agree_criteria}

    not_agree_answer: dict = models.decision_answer("not_agree_date", not_agree_question, state)

    category: str = not_agree_answer["choice"]

    category_probability: float = not_agree_answer["probabilities"][category]

    print(f"DATE NOT_AGREE ANALYZER: {category}({category_probability:.2f})")

    return category

#the offered day they picked
def picked_date(state: dict, offered_dates: list[str]) -> str:
    #with one day offered, their yes is to that day
    if(len(offered_dates) == 1):
        return offered_dates[0]

    #one choice per offered day, numbered the way the pending flag kept them
    picked_criteria: dict[str, str] = {}

    for date_number, offered_date in enumerate(offered_dates, start=1):
        picked_criteria[f"date_{date_number}"] = f"The customer picks {offered_date} to drop the vehicle off."

    question_text: str = booking_date_instructions.picked_date_instructions()

    examples: str = booking_date_examples.picked_date_analyze_examples()

    picked_question: dict = {"type": "choice", "instructions": f"{question_text}\n{examples}", "criteria": picked_criteria}

    picked_answer: dict = models.decision_answer("picked_date", picked_question, state)

    category: str = picked_answer["choice"]

    picked: str = offered_dates[int(category.removeprefix("date_")) - 1]

    picked_probability: float = picked_answer["probabilities"][category]

    print(f"PICKED DATE: {picked}({picked_probability:.2f})")

    return picked


#DROP OFF

#a day of the month with its st, nd, rd or th
def day_ordinal(day: int) -> str:
    #the 11th, 12th and 13th go by th like the rest of the teens
    if(day % 100 in (11, 12, 13)):
        return f"{day}th"

    suffixes: dict[int, str] = {1: "st", 2: "nd", 3: "rd"}

    return f"{day}{suffixes.get(day % 10, 'th')}"

#offered days have no year, so the picked one gets whichever year is closest to today
def picked_day(drop_off_date: str, shop_today):
    date_parts: list[str] = drop_off_date.split(", ", 1)

    month_day: list[str] = date_parts[1].split(" ")

    month_number: int = datetime.strptime(month_day[0], "%B").month

    picked = date(shop_today.year, month_number, int(month_day[1]))

    #a January day offered in December is next years, one that just went by is still this years
    if((shop_today - picked).days > HALF_YEAR_DAYS):
        picked = picked.replace(year=shop_today.year + 1)

    return picked

#the picked day the way the owner says it, just the weekday if thats clear, else with the date
def drop_off_day_text(drop_off_date: str, offered_dates: list[str], current_date_time: str) -> str:
    shop_today = datetime.strptime(current_date_time, state_form.CURRENT_DATE_TIME_FORMAT).date()

    #every offered day is written like Thursday, October 29, with no year
    date_parts: list[str] = drop_off_date.split(", ", 1)

    weekday: str = date_parts[0]

    month_day: list[str] = date_parts[1].split(" ")

    month_text: str = month_day[0]

    picked = picked_day(drop_off_date, shop_today)

    #two offered days on the same weekday, like Friday the 23rd and the 30th, need the date
    same_weekday_offered: bool = False

    for offered in offered_dates:
        if(offered != drop_off_date and offered.startswith(f"{weekday},")):
            same_weekday_offered = True

            break

    days_out: int = (picked - shop_today).days

    #the coming one, with no other day offered on that weekday
    if(0 < days_out < WEEKDAY_ONLY_DAYS and not same_weekday_offered):
        return weekday

    if(picked.month == shop_today.month):
        return f"{weekday} the {day_ordinal(picked.day)}"

    #its month too when it isn't this month, like Tuesday, November 3rd
    return f"{weekday}, {month_text} {day_ordinal(picked.day)}"

#midnight shop time a few days after drop off, when what they booked comes off file
def booked_clear_time(drop_off_date: str, current_date_time: str):
    shop_today = datetime.strptime(current_date_time, state_form.CURRENT_DATE_TIME_FORMAT).date()

    clear_day = picked_day(drop_off_date, shop_today) + timedelta(days=BOOKED_KEEP_DAYS)

    return datetime.combine(clear_day, time(0, 0), open_dates.SHOP_TIMEZONE)


#CONTACT

#the name and the number out of their message, each one empty when they didn't give it
def contact_values(state: dict) -> dict[str, str]:
    user_text: str = state["current_user_message"].get("user_text", "")

    #the shops last reply goes with it, so a bare Danny answering it reads as there name
    shop_last_reply: str = spacing.last_sent_reply(state["message_history"])

    extractor_output: str = models.extract_contact(user_text, shop_last_reply)

    contact: dict[str, str] = {"name": "", "number": ""}

    try:
        values: list[str] = models.extractor_values(extractor_output, ["name", "number"])

        for field_name, value in zip(["name", "number"], values):
            contact[field_name] = value
    except Exception as error:
        #extractor chatter saves nothing, the next reply still asks for what isn't on file
        print(f"CONTACT EXTRACTOR ERROR: {error}")

    return contact

#asks for there contact info, offered_dates is empty when asking again without the day
def contact_ask_reply(state: dict, id: str, drop_off_date: str, offered_dates: list[str], missing: list[str], reply_before: str) -> str:
    #the services they confirmed by picking the day, saved when the days went out for them
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    state_as_text: str = state_form.state_to_text(state)

    #the days wording is worked out here, never by the generator, so it confirms the right day
    drop_off_day: str = drop_off_day_text(drop_off_date, offered_dates, state["current_date_time"])

    #all three are missing on the first ask
    missing_text: str = json.dumps(missing)

    pricing_text: str = json.dumps(confirmed_services, ensure_ascii=False)

    total: str = services_total(confirmed_services)

    deposit: str = services_deposit(confirmed_services)

    #reply_before is a branchs answer going out first when they asked something instead
    ask_text: str = f"DROP_OFF_DATE: {drop_off_date}\n DROP_OFF_DAY: {drop_off_day}\n MISSING: {missing_text}\n SERVICES_PRICING: {pricing_text}\n TOTAL: {total}\n DEPOSIT: {deposit}\n REPLY_BEFORE: {reply_before}\n STATE: {state_as_text}"

    system_prompt: str = contact_ask.prompt()

    return models.generator("CONTACT ASK GENERATOR", system_prompt, ask_text, CONTACT_MAX_TOKENS, CONTACT_EFFORT, line_breaks=False)

#the reply that takes in their name, number and email once the drop off day is set
def contact_ack_reply(state: dict, drop_off_date: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    ack_text: str = f"DROP_OFF_DATE: {drop_off_date}\n STATE: {state_as_text}"

    system_prompt: str = contact_ack.prompt()

    return models.generator("CONTACT ACK GENERATOR", system_prompt, ack_text, CONTACT_MAX_TOKENS, CONTACT_EFFORT, line_breaks=False)

#whether their message gave any of there name, number or email for the invoice
def contact_analyzer(state: dict) -> str:
    contact_criteria: dict[str, str] = {}

    contact_criteria["contact_info"] = contact_instructions.instructions("contact_info")

    contact_criteria["no_contact_info"] = contact_instructions.instructions("no_contact_info")

    question_text: str = contact_instructions.contact_question_instructions()

    examples: str = contact_examples.contact_analyze_examples()

    contact_question: dict = {"type": "choice", "instructions": f"{question_text}\n{examples}", "criteria": contact_criteria}

    contact_answer: dict = models.decision_answer("contact", contact_question, state)

    category: str = contact_answer["choice"]

    category_probability: float = contact_answer["probabilities"][category]

    print(f"CONTACT ANALYZER: {category}({category_probability:.2f})")

    return category

#what a message with none of there info is, won't give it, getting it, a question, or spam
def no_contact_analyzer(state: dict) -> str:
    no_contact_criteria: dict[str, str] = {}

    no_contact_criteria["wont_give_info"] = contact_instructions.instructions("wont_give_info")

    no_contact_criteria["getting_info"] = contact_instructions.instructions("getting_info")

    no_contact_criteria["service_pricing"] = contact_instructions.instructions("service_pricing")

    no_contact_criteria["business_operations"] = contact_instructions.instructions("business_operations")

    no_contact_criteria["spam_harass"] = contact_instructions.instructions("spam_harass")

    question_text: str = contact_instructions.no_contact_question_instructions()

    examples: str = contact_examples.no_contact_analyze_examples()

    no_contact_question: dict = {"type": "choice", "instructions": f"{question_text}\n{examples}", "criteria": no_contact_criteria}

    no_contact_answer: dict = models.decision_answer("no_contact", no_contact_question, state)

    category: str = no_contact_answer["choice"]

    category_probability: float = no_contact_answer["probabilities"][category]

    print(f"CONTACT NO_CONTACT ANALYZER: {category}({category_probability:.2f})")

    return category

#the reply to a message with none of there info, written for the case it is
def no_contact_ack_reply(state: dict, case: str, drop_off_date: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    ack_text: str = f"CASE: {case}\n DROP_OFF_DATE: {drop_off_date}\n STATE: {state_as_text}"

    system_prompt: str = contact_no_info.prompt()

    return models.generator("CONTACT NO INFO GENERATOR", system_prompt, ack_text, CONTACT_MAX_TOKENS, CONTACT_EFFORT, line_breaks=False)


#OTHER REPLIES

#problems and person only asks get a quick ack, then True hands them to a person
def escalation_reply(state: dict, id: str) -> tuple:
    state_as_text: str = state_form.state_to_text(state)

    #it only acknowledges, so no details needed
    escalation_text: str = f"STATE: {state_as_text}"

    system_prompt: str = escalation_generator.prompt()

    response: str = models.generator("ESCALATION GENERATOR", system_prompt, escalation_text, ESCALATION_MAX_TOKENS, ESCALATION_EFFORT, line_breaks=False)

    regen_prompt: str = escalation_regenerator.prompt()

    reply: str = enforced_reply(state, id, escalation_text, response, "ESCALATION REGEN", regen_prompt, models.generator, ESCALATION_REGEN_MAX_TOKENS, ESCALATION_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)

    #never the systems call, so a person takes it from here
    return (reply, True)

#small talk gets answered and nudged back to what they need
def general_text_reply(state: dict, id: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #small talk needs no lookups, anything shop related is already in its prompt
    general_text: str = f"STATE: {state_as_text}"

    system_prompt: str = general_text_generator.prompt()

    response: str = models.generator("GENERAL TEXT GENERATOR", system_prompt, general_text, GENERAL_TEXT_MAX_TOKENS, GENERAL_TEXT_EFFORT, line_breaks=False)

    regen_prompt: str = general_text_regenerator.prompt()

    #small talk loved sneaking in a schedule ask, so it goes through the enforcers now too
    return enforced_reply(state, id, general_text, response, "GENERAL TEXT REGEN", regen_prompt, models.generator, GENERAL_TEXT_REGEN_MAX_TOKENS, GENERAL_TEXT_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)

#a person has them, so they hear whats still in the works instead of getting left on read
def hold_reply(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #whats in the works comes from our last replies, the shops info is already in its prompt
    hold_text: str = f"STATE: {state_as_text}"

    system_prompt: str = restricted_hold.prompt()

    return models.generator("HOLD GENERATOR", system_prompt, hold_text, HOLD_MAX_TOKENS, HOLD_EFFORT, line_breaks=False)

#they want a call, so they get the shops number and True hands them to a person
def phone_call_reply(state: dict) -> tuple:
    state_as_text: str = state_form.state_to_text(state)

    #the number and the hours to call in come from the business details in its prompt
    phone_call_text: str = f"STATE: {state_as_text}"

    system_prompt: str = phone_call_ack.prompt()

    response: str = models.generator("PHONE CALL GENERATOR", system_prompt, phone_call_text, PHONE_CALL_MAX_TOKENS, PHONE_CALL_EFFORT, line_breaks=False)

    return (response, True)

#they're wrapping up, so the door stays open with no question left hanging for them
def end_conversation_reply(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #they asked nothing, so no lookups, the shops info is already in its prompt
    end_text: str = f"STATE: {state_as_text}"

    system_prompt: str = end_conversation_ack.prompt()

    return models.generator("END CONVERSATION GENERATOR", system_prompt, end_text, END_CONVERSATION_MAX_TOKENS, END_CONVERSATION_EFFORT, line_breaks=False)

#the reply when they call off getting on the books for now, leaving the door open
def pricing_confirm_ack_reply(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    ack_text: str = f"STATE: {state_as_text}"

    system_prompt: str = pricing_confirm_ack.prompt()

    return models.generator("CONFIRM ACK GENERATOR", system_prompt, ack_text, PRICING_CONFIRM_MAX_TOKENS, PRICING_CONFIRM_EFFORT, line_breaks=False)


#COLOR NEWS

#the reply with the good news worked in, or just the good news when open days follow it
def color_approved_reply(state: dict, reply: str, days_after: bool) -> str:
    state_as_text: str = state_form.state_to_text(state)

    days_text: str = "no"

    if(days_after):
        days_text = "yes"

    #the chat names their color and job, so the good news says both the way they would
    color_approved_text: str = f"REPLY: {reply}\n DAYS_AFTER: {days_text}\n STATE: {state_as_text}"

    system_prompt: str = color_approved_generator.prompt()

    #the reply can come in parts, so a line break in what comes back is its own
    return models.generator("COLOR APPROVED GENERATOR", system_prompt, color_approved_text, COLOR_APPROVED_MAX_TOKENS, COLOR_APPROVED_EFFORT, line_breaks=True)

#the pick rule for one material, and when its the only one a plain yes picks it too
def material_criterion(position: int, material: dict[str, str], count: int) -> str:
    name: str = material.get("name", "")

    if(not name):
        name = "its color not read"

    description: str = material.get("description", "").replace("\n", "; ")

    if(count == 1):
        return f"The customer goes with material 1, {name}, the only pic the shop sent, which shows {description}. The shop asked if that one works for them, so any yes to it picks it: a yes, a bare 'yeah', 'yep' or 'ok' included, 'that works', 'sure', saying they like it ('I like it', 'looks clean'), saying to go ahead with it or do it, a yes to the shop making sure it's the one, or pointing to it ('#1', '1', 'that one'), even when it asks something too, about the wrap or colored PPF itself included"

    ordinal: str = day_ordinal(position)

    return f"The customer picks material {position}, {name}, the {ordinal} pic the shop sent ('#{position}', '{position}', 'the {ordinal} one'), which shows {description}"

#an ok only says nothing when more than one was sent, with one its a yes to it
def other_criterion(count: int) -> str:
    if(count == 1):
        return "The customer neither says yes to the material the shop sent nor turns it down: a question with no yes in it, a maybe, still deciding, a thanks, or anything else. A yes, an ok, saying they like it or going ahead with it is never other, even when it asks something too."

    return "The customer neither picks one of the materials nor turns them all down: a question with no pick in it, a maybe, still deciding, asking which one the shop would go with, a thanks or an ok, or anything else. A message that points to one of them, by its number or where it is in the order ('#1', '2', 'the last one') or by its color or finish, is never other, even when it asks something too."

#which closest material they picked, none or other if they didn't, and if they asked more
def material_pick(state: dict, materials: list[dict[str, str]]) -> tuple[str, bool]:
    #one choice per material, numbered in the order the owner sent them, like there history
    pick_criteria: dict[str, str] = {}

    for position, material in enumerate(materials, start=1):
        pick_criteria[f"{MATERIAL_PICK_PREFIX}{position}"] = material_criterion(position, material, len(materials))

    pick_criteria[NO_PICK] = "The customer doesn't want any of the materials the shop sent: none of them work for them, they don't like them, they want a different color than all of them, or none of them are close enough."

    pick_criteria[OTHER_PICK] = other_criterion(len(materials))

    pick_text: str = color_materials_examples.material_pick_instructions()

    pick_examples: str = color_materials_examples.material_pick_examples()

    pick_question: dict = {"type": "choice", "instructions": f"{pick_text}\n{pick_examples}", "criteria": pick_criteria}

    asks_text: str = color_materials_examples.material_asks_instructions()

    asks_examples: str = color_materials_examples.material_asks_examples()

    asks_question: dict = {"type": "noul", "instructions": f"{asks_text}\n{asks_examples}"}

    questions: dict[str, dict] = {"material_pick": pick_question, "material_asks": asks_question}

    answers: dict = models.decision_answers(questions, state)

    choice: str = answers["material_pick"]["choice"]

    pick_probability: float = answers["material_pick"]["probabilities"][choice]

    asks_probability: float = answers["material_asks"]["noul"]

    asks_more: bool = asks_probability > MATERIAL_ASKS_THRESHOLD

    print(f"MATERIAL PICK: {choice}({pick_probability:.2f}) | ASKS MORE: {asks_probability:.2f}")

    return (choice, asks_more)

#takes in their pick, reply is what else they asked or empty, picked is the materials color
def color_picked_reply(state: dict, id: str, reply: str, picked: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #comes back with the pick taken in and the schedule question for the job
    color_picked_text: str = f"REPLY: {reply}\n PICKED: {picked}\n STATE: {state_as_text}"

    system_prompt: str = color_picked_generator.prompt()

    #can come in parts, so a line break in here is on purpose
    response: str = models.generator("COLOR PICKED GENERATOR", system_prompt, color_picked_text, COLOR_PICKED_MAX_TOKENS, COLOR_PICKED_EFFORT, line_breaks=True)

    #the regen reads our last reply on its own, so an answer it gave never goes out twice
    shop_last_reply: str = spacing.last_sent_reply(state["message_history"])

    regen_prompt: str = color_picked_regenerator.prompt()

    return enforced_reply(state, id, color_picked_text, response, "COLOR PICKED REGEN", regen_prompt, models.generator, COLOR_PICKED_REGEN_MAX_TOKENS, COLOR_PICKED_REGEN_EFFORT, line_breaks=True, shop_last_reply=shop_last_reply)
