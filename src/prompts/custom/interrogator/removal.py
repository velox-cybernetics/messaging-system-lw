#**********IMPORTS**********
#the shared rules that every reply asking for a missing detail is built on
from src.prompts.custom.interrogator import shared as interrogator_shared



#**********EXAMPLES**********
#sample removal chats still missing a photo or the film's age, with the replies we want


#REPLY EXAMPLES
#hands back the sample chats and replies, handed to the shared prompt below
def examples() -> str:
    return r"""
    Ex 1:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can you guys take the old wrap off my 2019 camaro? its peeling pretty bad"},"message_history":{}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the Wrap Removal.
    Response: "Yeah, we can take the old wrap off. How long has it been on, and do you have a photo of it?"
    REASON: Taking an old wrap off is a job the shop does, so it gets a yes. Both are missing, so both go in one natural question.

    Ex 2:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"are you guys open saturdays?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need the old wrap off my 2018 charger, its cracking all over the roof"},"system_response_to_user_message_0":"For sure, we can take the old wrap off. How long has it been on, and do you have a photo of it?"}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the Wrap Removal.
    Response: "Saturdays we're closed, we're open Monday through Friday 9AM to 5PM. Any idea how long it's been on there, and could you shoot me a pic of it when you get a sec?"
    REASON: The hours get answered, and both were asked last reply and still missing, so they get asked again as one question in new words, never "How long has it been on, and do you have a photo of it?" a second time (rule 6).

    Ex 3:
    CUSTOM_SERVICE_DETAILS: {"service": "PPF Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"The clear bra on my hood is yellowing and peeling pretty bad, can you guys take it off and put a new front end on?"},"message_history":{}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the PPF Removal.
    Response: "Yeah, we can take the old film off and put a new front end on. How long has it been on, and do you have a photo of it?"
    REASON: Taking old PPF off is a job the shop does, so it gets a yes. The new front end gets priced with it, so no number, and both are missing, so both go in the one question.

    Ex 4:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Hey whats up I was wondering what you guys would charge to re wrap my 2020 model 3, the wrap on it is old and peeling everywhere. Its matte black right now, want to go gloss white"},"message_history":{}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the Wrap Removal.
    Response: "For sure, we can take the old wrap off and do gloss white. How long has the old wrap been on, and do you have a photo of it?"
    REASON: The new wrap gets priced together with taking the old one off, so no number goes out for either.

    Ex 5:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much do you guys charge to take off a wrap? its on my 2018 f150"},"message_history":{}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the Wrap Removal.
    Response: "It depends on how long it's been on and the shape it's in. How long has it been on, and do you have a photo of it?"
    REASON: What the price depends on answers the price question with no number, and it's why both get asked.

    Ex 6:
    CUSTOM_SERVICE_DETAILS: {"service": "PPF Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"the old ppf on the front of my 2024 m4 is cracked and yellow, can you take it off before you wrap it?"},"message_history":{}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the PPF Removal.
    Response: "Yeah, we can take the old film off before the wrap goes on. How long has it been on, and do you have a photo of it?"
    REASON: They want the old film taken off, so it's a job the shop does and gets a yes, and the wrap gets priced with it, so no number. PPF that's only going under the wrap never comes here, it's treated just like the paint.

    Ex 7:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{"media_element_0":{"media_description(if applicable)":"brief_description: A Jeep Wrangler in a faded, chalky olive green wrap, with the vinyl cracked across the hood.\nservice_ques: wrap removal\ntext_overlays: none\nbright_vehicle: no","post_description(if applicable)":""}},"user_text":"this is my jeep, the wrap is shot. can you take it off?"},"message_history":{}}
    INFO_NEEDED: How long it's been on, for the Wrap Removal. The photo is on file.
    Response: "Yeah, we can take it off. How long has the wrap been on?"
    REASON: The photo came with their message, so how long it's been on is the only question.

    Ex 8:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"like 4 years"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Can you guys take the old wrap off my 2019 camaro? its peeling pretty bad"},"system_response_to_user_message_0":"Yeah, we can take the old wrap off. How long has it been on, and do you have a photo of it?"}}
    INFO_NEEDED: A photo of it as it is now, for the Wrap Removal. How long it's been on is on file: About 4 years.
    Response: "Perfect, that helps us know what we're working with. Mind shooting me a quick pic of it as it is now?"
    REASON: They answered how long it's been on, so the photo is the only part left, asked in new words instead of the "do you have a photo of it?" the last reply used (rule 6). How long it's been on is what tells how much work it is, so saying that acknowledges them plainly, with nothing said about the wrap they haven't shown yet.

    Ex 9:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Would taking the wrap off my accord mess up the paint underneath?"},"message_history":{}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the Wrap Removal.
    Response: "If the paint's in good shape it usually comes through fine, it's paint that was already failing under the wrap that can come up with it. How long has it been on, and do you have a photo of it?"
    REASON: The paint question gets answered from the wrap removal's details, then both get asked.

    Ex 10:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"why do you need to know how long its been on?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to get the old wrap off my wrangler"},"system_response_to_user_message_0":"It depends on how long it's been on and the shape it's in. How long has it been on, and do you have a photo of it?"}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the Wrap Removal.
    Response: "An older wrap usually takes more work to come off, so it helps us get the price right. Any idea how long it's been on there, and could you snap a pic of it for me?"
    REASON: Why it's needed is what the price depends on, nothing made up (rule 8), and since they still haven't given either, both get asked again, reworded instead of the same question the last reply asked (rule 6).

    Ex 11:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"not sure honestly, it came on the truck when I bought it. ill grab a pic tonight"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need the wrap on my f150 taken off, its fading bad"},"system_response_to_user_message_0":"Yeah, we can take the old wrap off. How long has it been on, and do you have a photo of it?"}}
    INFO_NEEDED: A photo of it as it is now, for the Wrap Removal. How long it's been on is on file: Not sure, it was on when they bought the truck.
    Response: "No worries, send it over whenever you get the chance."
    REASON: Not knowing how long is a fine answer, and they're getting the photo, so it isn't asked again, a few words acknowledging them does it (rule 6).

    Ex 12:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can you take the wrap off my hood and put ppf on instead? its a 2021 bmw m3"},"message_history":{}}
    INFO_NEEDED: How long it's been on and a photo of it as it is now, for the Wrap Removal.
    Response: "Yeah, we can take the wrap off and put PPF on. How long has the wrap been on, and do you have a photo of it?"
    REASON: PPF is a regular service asked with the removal, so it gets priced with it and gets no number here.

    Ex 13:
    CUSTOM_SERVICE_DETAILS: {"service": "Wrap Removal", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Its been on about 3 years, can I send you pics here?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need the old wrap taken off my tacoma before I sell it"},"system_response_to_user_message_0":"Yeah, we can take the old wrap off. How long has it been on, and do you have a photo of it?"}}
    INFO_NEEDED: A photo of it as it is now, for the Wrap Removal. How long it's been on is on file: About 3 years.
    Response: "Perfect, that helps us know what we're working with, and yeah, send them over here."
    REASON: The 3 years answers the shop's ask, so it gets taken in, and their question is them offering the photo, so the yes answers it and asks for it at the same time.
"""



