#**********READING NOTE**********
#reminds the model to read each new text together with the texts that came before it


#CONTEXT NOTE
#pasted into every example set below, so a short reply like "No" gets read with the texts before it
def context_note() -> str:
    return r"""Read `current_user_message` in light of `message_history`, never on its own: a short reply or follow up ("No", "Yes, I do", "Dodge Durango", "What is the price difference?", "how much is just the chrome delete") keeps going on whatever job the earlier turns point it at. A job asked about only in earlier turns does NOT count once the current message moves on to a different one. A job mentioned only to rule it out ("no chrome delete", "hold off on the logos") does NOT count. A message can ask about more than one job, so the other jobs in it, custom or regular (a full wrap in one gloss, satin or matte color, PPF on the front end, full body or windshield, colored PPF, window tint, a ceramic coating), never change the answer. Media in `current_user_message.user_media` counts when the customer's text points at it ("this is what we want", "can you do these?"). `current_date_time` never changes the answer."""



#**********CUSTOM JOBS**********
#examples for spotting which custom job the owner prices himself a customer is asking about


#COMMERCIAL WRAP
#yes and no examples for the custom analyzer's commercial wrap question ("c1")
def commercial_wrap_examples() -> str:
    return rf"""Yes: a wrap or graphics for a business. A full, half or partial wrap, logos, decals, lettering or printed graphics on a business, company or work vehicle, a fleet, a van, box truck, food truck or trailer, business info on it like the company name, a phone number, a website or a QR code, the artwork, design or mock up for it, designing the printed wrap, a Meta form that names a commercial wrap, or a follow up to a commercial wrap quote. An answer to the shop asking whether a business job is a full wrap, a half wrap or just decals ("Full wrap", "half", "decals") is a commercial wrap on any vehicle, a personal car or SUV too, even when they floated a regular color change next to the business, and so is asking whether a price the shop gave was for their business wrap. An old wrap coming off counts only when a new wrap, decals or lettering for a business goes on after it.
No: a wrap on a personal car, truck or SUV with nothing about a business, a graphic wrap, graphics, a printed design, pattern, fade or livery that is only for the look ("Im looking to do a graphic wrap on my car", "can you wrap a cool design on my carbon fiber"), which is a custom wrap, a business wrap they drop outright for a color change ("forget the logo, just want it gloss red"), an old wrap on the vehicle now that they want taken off with nothing said about a new wrap, decals or lettering for a business going on, a business wrap too (the last owner's company wrap on a van they bought), even when the photos show its business name, phone number or website, or when they answer the shop asking about a full wrap, a half wrap or decals with just the removal ("we just want the wrap removed"), which is an old wrap coming off, a chrome delete, or any other job.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey I’m looking to get my 2023 ford transit van a business wrap. What does typical pricing look like?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Full wrap 4 sides art-work provided. 10-year warranty. For my business."}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I need a quote for 2 trailers"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Yes looking for a quote to get some logos on my truck"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_text":"hello my name is Kade Smith, I am looking to get the service of Commercial Wrap the vehicle I have is 2010 Infiniti G37x sedan"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{"media_element_0":{{"media_description(if applicable)":"brief_description: A digital mockup of a white Ford Transit van with a blue company logo, a phone number and a website on the side.\nservice_ques: Commercial wrap or decals.\ntext_overlays: SUMMIT PLUMBING, (801) 555-0142, summitplumbing.com\nbright_vehicle: no","post_description(if applicable)":""}}}},"user_text":"This is what we want on our van, how much would it be?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Custom Commercial"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Hey could I get a quote on a full wrap for a 2024 ford transit low roof?"}},"system_response_to_user_message_0":"Sure! Do you want a solid wrap or like a cusotom commercial wrap?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"No, just llama window cleaning\nIn both sides, and also phone number in the back"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Hey how much do you guys charge ??"}},"system_response_to_user_message_0":"For a full wrap?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"No"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Yes"}},"system_response_to_user_message_0":"What is it that you are looking to get done?","user_message_1":{{"user_media":{{}},"user_text":"Wrap for our business van"}},"system_response_to_user_message_1":"Do you have a mock up made for it already?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Yes, I do"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Im looking to get my 24ft food truck wrapped"}},"system_response_to_user_message_0":"Do you have a photo of the truck and design made?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What is the price difference?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"I have a 2021 Mercedes sprinter van that I'm looking to get some decal work done. I don't want a full color change, but just a good rap that represents our window replacement brand. Wanted to get a rough price on what that would cost."}},"system_response_to_user_message_0":"yes! we can either just install decals or do a half wrap"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much to put my logo and stuff on my truck"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Where you located"}},"system_response_to_user_message_0":"American fork Utah"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"We want to do the a full wrap on the whole fleet "}},"message_history":{{"user_message_0":{{"user_text":"hello my name is d G, I am interested in your services, the vehicle I have is 2024 Ford transit."}},"system_response_to_user_message_0":"Heyy D, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{{"user_media":{{}},"user_text":"Trying to wrap my fleet "}},"system_response_to_user_message_1":"For sure, are you looking for a full wrap, a half wrap or just decals on them?","user_message_2":{{"user_media":{{}},"user_text":"I have 19 vans, and 5 trucks. We want to do our company wrap on all of them "}},"system_response_to_user_message_2":"Yeah, we can do the whole fleet. Quick question, what's the make and model of the trucks?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"They are all transits, the trucks are f150s "}},"message_history":{{"user_message_0":{{"user_text":"hello my name is d G, I am interested in your services, the vehicle I have is 2024 Ford transit."}},"system_response_to_user_message_0":"Heyy D, this is Hazel at the Lone Wraps team, saw your quote request on the Transit. What are you looking to get done?","user_message_1":{{"user_media":{{}},"user_text":"Trying to wrap my fleet "}},"system_response_to_user_message_1":"For sure, are you looking for a full wrap, a half wrap or just decals on them?","user_message_2":{{"user_media":{{}},"user_text":"I have 19 vans, and 5 trucks. We want to do a full wrap on all of them "}},"system_response_to_user_message_2":"Sweet, we can get the full wrap done on the whole fleet. Quick question, what's the make and model of the trucks?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"We got a box truck at auction with the old company's wrap still on it, need that taken off and our own logo and number put on"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you guys do a wrap with a design I made? Its like a galaxy print with some splatter effects on the sides"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Full wrap gloss white with the roof and mirrors in gloss black, its a 2024 model y"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much do you charge for chrome deletes?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Actually hold off on the logos, how much is just the chrome delete on it?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Looking to get our company logo on the doors of our 2022 f150"}},"system_response_to_user_message_0":"Do you have the logo file and a mock up made for it already?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Full wrap "}},"message_history":{{"user_message_0":{{"user_text":"hello my name is g p, I am interested in your services, the vehicle I have is Honda Accord 2021."}},"system_response_to_user_message_0":"Heyy G, this is Hazel at the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?","user_message_1":{{"user_media":{{}},"user_text":"I have a g wagon "}},"system_response_to_user_message_1":"Yeah, what are you looking to get done on the G Wagon?","user_message_2":{{"user_media":{{}},"user_text":"I want to wrap my business on there or do a vinyl wraps whatever makes more sense. "}},"system_response_to_user_message_2":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Wait that’s the business wrap price? "}},"message_history":{{"user_message_0":{{"user_text":"hello my name is g p, I am interested in your services, the vehicle I have is Honda Accord 2021."}},"system_response_to_user_message_0":"Heyy G, this is Hazel at the Lone Wraps team, saw your quote request on the Accord. What are you looking to get done?","user_message_1":{{"user_media":{{}},"user_text":"I have a g wagon "}},"system_response_to_user_message_1":"Yeah, what are you looking to get done on the G Wagon?","user_message_2":{{"user_media":{{}},"user_text":"I want to wrap my business on there or do a vinyl wraps whatever makes more sense. "}},"system_response_to_user_message_2":"For sure, are you looking for a full wrap, a half wrap or just decals on it?","user_message_3":{{"user_media":{{}},"user_text":"Full wrap "}},"system_response_to_user_message_3":"Sweet, a full wrap on the G Wagon typically runs $3450 + tax. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty. What color are you wanting to go, and what color is it right now? Send me a pic if you can"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"prob a half wrap"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"wanna put my dog grooming business on my 2023 cr-v, or maybe just wrap it a different color"}},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"half"}},"message_history":{{"user_message_0":{{"user_text":"hello my name is jordan reyes, I am interested in your services, the vehicle I have is Honda Civic 2020."}},"system_response_to_user_message_0":"Heyy Jordan, this is Hazel at the Lone Wraps team, saw your quote request on the Civic. What are you looking to get done?","user_message_1":{{"user_media":{{}},"user_text":"want my insurance agency name and number on it, or maybe just a full color change, not sure"}},"system_response_to_user_message_1":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"just decals i think"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"my mustang could use my tattoo shop logo on it, or a satin blue wrap, whichever"}},"system_response_to_user_message_0":"Yeah, we can do that. Are you looking for a full wrap, a half wrap or just decals on the Mustang?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"nah forget the logo stuff, just want it wrapped gloss red"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"want my plumbing company on my 2019 charger, or just a color change if that makes more sense"}},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{"media_element_0":{{"media_description":"brief_description: A white high roof Ram ProMaster 2500 cargo van from the side, with a commercial wrap in green and yellow for a lawn care company, a big leaf logo, a phone number and a website. The wrap is faded and peeling along the lower panels.\nservice_ques: commercial wrap or decals\ntext_overlays: GREENLINE LAWN CARE, (385) 555-0148, greenlinelawn.com\nbright_vehicle: no"}},"media_element_1":{{"media_description":"brief_description: The rear doors of the same ProMaster with the lawn care company's logo and phone number printed on the wrap, the vinyl cracked and lifting at the edges.\nservice_ques: commercial wrap, wrap removal\ntext_overlays: GREENLINE LAWN CARE, (385) 555-0148\nbright_vehicle: no"}}}},"user_text":"Hi, I'm looking to get a quote on taking off the vinyl wrap that's on my 2019 Ram ProMaster 2500 now"}},"message_history":{{"user_message_0":{{"user_text":"hello my name is Riley Jensen, I am interested in your services, the vehicle I have is 2019 ram promaster 2500."}},"system_response_to_user_message_0":"Heyy Riley, this is Hazel at the Lone Wraps team, saw your quote request on the ProMaster 2500. What are you looking to get done?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"nah we just want the wrap removed"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"how much to get the old wrap off my transit? its got the last owners business wrap on it, we bought it used"}},"system_response_to_user_message_0":"For sure, are you looking to replace it with a full wrap, a half wrap or just decals on the van?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Im looking to do a graphic wrap on my car"}},"message_history":{{"user_message_0":{{"user_text":"hello my name is Adam Walker, I am interested in your services, the vehicle I have is 2017 Infiniti Q50."}},"system_response_to_user_message_0":"Heyy Adam, this is Hazel at the Lone Wraps team, saw your quote request on the Q50. What are you looking to get done?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"can you wrap a cool design on my carbon fiber"}},"message_history":{{}}}}
answer: False"""


