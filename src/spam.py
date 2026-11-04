#**********IMPORTS**********
#python's async tools, the decisions model, the conversation on file, and the spam rules
import asyncio

from helpers.models import models
from helpers.state import state_build
from helpers.state import state_form
from src.prompts.spam import analyzer_examples as spam_examples



#**********GLOBALS**********
#how sure the spam check has to be, and the locks that keep each sender's messages in order through it


#SPAM THRESHOLD
#a yes over this means a business, a service or a bot sent it, high on purpose since a customer it catches never gets a reply or shows in the dashboard
SPAM_THRESHOLD: float = 0.7


#INTAKE LOCKS
#one lock per sender, so a message waiting on its spam check never gets passed by the one they sent after it
INTAKE_LOCKS: dict[str, asyncio.Lock] = {}



#**********INTAKE ORDER**********
#messages from one sender take turns through the spam check, so they reach the dashboard and the batch in the order they came in


#INTAKE LOCK
#their lock, made the first time they need one
def intake_lock(id: str) -> asyncio.Lock:
    if(id not in INTAKE_LOCKS):
        INTAKE_LOCKS[id] = asyncio.Lock()

    return INTAKE_LOCKS[id]



#**********SPAM CHECK**********
#reads each message the moment it comes in, so ads, alerts and links to sign something never reach ghl, the dashboard, the batch or a reply


#SPAM STATE
#their text read against the conversation so far, the same state every check reads
def spam_state(id: str, text: str, channel: str) -> dict:
    user_message: dict = state_form.message_form([text], channel)

    return state_build.state_formulation(user_message, state_build.message_history_read(id))


#IS SPAM
#True when a business, a service or a bot sent it instead of a person writing to the shop
#a message with no text has nothing to read, and a check that fails lets it through, so a customer's message is never lost to it
def is_spam(id: str, text: str | None, channel: str) -> bool:
    if(text is None or text.strip() == ""):
        return False

    spam_question: dict = {"type": "noul", "instructions": f"Is `current_user_message` spam, sent by a business, a service or a bot instead of a person writing to the shop?\n{spam_examples.spam_examples()}"}

    try:
        probability_yes: float = models.decision_answer("spam", spam_question, spam_state(id, text, channel))["noul"]

    except Exception as error:
        print(f"SPAM CHECK ERROR: {error}, so the message from {id} on {channel} goes on as usual")

        print()

        return False

    if(probability_yes <= SPAM_THRESHOLD):
        return False

    print(f"SPAM IGNORED: {id} on {channel} sent spam ({probability_yes:.2f}), so it never shows in the dashboard or gets a reply")

    print(f"Spam text: {text}")

    print()

    return True
