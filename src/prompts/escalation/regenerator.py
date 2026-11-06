#**********IMPORTS**********
#the problem reply prompt the rewrite starts from, and the shared regen playbook
from src.prompts.enforcers import regen_guide
from src.prompts.escalation import generator as escalation_generator



#**********REGEN PROMPT**********
#the problem reply prompt plus the playbook for fixing a flagged reply, without promising anything along the way


#FIX NOTES
#a person owns this one, so the fix never says more than the ack already did
def fix_notes() -> str:
    return """
    #ESCALATION FIX NOTES
    - Acknowledge and look into it:
        - Rule: the reply only takes in what they're dealing with and says the shop will look into it, with no answer, no promise and no question, the way FLAGGED_RESPONSE already does.
        - Why: a person at the shop sorts this out, and anything the bot answers or promises is something the owner has to stand behind without ever seeing it.
        - How: when a fix takes out a question or a line, nothing goes in its place, and the acknowledgment and the line saying the shop will look into it stay as written."""


#REGEN PROMPT
#same rules and examples as the problem reply generator, then the playbook for fixing what got flagged
def prompt() -> str:
    #no extra inputs here, just the flagged reply and what to fix
    playbook: str = regen_guide.guide("", fix_notes())

    return f"""{escalation_generator.prompt()}{playbook}"""
