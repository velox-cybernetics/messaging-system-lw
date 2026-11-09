#EXAMPLES

AGREE_DATE_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Tuesday works"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"the 21st"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"first one"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"yes that works"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Thursday the 22nd open for drop off, does that work for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"Monday please, what time should I bring it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, we've got Monday the 26th or Tuesday the 27th open for drop off, which one works best for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"lets do wednesday"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"monday the 26th works"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?","user_message_1":{"user_media":{},"user_text":"none of those work for me"},"system_response_to_user_message_1":"No worries, we've also got Thursday the 22nd, Monday the 26th or Tuesday the 27th open for drop off, would any of those work?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"tuesday works, so stoked on that nardo gray"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"the 21st, will the green be in by then?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"ya thats it"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"tuesday works"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Protection for the front on my 2024 f150"},"system_response_to_user_message_0":"Sweet, so front end PPF on the F-150 would run $1800 + tax, that covers the full hood, fenders, bumper, headlights and mirrors. Did you want to get it on the schedule?","user_message_1":{"user_media":{},"user_text":"Ok what’s your schedule look like"},"system_response_to_user_message_1":"Perfect, so the price of front end PPF on the F-150 is $1800 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $360. We've got Monday the 26th, Tuesday the 27th or Wednesday the 28th open for drop off, which day works best for you?"}}
    category: agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"yep sounds good"},"message_history":{"user_message_0":{"user_media":{},"user_text":"lets get the tint done"},"system_response_to_user_message_0":"Perfect, so the price of ceramic tint on the sides and rear of the RAV4 is $450 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, so that would be $90. We've got Thursday the 22nd open for drop off, does that work for you?"}}
    category: agree_date
"""

AGREE_JOB_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Yes"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Protection for the front on my 2024 f150"},"system_response_to_user_message_0":"Sweet, so front end PPF on the F-150 would run $1800 + tax, that covers the full hood, fenders, bumper, headlights and mirrors. Did you want to get it on the schedule?","user_message_1":{"user_media":{},"user_text":"Ok what’s your schedule look like"},"system_response_to_user_message_1":"Perfect, so the price of front end PPF on the F-150 is $1800 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $360. We've got Monday the 26th, Tuesday the 27th or Wednesday the 28th open for drop off, which day works best for you?"}}
    category: agree_job

    state: {"current_user_message":{"user_media":{},"user_text":"sounds good"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for a full wrap and tint on my 2021 tacoma? its grey, want satin black, tint on the sides and rear"},"system_response_to_user_message_0":"Sweet, so satin black on the Tacoma would run $3450 + tax for a full wrap, and ceramic tint on the sides and rear is $450 on top.","user_message_1":{"user_media":{},"user_text":"Both sound good, lets book it"},"system_response_to_user_message_1":"Perfect, so the price of the full wrap in satin black on the Tacoma is $3450 plus tax, the price of ceramic tint on the sides and rear is $450 plus tax, and the total price comes out to $3900 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $780. We've got Tuesday the 20th, Wednesday the 21st or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: agree_job

    state: {"current_user_message":{"user_media":{},"user_text":"yep thats right, cant wait to see it in that green"},"message_history":{"user_message_0":{"user_media":{},"user_text":"any update on the green?"},"system_response_to_user_message_0":"Good news, we can get that satin green you sent ordered, are you interested in getting on the schedule for that wrap?","user_message_1":{"user_media":{},"user_text":"I’m ready "},"system_response_to_user_message_1":"Perfect, so the price of the full wrap in satin green on the 570S is $3200 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $640. We've got Monday the 26th, Tuesday the 27th or Wednesday the 28th open for drop off, which day works best for you?"}}
    category: agree_job

    state: {"current_user_message":{"user_media":{},"user_text":"perfect 👍"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Lets book it"},"system_response_to_user_message_0":"Perfect, so the price of the full wrap in gloss black on the Civic is $2950 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $590. We've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: agree_job
"""

