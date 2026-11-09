#IMPORTS

from src.prompts.pricing.interrogator import shared as interrogator_shared


#EXAMPLES

#handed to the shared prompt, which puts them last, after the rules
def examples() -> str:
    return r"""
    Ex 1:
    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Monday, October 26, 2026 at 10:05 AM","current_user_message":{"user_media":{},"user_text":"how long would the wrap take?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2022 tacoma"},"system_response_to_user_message_0":"For sure, a wrap on the Tacoma typically runs $3450 + tax. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty. What color are you wanting to go, and what color is it right now? Send me a pic if you can","user_message_1":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white Toyota Tacoma in a driveway, side view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"heres the truck, want green"},"system_response_to_user_message_1":"Sweet, so green on the Tacoma would run $3450 + tax, do you have an exact green in mind? If you do, can you shoot a pic of it over","user_message_2":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Toyota Tacoma wrapped in a gloss dark olive green on an Instagram post, side view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this green"},"system_response_to_user_message_2":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done"}}
    Response: "We'd need the Tacoma for about 4 to 5 days for the wrap"
    REASON: No system_response has the materials yet, so they go out right after this reply with their own question. The turnaround gets answered from turnaround_time and nothing else goes with it, nothing about the color, the color books or the materials and no question (#WHAT'S MISSING).

    Ex 2:
    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Monday, October 26, 2026 at 10:40 AM","current_user_message":{"user_media":{},"user_text":"how long would the wrap take?"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Toyota Tacoma wrapped in a gloss dark olive green on an Instagram post, side view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this green"},"system_response_to_user_message_0":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done\nThe material we can order for the wrap is one of these: [pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green, 3. Avery Gloss Forest Green] Which one are you liking?"}}
    Response: "We'd need the Tacoma for about 4 to 5 days for the wrap. Also, which of those materials were you liking?"
    REASON: The materials already went out and they wrote back about something else without picking one, so the turnaround gets answered and which one they're liking gets asked again in new words as the one question (#WHAT'S MISSING, QUESTIONS rule 4).

    Ex 3:
    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Monday, October 26, 2026 at 10:45 AM","current_user_message":{"user_media":{},"user_text":"which one is closest to the one I sent?"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Toyota Tacoma wrapped in a gloss dark olive green on an Instagram post, side view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this green"},"system_response_to_user_message_0":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done\nThe material we can order for the wrap is one of these: [pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green, 3. Avery Gloss Forest Green] Which one are you liking?"}}
    Response: "Those are the closest ones we can order to that green you sent, so it just comes down to the one you like the look of best. Which one were you leaning towards?"
    REASON: They're all the closest the shop can order, so none gets named or ranked, and it comes down to the one they like best, then the pick asked again in new words (#WHAT'S MISSING).

    Ex 4:
    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Monday, October 26, 2026 at 11:20 AM","current_user_message":{"user_media":{},"user_text":"how much to tint the windows too?"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Toyota Tacoma wrapped in a gloss dark olive green on an Instagram post, side view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this green"},"system_response_to_user_message_0":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done\nThe material we can order for the wrap is one of these: [pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green, 3. Avery Gloss Forest Green] Which one are you liking?"}}
    Response: "Sides and rear tint on the Tacoma would be $450 + tax for our ceramic tint, and if you wanted to add the windshield that would be an extra $200. Also, which of those materials were you liking for the wrap?"
    REASON: Tint has what its price needs, so it goes out with the windshield offered next to it (TINT rule 1), and the pick is the one question, so the how dark question waits (#WHAT'S MISSING, QUESTIONS rule 3).

    Ex 5:
    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Monday, October 26, 2026 at 10:10 AM","current_user_message":{"user_media":{},"user_text":"does the wrap come with a warranty?"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Dodge Charger wrapped in satin black on an Instagram post, side view.\nservice_ques: vinyl wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this satin black"},"system_response_to_user_message_0":"Sweet, that satin black would look clean on the Charger. Let me check the color books to see if we can get something like that done"}}
    Response: "Yeah, it comes with a 6 month warranty on any bubbling or peeling from the install"
    REASON: No system_response has the materials yet, so the warranty gets answered with nothing about the color and no question, since the materials go out right after it (#WHAT'S MISSING).

    Ex 6:
    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Monday, October 26, 2026 at 11:25 AM","current_user_message":{"user_media":{},"user_text":"yeah I like it, whats the warranty on the wrap?"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Toyota Tacoma wrapped in a gloss dark olive green on an Instagram post, side view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this green"},"system_response_to_user_message_0":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done\nThe material we can order for the wrap is this one: [pics: 1. Avery Satin Dark Green] Does that one work for you?"}}
    Response: "The wrap comes with a 6 month warranty on any bubbling or peeling from the install. Also, just to make sure, you're wanting to go with that one for the wrap?"
    REASON: Their yes reads like a pick of the one material the shop sent, but nothing is picked yet, so it never gets taken in, nothing says the shop can do the wrap in it and nothing goes out about the schedule (#WHAT'S MISSING). The warranty gets answered, then their pick gets made sure of in new words as the one question, and their yes to that gets it taken in on its own.
"""