#CUSTOM WRAP
#yes and no examples for the custom analyzer's custom wrap on a personal vehicle question ("c2")
def custom_wrap_examples() -> str:
    return rf"""Yes: a wrap on a personal vehicle that isn't a full wrap in one gloss, satin or matte color. A partial like just the hood, roof, mirrors, pillars, bumpers, a fender, one panel, the top half or just the cab, stripes or racing stripes, a two tone or a piece in its own color or finish next to a full wrap (a gloss black roof, hood, mirrors or pillars), a specialty film like chrome, satin or matte chrome (a chrome gold wrap), color shift, camo, Inozetek, carbon fiber or another textured film, a custom design or effect like a printed design, a fade, flames, a pattern, splatter or a livery, a graphic wrap, graphics or a design on their own car with nothing about a business ("Im looking to do a graphic wrap on my car", "can you wrap a cool design on my carbon fiber"), or a follow up to a custom wrap quote or to the shop asking for the pic of the vehicle and the design ("how much would this cost"). A plain "wrap", "full wrap" or "color change" with no design named is the regular wrap, so No.
No: a full wrap in one gloss, satin or matte color (metallic and pearl colors too), what a full wrap covers (the mirrors, the roof, the door jambs), emblems coming off or getting black replacements as part of a full wrap, anything for a business, company or work vehicle, a fleet, a van, box truck, food truck or trailer, even a half or partial wrap, decals, lettering or a printed design (that is a commercial wrap), covering or blacking out the chrome or the trim, grille, handles or badges (that is a chrome delete), redoing or fixing a wrap that's on the vehicle now on certain panels after an accident, for insurance or because a piece is lifting, interior pieces, a wrap going over hail damage, dents or body damage, or a wrap on a motorcycle, boat, jet ski, RV, motorhome, side by side, UTV, ATV, snowmobile or golf cart with nothing custom asked for (those are jobs the services don't list), PPF, or any other job.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how much to just get the hood wrapped? want it to match the rest of the car, its a forest green outback"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Just want the pillars done in piano black on my 2020 highlander"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"looking to get a tuxedo wrap on my 2023 grand cherokee"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how much to wrap my 2021 supra in matte white with some black accents?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Full wrap gloss white with the roof and mirrors in gloss black, its a 2024 model y"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"No just the roof and mirrors in black"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Hey how much for a wrap on my 2021 tahoe"}},"system_response_to_user_message_0":"For a full wrap?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you do the roof in gloss black too? No chrome delete, the trim on it is already black"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Full wrap satin white on my 2023 tahoe, its black right now"}},"system_response_to_user_message_0":"Sweet, so satin white on the Tahoe would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for two gloss black stripes over the hood and roof on my challenger"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{"media_element_0":{{"media_description(if applicable)":"brief_description: A grey Ford Mustang with two wide gloss black racing stripes over the hood, roof and trunk.\nservice_ques: Racing stripe wrap.\ntext_overlays: none\nbright_vehicle: no","post_description(if applicable)":""}}}},"user_text":"Can you do these on my 2019 mustang?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for chrome gold wrapping for a 2015 chevy corvette"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Whats the price if I go with a color shift instead?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Just looking to get a quote on my 2016 Audi s7 to be fully wrapped in satin white! Its black right now"}},"system_response_to_user_message_0":"Sweet, so satin white on the S7 would run $2950 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you guys do a wrap with a design I made? Its like a galaxy print with some splatter effects on the sides"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"If we could do this or something really similar for $1800 I'd do that for sure\nIs this something we can get scheduled?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Hey! Looking for a partial wrap.\r\n\r\nThis is what I'm wanting. But my budget is around $1500 so if it needs to be less than this I understand"}},"system_response_to_user_message_0":"For something like this, you would probably be looking around 1800. We could simplify it just a little bit more and hit that budget for sure."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Sure, curious on a price. Looking to do either all Matt black with chrome delete of course or the Yukon is a maroon color so would like to do possibly the top half from windows up black"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"hey guys how much to wrap my passenger fender/my bottom half front bumper in solar octane\nthe vehicle got in an accident and they didn't really paint match it during the repair."}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Just above the windshield needs a black wrap. Also look into a ceramic coating on the whole motorhome. Would like to get this done this week if possible"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Yes."}},"system_response_to_user_message_0":"Awesome, what is it that you’re looking to get done on your vehicle?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hi, I am looking for a quote for a 2021 expedition max chrome delete and matte black wrap."}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Does the full wrap cover the door jambs? And how much to add a chrome delete?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"}},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much is just the chrome delete"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Probably"}},"system_response_to_user_message_0":"Okay to add the chrome delete the total would be $650 to do those chrome trim, pillars, and mirror caps.\nAre you still wanting to get the tuxedo wrap?","user_message_1":{{"user_media":{{}},"user_text":"I'm getting 1 other quote and will get back asap!"}},"system_response_to_user_message_1":"Sounds good! let us know!"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What is the price difference?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"I have a 2021 Mercedes sprinter van that I'm looking to get some decal work done. I don't want a full color change, but just a good rap that represents our window replacement brand. Wanted to get a rough price on what that would cost."}},"system_response_to_user_message_0":"yes! we can either just install decals or do a half wrap"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Custom Commercial"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Hey could I get a quote on a full wrap for a 2024 ford transit low roof?"}},"system_response_to_user_message_0":"Sure! Do you want a solid wrap or like a cusotom commercial wrap?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey I’m looking to get my 2023 ford transit van a business wrap. What does typical pricing look like?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"half wrap prob"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"want my hvac company on my 2022 explorer or maybe just a new color, idk which"}},"system_response_to_user_message_0":"For sure, are you looking for a full wrap, a half wrap or just decals on it?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"2023 Audi S3, just looking to black out trim."}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"yeah"}},"system_response_to_user_message_0":"could you remind me what vehicle you were looking to get done"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey so I had my car wrapped by you guys about a year and a half ago. I was recently in an accident and messed up a couple panels. Caliber Collision reached out last week about getting it rewrapped and told me I'd just need to schedule an appointment to get it taken care of"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you do carbon fiber on the center console and the door panels inside?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you guys do motorcycles??"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hello, looking to do chrome delete"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Im looking to do a graphic wrap on my car"}},"message_history":{{"user_message_0":{{"user_text":"hello my name is Adam Walker, I am interested in your services, the vehicle I have is 2017 Infiniti Q50."}},"system_response_to_user_message_0":"Heyy Adam, this is Hazel at the Lone Wraps team, saw your quote request on the Q50. What are you looking to get done?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how much would this cost"}},"message_history":{{"user_message_0":{{"user_text":"hello my name is Adam Walker, I am interested in your services, the vehicle I have is 2017 Infiniti Q50."}},"system_response_to_user_message_0":"Heyy Adam, this is Hazel at the Lone Wraps team, saw your quote request on the Q50. What are you looking to get done?","user_message_1":{{"user_media":{{}},"user_text":"Im looking to do a graphic wrap on my car"}},"system_response_to_user_message_1":"For sure, we can definitely do a graphic wrap on the Q50. Our designer puts the design together with you, from one you already have or from scratch, and we print it all here in house on 3M, Avery or KPMF film. Any peeling or bubbling from the install gets fixed, and every edge gets tucked and trimmed so it doesn't lift. Can you shoot me a pic of the Q50 as it is now, and of the design or look you're going for if you have one?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"can you wrap a cool design on my carbon fiber"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Im looking to do a wrap on my car"}},"message_history":{{"user_message_0":{{"user_text":"hello my name is Adam Walker, I am interested in your services, the vehicle I have is 2017 Infiniti Q50."}},"system_response_to_user_message_0":"Heyy Adam, this is Hazel at the Lone Wraps team, saw your quote request on the Q50. What are you looking to get done?"}}}}
answer: False"""


