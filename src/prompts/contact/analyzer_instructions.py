#**********CONTACT ANSWERS**********
#what each kind of answer to asking for their name, number and email looks like


#CONTACT INFO
CONTACT_INFO_INSTRUCTIONS: str = """

    The customer gives their name, number or email for the shop to send the invoice for the deposit to. That is any one of them written out in the current message as theirs or as the one the invoice goes to: a name ("Jake Miller", "its sarah", "put it under my wife kelly"), a phone number typed out ("801-555-1234", "my cell is 8015559876"), the number they're texting from pointed to as the one to use ("this number works", "same number im texting from"), or an email address typed out with an @ ("jake.miller@gmail.com", "send it to my work one, jake@millerplumbing.com"). Any one of them is enough, so it is contact_info even when the others are missing, even when the email in it is only said in words while a name or number is typed out with it ("Chris Allen, chris at gmail dot com"), and even when the same message says or asks something else too ("Jake Miller, 801-555-1234, is there a waiting area?").
"""


#NO_CONTACT INFO
NO_CONTACT_INFO_INSTRUCTIONS: str = """

    The customer doesn't give their name, number or email for the invoice. That is a message with none of them in it ("thanks", "ok", "do I need to bring anything?", "ill send it when I get home", "can you text it to me instead?"), an email only said in words with no name or number typed out along with it ("jake at gmail dot com"), the shop's own number or email ((855) 494-1645, lonewraps@gmail.com), or a name, number or email they give for something other than the invoice.
"""


#WONT_GIVE INFO
WONT_GIVE_INFO_INSTRUCTIONS: str = """

    The customer doesn't want to give their info for the invoice or go ahead with the deposit. That is saying no to giving it ("id rather not give my email out", "I don't really do email"), wanting the invoice or the deposit some other way ("can you just text me the invoice?", "id rather just pay when I drop it off"), or calling it off ("actually nevermind, ill hold off for now", "I need to cancel").
"""


#GETTING INFO
GETTING_INFO_INSTRUCTIONS: str = """

    The customer will get their info to the shop but doesn't give it yet, or says something that only needs a few words back. That is not having it on them or needing to find it ("one sec let me find it", "ill send it when i get home", "let me ask my wife which email she uses"), an email said in words instead of written out with an @ ("jake at gmail dot com"), or a thanks or an ok with nothing else in it ("thanks!", "ok", "sounds good").
"""


#SERVICE PRICING
SERVICE_PRICING_INSTRUCTIONS: str = """

    The customer asks about a service or its price instead of giving their info. That is how long it takes, dropping it off early or the night before, picking it up, what to bring, the deposit or what's left to pay after it, what's included or covered, the colors, finishes or materials, adding a service, or any other detail of the work on their vehicle.
"""


#BUSINESS OPERATIONS
BUSINESS_OPERATIONS_INSTRUCTIONS: str = """

    The customer asks about the shop itself instead of giving their info. That is the hours, where the shop is, how to reach it, how the invoice gets paid (a card, cash, financing), whether it's licensed or insured, or who they're talking to and whether this is a bot.
"""


#SPAM HARASS
SPAM_HARASS_INSTRUCTIONS: str = """

    The customer sends spam or harasses the shop instead of giving their info. That is an ad, a sales pitch or a link that has nothing to do with their job, insults, cussing the shop out, threats, or telling the shop to stop texting them ("stop texting me", "f off").
"""



#**********CONTACT QUESTIONS**********
#hands each answer's rules to the decisions model, with the questions it asks about their reply


#ANSWER RULES
#the rules for one kind of answer, picked by its name ("contact_info", "wont_give_info", "spam_harass", ...), empty when the name isn't one of them
def instructions(instruction: str) -> str:
    if(instruction == "contact_info"):
        return CONTACT_INFO_INSTRUCTIONS

    elif(instruction == "no_contact_info"):
        return NO_CONTACT_INFO_INSTRUCTIONS

    elif(instruction == "wont_give_info"):
        return WONT_GIVE_INFO_INSTRUCTIONS

    elif(instruction == "getting_info"):
        return GETTING_INFO_INSTRUCTIONS

    elif(instruction == "service_pricing"):
        return SERVICE_PRICING_INSTRUCTIONS

    elif(instruction == "business_operations"):
        return BUSINESS_OPERATIONS_INSTRUCTIONS

    elif(instruction == "spam_harass"):
        return SPAM_HARASS_INSTRUCTIONS

    return ""


#CONTACT QUESTION
#whether their answer gives a name, number or email for the invoice
def contact_question_instructions() -> str:
    return "Does the customer give their name, number or email for the shop to send the invoice for the deposit to? Read the message history first: the shop asked them for a name, number and email to shoot the invoice for the 20% deposit over to, or for the ones still missing, and the current message answers it. Classify the current message in light of it. A name, a phone number or an email address written out in the current message as theirs or as the one the invoice goes to is contact_info, and so is pointing to the number they're texting from as the one to use. Any one of them is enough, even when the others are missing, when the email in it is only said in words while a name or number is typed out with it, or when the message says or asks something else too. Everything else is no_contact_info: a message with none of them in it, an email only said in words with no name or number typed out along with it, the shop's own number or email, or a name, number or email they give for something other than the invoice."


#NO_CONTACT QUESTION
#what their answer is when it has none of their info for the invoice
def no_contact_question_instructions() -> str:
    return "The customer didn't give their name, number or email for the invoice for the deposit. Which one of these is the current message? Read the message history first: the shop asked them for a name, number and email to shoot the invoice for the 20% deposit over to, or for the ones still missing. Classify the current message in light of it. Spam, a sales pitch, insults, threats or telling the shop to stop texting them is spam_harass, even when it also asks something. Not wanting to give their info, wanting the invoice or the deposit some other way, or calling it off is wont_give_info, even when it also asks something. A question about a service, a price or any detail of the work is service_pricing, and a question about the shop itself is business_operations, even when they also say they'll send their info later. Getting their info to the shop later, an email said in words instead of written out, or a thanks or an ok with nothing else in it is getting_info."
