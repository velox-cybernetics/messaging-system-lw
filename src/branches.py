#**********IMPORTS**********
#the reply and decision models, the conversation's saved info, the calendar and every prompt
import json
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import TypeAlias

from helpers.models import models
from helpers.state import log
from helpers.state import owner
from helpers.response import greeting
from helpers.response import spacing
from helpers.response import repeats
from helpers.state import state_form
from helpers.calendar import google_calendar
from helpers.calendar import open_dates
from src.prompts.router import instructions as router_instructions
from src.prompts.router import examples as router_examples
from src.prompts.pricing import analyzer_examples as pricing_examples
from src.prompts.pricing import checker_instructions as pricing_checker
from src.prompts.pricing import generator as pricing_generator
from src.prompts.pricing import enforcer as pricing_enforcer
from src.prompts.pricing import regenerator as pricing_regenerator
from src.prompts.pricing.lack_info import generator as pricing_lack_info_generator
from src.prompts.pricing.lack_info import enforcer as pricing_lack_info_enforcer
from src.prompts.pricing.lack_info import regenerator as pricing_lack_info_regenerator
from src.prompts.pricing.interrogator import vehicle
from src.prompts.pricing.interrogator import vehicle_color
from src.prompts.pricing.interrogator import which_route
from src.prompts.pricing.interrogator import color_now
from src.prompts.pricing.interrogator import exact_color
from src.prompts.pricing.interrogator import color_checking
from src.prompts.pricing.interrogator import closest_materials
from src.prompts.pricing.interrogator import enforcer as interrogator_enforcer
from src.prompts.pricing.interrogator import regenerator as interrogator_regenerator
from src.prompts.business import analyzer_examples as business_examples
from src.prompts.business import checker_instructions as business_checker
from src.prompts.business import generator as business_generator
from src.prompts.business import enforcer as business_enforcer
from src.prompts.business import regenerator as business_regenerator
from src.prompts.business.lack_info import generator as business_lack_info_generator
from src.prompts.business.lack_info import enforcer as business_lack_info_enforcer
from src.prompts.business.lack_info import regenerator as business_lack_info_regenerator
from src.prompts.custom import analyzer_examples as custom_examples
from src.prompts.custom.interrogator import wrap_type as custom_wrap_type
from src.prompts.custom.interrogator import vehicle_count as custom_vehicle_count
from src.prompts.custom.interrogator import make_model as custom_make_model
from src.prompts.custom.interrogator import vehicle_model as custom_vehicle_model
from src.prompts.custom.interrogator import logo_file as custom_logo_file
from src.prompts.custom.interrogator import photo as custom_photo
from src.prompts.custom.interrogator import removal as custom_removal
from src.prompts.custom.interrogator import commercial_enforcer
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
from src.prompts.escalation import enforcer as escalation_enforcer
from src.prompts.escalation import regenerator as escalation_regenerator
from src.prompts.general_text import generator as general_text_generator
from src.prompts.phone_call import ack as phone_call_ack
from src.prompts.end_conversation import ack as end_conversation_ack
from src.prompts.end_conversation import analyzer_examples as end_conversation_examples
from src.prompts.color_approved import generator as color_approved_generator
from src.prompts.color_materials import analyzer_examples as color_materials_examples
from src.prompts.color_materials.picked import generator as color_picked_generator
from src.prompts.color_materials.picked import enforcer as color_picked_enforcer
from src.prompts.color_materials.picked import regenerator as color_picked_regenerator
from src.prompts.restricted import analyzer_examples as restricted_examples
from src.prompts.restricted import hold as restricted_hold



#**********DETAILS FILES**********
#the shop's service, business and custom job details, read from their files once when the bot starts


#READ DETAILS
#reads one of the shop's details files into a dict
def read_details(path: str) -> dict:
    with open(path, "r") as file:
        details: dict = json.load(file)

    return details


#DETAILS DICTS
PRICING_DETAILS: dict = read_details("details_json/service_pricing_details.json")

BUSINESS_DETAILS: dict = read_details("details_json/business_operations_details.json")

CUSTOM_DETAILS: dict = read_details("details_json/custom_service_details.json")



#**********ANALYZER CODES**********
#the codes the analyzers give the services, and which of them change the vehicle's color


#GENERAL CODES
#the code for a message about the services or the business in general, it carries every detail
PRICING_GENERAL_CODE: str = "s6"

BUSINESS_GENERAL_CODE: str = "b15"


#COLOR CODES
#a color change in vinyl, and colored PPF, the other way to change the color
COLOR_CHANGE_CODE: str = "s1"

COLORED_PPF_CODE: str = "s3"

#the services whose price needs the color it is now, a follow up that names no service keeps the ones on file
COLOR_CODES: list[str] = [COLOR_CHANGE_CODE, COLORED_PPF_CODE]

#clear PPF and a ceramic coating don't change the color, so in a pair with them the wrap is the only route
PPF_CODE: str = "s2"

CERAMIC_COATING_CODE: str = "s5"



#**********COLOR PICKS**********
#the two films that change the color, and how their pick of the closest materials reads


#COLOR ROUTES
#the film they pick is kept on file as the route, and the route comes before any color question
WRAP_ROUTE: str = "wrap"

COLORED_PPF_ROUTE: str = "colored_ppf"

COLOR_ROUTES: list[str] = [WRAP_ROUTE, COLORED_PPF_ROUTE]

#what the route decision answers when they haven't picked or named either film yet
UNDECIDED_ROUTE: str = "undecided"


#MATERIAL PICKS
#a pick reads as this prefix and where the material was in the owner's pics, counting from 1
MATERIAL_PICK_PREFIX: str = "material_"

#they don't want any of them
NO_PICK: str = "none"

#they neither picked one nor turned them all down
OTHER_PICK: str = "other"



#**********COLOR NOW**********
#how many asks for a pic of their vehicle it takes before a color they type stands in for one


#PIC ASKS
#after this many replies asked for a pic of their vehicle with none coming, the color it is now they type goes on file in its place
COLOR_PIC_ASK_LIMIT: int = 2

#a color it is now on file from their text is marked with this, since no pic's bright_vehicle says whether it's a bright color
TYPED_COLOR_SOURCE: str = "text"



#**********PRICE FIRST**********
#what the exact price waits on gets asked before the color they want, and the ask that goes out in place of one for that color too early


#PRICE NEEDS
#what the exact price still waits on from them, in the order it gets asked
VEHICLE_NEED: str = "vehicle"

ROUTE_NEED: str = "route"

COLOR_NOW_NEED: str = "color_now"


#PRICE ASKS
#the owner's first ask for each, then the ways he asks it again, so an ask the shop already sent goes out in new words
VEHICLE_COLOR_NOW_ASKS: list[str] = ["What car is it, and what color is it right now? Send me a pic if you can", "What are you driving, and what color's it at right now? Shoot me a quick pic of it when you get a sec", "Which car is it, and what color's it at the moment? Snap a pic of it and send it over whenever you get a chance"]

VEHICLE_ROUTE_ASKS: list[str] = ["What vehicle is it, and which route are you leaning towards?", "What are you driving, and are you leaning more towards the wrap or the colored PPF?"]

VEHICLE_ASKS: list[str] = ["What car is it?", "What are you driving?", "Which car is it?"]

ROUTE_ASKS: list[str] = ["Which route are you leaning towards?", "Are you leaning more towards the wrap or the colored PPF?"]

#{vehicle} is the model on file, or the make when only it is
COLOR_NOW_ASKS: list[str] = ["What color is the {vehicle} right now? Send me a pic if you can", "What color's the {vehicle} at right now? Shoot me a quick pic of it when you get a sec", "When you get a chance, can you snap a pic of the {vehicle} and send it over, that way I can see the exact color on it"]



#**********THRESHOLDS**********
#how sure each decision has to be before the bot goes with it


#ROUTING
#a route under this falls back to the branch its best guess points to (see torn_route)
ROUTE_THRESHOLD: float = 0.75

#a yes over this lets the bot answer a restricted customer, high on purpose since a wrong answer reaches them
RESTRICTED_THRESHOLD: float = 0.65

#a yes over this opens a conversation they wrapped up back up, low on purpose since leaving a real ask on read costs more than answering one more ok
REOPEN_THRESHOLD: float = 0.4


#ANALYZERS
#a yes over this means a service or question was asked about and its details get used, in every analyzer
ANALYZER_THRESHOLD: float = 0.75

#a yes over this holds the price for a pic, low on purpose since a held price costs less than one without the color
COLOR_JOB_THRESHOLD: float = 0.5

#a yes over this means they asked to book too, so the reply with the price ends on the schedule question
BOOKING_INTENT_THRESHOLD: float = 0.5

#a yes over this lets a price into the shop's first reply, over half since the owner never wants one there they didn't ask for
PRICE_QUESTION_THRESHOLD: float = 0.6

#a pick over this puts the route on file, high on purpose since a route on file never gets asked again
COLOR_ROUTE_THRESHOLD: float = 0.75


#REPLY CHECKS
#a yes over this means the details can't answer it, high on purpose since answered messages never pass 0.5
CHECKER_THRESHOLD: float = 0.76

#a yes over this means the reply broke a rule, high on purpose since clean pricing replies score up to about 0.74
ENFORCER_THRESHOLD: float = 0.7


#BOOKING DAYS
#a yes over this means they asked for that open day, so it goes out before the next ones not turned down
ASKED_DATE_THRESHOLD: float = 0.5


#MATERIAL ASKS
#a yes over this means they asked more with their pick, over half since a miss only waits for their next text
MATERIAL_ASKS_THRESHOLD: float = 0.6



#**********GENERATION LIMITS**********
#how long each reply can get and how hard its model thinks before it writes


#REGEN ATTEMPTS
#a flagged reply gets fixed at most this many times, each fix checked like the first reply before it can go out
REGEN_MAX_ATTEMPTS: int = 2


#PRICING LIMITS
#every pricing reply and rewrite gets these token limits, and flashx writes the lack info reply and its rewrite at high, one notch under max (glm-5.3-flashx takes max, high, medium or low), so they go out sooner
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


#BUSINESS LIMITS
BUSINESS_MAX_TOKENS: int = 10*100

BUSINESS_EFFORT: str = "high"

BUSINESS_REGEN_MAX_TOKENS: int = 10*100

BUSINESS_REGEN_EFFORT: str = "high"


#CUSTOM LIMITS
CUSTOM_MAX_TOKENS: int = 10*100

CUSTOM_EFFORT: str = "high"

CUSTOM_REGEN_MAX_TOKENS: int = 10*100

CUSTOM_REGEN_EFFORT: str = "high"

#flashx writes the commercial wrap interrogators and their rewrites at high
CUSTOM_COMMERCIAL_EFFORT: str = "high"

CUSTOM_COMMERCIAL_REGEN_EFFORT: str = "high"

#flashx writes the photo and removal interrogators at high too
CUSTOM_INTERROGATOR_EFFORT: str = "high"


#PRICING CONFIRM LIMITS
PRICING_CONFIRM_MAX_TOKENS: int = 10*100

PRICING_CONFIRM_EFFORT: str = "high"


#BOOKING DATE LIMITS
BOOKING_DATE_MAX_TOKENS: int = 10*100

