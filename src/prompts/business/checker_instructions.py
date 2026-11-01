#**********IMPORTS**********
#the shop details, booking info and typo notes that the check reads along with its own rules
from src.prompts import shared



#**********EXAMPLES**********
#sample questions marked as answerable from the shop details or not, so the check learns the line


#CHECK EXAMPLES
#hands back the sample questions, pasted at the end of the check rules below
def examples() -> str:
    return r"""
    #Examples
    BUSINESS_DETAILS: every business detail, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Are you guys hiring?"},"message_history":{}}
    answer: True
    REASON: Nothing in BUSINESS_DETAILS covers hiring.

    BUSINESS_DETAILS: every business detail, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Is there parking out front?"},"message_history":{}}
    answer: True
    REASON: Nothing in BUSINESS_DETAILS covers parking.

    BUSINESS_DETAILS: {"Hours Of Operations": {"Mon, Tue, Wed, Thu, Fri": "9AM - 5PM", "Sat, Sun": "CLOSED"}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"are you guys open on thanksgiving?"},"message_history":{}}
    answer: True
    REASON: Hours Of Operations has no holiday hours (true case 2).

    BUSINESS_DETAILS: {"Shop Address": ["105 S 700 E St Unit E, American Fork, UT 84003"], "Shop Building": "The gray building just south of Jack and Jill's", "Shop Address Notes": "Give EVERY location listed when asked where located, with the shop building right after the address. NOT MOBILE(DONT MENTION UNLESS ASK), Waiting area avalible or can just drop off and get it whenever done(DONT MENTION UNLESS ASKED)"}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"do you guys have wifi in the waiting area?"},"message_history":{}}
    answer: True
    REASON: The waiting area is written there but wifi is not, and wifi is all they asked (true case 2).

    BUSINESS_DETAILS: {"Business License": "Registered in state of Texas"}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Ok whats the license number?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Are you guys licensed and registered?"},"system_response_to_user_message_0":"Yeah, we're registered in the state of Texas."}}
    answer: True
    REASON: Business License has no license number (true case 2).

    BUSINESS_DETAILS: every business detail, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"For like $200"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Do you guys do gift cards?"},"system_response_to_user_message_0":"Not sure on gift cards, let me look into that for you."}}
    answer: True
    REASON: The short reply clears up something the shop said it would look into, so it is still not covered (true case 3).

    BUSINESS_DETAILS: {"Hours Of Operations": {"Mon, Tue, Wed, Thu, Fri": "9AM - 5PM", "Sat, Sun": "CLOSED"}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"yall open on saturday?"},"message_history":{}}
    answer: False
    REASON: Hours Of Operations has it.

    BUSINESS_DETAILS: {"Financing": {"Provider": "Affirm", "Where It Happens": "On the QuickBooks estimate that gets sent to the customer", "How It Works": "They pick Affirm as the way to pay on that estimate and apply with Affirm there", "If Approved": "Affirm handles the financing from there", "What Changes": "Only the payment method, it's Affirm instead of card or cash. Everything else about the job stays the same"}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"do you guys do financing?"},"message_history":{}}
    answer: False
    REASON: Financing has it (false case 4).

    BUSINESS_DETAILS: {"Hours Of Operations": {"Mon, Tue, Wed, Thu, Fri": "9AM - 5PM", "Sat, Sun": "CLOSED"}}
    STATE: {"current_date_time":"Sunday, October 11, 2026 at 11:30 AM","current_user_message":{"user_media":{},"user_text":"you guys open right now?"},"message_history":{}}
    answer: False
    REASON: Hours Of Operations with current_date_time answers it (false case 4).

    BUSINESS_DETAILS: {"Shop Address": ["105 S 700 E St Unit E, American Fork, UT 84003"], "Shop Building": "The gray building just south of Jack and Jill's", "Shop Address Notes": "Give EVERY location listed when asked where located, with the shop building right after the address. NOT MOBILE(DONT MENTION UNLESS ASK), Waiting area avalible or can just drop off and get it whenever done(DONT MENTION UNLESS ASKED)"}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"do you guys come to me or do I have to bring it in?"},"message_history":{}}
    answer: False
    REASON: Shop Address Notes says the shop is not mobile. A note marked DONT MENTION UNLESS ASKED still counts once they ask.

    BUSINESS_DETAILS: {"Hours Of Operations": {"Mon, Tue, Wed, Thu, Fri": "9AM - 5PM", "Sat, Sun": "CLOSED"}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"what are your hours, and is there parking?"},"message_history":{}}
    answer: False
    REASON: Parking is not covered, but the hours are, so the regular reply gives the hours and says it'll look into the parking (false case 5).

    BUSINESS_DETAILS: {"Contact Email": "lonewraps@gmail.com"}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"What about email?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"Whats the best number to reach you guys at?"},"system_response_to_user_message_0":"You can reach us at (855) 494-1645."}}
    answer: False
    REASON: The short follow up asks for the email, and Contact Email has it.

    BUSINESS_DETAILS: {"Name of person talking to": "Hazel at the Lone Wraps team. When they ask straight out whether this is a bot, AI or a real person, Hazel is the Lone Wraps AI assistant, never a real person (DONT MENTION BEING AI UNLESS THEY ASK THAT)"}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Wait is this a bot?"},"message_history":{"user_message_0":{"user_media":{},"user_text":"yall open friday?"},"system_response_to_user_message_0":"Yeah, Friday we're open 9AM to 5PM."}}
    answer: False
    REASON: Whether this is a bot always gets answered (false case 6).

    BUSINESS_DETAILS: {"Business Name": "Lone Wraps"}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"is this lone wraps?"},"message_history":{}}
    answer: False
    REASON: Business Name has it.

    BUSINESS_DETAILS: {"Business License": "Registered in state of Texas", "Insurance": "The business is insured (nothing is written on what it covers, so never promise what it pays for)"}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Do you guys have insurance in case something happens to my car while its there?"},"message_history":{}}
    answer: False
    REASON: Insurance has it. They asked whether the shop is insured, so the regular reply says it is, without promising what it pays for.

    BUSINESS_DETAILS: {"Hours Of Operations": {"Mon, Tue, Wed, Thu, Fri": "9AM - 5PM", "Sat, Sun": "CLOSED"}}
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can I bring it in Friday at 2?"},"message_history":{}}
    answer: False
    REASON: Wanting to come in at a certain time, the regular reply handles that (false case 7).

    BUSINESS_DETAILS: {"Hours Of Operations": {"Mon, Tue, Wed, Thu, Fri": "9AM - 5PM", "Sat, Sun": "CLOSED"}}
    STATE: {"current_date_time":"Friday, October 09, 2026 at 03:38 PM","current_user_message":{"user_media":{},"user_text":"Can I swing by the shop to see wrap colors?"},"message_history":{}}
    answer: False
    REASON: The wrap color books are at the shop (#GENERAL SERVICE DETAILS), coming by to look at them isn't booking (#BOOKING DETAILS), and Hours Of Operations says when it's open (false case 9).

    BUSINESS_DETAILS: every business detail, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"Can I come by and look at the colored ppf colors?"},"message_history":{}}
    answer: False
    REASON: #GENERAL SERVICE DETAILS has the whole book of colored PPF colors at the shop (false case 9).

    BUSINESS_DETAILS: every business detail, one per line
    STATE: {"current_date_time":"Tuesday, October 06, 2026 at 01:15 PM","current_user_message":{"user_media":{},"user_text":"I have some questions about your business"},"message_history":{}}
    answer: False
    REASON: They ask about the business in general without asking one thing yet, so the regular reply asks what they want to know (false case 10).
"""



