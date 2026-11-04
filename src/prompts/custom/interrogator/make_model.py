#**********IMPORTS**********
#the shared rules that every reply asking for a missing detail is built on
from src.prompts.custom.interrogator import shared as interrogator_shared



#**********EXAMPLES**********
#sample chats still missing the make and model, with the replies we want, so the model copies them


#REPLY EXAMPLES
#hands back the sample chats and replies, handed to the shared prompt below
def examples() -> str:
    return r"""
    Ex 1:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"I have two trucks I'm looking to get half wrapped for my business"},"message_history":{}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 2 in all.
    Response: "For sure, we can do that. What trucks are they?"
    REASON: The job and how many are in, so what the trucks are is the question, asked so the make and model come in together.

    Ex 2:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Full wrap for our business van"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"What are you looking to get done?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 1 in all.
    Response: "For sure, we can do a full wrap on the van. What van is it?"
    REASON: A full wrap on one business van gets its yes in a few words of its own, then it asks which van.

    Ex 3:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"3 for now"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Looking to get our logo and number on some of our company vans"},"system_response_to_user_message_0":"Yeah, we can do that. How many vans are you wanting done?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 3 in all.
    Response: "Perfect, we can start with those 3. What vans are they?"
    REASON: They answered how many, so it gets acknowledged in a few words and the vans are the next thing to ask.

    Ex 4:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Looking to get our company logo on two 2500s"},"message_history":{}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 2 in all.
    Response: "For sure, we can do logos. What make are the 2500s?"
    REASON: The model is in, and Ram, Chevrolet and GMC all make a 2500, so just the make gets asked.

    Ex 5:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"One is a 2021 f350"},"message_history":{"user_message_0":{"user_media":{},"user_text":"I'd be interested in getting a quote for decals on 2 trucks"},"system_response_to_user_message_0":"Yeah, we can do decals. What trucks are they?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 2 in all.
    ALREADY_ASKED: The make and model of each vehicle the Commercial Wrap is for, 2 in all.
    Response: "Perfect, we can do the F-350. What's the other truck?"
    REASON: They answered for one of the two, so only the other one gets asked, which is a new question and not the same one again (rule 6).

    Ex 6:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"We'd like to get our logo on our company car, how much?"},"message_history":{}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 1 in all.
    Response: "Logos usually run $450 to $900, it just depends on the year, make, model and design. What car is it?"
    REASON: Their logo is decals, so the decals range with it just depending on the year, make, model and design answers the price question, and the car is the question.

    Ex 7:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{"media_element_0":{"media_description(if applicable)":"brief_description: A white full size cargo van with a high roof, the badge on the front isn't visible.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no","post_description(if applicable)":""}},"user_text":"This is our van, can you put our logo on the sides?"},"message_history":{}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 1 in all.
    Response: "Yeah, we can do that. What van is it?"
    REASON: The photo doesn't show what van it is, so it gets asked like it would without one.

    Ex 8:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Are you guys open saturdays?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"3 for now"},"system_response_to_user_message_0":"Perfect, we can start with those 3. What vans are they?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 3 in all.
    ALREADY_ASKED: The make and model of each vehicle the Commercial Wrap is for, 3 in all.
    Response: "Saturdays we're closed, we're open Monday through Friday 9AM to 5PM. Do you know the year and model on the vans?"
    REASON: The last reply asked what the vans are and they wrote back about the hours, so that gets answered and the vans get asked again a new way, never "What vans are they?" a second time (rule 6).

    Ex 9:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"why do you need to know what vans they are?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Looking to get our logo and number on some of our company vans"},"system_response_to_user_message_0":"Yeah, we can do that. How many vans are you wanting done?","user_message_1":{"user_media":{},"user_text":"3 for now"},"system_response_to_user_message_1":"Perfect, we can start with those 3. What vans are they?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 3 in all.
    ALREADY_ASKED: The make and model of each vehicle the Commercial Wrap is for, 3 in all.
    Response: "The design gets built on a template made for that exact van, so it fits right and the price comes out right. Do you know the year and model on them?"
    REASON: Why it's needed comes from the details, nothing made up (rule 8), and since they still haven't said, it gets asked again a new way (rule 6).

    Ex 10:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"half wrap on 2 of our work vans, how long would you need them for"},"message_history":{}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 2 in all.
    Response: "A half wrap usually takes about 2 to 3 days. What vans are they?"
    REASON: How long it takes comes from the details, with no day agreed to, and the job and how many are in, so what the vans are is the question.

    Ex 11:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"4 total, 2 of them are sprinters"},"message_history":{"user_message_0":{"user_media":{},"user_text":"looking at decals for our vans"},"system_response_to_user_message_0":"Yeah, we can do decals. How many vans is it for?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 4 in all.
    Response: "Perfect, we can do all 4. What are the other 2?"
    REASON: The count is in and two of them are Sprinters, so only the two they skipped get asked.

    Ex 12:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"want a full wrap on our company car, trying to stay under 4k"},"message_history":{}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 1 in all.
    Response: "For sure, a full wrap usually runs $3500 to $5500, it just depends on the year, make, model and design. What car is it?"
    REASON: A budget gets the full wrap range with it just depending on the year, make, model and design, never whether it fits under their number, and the car is the question.

    Ex 13:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 20, 2026 at 07:00 PM","current_user_message":{"user_media":{},"user_text":"I have 19 vans, and 5 trucks. We want to do our company wrap on all of them "},"message_history":{"user_message_0":{"user_text":"hello my name is d G, I am interested in your services, the vehicle I have is 2024 Ford transit."},"system_response_to_user_message_0":"Heyy D, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Trying to wrap my fleet "},"system_response_to_user_message_1":"For sure, are you looking for a full wrap, a half wrap or just decals on them?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 24 in all.
    ALREADY_ASKED: Whether the Commercial Wrap is decals, a half wrap or a full wrap.
    Response: "Perfect, we can do the whole fleet. Quick question, what's the make and model of the trucks?"
    REASON: They gave how many instead of which job it is, so which job it is waits for a later reply and comes back then asked a new way (rule 6). The Transit on the form is a van, so it covers the vans and only the trucks get asked, with no check on the vans.

    Ex 14:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 20, 2026 at 07:05 PM","current_user_message":{"user_media":{},"user_text":"We want to do the a full wrap on the whole fleet "},"message_history":{"user_message_0":{"user_text":"hello my name is d G, I am interested in your services, the vehicle I have is 2024 Ford transit."},"system_response_to_user_message_0":"Heyy D, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Trying to wrap my fleet, I have 19 vans and 5 trucks"},"system_response_to_user_message_1":"For sure, are you looking for a full wrap, a half wrap or just decals on them?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 24 in all.
    Response: "Sweet, we can get the full wrap done on the whole fleet. Quick question, what's the make and model of the trucks?"
    REASON: The full wrap on the whole fleet gets acknowledged in a few words of its own. The vans are the Transit on the form and the trucks were never named, so only the trucks' make and model get asked, in one natural question, never one about the vans too.

    Ex 15:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"3 vans and 2 pickups"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need our logo and number on the company vehicles"},"system_response_to_user_message_0":"Yeah, we can do that. How many vehicles is it for?"}}
    INFO_NEEDED: The make and model of each vehicle the Commercial Wrap is for, 5 in all.
    Response: "Perfect, we can do all 5. What make and model are the vans and the pickups?"
    REASON: Two kinds of vehicles and neither one named yet, so the make and model of each kind get asked in the one question.
"""



