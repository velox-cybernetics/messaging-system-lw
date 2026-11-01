#**********IMPORTS**********
#the prompt for the reply to a material pick, which the rewrite builds on
from src.prompts.color_materials.picked import generator as color_picked_generator



#**********PROMPT**********
#the rules for writing a reply again when the first one broke a rule


#REGEN PROMPT
#the system prompt for writing the material pick reply again after the check flagged it
def prompt() -> str:
    #the generator prompt plus what to do with the flagged reply
    return f"""{color_picked_generator.prompt()}
    #REGENERATION
    - The input also carries SHOP_LAST_REPLY, the shop's last reply on its own, and FLAGGED_RESPONSE: a reply already written for this same input that broke one or more of the rules above (saying again an answer, a price or a line SHOP_LAST_REPLY already gave that they didn't ask for again, saying the customer's own words back to them, more than one question or a question other than the schedule one, or the color still being checked, the materials note or a brand).
    - Write a fresh reply to the same input that follows every rule. Nothing SHOP_LAST_REPLY already said goes out again unless current_user_message asks for it again, so with nothing new to answer, their pick taken in is the whole reply. Never mention that a reply was flagged, and output only the new reply.
"""
