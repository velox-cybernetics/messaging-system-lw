#**********IMPORTS**********
#the shop details, booking info and typo notes that get added to the check
from src.prompts import shared



#**********EXAMPLES**********
#sample messages that show when the shop's service info can answer them and when it can't


#EXAMPLES
#go in last, after the shop details, so the checker sees which messages its info can and can't answer
def examples() -> str:
    return r"""
    #Examples
    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do ceramic coating?"},"message_history":{}}
    answer: False
    REASON: Ceramic coating has its own details now, the regular reply asks for the vehicle (false case 4).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_text":"hello my name is Kade Smith, I am looking to get the service of Window Tint the vehicle I have is 2010 Infiniti G37x sedan"},"message_history":{}}
    answer: False
    REASON: The lead form names tint, and the tint details have it, so the regular reply asks which windows (false case 4).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is 2010 Infiniti G37x sedan."},"message_history":{}}
    answer: False
    REASON: A website form names no service, so SERVICE_DETAILS has every service because nothing was asked yet, not because they asked about all of them. The regular reply asks which service they want (false case 9).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Hey can I get a quote on my car?"},"message_history":{}}
    answer: False
    REASON: No service is named yet, the regular reply asks what they want done (false case 9).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much would you guys charge for my 2022 silverado?"},"message_history":{}}
    answer: False
    REASON: A vehicle but no service, so nothing specific is being asked yet. The regular reply asks what they want done (false case 9).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Thats my old truck, I have a 2023 tundra now"},"message_history":{"user_message_0":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is 2019 ram 1500."},"system_response_to_user_message_0":"Heyy Kade, this is Hazel at the Lone Wraps team, saw your quote request on the Ram. What are you looking to get done?"}}
    answer: False
    REASON: They're correcting the vehicle from the form, and the vehicle can change at any point, so the regular reply just goes on with the Tundra and asks which service they want on it (false case 14).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Oh wait wrong car, its for my 2021 accord not the civic"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2019 civic, its grey, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Civic would run $2950 plus tax for a full wrap, and we take it apart for full coverage of the vehicle, it does also come with a free 6 month warranty."}}
    answer: False
    REASON: Switching to another vehicle is still the wrap they asked about, so the regular reply adjusts to the Accord and goes on from there (false case 14).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"What services yall offer"},"message_history":{}}
    answer: False
    REASON: They ask about the services in general, and SERVICE_DETAILS has every service to answer it from (false case 9).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do powder coating?"},"message_history":{}}
    answer: True
    REASON: Every service is in SERVICE_DETAILS, but none of them is powder coating, so nothing answers it (true case 1).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much to wrap my ram?"},"message_history":{}}
    answer: False
    REASON: wrap_price has it, the regular reply just asks for the year and colors first (false case 4).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How thick is the vinyl you guys use?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2019 audi a4, its grey, want gloss white"},"system_response_to_user_message_0":"Sweet, so gloss white on the A4 would run $2950 plus tax for a full wrap, and we take it apart for full coverage of the vehicle, it does also come with a free 6 month warranty."}}
    answer: False
    REASON: film_thickness has it.

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Sweet. Will it hold up going through a brush car wash?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"It's white, wanting gloss black"},"system_response_to_user_message_0":"Sweet, so gloss black on the Ram would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want, it also comes with a 6 month warranty."}}
    answer: False
    REASON: How a wrap holds up in a brush car wash is general knowledge about vinyl, not something only the shop knows, so the regular reply answers it (false case 12).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much to wrap my 2018 camaro in gold chrome? its yellow right now"},"message_history":{}}
    answer: True
    REASON: price_difference_material only has chrome on a truck, so chrome on a car has no price.

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Hey whats up I was wondering what you guys would charge to re wrap my 2020 model 3, the wrap on it is old and peeling everywhere. Its matte black right now, want to go gloss white"},"message_history":{}}
    answer: False
    REASON: Taking the old wrap off is not in SERVICE_DETAILS, but the wrap price is, so the regular reply prices the wrap and looks into the removal (false case 5).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"2019 mustang gt, its red, want matte black. Can you guys do PPF on the front bumper too?"},"message_history":{}}
    answer: False
    REASON: PPF on the front bumper with no word that they only want that piece gets the closest coverage, the front end (partials), and the vehicle and colors for the wrap quote are covered, so the regular reply gives the wrap price and points the bumper to the front end price (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Just need PPF on the front rock chip areas."},"message_history":{}}
    answer: False
    REASON: The front rock chip areas are the front end, and coverage_front_end and ppf_price have it (false case 4).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Does it come with a warranty? Also do you guys do ceramic coating by itself?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2018 4runner, its silver, want gloss black"},"system_response_to_user_message_0":"Sweet, so gloss black on the 4Runner would run $3450 plus tax for a full wrap, and we take it apart for full coverage of the vehicle, it does also come with a free 6 month warranty."}}
    answer: False
    REASON: The wrap's warranty has it, and the coating on its own is in ceramic_price (false case 4).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Hey guys! What would you charge to wrap just the cab of my truck?"},"message_history":{}}
    answer: False
    REASON: An unlisted partial, the regular reply asks for a photo (false case 6).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Thats more than I was expecting, can you do any better on it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    answer: False
    REASON: Pushback on the price, the price stands (false case 7).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Looking for a full wrap and window tinting"},"message_history":{}}
    answer: False
    REASON: Tint asked for with a wrap is the full ceramic tint add on in add_ons.

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"It's white, wanting gloss black"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Looking for a quote to wrap a 2024 ram 1500"},"system_response_to_user_message_0":"What color are you wanting to go, and could you send a pic of it?"}}
    answer: False
    REASON: Answers the shop's question for the wrap quote (false case 8).

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a gray Toyota 4Runner parked in a driveway, front three quarter view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":""},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for colored ppf on my 2022 4runner?"},"system_response_to_user_message_0":"Yeah, we can do colored PPF on the 4Runner. Could you send a pic of it?"}}
    answer: False
    REASON: A pic of their vehicle with no text answers the shop's pic request for the colored PPF quote (false case 8).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Friday, October 16, 2026 at 09:31 PM","current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a glossy metallic red McLaren P1 supercar, three quarter front view, parked on a brick paver driveway.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: yes"}},"user_text":"This is her 🫠🫠🫠 Love that car more than my\nWife and kids And I’d kill for them So better not fuck my shit up 😡😡 Jk 😂 My baby "},"message_history":{"user_message_0":{"user_text":"hello my name is Damien Walker, I am interested in your services, the vehicle I have is mclaren p1."},"system_response_to_user_message_0":"Heyy Damien, this is Hazel at the Lone Wraps team, saw your quote request on the P1. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"What’s the warranty? Colored PPF "},"system_response_to_user_message_1":"Colored PPF comes with a lifetime warranty on anything that fails, bubbles or peels due to the install, road damage isn't covered. Could you send a pic of the P1?","user_message_2":{"user_media":{},"user_text":"That makes sense. Yeah let me take one real quick. "},"system_response_to_user_message_2":"Sounds good, send it over whenever you're ready."}}
    answer: False
    REASON: The pic of their P1 is the one the shop asked for to price the colored PPF, and the rest is jokes about how much they love the car and a warning to take care of it, which ask for nothing (false case 8).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Powder coating"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Can you guys do my wheels on my 2021 camry?"},"system_response_to_user_message_0":"Not sure on that one, do you mean wrapping the wheels or powder coating them? Let me look into that for you."}}
    answer: True
    REASON: The short reply answers the shop's question about something it said it would look into, so it is still not covered (true case 3).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Sounds good, how do I get on the schedule?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 kia k5, its grey, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the K5 would run $2950 plus tax for a full wrap, and we take it apart for full coverage of the vehicle, it does also come with a free 6 month warranty."}}
    answer: False
    REASON: Wanting to book, the regular reply handles that (false case 8).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do PPF?"},"message_history":{}}
    answer: False
    REASON: PPF has SERVICE_DETAILS now, the regular reply asks front end or full body and the vehicle (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much for PPF on my ram?"},"message_history":{}}
    answer: False
    REASON: ppf_price has it, the regular reply just asks front end or full body first (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can PPF go over the wrap I already have on my 2021 model 3?"},"message_history":{}}
    answer: False
    REASON: ppf_over_wrap has it.

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Just looking to have my headlights ppfd"},"message_history":{}}
    answer: False
    REASON: partials answers it: the headlights are part of the front end, so the regular reply points it to the front end price (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How does the automatic car wash affect Ppf?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Mat PPF on my 2024 model 3"},"system_response_to_user_message_0":"Full body matte PPF on the Model 3 would be $6400 plus tax, matte runs $500 over the clear film."}}
    answer: False
    REASON: The regular reply answers how the film holds up in a car wash with a small inference from SERVICE_DETAILS (durable, double the thickness of a vinyl wrap, self healing, edges tucked), so it is covered (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can I take my car through a brush car wash after you put the clear bra on?"},"message_history":{}}
    answer: False
    REASON: Unlike a wrap, how PPF holds up in a brush car wash is answered with a small inference from SERVICE_DETAILS (durable, self healing, edges tucked), so it is covered (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can I use my own material? Ppf"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full matte ppf on my 2023 tahoe"},"system_response_to_user_message_0":"Full body matte PPF on the Tahoe would be $7400 plus tax, matte runs $500 over the clear film."}}
    answer: True
    REASON: SERVICE_DETAILS says nothing about customer supplied PPF, only a wrap has a customer_material field.

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Im thinking ppf But have opf on it So can you remove it"},"message_history":{"user_message_0":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is 2021/toyota/camry."},"system_response_to_user_message_0":"Heyy Kade, this is Hazel at the Lone Wraps team, saw your quote request on the Camry. What are you looking to get done?"}}
    answer: True
    REASON: Saying PPF only answers which service, it asks nothing SERVICE_DETAILS answers. The one thing they ask is whether the shop can take the old PPF already on it off, and SERVICE_DETAILS has nothing on that (true case 2).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Im thinking ppf, but it has old ppf on it. How much to take that off and put new on?"},"message_history":{"user_message_0":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is 2021/toyota/camry."},"system_response_to_user_message_0":"Heyy Kade, this is Hazel at the Lone Wraps team, saw your quote request on the Camry. What are you looking to get done?"}}
    answer: False
    REASON: They ask the price, and ppf_price has it once the coverage is known. Taking the old film off has no price, so the regular reply gives the price for the new film (false cases 4 and 5).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Full body ppf, can you take the old ppf off first?"},"message_history":{"user_message_0":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is 2023/toyota/rav4."},"system_response_to_user_message_0":"Heyy Kade, this is Hazel at the Lone Wraps team, saw your quote request on the RAV4. What are you looking to get done?"}}
    answer: False
    REASON: Full body is the coverage, so with the RAV4 from the form the regular reply has the price and gives it for the new film, since taking the old film off has no price (false case 5).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Ppf"},"message_history":{"user_message_0":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is 2022/honda/accord."},"system_response_to_user_message_0":"Heyy Kade, this is Hazel at the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?"}}
    answer: False
    REASON: Answers the shop's question with the service and asks nothing else, the regular reply asks front end or full body (false case 8).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much pof "},"message_history":{"user_message_0":{"user_text":"hello my name is Gabriel doe, I am interested in your services, the vehicle I have is mclaren 570s 2021."},"system_response_to_user_message_0":"Heyy Gabriel, this is Hazel at the Lone Wraps team, saw your quote request on the 570S. What are you looking to get done?"}}
    answer: False
    REASON: "pof" is a typo for PPF, the o sits right next to the p, so they're asking what PPF runs on the 570S from the form, and ppf_price has it (false case 4). A misspelled service is still that service, never a service with no SERVICE_DETAILS (true case 1).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Mainly interested in the paint protection film and ceramic coat for the whole vehicle, its a 2023 tahoe"},"message_history":{}}
    answer: False
    REASON: The full body price is in ppf_price and the coating on top of PPF is in ceramic_price, so both parts are covered (false case 4).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Well I'm deciding on a vinyl wrap or the ceramic coating protective film"},"message_history":{"user_message_0":{"user_text":"hello my name is tristan walker, I am interested in your services, the vehicle I have is 2026 Tesla model Y."},"system_response_to_user_message_0":"Heyy Tristan, this is Hazel at the Lone Wraps team, saw your quote request on the Model Y. What are you looking to get done?"}}
    answer: False
    REASON: A ceramic coating protective film mixes up the coating and PPF, and both have details, so the regular reply clears up that they're two different things and answers the wrap against them (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Is this your 50% off quote as per the ad?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Can you give me quote for full front and full body on my 2024 model 3. Don't want to change the color"},"system_response_to_user_message_0":"Front end PPF on the Model 3 is $1600 plus tax and full body is $5900 plus tax, both clear so the color stays the same."}}
    answer: False
    REASON: An old promo they bring up, the price stands (false case 7).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"I was between full stealth ppf or like a nardo grey wrap, its a 2021 bmw m340i, its black"},"message_history":{}}
    answer: False
    REASON: Both services have details, the full body satin PPF price and the wrap price are both there.

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do colored ppf?"},"message_history":{}}
    answer: False
    REASON: Colored PPF has its own details, the regular reply asks for the vehicle (false case 4).

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"What would colored ppf run on my 2022 bmw x5?"},"message_history":{}}
    answer: False
    REASON: color_ppf_price has the full body price for an SUV (false case 4).

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can you do colored ppf on just the hood of my 2023 camry?"},"message_history":{}}
    answer: False
    REASON: partials has no colored price for a single panel, but the full body covers the hood and has a price, so the regular reply points it there (false case 4).

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you have colored ppf in nardo grey?"},"message_history":{}}
    answer: False
    REASON: colors_offered answers it with the colored PPF book to look through in the shop (false case 4).

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much to take the old wrap off my 2020 model 3 and do colored ppf?"},"message_history":{}}
    answer: False
    REASON: Taking the wrap off has no price, but the colored PPF install does, so the regular reply prices the new film (false case 5).

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"What would you charge to install a colored ppf kit I already bought?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Colored ppf on my 2023 tacoma"},"system_response_to_user_message_0":"Sweet, so colored PPF on the Tacoma would run $7400 plus tax for the full body, which covers all the painted surfaces, and we clay bar your truck and give it a decontamination wash beforehand. It also comes with free side and rear window tint. What color were you thinking?"}}
    answer: True
    REASON: customer_material says they can bring their own kit and pay for labor, but there's no labor number, and the labor price is all they asked (true case 2).

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Is there a deposit to get started on the colored ppf?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Colored ppf on my 2023 tacoma"},"system_response_to_user_message_0":"Sweet, so colored PPF on the Tacoma would run $7400 plus tax for the full body, which covers all the painted surfaces, and we clay bar your truck and give it a decontamination wash beforehand. It also comes with free side and rear window tint. What color were you thinking?"}}
    answer: False
    REASON: #BOOKING DETAILS has the 20% deposit for every regular job, colored PPF included, so it's covered (false case 11).

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Colored ppf on my 2024 tahoe, and do you guys do ceramic coating too?"},"message_history":{}}
    answer: False
    REASON: color_ppf_price has the colored price and the coating details have the coating, so the regular reply prices both (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Does the ppf heal itself if it gets scratched?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Front end ppf on my 2024 audi a5"},"system_response_to_user_message_0":"Front end PPF on the A5 is $1600 plus tax, that covers the full hood, fenders, bumper, headlights and mirrors."}}
    answer: False
    REASON: self_healing has it.

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"What is your address so i can see samples? In person"},"message_history":{}}
    answer: False
    REASON: The address is in #BUSINESS DETAILS and the samples are the color books in colors_offerd (false case 11).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"When it’s time to remove the film will it damage my paint? "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Looking for a color change but I also want protection for my car "},"system_response_to_user_message_0":"Colored PPF is exactly that, it changes the color like a wrap and protects the paint like PPF. On the Model Y it's $6400 plus tax for the full body, which covers all the painted surfaces, we clay bar your car and give it a decontamination wash beforehand, and it comes with free side and rear window tint. What color were you thinking?"}}
    answer: False
    REASON: The film coming off down the road and whether that hurts the paint is in removal (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"And if I ever want it off down the road can you guys take it off? What would that run?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full body ppf on my 2023 bmw x5"},"system_response_to_user_message_0":"Sweet, so full body PPF on the X5 would run $6900 plus tax, which covers all the painted surfaces, and we clay bar your car and give it a decontamination wash beforehand. Did you want to hop on the schedule?"}}
    answer: False
    REASON: They're only asking about later on, and removal answers it with pictures first, then a price (false case 4). Wanting old film that's on the car now taken off would still be true case 2.

    SERVICE_DETAILS: {"service": "Colored Paint Protection Film", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can you apply this over my current ceramic coating? "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Colored ppf on my 2023 tacoma"},"system_response_to_user_message_0":"Sweet, so colored PPF on the Tacoma would run $7400 plus tax for the full body, which covers all the painted surfaces, and we clay bar your truck and give it a decontamination wash beforehand. It also comes with free side and rear window tint. What color were you thinking?"}}
    answer: False
    REASON: A coating already on their paint is in existing_ceramic_coating, unlike getting a ceramic coating done (false case 4).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do tint?"},"message_history":{}}
    answer: False
    REASON: The tint details have it, the regular reply asks for the vehicle and the windows first (false case 4).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can you guys tint my headlights? Or do you do house windows?"},"message_history":{}}
    answer: False
    REASON: headlight_taillight_tint and not_offered answer both, the shop doesn't do them, and saying so is an answer (false case 4).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can you take the old tint off my front windows and put a lighter one on?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"You guys tinted my 2019 corolla last month"},"system_response_to_user_message_0":"Glad you're liking it."}}
    answer: False
    REASON: Unlike old PPF or an old wrap, taking old tint off has a price in the tint removal field (false case 4).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"I got quoted $300 for a full tint at another shop, can you match that?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Sides and rear on my 2021 civic"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint. Did you want to hop on the schedule?"}}
    answer: False
    REASON: Pushback on the price, price_policy says the price stands (false case 7).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"If I post you guys on my tiktok can you do the tint for free?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Sides and rear on my 2021 civic"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint. Did you want to hop on the schedule?"}}
    answer: False
    REASON: Asking for it free is pushback on the price whatever the reason, and free_policy says nothing is ever given for free (false case 7).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Is there a deposit to hold the spot for the tint?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Sides and rear on my 2021 civic"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint. Did you want to hop on the schedule?"}}
    answer: False
    REASON: #BOOKING DETAILS has the 20% deposit for every regular job, tint included, so it's covered (false case 11).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can I bring my own tint film and just pay you guys to install it?"},"message_history":{}}
    answer: True
    REASON: The tint details say nothing on customer supplied film or a labor price for it (true case 2).

    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"whats the difference between ir and uv"},"message_history":{}}
    answer: False
    REASON: A general knowledge question about how tint works, nothing specific to the shop, so the regular reply answers it (false case 12).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"What's your quote on a 2025 tesla model 3 for a ceramic coating?"},"message_history":{}}
    answer: False
    REASON: ceramic_price has the coating on its own (false case 4).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much do you charge for a 3 year ceramic coating?"},"message_history":{}}
    answer: False
    REASON: durability and ceramic_price have it, the regular reply just asks for the vehicle first (false case 4).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Is that with the ceramic coating?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    answer: False
    REASON: The coating on top of a wrap is in ceramic_price (false case 4).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much for ceramic on my 2021 camry?"},"message_history":{}}
    answer: False
    REASON: Ceramic could be the coating or tint, and the regular reply asks which one they mean, with the coating details there to answer from once it's the coating (false case 4).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you do undercoating?"},"message_history":{}}
    answer: False
    REASON: not_offered answers it, the shop doesn't do undercoating, and saying so is an answer (false case 4).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"My paint has some swirls and light scratches, will the coating take care of those?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"What's your quote on a 2025 tesla model 3 for a ceramic coating?"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the Model 3 would run $700 plus tax, that covers all the painted surfaces and the coating lasts for years."}}
    answer: False
    REASON: prep and paint_correction answer it, the coating seals in whatever is on the surface and doesn't hide scratches, and minor things get a little extra prep first (false case 4).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do a paint correction before the coating?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"What's your quote on a 2025 tesla model 3 for a ceramic coating?"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the Model 3 would run $700 plus tax, that covers all the painted surfaces and the coating lasts for years."}}
    answer: False
    REASON: paint_correction answers it, it isn't done on its own, it's a little extra prep for minor things as part of the prep before the coating (false case 4).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"How much for a paint correction and ceramic coating on my 2022 tacoma?"},"message_history":{}}
    answer: False
    REASON: ceramic_price has the coating and paint_correction says the correction is part of the prep, not a job of its own, so both parts are covered (false case 4).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you do ceramic coatings for wheels by chance?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"What's your quote on a 2025 tesla model 3 for a ceramic coating?"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the Model 3 would run $700 plus tax, that covers all the painted surfaces and the coating lasts for years."}}
    answer: True
    REASON: coverage_other_surfaces has the headlights, taillights, fender flares and hardtops, nothing on the wheels, and that's all they asked (true case 2).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Is there a deposit for the coating?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"What's your quote on a 2025 tesla model 3 for a ceramic coating?"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the Model 3 would run $700 plus tax, that covers all the painted surfaces and the coating lasts for years."}}
    answer: False
    REASON: #BOOKING DETAILS has the 20% deposit for every regular job, a ceramic coating included, so it's covered (false case 11).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can you guys do mobile ceramic coatings? Might have a job for u"},"message_history":{}}
    answer: False
    REASON: #BUSINESS DETAILS says the shop isn't mobile, the vehicle gets brought in, so it's answered (false case 11).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Ok. I’ll have to pass for now on the ceramic coating.  I’m trying to figure out a ride for the drop off.  I’m excited!"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey how much would it cost to wrap a 2022 Tesla model y? Its white, thinking satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Model Y would run $2800 plus tax for a full wrap, and we take it apart for full coverage of the vehicle, it does also come with a free 6 month warranty.","user_message_1":{"user_media":{},"user_text":"Can you put a ceramic coating on it too?"},"system_response_to_user_message_1":"Yeah, we offer a 50% off ceramic coating on top of a vinyl wrap, the coating lasts for years and it gets the wrap closer to 7 years instead of 5 or 6. Did you want that added on?"}}
    answer: False
    REASON: Passing on the add on is an objection that asks for nothing new (false case 15), and the drop off is in #BOOKING DETAILS (false case 11).

    SERVICE_DETAILS: {"service": "Ceramic Coating", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys do paint correction?"},"message_history":{}}
    answer: False
    REASON: paint_correction answers it, it isn't done on its own, it's part of the prep before a coating, PPF or wrap, and saying so is an answer (false case 4).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Will you need to do a paint correction before wrapping it? It has some swirls"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    answer: False
    REASON: The wrap's paint_correction answers it, minor things get a little extra prep before the wrap goes on (false case 4).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"ok and what is that with tax?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 kia k5, its grey, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the K5 would run $2950 plus tax for a full wrap, and we take it apart for full coverage of the vehicle, it does also come with a free 6 month warranty."}}
    answer: False
    REASON: The tax is in SERVICE_DETAILS, 7.45% Utah sales tax on top of the price, so the regular reply works out the exact total with tax (false case 13).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Ok I will pass on the window tint and go somewhere else for that"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for front end ppf and tint on the sides and rear of my 2023 accord?"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Accord would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and ceramic tint on the sides and rear is $450 on top.","user_message_1":{"user_media":{},"user_text":"Does the ppf come with a warranty?"},"system_response_to_user_message_1":"Yeah, lifetime warranty on any bubbling or peeling from the install."}}
    answer: False
    REASON: Turning down the tint and getting it somewhere else is an objection, it asks for nothing the shop has to look up, so the regular reply takes it in stride and goes on with the PPF (false case 15).

    SERVICE_DETAILS: every service the shop offers, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"nvm we're gonna go with someone local for the vans"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need our logo and phone number on 3 work vans"},"system_response_to_user_message_0":"Yeah, we can do that. What vans are they, and could you send over the logo?"}}
    answer: False
    REASON: Calling off a job the details don't price is still an objection, nothing is being asked, so the regular reply takes it in stride (false case 15).

    SERVICE_DETAILS: {"service": "Vinyl Wrap", "service_details": {...}}
    STATE: {"current_date_time":"Wednesday, October 28, 2026 at 03:05 PM","current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a dark red Honda Civic Si sedan in gloss paint, side view, parked in a driveway. The hood and both doors have hazy, faded patches where the clear coat is failing.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"It is red. What do you guys do about clear coat failure?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2017 civic si"},"system_response_to_user_message_0":"For sure, a wrap on the Civic Si typically runs $2950 + tax, it just depends on what color it is right now, and we take it apart for full coverage of the vehicle, it does also come with a free 6 month warranty. What color is it right now? Send me a pic if you can"}}
    answer: False
    REASON: The pic is the one the shop asked for, and existing_paint with the sanding peeling paint add on answers the clear coat failure, worked out with logic for what a wrap does over it (false case 4).

    SERVICE_DETAILS: {"service": "Paint Protection Film", "service_details": {...}}
    SERVICE_DETAILS: {"service": "Window Tint", "service_details": {...}}
    STATE: {"current_date_time":"Wednesday, October 28, 2026 at 04:30 PM","current_user_message":{"user_media":{},"user_text":"can i do the full body\ncan you tint my side markers and lights too"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much for ppf on my 2026 huracan"},"system_response_to_user_message_0":"Front end PPF on the Huracan would run $2080 + tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and the full body would run $7670 + tax, which covers all the painted surfaces, and we clay bar your car and give it a decontamination wash beforehand. The full body also comes with free side and rear window tint. Which option are you leaning towards?"}}
    answer: False
    REASON: Picking the full body is a go ahead on a job the shop priced, and headlight_taillight_tint answers the side markers and lights, the shop doesn't tint them, and saying so is an answer (false cases 4 and 8).
"""



