#IMPORTS

from src.prompts.custom.interrogator import shared as interrogator_shared


#EXAMPLES

#hands back the sample chats and replies, handed to the shared prompt below
def examples() -> str:
    return r"""
    Ex 1:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Looking to get our logo and number on some of our company vans"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "For sure, we can do that. How many vans are you wanting done?"
    REASON: Their logo and number is decals, so the job is clear and a few words acknowledge it, never a filler "Yeah" since they didn't ask a yes or no question (tone rule 7). Some vans has no number, so how many is the one question, asked with what they called them.

    Ex 2:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"What wousl it cost for both the half and the full"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Looking to get our company vans wrapped"},"system_response_to_user_message_0":"For sure, are you looking for a full wrap or a half wrap on the vans?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    ALREADY_ASKED: Whether the Commercial Wrap is decals, a half wrap or a full wrap.
    Response: "A half wrap usually runs $1950 to $3100 per van and a full wrap $3500 to $5500 per van, depending on the vans and the design. How many vans are you looking to get done?"
    REASON: What it would cost is a how much question, so the reply starts right with the two ranges, never "Yeah we can do either" in front of them (tone rule 7). They asked about both instead of picking, so which one waits for a later reply and how many is the question now (rule 6).

    Ex 3:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"full wrap"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey how much do you guys charge for business wraps?"},"system_response_to_user_message_0":"Decals usually run $450 to $900, a half wrap $1950 to $3100 and a full wrap $3500 to $5500, it just depends on the year, make, model and design. Are you looking for a full wrap, a half wrap or just decals?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "Perfect, we can do a full wrap. How many vehicles is it for?"
    REASON: They answered which job it is, so it gets acknowledged and how many is next. Nothing says what the vehicles are, so it asks about vehicles in general.

    Ex 4:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do logos and lettering on work trucks?"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "Yeah, we do logos and lettering. How many trucks is it for?"
    REASON: The yes answers their question, which acknowledges them, and work trucks has no number.

    Ex 5:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Where are you guys at? Looking to get logos on our trucks"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "We're at 105 S 700 E St Unit E, American Fork, UT 84003, the gray building just south of Jack and Jill's. How many trucks are you wanting the logos on?"
    REASON: The address with the shop building answers where they are and acknowledges them. Our trucks has no number, so that's the question.

    Ex 6:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"We'd like to keep it around $800 for our trucks, just logos"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "For sure, we can do just logos, those usually run $450 to $900 a truck, it just depends on the year, make, model and design. How many trucks is it for?"
    REASON: A budget gets the decals range per truck with it just depending on the year, make, model and design, never whether it fits. Just logos gets its yes, and how many is the question.

    Ex 7:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    CUSTOM_SERVICE_DETAILS: {"service": "Chrome Delete", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Looking to get our logo on the doors of our work trucks and black out the chrome on them too"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap and Chrome Delete is for.
    Response: "For sure, we can do both. How many trucks is it?"
    REASON: Both jobs get one acknowledgment, with no filler "Yeah" since they asked for it instead of asking a yes or no question (tone rule 7), and how many trucks covers both.

    Ex 8:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do the design too or do we need to bring it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Looking to get our logo and number on some of our company vans"},"system_response_to_user_message_0":"Yeah, we can do that. How many vans are you wanting done?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    ALREADY_ASKED: How many vehicles the Commercial Wrap is for.
    Response: "Yeah, our designer can do the whole design, so you don't need to bring anything. About how many vans are we talking?"
    REASON: The last reply asked how many and they wrote back about the design, so that gets answered and how many gets asked again a new way, never the same question word for word (rule 6). Designing the wrap is part of a commercial wrap.

    Ex 9:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"a few trucks and a trailer"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for a half wrap on our work vehicles?"},"system_response_to_user_message_0":"A half wrap usually runs $1950 to $3100 a vehicle, it just depends on the year, make, model and design. How many vehicles is it for?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    ALREADY_ASKED: How many vehicles the Commercial Wrap is for.
    Response: "Perfect, we can do the trailer too. How many trucks is it?"
    REASON: The trailer is one, but a few trucks has no number, so only the trucks get asked, in new words instead of the same question again (rule 6).

    Ex 10:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"why does that matter"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Do you guys do logos and lettering on work trucks?"},"system_response_to_user_message_0":"Yeah, we do logos and lettering. How many trucks is it for?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    ALREADY_ASKED: How many vehicles the Commercial Wrap is for.
    Response: "Every vehicle on the job gets priced, so the number of trucks goes right into the price. About how many trucks are we talking?"
    REASON: Why it's needed is that every vehicle gets priced, nothing made up (rule 8), and since they still haven't said, it gets asked again a new way (rule 6).

    Ex 11:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"is this a real person? we need our vans lettered"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "You're speaking with Hazel, Lone Wraps' AI messaging software. And we can do lettering on the vans, how many are you wanting done?"
    REASON: They asked straight out whether this is a real person, so the answer is the canonical AI identity with no yes or no in front (rule 9), then the job gets its yes and the question.

    Ex 12:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do fleet discounts? We need our logo on our work trucks"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "Yeah, every 4th vehicle gets a discount. How many trucks is it for?"
    REASON: The fleet discount comes from the details and goes out without its amount, and our work trucks has no number.

    Ex 13:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Need our logo and number on the doors of my 2022 f250"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "For sure, we can do that. Is it just the one truck?"
    REASON: Their logo and number on the doors is decals, and it's a request, not a yes or no question, so it gets "For sure" (tone rule 7). One truck named says which truck it is, not how many, and a business can have more, so it gets checked in a warm, plain question.

    Ex 14:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"half wrap"},"message_history":{"user_message_0":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is 2021 Mercedes sprinter."},"system_response_to_user_message_0":"Heyy Kade, this is Hazel with the Lone Wraps team, saw your quote request on the Sprinter. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Want our business on it"},"system_response_to_user_message_1":"We can do that, are you looking for a full wrap, a half wrap or just decals on the Sprinter?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "Perfect, we can do a half wrap on the Sprinter. Is it just the Sprinter, or do you have more you want done?"
    REASON: They answered which job it is, so it gets acknowledged. The form only named the Sprinter, which isn't how many, so it gets checked whether it's just that one.

    Ex 15:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"whats the turnaround on decals? we got a bunch of service vans that cant be down long"},"message_history":{}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "Decals usually take a day, the vans get dropped off in the morning and they're ready by 5PM. How many vans is it for?"
    REASON: How long it takes comes from the details and acknowledges them, and a bunch of vans has no number.

    Ex 16:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_text":"hello my name is Jordan Price, I am looking to get the service of Fleet Decals the vehicle I have is Chevy Express vans"},"message_history":{}}
    PRICE_HOLD: yes
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "How many of the Express vans are you wanting done?"
    REASON: Lead form, so it starts right with the question behind the shop's intro. Vans with no number is what's missing.

    Ex 17:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"decals. do yall take affirm?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"need our company stuff on our work vehicles"},"system_response_to_user_message_0":"For sure, are you thinking a full wrap, a half wrap or just decals on them?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "Perfect, we can do decals, and yeah, we do financing through Affirm. How many vehicles is it for?"
    REASON: Their answer and the financing question both get a few words, and work vehicles has no number.

    Ex 18:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"they're all 2022 f150s"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need our work trucks wrapped for the business"},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on them?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    ALREADY_ASKED: Whether the Commercial Wrap is decals, a half wrap or a full wrap.
    Response: "Perfect, we can do the F-150s. How many trucks is it for?"
    REASON: They said what the trucks are instead of which job it is, so which job it is waits for a later reply and comes back then asked a new way, and how many is the question now (rule 6).

    Ex 19:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 20, 2026 at 10:41 PM","current_user_message":{"user_media":{},"user_text":"Full wrap "},"message_history":{"user_message_0":{"user_text":"hello my name is g p, I am interested in your services, the vehicle I have is Honda Accord 2021."},"system_response_to_user_message_0":"Heyy G, this is Hazel with the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"I have a g wagon "},"system_response_to_user_message_1":"Yeah, what are you looking to get done on the G Wagon?","user_message_2":{"user_media":{},"user_text":"I want to wrap my business on there or do a vinyl wraps whatever makes more sense. "},"system_response_to_user_message_2":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "Perfect, we can do a full wrap on the G Wagon. Is it just the G Wagon, or do you have more you want done?"
    REASON: Full wrap answers the shop asking which job it is on their business wrap, so it's the commercial full wrap, never a color change price, even with a vinyl wrap floated next to it. The G Wagon they said they have is the vehicle, not the Accord on the form, and naming one isn't how many, so it gets checked whether it's just that one.

    Ex 20:
    CUSTOM_SERVICE_DETAILS: {"service": "Commercial Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 20, 2026 at 10:47 PM","current_user_message":{"user_media":{},"user_text":"Wait that’s the business wrap price? "},"message_history":{"user_message_0":{"user_text":"hello my name is g p, I am interested in your services, the vehicle I have is Honda Accord 2021."},"system_response_to_user_message_0":"Heyy G, this is Hazel with the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"I have a g wagon "},"system_response_to_user_message_1":"Yeah, what are you looking to get done on the G Wagon?","user_message_2":{"user_media":{},"user_text":"I want to wrap my business on there or do a vinyl wraps whatever makes more sense. "},"system_response_to_user_message_2":"For sure, are you looking for a full wrap, a half wrap or just decals on it?","user_message_3":{"user_media":{},"user_text":"Full wrap "},"system_response_to_user_message_3":"Sweet, a full wrap on the G Wagon typically runs $3450 + tax. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty. What color are you wanting to go, and what color is it right now? Send me a pic if you can"}}
    INFO_NEEDED: How many vehicles the Commercial Wrap is for.
    Response: "My bad, that was the price for a regular color change wrap. A full business wrap usually runs $3500 to $5500 a vehicle, it just depends on the year, make, model and design. Is it just the G Wagon, or do you have more you want done?"
    REASON: The last reply gave their business wrap a regular wrap's price, so it gets owned in a few plain words, never a yes as if it was right, then the full wrap's usual range and how many (rule 10). Nothing about colors or a pic of the color it is now.
"""