#PPF REMOVAL
#yes and no examples for the custom analyzer's old ppf coming off question ("c3")
def ppf_removal_examples() -> str:
    return rf"""Yes: PPF or clear bra the customer says is on the vehicle now that they want taken off, redone or replaced. Old, yellowed, peeling, bubbling, torn or chipped PPF getting taken off, redone or replaced, on its own or before a wrap or new film goes on, what taking it off costs or whether that's included, whether it has to come off before new film goes on, or a follow up to a quote for taking it off.
No: new PPF going on with nothing saying there's PPF on the vehicle now, whether the front end, the full body or just one piece like the headlights, the hood or a bumper (new PPF on one piece is the front end or a job the services don't list), even when it comes up as a follow up to another job, an old wrap, chrome delete or tint coming off, whether PPF or a wrap can come off someday down the road, PPF on the vehicle now that a wrap only goes over, which is treated just like the paint with no extra cost and no extra work (saying it's on there, whether the shop can wrap over it, whether it has to come off first or whether that costs more), or any other job.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I'm looking to remove old PPF on the front of my Ineos and Tint my front two windows including the two small safari windows"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Yes, possibly.  I'm looking at picking up a car that has PPF, but it's got several rock marks in it.  I'm told it probably needs to be replaced.  What would it cost to remove and fully replace?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Ok cool. Does that include removing old clear bra?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Looking for a quote on a 2018 Tesla model s for a front end clear bra install. \nBumper\nRight and left fender\nHood\nHeadlights and back of mirrors."}},"system_response_to_user_message_0":"Hey! Full front Ppf on this vehicle is $1600+tax. We can get it done this upcoming week"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Sorry I had my notifications off,  think the front doors might have ppf on it, does it cost to have that removed or do I need to do it before?\nI work in salt lake so I would just need to plan ahead of time to be able to have a different car, hopefully in the month of October though"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"I am looking to get my Tesla y wrapped a nardo gray type color. What would the cost be on that and how long would you need the car?"}},"system_response_to_user_message_0":"That would be $2800, we would need the car for three days\nHow soon are you looking to get this done?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Yeah I love it, I already have a PPF for the front so that would most likely have to come off when wrapping this correct?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"2024 M4 Competition\nWhite"}},"system_response_to_user_message_0":"You’d be about $3300\nThat thing would be insane wrapped lol"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"The clear bra on my hood is yellowing and peeling pretty bad, can you guys take it off and put a new front end on?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Just looking to have my headlights ppfd"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I will let you know I might have found another place that will do it for me here in America fork\nHello good morning I was just wondering how much would it cost I’d do a clear wrap on a 2025 Toyota Rav 4 just the hood for Rock chip protection"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for clear PPF on just the rocker panels of my 2022 4runner?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hi, I have a truck that I had blackout done on, it's peeling off in some areas and was wondering if you could replace it for me."}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for a chrome delete on my 2022 ram 1500? And if I get PPF later can it come off without hurting the paint?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"2020 civic, and could you do clear PPF on just the hood too?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"How much do you charge for chrome deletes?"}},"system_response_to_user_message_0":"What vehicle is it?"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey so I had my car wrapped by you guys about a year and a half ago. I was recently in an accident and messed up a couple panels. Caliber Collision reached out last week about getting it rewrapped and told me I'd just need to schedule an appointment to get it taken care of"}},"message_history":{{}}}}
answer: False"""


