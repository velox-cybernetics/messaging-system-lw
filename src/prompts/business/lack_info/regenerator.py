#**********IMPORTS**********
#the "let me look into that" reply prompt, so a flagged reply gets rewritten with the same rules
from src.prompts.business.lack_info import generator as business_lack_info_generator



#**********REGEN PROMPT**********
#the "let me look into that" prompt again, plus how to rewrite a reply that broke a rule


#REGEN PROMPT
#hands back the lack info generator prompt with the rewrite rules for a reply the enforcer flagged
def prompt() -> str:
    #the generator prompt plus what to do with the flagged reply
    return f"""{business_lack_info_generator.prompt()}
    #REGENERATION
    - The input also carries FLAGGED_RESPONSE: a reply already written for this same input that broke one or more of the rules above (an answer or a guess at what they asked, not saying you're not sure, not saying you'll look into it, or bringing up the owner, promising when the answer comes, picking a meaning instead of asking, skipping over something else they said, mentioning something they never gave, AI wording, or a greeting that does not belong).
    - Write a fresh reply to the same STATE that follows every rule. Never reuse the flagged wording, never mention that a reply was flagged, and output only the new reply.
"""
