#IMPORTS

from src.prompts.enforcers import regen_guide


#REGEN PROMPT

#the interrogator regen also gets the shops last reply, and the price hold line on a first reply
def extra_inputs() -> str:
    return """
    - SHOP_LAST_REPLY: the last system_response in message_history on its own, empty when none went out yet, so a fix never says one of its lines again.
    - PRICE_HOLD: yes, only on the shop's first reply when they didn't ask what anything costs (#PRICE HOLD above)."""

#the interrogator quirks, mostly about whats missing and which prices stay held
def fix_notes() -> str:
    return """
    #INTERROGATOR FIX NOTES
    - What's missing:
        - Rule: #WHAT'S MISSING above is what was missing when FLAGGED_RESPONSE was written, so go by it even when STATE seems to give the missing piece.
        - Why: the shop picked this prompt from what's on file, and what's on file is what the price and the booking really wait on.
        - How: the ask for what's missing stays as written unless a QUESTION line is about it. When it says they already gave it or already answered it, take in what they gave in a few words and leave that ask out.
    - Held prices:
        - Rule: a price #WHAT'S MISSING holds never goes in, and every price it lets out stays exactly as FLAGGED_RESPONSE has it, unless WHAT_TO_FIX has a PRICE HOLD line.
        - Why: a held price waits on something the shop doesn't have yet, so it could be wrong, and the prices that already went in were worked out by the rules above.
    - Price hold:
        - Rule: with PRICE_HOLD: yes in the input, every number comes out by #PRICE HOLD, the ones #WHAT'S MISSING lets out included, and the question #WHAT'S MISSING gives still ends the reply.
        - Why: the owner never puts a price in a first reply they didn't ask a price on, and the ask for what's missing is what gets them talking.
    - Parts and line breaks:
        - Rule: a reply about more than one thing can come in short parts with a line break (\\n) between them. Keep the parts and their order as FLAGGED_RESPONSE has them, and when a fix takes out everything in a part, that part comes out with its line break.
        - Why: each part goes out as its own text, so an empty part would send them a blank text.
    - SHOP_LAST_REPLY:
        - Rule: when a fix needs a few new words, they never come from SHOP_LAST_REPLY, in the same words or close to them.
        - Why: the same line twice in a row reads copy pasted, and customers notice that right away."""

#the prompt the flagged reply was written with, so the fix goes by the same whats missing
def prompt(interrogator_prompt: str) -> str:
    playbook: str = regen_guide.guide(extra_inputs(), fix_notes())

    return f"""{interrogator_prompt}{playbook}"""