#flashx writes the drop off day replies at high
BOOKING_DATE_EFFORT: str = "high"


#CONTACT LIMITS
CONTACT_MAX_TOKENS: int = 10*100

CONTACT_EFFORT: str = "high"


#ESCALATION LIMITS
ESCALATION_MAX_TOKENS: int = 10*100

ESCALATION_EFFORT: str = "high"

ESCALATION_REGEN_MAX_TOKENS: int = 10*100

ESCALATION_REGEN_EFFORT: str = "high"


#GENERAL TEXT LIMITS
GENERAL_TEXT_MAX_TOKENS: int = 10*100

GENERAL_TEXT_EFFORT: str = "high"


#HOLD LIMITS
HOLD_MAX_TOKENS: int = 10*100

HOLD_EFFORT: str = "high"


#PHONE CALL LIMITS
PHONE_CALL_MAX_TOKENS: int = 10*100

PHONE_CALL_EFFORT: str = "high"


#END CONVERSATION LIMITS
END_CONVERSATION_MAX_TOKENS: int = 10*100

END_CONVERSATION_EFFORT: str = "high"


#COLOR APPROVED LIMITS
COLOR_APPROVED_MAX_TOKENS: int = 10*100

COLOR_APPROVED_EFFORT: str = "high"


#COLOR PICKED LIMITS
COLOR_PICKED_MAX_TOKENS: int = 10*100

COLOR_PICKED_EFFORT: str = "high"

COLOR_PICKED_REGEN_MAX_TOKENS: int = 10*100

COLOR_PICKED_REGEN_EFFORT: str = "high"



#**********SHOP HOURS**********
#when the shop is open, so a price promised for later lands while it's open


#OPEN HOURS
#copied from the business details (Monday to Friday, 9AM to 5PM), so an hours change goes here too
SHOP_OPENS: time = time(9, 0)

#a price promised in about 30 minutes has to land before the shop closes at 5PM
PRICE_BACK_CUTOFF: time = time(16, 30)

#the last day of the week the shop is open, datetime counts Monday as 0 so Friday is 4
LAST_OPEN_WEEKDAY: int = 4



#**********COMMERCIAL ASKS**********
#what a commercial wrap's price still needs, and the words that show a question asks for it


#COMMERCIAL ASK
#one thing the price still needs: what it is, its interrogator prompt and the one line on what it asks for
COMMERCIAL_ASK: TypeAlias = tuple[str, Callable[[], str], str]


#GROUP FIELDS
#the fields on file each one fills, the make and model are one ask since they come in together
COMMERCIAL_GROUP_FIELDS: dict[str, list[str]] = {}

COMMERCIAL_GROUP_FIELDS["wrap_type"] = ["wrap_type"]

COMMERCIAL_GROUP_FIELDS["car_amount"] = ["car_amount"]

COMMERCIAL_GROUP_FIELDS["vehicles"] = ["makes", "models"]

COMMERCIAL_GROUP_FIELDS["vector_files"] = ["vector_files"]


#GROUP WORDS
#words a question asking for each one has, so one skipped for a later reply gets caught however it's reworded
COMMERCIAL_GROUP_WORDS: dict[str, list[str]] = {}

COMMERCIAL_GROUP_WORDS["wrap_type"] = ["full wrap", "half wrap", "partial wrap", "decal", "decals", "kind of wrap", "type of wrap", "what wrap", "which job", "leaning towards", "leaning toward"]

COMMERCIAL_GROUP_WORDS["car_amount"] = ["how many", "just the one", "the only one", "have more", "any more", "more you want"]

COMMERCIAL_GROUP_WORDS["vehicles"] = ["make", "makes", "model", "models", "what van", "what vans", "what truck", "what trucks", "what car", "what cars", "what vehicle", "what vehicles", "which van", "which vans", "which truck", "which trucks", "what kind of van", "what kind of vans", "what kind of truck", "what kind of trucks", "the other", "how big", "dimensions", "how long and tall"]

COMMERCIAL_GROUP_WORDS["vector_files"] = ["vector", "logo file", "logo files", "ai file", "eps", "svg", "pdf", "artwork", "print files", "logo that goes", "just the lettering"]



#**********INVOICE**********
#the deposit, and how the drop off day gets said in the replies about the invoice


#DEPOSIT RATE
#the deposit that locks in their spot is a fifth of what the services they confirmed come out to before tax
DEPOSIT_RATE: Decimal = Decimal("0.2")


#DAY WRITING
#a drop off day under this many days out is just its weekday ("Thursday"), further out it gets its date too
WEEKDAY_ONLY_DAYS: int = 7

#a drop off day is written with no year, so one more than this many days behind today is next year's
HALF_YEAR_DAYS: int = 182



#**********JUST BOOKED**********
#how long what they booked stays on file, so every reply till then knows they just booked


#BOOKED KEEP
#what they booked stays on file till this many days after its drop off day
BOOKED_KEEP_DAYS: int = 2



#**********CONTACT FIELDS**********
#what the owner needs from them to send the invoice for the deposit


#CONTACT FIELDS
#all three come in before the owner gets texted to send the estimate
CONTACT_FIELDS: list[str] = ["name", "number", "email"]

#a number they point to instead of typing it out comes out of the contact extractor as this, the one they text from
TEXTING_NUMBER: str = "texting"



#**********ROUTING**********
#decides which branch answers the customer's message, and where a torn decision goes


#TORN ROUTE
#the branch a route decision goes to when the router wasn't sure enough about its pick
def torn_route(category: str, probabilities: dict[str, float]) -> str:
    #torn, but its best guess is a branch that can take it on its own, so it goes there
    if(category in ["service_pricing", "business_operations", "services_req_humans", "escalation", "general_text", "phone_call", "end_conversation"]):
        return category

    #a booking only kicks off its confirm chain on a clear pick, so when torn its chance counts toward the service
    service_probability: float = probabilities["service_pricing"] + probabilities["booking_service_acknowledge"]

    if(service_probability >= ROUTE_THRESHOLD):
        return "service_pricing"

    #torn between the service and the shop, the pricing branch takes it since its replies carry the shop's info too
    if(probabilities["services_req_humans"] < min(service_probability, probabilities["business_operations"])):
        return "service_pricing"

    return "general_text"


#ROUTE
#the branch that answers it, with the model's chance for that branch
def pick_route(state: dict) -> tuple[str, float]:
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
        #a yes to the shop's schedule question with a question on it can land just under the cutoff, and the booking reply answers the question
        user_text: str = state["current_user_message"].get("user_text") or ""

        if(category == "booking_service_acknowledge" and spacing.yes_to_booking_question(user_text, state["message_history"])):
            print(f"ROUTE: a yes to the schedule question, torn at {confidence:.2f}, so it books")

            return (category, probabilities[category])

        torn: str = torn_route(category, probabilities)

        return (torn, probabilities[torn])

    return (category, probabilities[category])



#**********RESTRICTED ROUTING**********
#while a person has the conversation, the bot only answers what the details can answer on their own, and someone at the shop always hears to come on in


#RESTRICTED QUESTIONS
#the yes or no questions that decide whether a restricted customer's message is still the bot's to answer
def restricted_analyzer_questions() -> dict[str, dict]:
    questions: dict[str, dict] = {}

    questions["service_pricing"] = {"type": "noul", "instructions": f"Is the customer asking about one of the shop's regular services or what it costs in `current_user_message`, with nothing in it only a person at the shop can handle?\n{restricted_examples.service_pricing_examples()}"}

    questions["business_operations"] = {"type": "noul", "instructions": f"Is the customer asking about the shop itself in `current_user_message`, with nothing in it only a person at the shop can handle?\n{restricted_examples.business_operations_examples()}"}

    questions["at_shop"] = {"type": "noul", "instructions": f"Does the customer say in `current_user_message` that they're at the shop right now?\n{restricted_examples.at_shop_examples()}"}

    return questions


#RESTRICTED ROUTE
#the branch that answers it with the model's chance for it, restricted has none since no question picked it
def pick_restricted_route(state: dict) -> tuple[str, float | None]:
    #a person has the conversation, so the bot only answers what the service or business details can answer on their own
    classified: tuple[list[str], dict[str, float]] = models.classifier(restricted_analyzer_questions(), state, RESTRICTED_THRESHOLD)

    asked: list[str] = classified[0]

    probabilities: dict[str, float] = classified[1]

    print(f"RESTRICTED ANALYZER: {models.codes_with_probabilities(asked, probabilities)}")

    #a service question with a shop question in it goes to the pricing branch, its replies carry the shop's info too
    if("service_pricing" in asked):
        return ("service_pricing", probabilities["service_pricing"])

    if("business_operations" in asked):
        return ("business_operations", probabilities["business_operations"])

    #they're at the shop, so they always hear to come on in
    if("at_shop" in asked):
        return ("at_shop", probabilities["at_shop"])

    #anything else waits on a person
    return ("restricted", None)



#**********ENDED CONVERSATIONS**********
#once they wrap up for now and the shop takes it in, the bot leaves them be until they ask about something again, with nobody taking them over


#REOPENS
#True when their message asks about something again after they wrapped up, a closing ok, thanks or emoji never does
def reopens_conversation(state: dict) -> bool:
    reopen_question: dict = {"type": "noul", "instructions": f"Does the customer open the conversation back up in `current_user_message`, asking about something or bringing up something new for the shop to answer, after they wrapped it up for now?\n{end_conversation_examples.reopen_examples()}"}

    probability_yes: float = models.decision_answer("reopen", reopen_question, state)["noul"]

    print(f"CONVERSATION REOPENS: {probability_yes:.2f}")

    return probability_yes > REOPEN_THRESHOLD



#**********REPLY CHECKS**********
#lays out the details a reply is written from, writes the reply again when it broke a rule, and sees if their message has a pic


#DETAILS TEXT
#the analyzed details one json line each, the way the generators read them
def details_text(analyzed_details: dict[str, dict], general_code: str | None) -> str:
    #the general code has every detail sub-listed within it, so each one goes in once
    listed_details: dict[str, dict] = analyzed_details.get(general_code, analyzed_details)

    details: str = ""

    for detail in listed_details.values():
        details += f"{json.dumps(detail)}\n"

    return details


