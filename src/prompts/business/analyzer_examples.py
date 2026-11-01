#**********READING NOTE**********
#reminds the model to read each new text together with the texts that came before it


#CONTEXT NOTE
#pasted into every example set below, so a short follow up gets read with the texts before it
def context_note() -> str:
    return r"""Read `current_user_message` in light of `message_history`, never on its own: a short or vague follow up ("cool, and the address?", "what about email?", "and on sunday?") asks about whatever the earlier turns point it at. A detail asked about only in earlier turns does NOT count once the current message moves on to a different one. A detail mentioned only to rule it out ("I don't need the phone") does NOT count. `current_date_time` never changes the answer."""



#**********SHOP BASICS**********
#examples for spotting questions about the shop's hours, its years in business, its name and owner


#HOURS
#yes and no examples for the business analyzer's hours question ("b1")
def hours_examples() -> str:
    return rf"""Yes: when the shop is open or closed. Hours, opening or closing time, open today, tomorrow, this weekend, on a holiday or right now, "can I swing by at 4".
No: how long a job takes (turnaround), how long the shop has been in business, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Hey you guys open on Saturday?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"yall open tmr and saturday"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What are your hours and what's the address?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Are you open right now? Forget the address, I'll use GPS."}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"are you guys open on thanksgiving"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"and on saturday?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"yall open friday?"}},"system_response_to_user_message_0":"Yeah, Friday we're open 9AM to 5PM."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How long has Lone Wraps been around?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How long would you need my car for?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Cool, and the address?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Hey you guys open on Friday?"}},"system_response_to_user_message_0":"Yeah, Friday we're open 9AM to 5PM."}}}}
answer: False"""


#BUSINESS YEARS
#yes and no examples for the business analyzer's years in business question ("b2")
def years_in_business_examples() -> str:
    return rf"""Yes: how long the shop has been around or when it started. "how long have you been in business", "when did you start", "how long has he been doing this", experience as a shop.
No: how long a job takes, the hours, who owns the shop, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How long has Lone Wraps been around?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Who owns the shop and how long have they been doing this?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"And how long has he been running it?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Whos the owner over there?"}},"system_response_to_user_message_0":"The owner is Tristan Walker."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How long does a full wrap take?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Who's the owner of the shop?"}},"message_history":{{}}}}
answer: False"""


#BUSINESS NAME
#yes and no examples for the business analyzer's shop name question ("b3")
def business_name_examples() -> str:
    return rf"""Yes: confirming or asking the name of the shop. "is this Lone Wraps", "what's the shop called", "did I reach the right shop", "is this the right number for Lone Wraps".
No: asking for the phone number to call, the owner's name, who they are talking to, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Is this the right number for Lone Wraps?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"what's the name of the shop again"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Best number to call for a quote?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"who am I talking to?"}},"message_history":{{}}}}
answer: False"""


#OWNER
#yes and no examples for the business analyzer's owner question ("b4")
def owner_examples() -> str:
    return rf"""Yes: who owns or runs the shop. "who's the owner", "who runs the shop", "who started this".
No: how many people work there, who they are talking to right now, how long the shop has been around, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Who's the owner of the shop?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Who owns the shop and how long have they been doing this?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How big is your crew over there?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"And how long has he been running it?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Whos the owner over there?"}},"system_response_to_user_message_0":"The owner is Tristan Walker."}}}}
answer: False"""



#**********CONTACT INFO**********
#examples for spotting questions about where the shop is and how to call, email or find it online


