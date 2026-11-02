#**********EXAMPLES**********
#sample messages for each kind of text the router sorts, so it learns which reply chain gets it


#SERVICE PRICING
SERVICE_PRICING_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Looking for a quote to wrap a 2024 ram 1500"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Hey can I get a quote on my car?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Color change"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Full wrap.  Currently white. Wanting to do a matte black."},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Whats a full wrap run on my 2016 tesla model s? Its wrapped white right now, want satin black"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"How much for a Tesla Y in gun metal grey satin?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Do you guys do tint"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"how much does it cost for a full wrap, if i buy the wrap myself"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Is the price 2800 for any vehicle?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"2019 chrysler 300 full wrap"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey can I get a quote on my car?"},"system_response_to_user_message_0":"Yes, what are you looking to get done and what car is it?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Black"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yo yo, how much for a wrap on my 2023 raptor"},"system_response_to_user_message_0":"What color is it currently and what color are you wanting to go?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"How long does a wrap last"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full matte black on my 2021 Tacoma, its red now"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"ok cool, where can i see what colors/textures you guys offer?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey how much would it cost to wrap a 2022 Tesla model y? Its white, thinking satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Model Y would run $2800 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Does it comes with any warranty?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Ok cool thanks"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Can I get my 2020 civic tinted this week?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"I want to book a full wrap on my 2022 tacoma, its white and I want satin black"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Which one would you go with?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for ppf on my 2023 accord"},"system_response_to_user_message_0":"Front end on the Accord would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 plus tax. Which option are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_text":"hello my name is Kade Smith, I am looking to get the service of Vinyl Wraps the vehicle I have is 2010 Infiniti G37x sedan"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is 2010 Infiniti G37x sedan."},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Can I swing by the shop to see wrap colors"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yall open today"},"system_response_to_user_message_0":"Yeah, we're open today until 5PM."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Can I come by and look at the colored ppf colors?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Whats colored ppf run on a 2024 tahoe?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What is your address so i can see samples? In person"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"is 20% legal on the front windows in utah?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Can I come by and look at the tint shades before I pick one?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"4 doors and the back glass"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic"},"system_response_to_user_message_0":"Which windows are you wanting tinted?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What about a windshield brow"},"message_history":{"user_message_0":{"user_media":{},"user_text":"It’s green now. I want it black satin"},"system_response_to_user_message_0":"Sweet, so satin black on the F150 would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty.","user_message_1":{"user_media":{},"user_text":"Ok do you tint also?"},"system_response_to_user_message_1":"Yeah, we do ceramic tint. Sides and rear on the F150 would run $450 on top of the wrap, done in the same visit, and if you wanted to add the windshield that would be an extra $200.","user_message_2":{"user_media":{},"user_text":"Ok I want 5% all around"},"system_response_to_user_message_2":"5% is no problem on the rear windows and back glass, but we only go as dark as 20% on the front two, so a lot of people do 20% on the front two and 5% on the rear. The windshield only goes 70% or 50% if you wanted that too."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"whats the difference between ir and uv"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What's your quote on a 2025 tesla model 3 for a ceramic coating?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Is that with the ceramic coating?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"How long does the ceramic coating last and does it need to cure?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"What's your quote on a 2025 tesla model 3 for a ceramic coating?"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the Model 3 would run $700 plus tax, that covers all the painted surfaces and the coating lasts for years."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Does that cover the mirrors and the door jambs?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"How much extra to tint my headlights and tail lights"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How long will it take and when do you have an opening?"},"system_response_to_user_message_0":"It’s 4-5days for a full wrap, right now we can start the week of the 28th"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What's your warranty like? And do you guys cut around emblems and protective pieces or would you remove those and then put them on over the wrap?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Oof I'll have to look at some options then. Is there a great brand that you prefer and could last 10+ years so I can look at the color."},"system_response_to_user_message_0":"Vinyl wouldn’t last 10 years. You’d probably see more like 5 to 6 years out of it. We use 3M and Avery Dennison"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What parts would need to come off Cause it’s an expensive car Do you guys have insurance? In case you mess up a piece "},"message_history":{"user_message_0":{"user_media":{},"user_text":"It’s white It’s my baby Car cost me 2.1 million Have you guys ever worked on a McLaren? Senna "},"system_response_to_user_message_0":"Sweet, so red on the Senna would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want. Yeah, we've worked on high end cars, the owner does every install himself."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"How long would you need it? And you guys are insured right?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 bmw m3, its blue, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the M3 would run $2950 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What are your hours? Also do you do ceramic coating?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Wheres the shop at? Also how much is ppf on the front of a 2023 bronco"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Depends on the price, I have a couple trucks I want done"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to wrap my 2023 raptor"},"system_response_to_user_message_0":"What color is it currently and what color are you wanting to go?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What do yall do over there?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What type of work does your shop do?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Do you guys just do tint or other stuff too?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Got any deals going on?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a glossy red Porsche 911 at a car show, front three quarter view, with dark tinted windows, and a car wrapped in a chrome purple film behind it.\nservice_ques: window tint on the red car; the chrome purple car in the back points to a chrome wrap\ntext_overlays: none\nbright_vehicle: yes"}},"user_text":"here she is, thinking satin black "},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2020 911?"},"system_response_to_user_message_0":"Sweet, we can do that. What color is the 911 right now?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a red Ram 1500 in a driveway, side view, with chrome bumpers, a chrome grille and chrome door handles.\nservice_ques: the chrome bumpers, grille and door handles point to a chrome delete\ntext_overlays: none\nbright_vehicle: yes"}},"user_text":""},"message_history":{"user_message_0":{"user_media":{},"user_text":"Wanting a quote on a full wrap for my 2020 ram 1500, thinking matte black"},"system_response_to_user_message_0":"Sweet, what color is the Ram right now?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white Kia Telluride, front view, with a long scratch on the front bumper.\nservice_ques: the scratch on the bumper points to touch up paint\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"This is the car, how much for full front ppf?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description(if applicable)":"brief_description: A satin dark grey SUV parked outside a shop.\nservice_ques: Vinyl wrap color change.\ntext_overlays: none\nbright_vehicle: no","post_description(if applicable)":"Satin dark grey on this Tahoe, full wrap by Lone Wraps #lonewraps #wrap"}},"user_text":"I would like to put that color on my car"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a gray sedan, rear three quarter view, with very dark tint on the side windows and the back glass.\nservice_ques: window tint\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"all of them, this dark"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2022 camry"},"system_response_to_user_message_0":"Which windows are you wanting tinted?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white Ford F-250 work truck, side view, with a company logo and phone number on the door.\nservice_ques: a commercial wrap or decals\ntext_overlays: Peak Roofing, (801) 555-0123\nbright_vehicle: no"}},"user_text":""},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint the windows on our work truck?"},"system_response_to_user_message_0":"Yeah, we can do that. What truck is it?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a gray Dodge Charger in a parking lot, side view, with blacked out badges and a carbon fiber spoiler.\nservice_ques: blacked out badges; a carbon fiber piece\ntext_overlays: none\nbright_vehicle: no"},"media_element_1":{"media_description":"brief_description: A photo of a Dodge Challenger wrapped in gloss purple, front three quarter view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"thats mine, and this is the color i want"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a blue Porsche sports car with a contrasting dark gray hood section, black wheels, black side accents and script lettering on the door, parked on grass at an outdoor car show with many other cars and people in the background. A person leans over the windshield taking a photo, and the crest badge on the hood makes it a Porsche, with a large rear wing at the back.\nservice_ques: a hood piece in its own color, possibly a specialty carbon fiber film\ntext_overlays: RS24 UFO\nbright_vehicle: no"}},"user_text":"Thats it Ams thinking purple I am* "},"message_history":{"user_message_0":{"user_text":"hello my name is Gabriel Walker, I am interested in your services, the vehicle I have is Porche 9111 gt3rs 2025."},"system_response_to_user_message_0":"Heyy Gabriel, this is Hazel at the Lone Wraps team, saw your quote request on the 911 GT3 RS. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Looking for window tint and a wrap "},"system_response_to_user_message_1":"Yeah, we can do both. A wrap on the GT3 RS typically runs $2950 plus tax, it just depends on what color it is right now, and our ceramic tint on the sides and rear is $300+tax since it's a 2 door, and if you wanted to add the windshield that would be an extra $200. What color are you wanting to go, and could you send a pic of it?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white BMW M4 in a parking garage, front three quarter view, with a contrasting carbon fiber roof, black mirror caps and black wheels.\nservice_ques: a roof in its own color, possibly a specialty carbon fiber film\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"heres the car, wnat satin balck *want *black"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2022 m4"},"system_response_to_user_message_0":"Sweet, we can do that. What color are you wanting to go, and could you send a pic of the M4?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"its whtie rn\nthinkin nardo gery\n*grey"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Looking for a wrap on my 2021 audi rs5"},"system_response_to_user_message_0":"Sweet, what color is the RS5 right now, and what color are you wanting to go?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a black Dodge Charger in a driveway, side view, with a contrasting matte black hood, chrome window trim and black wheels.\nservice_ques: a hood in its own color; the chrome window trim points to a chrome delete\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"thsts the car, gonna do glos red i mean gloss"},"message_history":{"user_message_0":{"user_text":"hello my name is Kade Smith, I am interested in your services, the vehicle I have is dodge chargr 2020."},"system_response_to_user_message_0":"Heyy Kade, this is Hazel at the Lone Wraps team, saw your quote request on the Charger. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"wrap and tint"},"system_response_to_user_message_1":"Yeah, we can do both. A wrap on the Charger typically runs $2950 plus tax, it just depends on what color it is right now, and our ceramic tint on the sides and rear is $450 plus tax, and if you wanted to add the windshield that would be an extra $200. What color are you wanting to go, and could you send a pic of it?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a light blue McLaren convertible sports car in glossy paint, front three quarter view, parked on a road with a dry brush hillside and golden sunlight behind it, black multi spoke wheels with red brake calipers and blacked out lower front trim and side intake.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"That is it I want it blacked out "},"message_history":{"user_message_0":{"user_text":"hello my name is Gabe p, I am interested in your services, the vehicle I have is mclaren 570s 2021."},"system_response_to_user_message_0":"Heyy Gabe, this is Hazel at the Lone Wraps team, saw your quote request on the 570S. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Color change "},"system_response_to_user_message_1":"For sure, there's two ways we can go on the 570S. A vinyl wrap is the more affordable route and comes in pretty much any color and finish, and colored PPF is basically our protective film with the color in it, so it changes the color and takes the rock chips too, it's about twice as thick as vinyl and lasts about double. What color are you thinking, and could you send a pic of the 570S?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"So you will do 20% on the fromt windshield rhat us kind of dark "},"message_history":{"user_message_0":{"user_text":"hello my name is Tristan Walker, I am interested in your services, the vehicle I have is honda accords 2012."},"system_response_to_user_message_0":"Heyy Tristan, this is Hazel at the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Wanting window tint "},"system_response_to_user_message_1":"Sweet, so sides and rear on the Accord would run $450 plus tax for our ceramic tint, it blocks 99% of the UV and 90% of the heat, and if you wanted to add the windshield that would be an extra $200.","user_message_2":{"user_media":{},"user_text":"Ok cool whats cost for sides rear and fron windshield "},"system_response_to_user_message_2":"Sides, rear and windshield on the Accord would run $650 plus tax."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"ok add the windshield too, 20% on everything"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint, and if you wanted to add the windshield that would be an extra $200."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Is that the ceramic tint?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint, and if you wanted to add the windshield that would be an extra $200.","user_message_1":{"user_media":{},"user_text":"whats the warranty"},"system_response_to_user_message_1":"Lifetime warranty on any bubbling or peeling from the install. Did you want to hop on the schedule?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Yes, but can we do 35 on the fronts instead?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Sides and rear on my 2021 f150, 20% all around"},"system_response_to_user_message_0":"Sweet, so sides and rear on the F150 would run $450 plus tax for our ceramic tint.","user_message_1":{"user_media":{},"user_text":"How long does it take?"},"system_response_to_user_message_1":"Usually same day, drop it off in the morning and it's ready by the end of the day. Did you want to hop on the schedule?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Probably the full body"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for ppf on my 2023 accord"},"system_response_to_user_message_0":"Front end on the Accord would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 plus tax. Which option are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Ok I will pass on the window tint and go somewhere else for that"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for front end ppf and tint on the sides and rear of my 2023 accord?"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Accord would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and ceramic tint on the sides and rear is $450 on top.","user_message_1":{"user_media":{},"user_text":"Does the ppf come with a warranty?"},"system_response_to_user_message_1":"Yeah, lifetime warranty on any bubbling or peeling from the install."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"nah ill skip the chrome delete, thats too much"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2023 tahoe, its white, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Tahoe would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty.","user_message_1":{"user_media":{},"user_text":"Does that include chrome delete?"},"system_response_to_user_message_1":"No, chrome delete is $750 on top of that. Did you want that added on?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"nvm we're gonna go with someone local for the vans"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need our logo and phone number on 3 work vans"},"system_response_to_user_message_0":"Yeah, we can do that. What vans are they, and could you send over the logo?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"yeah im good on the coating"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 tesla model 3, white, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Model 3 would run $2800 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty.","user_message_1":{"user_media":{},"user_text":"Can you put a ceramic coating on it too?"},"system_response_to_user_message_1":"Yeah, we offer a 50% off ceramic coating on top of a vinyl wrap, the coating lasts for years and it gets the wrap closer to 7 years instead of 5 or 6. Did you want that added on?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"eh nevermind on the black roof, just the full wrap"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full wrap gloss white on my 2023 x5, its blue. could you do the roof in gloss black too?"},"system_response_to_user_message_0":"Sweet, so gloss white on the X5 would run $4300 plus tax for a full wrap. Could you send a pic of the X5 so we can see the roof?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"actually can we do the whole thing in gloss black instead of satin?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Tacoma would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Im thinking just cheaper one for now Can i get a frontal ppf on it To get some protection "},"message_history":{"user_message_0":{"user_text":"hello my name is Gabriel Perez, I am interested in your services, the vehicle I have is Porche 9111 gt3rs 2025."},"system_response_to_user_message_0":"Heyy Gabriel, this is Hazel at the Lone Wraps team, saw your quote request on the 911 GT3 RS. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Color change on it "},"system_response_to_user_message_1":"For sure, there's two ways we can go on the GT3 RS. A vinyl wrap is the more affordable route and comes in pretty much any color and finish, and colored PPF is basically our protective film with the color in it, so it changes the color and takes the rock chips too, it's about twice as thick as vinyl and lasts about double. What color are you thinking, and could you send a pic of it?","user_message_2":{"user_media":{},"user_text":"What prices on each "},"system_response_to_user_message_2":"A wrap on the GT3 RS typically runs $2950 plus tax and colored PPF typically runs $6400 plus tax for the full body, it just depends on what color it is right now. Could you send a pic of it?","user_message_3":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a bright gloss blue Porsche 911 GT3 RS sports car at an outdoor car show, front three quarter view, with a large black carbon rear wing, black wheels with yellow brake calipers, black mirrors, black hood vent accents and side stripe graphics, parked on grass with a person beside it and many other cars in the background.\nservice_ques: racing stripes and custom graphics\ntext_overlays: RS24 UFO, GT3 RS\nbright_vehicle: yes"}},"user_text":"Thats it "},"system_response_to_user_message_3":"Sweet, so a wrap on the GT3 RS would run $3200 plus tax and colored PPF $6650 plus tax for the full body, bright colored cars like that blue run $250 more since they take more to cover. What color are you wanting to go?","user_message_4":{"user_media":{},"user_text":"Why so much more Its just blue "},"system_response_to_user_message_4":"Bright colors like that blue take more skill and time to cover no matter what goes over it, so it's $250 more on either one.","user_message_5":{"user_media":{},"user_text":"Ok well what us warranty Is* "},"system_response_to_user_message_5":"The wrap comes with a 6 month warranty on any peeling or bubbling from the install, and colored PPF has a lifetime warranty on anything that fails, bubbles or peels from the install. Which route are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"lets do the wrap, and id want ppf on the front of it so it doesnt chip"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2023 camaro, its black, want to change the color, whats the price on a wrap vs colored ppf"},"system_response_to_user_message_0":"Two ways to go on the Camaro, a vinyl wrap is the more affordable one, and colored PPF changes the color and protects the paint from rock chips at the same time. The wrap would be $2950 plus tax and colored PPF $6400 plus tax for the full body. Which route are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Wanna change the color "},"message_history":{"user_message_0":{"user_text":"hello my name is Damien Walker, I am interested in your services, the vehicle I have is mclaren 570s 2021."},"system_response_to_user_message_0":"Heyy Damien, this is Hazel at the Lone Wraps team, saw your quote request on the 570S. What are you looking to get done?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"thinking about changing the color on my truck"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"want to black out my whole 2020 ram 2500"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Not quite sure yet "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Wanna change the color on my 2021 mclaren 570s"},"system_response_to_user_message_0":"For sure, a vinyl wrap is the more affordable way and comes in pretty much any color and finish, and colored PPF changes the color while protecting the paint from rock chips at the same time. What color are you thinking, and could you send a pic of the 570S?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Sounds goods "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Wanna change the color on my 2021 mclaren 570s, its bright red"},"system_response_to_user_message_0":"Sweet, so since it's a bright red now, a full wrap on the 570S would run $3200 plus tax and colored PPF would be $6650 plus tax. Which route are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"I’ll swing by tmr When do you open "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Wrap on my 2021 mclaren 570s, not sure on the color"},"system_response_to_user_message_0":"We do have all our color samples here at the shop if you would like to swing by."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Shit man I work at 9 am Can we do 8:30? So I can pic a color "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Wrap on my 2021 mclaren 570s, not sure on the color"},"system_response_to_user_message_0":"We do have all our color samples here at the shop if you would like to swing by.","user_message_1":{"user_media":{},"user_text":"I’ll swing by tmr When do you open "},"system_response_to_user_message_1":"We open at 9AM, so anytime after that works."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"I get off at 10pm When do you close? "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Wrap on my 2021 mclaren 570s, not sure on the color"},"system_response_to_user_message_0":"We do have all our color samples here at the shop if you would like to swing by."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Ok well lets just oick when i go Can i do that "},"message_history":{"user_message_0":{"user_text":"hello my name is Gabriel Walker, I am interested in your services, the vehicle I have is Porche 9111 gt3rs 2025."},"system_response_to_user_message_0":"Heyy Gabriel, this is Hazel at the Lone Wraps team, saw your quote request on the 911 GT3 RS. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Want a window tint "},"system_response_to_user_message_1":"Sweet, so sides and rear on the GT3 RS would run $300 plus tax since it's a 2 door, and our ceramic tint blocks 99% of the UV and 90% of the heat. Do you know how dark you're wanting to go?","user_message_2":{"user_media":{},"user_text":"What is darkest You can do "},"system_response_to_user_message_2":"Darkest is 5% on the rear, but the front two top out at 20%, and if you wanted the windshield it goes 50% at the darkest."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"which color do you think looks better"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 civic, deciding between satin black or nardo grey wrap"},"system_response_to_user_message_0":"Sweet, so the Civic would run $2950 plus tax for a full wrap in either one, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"I'm ready"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for ppf on my 2023 accord"},"system_response_to_user_message_0":"Front end on the Accord would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 plus tax. Which option are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"I'm ready"},"message_history":{"user_message_0":{"user_media":{},"user_text":"want to wrap my car"},"system_response_to_user_message_0":"Yeah, we can do that. What vehicle is it?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"want it a different color, what would that run"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"probably the wrap, how long does it last?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"thinking about changing the color on my 2020 tacoma, its white"},"system_response_to_user_message_0":"Sweet, so a full wrap on the Tacoma would run $3450 plus tax, and colored PPF would be $7400 plus tax, which changes the color and protects the paint at the same time. Which route are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"yo whats good, how much for ppf on the front of a 2022 bronco"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"its a 2021 f150, white right now"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much for a full wrap in satin black?"},"system_response_to_user_message_0":"What vehicle is it, and what color is it now?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Can you tell me about the film"},"message_history":{"user_message_0":{"user_text":"hello my name is Gabriel Perez, I am interested in your services, the vehicle I have is mclaren 570s 2021."},"system_response_to_user_message_0":"Heyy Gabriel, this is Hazel at the Lone Wraps team, saw your quote request on the 570S. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Front end ppf and tint on the sides and rear"},"system_response_to_user_message_1":"Sweet, so front end PPF on the 570S would run $2080 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and ceramic tint on the sides and rear is $390 on top since it's a 2 door, and if you wanted to add the windshield that would be an extra $260. Do you know how dark you're wanting to go?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"what film do you guys use"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a grey Toyota Tacoma in a driveway, side view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"2021 tacoma, its grey, want satin green"},"system_response_to_user_message_0":"Sweet, so satin green on the Tacoma would run $3450 plus tax, do you have an exact green in mind? If you do, can you shoot a pic of it over"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"is the vinyl good quality? how does it hold up"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white Toyota Camry in a parking lot, front three quarter view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"how much to wrap my 2020 camry gloss black, its white"},"system_response_to_user_message_0":"Sweet, so gloss black on the Camry would run $2950 plus tax, do you have an exact black in mind? If you do, can you shoot a pic of it over"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"tell me more about the ppf"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for ppf on my 2023 accord"},"system_response_to_user_message_0":"Front end on the Accord would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 plus tax. Which option are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a single satin dark green vinyl color swatch on a white background, with the film name under it.\nservice_ques: a color change wrap in satin dark green\ntext_overlays: 3M 2080 Satin Dark Green\nbright_vehicle: no"}},"user_text":"this one"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a grey Toyota Tacoma in a driveway, side view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"2021 tacoma, its grey, want satin green"},"system_response_to_user_message_0":"Sweet, so satin green on the Tacoma would run $3450 plus tax, do you have an exact green in mind? If you do, can you shoot a pic of it over"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"https://graphics.averydennison.com/en/home/graphics-products/vehicle-wrap-films/supreme-wrapping-film/gloss-metallic-blue.html thats the one"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white BMW M3 in a parking garage, side view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"want to wrap my 2022 bmw m3 blue, its white"},"system_response_to_user_message_0":"Sweet, so blue on the M3 would run $2950 plus tax, do you have an exact blue in mind? If you do, can you shoot a pic of it over"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of the Avery Dennison website showing a color page for a gloss grey wrap film, with a sample car in that color.\nservice_ques: a color change wrap in gloss grey\ntext_overlays: Avery Dennison SW900, Gloss Nardo Grey\nbright_vehicle: no"}},"user_text":""},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white Audi RS5 on the street, front three quarter view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"Wrap on my 2021 audi rs5, its white, thinking nardo grey"},"system_response_to_user_message_0":"Sweet, so nardo grey on the RS5 would run $2950 plus tax, do you have an exact grey in mind? If you do, can you shoot a pic of it over"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"nah forget the logo stuff, just want it wrapped gloss red"},"message_history":{"user_message_0":{"user_media":{},"user_text":"want my plumbing company on my 2019 charger, or just a color change if that makes more sense"},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Im looking to do a wrap on my car"},"message_history":{"user_message_0":{"user_text":"hello my name is Adam Walker, I am interested in your services, the vehicle I have is 2017 Infiniti Q50."},"system_response_to_user_message_0":"Heyy Adam, this is Hazel at the Lone Wraps team, saw your quote request on the Q50. What are you looking to get done?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"full wrap, color change"},"message_history":{"user_message_0":{"user_text":"hello my name is Adam Walker, I am interested in your services, the vehicle I have is 2017 Infiniti Q50."},"system_response_to_user_message_0":"Heyy Adam, this is Hazel at the Lone Wraps team, saw your quote request on the Q50. What are you looking to get done?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"let me think about it, how long would it take?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"found someone cheaper, thanks anyway"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic, 4 doors and the back glass"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Can I get a quote on a wrap for my 21 ram trx and the ceramic coating special?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"would you guys knock anything off if I post you on my page?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2023 tahoe, its white, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Tahoe would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"how much to wrap my 2019 civic? also do you guys do the stars in the headliner?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"do you guys do matte ppf?"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Hey! I do car content on tiktok, just picked up a 2024 mustang and want it wrapped satin purple, would love to collab with you guys on it"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"want ppf on the hood, bumper and mirrors of my 2022 4runner, rock chips are killing me"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"We had the wrap taken off my husbands Audi S5 after a door ding, now hes wanting clear bra on the hood and fenders before it gets chipped"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Sorry I had my notifications off,  think the front doors might have ppf on it, does it cost to have that removed or do I need to do it before?\nI work in salt lake so I would just need to plan ahead of time to be able to have a different car, hopefully in the month of October though"},"message_history":{"user_message_0":{"user_media":{},"user_text":"I am looking to get my Tesla y wrapped a nardo gray type color. What would the cost be on that and how long would you need the car?"},"system_response_to_user_message_0":"That would be $2800, we would need the car for three days\nHow soon are you looking to get this done?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Yeah I love it, I already have a PPF for the front so that would most likely have to come off when wrapping this correct?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2024 M4 Competition\nWhite"},"system_response_to_user_message_0":"You’d be about $3300\nThat thing would be insane wrapped lol"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"What does the warranty entail?\nI don’t have a picture of it, but it is black right now with satin PPF on it. Can you wrap over that?"},"message_history":{"user_message_0":{"user_text":"hello my name is Makenzie Walker, I am interested in your services, the vehicle I have is 2024 Kia sorento."},"system_response_to_user_message_0":"Heyy Makenzie, this is Hazel at the Lone Wraps team, saw your quote request on the Sorento. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"A full wrap"},"system_response_to_user_message_1":"Sweet, we can get your Sorento wrapped, a full wrap on it typically runs $3450 + tax. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty. What color is it right now? Send me a pic if you can"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"hey are you guys available this friday? got a new audi i want wrapped"},"message_history":{}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"are you open saturday? need tint on my 2019 tacoma"},"message_history":{}}
    category: service_pricing