#ENFORCED REPLY
#shop_last_reply is None for a branch whose rules never check a line its last reply said going out again
#regen_generator writes the regens, the same generator its branch wrote the reply with
#held is True on the shop's first reply while it holds every price, where a reply with a $ in it always breaks the hold
def enforced_reply(state: dict, text: str, response: str, rules: str, regen_label: str, regen_prompt: str, regen_generator: Callable[..., str], max_tokens: int, effort: str, line_breaks: bool, shop_last_reply: str | None, held: bool = False) -> str:
    enforce_question: str = f"Is the systems response currenty going against any of the rules defined here\n{rules}\n?"

    #the flagged reply the enforcer was least sure breaks a rule, it goes out when every regen gets flagged too
    least_flagged_reply: str = response

    least_flagged_probability: float = 1.0

    #the reply gets checked, then each regen of the last flagged one gets checked the same way
    for attempt in range(REGEN_MAX_ATTEMPTS + 1):
        if(attempt > 0):
            #the regen gets the same text the reply was written from, with the flagged reply under it
            regen_text: str = f"{text}\n FLAGGED_RESPONSE: {response}"

            #and the last reply on its own, the same one the enforcer checked it against
            if(shop_last_reply is not None):
                regen_text = f"{text}\n SHOP_LAST_REPLY: {shop_last_reply}\n FLAGGED_RESPONSE: {response}"

            regen_response: str = regen_generator(regen_label, regen_prompt, regen_text, max_tokens, effort, line_breaks=line_breaks)

            #a regen that came back empty never goes out, the next one fixes the same flagged reply
            if(regen_response.strip() == ""):
                continue

            #the fixer changed nothing, so it found no rule broken and checking the same words again only flags them again
            if(regen_response.strip() == response.strip()):
                print(f"{regen_label} CAME BACK UNCHANGED")

                break

            response = regen_response

        broke_probability: float = 1.0

        #a price in a reply that holds every price is broken whatever the enforcer makes of it, so only a reply without one gets checked
        if(held and "$" in response):
            print("PRICE HOLD BROKEN: the reply gave a price on the shop's first reply")

        else:
            broke_probability = models.enforcer(enforce_question, state, response, shop_last_reply)

        broke_rule: bool = broke_probability > ENFORCER_THRESHOLD

        print(f"ENFORCER: {broke_rule}({broke_probability:.2f})")

        if(not broke_rule):
            return response

        if(broke_probability < least_flagged_probability):
            least_flagged_reply = response

            least_flagged_probability = broke_probability

    print(f"{regen_label} STILL FLAGGED, THE LEAST FLAGGED REPLY GOES OUT: {least_flagged_reply}")

    return least_flagged_reply


#HAS PIC
#their message came with a pic or video, the only time a reply can bring up something else in one
def has_pic(state: dict) -> bool:
    return state["current_user_message"].get("user_media", {}) != {}



#**********COLOR JOB**********
#keeps track of a wrap or colored PPF job, the jobs whose price waits on a pic of the vehicle


#CONVERSATION JOB
#True when a wrap, a color change or colored PPF is still the job they want, read from the whole conversation
def conversation_color_job(state: dict) -> bool:
    color_job_question: dict = {"type": "noul", "instructions": f"Is a vinyl wrap, a color change or colored PPF the job the customer wants in this conversation, asked about in `current_user_message` or earlier in `message_history` and not moved off of or turned down?\n{pricing_examples.color_job_examples()}"}

    probability_yes: float = models.decision_answer("color_job", color_job_question, state)["noul"]

    color_job_now: bool = probability_yes > COLOR_JOB_THRESHOLD

    print(f"CONVERSATION COLOR JOB: {color_job_now}({probability_yes:.2f})")

    return color_job_now


#NAMED CODES
#the services the analyzer named, the general code names none
def named_codes(codes: list[str]) -> list[str]:
    named: list[str] = []

    for code in codes:
        if(code != PRICING_GENERAL_CODE):
            named.append(code)

    return named


#SAVED CODES
#the color codes on file, a file from before the codes went on it only has the on flag, so it's both
def color_codes_in(on_file: dict) -> list[str]:
    if("codes" not in on_file and on_file.get("on", False)):
        return COLOR_CODES

    return on_file.get("codes", [])


#SAVED JOB
#the color codes the conversation is on, empty when it isn't on a wrap or colored PPF
def color_job_on_file(id: str) -> list[str]:
    return color_codes_in(log.read_state(f"s_p_color_job_{id}"))


#COLOR NOW MISSING
#a wrap or colored PPF job still waiting on the color it is now, the only time a pic of their vehicle gets asked for
def color_now_missing(id: str) -> bool:
    return len(color_job_on_file(id)) > 0 and log.read_info(f"criticalInfo_{id}").get("color") is None


#PIC ASKS
#how many replies asked for a pic of their vehicle while the color it is now wasn't on file
def color_pic_asks(id: str) -> int:
    return log.read_count(f"color_pic_asks_{id}")


#PIC ASKED
#a reply that went out asking for a pic while the job still waits on the color it is now is one more ask for it, never the exact color they want
def note_color_pic_ask(id: str, reply: str) -> None:
    if(not spacing.asks_for_pic(reply) or not color_now_missing(id)):
        return

    asks: int = log.next_count(f"color_pic_asks_{id}")

    print(f"COLOR PIC ASKS: {asks}")


#MARK JOB
#a booking held for the color goes back to the pricing branch on the job on file, both codes when none is named yet
def turn_color_job_on(id: str) -> None:
    codes: list[str] = color_job_on_file(id)

    if(len(codes) == 0):
        codes = COLOR_CODES

    log.write_state(f"s_p_color_job_{id}", {"codes": codes})


#COLOR JOB
#the color codes the conversation is on, a wrap and colored PPF are the jobs whose price needs the color it is now
def color_job(codes: list[str], state: dict, id: str) -> list[str]:
    named: list[str] = named_codes(codes)

    color_codes: list[str] = []

    #kept as their latest message names the job
    if(len(named) > 0):
        for code in named:
            if(code in COLOR_CODES):
                color_codes.append(code)

        #another service asked about on top of the job on file ("also for window tint I can do any shade right?") only ends it when they moved off it
        job_on_file: list[str] = color_job_on_file(id)

        if(len(color_codes) == 0 and len(job_on_file) > 0 and conversation_color_job(state)):
            return job_on_file

    else:
        #a follow up that names no service ("no pics on this phone", a pic, "lets do it") keeps going on the job on file
        on_file: dict = log.read_state(f"s_p_color_job_{id}")

        if(len(on_file) > 0):
            return color_codes_in(on_file)

        #nothing on file yet, like a job asked about in a message another branch answered, so it's read for once
        if(conversation_color_job(state)):
            color_codes = COLOR_CODES

    log.write_state(f"s_p_color_job_{id}", {"codes": color_codes})

    #the route belongs to the color job, so moving off it clears it and a color change later gets asked again
    if(len(color_codes) == 0):
        log.clear_info(f"criticalInfo_{id}", ["route"])

    return color_codes



#**********COLOR ROUTE**********
#works out which film they want for the color change, and when the owner checks the color they sent


#DECIDED ROUTE
#the route the decisions model picks, with how sure it is and its chance for that route, going by the whole conversation
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


#COLOR ROUTE
#the film they pick for the color change goes on file, so every follow up goes by it and it never gets asked again
def color_route(state: dict, codes: list[str], id: str) -> None:
    #a wrap weighed against clear PPF or a coating has one way to change the color in it, so there's nothing to decide
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

    #only a clear pick goes on file, so a follow up that names no film never loses the one they picked
    if(picked in COLOR_ROUTES and confidence >= COLOR_ROUTE_THRESHOLD):
        log.write_info(f"criticalInfo_{id}", [picked], ["route"])


#COLOR CHECK
#the vehicle, the route, a pic and the exact color are in, and the owner hasn't been asked about that color yet
def color_check_due(color_job_on: bool, critical_info: dict[str, str], color_check: str) -> bool:
    vehicle_known: bool = critical_info.get("make") is not None or critical_info.get("model") is not None

    #the owner checks the color in the film they picked, so the check waits for the route like the color questions do
    route_picked: bool = critical_info.get("route") is not None

    exact_color_in: bool = critical_info.get("color") is not None and critical_info.get("want") is not None

    return color_job_on and vehicle_known and route_picked and exact_color_in and color_check == ""



#**********EARLY COLOR ASKS**********
#what the exact price waits on gets asked before the color they want, so the ask for it goes out in place of one for that color too early


#PRICE NEEDS
#what the exact price still waits on from them, in the order it gets asked, empty once the color they want is next
#the color it is now counts as in once the asks for a pic of it ran out, the same way a color they type stands in for the pic then
def price_needs(critical_info: dict[str, str], id: str) -> list[str]:
    needs: list[str] = []

    if(critical_info.get("make") is None and critical_info.get("model") is None):
        needs.append(VEHICLE_NEED)

    #a color change with no film picked waits on the route before any color question, the same as the pricing branch asks it
    if(len(color_job_on_file(id)) > 0 and critical_info.get("route") is None):
        needs.append(ROUTE_NEED)

    if(critical_info.get("color") is None and color_pic_asks(id) < COLOR_PIC_ASK_LIMIT):
        needs.append(COLOR_NOW_NEED)

    return needs


#PRICE ASK WORDS
#the ways to ask for the first thing the price waits on, grouped the way the owner asks them
def price_ask_words(needs: list[str]) -> list[str]:
    if(needs[0] == VEHICLE_NEED):
        #a color change with no film picked asks the vehicle with which route, the color it is now waits for the route
        if(ROUTE_NEED in needs):
            return VEHICLE_ROUTE_ASKS

        if(COLOR_NOW_NEED in needs):
            return VEHICLE_COLOR_NOW_ASKS

        return VEHICLE_ASKS

    if(needs[0] == ROUTE_NEED):
        return ROUTE_ASKS

    return COLOR_NOW_ASKS


#PRICE ASK
#the one question for what the exact price waits on, in words the shop hasn't asked it in yet, the last way it's asked once it used them all
def price_ask(critical_info: dict[str, str], needs: list[str], message_history: dict) -> str:
    vehicle: str = critical_info.get("model") or critical_info.get("make") or ""

    asks: list[str] = []

    for ask in price_ask_words(needs):
        asks.append(ask.format(vehicle=vehicle))

    earlier_replies: list[str] = spacing.sent_replies(message_history)

    for ask in asks:
        if(len(repeats.repeated_questions(ask, earlier_replies)) == 0):
            return ask

    return asks[-1]



#**********PRICE HOLD**********
#the shop's first reply never gives a price unless their message asks what something costs, a lead form included, so they're talking first


#HOLD LINE
#goes on the input of a reply written while it holds every price, the prompts and their regens go by #PRICE HOLD when they see it
PRICE_HOLD_LINE: str = "PRICE_HOLD: yes"


#PRICE QUESTION
#True when their message asks what something costs, the one thing that lets a price into the shop's first reply
def price_question(state: dict) -> bool:
    question: dict = {"type": "noul", "instructions": f"Is the customer asking what something costs, or about its price, in `current_user_message`?\n{pricing_examples.price_question_examples()}"}

    probability_yes: float = models.decision_answer("price_question", question, state)["noul"]

    print(f"PRICE QUESTION: {probability_yes:.2f}")

    return probability_yes > PRICE_QUESTION_THRESHOLD


#PRICE HELD
#True on the shop's first reply when their message doesn't ask what anything costs, the reply the form intro goes on counts as the first one too
def price_held(state: dict) -> bool:
    #a reply already went out, so every price goes by the rules like any other reply
    if(greeting.replied_before(state["message_history"])):
        return False

    held: bool = not price_question(state)

    print(f"PRICE HOLD: {held}")

    return held


#HELD TEXT
#the input a reply gets written from, with the hold line on it while the reply holds every price
def held_text(text: str, held: bool) -> str:
    if(not held):
        return text

    return f"{text}\n {PRICE_HOLD_LINE}"


#HELD PRICE CUT
#a price that got past the hold comes off with its sentence, and when every sentence had one a person answers them instead
def held_price_cut(reply: str, held: bool, id: str) -> str:
    if(not held):
        return reply

    kept_reply: str = spacing.drop_prices(reply)

    if(kept_reply == "" and reply.strip() != ""):
        owner.restrict(id, owner.REASONS["price_hold"])

    return kept_reply