#SHOP ADDRESS
#yes and no examples for the business analyzer's address and drop off question ("b5")
def address_examples() -> str:
    return rf"""Yes: where the shop is or how getting the car there works. "where are you located", "what's your address", "what city are you in", "GPS isn't finding you", whether the shop is mobile or comes to them, whether they can wait there or drop the car off.
No: "where can I find you online" (that is the website), an address they ruled out ("forget the address"), or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What's your address? GPS isn't finding you."}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What are your hours and what's the address?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Cool, and the address?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Hey you guys open on Friday?"}},"system_response_to_user_message_0":"Yeah, Friday we're open 9AM to 5PM."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"do you guys come to me or do I have to bring it in?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"can I just drop it off and grab it later?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Where can I find you online?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Are you open right now? Forget the address, I'll use GPS."}},"message_history":{{}}}}
answer: False"""


#CONTACT PHONE
#yes and no examples for the business analyzer's phone number question ("b6")
def phone_examples() -> str:
    return rf"""Yes: the phone number to call or text. "phone number", "what's your number", "best number to reach you", "how can I contact you" with no channel named.
No: an email address, a phone number they ruled out ("I don't need the phone"), or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Best number to call for a quote?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Phone number, email, and website please"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how can I contact you guys"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Wats ur number"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Full gloss black on my 2019 chrysler 300, its silver"}},"system_response_to_user_message_0":"Sweet, so gloss black on the 300 would run $2950 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I don't need the phone, just give me the email"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What about email?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Whats the best number to reach you guys at?"}},"system_response_to_user_message_0":"You can reach us at (855) 494-1645."}}}}
answer: False"""


#CONTACT EMAIL
#yes and no examples for the business analyzer's email question ("b7")
def email_examples() -> str:
    return rf"""Yes: an email address to send a message or pictures to. "email address", "where do I email", "is there an email".
No: the phone number, the website, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Do you have an email I can send pictures to?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I don't need the phone, just give me the email"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What about email?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Whats the best number to reach you guys at?"}},"system_response_to_user_message_0":"You can reach us at (855) 494-1645."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Best number to call for a quote?"}},"message_history":{{}}}}
answer: False"""


#WEBSITE
#yes and no examples for the business analyzer's website question ("b8")
def website_examples() -> str:
    return rf"""Yes: the shop's website or finding it online. "do you have a website", "what's your site", "is there an online quote form", "where can I find you online".
No: the physical address, social media like Instagram, the email, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Got a website I can look at?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Where can I find you online?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Phone number, email, and website please"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Whats your instagram?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What's your address? GPS isn't finding you."}},"message_history":{{}}}}
answer: False"""



#**********TEAM AND TRUST**********
#examples for spotting questions about the crew, the license and insurance, and who is texting them


#EMPLOYEE COUNT
#yes and no examples for the business analyzer's team size question ("b9")
def employees_examples() -> str:
    return rf"""Yes: how many people work at the shop. "how many people work there", "how big is the team", "how many installers do you have".
No: who owns the shop, who they are talking to, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How big is your crew over there?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how many installers yall got"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Who's the owner of the shop?"}},"message_history":{{}}}}
answer: False"""


#LICENSE INSURANCE
#yes and no examples for the business analyzer's license and insurance question ("b10")
def license_examples() -> str:
    return rf"""Yes: whether the shop is licensed, registered, insured or legit. "are you licensed", "license number", "are you a registered business", "are you insured", "do you have insurance in case something happens to my car", "are you guys legit".
No: the warranty, whether tint is street legal, their own insurance paying for a job (a claim after an accident), or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Are you guys licensed and registered?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Ok whats the license number?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"Are you guys licensed and registered?"}},"system_response_to_user_message_0":"Yeah, we're registered in the state of Texas."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Are you guys insured?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Do you guys have insurance? In case you mess up a piece"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"2021 tacoma, its grey, want matte black"}},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"is the tint legal in utah"}},"message_history":{{}}}}
answer: False"""


