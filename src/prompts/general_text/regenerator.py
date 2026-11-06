#**********IMPORTS**********
#the small talk prompt the rewrite starts from, and the shared regen playbook
from src.prompts.enforcers import regen_guide
from src.prompts.general_text import generator as general_text_generator



#**********REGEN PROMPT**********
#small talk gets a second shot too now, same prompt plus the playbook for fixing what got flagged


#FIX NOTES
#small talk stays small, a thanks never turns into a sales pitch
def fix_notes() -> str:
    return """
    #SMALL TALK FIX NOTES
    - Warm and short:
        - Rule: small talk gets a short, warm reply that matches what they sent, and when a fix takes out a question, the warm reply on its own is the whole reply.
        - Why: not every text needs to move the job forward. A "sorry about that" or a "thanks" answered with a sales question reads like the shop only cares about booking, and the next text they send goes to another shop.
        - How: keep the warm part as written and end the reply there."""


#REGEN PROMPT
#same rules and examples as the small talk generator, then the playbook for fixing what got flagged
def prompt() -> str:
    #no extra inputs here, just the flagged reply and what to fix
    playbook: str = regen_guide.guide("", fix_notes())

    return f"""{general_text_generator.prompt()}{playbook}"""
