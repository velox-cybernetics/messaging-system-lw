#IMPORTS

from helpers.response import greeting
from helpers.response import laughs
from helpers.response import spacing


#WORDING

#runs every wording fix over the reply in order and hands back the reply that goes out
def wording_rules(system_response: str, channel: str, message_history: dict, current_message_batch: list, vehicle_models: list[str], follow_up: bool = False) -> str:
    #form leads get the set intro, the greeting only stays where a conversation opens or resumes
    system_response = greeting.fix_greeting(system_response, channel, message_history, current_message_batch, vehicle_models, follow_up)

    #haha, lol or the laugh emoji, any other laugh the model wrote becomes haha
    system_response = laughs.fix_laughs(system_response)

    #sweet and perfect each open at most one of every three replies
    system_response = spacing.swap_opener(system_response, message_history, spacing.ACK_OPENERS)

    #sweet and perfect only ever open the reply, one later in it goes out as And
    system_response = spacing.flow_openers(system_response)

    #and never opens two sentences in a row, once is plenty
    system_response = spacing.no_double_and(system_response)

    #yeah, yess and yep each open at most one of every three replies
    system_response = spacing.swap_opener(system_response, message_history, spacing.YES_OPENERS)

    #no worries opens at most one of every three replies, a repeat goes out as its all good
    system_response = spacing.swap_worries(system_response, message_history)

    return system_response