#**********RULES**********
#decides if nothing they asked has an answer in the shop details, so the reply says we're not sure


#CHECK RULES
#hands back the rules for the business check, which is true when BUSINESS_DETAILS covers nothing they asked
def instructions() -> str:
    instructions_text: str = """
    #How To Answer
    -Answer True only when NOTHING in current_user_message can be handled from BUSINESS_DETAILS: everything they ask for has no answer there and no false case fits. If ANY part of the message is covered, answer False even when another part is not covered. The regular reply handles the covered part and says it'll look into the rest. Thanks, compliments and small talk next to an uncovered question are not a covered part.
    -BUSINESS_DETAILS is everything the shop knows about the business details the customer is asking about, one JSON object per line. When the message is about the business in general or names no detail in particular, it has every business detail.
    -Every business detail being in BUSINESS_DETAILS is never a reason for False on its own. When they ask something specific that none of it answers, it's still True.
    -STATE is the conversation. current_user_message is what the customer just sent, message_history holds the earlier turns oldest first (user_message_N is an earlier customer message, system_response_to_user_message_N is the shop's reply to it). Read the current message in light of the history. A short follow up ("what about email?", "and on sunday?") belongs to the topic the earlier turns point it at.
    -Go through every part of current_user_message before answering. Judge only what is written in BUSINESS_DETAILS and in #GENERAL SERVICE DETAILS and #BOOKING DETAILS below, never whether the shop could probably figure it out: not written there means not known. Notes inside a value, like "(DONT MENTION UNLESS ASKED)", are still written there.
    -#GENERAL SERVICE DETAILS and #BOOKING DETAILS below are what the regular reply knows on top of BUSINESS_DETAILS, so a question they answer counts as covered (false case 9).

    #True Cases (only when nothing else in the message is covered)
    1. They ask about something BUSINESS_DETAILS doesn't cover at all, like parking, wifi, hiring, gift cards, loaner cars or rides.
    2. They ask about a detail BUSINESS_DETAILS has, but it says nothing on the part they want to know, like holiday hours, a license number, or a location that isn't listed.
    3. Their short reply answers a question the shop asked while clearing up something it said it would look into.

    #False Cases
    4. BUSINESS_DETAILS has the answer. For being open today, tomorrow or right now, Hours Of Operations with current_date_time answers it.
    5. The message mixes a part that falls under the true cases with a part BUSINESS_DETAILS covers, like the hours plus parking. The regular reply answers the covered part and says it'll look into the rest.
    6. They ask who they are talking to, or whether this is a bot or a real person.
    7. They want to come in at a certain day or time or get on the schedule. The regular reply handles that.
    8. The message asks for nothing new: a thanks, an ok, or saying they'll come by.
    9. They ask about the services or booking and #GENERAL SERVICE DETAILS or #BOOKING DETAILS answers it, like coming by to look through the wrap or colored PPF color books, what the shop does, turnaround or warranty.
    10. They ask about the business in general, or say they have questions without asking one yet ("I have some questions about your business", "tell me about the shop"). BUSINESS_DETAILS has every business detail, and the regular reply answers from it or asks what they want to know.

    #Answer
    -True: nothing in the message has an answer in BUSINESS_DETAILS and no false case fits.
    -False: BUSINESS_DETAILS answers any part of it, or any false case fits.
    -In the examples "every business detail, one per line" stands for all of them, you get the full JSON.
"""

    instructions_text += shared.general_service_details()

    instructions_text += shared.booking_details()

    instructions_text += shared.typos()

    instructions_text += examples()

    return instructions_text