#**********PRICING**********
#answers questions about the shop's services and their prices, asking for what a price still needs


#PRICING QUESTIONS
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


#PRICING SERVICES
#the services the message is about (the job on file when it names none), and the color codes it's on
def pricing_services(state: dict, id: str) -> tuple[list[str], list[str]]:
    classified: tuple[list[str], dict[str, float]] = models.classifier(pricing_analyzer_questions(), state, ANALYZER_THRESHOLD)

    codes: list[str] = classified[0]

    probabilities: dict[str, float] = classified[1]

    #kept before the check, so every analyzed message updates the job the conversation is on
    color_codes: list[str] = color_job(codes, state, id)

    #a message no question picked up ("no pics on this phone", a pic with no text) carries on with the job on file
    if(codes == []):
        if(len(color_codes) > 0):
            codes = color_codes

        #with no job on, it's a general one
        else:
            codes = [PRICING_GENERAL_CODE]

    #another service asked about while the color job stays on gets the job's details next to its own
    else:
        for code in color_codes:
            if(code not in codes):
                codes.append(code)

    print(f"ANALYZER: {models.codes_with_probabilities(codes, probabilities)}")

    return (codes, color_codes)


#PRICING LACK INFO
#only acknowledges, for a message the service details have no answer for
def pricing_lack_info(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #the lack info generator only acknowledges, so it gets no service details to answer from
    lack_info_text: str = f"STATE: {state_as_text}"

    system_prompt: str = pricing_lack_info_generator.prompt()

    response: str = models.generator("LACK INFO GENERATOR", system_prompt, lack_info_text, PRICING_MAX_TOKENS, PRICING_EFFORT, line_breaks=False)

    rules: str = pricing_lack_info_enforcer.instructions()

    regen_prompt: str = pricing_lack_info_regenerator.prompt()

    return enforced_reply(state, lack_info_text, response, rules, "LACK INFO REGEN", regen_prompt, models.generator, PRICING_REGEN_MAX_TOKENS, PRICING_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)


#INTERROGATOR PROMPT
#the interrogator prompt and its what's missing for what the price or the booking still needs, None when everything is in
def pricing_interrogator(color_job_on: bool, critical_info: dict[str, str], color_check: str) -> tuple[str, str] | None:
    make: str | None = critical_info.get("make")

    model: str | None = critical_info.get("model")

    color: str | None = critical_info.get("color")

    want: str | None = critical_info.get("want")

    route: str | None = critical_info.get("route")

    #a color change can be done in vinyl or colored PPF, and the route comes before any color question
    route_needed: bool = color_job_on and route is None

    #only a pic gives the color it is now, so a wrap or colored PPF price waits on one until it's on file
    color_needed: bool = color_job_on and color is None

    #each prompt goes out with its what's missing, so the enforcer and the regen hold the same prices it does
    if(make is None and model is None):
        #the one that gets the make, model and color, with which route grouped in when that's missing too
        if(color_needed):
            return (vehicle_color.prompt(), vehicle_color.whats_missing())

        #the one that gets the make and model only, since the color isn't needed here
        return (vehicle.prompt(), vehicle.whats_missing())

    #the one that lays out both routes and gets theirs, before the color they want, the color it is now or a pic
    elif(route_needed):
        return (which_route.prompt(), which_route.whats_missing())

    #the one that gets the color
    elif(color_needed):
        return (color_now.prompt(), color_now.whats_missing())

    #the price can go out, but booking waits on a pic or link of the exact color they want
    elif(color_job_on and want is None):
        return (exact_color.prompt(), exact_color.whats_missing())

    #they sent it, and booking waits on the owner making sure the shop can get it in
    elif(color_job_on and color_check in ["", owner.PENDING_STATUS]):
        return (color_checking.prompt(), color_checking.whats_missing())

    #the shop can't get that exact color, so booking waits on them picking one of the closest materials it can order
    elif(color_check == owner.MATERIALS_STATUS):
        return (closest_materials.prompt(), closest_materials.whats_missing())

    #everything the price and the booking need is in, so the main generator answers
    return None


#PRICING INTERROGATE
#every interrogator is written by flashx, held is True on the shop's first reply while it holds every price
def pricing_interrogate(state: dict, user_text: str, interrogator: tuple[str, str], held: bool) -> str:
    interrogator_prompt: str = interrogator[0]

    whats_missing: str = interrogator[1]

    response: str = models.generator("INTERROGATOR", interrogator_prompt, user_text, PRICING_MAX_TOKENS, PRICING_INTERROGATOR_EFFORT, line_breaks=True)

    #the enforcer and the regen get the shop's last reply on its own, so a line from it said again gets caught
    shop_last_reply: str = spacing.last_sent_reply(state["message_history"])

    #the color pic rule only goes into the check when their message has a pic, and the price hold rule only on a first reply that holds every price
    rules: str = interrogator_enforcer.instructions(whats_missing, has_pic(state), held)

    #the regen gets the interrogator's whole prompt, so a service the reply left out gets put back with its price
    regen_prompt: str = interrogator_regenerator.prompt(interrogator_prompt)

    return enforced_reply(state, user_text, response, rules, "INTERROGATOR REGEN", regen_prompt, models.generator, PRICING_REGEN_MAX_TOKENS, PRICING_INTERROGATOR_REGEN_EFFORT, line_breaks=True, shop_last_reply=shop_last_reply, held=held)


#BOOKING INTENT
#a booking ask sent here with a job question still has to end on the schedule question once the price is out
def booking_intent(state: dict) -> bool:
    booking_question: dict = {"type": "noul", "instructions": f"Is the customer asking to get on the schedule or the books, to book it, or when they can get in or bring it in, in `current_user_message`?\n{pricing_examples.booking_intent_examples()}"}

    probability_yes: float = models.decision_answer("booking_intent", booking_question, state)["noul"]

    print(f"BOOKING INTENT: {probability_yes:.2f}")

    return probability_yes > BOOKING_INTENT_THRESHOLD


#PRICING REPLY
#the reply and whether the service details had no answer for their message, the lack info reply goes out then
def pricing_reply(state: dict, critical_info: dict[str, str], id: str) -> tuple:
    services: tuple[list[str], list[str]] = pricing_services(state, id)

    service_details: dict[str, dict] = models.analyzed_details(services[0], PRICING_DETAILS, PRICING_GENERAL_CODE)

    color_job_on: bool = len(services[1]) > 0

    print(f"COLOR JOB: {color_job_on}")

    #a color change can be done in vinyl or colored PPF, so both details go in and the reply can lay out both routes
    if(COLOR_CHANGE_CODE in service_details and COLORED_PPF_CODE not in service_details):
        service_details[COLORED_PPF_CODE] = PRICING_DETAILS[COLORED_PPF_CODE]

    #colored PPF gets the wrap's details next to it, so a budget it's over can get the wrap offered with its number
    if(COLORED_PPF_CODE in service_details and COLOR_CHANGE_CODE not in service_details):
        service_details[COLOR_CHANGE_CODE] = PRICING_DETAILS[COLOR_CHANGE_CODE]

    #the film they picked goes on file before the prompt gets picked, so the route gets asked before any color question
    if(color_job_on):
        color_route(state, services[0], id)

        critical_info = log.read_info(f"criticalInfo_{id}")

    state_as_text: str = state_form.state_to_text(state)

    details: str = details_text(service_details, PRICING_GENERAL_CODE)

    user_text: str = f"SERVICE_DETAILS: {details}\n STATE: {state_as_text}"

    check_rules: str = pricing_checker.instructions()

    check_question: str = f"Is everything the customer is asking for in current_user_message something SERVICE_DETAILS has no answer for, with no part of the message covered, per the rules defined here\n{check_rules}\n?"

    service_check: bool = models.checker(check_question, state, "SERVICE_DETAILS", details, CHECKER_THRESHOLD)

    if(service_check):
        return (pricing_lack_info(state), service_check)

    #the shop's first reply holds every price unless their message asks what something costs
    held: bool = price_held(state)

    user_text = held_text(user_text, held)

    color_check: str = owner.color_check_status(id)

    interrogator: tuple[str, str] | None = pricing_interrogator(color_job_on, critical_info, color_check)

    #the exact color they sent goes to the owner once, so he can make sure the shop can get it in for their route
    if(color_check_due(color_job_on, critical_info, color_check)):
        owner.request_color_check(id, critical_info.get("route", ""))

    #what a price or the booking needs isn't in yet, so the reply answers what it can and asks for it
    if(interrogator is not None):
        interrogated: str = pricing_interrogate(state, user_text, interrogator, held)

        return (held_price_cut(interrogated, held, id), service_check)

    system_prompt: str = pricing_generator.prompt()

    response: str = models.s_p_generator("MAIN GENERATOR", system_prompt, user_text, PRICING_MAX_TOKENS, PRICING_MAIN_EFFORT, line_breaks=True)

    #the enforcer and the regen get the shop's last reply on its own, so a line from it said again gets caught
    shop_last_reply: str = spacing.last_sent_reply(state["message_history"])

    #the color pic rule only goes into the check when their message has a pic, and the price hold rule only on a first reply that holds every price
    rules: str = pricing_enforcer.instructions(has_pic(state), held)

    regen_prompt: str = pricing_regenerator.prompt()

    reply: str = enforced_reply(state, user_text, response, rules, "MAIN REGEN", regen_prompt, models.s_p_generator, PRICING_REGEN_MAX_TOKENS, PRICING_MAIN_REGEN_EFFORT, line_breaks=True, shop_last_reply=shop_last_reply, held=held)

    #a price that got past the hold never goes out on the shop's first reply
    return (held_price_cut(reply, held, id), service_check)



#**********BUSINESS**********
#answers questions about the shop itself, like its hours, where it is and how to pay


#BUSINESS QUESTIONS
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


#BUSINESS LACK INFO
#only acknowledges, for a message the business details have no answer for
def business_lack_info(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #the lack info generator only acknowledges, so it gets no business details to answer from
    lack_info_text: str = f"STATE: {state_as_text}"

    system_prompt: str = business_lack_info_generator.prompt()

    response: str = models.generator("LACK INFO GENERATOR", system_prompt, lack_info_text, BUSINESS_MAX_TOKENS, BUSINESS_EFFORT, line_breaks=False)

    rules: str = business_lack_info_enforcer.instructions()

    regen_prompt: str = business_lack_info_regenerator.prompt()

    return enforced_reply(state, lack_info_text, response, rules, "LACK INFO REGEN", regen_prompt, models.generator, BUSINESS_REGEN_MAX_TOKENS, BUSINESS_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)


#BUSINESS REPLY
#the reply and whether the business details had no answer for their message, the lack info reply goes out then
def business_reply(state: dict) -> tuple:
    business_details: dict[str, dict] = models.analyzer(business_analyzer_questions(), state, BUSINESS_DETAILS, BUSINESS_GENERAL_CODE, ANALYZER_THRESHOLD)

    state_as_text: str = state_form.state_to_text(state)

    details: str = details_text(business_details, BUSINESS_GENERAL_CODE)

    user_text: str = f"BUSINESS_DETAILS: {details}\n STATE: {state_as_text}"

    check_rules: str = business_checker.instructions()

    check_question: str = f"Is everything the customer is asking for in current_user_message something BUSINESS_DETAILS has no answer for, with no part of the message covered, per the rules defined here\n{check_rules}\n?"

    business_check: bool = models.checker(check_question, state, "BUSINESS_DETAILS", details, CHECKER_THRESHOLD)

    if(business_check):
        return (business_lack_info(state), business_check)

    system_prompt: str = business_generator.prompt()

    response: str = models.generator("MAIN GENERATOR", system_prompt, user_text, BUSINESS_MAX_TOKENS, BUSINESS_EFFORT, line_breaks=False)

    rules: str = business_enforcer.instructions()

    regen_prompt: str = business_regenerator.prompt()

    reply: str = enforced_reply(state, user_text, response, rules, "MAIN REGEN", regen_prompt, models.generator, BUSINESS_REGEN_MAX_TOKENS, BUSINESS_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)

    return (reply, business_check)



#**********CUSTOM JOB INFO**********
#pulls what they gave for a custom job out of their message and saves it to the job's file


#CUSTOM VALUES
#the values out of the extractor's line, raises when it isn't the format
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


#STALE VEHICLES
#takes the makes and models off file when they gave a new vehicle count, so the vehicles get asked again for it
def clear_stale_vehicles(id: str, extracted_values: list[str], field_names: list[str]) -> None:
    extracted_info: dict[str, str] = dict(zip(field_names, extracted_values))

    car_amount: str = extracted_info["car_amount"]

    #a new amount can outgrow the vehicles on file, so makes and models it left empty come off and get asked again
    if(car_amount != "" and car_amount != log.read_info(f"custom_service_{id}").get("car_amount")):
        stale_fields: list[str] = []

        for field_name in ["makes", "models"]:
            if(extracted_info[field_name] == ""):
                stale_fields.append(field_name)

        log.clear_info(f"custom_service_{id}", stale_fields)


#CUSTOM SAVE
#puts the custom job info the extractor pulled out of their message on file
def save_custom_info(id: str, extractor_output: str, field_names: list[str], commercial_wrap: bool) -> None:
    #a reply that talks instead of giving the format is never saved, the reply still asks for what isn't on file
    try:
        extracted_values: list[str] = custom_values(extractor_output, field_names)

        if(commercial_wrap and len(extracted_values) == len(field_names)):
            clear_stale_vehicles(id, extracted_values, field_names)

        log.write_info(f"custom_service_{id}", extracted_values, field_names)

    except Exception as error:
        print(f"C_S EXTRACTOR ERROR: {error}")


#CUSTOM EXTRACT
#saves what their message gave for the job and hands back the fields this job needs
def custom_extract_and_save(id: str, user_text: str, commercial_wrap: bool, removal: bool) -> list[str]:
    #a commercial wrap needs the wrap type, the vehicles and the logo files
    if(commercial_wrap):
        field_names: list[str] = ["wrap_type", "car_amount", "makes", "models", "vector_files"]

        extractor_output: str = models.extract_commercial_wrap(user_text)

    #old PPF or an old wrap coming off needs a photo and how long it's been on
    elif(removal):
        field_names: list[str] = ["media", "time_on"]

        extractor_output: str = models.extract_removal(user_text)

    #every other custom job needs a photo
    else:
        field_names: list[str] = ["media"]

        extractor_output: str = models.extract_photo(user_text)

    save_custom_info(id, extractor_output, field_names, commercial_wrap)

    return field_names



#**********CUSTOM ACK**********
#lets them know a person has everything to price the job, and when the price comes back


#PRICE BACK
#when the owner gets back to them with the custom price, said the way the shop says it from its hours
def custom_price_back(current_date_time: str) -> str:
    shop_time: datetime = datetime.strptime(current_date_time, state_form.CURRENT_DATE_TIME_FORMAT)

    weekday: int = shop_time.weekday()

    clock: time = shop_time.time()

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


#CUSTOM ACK
#the reply that lets them know a person prices the custom job and when they'll hear back
def custom_ack_reply(state: dict, user_text: str, custom_service_info: dict[str, str], field_names: list[str]) -> str:
    #only the fields this job needed, so info on file for another custom job never gets read back
    info_on_file: dict[str, str] = {}

    for field_name in field_names:
        info_on_file[field_name] = custom_service_info[field_name]

    info_text: str = json.dumps(info_on_file, ensure_ascii=False)

    price_back: str = custom_price_back(state["current_date_time"])

    #what's on file goes in with when the price comes back
    ack_text: str = f"{user_text}\n INFO_ON_FILE: {info_text}\n PRICE_BACK: {price_back}"

    system_prompt: str = custom_ack.prompt()

    return models.generator("ACK GENERATOR", system_prompt, ack_text, CUSTOM_MAX_TOKENS, CUSTOM_EFFORT, line_breaks=False)



#**********REPEATED ASKS**********
#keeps a commercial wrap question from going out again in the same words or the same way


#LAST ASKED
#the commercial wrap detail the shop's last reply asked for, None when that reply didn't ask for one
def last_asked_group(id: str, message_history: dict) -> str | None:
    asked: dict[str, str] = log.read_info(f"c_s_asked_{id}")

    group: str | None = asked.get("group")

    question: str | None = asked.get("question")

    if(group is None or question is None):
        return None

    #it only counts when the last reply that went out asked it, a reply from another branch asked something else
    if(not repeats.asked_in(question, spacing.last_sent_reply(message_history))):
        return None

    return group


#SAVE ASKED
#keeps the question the reply ended on with the detail it asked for, so the next reply can tell if it went unanswered
def save_asked(id: str, group: str, response: str) -> None:
    questions: list[str] = repeats.question_sentences(response)

    #no question went out, so whatever the next reply asks is never a repeat
    if(len(questions) == 0):
        log.clear_info(f"c_s_asked_{id}", ["group", "question"])

        return

    log.write_info(f"c_s_asked_{id}", [group, questions[-1]], ["group", "question"])


#ASKS GROUP
#True when the question asks for that group's commercial wrap detail, going by its words
def asks_group(question: str, group: str) -> bool:
    plain_text: str = " ".join(repeats.plain_words(question))

    question_text: str = f" {plain_text} "

    for words in COMMERCIAL_GROUP_WORDS[group]:
        if(f" {words} " in question_text):
            return True

    return False


#REPEATED ASKS
#the questions in the reply the shop already asked before, plus ones still asking for the detail they skipped
def repeated_asks(response: str, earlier_replies: list[str], group: str, skipped_group: str) -> list[str]:
    repeated: list[str] = repeats.repeated_questions(response, earlier_replies)

    if(skipped_group == ""):
        return repeated

    #what they skipped waits for a later reply, so a question about it in other words is still asking it now
    for question in repeats.question_sentences(response):
        if(asks_group(question, skipped_group) and not asks_group(question, group) and question not in repeated):
            repeated.append(question)

    return repeated


#UNREPEATED REPLY
#the reply with no question worded like one the shop already asked, rewritten when it repeated one
def unrepeated_reply(state: dict, interrogator_text: str, response: str, regen_prompt: str, group: str, skipped_group: str) -> str:
    #every question the shop asked so far, so none goes out in the same words or the same way again
    earlier_replies: list[str] = spacing.sent_replies(state["message_history"])

    repeated: list[str] = repeated_asks(response, earlier_replies, group, skipped_group)

    if(len(repeated) == 0):
        return response

    #the enforcer let through a question worded like one the shop already asked, so the regen gets told which one
    print(f"REPEATED QUESTION: {repeated}")

    repeated_text: str = " ".join(repeated)

    regen_text: str = f"{interrogator_text}\n FLAGGED_RESPONSE: {response}\n REPEATED_QUESTION: {repeated_text}"

    regen_response: str = models.generator("REPEAT REGEN", regen_prompt, regen_text, CUSTOM_REGEN_MAX_TOKENS, CUSTOM_COMMERCIAL_REGEN_EFFORT, line_breaks=False)

    regen_repeated: list[str] = repeated_asks(regen_response, earlier_replies, group, skipped_group)

    #a regen that came back empty never goes out, the first reply's rest does
    if(regen_response.strip() != "" and len(regen_repeated) == 0):
        return regen_response

    #the regen asked it again too, so it comes off and the rest goes out, the first reply's rest when the regen had none
    for reply, reply_repeated in [(regen_response, regen_repeated), (response, repeated)]:
        kept_reply: str = repeats.drop_questions(reply, reply_repeated)

        if(kept_reply != ""):
            print(f"REPEATED QUESTION CUT: {reply_repeated}")

            return kept_reply

    #both replies were only the question, so it stays and something still goes out
    print(f"REPEATED QUESTION KEPT, NOTHING ELSE IN THE REPLY: {regen_response}")

    return regen_response



#**********COMMERCIAL WRAP**********
#asks for what a commercial wrap's price still needs one thing at a time, then hands it to a person


#VEHICLE COUNT
#how many vehicles are on file, said as a short add on to the make and model ask
def vehicle_count(car_amount: str | None) -> str:
    #how many isn't on file when that question was skipped for a later reply, so the line leaves it out
    if(car_amount is None):
        return ""

    return f", {car_amount} in all"


#COMMERCIAL MISSING
#every commercial wrap detail the price still needs, in the order the owner asks for them
def commercial_wrap_missing(custom_service_info: dict[str, str], services: str) -> list[COMMERCIAL_ASK]:
    wrap_type: str | None = custom_service_info.get("wrap_type")

    car_amount: str | None = custom_service_info.get("car_amount")

    makes: str | None = custom_service_info.get("makes")

    vehicle_models: str | None = custom_service_info.get("models")

    vector_files: str | None = custom_service_info.get("vector_files")

    #everything the price still needs, in the order the owner asks for it, empty when it's all on file
    missing: list[COMMERCIAL_ASK] = []

    if(wrap_type is None):
        missing.append(("wrap_type", custom_wrap_type.prompt, f"Whether the {services} is decals, a half wrap or a full wrap."))

    if(car_amount is None):
        missing.append(("car_amount", custom_vehicle_count.prompt, f"How many vehicles the {services} is for."))

    #the make and model come in together, so they're one ask, and the model gets asked on its own once every make is in
    if(makes is None):
        missing.append(("vehicles", custom_make_model.prompt, f"The make and model of each vehicle the {services} is for{vehicle_count(car_amount)}."))

    elif(vehicle_models is None):
        missing.append(("vehicles", custom_vehicle_model.prompt, f"The model of each vehicle the {services} is for, makes on file: {makes}."))

    if(vector_files is None):
        missing.append(("vector_files", custom_logo_file.prompt, f"Whether they have the logo and artwork for the {services} as vector files (an AI, EPS, SVG or PDF file)."))

    return missing


#OTHER INFO
#True when their message filled in a commercial wrap detail other than the one the last reply asked for
def gave_other_info(info_before: dict[str, str], info_after: dict[str, str], group: str) -> bool:
    for other_group, field_names in COMMERCIAL_GROUP_FIELDS.items():
        if(other_group == group):
            continue

        for field_name in field_names:
            value: str | None = info_after.get(field_name)

            #a field this message filled in or changed, like how many when the last reply asked which job it is
            if(value is not None and value != info_before.get(field_name)):
                return True

    return False


#COMMERCIAL ASK
#which missing detail this reply asks for, what the last reply already asked, and the detail they skipped by giving something else
def commercial_ask(state: dict, id: str, missing: list[COMMERCIAL_ASK], info_before: dict[str, str], custom_service_info: dict[str, str]) -> tuple[COMMERCIAL_ASK, str, str]:
    first: COMMERCIAL_ASK = missing[0]

    #the last reply asked something else, so what's missing first gets asked as usual
    if(last_asked_group(id, state["message_history"]) != first[0]):
        return (first, "", "")

    #they wrote back without it, so it goes in as already asked and gets asked again in a new way
    already_asked: str = first[2]

    #they gave something else instead, so the next thing missing gets asked and it comes back in a later reply
    if(gave_other_info(info_before, custom_service_info, first[0]) and len(missing) > 1):
        print(f"ASKED AGAIN SKIPPED: {first[0]}, asking {missing[1][0]} instead")

        return (missing[1], already_asked, first[0])

    return (first, already_asked, "")


#COMMERCIAL INTERROGATE
#writes the reply that asks for the next commercial wrap detail and checks it against the rules, held is True on the shop's first reply while it holds every price
def commercial_interrogate(state: dict, user_text: str, ask: COMMERCIAL_ASK, already_asked: str, skipped_group: str, held: bool) -> str:
    interrogator_prompt: str = ask[1]()

    interrogator_text: str = f"{user_text}\n INFO_NEEDED: {ask[2]}"

    #what the shop's last reply asked that they wrote back without, so it never gets asked the same way twice in a row
    if(already_asked != ""):
        interrogator_text = f"{interrogator_text}\n ALREADY_ASKED: {already_asked}"

    response: str = models.generator("INTERROGATOR", interrogator_prompt, interrogator_text, CUSTOM_MAX_TOKENS, CUSTOM_COMMERCIAL_EFFORT, line_breaks=False)

    regen_prompt: str = commercial_regenerator.prompt(interrogator_prompt)

    #the price hold rule only goes into the check on a first reply that holds every price
    rules: str = commercial_enforcer.instructions(held)

    response = enforced_reply(state, interrogator_text, response, rules, "INTERROGATOR REGEN", regen_prompt, models.generator, CUSTOM_REGEN_MAX_TOKENS, CUSTOM_COMMERCIAL_REGEN_EFFORT, line_breaks=False, shop_last_reply=None, held=held)

    #the enforcer can miss a question asked twice in a row, so the code checks for it too
    return unrepeated_reply(state, interrogator_text, response, regen_prompt, ask[0], skipped_group)


#COMMERCIAL WRAP
#the next commercial wrap detail asked for, or the ack once everything the price needs is on file
def commercial_wrap_reply(state: dict, id: str, user_text: str, services: str, info_before: dict[str, str], custom_service_info: dict[str, str], field_names: list[str], held: bool) -> tuple:
    missing: list[COMMERCIAL_ASK] = commercial_wrap_missing(custom_service_info, services)

    #everything the price needs is on file, so the ack goes out and a person takes it from here
    if(len(missing) == 0):
        log.clear_info(f"c_s_asked_{id}", ["group", "question"])

        return (custom_ack_reply(state, user_text, custom_service_info, field_names), True)

    ask: tuple[COMMERCIAL_ASK, str, str] = commercial_ask(state, id, missing, info_before, custom_service_info)

    response: str = commercial_interrogate(state, user_text, ask[0], ask[1], ask[2], held)

    save_asked(id, ask[0][0], response)

    return (response, False)



#**********CUSTOM**********
#gets what a person needs to price a custom job, then lets them know when the price comes back


#CUSTOM QUESTIONS
#the yes or no questions that find which custom job their message asks about, one code each
def custom_analyzer_questions() -> dict[str, dict]:
    questions: dict[str, dict] = {}

    questions["c1"] = {"type": "noul", "instructions": f"Is the customer asking about a commercial wrap (a wrap, logos, decals, lettering or graphics for a business) in `current_user_message`?\n{custom_examples.commercial_wrap_examples()}"}

    questions["c2"] = {"type": "noul", "instructions": f"Is the customer asking about a custom wrap on a personal vehicle (a partial, a two tone, a specialty film or a custom design, not for a business) in `current_user_message`?\n{custom_examples.custom_wrap_examples()}"}

    questions["c3"] = {"type": "noul", "instructions": f"Is the customer asking about PPF or clear bra that's already on the vehicle now getting taken off, redone or replaced in `current_user_message`?\n{custom_examples.ppf_removal_examples()}"}

    questions["c4"] = {"type": "noul", "instructions": f"Is the customer asking about a chrome delete (covering or blacking out the chrome) in `current_user_message`?\n{custom_examples.chrome_delete_examples()}"}

    questions["c5"] = {"type": "noul", "instructions": f"Is the customer asking about some other job the shop's services don't list, one that isn't a commercial wrap, a custom wrap, old PPF or an old wrap coming off or a chrome delete (body work, PPF on just one piece, a motorcycle, boat or RV and the like), in `current_user_message`?\n{custom_examples.other_job_examples()}"}

    questions["c6"] = {"type": "noul", "instructions": f"Is the customer asking about a vinyl wrap that's already on the vehicle now getting taken off, redone or replaced in `current_user_message`?\n{custom_examples.wrap_removal_examples()}"}

    return questions


#CUSTOM SERVICES
#the custom services named in one line, or job when none could be named
def custom_services(custom_details: dict[str, dict]) -> str:
    #the custom services are named, so the one line on what's needed says what it's for
    service_names: list[str] = []

    for custom_detail in custom_details.values():
        service_names.append(custom_detail["service"])

    services: str = " and ".join(service_names)

    #no custom service could be named, so the one line is about the job as a whole
    if(services == ""):
        services = "job"

    return services


#REMOVAL MISSING
#the prompt and the ask while a removal job still needs its photo or how long the film has been on
def removal_missing(custom_service_info: dict[str, str], services: str) -> tuple[str, str]:
    media_sent: str | None = custom_service_info.get("media")

    time_on: str | None = custom_service_info.get("time_on")

    interrogator_prompt: str = custom_removal.prompt()

    #the owner asks for both in the same question, then only for whichever one is still missing
    if(media_sent is None and time_on is None):
        return (interrogator_prompt, f"How long it's been on and a photo of it as it is now, for the {services}.")

    elif(time_on is None):
        return (interrogator_prompt, f"How long it's been on, for the {services}. The photo is on file.")

    elif(media_sent is None):
        return (interrogator_prompt, f"A photo of it as it is now, for the {services}. How long it's been on is on file: {time_on}.")

    #the photo and how long it's been on are both on file
    return ("", "")


#MEDIA MISSING
#the photo prompt and the ask while the custom job has no photo on file, empty once it does
def media_missing(custom_service_info: dict[str, str], services: str) -> tuple[str, str]:
    media_sent: str | None = custom_service_info.get("media")

    if(media_sent is None):
        return (custom_photo.prompt(), f"A photo of the vehicle or of what they want for the {services}.")

    #the photo is on file
    return ("", "")


#CUSTOM MISSING
#the interrogator prompt and the one line on what it asks for, both empty when nothing is missing
def custom_missing(custom_service_info: dict[str, str], services: str, removal: bool) -> tuple[str, str]:
    if(removal):
        return removal_missing(custom_service_info, services)

    return media_missing(custom_service_info, services)


#CUSTOM INTERROGATE
#the photo and removal interrogators' replies go out as written, written by flashx like every other interrogator
def custom_interrogate(user_text: str, interrogator_prompt: str, info_needed: str) -> str:
    interrogator_text: str = f"{user_text}\n INFO_NEEDED: {info_needed}"

    return models.generator("INTERROGATOR", interrogator_prompt, interrogator_text, CUSTOM_MAX_TOKENS, CUSTOM_INTERROGATOR_EFFORT, line_breaks=False)


#CUSTOM REPLY
#the reply and whether a person takes it from here, which is once everything the price needs is on file
def custom_reply(state: dict, id: str) -> tuple:
    #a custom job has no general code
    custom_details: dict[str, dict] = models.analyzer(custom_analyzer_questions(), state, CUSTOM_DETAILS, None, ANALYZER_THRESHOLD)

    state_as_text: str = state_form.state_to_text(state)

    details: str = details_text(custom_details, None)

    user_text: str = f"CUSTOM_SERVICE_DETAILS: {details}\n STATE: {state_as_text}"

    commercial_wrap: bool = "c1" in custom_details

    #PPF (c3) or wrap (c6) removal, a commercial wrap's own details cover taking old decals or a wrap off
    removal: bool = not commercial_wrap and ("c3" in custom_details or "c6" in custom_details)

    #what a commercial wrap had on file before this message, so what they just gave shows
    info_before: dict[str, str] = {}

    if(commercial_wrap):
        info_before = log.read_info(f"custom_service_{id}")

    field_names: list[str] = custom_extract_and_save(id, user_text, commercial_wrap, removal)

    services: str = custom_services(custom_details)

    custom_service_info: dict[str, str] = log.read_info(f"custom_service_{id}")

    #the shop's first reply holds every price unless their message asks what something costs, the extractors above read their message without the hold
    held: bool = price_held(state)

    reply_text: str = held_text(user_text, held)

    if(commercial_wrap):
        custom_return: tuple = commercial_wrap_reply(state, id, reply_text, services, info_before, custom_service_info, field_names, held)

    else:
        missing: tuple[str, str] = custom_missing(custom_service_info, services, removal)

        interrogator_prompt: str = missing[0]

        info_needed: str = missing[1]

        #everything the price needs is on file, so the ack goes out and a person takes it from here
        if(info_needed == ""):
            custom_return = (custom_ack_reply(state, reply_text, custom_service_info, field_names), True)

        else:
            custom_return = (custom_interrogate(reply_text, interrogator_prompt, info_needed), False)

    #a price that got past the hold never goes out on the shop's first reply
    return (held_price_cut(custom_return[0], held, id), custom_return[1])



#**********PRICES AND DEPOSIT**********
#adds up the prices quoted for what they're booking and works out the deposit like the invoice does


#PRICE AMOUNT
#the dollar amount in one extracted price, None when it was never quoted or isn't in the shop's format
def price_amount(price: str) -> Decimal | None:
    price_text: str = price.strip().lower()

    #every price the extractor writes is $<amount> plus tax, so one never quoted or in any other shape has no amount
    if(not price_text.startswith("$") or not price_text.endswith(" plus tax")):
        return None

    amount_text: str = price_text[len("$"):-len(" plus tax")].replace(",", "").strip()

    try:
        amount: Decimal = Decimal(amount_text)

    except InvalidOperation:
        return None

    #a real quote is never negative, nan or infinite
    if(not amount.is_finite() or amount < 0):
        return None

    return amount


#SERVICES AMOUNT
#every extracted price added up, None when nothing came up yet or one service was never quoted
def services_amount(services_pricing: dict[str, str]) -> Decimal | None:
    #nothing they want has come up yet, so there's nothing to add up
    if(len(services_pricing) == 0):
        return None

    total: Decimal = Decimal(0)

    for price in services_pricing.values():
        amount: Decimal | None = price_amount(price)

        #one service never quoted leaves the total unknown
        if(amount is None):
            return None

        total += amount

    return total


#DOLLAR TEXT
#an amount written the way the shop writes a price
def dollar_text(amount: Decimal) -> str:
    #written the way the shop writes a price, like $3900, with cents only when there are some
    if(amount == amount.to_integral_value()):
        return f"${int(amount)}"

    return f"${amount:.2f}"


#SERVICES TOTAL
#the total of every service they want written like the shop writes it, empty when it can't be added up
def services_total(services_pricing: dict[str, str]) -> str:
    total: Decimal | None = services_amount(services_pricing)

    if(total is None):
        return ""

    return f"{dollar_text(total)} plus tax"


#DEPOSIT AMOUNT
#the 20% deposit on the total to the cent, None when there's no total
def deposit_amount(services_pricing: dict[str, str]) -> Decimal | None:
    total: Decimal | None = services_amount(services_pricing)

    #with no total there's nothing to take the deposit from
    if(total is None):
        return None

    #a fifth of the total, to the cent the way the invoice charges it
    return (total * DEPOSIT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


#SERVICES DEPOSIT
#the deposit written like the shop writes a price, empty when there's no total
def services_deposit(services_pricing: dict[str, str]) -> str:
    deposit: Decimal | None = deposit_amount(services_pricing)

    if(deposit is None):
        return ""

    return dollar_text(deposit)


#SERVICES PRICING
#reply_before is a branch's answer going out right before the days in the same text, a price it quotes counts too
def extract_services_pricing(state: dict, reply_before: str) -> dict[str, str]:
    state_as_text: str = state_form.state_to_text(state)

    extractor_output: str = models.extract_services(f"REPLY_BEFORE: {reply_before}\n STATE: {state_as_text}")

    #the service is the key and the price quoted for it is the value, for every service they want
    services_pricing: dict[str, str] = {}

    #a reply that talks instead of giving the format is never used, so nothing gets booked from it
    try:
        services_pricing = models.services_pricing_values(extractor_output)

    except Exception as error:
        print(f"S_P EXTRACTOR ERROR: {error}")

    print(f"SERVICES PRICING: {services_pricing}")

    return services_pricing



#**********BOOKING DATES**********
#finds the open drop off days on the calendar and offers them, or lets them know none are open


#OPEN DATES
#every open drop off day in the next 3 weeks for the job on file, each written like Monday, October 12
def pull_open_dates(state: dict, id: str) -> list[str]:
    #the job they want, saved when the open days first went out for it
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    #nothing on file, so no day can fit the job and the ack goes out for a person to find one
    if(len(confirmed_services) == 0):
        print("BOOKING DATE ERROR: no booked services on file, so no drop off day can be found")

    service_names: list[str] = list(confirmed_services.keys())

    shop_today: date = datetime.strptime(state["current_date_time"], state_form.CURRENT_DATE_TIME_FORMAT).date()

    calendar_window: tuple = open_dates.calendar_window(shop_today)

    events: list[dict] = google_calendar.read_events(calendar_window[0], calendar_window[1])

    #every open day in the next 3 weeks, soonest first
    open_days: list[date] = open_dates.open_drop_off_dates(service_names, events, shop_today)

    #each day is written like Monday, October 12, so the generator can say it the way the owner texts it
    open_date_texts: list[str] = []

    for open_day in open_days:
        open_date_texts.append(f"{open_day.strftime('%A, %B')} {open_day.day}")

    print(f"OPEN DATES: {open_date_texts}")

    return open_date_texts


#DATE ACK
#open_date_texts is empty when nothing is open, otherwise the days that went out and none of them work for them
def booking_date_ack_reply(state: dict, open_date_texts: list[str], reply_before: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    dates_text: str = json.dumps(open_date_texts)

    #reply_before is a branch's answer going out right before this one, empty when the ack has to answer it
    ack_text: str = f"OPEN_DATES: {dates_text}\n REPLY_BEFORE: {reply_before}\n STATE: {state_as_text}"

    system_prompt: str = booking_date_ack.prompt()

    return models.generator("DATE ACK GENERATOR", system_prompt, ack_text, BOOKING_DATE_MAX_TOKENS, BOOKING_DATE_EFFORT, line_breaks=False)


#DATE PROPOSE
#the reply offering the open drop off days, with the job's total and deposit worked out here
def date_propose_reply(state: dict, open_date_texts: list[str], turned_down_texts: list[str], id: str, reply_before: str) -> str:
    #the job the days go out for, saved when they first went out for it
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    #worked out here and never by the generator, so a price or deposit they ask about is the one the invoice charges
    total: str = services_total(confirmed_services)

    deposit: str = services_deposit(confirmed_services)

    print(f"SERVICES TOTAL: {total} | DEPOSIT: {deposit}")

    state_as_text: str = state_form.state_to_text(state)

    dates_text: str = json.dumps(open_date_texts)

    #days they just turned down, empty on the first offer
    turned_down_text: str = json.dumps(turned_down_texts)

    pricing_text: str = json.dumps(confirmed_services, ensure_ascii=False)

    #total and deposit are empty when a service was never quoted, and reply_before is empty when nothing goes out first
    propose_text: str = f"OPEN_DATES: {dates_text}\n TURNED_DOWN: {turned_down_text}\n SERVICES_PRICING: {pricing_text}\n TOTAL: {total}\n DEPOSIT: {deposit}\n REPLY_BEFORE: {reply_before}\n STATE: {state_as_text}"

    system_prompt: str = booking_date_propose.prompt()

    return models.generator("DATE PROPOSE GENERATOR", system_prompt, propose_text, BOOKING_DATE_MAX_TOKENS, BOOKING_DATE_EFFORT, line_breaks=False)


#BOOKING DATE
#offers the soonest open days, or the ack when nothing is open, and hands back the days that went out
def booking_date_reply(state: dict, id: str, reply_before: str) -> tuple:
    #the soonest open days go out first
    open_date_texts: list[str] = pull_open_dates(state, id)[:open_dates.DATES_TO_PROPOSE]

    response: str = ""

    #nothing is open in the next 3 weeks, so the ack lets them know a person finds them a day, after any answer first
    if(len(open_date_texts) == 0):
        response = booking_date_ack_reply(state, open_date_texts, reply_before)

    #the open days get offered, after the answer to anything they asked along with their yes
    else:
        response = date_propose_reply(state, open_date_texts, [], id, reply_before)

    return (response, open_date_texts)


#ASKED DATES
#the open days they asked for by name, in calendar order
def asked_open_dates(state: dict, open_date_texts: list[str]) -> list[str]:
    #a yes or no for each open day, so a day they asked for is found anywhere in the next 3 weeks
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


#DATE RESEARCH
#a fresh set of open days after they turned the last ones down, with the reply offering them
def booking_date_research(state: dict, id: str, turned_down_texts: list[str], last_offered_texts: list[str]) -> tuple:
    #the calendar gets read again, so a day that filled up since the last set never goes out and one that opened up can
    open_date_texts: list[str] = pull_open_dates(state, id)

    research_date_texts: list[str] = []

    #a day they asked for that's open goes out, even one they turned down before
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



#**********DATE ANSWERS**********
#reads their answer to the offered drop off days: a pick, a yes to the job, or something else


#DATE AGREE
#whether they picked one of the offered days, said yes to the job without picking one, or neither
def date_agree_analyzer(state: dict) -> str:
    #the three things their answer to the job and the offered days can be
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


#DATE NOT AGREE
#what their answer is when it picks no day: none work, the job or a price is off, nevermind, or a question
def date_not_agree_analyzer(state: dict) -> str:
    #the five things their answer can be when it doesn't pick a day
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


#PICKED DATE
#the offered day they picked
def picked_date(state: dict, offered_dates: list[str]) -> str:
    #with one day offered, their yes is to that day
    if(len(offered_dates) == 1):
        return offered_dates[0]

    #one choice for each day offered, numbered the same as they were kept with the pending flag
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



#**********DROP OFF DAY**********
#says the day they picked the way the owner would, and works out when the booking comes off file


#DAY ORDINAL
#a day of the month with its st, nd, rd or th
def day_ordinal(day: int) -> str:
    #the 11th, 12th and 13th go by th like the rest of the teens
    if(day % 100 in (11, 12, 13)):
        return f"{day}th"

    suffixes: dict[int, str] = {1: "st", 2: "nd", 3: "rd"}

    return f"{day}{suffixes.get(day % 10, 'th')}"


#PICKED DAY
#offered days are written like Thursday, October 29 with no year, so its year is the one closest to today
def picked_day(drop_off_date: str, shop_today: date) -> date:
    date_parts: list[str] = drop_off_date.split(", ", 1)

    month_day: list[str] = date_parts[1].split(" ")

    month_number: int = datetime.strptime(month_day[0], "%B").month

    picked: date = date(shop_today.year, month_number, int(month_day[1]))

    #a day in January offered in December is next year's, while one that just went by is still this year's
    if((shop_today - picked).days > HALF_YEAR_DAYS):
        picked = picked.replace(year=shop_today.year + 1)

    return picked


#DROP OFF
#the picked day said the way the owner confirms it: just the weekday when it can only be that one, else with its date
def drop_off_day_text(drop_off_date: str, offered_dates: list[str], current_date_time: str) -> str:
    shop_today: date = datetime.strptime(current_date_time, state_form.CURRENT_DATE_TIME_FORMAT).date()

    #every offered day is written like Thursday, October 29, with no year
    date_parts: list[str] = drop_off_date.split(", ", 1)

    weekday: str = date_parts[0]

    month_day: list[str] = date_parts[1].split(" ")

    month_text: str = month_day[0]

    picked: date = picked_day(drop_off_date, shop_today)

    #two days offered on the same weekday, like Friday the 23rd or Friday the 30th, need the day of the month
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

    #its month too when it isn't this month ("Tuesday, November 3rd")
    return f"{weekday}, {month_text} {day_ordinal(picked.day)}"


#CLEAR TIME
#the start of the day a few days after their drop off day in the shop's time, when what they booked comes off file
def booked_clear_time(drop_off_date: str, current_date_time: str) -> datetime:
    shop_today: date = datetime.strptime(current_date_time, state_form.CURRENT_DATE_TIME_FORMAT).date()

    clear_day: date = picked_day(drop_off_date, shop_today) + timedelta(days=BOOKED_KEEP_DAYS)

    return datetime.combine(clear_day, time(0, 0), open_dates.SHOP_TIMEZONE)



#**********CONTACT**********
#gets their name, number and email for the invoice, and reads what they answer instead


#CONTACT VALUES
#the name and the number out of their message, each one empty when they didn't give it
def contact_values(state: dict) -> dict[str, str]:
    user_text: str = state["current_user_message"].get("user_text", "")

    #the shop's last reply goes with it, so a bare "Danny" answering it reads as their name
    shop_last_reply: str = spacing.last_sent_reply(state["message_history"])

    extractor_output: str = models.extract_contact(user_text, shop_last_reply)

    contact: dict[str, str] = {"name": "", "number": ""}

    try:
        values: list[str] = models.extractor_values(extractor_output, ["name", "number"])

        for field_name, value in zip(["name", "number"], values):
            contact[field_name] = value

    #a reply that talks instead of giving the format is never saved, the next reply still asks for what isn't on file
    except Exception as error:
        print(f"CONTACT EXTRACTOR ERROR: {error}")

    return contact


#CONTACT ASK
#offered_dates are the days the pick came out of, empty when it gets asked for again and the day isn't said
def contact_ask_reply(state: dict, id: str, drop_off_date: str, offered_dates: list[str], missing: list[str], reply_before: str) -> str:
    #the services they confirmed by picking the day, saved when the days went out for them
    confirmed_services: dict = log.read_state(f"s_p_confirmed_{id}")

    state_as_text: str = state_form.state_to_text(state)

    #how the day gets said is worked out here, never by the generator, so the day it confirms is the one they picked
    drop_off_day: str = drop_off_day_text(drop_off_date, offered_dates, state["current_date_time"])

    #all three are missing on the first ask
    missing_text: str = json.dumps(missing)

    pricing_text: str = json.dumps(confirmed_services, ensure_ascii=False)

    total: str = services_total(confirmed_services)

    deposit: str = services_deposit(confirmed_services)

    #reply_before is a branch's answer going out first when they asked something instead
    ask_text: str = f"DROP_OFF_DATE: {drop_off_date}\n DROP_OFF_DAY: {drop_off_day}\n MISSING: {missing_text}\n SERVICES_PRICING: {pricing_text}\n TOTAL: {total}\n DEPOSIT: {deposit}\n REPLY_BEFORE: {reply_before}\n STATE: {state_as_text}"

    system_prompt: str = contact_ask.prompt()

    return models.generator("CONTACT ASK GENERATOR", system_prompt, ask_text, CONTACT_MAX_TOKENS, CONTACT_EFFORT, line_breaks=False)


#CONTACT ACK
#the reply that takes in their name, number and email once the drop off day is set
def contact_ack_reply(state: dict, drop_off_date: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    ack_text: str = f"DROP_OFF_DATE: {drop_off_date}\n STATE: {state_as_text}"

    system_prompt: str = contact_ack.prompt()

    return models.generator("CONTACT ACK GENERATOR", system_prompt, ack_text, CONTACT_MAX_TOKENS, CONTACT_EFFORT, line_breaks=False)


#CONTACT ANALYZER
#whether their message gave any of their name, number or email for the invoice
def contact_analyzer(state: dict) -> str:
    #the two things their answer can be
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


#NO CONTACT ANALYZER
#what their message is when it has none of their info: won't give it, getting it, a question, or spam
def no_contact_analyzer(state: dict) -> str:
    #the five things their answer can be when it has none of their info for the invoice
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


#NO CONTACT ACK
#the reply to a message with none of their info, written for the case it is
def no_contact_ack_reply(state: dict, case: str, drop_off_date: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    ack_text: str = f"CASE: {case}\n DROP_OFF_DATE: {drop_off_date}\n STATE: {state_as_text}"

    system_prompt: str = contact_no_info.prompt()

    return models.generator("CONTACT NO INFO GENERATOR", system_prompt, ack_text, CONTACT_MAX_TOKENS, CONTACT_EFFORT, line_breaks=False)



#**********OTHER REPLIES**********
#the replies for a problem, small talk, a phone call ask, them wrapping up and calling off a booking


#ESCALATION
#the ack for a problem with the shop or an ask only a person answers (a deal they saw, a job at the shop, someone selling to it), checked against its rules, and True so a person takes it from here
def escalation_reply(state: dict) -> tuple:
    state_as_text: str = state_form.state_to_text(state)

    #the escalation generator only acknowledges, so it gets no details to answer from
    escalation_text: str = f"STATE: {state_as_text}"

    system_prompt: str = escalation_generator.prompt()

    response: str = models.generator("ESCALATION GENERATOR", system_prompt, escalation_text, ESCALATION_MAX_TOKENS, ESCALATION_EFFORT, line_breaks=False)

    rules: str = escalation_enforcer.instructions()

    regen_prompt: str = escalation_regenerator.prompt()

    reply: str = enforced_reply(state, escalation_text, response, rules, "ESCALATION REGEN", regen_prompt, models.generator, ESCALATION_REGEN_MAX_TOKENS, ESCALATION_REGEN_EFFORT, line_breaks=False, shop_last_reply=None)

    #a problem, a deal they saw, a job at the shop or a sales pitch is never the bot's to answer, so a person takes it from here
    return (reply, True)


#GENERAL TEXT
#the reply to small talk that brings them back to what they need
def general_text_reply(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #small talk needs no details looked up, what it might touch on about the shop is already in its prompt
    general_text: str = f"STATE: {state_as_text}"

    system_prompt: str = general_text_generator.prompt()

    return models.generator("GENERAL TEXT GENERATOR", system_prompt, general_text, GENERAL_TEXT_MAX_TOKENS, GENERAL_TEXT_EFFORT, line_breaks=False)


#HOLD
#a person has them, so what they sent gets taken in and they hear what's still being worked on, never left on read
def hold_reply(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #what's being worked on comes from the shop's last replies in the state, the shop's info is already in its prompt
    hold_text: str = f"STATE: {state_as_text}"

    system_prompt: str = restricted_hold.prompt()

    return models.generator("HOLD GENERATOR", system_prompt, hold_text, HOLD_MAX_TOKENS, HOLD_EFFORT, line_breaks=False)


#PHONE CALL
#the reply giving them the shop's number when they want a call, and True so a person takes it from here
def phone_call_reply(state: dict) -> tuple:
    state_as_text: str = state_form.state_to_text(state)

    #the number and the hours to call in come from the business details in its prompt
    phone_call_text: str = f"STATE: {state_as_text}"

    system_prompt: str = phone_call_ack.prompt()

    response: str = models.generator("PHONE CALL GENERATOR", system_prompt, phone_call_text, PHONE_CALL_MAX_TOKENS, PHONE_CALL_EFFORT, line_breaks=False)

    #they want a person on the phone, so once the number goes out a person takes it from here
    return (response, True)


#END CONVERSATION
#the reply that takes in them wrapping up for now and leaves the door open, with no question so nothing is left for them to answer
def end_conversation_reply(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #they asked nothing, so nothing gets looked up, the shop's info it can't go against is already in its prompt
    end_text: str = f"STATE: {state_as_text}"

    system_prompt: str = end_conversation_ack.prompt()

    return models.generator("END CONVERSATION GENERATOR", system_prompt, end_text, END_CONVERSATION_MAX_TOKENS, END_CONVERSATION_EFFORT, line_breaks=False)


#CONFIRM ACK
#the reply when they call off getting on the books for now, leaving the door open
def pricing_confirm_ack_reply(state: dict) -> str:
    state_as_text: str = state_form.state_to_text(state)

    ack_text: str = f"STATE: {state_as_text}"

    system_prompt: str = pricing_confirm_ack.prompt()

    return models.generator("CONFIRM ACK GENERATOR", system_prompt, ack_text, PRICING_CONFIRM_MAX_TOKENS, PRICING_CONFIRM_EFFORT, line_breaks=False)



#**********COLOR NEWS**********
#tells them the owner can get their color, and reads their pick when he sent the closest materials


#COLOR APPROVED
#reply comes back with the good news worked in, or only the good news when the open days go out right after it
def color_approved_reply(state: dict, reply: str, days_after: bool) -> str:
    state_as_text: str = state_form.state_to_text(state)

    days_text: str = "no"

    if(days_after):
        days_text = "yes"

    #the conversation names the color they sent and the job it's for, so the good news says both the way they would
    color_approved_text: str = f"REPLY: {reply}\n DAYS_AFTER: {days_text}\n STATE: {state_as_text}"

    system_prompt: str = color_approved_generator.prompt()

    #the reply can come in parts, so a line break in what comes back is its own
    return models.generator("COLOR APPROVED GENERATOR", system_prompt, color_approved_text, COLOR_APPROVED_MAX_TOKENS, COLOR_APPROVED_EFFORT, line_breaks=True)


#MATERIAL CRITERION
#the shop asked if the only material it sent works for them, so a yes to it picks it the same as pointing to it
def material_criterion(position: int, material: dict[str, str], count: int) -> str:
    name: str = material.get("name", "")

    if(not name):
        name = "its color not read"

    description: str = material.get("description", "").replace("\n", "; ")

    if(count == 1):
        return f"The customer goes with material 1, {name}, the only pic the shop sent, which shows {description}. The shop asked if that one works for them, so any yes to it picks it: a yes, a bare 'yeah', 'yep' or 'ok' included, 'that works', 'sure', saying they like it ('I like it', 'looks clean'), saying to go ahead with it or do it, a yes to the shop making sure it's the one, or pointing to it ('#1', '1', 'that one'), even when it asks something too, about the wrap or colored PPF itself included"

    ordinal: str = day_ordinal(position)

    return f"The customer picks material {position}, {name}, the {ordinal} pic the shop sent ('#{position}', '{position}', 'the {ordinal} one'), which shows {description}"


#OTHER CRITERION
#an ok only says nothing when more than one was sent, with one it's a yes to it
def other_criterion(count: int) -> str:
    if(count == 1):
        return "The customer neither says yes to the material the shop sent nor turns it down: a question with no yes in it, a maybe, still deciding, a thanks, or anything else. A yes, an ok, saying they like it or going ahead with it is never other, even when it asks something too."

    return "The customer neither picks one of the materials nor turns them all down: a question with no pick in it, a maybe, still deciding, asking which one the shop would go with, a thanks or an ok, or anything else. A message that points to one of them, by its number or where it is in the order ('#1', '2', 'the last one') or by its color or finish, is never other, even when it asks something too."


#MATERIAL PICK
#which of the closest materials they picked (none or other when they didn't), and if they asked something else too
def material_pick(state: dict, materials: list[dict[str, str]]) -> tuple[str, bool]:
    #one choice for each material, numbered in the order the owner sent them, the same way their history notes them
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


#COLOR PICKED
#reply answers what they asked with their pick (empty when the pick is all), picked is the color of the material
def color_picked_reply(state: dict, reply: str, picked: str) -> str:
    state_as_text: str = state_form.state_to_text(state)

    #it comes back with the pick taken in and the schedule question for the job
    color_picked_text: str = f"REPLY: {reply}\n PICKED: {picked}\n STATE: {state_as_text}"

    system_prompt: str = color_picked_generator.prompt()

    #the reply can come in parts, so a line break in what comes back is its own
    response: str = models.generator("COLOR PICKED GENERATOR", system_prompt, color_picked_text, COLOR_PICKED_MAX_TOKENS, COLOR_PICKED_EFFORT, line_breaks=True)

    #the enforcer and the regen get the shop's last reply on its own, so an answer it already gave never goes out again
    shop_last_reply: str = spacing.last_sent_reply(state["message_history"])

    rules: str = color_picked_enforcer.instructions()

    regen_prompt: str = color_picked_regenerator.prompt()

    return enforced_reply(state, color_picked_text, response, rules, "COLOR PICKED REGEN", regen_prompt, models.generator, COLOR_PICKED_REGEN_MAX_TOKENS, COLOR_PICKED_REGEN_EFFORT, line_breaks=True, shop_last_reply=shop_last_reply)