#CHROME DELETE
#yes and no examples for the custom analyzer's chrome delete question ("c4")
def chrome_delete_examples() -> str:
    return rf"""Yes: covering or blacking out the chrome on the vehicle. A chrome delete, dechrome, blackout or de-badge, the chrome or silver window trim, grille, bumpers, running boards, roof rails, door handles, mirror caps, emblems or badges wrapped black or in another color, redoing or replacing an old chrome delete that's peeling, or a follow up to a chrome delete quote. Blacking out the window trim, grille, emblems or badges ("blackout", "black out the trim") is a chrome delete even when the message doesn't say they're chrome.
No: a full wrap in a chrome film (a chrome gold wrap, that is a custom wrap), emblems coming off or getting black replacements as part of a full wrap, a roof, hood, pillars or other painted pieces in their own color (that is a custom wrap), a full wrap in one color with nothing about the chrome, interior trim or pieces (that is a job the services don't list), or any other job.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hello, looking to do chrome delete"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much do you charge for chrome deletes?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I'm looking to get the silver part of the grille wrapped black."}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Just looking to cover up some chrome. \nFront and rear bumpers and a small strip along the running boards. Color matching the truck. Ford star white"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hi, I am looking for a quote for a 2021 expedition max chrome delete and matte black wrap."}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Looking for pricing to do a stealth wrap on my wife's 2023 Kia Telluride with some black accents (chrome delete)"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hi, I have a truck that I had blackout done on, it's peeling off in some areas and was wondering if you could replace it for me."}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"2023 Audi S3, just looking to black out trim."}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"yeah"}},"system_response_to_user_message_0":"could you remind me what vehicle you were looking to get done"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"yes\nI was wanting my front and back Mazda sign then the trim around my windows\nif your able to do that"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"ok all good, i'll be there in a minute\ndo you guys also do chrome delete"}},"system_response_to_user_message_0":"Yes, we do. Same car?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much is just the chrome delete"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Probably"}},"system_response_to_user_message_0":"Okay to add the chrome delete the total would be $650 to do those chrome trim, pillars, and mirror caps.\nAre you still wanting to get the tuxedo wrap?","user_message_1":{{"user_media":{{}},"user_text":"I'm getting 1 other quote and will get back asap!"}},"system_response_to_user_message_1":"Sounds good! let us know!"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Yeah crime trim too\nChrome"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Car is white now want a full wrap to black and the door handles red"}},"system_response_to_user_message_0":"Great, we can do that. Are you wanting the chrome trim done red as well? Or just the door handles. And is there chrome trim around the windows or is it black?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Dodge Durango"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Hey i tried to book an estimate with you guys for a chrome delete service but its not working on my end🙏🏾"}},"system_response_to_user_message_0":"What vehicle are you looking to get done?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Sure, curious on a price. Looking to do either all Matt black with chrome delete of course or the Yukon is a maroon color so would like to do possibly the top half from windows up black"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for chrome gold wrapping for a 2015 chevy corvette"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Just want the pillars done in piano black on my 2020 highlander"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Full wrap gloss white with the roof and mirrors in gloss black, its a 2024 model y"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you do the roof in gloss black too? No chrome delete, the trim on it is already black"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Full wrap satin white on my 2023 tahoe, its black right now"}},"system_response_to_user_message_0":"Sweet, so satin white on the Tahoe would run $3450 plus tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I'm looking to remove old PPF on the front of my Ineos and Tint my front two windows including the two small safari windows"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you do carbon fiber on the center console and the door panels inside?"}},"message_history":{{}}}}
answer: False"""