#**********CHECK PROMPT**********
#puts together the check that spots messages the shop's service info can't answer at all


#INSTRUCTIONS
#the shop's details and typo notes go in with the rules, so the check knows everything the shop can answer
def instructions() -> str:
    instructions_text: str = """
    #How To Answer
    -Answer True only when NOTHING in current_user_message can be handled from SERVICE_DETAILS: everything they ask for has no answer there and no false case fits. If ANY part of the message is covered, a question SERVICE_DETAILS answers, the vehicle or colors for a wrap quote, a new or corrected vehicle, a go ahead, answer False even when another part is not covered. The regular reply handles the covered part and leaves the rest out. Thanks, compliments and small talk next to an uncovered question are not a covered part. Neither is just saying which service they want when all they ask about it has no answer, even when it answers the shop's "which service" question: in "Im thinking ppf But have opf on it So can you remove it" the only thing asked is taking the old PPF off (true case 2). Once they also ask the price or give what it still needs (the coverage, the colors), the regular reply prices the new film or wrap, so it is false case 5. With nothing else asked, just the service is false case 8.
    -Small talk, jokes, emojis, venting and warnings to take good care of their vehicle ("this is her", "love that car more than my wife and kids", "better not mess it up", "jk", "my baby") ask for nothing, so they are never something SERVICE_DETAILS has no answer for and never make the answer True on their own. A message that's only that, or that plus what the shop asked for (a pic or video of their vehicle, the vehicle, the colors), is false case 8.
    -SERVICE_DETAILS is everything the shop knows about the services the customer is asking about, one JSON object per line. When the message is about the services in general or names no service, it has every service the shop offers.
    -Every service being in SERVICE_DETAILS is never a reason for False on its own. When they name a service or ask something specific to the shop that none of it answers, it's still True.
    -STATE is the conversation. current_user_message is what the customer just sent, message_history holds the earlier turns oldest first (user_message_N is an earlier customer message, system_response_to_user_message_N is the shop's reply to it). Read the current message in light of the history. A short reply ("Powder coating", "2023", "yes") answers whatever the shop asked last, so it belongs to that topic.
    -Go through every part of current_user_message before answering. Anything specific to this shop (whether it offers something, a price, a brand, a time frame, a policy like a deposit or bringing their own material) is judged only by what is written in SERVICE_DETAILS and in #BUSINESS DETAILS and #BOOKING DETAILS below, never by whether the shop could probably figure it out: not written there means not known. A question the regular reply can work out with logic from what is written there plus trade knowledge is covered, like what a wrap does over failing clear coat from existing_paint (false case 4), and a general knowledge question that doesn't depend on this shop is covered by general knowledge (false case 12).
    -#BUSINESS DETAILS and #BOOKING DETAILS below are what the regular reply knows on top of SERVICE_DETAILS, so a question they answer counts as covered (false case 11).

    #True Cases (only when nothing else in the message is covered)
    1. They ask about a service with no SERVICE_DETAILS: paint, body work, detailing, powder coating, bedliners, or anything else not covered. A lead form that names one of these counts. A ceramic coating has its own details now, and a paint correction is in the wrap, PPF, colored PPF and coating details, so they only count here when none of those details are in SERVICE_DETAILS.
    2. They ask about the wrap, PPF, colored PPF, tint or a ceramic coating, but SERVICE_DETAILS says nothing on the thing they want to know. For a wrap: a specialty film with no price for their vehicle (chrome on a car) or taking an old wrap off. Failing clear coat or peeling paint under the wrap is not this, existing_paint and the sanding peeling paint add on answer it. For PPF: taking old PPF that's on the vehicle now off, bringing their own film, or a specific brand the shop doesn't list (XPEL). A PPF partial (headlights only, hood only, bumper only, doors, bedsides, tailgate) is not this, partials answers it. How PPF holds up in a car wash is not this either, the regular reply answers it with a small inference from the film's details. For colored PPF: taking an existing wrap or old film off on its own, the labor price to install their own kit, a brand other than the one in material, or colored PPF on something that isn't a car or truck body (wheels, side by sides). Colored PPF on just the front end or a single panel is not this, the regular reply points it to the full body price, and neither is whether a certain color is available, colors_offered answers it with the color book. The PPF or colored PPF coming off down the road is not this either: whether it can come off later, whether that hurts the paint, who should take it off, or what the shop would charge to take it off then, removal answers it (pictures first, then a price). Wanting old film or a wrap that's on the vehicle now taken off still is this, removal is only about later on. A ceramic coating already on their paint and rock chips under the film are not this, existing_ceramic_coating and prep answer them. For tint: bringing their own tint film. Taking old tint off is not this, the tint removal field prices it, and neither are shades, tint laws, headlight, taillight, side marker or other light tint, home or mobile tint, the tint details answer them. For a ceramic coating: coating the wheels (coverage_other_surfaces only has the headlights, taillights, fender flares, hardtops and the glass), or bringing their own coating for the shop to put on. Whether the coating hides scratches, what it protects against, how long it lasts, its brand, warranty, cure time, aftercare, undercoating, coating the trim or what the trim costs (coverage_other_surfaces says the trim doesn't get coated), coating the windows or the glass, what that costs, or whether what the shop said it covers takes the windows in ("does that include the windows?", "what about the windows?", coverage_other_surfaces and ceramic_price say the glass isn't part of the coating but can be coated for $150 more for all the windows), or a coating already on their paint before a wrap are not this, the coating details answer them. A paint correction or buffing, on its own or before a wrap, PPF, colored PPF or a coating, is never this, paint_correction answers it (it isn't done on its own, it's a little extra prep for minor things as part of the prep). A deposit is never this for any of them, #BOOKING DETAILS has the 20% deposit for every regular job (false case 11). This holds when the same message also says which service they want, as long as it doesn't ask the price or give what the price still needs (false case 5).
    3. Their short reply answers a question the shop asked while clearing up something it said it would look into.

    #False Cases
    4. SERVICE_DETAILS has the answer, even when the customer still has to give the vehicle, colors, PPF coverage (front end, full body, windshield), the windows for tint, or the vehicle for a ceramic coating first. The regular reply just asks for them.
    5. The message mixes a part that falls under the true cases with a part covered by SERVICE_DETAILS or another false case, like a wrap quote plus detailing, a coating quote plus coating the wheels, or a colored PPF quote plus installing their own kit. The regular reply answers the covered part and leaves the rest out.
    6. A wrap job with no listed price that the regular reply asks a photo for: an unlisted partial like just the cab, a trailer, damage or rust. Peeling paint or failing clear coat under a wrap isn't even that, existing_paint and the sanding peeling paint add on answer it (false case 4).
    7. Pushback on a price: asking for a discount, an old quote or an old promo, or asking for anything for free, for any reason (a threat, a hardship, a post or review, a bundle, or just asking). The price in SERVICE_DETAILS stands, free_policy says nothing is ever given for free, and the regular reply says so.
    8. The message asks for nothing new: it gives what the shop asked for a wrap, PPF, colored PPF, tint or ceramic coating quote (a vehicle, a color, a pic or video of their vehicle with no text or with small talk, jokes, emojis or a warning to take care of it, "front end", "full, colored", the windows, "coating", "yes"), says thanks or makes small talk, or says they want to go ahead or book.
    9. No service is named yet ("can I get a quote on my car", a website lead form with only the vehicle), or they ask about the services in general ("what services do you offer", "what else do you do"). SERVICE_DETAILS has every service, and the regular reply answers from it and asks what they want done.
    10. They ask who they're talking to, or whether this is a bot, AI or a real person.
    11. They ask about the shop itself or booking and #BUSINESS DETAILS or #BOOKING DETAILS answers it, like where the shop is, the hours, financing, the deposit, or coming by to look through the color books.
    12. They ask a general knowledge question that doesn't depend on what this shop offers, charges or does: how something works or what it means, like the difference between IR and UV, what nano ceramic is, or how vinyl holds up in a brush car wash. The regular reply answers it from general knowledge. Whether the shop offers something, its prices and its policies are never general knowledge.
    13. They ask about the tax: how much it is, why there's tax, the total with tax or out the door, or what a plus tax price comes to ("which is what?"). The prices in SERVICE_DETAILS say the tax is 7.45% Utah sales tax and how to work it out, so the regular reply gives the exact number.
    14. They change or correct their vehicle, at any point in the conversation, even when it doesn't answer what the shop just asked ("I don't have a transit I have a McLaren P1", "wrong car, its for my wife's tahoe", "actually its a 2021 accord not the civic"). The vehicle a customer has can change, and that's never something SERVICE_DETAILS has no answer for, so the regular reply just goes on with the new one: it asks which service they want on it, or gives the price for it, the same as if they had named it first.
    15. They turn down or push back on a service, an option or an add on that came up in the conversation, whatever service or job it is: passing on it or skipping it, going somewhere else or with another shop for it, not wanting it or not being interested anymore, holding off on it, or that it costs more than they want to spend or isn't worth it to them ("Ok I will pass on the window tint and go somewhere else for that", "nah ill skip the chrome delete, thats too much", "found someone cheaper, thanks anyway"). That's an objection, it asks for nothing the shop has to look up, so the regular reply takes it in stride and goes on with whatever else they're still getting.

    #Answer
    -True: nothing in the message has an answer in SERVICE_DETAILS and no false case fits.
    -False: SERVICE_DETAILS answers any part of it, or any false case fits.
    -In the examples service_details is shortened to {...}, and "every service the shop offers, one per line" stands for all of them, you get the full JSON.
"""

    instructions_text += shared.business_details()

    instructions_text += shared.booking_details()

    instructions_text += shared.typos()

    instructions_text += examples()

    return instructions_text
