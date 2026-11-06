#**********IMPORTS**********
#the new girl's "I'll ask the owner" prompt the rewrite starts from, and the shared regen playbook
from src.prompts.enforcers import regen_guide
from src.prompts.business.lack_info import generator as business_lack_info_generator



#**********REGEN PROMPT**********
#the "I'll ask the owner" prompt plus the playbook for fixing a flagged reply, with what a fix can never touch


#FIX NOTES
#the not sure reply has a couple of untouchables, and here's why
def fix_notes() -> str:
    return """
    #NOT SURE FIX NOTES
    - The new girl line:
        - Rule: the line saying she's not sure, that she's still new and learning the ropes, and that she'll ask the owner stays in the fixed reply with its 😅, the way FLAGGED_RESPONSE has it.
        - Why: it's how the shop is honest about not knowing without guessing, and it tells them the owner will get back to them with the real answer, so it's the whole point of this reply.
        - How: fix around it, and never reword it into an answer, a promise or a when.
    - No answers:
        - Rule: nothing gets answered, guessed or hinted while fixing: no yes or no, no hours, no address, no numbers, no "probably".
        - Why: BUSINESS_DETAILS had nothing on what they asked, so any answer would be made up, and a made up answer that turns out wrong costs more trust than not knowing."""


#REGEN PROMPT
#same rules and examples as the not sure generator, then the playbook for fixing what got flagged
def prompt() -> str:
    #no extra inputs here, just the flagged reply and what to fix
    playbook: str = regen_guide.guide("", fix_notes())

    return f"""{business_lack_info_generator.prompt()}{playbook}"""