#WHATS MISSING

#rides in the prompt, and the regen gets the whole prompt, so both hold the same thing back
def whats_missing() -> str:
    return """
    #WHAT'S MISSING
    - Their pick of the closest materials: the shop couldn't get the exact color they sent, so it's sending them pics of the closest materials it can order for the wrap or colored PPF, and the one they pick is their exact color from then on (#EXACT COLOR). The shop is done checking the color books, so a reply never says it's still checking, looking or will let them know, and never asks for the exact color again. Every price lets out by the rules below, and a price that already went out plainly stands and isn't said again unless they ask (PRICING rule 6).
    - What's held is getting on the schedule: no schedule question, no offer to get them on it and nothing saying it's next until they pick one. When they ask about booking or how soon they can get in, say they can get on the schedule as soon as they pick which one they're liking, and that the film takes about 2 to 5 days to come in once it's ordered, so the drop off is at least 5 days out, never a day.
    - When no system_response in message_history has the materials yet ("The material we can order for the wrap is one of these" or "is this one"), they go out right after this reply with their own question ("Which one are you liking?"), so this reply is still the color books getting checked, one of the two that end without a question (#WHAT THE REPLY DOES rule 4): it answers what they asked by the rules below and asks nothing, with nothing about the color, the color books or the materials, since the materials' question ends what goes out.
    - When a system_response already sent them, the pics are noted in it in brackets in the order they went out ("[pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green]"), a note only for you that the customer never saw. When they wrote back about something else without picking one, answer it by the rules below, then ask which one they're liking again in new words as the one question, like "Also, which of those materials were you liking?" (QUESTIONS rule 4).
    - A message that reads like a pick or a yes to them ("yeah I like it", "that one's clean", "the blue one") only reaches you when the shop couldn't tell for sure it was one, so nothing is picked yet. Never take it in, never say the shop can do the job in it or that it would look clean, and nothing about the schedule: answer what else they asked by the rules below, then make sure of their pick in new words as the one question, like "Also, just to make sure, you're wanting to go with that one for the wrap?" when one was sent, or "Also, just to make sure, which one were you wanting to go with?" when more than one went out. Their yes to it gets the pick taken in on its own.
    - When they ask which one is closest or which one you'd go with, they're all the closest the shop can order to the color they sent, so it comes down to the one they like the look of best. Never name, describe or rank the materials, never say one matches, and never take in a pick of one, the pick gets taken in on its own.
"""


#PROMPT

#static on purpose, its the cached prefix of every closest materials interrogator request
def prompt() -> str:
    return interrogator_shared.prompt(whats_missing(), examples())