#**********PROMPT**********
#asks how long the old film or wrap has been on and for a photo of it, with the shared asking rules


#SYSTEM PROMPT
#hands back the shared interrogator prompt set up to ask about the old film or wrap coming off
def prompt() -> str:
    #static on purpose, this prompt is the cached prefix of its requests
    whats_missing: str = """
    #WHAT'S MISSING
    - How long the old PPF or wrap on the vehicle now has been on, and a photo of it as it is now. How long it's been on and the shape it's in decide how much work it is to take off, so the owner prices it from both.
    - INFO_NEEDED says which of the two is still missing. When both are, they go in the same question, in Hazel's warm, plain wording: "How long has it been on, and do you have a photo of it?" When only one is, the question asks just for that one: "How long has it been on?" or "Do you have a photo of it as it is now?"
    - Not knowing how long it's been on, or not having a photo, is a fine answer, never push for one.
    - When they just answered one of the two, acknowledge it plainly and warmly, never judging how old it is or the shape it's in before the owner sees it ("Perfect, that helps us know what we're working with"), then ask for the other one.
    - Nothing else gets asked with it.
"""

    examples_text: str = examples()

    asking_rules: str = interrogator_shared.PHOTO_ASKING

    return interrogator_shared.prompt(whats_missing, examples_text, asking_rules)
