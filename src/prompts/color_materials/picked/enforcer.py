#**********EXAMPLES**********
#sample replies to a customer picking one of the closest materials, each marked as breaking the rules or not


#CHECK EXAMPLES
#the sample replies added to the end of the check, each marked as breaking the rules or not
def examples() -> str:
    return r"""
    #Examples
    STATE: {"current_date_time":"Tuesday, October 27, 2026 at 02:06 PM","current_user_message":{"user_media":{},"user_text":"yeah I will throw windshield in there but pick shade when I get there\nyeah I like that one\nalmost exact match lol"},"message_history":{"system_response_to_user_message_5":"Yeah, the free tint covers the sides and rear, so you can pick any shade on those, the front two max out at 20% and the rear can go down to 5%, and the price stays the same no matter the shade\nIf you wanted to add the windshield that would be an extra $260 + tax, and that one only comes in 70% or 50%, were you thinking one of those?\nThe material we can order for the colored PPF is this one: [pics: 1. Gray] Does that one work for you?"}}
    SHOP_LAST_REPLY:
    Yeah, the free tint covers the sides and rear, so you can pick any shade on those, the front two max out at 20% and the rear can go down to 5%, and the price stays the same no matter the shade
    If you wanted to add the windshield that would be an extra $260 + tax, and that one only comes in 70% or 50%, were you thinking one of those?
    The material we can order for the colored PPF is this one: [pics: 1. Gray] Does that one work for you?
    SYSTEM_RESPONSE:
    Yeah, the free tint covers the sides and rear, so you can pick any shade on those, the front two max out at 20% and the rear can go down to 5%, and the price stays the same no matter the shade
    If you wanted to add the windshield that would be an extra $260 + tax, and that one only comes in 70% or 50%. And that gray would look clean on the Regera, are you interested in getting on the schedule for that colored PPF?
    answer: True
    REASON: The tint and windshield answers were already in the shop's last reply, so they go out a second time (rule 1).

    STATE: {"current_date_time":"Tuesday, October 27, 2026 at 02:06 PM","current_user_message":{"user_media":{},"user_text":"yeah I will throw windshield in there but pick shade when I get there\nyeah I like that one\nalmost exact match lol"},"message_history":{"system_response_to_user_message_5":"Yeah, the free tint covers the sides and rear, so you can pick any shade on those, the front two max out at 20% and the rear can go down to 5%, and the price stays the same no matter the shade\nIf you wanted to add the windshield that would be an extra $260 + tax, and that one only comes in 70% or 50%, were you thinking one of those?\nThe material we can order for the colored PPF is this one: [pics: 1. Gray] Does that one work for you?"}}
    SHOP_LAST_REPLY:
    Yeah, the free tint covers the sides and rear, so you can pick any shade on those, the front two max out at 20% and the rear can go down to 5%, and the price stays the same no matter the shade
    If you wanted to add the windshield that would be an extra $260 + tax, and that one only comes in 70% or 50%, were you thinking one of those?
    The material we can order for the colored PPF is this one: [pics: 1. Gray] Does that one work for you?
    SYSTEM_RESPONSE:
    Perfect, that gray would look clean on the Regera, are you interested in getting on the schedule for that colored PPF?
    answer: False

    STATE: {"current_date_time":"Tuesday, October 27, 2026 at 02:06 PM","current_user_message":{"user_media":{},"user_text":"yeah I will throw windshield in there but pick shade when I get there\nyeah I like that one\nalmost exact match lol"},"message_history":{"system_response_to_user_message_5":"Yeah, the free tint covers the sides and rear, so you can pick any shade on those, the front two max out at 20% and the rear can go down to 5%, and the price stays the same no matter the shade\nIf you wanted to add the windshield that would be an extra $260 + tax, and that one only comes in 70% or 50%, were you thinking one of those?\nThe material we can order for the colored PPF is this one: [pics: 1. Gray] Does that one work for you?"}}
    SHOP_LAST_REPLY:
    Yeah, the free tint covers the sides and rear, so you can pick any shade on those, the front two max out at 20% and the rear can go down to 5%, and the price stays the same no matter the shade
    If you wanted to add the windshield that would be an extra $260 + tax, and that one only comes in 70% or 50%, were you thinking one of those?
    The material we can order for the colored PPF is this one: [pics: 1. Gray] Does that one work for you?
    SYSTEM_RESPONSE:
    Yeah I will throw windshield in there but pick shade when I get there. And that gray would look clean on the Regera, are you interested in getting on the schedule for that colored PPF?
    answer: True
    REASON: It says the customer's own message back to them as if it were the shop talking (rule 2).

    STATE: {"current_date_time":"Monday, October 26, 2026 at 12:05 PM","current_user_message":{"user_media":{},"user_text":"yeah that works"},"message_history":{"system_response_to_user_message_1":"Yeah, the wrap comes with a 6 month warranty on the install\nThe material we can order for the wrap is this one: [pics: 1. Avery Satin Dark Green] Does that one work for you?"}}
    SHOP_LAST_REPLY:
    Yeah, the wrap comes with a 6 month warranty on the install
    The material we can order for the wrap is this one: [pics: 1. Avery Satin Dark Green] Does that one work for you?
    SYSTEM_RESPONSE:
    Yeah, the wrap comes with a 6 month warranty on the install. And that satin dark green would look clean on the Tacoma, are you interested in getting on the schedule for that wrap?
    answer: True
    REASON: The warranty answer goes out again word for word from the shop's last reply (rule 1).

    STATE: {"current_date_time":"Monday, October 26, 2026 at 12:05 PM","current_user_message":{"user_media":{},"user_text":"yeah that works, how long was the warranty again?"},"message_history":{"system_response_to_user_message_1":"Yeah, the wrap comes with a 6 month warranty on the install\nThe material we can order for the wrap is this one: [pics: 1. Avery Satin Dark Green] Does that one work for you?"}}
    SHOP_LAST_REPLY:
    Yeah, the wrap comes with a 6 month warranty on the install
    The material we can order for the wrap is this one: [pics: 1. Avery Satin Dark Green] Does that one work for you?
    SYSTEM_RESPONSE:
    The wrap comes with a 6 month warranty on the install. And that satin dark green would look clean on the Tacoma, are you interested in getting on the schedule for that wrap?
    answer: False
    REASON: They asked for the warranty again, so saying it again answers them (rule 1).

    STATE: {"current_date_time":"Monday, October 26, 2026 at 12:05 PM","current_user_message":{"user_media":{},"user_text":"the satin one, how long would the wrap take?"},"message_history":{"system_response_to_user_message_0":"Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done\nThe material we can order for the wrap is one of these: [pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green] Which one are you liking?"}}
    SHOP_LAST_REPLY:
    Sweet, that green would look clean on the Tacoma. Let me check the color books to see if we can get something like that done
    The material we can order for the wrap is one of these: [pics: 1. 3M Gloss Dark Green, 2. Avery Satin Dark Green] Which one are you liking?
    SYSTEM_RESPONSE:
    We'd need the Tacoma for about 4 to 5 days for the wrap. And that satin dark green would look clean on it, are you interested in getting on the schedule for that wrap?
    answer: False
"""



#**********INSTRUCTIONS**********
#what makes a reply to a material pick break the rules


#CHECK INSTRUCTIONS
#the rules a reply to a material pick gets checked against, with the samples on the end
def instructions() -> str:
    instructions_text: str = """
    #Context
    -STATE is the conversation, SHOP_LAST_REPLY is the shop's last reply on its own, and SYSTEM_RESPONSE is the reply about to go out after the customer picked one of the materials the shop sent.

    #Rules To Enforce
    -The response breaks a rule when:
    1. It says again an answer, a price or a line SHOP_LAST_REPLY already gave, word for word or close to it, when current_user_message didn't ask for it again.
    2. It says the customer's own words back to them, or writes as the customer ("I will", "I like that one") instead of as the shop.
    3. It asks more than one question, or asks anything other than whether they want to get on the schedule.
    4. It says the shop is still checking the color, brings up the materials note in brackets, or names a brand or film code.

    #Answer
    -True: the response breaks at least one rule above.
    -False: the response follows every rule above.
"""

    instructions_text += examples()

    return instructions_text