NOT_AGREE_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"none of those work"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"can I do the 28th instead?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"no"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Thursday the 22nd open for drop off, does that work for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"actually nevermind, ill hold off"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, we've got Monday the 26th or Tuesday the 27th open for drop off, which one works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"how long would you need it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"do you guys take cards?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Thursday the 22nd open for drop off, does that work for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"if my gf drops it at 9 wed can i grab it after work like 4:30? is it done by then"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yeah thats right"},"system_response_to_user_message_0":"Perfect, we've got Tuesday the 20th, Wednesday the 21st or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"could i do the early drop like 6:30 on wednesday the 21st? and is there any friday at all"},"message_history":{"user_message_0":{"user_media":{},"user_text":"front end yes for sure"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"prolly tues the 20th but lemme ask my dad first, ill lmk tmrw"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yep"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"hmm none of those either"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?","user_message_1":{"user_media":{},"user_text":"none of those work for me"},"system_response_to_user_message_1":"No worries, we've also got Thursday the 22nd, Monday the 26th or Tuesday the 27th open for drop off, would any of those work?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"cool, does the film for my color have to come in first?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"I’m ready "},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"actually thinking about a different color now, can i send you another one before i pick a day"},"message_history":{"user_message_0":{"user_media":{},"user_text":"correct"},"system_response_to_user_message_0":"Perfect, we've got Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"actually just the wrap, no tint"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for a full wrap and tint on my 2021 tacoma? its grey, want satin black, tint on the sides and rear"},"system_response_to_user_message_0":"Sweet, so satin black on the Tacoma would run $3450 + tax for a full wrap, and ceramic tint on the sides and rear is $450 on top.","user_message_1":{"user_media":{},"user_text":"Both sound good, lets book it"},"system_response_to_user_message_1":"Perfect, so the price of the full wrap in satin black on the Tacoma is $3450 plus tax, the price of ceramic tint on the sides and rear is $450 plus tax, and the total price comes out to $3900 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $780. We've got Tuesday the 20th, Wednesday the 21st or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: not_agree

    state: {"current_user_message":{"user_media":{},"user_text":"wait wasnt it 1500?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for ppf on my 2023 accord"},"system_response_to_user_message_0":"Front end on the Accord would run $1600 + tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 + tax. Which option are you leaning towards?","user_message_1":{"user_media":{},"user_text":"Front end, lets book it"},"system_response_to_user_message_1":"Perfect, so the price of front end PPF on the Accord is $1600 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $320. We've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree
"""

NOT_AGREE_DATE_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"none of those work for me"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"can I do the 28th instead?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"what about saturday?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Thursday the 22nd open for drop off, does that work for you?"}}
    category: not_agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"no"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Thursday the 22nd open for drop off, does that work for you?"}}
    category: not_agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"anything the week after?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, we've got Monday the 26th or Tuesday the 27th open for drop off, which one works best for you?"}}
    category: not_agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"no fridays at all?? like not even the 30th"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yes thats right"},"system_response_to_user_message_0":"Perfect, we've got Tuesday the 20th, Wednesday the 21st or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: not_agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"hmm none of those either"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?","user_message_1":{"user_media":{},"user_text":"none of those work for me"},"system_response_to_user_message_1":"No worries, we've also got Thursday the 22nd, Monday the 26th or Tuesday the 27th open for drop off, would any of those work?"}}
    category: not_agree_date

    state: {"current_user_message":{"user_media":{},"user_text":"none of those work, saturday the 24th? the film should be in by then right"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree_date
"""

NOT_AGREE_PRICING_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"actually just the wrap, no tint"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for a full wrap and tint on my 2021 tacoma? its grey, want satin black, tint on the sides and rear"},"system_response_to_user_message_0":"Sweet, so satin black on the Tacoma would run $3450 + tax for a full wrap, and ceramic tint on the sides and rear is $450 on top.","user_message_1":{"user_media":{},"user_text":"Both sound good, lets book it"},"system_response_to_user_message_1":"Perfect, so the price of the full wrap in satin black on the Tacoma is $3450 plus tax, the price of ceramic tint on the sides and rear is $450 plus tax, and the total price comes out to $3900 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $780. We've got Tuesday the 20th, Wednesday the 21st or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: not_agree_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"actually lets do the full body instead"},"message_history":{"user_message_0":{"user_media":{},"user_text":"How much for ppf on my 2023 accord"},"system_response_to_user_message_0":"Front end on the Accord would run $1600 + tax, which covers the full hood, fenders, bumpers, headlights and mirrors, and full body is $5900 + tax. Which option are you leaning towards?","user_message_1":{"user_media":{},"user_text":"Front end, lets book it"},"system_response_to_user_message_1":"Perfect, so the price of front end PPF on the Accord is $1600 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $320. We've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"I thought you said 2800?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Lets book it"},"system_response_to_user_message_0":"Perfect, so the price of the full wrap in gloss black on the Civic is $2950 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $590. We've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"actually throw the tint on there too"},"message_history":{"user_message_0":{"user_media":{},"user_text":"satin black on my 2022 k5, its white. and how much for tint?"},"system_response_to_user_message_0":"Sweet, so satin black on the K5 would run $2950 + tax for a full wrap, and our ceramic tint on the sides and rear is $450 on top.","user_message_1":{"user_media":{},"user_text":"lets just do the wrap for now"},"system_response_to_user_message_1":"Perfect, so the price of the full wrap in satin black on the K5 is $2950 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $590. We've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"thats not what I wanted"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Lets book it"},"system_response_to_user_message_0":"Perfect, so the price of the full wrap in gloss black on the Civic is $2950 plus tax. Just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $590. We've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: not_agree_pricing
"""

NEVERMIND_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"Actually nevermind"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: nevermind

    state: {"current_user_message":{"user_media":{},"user_text":"Im gonna hold off for now"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Thursday the 22nd open for drop off, does that work for you?"}}
    category: nevermind

    state: {"current_user_message":{"user_media":{},"user_text":"let me think about it and Ill reach out when Im ready"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, we've got Monday the 26th or Tuesday the 27th open for drop off, which one works best for you?"}}
    category: nevermind

    state: {"current_user_message":{"user_media":{},"user_text":"Found someone else, sorry"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: nevermind
"""

