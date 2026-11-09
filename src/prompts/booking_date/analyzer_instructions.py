#DATE ANSWERS

AGREE_DATE_INSTRUCTIONS: str = """

    The customer picks one of the drop off days the shop's last reply offered them. That is naming one of the offered days ("tuesday works", "the 20th", "monday please", "lets do wednesday"), pointing to one ("the first one", "the earliest one"), or a yes when only one day was offered ("yes that works", "yep"). It is agree_date even when the same message asks something else too, the day they picked is what counts, and a comment or question about the exact color the shop already made sure it can get never takes the pick away ("tuesday works, so stoked on that green", "the 21st, will the film be in by then?"). A day that only comes up inside a question or an if isn't a pick yet ("could I do the early drop on wednesday?", "if I drop it off wednesday can I grab it by 4:30?"), and neither is a maybe that waits on someone or something else ("prolly tues the 20th but lemme ask my dad first, ill lmk"), so it's never this.
"""

AGREE_JOB_INSTRUCTIONS: str = """

    The customer says yes to the job the shop's last reply named with the drop off days, without picking one of the days, when it offered more than one. That is a yes, ok or sounds good with no day in it ("yes", "yep thats right", "sounds good", "perfect", "lets do it 🔥"), even with a comment on the job or on the exact color the shop already made sure it can get ("yes, cant wait to see it in that green"). A yes when only one day was offered picks that day, so it's agree_date, and a yes that asks something, changes the job or names a day is never this.
"""

NOT_AGREE_INSTRUCTIONS: str = """

    The customer doesn't pick one of the drop off days the shop's last reply offered them. That is a no, asking for a day that wasn't offered ("can I do the 28th?", "what about saturday?"), saying none of them work, a change to the job or one of its prices ("actually just the wrap, no tint", "I thought you said 2800?"), calling it off ("nevermind", "let me hold off"), a question about a service, a price or the shop, a day that only comes up inside a question or an if ("if I drop it off wednesday can I grab it by 4:30?"), or anything else that doesn't pick one of the offered days or say yes to the job.
"""

NOT_AGREE_DATE_INSTRUCTIONS: str = """

    None of the drop off days the shop's last reply offered work for the customer. That is a no to them ("no", "none of those work"), asking for a day that wasn't offered, even as a question ("can I do the 28th instead?", "what about saturday?", "no fridays at all?? not even the 30th", "could i do monday the 26th"), or saying they can't make those days. Asking about dropping it off early or the night before, picking it up after work, how long it takes or whether it's done by a certain time is never this, it doesn't turn the days down.
"""

NOT_AGREE_PRICING_INSTRUCTIONS: str = """

    The customer still wants to get on the books, but the job or a price the shop's last reply named with the drop off days isn't right for them. That is dropping a service ("actually just the wrap, no tint"), switching to an option the shop already quoted ("lets do the full body instead"), switching the wrap or colored PPF to a different color than the one named ("can we do the matte green instead?"), adding back a service the shop already quoted in the conversation ("can you add the tint too?" after the tint got its price), saying a price or the total is wrong ("I thought you said 2800?", "wasnt it 3000?"), or saying the job isn't right without saying what ("thats not what I wanted", "thats not right"). A no to the days themselves, like none of them working, is never this.
"""

NEVERMIND_INSTRUCTIONS: str = """

    The customer is calling off getting on the books for now. That is "nevermind", "actually Ill hold off", "let me think about it", "Ill reach out when Im ready", "found someone else", or not wanting the work done anymore.
"""

SERVICE_PRICING_INSTRUCTIONS: str = """

    The customer asks about a service or its price instead of picking a day. That is how long it takes, whether it's done by a certain time, dropping it off early or the night before, picking it up after work or after closing, the deposit, what's included or covered, the colors, finishes or materials, adding a service the shop hasn't quoted yet, or any other detail of the work on their vehicle.
"""

BUSINESS_OPERATIONS_INSTRUCTIONS: str = """

    The customer asks about the shop itself instead of picking a day. That is the hours, where the shop is, how to reach it, payments, financing, whether it's licensed or insured, or who they're talking to and whether this is a bot.
"""