#OTHER JOB
#yes and no examples for the custom analyzer's other job question, for anything the services don't list ("c5")
def other_job_examples() -> str:
    return rf"""Yes: a job that is none of the shop's services and none of the other custom jobs (a commercial wrap, a custom wrap, old PPF or an old wrap coming off, a chrome delete), that the shop doesn't say it won't do. Body work or dents getting fixed, a wrap or film going over hail damage, dents or body damage, clear PPF or clear bra on just one piece or a section of a panel rather than the front end, full body or windshield, a piece the front end doesn't cover (just the rocker panels, just the tailgate) or one it covers (just the hood, the bumper or the headlights) only once a system_response in message_history already offered them the front end and they still want only that piece, redoing a wrap or PPF on certain panels after an accident, for insurance or because a piece is lifting, wheels, rims or calipers, a motorcycle, boat, jet ski or other watercraft, RV or motorhome, side by side or UTV (a Polaris RZR, often typed "razor", a Can-Am Maverick), ATV, snowmobile, golf cart, interior pieces and the like, or a follow up to one of these. A job on a motorcycle, boat or other watercraft, RV or motorhome, side by side, UTV, ATV, snowmobile or golf cart is Yes whatever the job is, and so is a wrap or film on a vehicle with hail damage, dents or body damage, since the owner looks at the damage first.
No: a commercial wrap (any wrap or graphics for a business, a fleet, a van, box truck, food truck or trailer), a custom wrap on the outside of a car, truck or SUV (a partial or one piece in vinyl like just the roof, hood, mirrors or pillars, stripes, a two tone, a specialty film like chrome, carbon fiber or color shift, or a custom design), taking off or redoing PPF or a wrap that's on the vehicle now because it's old or worn, a chrome delete (the chrome, window trim, grille, handles, emblems or badges covered or blacked out, a blackout), a regular job (a full wrap in one gloss, satin or matte color, PPF on the front end, full body or windshield, colored PPF, window tint, a ceramic coating), new clear PPF on pieces the front end covers (the hood, the front bumper, the fenders, the headlights, the mirrors) while no system_response in message_history offered them the front end yet, even when they say just or only those pieces ("Just looking to have my headlights ppfd", "a quote for the whole car and just the front and hood"), which gets the front end offered first, or something the shop says it doesn't do (home window tint, headlight or taillight tint, undercoating, paint work like painting or repainting, chips, scratches or scuffs fixed with paint or a paint color match).
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I only need the bumper done, not the rest of the front"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"how much for clear bra on just the front bumper of my 2021 camry"}},"system_response_to_user_message_0":"Sweet, so front end PPF on the Camry would run $1600 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and it comes with a lifetime warranty. Did you want to get it on the schedule?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"can you just do the hood though? dont need the fenders or mirrors"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"ppf on the hood of my 2024 tacoma, its getting chipped up"}},"system_response_to_user_message_0":"Sweet, so front end PPF on the Tacoma would run $1800 plus tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $6900 plus tax. Which option are you leaning towards?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Just looking to have my headlights ppfd"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I will let you know I might have found another place that will do it for me here in America fork\nHello good morning I was just wondering how much would it cost I’d do a clear wrap on a 2025 Toyota Rav 4 just the hood for Rock chip protection"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hi Tristan, I'm looking to get a section of my front bumper re-wrapped in clear PPF as well as getting a quote for tinting my windows, all side windows and rear window."}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey so I had my car wrapped by you guys about a year and a half ago. I was recently in an accident and messed up a couple panels. Caliber Collision reached out last week about getting it rewrapped and told me I'd just need to schedule an appointment to get it taken care of"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"We just had someone hit and run and bump into our Panamera and dent the bumper. Do you guys have the capability to fix that when we wrap it"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"You guys don't do body work do you?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Would like to get a quote for a full wrap on an 08 Silverado 2500 crew cab short bed in gloss black"}},"system_response_to_user_message_0":"We can get a full wrap done on this vehicle for $3450 plus tax"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you guys do motorcycles??"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how much to wrap my 2022 yamaha r1 in matte black? need it done before a race next week"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"what would you charge to wrap my sea doo?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how much to wrap a 2022 can am maverick x3 max in matte grey?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"do yall do sleds too? looking to wrap my arctic cat"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"my 2018 camry has hail dents all over the roof and hood, could you still wrap it?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Just above the windshield needs a black wrap. Also look into a ceramic coating on the whole motorhome. Would like to get this done this week if possible"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Yes."}},"system_response_to_user_message_0":"Awesome, what is it that you’re looking to get done on your vehicle?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Do you guys wrap wheels or calipers?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for clear PPF on just the rocker panels of my 2022 4runner?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you do carbon fiber on the center console and the door panels inside?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hello, looking to do chrome delete"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I'm looking to remove old PPF on the front of my Ineos and Tint my front two windows including the two small safari windows"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you guys take the old wrap off my 2019 camaro? its peeling pretty bad"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for two gloss black stripes over the hood and roof on my challenger"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how much to just get the hood wrapped? want it to match the rest of the car, its a forest green outback"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I'm looking to get the silver part of the grille wrapped black."}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"2023 Audi S3, just looking to black out trim."}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"yeah"}},"system_response_to_user_message_0":"could you remind me what vehicle you were looking to get done"}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I need a quote for 2 trailers"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey I’m looking to get my 2023 ford transit van a business wrap. What does typical pricing look like?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much to tint my headlights? And how much for a chrome delete on my 2021 charger?"}},"message_history":{{}}}}
answer: False"""


