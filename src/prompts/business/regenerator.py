#**********IMPORTS**********
#the prompt that writes replies about the shop, so a flagged reply gets the same rules
from src.prompts.business import generator as business_generator



#**********REGEN PROMPT**********
#the shop reply prompt again, plus how to write a fresh reply when the last one broke a rule


#REGEN PROMPT
#hands back the business generator prompt with the rewrite rules for a reply the enforcer flagged
def prompt() -> str:
    #the generator prompt plus what to do with the flagged reply
    return f"""{business_generator.prompt()}
    #REGENERATION
    - The input also carries FLAGGED_RESPONSE: a reply already written for this same input that broke one or more of the rules above (answering something they didn't ask, copying a note into the reply, guessing at something BUSINESS_DETAILS doesn't cover, re-asking or re-giving something already in the conversation, agreeing to a day or time, trying to book them, AI wording, claiming to be a person, dodging a question about whether this is a bot, AI or a real person, or a greeting that does not belong).
    - Write a fresh reply to the same STATE that follows every rule. Never reuse the flagged wording, but keep every detail exactly as BUSINESS_DETAILS has it. Never mention that a reply was flagged, and output only the new reply.
    - When the flagged reply opened with "Yeah", "Yess" or "Yep" and they didn't ask a yes or no question or check something with the shop, the new reply starts right with the answer or with the owner's acknowledgment ("For sure", "Sweet", "Perfect", "Sounds good"), never a Yeah in front (tone rule 9).
"""