ASKED_DATE_INSTRUCTIONS: str = """

    The customer turned down the drop off days the shop's last reply offered them, and the shop is finding them other days. Read message_history first, then current_user_message, and work out which days they mean from current_date_time and the days the shop offered. It's a yes when they ask to drop it off on this day: naming its date or day of the month ("can I do the 28th?", "what about wednesday the 28th"), its weekday ("what about wednesday?", "any wednesdays open?"), a week it's in ("anything the week after?", "what about the week of the 26th?"), or going back to it after the shop offered it before ("actually the tuesday works after all"). It's a no for a plain no, none of the days working, a reason they can't make them, asking for a different day, weekday or week, or a day they say they can't do ("Im out of town all next week").
"""


#DATE QUESTIONS

#rules for one kind of answer looked up by name, empty string for a name it doesn't know
def instructions(instruction: str) -> str:
    if(instruction == "agree_date"):
        return AGREE_DATE_INSTRUCTIONS
    elif(instruction == "agree_job"):
        return AGREE_JOB_INSTRUCTIONS
    elif(instruction == "not_agree"):
        return NOT_AGREE_INSTRUCTIONS
    elif(instruction == "not_agree_date"):
        return NOT_AGREE_DATE_INSTRUCTIONS
    elif(instruction == "not_agree_pricing"):
        return NOT_AGREE_PRICING_INSTRUCTIONS
    elif(instruction == "nevermind"):
        return NEVERMIND_INSTRUCTIONS
    elif(instruction == "service_pricing"):
        return SERVICE_PRICING_INSTRUCTIONS
    elif(instruction == "business_operations"):
        return BUSINESS_OPERATIONS_INSTRUCTIONS
    elif(instruction == "asked_date"):
        return ASKED_DATE_INSTRUCTIONS

    return ""

#whether there answer to the offered days picks one of them, says yes to the job only, or neither
def date_agree_instructions() -> str:
    return "Does the customer pick one of the drop off days the shop's last reply offered them? Read the message history first: the shop's last reply offers them days to drop the vehicle off, asking which day works for the job, and the current message is their answer to it. Classify the current message in light of it. Naming or pointing to one of the offered days as their pick, or a yes when only one day was offered, is agree_date, even when the message asks something else too. A yes, ok or sounds good to the job and the days that picks no day, when more than one day was offered, is agree_job. A day that only comes up inside a question or an if isn't a pick yet ('could I do the early drop on wednesday?', 'if I drop it off wednesday can I grab it by 4:30?'), so it is not_agree. Everything else is not_agree: a no, a day that wasn't offered, none of them working, a change to the job or a price, calling it off, a question about a service, a price or the shop, or anything that doesn't pick one of the offered days."

#what there answer is when it doesn't pick one of the offered days
def date_not_agree_instructions() -> str:
    return "The customer didn't pick one of the drop off days the shop's last reply offered them. Which one of these is the current message? Read the message history first: the shop's last reply offers them days to drop the vehicle off, asking which day works for the job. Classify the current message in light of it. A no, none of the days working, or asking for a day that wasn't offered is not_agree_date. A change to the job they want booked or one of its prices, dropping, adding back or switching a service, an option or a color the shop already quoted, or saying a price is wrong or the job isn't right, is not_agree_pricing. Calling off getting on the books is nevermind. A question about a service, what a price or the deposit is, or any detail of the work is service_pricing, and that includes dropping it off early or the night before, picking it up after work, how long it takes or whether it's done by a certain time on one of the offered days, since those don't turn the days down. A question about the shop itself is business_operations."

#which of the offered days they picked, however they point to it
def picked_date_instructions() -> str:
    return "Which of the drop off days the shop's last reply offered does the customer pick? Read the message history first: the shop's last reply offers them days to drop the vehicle off, and the current message picks one of them. Classify the current message in light of it, working the day out from current_date_time and the days offered: the weekday ('tuesday works'), the day of the month ('the 21st'), where it is in the list ('the first one', 'the last one') or a day said from today ('tomorrow'). The day they picked is what counts, even when the message also asks or says something else."