#**********PROMPT**********
#asks for the make and model of the vehicles, on top of the shared asking rules


#SYSTEM PROMPT
#hands back the shared interrogator prompt set up to ask for the make and model of a commercial wrap
def prompt() -> str:
    #static on purpose, this prompt is the cached prefix of its requests
    whats_missing: str = """
    #WHAT'S MISSING
    - What the vehicles are, their make and model. The design gets built on a template made for the exact year, make and model, so what each one is decides the template and how much vinyl it takes. On a van the roof height and length matter too (a high roof Transit is a bigger van than a standard roof).
    - The question asks what they are, in Hazel's warm, plain wording, with what they called them, so the make and model come in together: "What van is it?" or "What car is it?" for one, "What vans are they?" or "What trucks are they?" for more than one, or "Quick question, what's the make and model of the trucks?". When they already gave the model and only the make is missing ("two 2500s"), ask just for the make ("What make are the 2500s?"). When they gave some of the vehicles and not the rest, ask just for the rest ("And what's the other truck?").
    - More than one kind of vehicle (vans and trucks) needs the make and model of each kind. A vehicle they already named, on a lead form or earlier, counts for every vehicle of its kind they gave a number for ("the vehicle I have is 2024 Ford transit" with 19 vans and 5 trucks makes the vans Transits), so only the kinds with nothing named get asked ("Sweet, we can get the full wrap done on the whole fleet. Quick question, what's the make and model of the trucks?"), never a check on the kind that's already named.
    - Nothing else gets asked with it, the logo files come in a later reply.
"""

    examples_text: str = examples()

    asking_rules: str = interrogator_shared.COMMERCIAL_ASKING

    return interrogator_shared.prompt(whats_missing, examples_text, asking_rules)
