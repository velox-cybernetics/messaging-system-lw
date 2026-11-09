#CHECK EXAMPLES

#yes and no rules plus samples for whether everything she'd ask the owner about is small
def small_ask_examples() -> str:
    return r"""Yes: every thing SYSTEM_RESPONSE says she isn't sure on and will ask the owner about is something small about coming to the shop, the kind of thing that never changes the job, the price or the booking: the wifi, what's in the waiting area (a bathroom, coffee, snacks, a TV, outlets, seating), parking or the lot (where to park, whether it's gated, leaving the car there overnight), EV charging, bringing a kid or a dog along, or merch like stickers or shirts.
No: any of it is about a job or a service (whether the shop does something, how, on what, or wrapping over something), a price, a fee, a payment or financing, the hours, a holiday or a day, booking, the warranty, insurance or what it covers, a license, hiring, gift cards, a deal, a discount, a referral, a collab, or anything else only the owner can decide.
SYSTEM_RESPONSE is the reply going out. The part where she says she isn't sure and will ask the owner is the one that counts, everything else it answers never changes the answer. `current_date_time` never changes the answer.
Examples:
state: {"current_user_message":{"user_media":{},"user_text":"what are your hours, and do you guys have wifi?"},"message_history":{}}
system_response: We're open Monday through Friday 9AM to 5PM, and closed weekends. As for the wifi, tbh I'm not sure 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner.
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"is there parking out front?"},"message_history":{}}
system_response: tbh I'm not sure on the parking 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner.
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"Is there a bathroom in the waiting area? I'll have my kid with me"},"message_history":{}}
system_response: Honestly I'm not sure on the bathroom 😅 I'm still new here so I'm learning the ropes, but I'll ask the owner.
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"how much to wrap my 2022 tacoma? its white, want satin black. also do you guys have wifi i can use while i wait"},"message_history":{}}
system_response: Sweet, satin black on the Tacoma would run $3450 + tax for a full wrap. Our vinyl wraps use high quality film and it does also come with a free 6 month warranty.\nAs for the wifi, tbh I'm not sure 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"is there a fee if I pay with card or is cash better"},"message_history":{}}
system_response: Any card or cash works. As for a card fee, tbh I'm not sure 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner.
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"are you guys open on christmas eve?"},"message_history":{}}
system_response: tbh I'm not sure on Christmas Eve hours 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner.
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"Are you guys hiring?"},"message_history":{}}
system_response: tbh I'm not sure on that one 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner.
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"My buddy got his rims wrapped at another shop, can you guys wrap my rims too?"},"message_history":{}}
system_response: tbh I'm not sure on wrapping the rims 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"if yall scratch my paint who pays for it?? are u insured"},"message_history":{}}
system_response: Yeah, we're insured. tbh I'm not sure on exactly what it covers though 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner.
answer: False"""

#yes and no rules plus samples for whether they asked again about her small ask to the owner
def persist_examples() -> str:
    return r"""Yes: `current_user_message` asks about the small thing a system_response in `message_history` said she wasn't sure on and would ask the owner about, again, in any words: asking it again ("so is there wifi or not?"), following up on it ("any word on the parking?", "did you ask him yet?"), or pushing for the answer ("I really need to know if there's wifi, I have to work while I wait"), even when the message asks something else too.
No: it doesn't bring that thing up again: an ok, a thanks or a "no worries" taking it in, small talk, a different question, going ahead with the job, or answering something else the shop asked.
Read `current_user_message` in light of `message_history`. `current_date_time` never changes the answer.
Examples:
state: {"current_user_message":{"user_media":{},"user_text":"so is there wifi or not??"},"message_history":{"user_message_0":{"user_media":{},"user_text":"do you guys have wifi in the waiting area?"},"system_response_to_user_message_0":"Honestly I'm not sure on the wifi 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner."}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"any word on the parking? im heading over tomorrow"},"message_history":{"user_message_0":{"user_media":{},"user_text":"is there parking out front?"},"system_response_to_user_message_0":"tbh I'm not sure on the parking 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner."}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"did you ask him yet"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Is there a bathroom in the waiting area? I'll have my kid with me"},"system_response_to_user_message_0":"Honestly I'm not sure on the bathroom 😅 I'm still new here so I'm learning the ropes, but I'll ask the owner."}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"ok no worries"},"message_history":{"user_message_0":{"user_media":{},"user_text":"do you guys have wifi in the waiting area?"},"system_response_to_user_message_0":"Honestly I'm not sure on the wifi 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner."}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"cool, how much for tint on a 2021 civic?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"is there parking out front?"},"system_response_to_user_message_0":"tbh I'm not sure on the parking 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner."}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"thanks! ill just bring my hotspot"},"message_history":{"user_message_0":{"user_media":{},"user_text":"what are your hours, and do you guys have wifi?"},"system_response_to_user_message_0":"We're open Monday through Friday 9AM to 5PM, and closed weekends. As for the wifi, tbh I'm not sure 😅 I'm still learning the ropes here since I'm new, but I'll ask the owner."}}
answer: False"""