#WRAP REMOVAL
#yes and no examples for the custom analyzer's old wrap coming off question ("c6")
def wrap_removal_examples() -> str:
    return rf"""Yes: a vinyl wrap the customer says is on the vehicle now, all of it or some of its panels, getting taken off, redone, re-wrapped or replaced, because it's old, peeling, cracking, faded or bubbling or because they just want it gone, what taking it off costs or whether that's included, whether it has to come off before a new wrap, PPF or colored PPF goes on, or a follow up to a quote for taking it off. A business wrap counts the same, its logos, lettering and business info and all (the last owner's company wrap on a van they bought), even when the photos show a business name, a phone number or a website on it.
No: a wrap named only as the color the vehicle is now, with nothing about it coming off, getting redone or the shape it's in ("its wrapped white right now, want satin black"), whether a wrap or PPF can come off someday down the road, a wrap or PPF on certain panels getting redone after an accident, for insurance or because one piece is lifting (that is a job the services don't list), old PPF or clear bra coming off, an old chrome delete or blackout getting redone, old tint coming off, old decals or lettering on a business vehicle that isn't wrapped (that is a commercial wrap), or any other job.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"So this the current wrap i have on my car at them moment, but its currently peeling now. Its been on for about 5 years. Is this somthing you guys could do again?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can you guys take the old wrap off my 2019 camaro? its peeling pretty bad"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey whats up I was wondering what you guys would charge to re wrap my 2020 model 3, the wrap on it is old and peeling everywhere. Its matte black right now, want to go gloss white"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey Tristan, I was hoping I could schedule a time to have you remove the wrap on my cars sensors?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"When are you able to remove the wrap and how long does it take? I want to get some body work repair done after it is removed and before the new wrap is on it"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for colored ppf? And there would be an existing wrap removal as well."}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Whats a full wrap run on my 2016 tesla model s? Its wrapped white right now, want satin black"}},"system_response_to_user_message_0":"Sweet, so satin black on the Model S would run $2800 plus tax for the new wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"like 4 years"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Can you guys take the old wrap off my 2019 camaro? its peeling pretty bad"}},"system_response_to_user_message_0":"Yeah, we can take the old wrap off. How long has it been on, and do you have a photo of it?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{"media_element_0":{{"media_description(if applicable)":"brief_description: The hood and front bumper of a Chevrolet Camaro in a matte gray wrap that's cracked and peeling along the edges.\nservice_ques: wrap removal\ntext_overlays: none\nbright_vehicle: no","post_description(if applicable)":""}}}},"user_text":""}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Can you guys take the old wrap off my 2019 camaro? its peeling pretty bad"}},"system_response_to_user_message_0":"Yeah, we can take the old wrap off. How long has it been on, and do you have a photo of it?","user_message_1":{{"user_media":{{}},"user_text":"like 4 years"}},"system_response_to_user_message_1":"Perfect, we can get the old wrap off the Camaro. Do you have a photo of it as it is now?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{"media_element_0":{{"media_description":"brief_description: A white high roof Ram ProMaster 2500 cargo van from the side, with a commercial wrap in green and yellow for a lawn care company, a big leaf logo, a phone number and a website. The wrap is faded and peeling along the lower panels.\nservice_ques: commercial wrap or decals\ntext_overlays: GREENLINE LAWN CARE, (385) 555-0148, greenlinelawn.com\nbright_vehicle: no"}},"media_element_1":{{"media_description":"brief_description: The rear doors of the same ProMaster with the lawn care company's logo and phone number printed on the wrap, the vinyl cracked and lifting at the edges.\nservice_ques: commercial wrap, wrap removal\ntext_overlays: GREENLINE LAWN CARE, (385) 555-0148\nbright_vehicle: no"}}}},"user_text":"Hi, I'm looking to get a quote on taking off the vinyl wrap that's on my 2019 Ram ProMaster 2500 now"}},"message_history":{{"user_message_0":{{"user_text":"hello my name is Riley Jensen, I am interested in your services, the vehicle I have is 2019 ram promaster 2500."}},"system_response_to_user_message_0":"Heyy Riley, this is Hazel at the Lone Wraps team, saw your quote request on the ProMaster 2500. What are you looking to get done?"}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"We got a box truck at auction with the old company's wrap still on it, need that taken off and our own logo and number put on"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Whats a full wrap run on my 2016 tesla model s? Its wrapped white right now, want satin black"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hi. Curious how much it is to remove the wrap after the fact? And what are the common issues you see after removing a wrap?\nLeaning towards getting matte black on my 2023 raptor"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey so I had my car wrapped by you guys about a year and a half ago. I was recently in an accident and messed up a couple panels. Caliber Collision reached out last week about getting it rewrapped and told me I'd just need to schedule an appointment to get it taken care of"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hi, I have a truck that I had blackout done on, it's peeling off in some areas and was wondering if you could replace it for me."}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"The clear bra on my hood is yellowing and peeling pretty bad, can you guys take it off and put a new front end on?"}},"message_history":{{}}}}
answer: False"""
