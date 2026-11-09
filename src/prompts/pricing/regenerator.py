#IMPORTS

from src.prompts.enforcers import regen_guide
from src.prompts.pricing import generator as pricing_generator


#REGEN PROMPT

#the main regen also gets the shops last reply, and the price hold line on a first reply
def extra_inputs() -> str:
    return """
    - SHOP_LAST_REPLY: the last system_response in message_history on its own, empty when none went out yet, so a fix never says one of its lines again.
    - PRICE_HOLD: yes, only on the shop's first reply when they didn't ask what anything costs (#PRICE HOLD above)."""

#the pricing quirks to keep in mind while fixing, each one with why it matters
def fix_notes() -> str:
    return """
    #PRICING FIX NOTES
    - The schedule question:
        - Rule: when a QUESTION line takes out the schedule question, the reply ends on the answer, or on a few warm words leaving the door open, and never on another question about the job.
        - Why: QUESTIONS rule 5 above already spaces questions out to every other reply and skips them once they're waiting on the vehicle or still deciding. When the check still caught one, it slipped past that rule, and any question there reads as the same push. The answer on its own keeps the job moving better, because it gives them a reason to come back.
        - How: answer what they asked, and when it fits, take in what they said in a few words ("Sounds good, just reach out once it's here"), then stop.
    - Prices:
        - Rule: every price stays exactly as FLAGGED_RESPONSE has it, with its "+ tax", its "typically" and what it depends on, unless WHAT_TO_FIX has a PRICE HOLD line.
        - Why: each number was worked out from SERVICE_DETAILS for their vehicle by the rules above, and a question or tone fix has nothing to do with what the job costs, so touching a number only risks a wrong price going out.
    - Parts and line breaks:
        - Rule: a reply about a service can come in two to four short parts with a line break (\\n) between them. Keep the parts and their order as FLAGGED_RESPONSE has them, and when a fix takes out everything in a part, that part comes out with its line break.
        - Why: each part goes out as its own text, so an empty part would send them a blank text, and parts moved around would answer things out of order.
    - SHOP_LAST_REPLY:
        - Rule: when a fix needs a few new words, they never come from SHOP_LAST_REPLY, in the same words or close to them.
        - Why: the same line twice in a row reads copy pasted, and customers notice that right away.
    - Lead forms:
        - Rule: a first reply to a lead form goes out with the shop's intro in front of it, so the fixed reply never starts with a greeting, a name, an introduction or anything about the form.
        - Why: the intro already greeted them by name and said who's texting, so a second greeting right under it reads like two bots talking over each other.
    - Price hold:
        - Rule: with PRICE_HOLD: yes in the input, the fixed reply has no price at all, and fixing anything else never puts one back.
        - Why: the owner gets them talking before any number comes up (#PRICE HOLD above).
        - How: the question that takes a held price's place is the one #PRICE HOLD gives, so "Front end PPF on the G37 is $1600 + tax, that covers the full hood, fenders, bumper, headlights and mirrors, and full body is $5900 + tax, which covers all the painted surfaces. Which option are you leaning towards?" becomes "The front end covers the full hood, fenders, bumper, headlights and mirrors, and the full body covers all the painted surfaces and comes with free side and rear window tint. Are you looking for just the front end or full body on the G37?"."""

#same rules and examples as the main generator, then the playbook for fixing what got flagged
def prompt() -> str:
    playbook: str = regen_guide.guide(extra_inputs(), fix_notes())

    return f"""{pricing_generator.prompt()}{playbook}"""
