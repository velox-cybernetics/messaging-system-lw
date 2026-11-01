#**********IMPORTS**********
#the prompt for the first reply to a customer with a problem, which the rewrite builds on
from src.prompts.escalation import generator as escalation_generator



#**********PROMPT**********
#the rules for writing a reply again when the first one broke a rule


#REGEN PROMPT
#the system prompt for writing the escalation reply again after the check flagged it
def prompt() -> str:
    #the generator prompt plus what to do with the flagged reply
    return f"""{escalation_generator.prompt()}
    #REGENERATION
    - The input also carries FLAGGED_RESPONSE: a reply already written for this same input that broke one or more of the rules above (giving info on what they asked or are upset about, a yes or no on a refund, the warranty, a deal or the shop hiring, promising to make it right or when they'll hear back, not saying you'll look into it, or on a deal not giving the owner's line "Let me have the owner text you, he handles deals personally", bringing up the owner, a person or someone reaching out other than that deal line or asking for Tristan when they're at the shop, not acknowledging what they're dealing with or asking about, blaming anyone or taking the blame, arguing or defending the shop, asking them anything, bringing up a price, a service or booking, AI wording, a laugh, an emoji, an exclamation point or one of Hazel's warm openers, or a greeting).
    - Write a fresh reply to the same STATE that follows every rule. Never reuse the flagged wording, never mention that a reply was flagged, and output only the new reply.
"""