#PERSON TALKING
#yes and no examples for the business analyzer's who am i talking to question ("b11")
def person_talking_to_examples() -> str:
    return rf"""Yes: who the customer is talking to right now, or whether this is a bot or a real person. "who am I talking to", "what's your name", "is this a bot", "am I talking to a real person".
No: who owns the shop, the name of the shop, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"who am I talking to?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"whats your name btw"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Wait is this a bot?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"yall open friday?"}},"system_response_to_user_message_0":"Yeah, Friday we're open 9AM to 5PM."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Who's the owner of the shop?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Is this the right number for Lone Wraps?"}},"message_history":{{}}}}
answer: False"""



#**********MORE DETAILS**********
#examples for spotting questions about paying, social media, financing, or the business as a whole


#PAYMENTS ACCEPTED
#yes and no examples for the business analyzer's payment methods question ("b12")
def payments_examples() -> str:
    return rf"""Yes: which payment methods the shop takes, or whether there is tax and how much it is. "do you take card", "can I pay cash", "do yall take zelle", "is there tax on that", "how much is tax".
No: financing or payment plans, the price of a job, the deposit, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"do yall take card or cash only"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"can I pay with zelle?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"do you guys do financing"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how much is the deposit"}},"message_history":{{}}}}
answer: False"""


#SOCIAL MEDIA
#yes and no examples for the business analyzer's social media question ("b13")
def social_media_examples() -> str:
    return rf"""Yes: the shop's social media. "whats your instagram", "are you on facebook", "do you have a tiktok", "anywhere I can follow you".
No: the website, the email, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Whats your instagram?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"you guys on social media? want to see more of your work"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Got a website I can look at?"}},"message_history":{{}}}}
answer: False"""


#FINANCING
#yes and no examples for the business analyzer's financing question ("b14")
def financing_examples() -> str:
    return rf"""Yes: financing or paying for the job over time. "do you guys do financing", "can I make payments on it", "do you take affirm", "any payment plans", "can I finance a wrap".
No: which payment methods the shop takes (card, cash, zelle), the price of a job, the deposit, or any other detail.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"do you guys do financing"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Is there any way to make payments on it?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"2021 tacoma, its grey, want matte black"}},"system_response_to_user_message_0":"Sweet, so matte black on the Tacoma would run $3450 plus tax for a full wrap, and that wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"do yall take card or cash only"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"how much is the deposit"}},"message_history":{{}}}}
answer: False"""


#GENERAL BUSINESS
#yes and no examples for the business analyzer's general question, asked about the business as a whole
def general_business_examples() -> str:
    return rf"""Yes: the business in general, not one detail in particular. "I have some questions about your business", "can I ask you a few questions about the shop", "tell me about your business", "what can you tell me about Lone Wraps", "I'd like some info on you guys", "tell me more about the company". A message that asks about the business in general along with one detail ("tell me a bit about the shop, and where are you located?") is still Yes.
No: one or more details named with nothing asked about the business in general (the hours, how long the shop has been around, its name, the owner, the address, the phone number, email, website, how many people work there, the license or insurance, who they are talking to, payments, social media or financing), or a question about a service, a price or a job on their car.
{context_note()}
Examples:
state: {{"current_user_message":{{"user_media":{{}},"user_text":"I have some questions about your business"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Can I ask you guys a few questions about the shop?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Tell me about your business"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"what can you tell me about lone wraps"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Tell me a bit about the shop, and where are you located?"}},"message_history":{{}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Cool, and can you tell me more about the company?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"yall open friday?"}},"system_response_to_user_message_0":"Yeah, Friday we're open 9AM to 5PM."}}}}
answer: True
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Are you guys open today"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"What are your hours and what's the address?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"Who's the owner of the shop?"}},"message_history":{{}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"and on saturday?"}},"message_history":{{"user_message_0":{{"user_media":{{}},"user_text":"yall open friday?"}},"system_response_to_user_message_0":"Yeah, Friday we're open 9AM to 5PM."}}}}
answer: False
state: {{"current_user_message":{{"user_media":{{}},"user_text":"How much for a wrap on my 2023 raptor?"}},"message_history":{{}}}}
answer: False"""
