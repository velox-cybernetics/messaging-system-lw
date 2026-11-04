#**********IMPORTS**********
#the shared rules that every reply asking for a missing detail is built on
from src.prompts.custom.interrogator import shared as interrogator_shared



#**********EXAMPLES**********
#sample chats still missing the vehicle model, with the replies we want, so the model copies them


#REPLY EXAMPLES
#hands back the sample chats and replies, handed to the shared prompt below
def examples() -> str:
    return r"""
    Ex 1:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Need lettering on my ford for my plumbing business"},"message_history":{}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Ford.
    Response: "For sure, we can do lettering. Which Ford is it?"
    REASON: The make is in, so the model is the question, asked with the make they gave.

    Ex 2:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"all chevys"},"message_history":{"user_message_0":{"user_media":{},"user_text":"We need our logo on our work trucks"},"system_response_to_user_message_0":"Yeah, we can do logos. How many trucks is it for?","user_message_1":{"user_media":{},"user_text":"4"},"system_response_to_user_message_1":"Perfect, we can do all 4. What trucks are they?"}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Chevrolet.
    ALREADY_ASKED: The model of each vehicle the Commercial Wrap is for, makes on file: Chevrolet.
    Response: "Perfect, we can do the Chevys. What model are they?"
    REASON: They answered part of what the trucks are, so only the model they skipped gets asked, a new question and not the same one again (rule 6).

    Ex 3:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"I need a quote for full wraps on 2 trailers"},"message_history":{}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Trailer.
    Response: "For sure, we can do full wraps on those. How big are the trailers?"
    REASON: A trailer's size is what's missing, so that's the question, asked plainly and naturally.

    Ex 4:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Im looking to get a full wrap on my food truck"},"message_history":{}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Food Truck.
    Response: "For sure, we can do that. How big is the food truck?"
    REASON: A food truck with no make is sized like a trailer, so its size is the question.

    Ex 5:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"We'd like a full wrap on our trailer for the gym"},"message_history":{}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Trailer.
    Response: "For sure, we can do that. Do you know the trailer dimensions?"
    REASON: The trailer's size is what's missing, asked the other plain, natural way.

    Ex 6:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"One is a 6x12"},"message_history":{"user_message_0":{"user_media":{},"user_text":"I need a quote for full wraps on 2 trailers"},"system_response_to_user_message_0":"Yeah, we can do full wraps on those. How big are the trailers?"}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Trailer.
    ALREADY_ASKED: The model of each vehicle the Commercial Wrap is for, makes on file: Trailer.
    Response: "Perfect, we can do the 6x12. How big is the other one?"
    REASON: They gave the size of one of the two, so only the other one gets asked, a new question and not the same one again (rule 6).

    Ex 7:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"do you guys take card?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need lettering on my ford for my plumbing business"},"system_response_to_user_message_0":"Yeah, we can do lettering. Which Ford is it?"}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Ford.
    ALREADY_ASKED: The model of each vehicle the Commercial Wrap is for, makes on file: Ford.
    Response: "Yeah, any card or cash works. Do you know the model on the Ford, like an F-150 or a Transit?"
    REASON: The last reply asked which Ford and they wrote back about paying, so that gets answered and the model gets asked again a new way, never "Which Ford is it?" a second time (rule 6).

    Ex 8:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"does the size really matter?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"I need a quote for full wraps on 2 trailers"},"system_response_to_user_message_0":"Yeah, we can do full wraps on those. How big are the trailers?"}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Trailer.
    ALREADY_ASKED: The model of each vehicle the Commercial Wrap is for, makes on file: Trailer.
    Response: "Yeah, a bigger trailer takes a lot more vinyl and design, so the size goes right into the price. Do you know roughly how long and tall they are?"
    REASON: Why the size matters is what the price depends on, with no number (rule 8), and since they still haven't said, it gets asked again a new way (rule 6).

    Ex 9:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"need a full wrap on the box truck for my moving company"},"message_history":{}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Box Truck.
    Response: "For sure, we can do that. How long and tall is the box truck?"
    REASON: A box truck with no make goes by its size, so the length and height are the question.

    Ex 10:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"its an isuzu"},"message_history":{"user_message_0":{"user_media":{},"user_text":"just want our logo and number on our truck, only the one"},"system_response_to_user_message_0":"Yeah, we can do that. What truck is it?"}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Isuzu.
    ALREADY_ASKED: The model of each vehicle the Commercial Wrap is for, makes on file: Isuzu.
    Response: "Perfect, we can do the Isuzu. Which model is it?"
    REASON: They gave the make, so only the model they skipped gets asked, a new question and not the same one again (rule 6).

    Ex 11:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How long does the design take? Need lettering on my dodge for the HVAC business"},"message_history":{}}
    INFO_NEEDED: The model of each vehicle the Commercial Wrap is for, makes on file: Dodge.
    Response: "The design and printing usually take about a week before the install. Which Dodge is it?"
    REASON: How long the design takes comes from the details and acknowledges them, and the make is in, so the model is the question.
"""



#**********PROMPT**********
#asks for the model of the vehicles when we only have the make, on top of the shared asking rules


#SYSTEM PROMPT
#hands back the shared interrogator prompt set up to ask for the model when only the make is on file
def prompt() -> str:
    #static on purpose, this prompt is the cached prefix of its requests
    whats_missing: str = """
    #WHAT'S MISSING
    - The model of the vehicles. They said the make, written in INFO_NEEDED, and the design gets built on a template made for that exact model, so the model decides the template and how much vinyl it takes, with the trim or roof height when they give it (Transit 250, Sprinter High Roof). A trailer, or a box truck or food truck with no make, goes by its size in place of a model, the length and the height, so for those its size is what's missing.
    - The question asks for the model, in Hazel's warm, plain wording, with the make they gave: "Which Ford is it?", "What model are the Chevys?". For a trailer, a box truck or a food truck it asks how big it is: "How big are the trailers?", "Do you know the trailer dimensions?", "How long and tall is the food truck?". When they gave some of the models or sizes and not the rest, ask just for the rest ("And how big is the other one?").
    - More than one kind of vehicle gets the model of each kind in the one question ("What models are the Fords and the Chevys?"), and a kind whose model is already in, like the Transit on a lead form for their vans, never gets asked again.
    - Nothing else gets asked with it, the logo files come in a later reply.
"""

    examples_text: str = examples()

    asking_rules: str = interrogator_shared.COMMERCIAL_ASKING

    return interrogator_shared.prompt(whats_missing, examples_text, asking_rules)