"""


#BUSINESS OPERATIONS
BUSINESS_OPERATIONS_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Are you guys open today"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"What are your hours of operation?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"Wats ur number"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"Can I swing by today?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"Are you guys licensed and insured?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"Do you guys have insurance in case something happens to it while its there?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"do you guys do financing?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"I've got a few questions about the shop"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"Hey, question for you"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"Can you tell me a bit about your company?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Google business listing for Lone Wraps showing its hours.\nservice_ques: none visible\ntext_overlays: Lone Wraps, Closed, Saturday\nbright_vehicle: no"}},"user_text":"says you guys are closed saturday, is that right?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"are you open saturdays?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"can I finance ppf with you guys?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"what time do you close today"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"hey how are you, you guys open today?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"whos this?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"wait is this a bot lol"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yall open friday?"},"system_response_to_user_message_0":"Yeah, Friday we're open 9AM to 5PM."}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"what's the shop's phone number?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"what time do yall close on fridays?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"what's your schedule like?"},"message_history":{}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"how many guys you got working there?"},"message_history":{}}
    category: business_operations
"""


#HUMAN SERVICES
SERVICES_REQ_HUMANS_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"I need a quote for 2 trailers"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Full wrap 4 sides art-work provided. 10-year warranty. For my business."},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Hey I’m looking to get my 2023 ford transit van a business wrap. What does typical pricing look like?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Yes looking for a quote to get some logos on my truck"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Custom Commercial"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey could I get a quote on a full wrap for a 2024 ford transit low roof?"},"system_response_to_user_message_0":"Sure! Do you want a solid wrap or like a cusotom commercial wrap?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"No, just llama window cleaning\nIn both sides, and also phone number in the back"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey how much do you guys charge ??"},"system_response_to_user_message_0":"For a full wrap?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"How much to put my logo and stuff on my truck"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Where you located"},"system_response_to_user_message_0":"American fork Utah"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"No"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"What is it that you are looking to get done?","user_message_1":{"user_media":{},"user_text":"Wrap for our business van"},"system_response_to_user_message_1":"Do you have a mock up made for it already?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Yes, I do"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Im looking to get my 24ft food truck wrapped"},"system_response_to_user_message_0":"Do you have a photo of the truck and design made?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"What is the price difference?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"I have a 2021 Mercedes sprinter van that I'm looking to get some decal work done. I don't want a full color change, but just a good rap that represents our window replacement brand. Wanted to get a rough price on what that would cost."},"system_response_to_user_message_0":"yes! we can either just install decals or do a half wrap"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Want company info on car"},"message_history":{"user_message_0":{"user_text":"hello my name is Gabriel Walker, I am interested in your services, the vehicle I have is 2024 Ford transit."},"system_response_to_user_message_0":"Heyy Gabriel, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Whats the differenfe in what theys doe"},"message_history":{"user_message_0":{"user_text":"hello my name is Tristan doe, I am interested in your services, the vehicle I have is 2024 Ford transit."},"system_response_to_user_message_0":"Heyy Tristan, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Want to put my company info pn it"},"system_response_to_user_message_1":"We can do that, are you looking for a full wrap, a half wrap or just decals on the Transit?","user_message_2":{"user_media":{},"user_text":"Depends on the cost"},"system_response_to_user_message_2":"Decals usually run $450 to $900, a half wrap $1950 to $3100 and a full wrap $3500 to $5500, it just depends on the year, make, model and design. Which one are you leaning towards?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Probably full wrap, and this pricing is per vehicle right?"},"message_history":{"user_message_0":{"user_text":"hello my name is Tristan Walker, I am interested in your services, the vehicle I have is 2024 Ford transit."},"system_response_to_user_message_0":"Heyy Tristan, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Want company info on it"},"system_response_to_user_message_1":"Yeah, we can put your company info on the Transit. Are you thinking a full wrap, a half wrap or just decals?","user_message_2":{"user_media":{},"user_text":"Whats the difference ? Just want it all on it"},"system_response_to_user_message_2":"Decals are just your logo and info put on over the paint for $450 to $900, a half wrap is printed vinyl over part of the van for $1950 to $3100, and a full wrap covers the whole thing for $3500 to $5500, it just depends on the year, make, model and design. Sounds like a full wrap might be what you want, which one are you leaning towards?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"If we could do this or something really similar for $1800 I'd do that for sure\nIs this something we can get scheduled?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey! Looking for a partial wrap.\r\n\r\nThis is what I'm wanting. But my budget is around $1500 so if it needs to be less than this I understand"},"system_response_to_user_message_0":"For something like this, you would probably be looking around 1800. We could simplify it just a little bit more and hit that budget for sure."}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"how much to just get the hood wrapped? want it to match the rest of the car, its a forest green outback"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Just want the pillars done in piano black on my 2020 highlander"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Full wrap gloss white with the roof and mirrors in gloss black, its a 2024 model y"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"No just the roof and mirrors in black"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey how much for a wrap on my 2021 tahoe"},"system_response_to_user_message_0":"For a full wrap?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"How much for two gloss black stripes over the hood and roof on my challenger"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"How much for chrome gold wrapping for a 2015 chevy corvette"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Whats the price if I go with a color shift instead?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Just looking to get a quote on my 2016 Audi s7 to be fully wrapped in satin white! Its black right now"},"system_response_to_user_message_0":"Sweet, so satin white on the S7 would run $2950 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Can you guys do a wrap with a design I made? Its like a galaxy print with some splatter effects on the sides"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"I'm looking to remove old PPF on the front of my Ineos and Tint my front two windows including the two small safari windows"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Yes, possibly.  I'm looking at picking up a car that has PPF, but it's got several rock marks in it.  I'm told it probably needs to be replaced.  What would it cost to remove and fully replace?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Ok cool. Does that include removing old clear bra?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Looking for a quote on a 2018 Tesla model s for a front end clear bra install. \nBumper\nRight and left fender\nHood\nHeadlights and back of mirrors."},"system_response_to_user_message_0":"Hey! Full front Ppf on this vehicle is $1600+tax. We can get it done this upcoming week"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Hi Tristan, I'm looking to get a section of my front bumper re-wrapped in clear PPF as well as getting a quote for tinting my windows, all side windows and rear window."},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Can you guys take the old wrap off my 2019 camaro? its peeling pretty bad"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Hey whats up I was wondering what you guys would charge to re wrap my 2020 model 3, the wrap on it is old and peeling everywhere. Its matte black right now, want to go gloss white"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"How much for colored ppf? And there would be an existing wrap removal as well."},"message_history":{"user_message_0":{"user_media":{},"user_text":"Whats a full wrap run on my 2016 tesla model s? Its wrapped white right now, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Model S would run $2800 plus tax for the new wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"like 4 years"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Can you guys take the old wrap off my 2019 camaro? its peeling pretty bad"},"system_response_to_user_message_0":"Yeah, we can take the old wrap off. How long has it been on, and do you have a photo of it?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Hello, looking to do chrome delete"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Do you guys do chrome deletes? And are you open saturday?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"How much do you charge for chrome deletes?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"I'm looking to get the silver part of the grille wrapped black."},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Just looking to cover up some chrome. \nFront and rear bumpers and a small strip along the running boards. Color matching the truck. Ford star white"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Hi, I am looking for a quote for a 2021 expedition max chrome delete and matte black wrap."},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Hi, I have a truck that I had blackout done on, it's peeling off in some areas and was wondering if you could replace it for me."},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"2023 Audi S3, just looking to black out trim."},"message_history":{"user_message_0":{"user_media":{},"user_text":"yeah"},"system_response_to_user_message_0":"could you remind me what vehicle you were looking to get done"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"yes\nI was wanting my front and back Mazda sign then the trim around my windows\nif your able to do that"},"message_history":{"user_message_0":{"user_media":{},"user_text":"ok all good, i'll be there in a minute\ndo you guys also do chrome delete"},"system_response_to_user_message_0":"Yes, we do. Same car?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"How much is just the chrome delete"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Probably"},"system_response_to_user_message_0":"Okay to add the chrome delete the total would be $650 to do those chrome trim, pillars, and mirror caps.\nAre you still wanting to get the tuxedo wrap?","user_message_1":{"user_media":{},"user_text":"I'm getting 1 other quote and will get back asap!"},"system_response_to_user_message_1":"Sounds good! let us know!"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Sure, curious on a price. Looking to do either all Matt black with chrome delete of course or the Yukon is a maroon color so would like to do possibly the top half from windows up black"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Yeah crime trim too\nChrome"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Car is white now want a full wrap to black and the door handles red"},"system_response_to_user_message_0":"Great, we can do that. Are you wanting the chrome trim done red as well? Or just the door handles. And is there chrome trim around the windows or is it black?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Dodge Durango"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hey i tried to book an estimate with you guys for a chrome delete service but its not working on my end🙏🏾"},"system_response_to_user_message_0":"What vehicle are you looking to get done?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Just above the windshield needs a black wrap. Also look into a ceramic coating on the whole motorhome. Would like to get this done this week if possible"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes."},"system_response_to_user_message_0":"Awesome, what is it that you’re looking to get done on your vehicle?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"hey guys how much to wrap my passenger fender/my bottom half front bumper in solar octane\nthe vehicle got in an accident and they didn't really paint match it during the repair."},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Just looking to have my headlights ppfd"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"I will let you know I might have found another place that will do it for me here in America fork\nHello good morning I was just wondering how much would it cost I’d do a clear wrap on a 2025 Toyota Rav 4 just the hood for Rock chip protection"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Hey so I had my car wrapped by you guys about a year and a half ago. I was recently in an accident and messed up a couple panels. Caliber Collision reached out last week about getting it rewrapped and told me I'd just need to schedule an appointment to get it taken care of"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"We just had someone hit and run and bump into our Panamera and dent the bumper. Do you guys have the capability to fix that when we wrap it"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"You guys don't do body work do you?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Would like to get a quote for a full wrap on an 08 Silverado 2500 crew cab short bed in gloss black"},"system_response_to_user_message_0":"We can get a full wrap done on this vehicle for $3450 plus tax"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Can you guys do motorcycles??"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"can you wrap my 2023 R6 before the track day saturday?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"how much to wrap a 2021 harley road glide in gloss black?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"how much to wrap my 2022 m3 in nardo grey with some red accents?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"thinking satin black with gold accents on my challenger, what would that run"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"what would it run to wrap my 2021 can am maverick x3? want it gloss black"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"do yall wrap sleds? got a 2020 ski doo i want redone"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"my 2019 civic got hit by hail and has a bunch of little dents, could you still wrap it satin black?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Not sure, depends on the price. We have 3 vans total"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need a quote on wrapping our company van"},"system_response_to_user_message_0":"Yeah, we can do that. Are you looking for a full wrap, a half wrap or just decals on the van?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"I have 19 vans, and 5 trucks. We want to do our company wrap on all of them "},"message_history":{"user_message_0":{"user_text":"hello my name is d G, I am interested in your services, the vehicle I have is 2024 Ford transit."},"system_response_to_user_message_0":"Heyy D, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Trying to wrap my fleet "},"system_response_to_user_message_1":"For sure, are you looking for a full wrap, a half wrap or just decals on them?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"We want to do the a full wrap on the whole fleet "},"message_history":{"user_message_0":{"user_text":"hello my name is d G, I am interested in your services, the vehicle I have is 2024 Ford transit."},"system_response_to_user_message_0":"Heyy D, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Trying to wrap my fleet "},"system_response_to_user_message_1":"For sure, are you looking for a full wrap, a half wrap or just decals on them?","user_message_2":{"user_media":{},"user_text":"I have 19 vans, and 5 trucks. We want to do our company wrap on all of them "},"system_response_to_user_message_2":"Yeah, we can do the whole fleet. Quick question, what's the make and model of the trucks?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"They are all transits, the trucks are f150s "},"message_history":{"user_message_0":{"user_text":"hello my name is d G, I am interested in your services, the vehicle I have is 2024 Ford transit."},"system_response_to_user_message_0":"Heyy D, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Trying to wrap my fleet "},"system_response_to_user_message_1":"For sure, are you looking to get the Transit wrapped, a full wrap, a half wrap or just decals on it?","user_message_2":{"user_media":{},"user_text":"I have 19 vans, and 5 trucks. We want to do our company wrap on all of them "},"system_response_to_user_message_2":"Yeah, we can handle the whole fleet. Are you wanting a full wrap, a half wrap or just decals on the vans and trucks?","user_message_3":{"user_media":{},"user_text":"We want to do the a full wrap on the whole fleet "},"system_response_to_user_message_3":"Sweet, full wraps on the whole fleet. Is the Transit the only one you've got or are the other vans Transits too, and what trucks are they?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"the trucks are f150s"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Trying to wrap my fleet, I have 19 vans and 5 trucks"},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on them?","user_message_1":{"user_media":{},"user_text":"full wrap on all of them"},"system_response_to_user_message_1":"Sweet, we can get the full wrap done on the whole fleet. Quick question, what's the make and model of the trucks?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Full wrap "},"message_history":{"user_message_0":{"user_text":"hello my name is g p, I am interested in your services, the vehicle I have is Honda Accord 2021."},"system_response_to_user_message_0":"Heyy G, this is Hazel at the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"I have a g wagon "},"system_response_to_user_message_1":"Yeah, what are you looking to get done on the G Wagon?","user_message_2":{"user_media":{},"user_text":"I want to wrap my business on there or do a vinyl wraps whatever makes more sense. "},"system_response_to_user_message_2":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Wait that’s the business wrap price? "},"message_history":{"user_message_0":{"user_text":"hello my name is g p, I am interested in your services, the vehicle I have is Honda Accord 2021."},"system_response_to_user_message_0":"Heyy G, this is Hazel at the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"I have a g wagon "},"system_response_to_user_message_1":"Yeah, what are you looking to get done on the G Wagon?","user_message_2":{"user_media":{},"user_text":"I want to wrap my business on there or do a vinyl wraps whatever makes more sense. "},"system_response_to_user_message_2":"For sure, are you looking for a full wrap, a half wrap or just decals on it?","user_message_3":{"user_media":{},"user_text":"Full wrap "},"system_response_to_user_message_3":"Sweet, a full wrap on the G Wagon typically runs $3450 + tax. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty. What color are you wanting to go, and what color is it right now? Send me a pic if you can"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"half"},"message_history":{"user_message_0":{"user_media":{},"user_text":"want my house cleaning company on my 2022 lexus rx, or maybe just change it to white, not sure yet"},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"decals"},"message_history":{"user_message_0":{"user_media":{},"user_text":"thinking about putting my photography business logo on my x5 or just doing a matte grey wrap on it"},"system_response_to_user_message_0":"Yeah, we can do either. Are you looking for a full wrap, a half wrap or just decals on it?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Full"},"message_history":{"user_message_0":{"user_media":{},"user_text":"I have a 2020 jeep wrangler I use for my pest control business, want it wrapped with the company on it or maybe just a new color"},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on the Wrangler?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"wait is that for the logo wrap?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"could you put my bakery's logo on my audi q7? or a regular wrap works too"},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on it?","user_message_1":{"user_media":{},"user_text":"full wrap"},"system_response_to_user_message_1":"Sweet, a full wrap on the Q7 would run $3650 + tax. What color are you wanting to go?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"2 f250s and a 2021 silverado"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need our logo on 3 work trucks"},"system_response_to_user_message_0":"Yeah, we can do logos. What trucks are they?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"yeah I have an AI file"},"message_history":{"user_message_0":{"user_media":{},"user_text":"They are all transits, the trucks are f150s"},"system_response_to_user_message_0":"Perfect, we can do the full wrap on all 19 Transits and the 5 F-150s. Do you have a vector file for your logo?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a Chevrolet Corvette wrapped in a chrome red film, side view.\nservice_ques: a chrome wrap\ntext_overlays: none\nbright_vehicle: yes"}},"user_text":"how much for this on my 2022 mustang?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a black Toyota Tundra, front three quarter view, with a chrome grille, chrome bumpers and chrome window trim.\nservice_ques: a chrome delete\ntext_overlays: none\nbright_vehicle: no"}},"user_text":""},"message_history":{"user_message_0":{"user_media":{},"user_text":"need a quote on a chrome delete for my 2021 tundra"},"system_response_to_user_message_0":"Yeah, we can do that. Can you send a picture of the truck so we can see all the chrome on it?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white vinyl mountain decal laid on a table next to the hood of a gray Jeep Wrangler.\nservice_ques: a decal install\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this one, going on the hood"},"message_history":{"user_message_0":{"user_media":{},"user_text":"can you guys put a decal on my jeep? want it done next week"},"system_response_to_user_message_0":"Yeah, we can do that. Do you have a pic of the decal and where you want it on the Jeep?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a simple black and white company logo for a landscaping business.\nservice_ques: a logo on a vehicle\ntext_overlays: Green Peak Landscaping\nbright_vehicle: no"}},"user_text":"here it is"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to put our logo on both doors of a 2020 ram 2500"},"system_response_to_user_message_0":"Yeah, we can do that. Could you send over the logo you want on there?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A close up of a white hood with clear film that is yellowed and lifting along the front edge.\nservice_ques: PPF removal and replacement\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"Can you take this off and put new on?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A Honda Civic from the side in a satin blue wrap that's peeling up along the doors and the rear bumper.\nservice_ques: wrap removal\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"can you take this off and redo it?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A digital mockup of a white Ford Transit van with a blue company logo, a phone number and a website on the side.\nservice_ques: Commercial wrap or decals.\ntext_overlays: SUMMIT PLUMBING, (801) 555-0142, summitplumbing.com\nbright_vehicle: no"}},"user_text":"This is what we want on our van, how much would it be?"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a white BMW X5 with a gloss black roof, side view.\nservice_ques: a roof in its own color\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"Can we do the roof like this too?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full wrap gloss white on my 2023 x5, its blue"},"system_response_to_user_message_0":"Sweet, so gloss white on the X5 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Lets do the wrap and the chrome delete, when can I bring it in?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 f150, its white, want matte black. also want the chrome blacked out"},"system_response_to_user_message_0":"Sweet, so matte black on the F150 would run $3450 plus tax for a full wrap. Could you send a pic of the truck so we can see all the chrome on it?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"I'll pass on the tint, but can you black out the chrome trim too?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 f150, its white, want matte black, and tint on the sides and rear"},"system_response_to_user_message_0":"Sweet, so matte black on the F150 would run $3450 plus tax for a full wrap, and ceramic tint on the sides and rear is $450 on top."}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"skip the tint, but could you do the hood in gloss black instead of matte?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2023 bmw m4, its blue, want matte grey, and how much for tint?"},"system_response_to_user_message_0":"Sweet, so matte grey on the M4 would run $2950 plus tax for a full wrap, and ceramic tint on the sides and rear is $300 on top since it's a 2 door."}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"the wrap, and can you put ppf on just the hood over it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2023 camaro, its black, want to change the color, whats the price on a wrap vs colored ppf"},"system_response_to_user_message_0":"Two ways to go on the Camaro, a vinyl wrap is the more affordable one, and colored PPF changes the color and protects the paint from rock chips at the same time. The wrap would be $2950 plus tax and colored PPF $6400 plus tax for the full body. Which route are you leaning towards?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"Im looking to do a graphic wrap on my car"},"message_history":{"user_message_0":{"user_text":"hello my name is Adam Walker, I am interested in your services, the vehicle I have is 2017 Infiniti Q50."},"system_response_to_user_message_0":"Heyy Adam, this is Hazel at the Lone Wraps team, saw your quote request on the Q50. What are you looking to get done?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"how much would this cost"},"message_history":{"user_message_0":{"user_text":"hello my name is Adam Walker, I am interested in your services, the vehicle I have is 2017 Infiniti Q50."},"system_response_to_user_message_0":"Heyy Adam, this is Hazel at the Lone Wraps team, saw your quote request on the Q50. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Im looking to do a graphic wrap on my car"},"system_response_to_user_message_1":"For sure, we can definitely do a graphic wrap on the Q50. Our designer puts the design together with you, from one you already have or from scratch, and we print it all here in house on 3M, Avery or KPMF film. Any peeling or bubbling from the install gets fixed, and every edge gets tucked and trimmed so it doesn't lift. Can you shoot me a pic of the Q50 as it is now, and of the design or look you're going for if you have one?"}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"can you wrap a cool design on my carbon fiber"},"message_history":{}}
    category: services_req_humans

    state: {"current_user_message":{"user_media":{},"user_text":"want a red to black fade on my 2020 mustang gt, how much?"},"message_history":{}}
    category: services_req_humans
"""


#BOOKING ACKNOWLEDGE
BOOKING_SERVICE_ACKNOWLEDGE_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Let's do it, how do I get on the schedule?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Yeah lets do it"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 jeep wrangler, its red, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Wrangler would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Ill take the full body"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for ppf on my 2023 accord"},"system_response_to_user_message_0":"Front end on the Accord would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 plus tax. Which option are you leaning towards?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"just the sides and rear"},"message_history":{"user_message_0":{"user_text":"hello my name is tristan walker, I am interested in your services, the vehicle I have is Honda Accord 2021."},"system_response_to_user_message_0":"Heyy Tristan, this is Hazel at the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Window tint, can I get on the books? "},"system_response_to_user_message_1":"Sweet, so sides and rear on the Accord would run $450 plus tax for our ceramic tint, it blocks 99% of the UV and 90% of the heat, and if you wanted to add the windshield that would be an extra $200. Did you want to get on the schedule for the sides and rear, or with the windshield too?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"front end"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much for ppf on my 2023 camry? can i get in next week"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Camry would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 plus tax. Which one did you want to get on the schedule?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"front end"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much for ppf on my 2023 camry"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Camry would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 plus tax. Which option are you leaning towards?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"Lets do it! How long will it take?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Lets do the camo then"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Its a 2024 ram 1500, white, wanting gloss black"},"system_response_to_user_message_0":"Sweet, so gloss black on the Ram would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want.","user_message_1":{"user_media":{},"user_text":"What would it be if we did camo instead?"},"system_response_to_user_message_1":"Camo film runs $500 more, so the price for the Ram would be $3950 plus tax. Which option are you leaning towards?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"ok cool lets get it done"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want satin black and tint on the sides and rear"},"system_response_to_user_message_0":"Sweet, so satin black on the Tacoma would run $3450 plus tax for a full wrap, with the $450 tint on top. Did you want to get both on the schedule?","user_message_1":{"user_media":{},"user_text":"whats the warranty on the wrap"},"system_response_to_user_message_1":"6 months on the wrap for any bubbling or peeling, and lifetime on the tint."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Yeah"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint, and if you wanted to add the windshield that would be an extra $200.","user_message_1":{"user_media":{},"user_text":"whats the warranty"},"system_response_to_user_message_1":"Lifetime warranty on any bubbling or peeling from the install. Did you want to hop on the schedule?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Sure, does it need to be washed before I bring it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Front end ppf on my 2023 camry"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Camry would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors.","user_message_1":{"user_media":{},"user_text":"Front end please"},"system_response_to_user_message_1":"Perfect, did you want to get the Camry on the schedule?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Im down"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2023 ram 1500, its white, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Ram would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty.","user_message_1":{"user_media":{},"user_text":"Does it come with a warranty?"},"system_response_to_user_message_1":"Yeah, 6 months on the wrap for any bubbling or peeling. Do you want to get the Ram on the schedule?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Sounds good, lets get it booked. Do you guys take cards?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Sides and rear on my 2021 f150"},"system_response_to_user_message_0":"Sweet, so sides and rear on the F150 would run $450 plus tax for our ceramic tint. Do you know how dark you're wanting to go?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Perfect, when can you get me in?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"What's your quote on a 2025 tesla model 3 for a ceramic coating?"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the Model 3 would run $700 plus tax, that covers all the painted surfaces and the coating lasts for years."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Book it, is there a deposit?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2019 audi a4, its grey, want gloss white"},"system_response_to_user_message_0":"Sweet, so gloss white on the A4 would run $2950 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Can I drop it off monday?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic, 4 doors and the back glass"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Yes add the coating, and lets get it scheduled"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2022 tesla model y, white, want satin black"},"system_response_to_user_message_0":"Sweet, so satin black on the Model Y would run $2800 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty.","user_message_1":{"user_media":{},"user_text":"How much for a ceramic coating on top?"},"system_response_to_user_message_1":"A ceramic coating on top of the wrap is $350 plus tax, the coating lasts for years and it gets the wrap closer to 7 years instead of 5 or 6. Did you want that added on?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Ok I want to get it on the schedule, what do you need from me?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for colored ppf on my 2021 tahoe? its black"},"system_response_to_user_message_0":"Sweet, so colored PPF on the Tahoe would run $7400 plus tax for the full body, and it comes with free side and rear window tint."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Alright im ready to book whenever"},"message_history":{"user_message_0":{"conversation_summary":"The customer has a white 2020 Honda Civic and wants front end PPF. The shop quoted $1600 plus tax for the front end and said it takes about a day and a half."},"system_response_to_user_message_0":""}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"night before drop could work tho. what days u got open"},"message_history":{"user_message_0":{"user_media":{},"user_text":"sides and rear on my 2022 4runner"},"system_response_to_user_message_0":"Sweet, so sides and rear on the 4Runner would run $450 plus tax for our ceramic tint, and you can drop it off the night before with the key drop box."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Ok what’s your schedule look like"},"message_history":{"user_message_0":{"user_text":"hello my name is tristan walker, I am interested in your services, the vehicle I have is 2024 ford f150."},"system_response_to_user_message_0":"Heyy Tristan, this is Hazel at the Lone Wraps team, saw your quote request on the F-150. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Protection for the front"},"system_response_to_user_message_1":"Sweet, so front end PPF on the F-150 would run $1800 + tax, that covers the full hood, fenders, bumper, headlights and mirrors. Did you want to get it on the schedule?","user_message_2":{"user_media":{},"user_text":"What brand do you use"},"system_response_to_user_message_2":"We use Ghost Films, their Revenant film","user_message_3":{"user_media":{},"user_text":"How thick is that and can you see it on the car"},"system_response_to_user_message_3":"The film is about double the thickness of a vinyl wrap, and once it's on the paint looks the same since it's a clear film, plus everything gets tucked so the edges don't show. Did you want to get the front end on the schedule for the F-150?","user_message_4":{"user_media":{},"user_text":"Do you hand cut or how do you install"},"system_response_to_user_message_4":"Every piece is precision cut on a Graphtec plotter, so no blades ever touch the paint, and we wrap as many edges as possible so everything is tucked"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"what does your schedule look like this week?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"ceramic coating on my 2023 model y"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the Model Y would run $700 + tax, that covers all the painted surfaces and the coating lasts for years.","user_message_1":{"user_media":{},"user_text":"how long do you need it"},"system_response_to_user_message_1":"Drop it off in the morning and it's ready to pick up the next day. Did you want to hop on the schedule?","user_message_2":{"user_media":{},"user_text":"do I need to wash it first"},"system_response_to_user_message_2":"Nope, we do all the prep here"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"is tues the 27th open? and the 525 includes taking the old tint off right"},"message_history":{"user_message_0":{"user_media":{},"user_text":"fronts have old purple tint, want sides and rear on my 2021 g550"},"system_response_to_user_message_0":"Sides and rear on the G550 would run $450 plus tax for our ceramic tint, and taking the old film off the front two is $75, so $525 plus tax all in."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Ill pass on the coating for now, just the wrap. Lets get it booked"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2020 camry, its white, want gloss black, and how much is the ceramic coating?"},"system_response_to_user_message_0":"Sweet, so gloss black on the Camry would run $2950 plus tax for a full wrap, and a ceramic coating on top of it is $350 plus tax, the coating lasts for years."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"I’m ready "},"message_history":{"user_message_0":{"user_text":"hello my name is Damien Walker, I am interested in your services, the vehicle I have is mclaren 570s 2021."},"system_response_to_user_message_0":"Heyy Damien, this is Hazel at the Lone Wraps team, saw your quote request on the 570S. What are you looking to get done?","user_message_1":{"user_media":{},"user_text":"Wanna change the color "},"system_response_to_user_message_1":"For sure, a vinyl wrap is the more affordable way and comes in pretty much any color and finish, and colored PPF changes the color while protecting the paint from rock chips at the same time. What color are you thinking, and could you send a pic of the 570S?","user_message_2":{"user_media":{},"user_text":"It’s red thinking I wanna do like a maroon or beige It’s a bright red "},"system_response_to_user_message_2":"Sweet, so since it's a bright red now, a full wrap on the 570S would run $3200 plus tax and colored PPF would be $6650 plus tax. Which route are you leaning towards?","user_message_3":{"user_media":{},"user_text":"Wrap"},"system_response_to_user_message_3":"Sounds good, that's $3200 plus tax for a full wrap on the 570s. Just tell me you're ready to go ahead with the $3200 plus tax wrap and which color you picked, then I'll get you the open drop off days."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Alright well I can book now and just pick a color when I come in 10 am at Saturday work? "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Wrap, its a bright red 2021 mclaren 570s, thinking maroon or beige"},"system_response_to_user_message_0":"Sweet, so since it's a bright red now, that's $3200 plus tax for a full wrap on the 570s. Just tell me you're ready to go ahead with the $3200 plus tax wrap and which color you picked, then I'll get you the open drop off days.","user_message_1":{"user_media":{},"user_text":"Not sure on the color yet"},"system_response_to_user_message_1":"We do have all our color samples here at the shop if you would like to swing by."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"How do I confirm? "},"message_history":{"user_message_0":{"user_media":{},"user_text":"Wrap, its a bright red 2021 mclaren 570s"},"system_response_to_user_message_0":"Sweet, so since it's a bright red now, that's $3200 plus tax for a full wrap on the 570s. Just tell me you're ready to go ahead with the $3200 plus tax wrap and which color you picked, then I'll get you the open drop off days."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"ready"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2020 mustang gt its white, want satin dark grey"},"system_response_to_user_message_0":"Sweet, so satin dark grey on the Mustang would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"im ready lets do it"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2022 silverado, its black"},"system_response_to_user_message_0":"What color are you wanting to go?","user_message_1":{"user_media":{},"user_text":"either nardo grey or a gloss white idk yet"},"system_response_to_user_message_1":"Sweet, so the Silverado would run $3450 plus tax for a full wrap in either one, and we've got the color books here at the shop if you want to see them in person."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"lets book it ill pick the color when i drop it off"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Color change on my 2019 4runner, its silver"},"system_response_to_user_message_0":"For sure, a vinyl wrap is the more affordable way and comes in pretty much any color and finish, and colored PPF is a self healing film that changes the color and protects the paint at the same time. What color are you thinking?","user_message_1":{"user_media":{},"user_text":"wrap for sure, some kind of green"},"system_response_to_user_message_1":"Sweet, so a full wrap on the 4Runner would run $3450 plus tax, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"what do I need to do to lock it in"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Matte black on my 2023 bronco, no roof"},"system_response_to_user_message_0":"Sweet, so matte black on the Bronco would run $2800 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"yeah im good to go"},"message_history":{"user_message_0":{"user_media":{},"user_text":"satin white on my 2021 model 3? its blue"},"system_response_to_user_message_0":"Sweet, so satin white on the Model 3 would run $2800 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty.","user_message_1":{"user_media":{},"user_text":"how long do you need it"},"system_response_to_user_message_1":"About 3 to 4 days for the Model 3."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"ok how do i get on the books"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Gloss black on a 2018 audi s5 coupe, its red"},"system_response_to_user_message_0":"Sweet, so gloss black on the S5 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Im ready whenever"},"message_history":{"user_message_0":{"user_media":{},"user_text":"tint on my 2017 corvette, sides and rear 20%"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Corvette would run $300 plus tax for our ceramic tint, it blocks 99% of the UV and 90% of the heat."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"ok im ready for the front end"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Front end ppf on my 2024 tundra"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Tundra would run $1800 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Ready to go, still deciding between the two greys but ill figure that out at the shop"},"message_history":{"user_message_0":{"user_media":{},"user_text":"colored ppf on my 2023 bmw m3, its white. thinking a grey"},"system_response_to_user_message_0":"Sweet, so colored PPF on the M3 would run $6400 plus tax for the full body, and it comes with free side and rear window tint. We've got the whole color book here at the shop too."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"cool im ready"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much for a ceramic coating on my 2022 rav4"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the RAV4 would run $700 plus tax, that covers all the painted surfaces and the coating lasts for years."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Im ready, can I pay the deposit with affirm?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 f150 is blue, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the F150 would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"ready when u are. can i do the night before drop?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"sides and rear and windshield 70 on my 2020 accord"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Accord would run $450 plus tax for our ceramic tint, and adding the windshield is an extra $200, so $650 plus tax all in."}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Yes! I think let’s do the green "},"message_history":{"user_message_0":{"user_media":{},"user_text":"want to wrap my 2024 mach e in a bright color, its white"},"system_response_to_user_message_0":"Sweet, so neon green or neon pink on the Mach-E would run $3450 + tax, do you have an exact green or pink in mind? If you do, can you shoot a pic of it over","user_message_1":{"user_media":{"media_element_0":{"media_description":"brief_description: A solid hot pink image with nothing else in it.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"},"media_element_1":{"media_description":"brief_description: A solid bright neon green image with nothing else in it.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"like this or like this"},"system_response_to_user_message_1":"Either of those would pop on the Mach-E. Let me check the color books to see if we can get something like those done","user_message_2":{"user_media":{},"user_text":"did you hear back on the colors?"},"system_response_to_user_message_2":"Good news, we can get those colors you sent ordered, are you interested in getting on the schedule for that wrap?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"yes lets do it"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2022 tacoma, its white, want green"},"system_response_to_user_message_0":"Sweet, so green on the Tacoma would run $3450 + tax, do you have an exact green in mind? If you do, can you shoot a pic of it over","user_message_1":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Toyota Tacoma wrapped in a gloss dark olive green on an Instagram post, side view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this green"},"system_response_to_user_message_1":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done\nThe material we can order for the wrap is one of these: [pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green, 3. Avery Gloss Forest Green] Which one are you liking?","user_message_2":{"user_media":{},"user_text":"the second one"},"system_response_to_user_message_2":"Perfect, that satin dark green would look clean on the Tacoma, are you interested in getting on the schedule for that wrap?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"yessir that and ceramic coating\nw that free tint of course"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a black Chevy Tahoe parked in a driveway, side view.\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"how much for colored ppf on my 2022 tahoe? and a ceramic coating on top"},"system_response_to_user_message_0":"Sweet, so colored PPF on the Tahoe would run our standard price of $7400 + tax for the full body, since it's a standard color right now, and it comes with free side and rear window tint. A ceramic coating on top would be $350 + tax. Do you have an exact color in mind? If you do, can you shoot a pic of it over","user_message_1":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a bright blue SUV parked on gravel, rear three quarter view.\ntext_overlays: none\nbright_vehicle: yes"}},"user_text":"something like this, and def add the ceramic"},"system_response_to_user_message_1":"Sweet, that bright blue would look clean on the Tahoe, and we can get the ceramic on there too. Let me check the color books to see if we can get something like that done\nThe material we can order for the colored PPF is this one: [pics: 1. Gloss Bright Blue] Does that one work for you?","user_message_2":{"user_media":{},"user_text":"Yeah that works for me"},"system_response_to_user_message_2":"Perfect, that gloss bright blue would look clean on the Tahoe, are you interested in getting on the schedule for that colored PPF?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"yeah"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2022 tacoma, its white, want green"},"system_response_to_user_message_0":"Sweet, so green on the Tacoma would run $3450 + tax, do you have an exact green in mind? If you do, can you shoot a pic of it over","user_message_1":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Toyota Tacoma wrapped in a gloss dark olive green on an Instagram post, side view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this green"},"system_response_to_user_message_1":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done\nThe material we can order for the wrap is one of these: [pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green, 3. Avery Gloss Forest Green] Which one are you liking?","user_message_2":{"user_media":{},"user_text":"the second one"},"system_response_to_user_message_2":"Perfect, that satin dark green would look clean on the Tacoma, are you interested in getting on the schedule for that wrap?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"yeah! how long would you need it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2022 tacoma, its white, want green"},"system_response_to_user_message_0":"Sweet, so green on the Tacoma would run $3450 + tax, do you have an exact green in mind? If you do, can you shoot a pic of it over","user_message_1":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of a Toyota Tacoma wrapped in a gloss dark olive green on an Instagram post, side view.\nservice_ques: a color change wrap\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"this green"},"system_response_to_user_message_1":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done\nThe material we can order for the wrap is one of these: [pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green, 3. Avery Gloss Forest Green] Which one are you liking?","user_message_2":{"user_media":{},"user_text":"the second one"},"system_response_to_user_message_2":"Perfect, that satin dark green would look clean on the Tacoma, are you interested in getting on the schedule for that wrap?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"yessir, do yall take card?"},"message_history":{"user_message_0":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a black Chevy Tahoe parked in a driveway, side view.\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"how much for colored ppf on my 2022 tahoe?"},"system_response_to_user_message_0":"Sweet, so colored PPF on the Tahoe would run our standard price of $7400 + tax for the full body, since it's a standard color right now, and it comes with free side and rear window tint. Do you have an exact color in mind? If you do, can you shoot a pic of it over","user_message_1":{"user_media":{"media_element_0":{"media_description":"brief_description: A photo of a bright blue SUV parked on gravel, rear three quarter view.\ntext_overlays: none\nbright_vehicle: yes"}},"user_text":"something like this"},"system_response_to_user_message_1":"Sweet, that bright blue would look clean on the Tahoe. Let me check the color books to see if we can get something like that done","user_message_2":{"user_media":{},"user_text":"any update on the blue?"},"system_response_to_user_message_2":"Good news, we can get that blue you sent ordered, are you interested in getting on the schedule for that colored PPF?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"yeah lets do 20% all around"},"message_history":{"user_message_0":{"user_media":{},"user_text":"sides and rear on my 2021 camry"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Camry would run $450 + tax for our ceramic tint, it blocks 99% of the UV and 90% of the heat.","user_message_1":{"user_media":{},"user_text":"how long does it take"},"system_response_to_user_message_1":"Usually same day, drop it off in the morning and it's ready by the end of the day. Did you want to hop on the schedule?"}}
    category: booking_service_acknowledge

    state: {"current_user_message":{"user_media":{},"user_text":"Yes I can mater today"},"message_history":{"user_message_0":{"user_media":{},"user_text":"I’m thinking Ppf but I’m not sure what it costs"},"system_response_to_user_message_0":"Colored PPF on the Ranger typically runs $7400 + tax for the full body. That covers all the painted surfaces, and we clay bar your truck and give it a decontamination wash beforehand. What color is it right now? Send me a pic if you can","user_message_1":{"user_media":{},"user_text":"It’s black now\nI don’t have a photo"},"system_response_to_user_message_1":"No worries, so the $7400 + tax I gave you is our typical price, but it does depend on the exact color of the Ranger. If it's not too much trouble could you snap a pic of it whenever you get the chance, that way I can see the exact black"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"yep can do, ill send it tonight"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2021 civic"},"system_response_to_user_message_0":"For sure, a wrap on the Civic typically runs $2950 + tax. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty. What color is it right now? Send me a pic if you can"}}
    category: service_pricing
"""


#ESCALATION
ESCALATION_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"I want a refund"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"The wrap you guys did on my tacoma is already peeling on the hood and its only been 3 weeks. I want my money back"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Something came up and I cant do the wrap anymore. Can I get my deposit back?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"jake.miller@gmail.com"},"system_response_to_user_message_0":"Sweet, just sent that over. As soon as it's paid we'll get you locked in on the calendar for Tuesday the 20th."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"I paid the deposit last week but I need to cancel, how do I get my money back?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Just picked up my car and theres a scratch on the drivers door that wasnt there before"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"the tint you guys did last month has bubbles all over the back window"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A close up of the front bumper of a car in a satin grey wrap that's peeling up along the bottom edge.\nservice_ques: wrap removal or a wrap repair\ntext_overlays: none\nbright_vehicle: no"}},"user_text":"its only been a month and its already doing this"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2020 mustang gt its white, want satin dark grey"},"system_response_to_user_message_0":"Sweet, so satin dark grey on the Mustang would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"The ppf on my hood is lifting at the edges already. Is that covered or what"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Front end ppf on my 2023 camry"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Camry would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"I asked for 35 on the fronts and these are way darker. This isnt what I wanted at all"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Sides and rear on my 2021 f150, 35 on the fronts"},"system_response_to_user_message_0":"Sweet, so sides and rear on the F150 would run $450 plus tax for our ceramic tint."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Your installer cut into my paint on the hood when he was trimming the ppf"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Theres glue all over my door jambs from the wrap, did anyone even check it before giving it back?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Honestly really disappointed with how the car came out, you can see the seams on both doors"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"the tint you did is already bubbling. also how much would the windshield be?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic, 4 doors and the back glass"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"This is the third time Ive messaged about my quote and nobody has gotten back to me. Kinda ridiculous"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need our logo on 2 work trucks, both 2022 f150s, I have the AI file"},"system_response_to_user_message_0":"Perfect, that's everything I need for the 2 F-150s, I'll go over it with our commercial wrap lead and get a price back to you in about 30 minutes."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"You said 5 days and its been 2 weeks. Where is my car??"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"The guy at the front was really rude to my wife when she picked up the truck yesterday"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"The invoice says $3800 but you guys told me $3450. Whats going on"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 f150, its blue, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the F150 would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"I just got charged twice for the deposit??"},"message_history":{"user_message_0":{"user_media":{},"user_text":"jtmiller@gmail.com"},"system_response_to_user_message_0":"Sweet, just sent that over. As soon as it's paid we'll get you locked in on the calendar for Tuesday the 13th."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Affirm denied me. I really wanted to get this done, what am I supposed to do now?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"do you guys do financing?"},"system_response_to_user_message_0":"Yeah, we do financing through Affirm, you can pick it as the way to pay on the estimate we send over."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"my affirm payment isnt going through on the estimate you sent"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Im disputing the charge with my bank"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Worst experience Ive ever had with a shop. Leaving a 1 star review"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"You guys took my deposit 3 weeks ago and still havent called me back to schedule. Starting to think this is a scam"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"wtf the wrap is already coming off the bumper"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2020 mustang gt its white, want satin dark grey"},"system_response_to_user_message_0":"Sweet, so satin dark grey on the Mustang would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"I called twice yesterday and nobody picked up"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"I saw your post about $500 off wraps this month, is that still going?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"is the black friday deal still going on tint? I want the sides and rear"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic, 4 doors and the back glass"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"can I use the promo code from your ad? WRAP20"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: escalation

    state: {"current_user_message":{"user_media":{"media_element_0":{"media_description":"brief_description: A screenshot of an Instagram story from Lone Wraps advertising 20% off full body PPF through the end of the month.\nservice_ques: paint protection film\ntext_overlays: 20% OFF FULL BODY PPF, ENDS 10/31\nbright_vehicle: no"}},"user_text":"can I still get this?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"my buddy said you guys do $100 off if he sent me, can I get that on the front end?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Front end ppf on my 2023 camry"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Camry would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Tristan said hed do the tint for $350 when I called last week"},"message_history":{"user_message_0":{"user_media":{},"user_text":"sides and rear on my 2021 camry"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Camry would run $450 plus tax for our ceramic tint, it blocks 99% of the UV and 90% of the heat."}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Are you guys hiring?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Hey I've been installing ppf and tint for about 4 years, any chance you need another installer?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"can I drop off a resume this week? also what are your hours"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Hi there, Im with Apex Marketing. We help wrap shops get more leads with Google ads, do you have 10 min this week?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"We sell wholesale 3M and Avery vinyl, can I send over our price sheet?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"Would you guys be interested in sponsoring our car show next month?"},"message_history":{}}
    category: escalation

    state: {"current_user_message":{"user_media":{},"user_text":"I run a detail shop down the road, want to start sending each other referrals?"},"message_history":{}}
    category: escalation
"""


#GENERAL TEXT
GENERAL_TEXT_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"hey"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"Hey whats up"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"hey how are you"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"Good morning!"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"you guys do sick work, been following you on insta for a while"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"sorry wrong number"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"😂😂"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"this weather is crazy today"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"what do you drive lol"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"hello?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"hey"},"system_response_to_user_message_0":"What can I help you with?"}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"hey hows it going"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"haha you watching the game tonight?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Front end ppf and tint on the sides and rear for my 2021 mclaren 570s"},"system_response_to_user_message_0":"Sweet, so front end PPF on the 570S would run $2080 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and ceramic tint on the sides and rear is $390 on top since it's a 2 door, and if you wanted to add the windshield that would be an extra $260. Do you know how dark you're wanting to go?"}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"have a good weekend!"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"do you guys sell vinyl rolls?"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"can I buy some ppf film from you guys? want to put it on myself"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"do you guys do interior detailing?"},"message_history":{}}
    category: general_text

    state: {"current_user_message":{"user_media":{},"user_text":"how much for a full detail on my tahoe?"},"message_history":{}}
    category: general_text
"""


#PHONE CALL
PHONE_CALL_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"can I just call you guys?"},"message_history":{}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"Is there a number I can call to talk to someone?"},"message_history":{}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"id rather talk on the phone, can you call me? 801-555-0199"},"message_history":{}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"give me a call when you get a chance"},"message_history":{}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"can I talk to the owner?"},"message_history":{}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"is tristan around? want to call him real quick"},"message_history":{}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"honestly would be easier to talk on the phone"},"message_history":{"user_message_0":{"user_media":{},"user_text":"sides and rear on my 2019 civic"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint."}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"how much for ppf on the front of a 2022 bronco? or can I just call"},"message_history":{}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"lets do it, can I call to get it booked?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: phone_call

    state: {"current_user_message":{"user_media":{},"user_text":"the tint you did last week is already bubbling, I want to talk to someone about this"},"message_history":{}}
    category: phone_call
"""


#END CONVERSATION
END_CONVERSATION_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Ok cool, ill think about it and let you know"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2021 tacoma, its grey, want matte black"},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"Let me talk to my wife first and I'll get back to you"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Front end ppf on my 2023 camry"},"system_response_to_user_message_0":"Sweet, so front end PPF on the Camry would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"thanks for the info!"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much to tint my 2019 civic, 4 doors and the back glass"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Civic would run $450 plus tax for our ceramic tint."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"nah not right now"},"message_history":{"user_message_0":{"user_media":{},"user_text":"sides and rear on my 2021 camry"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Camry would run $450 plus tax for our ceramic tint, it blocks 99% of the UV and 90% of the heat.","user_message_1":{"user_media":{},"user_text":"how long does it take"},"system_response_to_user_message_1":"Usually same day, drop it off in the morning and it's ready by the end of the day. Did you want to hop on the schedule?"}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"Not yet, probably in the spring. Ill reach out"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for colored ppf on my 2021 tahoe? its black"},"system_response_to_user_message_0":"Sweet, so colored PPF on the Tahoe would run $7400 plus tax for the full body, and it comes with free side and rear window tint.","user_message_1":{"user_media":{},"user_text":"how long would you need it"},"system_response_to_user_message_1":"About 4 to 5 days for the full body on the Tahoe. Did you want to get the Tahoe on the schedule?"}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"Appreciate it, thats all I needed"},"message_history":{"user_message_0":{"user_media":{},"user_text":"what time do yall close on fridays?"},"system_response_to_user_message_0":"We're open till 5PM on Fridays."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"gonna shop around a bit but ill keep you guys in mind"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much for a ceramic coating on my 2022 rav4"},"system_response_to_user_message_0":"Sweet, so a ceramic coating on the RAV4 would run $700 plus tax, that covers all the painted surfaces and the coating lasts for years."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"ill hold off for now"},"message_history":{"user_message_0":{"user_media":{},"user_text":"2020 mustang gt its white, want satin dark grey"},"system_response_to_user_message_0":"Sweet, so satin dark grey on the Mustang would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"Need to save up a bit first, ill hit you up in a couple months"},"message_history":{"user_message_0":{"user_media":{},"user_text":"colored ppf on my 2023 bmw m3, its white. thinking a grey"},"system_response_to_user_message_0":"Sweet, so colored PPF on the M3 would run $6400 plus tax for the full body, and it comes with free side and rear window tint. We've got the whole color book here at the shop too."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"Ok thank you\nIll let you know"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want.","user_message_1":{"user_media":{},"user_text":"Does it comes with any warranty?"},"system_response_to_user_message_1":"Yeah, the wrap comes with a 6 month warranty."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"Sounds good, let me check my schedule and ill get back to you"},"message_history":{"user_message_0":{"user_media":{},"user_text":"satin white on my 2021 model 3? its blue"},"system_response_to_user_message_0":"Sweet, so satin white on the Model 3 would run $2800 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty.","user_message_1":{"user_media":{},"user_text":"how long do you need it"},"system_response_to_user_message_1":"About 3 to 4 days for the Model 3."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"ill think about which green and get back to you"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2022 tacoma green, its white"},"system_response_to_user_message_0":"Sweet, so green on the Tacoma would run $3450 plus tax for a full wrap, do you have an exact green in mind? If you do, can you shoot a pic of it over"}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"let me run it by my boss and ill get back to you"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Need our logo and phone number on 3 work vans"},"system_response_to_user_message_0":"Yeah, we can do that. What vans are they, and could you send over the logo?"}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"Thanks, have a good one"},"message_history":{"user_message_0":{"user_media":{},"user_text":"The ppf, does it come with a warranty?"},"system_response_to_user_message_0":"Yeah, PPF comes with a lifetime warranty on any bubbling or peeling from the install."}}
    category: end_conversation

    state: {"current_user_message":{"user_media":{},"user_text":"thanks man, see you tuesday"},"message_history":{"user_message_0":{"user_media":{},"user_text":"jake.miller@gmail.com"},"system_response_to_user_message_0":"Sweet, just sent that over. As soon as it's paid we'll get you locked in on the calendar for Tuesday the 20th."},"just_booked":{"services_pricing":{"Full wrap in matte black":"$3450"},"drop_off_date":"Tuesday, October 20"}}
    category: end_conversation
"""



#**********ALL EXAMPLES**********
#puts every kind's samples together under its name for the router prompt


#ROUTER EXAMPLES
#every route's samples under its name, added under the router question
def examples() -> str:
    return f"""

    # service_pricing
    {SERVICE_PRICING_EXAMPLES} 

    # business_operations
    {BUSINESS_OPERATIONS_EXAMPLES}

    # services_req_humans
    {SERVICES_REQ_HUMANS_EXAMPLES}

    # booking_service_acknowledge
    {BOOKING_SERVICE_ACKNOWLEDGE_EXAMPLES}

    # escalation
    {ESCALATION_EXAMPLES}

    # general_text
    {GENERAL_TEXT_EXAMPLES}

    # phone_call
    {PHONE_CALL_EXAMPLES}

    # end_conversation
    {END_CONVERSATION_EXAMPLES}

 
"""
