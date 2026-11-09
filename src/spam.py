#IMPORTS

import asyncio

from helpers.models import models
from helpers.state import state_build
from helpers.state import state_form
from src.prompts.spam import analyzer_examples as spam_examples


#GLOBALS

#a yes over this means a business or a service sent it, high since a customer it catches is ghosted
SPAM_THRESHOLD: float = 0.7

#one lock per sender, so a message stuck in its spam check never gets passed by there next one
INTAKE_LOCKS: dict = {}


#INTAKE ORDER

#their lock, made the first time they need one
def intake_lock(id: str):
    if(id not in INTAKE_LOCKS):
        INTAKE_LOCKS[id] = asyncio.Lock()

    return INTAKE_LOCKS[id]


#SPAM CHECK

#there text read against the conversation so far, the same state every check reads
def spam_state(id: str, text: str, channel: str) -> dict:
    user_message: dict = state_form.message_form([text], channel)

    return state_build.state_formulation(user_message, state_build.message_history_read(id))

#true when a business or a service sent it, no text or a failed check lets it through
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
