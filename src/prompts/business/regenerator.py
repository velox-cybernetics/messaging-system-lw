#IMPORTS

from src.prompts.enforcers import regen_guide
from src.prompts.business import generator as business_generator


#REGEN PROMPT

#replies about the shop live and die by the details, so these never get touched
def fix_notes() -> str:
    return """
    #BUSINESS FIX NOTES
    - Details:
        - Rule: every hour, day, address, number, email, link and name stays exactly as FLAGGED_RESPONSE has it, character for character.
        - Why: it all came straight from BUSINESS_DETAILS, and one wrong digit sends them to the wrong address or the wrong number.
    - Questions:
        - Rule: a reply about the shop answers and stops, so when a fix takes out a question, nothing goes in its place.
        - Why: they asked about the shop, not about booking, so a closing question only reads like a sales push (CONVERSATION rule 3 above)."""

#same rules and examples as the shop reply generator, then the playbook for fixing what got flagged
def prompt() -> str:
    #no extra inputs here, just the flagged reply and what to fix
    playbook: str = regen_guide.guide("", fix_notes())

    return f"""{business_generator.prompt()}{playbook}"""
