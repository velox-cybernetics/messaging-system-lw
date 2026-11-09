#CHECK EXAMPLES

#yes and no rules plus samples for whether a business or a bot sent it instead of a person
def spam_examples() -> str:
    return r"""Yes: `current_user_message` is spam, a text a business, a service or a bot sent out instead of a person writing to the shop: ads and offers for whoever has the number (a loan, cash, credit, insurance, an auto warranty or a vehicle coverage plan), alerts and notices (a settlement or claim, an account, a payment, an approval, a delivery, a document to sign or review, a verification code), a notice or offer written to someone else by name like "Kim" or "Dana", a link to click to claim, confirm, sign, review, apply or update something, or anything with an opt out on it like "Reply STOP to opt out", "Reply Stop to Stop" or "Txt STOP to end". It's Yes even when it names a vehicle, and even when the shop already answered one like it in `message_history`.
No: a person writing to the shop: asking about or wanting work done on a vehicle, asking about the shop, a price or booking, sending a pic, a video or a link of their vehicle or of a color they want, small talk, a thanks or a reaction, saying it's a wrong number or texting someone else about their own plans ("hey kim its jess, we still on for lunch?"), telling the shop to stop texting them ("STOP", "stop texting me", "unsubscribe"), a business that wants work done on its own vehicles, someone pitching the shop itself something for its business (marketing, leads, a website, supplies, a collab) or asking about a job there, which a person at the shop answers, and anything from someone already talking with the shop about a job in `message_history`.
Read `current_user_message` in light of `message_history`, oldest first: user_message_N is theirs and system_response_to_user_message_N is the shop's reply to it. When it isn't clear it's spam, it's No. `current_date_time` never changes the answer.
Examples:
state: {"current_user_message":{"user_media":{},"user_text":"SIGNDOCS: Your agreement is ready for your signature. Review and sign here: signdocs-portal.co/Xk29Lp Reply STOP to opt out"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"Hi Dana, your claim payout is waiting on one last step. Confirm here: https://claims-center.co/7Hd2 Txt STOP to end"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"Velo Auto Protect: your vehicle's coverage plan is ready at $52/mo, see the details here: https://vap.co/x8Kq Reply STOP to opt out"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"Good news! You're pre-approved for up to $5,000 with no credit check. Pick your amount and get funded today: qwkfnd.com/a8Hs"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"Your verification code is 482913. Do not share it with anyone."},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"USPS: Your package is on hold due to an incomplete address. Update it within 24 hours: usps-redelivery.info/tr8"},"message_history":{}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"Dana, final notice: your claim closes tonight at 5pm. Confirm now at claims-center.co/9Lq Txt STOP to end"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Hi Dana, your claim payout is waiting on one last step. Confirm here: https://claims-center.co/7Hd2 Txt STOP to end"},"system_response_to_user_message_0":"No worries, looks like that was meant for someone else. Anything you were looking to get done on your car by chance?"}}
answer: True
state: {"current_user_message":{"user_media":{},"user_text":"how much to wrap my 2022 tacoma green, its white"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"this is the green I want https://www.3m.com/3M/en_US/p/d/b5005134007/"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how much to wrap my 2022 tacoma green, its white"},"system_response_to_user_message_0":"Sweet, so green on the Tacoma would run $3450 + tax for a full wrap, do you have an exact green in mind? If you do, can you shoot a pic of it over"}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"sorry wrong number"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"hey kim its jess, we still on for lunch tomorrow?"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"STOP"},"message_history":{"user_message_0":{"user_media":{},"user_text":"sides and rear on my 2021 camry"},"system_response_to_user_message_0":"Sweet, so sides and rear on the Camry would run $450 + tax for our ceramic tint, it blocks 99% of the UV and 90% of the heat. Did you want to hop on the schedule?"}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"Hi! We sell wholesale vinyl and PPF film to wrap shops, can I send Lone Wraps our price sheet?"},"message_history":{}}
answer: False
state: {"current_user_message":{"user_media":{},"user_text":"We have 6 work vans that need our logo and phone number on them, do you guys do fleet wraps?"},"message_history":{}}
answer: False"""
