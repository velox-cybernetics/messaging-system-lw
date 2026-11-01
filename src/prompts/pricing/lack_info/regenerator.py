#**********IMPORTS**********
#the prompt for replies about things the shop has no info on yet
from src.prompts.pricing.lack_info import generator as pricing_lack_info_generator



#**********REGEN PROMPT**********
#builds the prompt that rewrites a flagged not sure reply so it follows the rules


#REGEN PROMPT
#same rules and examples as the lack info generator, plus what to do with the flagged reply
def prompt() -> str:
    return f"""{pricing_lack_info_generator.prompt()}
    #REGENERATION
    - The input also carries FLAGGED_RESPONSE: a reply already written for this same input that broke one or more of the rules above (an answer or a guess at what they asked, not saying you're not sure, not saying you'll look into it, or bringing up the owner, pitching the wrap instead, promising when the answer comes, picking a meaning instead of asking, skipping over something else they said, mentioning something they never gave, AI wording, or a greeting that does not belong).
    - A first reply to a lead form still goes out with the shop's intro in front of it, so the new reply starts right with the answer: no greeting, no name, no introducing yourself or the shop and nothing about the form, even when the flagged reply had none of those.
    - Write a fresh reply to the same STATE that follows every rule. Never reuse the flagged wording, never mention that a reply was flagged, and output only the new reply.
"""
