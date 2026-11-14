#EXAMPLES

CONTACT_INFO_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Jake Miller 801-555-1234 jake.miller@gmail.com"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Tuesday works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Tuesday the 13th?"}}
    category: contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"its Sarah Kim, sarah.k22@yahoo.com"},"message_history":{"user_message_0":{"user_media":{},"user_text":"the 21st"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday?"}}
    category: contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"Brittany Lopez, 385-555-0192, brittany.l@outlook.com. is there a waiting area?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"monday"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Monday?"}}
    category: contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"use my wifes, Kelly Miller kelly.m@gmail.com"},"message_history":{"user_message_0":{"user_media":{},"user_text":"wednesday the 28th"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday the 28th?"}}
    category: contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"Mike R, this number works, mike.r@outlook.com"},"message_history":{"user_message_0":{"user_media":{},"user_text":"thursday"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Thursday the 22nd?"}}
    category: contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"jtmiller@gmail.com"},"message_history":{"user_message_0":{"user_media":{},"user_text":"JT Miller, 801 555 7788"},"system_response_to_user_message_0":"Sweet, and what's the best email to send it to?"}}
    category: contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"Danny"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yeah that one works"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Tuesday, November 3rd?"}}
    category: contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"Chris Allen, chris at gmail dot com"},"message_history":{"user_message_0":{"user_media":{},"user_text":"tuesday"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Tuesday?"}}
    category: contact_info
"""

NO_CONTACT_INFO_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"ill send it when i get home"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Tuesday works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Tuesday the 13th?"}}
    category: no_contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"jake at gmail dot com"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Jake Miller, 801-555-1234"},"system_response_to_user_message_0":"Sweet, and what's the best email to send it to?"}}
    category: no_contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"do i need to bring anything when i drop it off?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yes that works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Thursday the 22nd?"}}
    category: no_contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"can you just text me the invoice?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"monday"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Monday?"}}
    category: no_contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"is info@lonewraps.com where i send pics of the car?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"wednesday the 28th"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday the 28th?"}}
    category: no_contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"actually nevermind, ill hold off for now"},"message_history":{"user_message_0":{"user_media":{},"user_text":"first one"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Monday the 19th?"}}
    category: no_contact_info

    state: {"current_user_message":{"user_media":{},"user_text":"ok"},"message_history":{"user_message_0":{"user_media":{},"user_text":"the 21st"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday?"}}
    category: no_contact_info
"""

WONT_GIVE_INFO_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"id rather not give my email out"},"message_history":{"user_message_0":{"user_media":{},"user_text":"the 21st"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday?"}}
    category: wont_give_info

    state: {"current_user_message":{"user_media":{},"user_text":"can you just text me the invoice?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"monday"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Monday?"}}
    category: wont_give_info

    state: {"current_user_message":{"user_media":{},"user_text":"actually nevermind, ill hold off for now"},"message_history":{"user_message_0":{"user_media":{},"user_text":"first one"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Monday the 19th?"}}
    category: wont_give_info

    state: {"current_user_message":{"user_media":{},"user_text":"id rather just pay when I drop it off"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yes that works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Thursday the 22nd?"}}
    category: wont_give_info

    state: {"current_user_message":{"user_media":{},"user_text":"I need to cancel, something came up"},"message_history":{"user_message_0":{"user_media":{},"user_text":"JT Miller, 801 555 7788"},"system_response_to_user_message_0":"Sweet, and what's the best email to send it to?"}}
    category: wont_give_info
"""

GETTING_INFO_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"ill send it when i get home"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Tuesday works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Tuesday the 13th?"}}
    category: getting_info

    state: {"current_user_message":{"user_media":{},"user_text":"one sec let me find it"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Sarah Kim 385 555 2210"},"system_response_to_user_message_0":"Perfect, and what's the best email to send it to?"}}
    category: getting_info

    state: {"current_user_message":{"user_media":{},"user_text":"let me ask my wife which email she uses"},"message_history":{"user_message_0":{"user_media":{},"user_text":"wednesday the 28th"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday the 28th?"}}
    category: getting_info

    state: {"current_user_message":{"user_media":{},"user_text":"jake at gmail dot com"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Jake Miller, 801-555-1234"},"system_response_to_user_message_0":"Sweet, and what's the best email to send it to?"}}
    category: getting_info

    state: {"current_user_message":{"user_media":{},"user_text":"ok"},"message_history":{"user_message_0":{"user_media":{},"user_text":"the 21st"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday?"}}
    category: getting_info
"""

SERVICE_PRICING_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"do i need to bring anything when i drop it off?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yes that works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Thursday the 22nd?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"how long will you need it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Tuesday works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Tuesday the 13th?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"is the rest due when I pick it up?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"first one"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Monday the 19th?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"can i drop it off the night before? ill send my email in a bit"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Kyle Reed 801-555-3321"},"system_response_to_user_message_0":"Sweet, and what's the best email to send it to?"}}
    category: service_pricing
"""

BUSINESS_OPERATIONS_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"do you guys take cards?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"monday"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Monday?"}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"is info@lonewraps.com where i send pics of the car?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"wednesday the 28th"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday the 28th?"}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"can I finance the deposit through affirm?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Tuesday works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Tuesday the 13th?"}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"where are you guys located again?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"JT Miller, 801 555 7788"},"system_response_to_user_message_0":"Sweet, and what's the best email to send it to?"}}
    category: business_operations
"""

SPAM_HARASS_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Hi! We help local shops get more 5 star Google reviews, check out reviewboost.co"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Tuesday works"},"system_response_to_user_message_0":"Sounds good, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Tuesday the 13th?"}}
    category: spam_harass

    state: {"current_user_message":{"user_media":{},"user_text":"stop texting me"},"message_history":{"user_message_0":{"user_media":{},"user_text":"the 21st"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Wednesday?"}}
    category: spam_harass

    state: {"current_user_message":{"user_media":{},"user_text":"you guys are a joke, f off"},"message_history":{"user_message_0":{"user_media":{},"user_text":"monday"},"system_response_to_user_message_0":"Sweet, can I get a name, number and email to shoot that invoice over to so we can lock in your date for Monday?"}}
    category: spam_harass
"""


#CHECK EXAMPLES

#the samples for the question of whether there answer gives any of their info for the invoice
def contact_analyze_examples() -> str:
    return f"""

    # contact_info
    {CONTACT_INFO_EXAMPLES}

    # no_contact_info
    {NO_CONTACT_INFO_EXAMPLES}
"""

#the samples for the question of what there answer is when it has none of their info
def no_contact_analyze_examples() -> str:
    return f"""

    # wont_give_info
    {WONT_GIVE_INFO_EXAMPLES}

    # getting_info
    {GETTING_INFO_EXAMPLES}

    # service_pricing
    {SERVICE_PRICING_EXAMPLES}

    # business_operations
    {BUSINESS_OPERATIONS_EXAMPLES}

    # spam_harass
    {SPAM_HARASS_EXAMPLES}
"""
