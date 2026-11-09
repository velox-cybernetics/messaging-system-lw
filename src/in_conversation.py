#IMPORTS

from helpers.channels import senders
from helpers.models import models
from helpers.response import greeting
from helpers.state import dashboard
from helpers.state import log
from helpers.state import owner
from helpers.state import state_build
from helpers.state import state_form
from src.prompts.in_conversation import analyzer_examples as in_conversation_examples


#GLOBALS

#a yes over this means they already know the owner, high since a stranger it catches gets ghosted
IN_CONVERSATION_THRESHOLD: float = 0.7


#IN CONVERSATION

#on file as the owners from before the system, so no reply, a failed read lets them through
def owner_has_them(id: str) -> bool:
    try:
        held: bool = owner.convo_held(id)
    except Exception as error:
        #redis hiccup, so they get the system like anyone else
        print(f"IN CONVERSATION READ ERROR: {error}, so {id} goes on as usual")

        return False

    if(held):
        print(f"IN CONVERSATION: {id} was already talking with the owner before the bot showed up, so their batch gets no reply")

    return held

#nobody has them, no form, no reply yet, the only time a message can pick up with the owner
def first_contact(message_history: dict, id: str, channel: str) -> bool:
    if(channel in state_form.FORM_CHANNELS):
        return False

    if(greeting.replied_before(message_history)):
        return False

    return not log.read_state(f"restricted_{id}")

#a yes when the message reads like they're picking up an old chat with the owner
def picks_up_convo(state: dict) -> bool:
    convo_question: dict = {"type": "noul", "instructions": f"Is `current_user_message` picking up a conversation they were already having with the owner, someone he already knows, instead of someone reaching out to the shop for the first time?\n{in_conversation_examples.in_conversation_examples()}"}

    probability_yes: float = models.decision_answer("in_conversation", convo_question, state)["noul"]

    print(f"IN CONVERSATION: {probability_yes:.2f}")

    return probability_yes > IN_CONVERSATION_THRESHOLD

#a first message picking up with the owner makes them his for good, a failed check lets it through
def picks_up(user_message: dict, message_history: dict, id: str, channel: str) -> bool:
    try:
        if(not first_contact(message_history, id, channel)):
            return False

        if(not picks_up_convo(state_build.state_formulation(user_message, message_history))):
            return False

        owner.restrict_convo(id)
    except Exception as error:
        print(f"IN CONVERSATION CHECK ERROR: {error}, so {id} goes on as usual")

        return False

    #it landed on the board already, so it comes back off since the system won't touch them
    dashboard.forget(id)

    #core already put the bubble up, and nobodys replying, so down it comes
    senders.stop_typing(id, channel)

    print(f"IN CONVERSATION: {id} on {channel} picks up a chat they already had going with the owner, so they're his for good and nothing goes back or on file")

    return True
