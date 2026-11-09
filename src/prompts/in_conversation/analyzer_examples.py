#CHECK EXAMPLES

#yes and no rules plus samples for whether there first message continues a chat with the owner
def in_conversation_examples() -> str:
    return r"""Yes: `current_user_message` picks up a conversation they were already having with the owner outside this chat, so they're someone he already knows, an old customer, a friend or family, a partner or a vendor, and it leans on something between them that `message_history` never shows: their own car, job or visit ("is my truck ready?", "what time you want it tomorrow?", "ok sounds good, see you at 9"), something he said, sent, quoted or asked them for, or asking for it again ("here's the pic you wanted", "how much did you say the full front was again?", "can you resend that quote?", "sent the deposit on zelle"), work the shop already did for them, even when they want more done ("the tint you did last week has a bubble on the back glass", "you guys tinted my civic last year, want to get the tundra done now"), plans or talk only people who know each other have, about their lives, a game, a night out or a holiday ("we still on for saturday?", "sorry I missed your call bro", "happy birthday man", "lmao last night was crazy", "you catch the fight?"), or a business he already works with following up on it, a supplier, a body shop, a detailer or a photographer ("the 3M rolls you ordered ship out today", "we still good for the shoot tuesday?"). A car, a job, a quote, a payment or plans they talk about as already known between them, with a "the", a "that" or an "again" nothing here explains, leans on it too.
No: someone reaching out to the shop for the first time, however short or casual: a greeting on its own ("hi", "hey", "yo"), asking about a service, a price, the hours, the location or booking ("how much to wrap my 2022 model 3?", "do you guys do tint?"), a reply to the shop's own post, story, reel or ad (media with a post_description), a pic, video or link of their vehicle or of a look they want, saying who sent them or where they found the shop ("my buddy said to hit you up", "saw your work on tiktok"), a lead form, someone new pitching the shop something or asking about a job there, or anything else a new customer could send. A "this" or "that" pointing at a post, story, pic or video they sent is about that media, never something between them and the owner. When it isn't clear they already know him, it's No.
Nobody here ever replied to them, so `message_history` is empty or only holds earlier messages of theirs that got no reply. Read all of `current_user_message`, its text and its media. `current_date_time` never changes the answer.
Examples:
state: {"current_user_message":{"user_media":{},"user_text":"is my truck ready to pick up?"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"ok sounds good, see you at 9 tomorrow"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"the tint you did last week has a bubble on the back window, can I swing by?"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"yo we still on for saturday?"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"Sent the deposit on zelle 👍"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"The 3M rolls you ordered ship out today, tracking to follow"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"you guys tinted my civic last year, want to get my new tundra done now"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{"media_element_0":{"media_description(if applicable)":"brief_description: A photo of a white Ford F-150 parked in a driveway, side view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no","post_description(if applicable)":""}},"user_text":"heres the pic you wanted"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"hi"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"How much to wrap my 2022 model 3? its white"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{"media_element_0":{"media_description(if applicable)":"brief_description: A post showing a satin black Toyota Tacoma with its chrome blacked out.\nservice_ques: a color change wrap\ntext_overlays: lone.wraps\nbright_vehicle: no","post_description(if applicable)":"Satin black on this Tacoma, swipe for the before"}},"user_text":"how much for this?"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"my buddy said to hit you up, he got his tint done there. looking to do my civic"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{"media_element_0":{"media_description(if applicable)":"brief_description: A photo of a grey Honda Accord parked in a lot, front three quarter view.\nservice_ques: none visible\ntext_overlays: none\nbright_vehicle: no","post_description(if applicable)":""}},"user_text":""},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"Hi! We sell wholesale vinyl and PPF film to wrap shops, can I send you our price sheet?"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"you guys open saturday?"},"message_history":{}}
answer: False"""
