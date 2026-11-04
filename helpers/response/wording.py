#**********IMPORTS**********
#the fixers for greetings, laughs and the words a reply opens with
from helpers.response import greeting
from helpers.response import laughs
from helpers.response import spacing



#**********WORDING**********
#fixes the reply's wording so it sounds like hazel before it goes out


#WORDING RULES
#runs every wording fix over the reply in order and hands back the reply that goes out
def wording_rules(system_response: str, channel: str, message_history: dict, current_message_batch: list, vehicle_models: list[str], follow_up: bool = False) -> str:
    #the first reply to a form lead greets with the set intro naming every model read off the form, the greeting only stays on where a conversation opens or picks back up
    system_response = greeting.fix_greeting(system_response, channel, message_history, current_message_batch, vehicle_models, follow_up)

    #a laugh only ever goes out as haha, lol or the laugh emoji, so any other laugh the model wrote becomes haha
    system_response = laughs.fix_laughs(system_response)

    #sweet and perfect each open at most one of every three replies
    system_response = spacing.swap_opener(system_response, message_history, spacing.ACK_OPENERS)

    #sweet and perfect only ever open the reply, one later in it goes out as And
    system_response = spacing.flow_openers(system_response)

    #"And" never opens two sentences in a row, the second one starts clean
    system_response = spacing.no_double_and(system_response)

    #yeah, yess and yep each open at most one of every three replies
    system_response = spacing.swap_opener(system_response, message_history, spacing.YES_OPENERS)

    #no worries opens at most one of every three replies, a repeat goes out as it's all good
    system_response = spacing.swap_worries(system_response, message_history)

    return system_response
