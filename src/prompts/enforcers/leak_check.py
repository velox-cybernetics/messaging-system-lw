#**********LEAK CHECK**********
#the one safety net jev still runs next to the question and tone enforcers


#QUESTION
#jev only gets the draft here, so notes the writer left in it get caught before a customer reads them
def question() -> str:
    return r"""Does `draft_reply` have anything in it besides the text that goes to the customer?
Yes: any of the writer's own notes about the reply, what it's going to answer, say, mention, ask or leave out, in any form and anywhere in it, before the text, after it or between its parts: a plan ("I'll answer the brands question with the material line"), orders to itself ("give them the warranty line, then ask for the pic"), labels or a summary of the reply ("Warranty question:", "Short answer, then the pic ask."), the reply drafted in quotes with notes around it, talk about the rules, the examples, the state, message_history, SERVICE_DETAILS or what's missing, or talk about the customer instead of to them ("the customer asked about brands", "they typed white, so ask for a pic"). The owner never puts quotes around what he texts.
No: it's only the text the customer gets, the way the shop texts, however short it is, in one part or in parts on their own lines, even when it says what the shop will do ("I'll let you know what I find", "Let me check the color books") or says "they" about anything but the customer ("they come in gloss, satin and matte")."""


#EXAMPLES
#a couple of leaky drafts and a few clean ones, so a normal reply never trips it
def examples() -> str:
    return r"""Examples:
draft_reply: Since the color books are still being checked, I'll answer the brands question with the material line and say the check on that military green is still in progress.

"The wrap uses the material 3M, Avery, or others we have in the shop, depending on the exact color you want
And I'm still checking the color books on that military green, I'll let you know what I find"
answer: True
draft_reply: Customer wants the warranty, give the 6 month line, no question since the last reply asked one.
Our warranty is 6 months and covers any peeling or bubbling from the install
answer: True
draft_reply: Sweet, so a ceramic coating on the 4Runner would run $700 + tax. Did you want to hop on the schedule?
answer: False
draft_reply: So the wrap on the F150 takes about 4 to 5 days
And our warranty is 6 months and covers any peeling or bubbling, so if it peels you just bring it back and we'll get it fixed
answer: False
draft_reply: Perfect, that matte military green would look clean on the F150. Let me check the color books to see if we can get something like that done
answer: False"""


#FIX
#the model left its homework in the reply, so the regen hears exactly that
def fix() -> str:
    return "LEAK: The draft has the writer's own notes in it (a plan, labels, talk about the rules or the customer) next to the text for the customer. Cut everything but the text the customer gets."