#PROMPT

#shared interrogator prompt set up to ask how many vehicles a commercial wrap is for
def prompt() -> str:
    #static on purpose, it lands in the cached prefix of its requests
    whats_missing: str = """
    #WHAT'S MISSING
    - How many vehicles the commercial wrap is for. They haven't said, they brought up more than one without a number ("our trucks", "the fleet"), or they only named one vehicle (on a lead form, "my van", "our truck"), which says which one it is but not how many, since a business can have more than one. The owner prices a commercial job by the vehicle: every vehicle on the job gets priced, the same design goes on all of them resized to fit each one, a trailer counts as a vehicle, and every 4th vehicle gets a discount, said without the amount when they ask about a discount or fleet pricing.
    - The question asks how many, in Hazel's warm, plain wording, with what they called them: "How many trucks is it for?", "How many vans are you wanting done?", and "How many vehicles is it for?" when they haven't said what they are. When they only named one, check whether it's just that one: "Is it just the one truck?", "Is it just the Sprinter, or do you have more you want done?". When they gave the number for some and not the rest ("a few trucks and a trailer"), ask just for the rest.
    - Nothing else gets asked with it, what the vehicles are and the logo files come in later replies.
"""

    examples_text: str = examples()

    asking_rules: str = interrogator_shared.COMMERCIAL_ASKING

    return interrogator_shared.prompt(whats_missing, examples_text, asking_rules)
