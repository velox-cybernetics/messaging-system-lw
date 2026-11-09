#IMPORTS

from src.prompts.enforcers import regen_guide
from src.prompts.color_materials.picked import generator as color_picked_generator


#REGEN PROMPT

#this regen also gets the shops last reply, the one their pick answers
def extra_inputs() -> str:
    return """
    - SHOP_LAST_REPLY: the shop's last reply on its own, so a fix never says its lines again."""

#what a material pick reply has to keep straight while it gets fixed
def fix_notes() -> str:
    return """
    #COLOR PICKED FIX NOTES
    - SHOP_LAST_REPLY:
        - Rule: nothing SHOP_LAST_REPLY already said goes out again unless current_user_message asks for it again, so with nothing new to answer, their pick taken in is the whole reply.
        - Why: they just picked from what the shop sent, so saying its lines again reads like the shop didn't notice their pick.
    - The schedule question:
        - Rule: the reply's one question is the schedule question for the job, unless a QUESTION line takes it out.
        - Why: their pick was the last thing the job waited on, so getting on the schedule is the natural next step, unless they already said they aren't ready or were just asked.
    - Parts and line breaks:
        - Rule: the reply can come in parts with a line break (\\n) between them. Keep the parts as FLAGGED_RESPONSE has them, and a part a fix empties comes out with its line break.
        - Why: each part goes out as its own text, so an empty part would send them a blank text."""

#same rules and examples as the material pick generator, plus the playbook for the fix
def prompt() -> str:
    playbook: str = regen_guide.guide(extra_inputs(), fix_notes())

    return f"""{color_picked_generator.prompt()}{playbook}"""