SERVICE_PRICING_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"how long would you need it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"is there a deposit?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"does the front end cover the headlights?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, we've got Monday the 26th or Tuesday the 27th open for drop off, which one works best for you?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"can you add tint on the sides and rear too?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"can i drop early like 630 before work / n hw long u need it for"},"message_history":{"user_message_0":{"user_media":{},"user_text":"ya"},"system_response_to_user_message_0":"Perfect, we've got Monday the 26th, Tuesday the 27th or Wednesday the 28th open for drop off, which day works best for you?"}}
    category: service_pricing

    state: {"current_user_message":{"user_media":{},"user_text":"if my gf drops it at 9 wed can i grab it after work like 4:30? is it done by then"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yeah thats right"},"system_response_to_user_message_0":"Perfect, we've got Tuesday the 20th, Wednesday the 21st or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: service_pricing
"""

BUSINESS_OPERATIONS_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following:

    state: {"current_user_message":{"user_media":{},"user_text":"do you guys take cards?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Thursday the 22nd open for drop off, does that work for you?"}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"where are you guys located?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"what time do you guys open?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, we've got Monday the 26th or Tuesday the 27th open for drop off, which one works best for you?"}}
    category: business_operations

    state: {"current_user_message":{"user_media":{},"user_text":"can I finance it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: business_operations
"""

ASKED_DATE_EXAMPLES: str = r"""
    # Examples showing correct answers are the following, each for the day above it:

    day: Wednesday, October 28
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"can I do the 28th instead?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    answer: True

    day: Thursday, October 22
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"can I do the 28th instead?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    answer: False

    day: Friday, October 23
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"what about friday?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, we've got Tuesday the 20th, Wednesday the 21st or Thursday the 22nd open for drop off, which day works best for you?"}}
    answer: True

    day: Monday, October 26
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"anything the week after?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    answer: True

    day: Thursday, October 22
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"anything the week after?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    answer: False

    day: Thursday, October 22
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"none of those work for me"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    answer: False

    day: Thursday, October 22
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Im out of town all next week"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    answer: False

    day: Monday, October 26
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Im out of town all next week, anything the week after that?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    answer: True

    day: Tuesday, October 20
    state: {"current_date_time":"Friday, October 16, 2026 at 09:30 AM","current_user_message":{"user_media":{},"user_text":"actually tuesday the 20th works after all"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, we've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?","user_message_1":{"user_media":{},"user_text":"none of those work for me"},"system_response_to_user_message_1":"No worries, we've also got Thursday the 22nd, Monday the 26th or Tuesday the 27th open for drop off, would any of those work?"}}
    answer: True
"""

PICKED_DATE_EXAMPLES: str = r"""
    # Examples showing correct classifications are the following, each with the days the shop offered numbered the way the categories are:

    days: date_1 is Monday, October 19, date_2 is Tuesday, October 20, date_3 is Wednesday, October 21
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Tuesday works"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yes"},"system_response_to_user_message_0":"Perfect, just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $640. We've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: date_2

    days: date_1 is Monday, October 19, date_2 is Tuesday, October 20, date_3 is Wednesday, October 21
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"the 21st"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $320. We've got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: date_3

    days: date_1 is Monday, October 19, date_2 is Tuesday, October 20, date_3 is Wednesday, October 21
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:40 PM","current_user_message":{"user_media":{},"user_text":"ok first one then"},"message_history":{"user_message_0":{"user_media":{},"user_text":"how long would you need it?"},"system_response_to_user_message_0":"We'd need it 3 to 4 days for the Camaro. And for the satin grey wrap, we've still got Monday the 19th, Tuesday the 20th or Wednesday the 21st open for drop off, which day works best for you?"}}
    category: date_1

    days: date_1 is Monday, October 26, date_2 is Tuesday, October 27
    state: {"current_date_time":"Wednesday, October 21, 2026 at 04:05 PM","current_user_message":{"user_media":{},"user_text":"Monday please, what time should I bring it?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Correct"},"system_response_to_user_message_0":"Perfect, just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $690. We've got Monday the 26th or Tuesday the 27th open for drop off, which one works best for you?"}}
    category: date_1

    days: date_1 is Tuesday, October 20, date_2 is Thursday, October 22, date_3 is Friday, October 23
    state: {"current_date_time":"Monday, October 19, 2026 at 04:30 PM","current_user_message":{"user_media":{},"user_text":"tomorrow works"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yes!"},"system_response_to_user_message_0":"Perfect, just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $530. We've got Tuesday the 20th, Thursday the 22nd or Friday the 23rd open for drop off, which day works best for you?"}}
    category: date_1

    days: date_1 is Thursday, October 22, date_2 is Monday, October 26, date_3 is Tuesday, October 27
    state: {"current_date_time":"Thursday, October 15, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"monday the 26th works"},"message_history":{"user_message_0":{"user_media":{},"user_text":"none of those work for me"},"system_response_to_user_message_0":"No worries, for the satin grey wrap we've also got Thursday the 22nd, Monday the 26th or Tuesday the 27th open for drop off, would any of those work?"}}
    category: date_2

    days: date_1 is Monday, October 19, date_2 is Tuesday, October 20, date_3 is Thursday, October 22
    state: {"current_date_time":"Friday, October 16, 2026 at 11:00 AM","current_user_message":{"user_media":{},"user_text":"the last one, so stoked on that nardo gray"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Yep thats right"},"system_response_to_user_message_0":"Perfect, just a heads up, there is a 20% deposit required to lock in your spot, after you pick a day, so that would be $640. We've got Monday the 19th, Tuesday the 20th or Thursday the 22nd open for drop off, which day works best for you?"}}
    category: date_3
"""


#CHECK EXAMPLES

#samples for whether they picked an offered day, said yes to just the job, or neither
def agree_date_analyze_examples() -> str:
    return f"""

    # agree_date
    {AGREE_DATE_EXAMPLES}

    # agree_job
    {AGREE_JOB_EXAMPLES}

    # not_agree
    {NOT_AGREE_EXAMPLES}
"""

#the samples for the question of what there answer is when it doesn't pick an offered day
def not_agree_date_analyze_examples() -> str:
    return f"""

    # not_agree_date
    {NOT_AGREE_DATE_EXAMPLES}

    # not_agree_pricing
    {NOT_AGREE_PRICING_EXAMPLES}

    # nevermind
    {NEVERMIND_EXAMPLES}

    # service_pricing
    {SERVICE_PRICING_EXAMPLES}

    # business_operations
    {BUSINESS_OPERATIONS_EXAMPLES}
"""

#yes or no samples for each open day, did they ask to drop it off on that one
def asked_date_analyze_examples() -> str:
    return ASKED_DATE_EXAMPLES

#the samples for the question of which offered day they picked
def picked_date_analyze_examples() -> str:
    return PICKED_DATE_EXAMPLES
