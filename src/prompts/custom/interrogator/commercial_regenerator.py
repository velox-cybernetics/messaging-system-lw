#IMPORTS

from src.prompts.enforcers import regen_guide


#REGEN PROMPT

#commercial regen extras, the price hold line and sometimes the codes repeat flag
def extra_inputs() -> str:
    return """
    - PRICE_HOLD: yes, only on the shop's first reply when they didn't ask what anything costs (#PRICE HOLD above).
    - REPEATED_QUESTION: sometimes comes in place of WHAT_TO_FIX, from the shop's own code. #COMMERCIAL FIX NOTES below says what it means and how to fix it."""

#the commercial quirks, mostly about the one ask and the numbers the owner actually stands behind
def fix_notes() -> str:
    return """
    #COMMERCIAL FIX NOTES
    - Repeated questions:
        - Rule: when REPEATED_QUESTION comes in place of WHAT_TO_FIX, the shop's code caught a question in FLAGGED_RESPONSE worded the same as, or in the same manner as, one the shop already asked in message_history (rule 6), and it gets fixed the same careful way as a WHAT_TO_FIX line.
        - Why: the same question in the same words reads like a bot stuck on a loop, even when the shop really does still need that info.
        - How:
            - INFO_NEEDED and ALREADY_ASKED give different things: it comes out, nothing about what ALREADY_ASKED gives goes in for it, and the question INFO_NEEDED gives goes in its place, like "Perfect, we can do the whole fleet. Do you have a vector file for your logo?". That question is never left out.
            - Otherwise it still needs an answer, so it stays in the reply asked a new way, never in those words or that manner again, like "What kind of coverage were you thinking, the whole van wrapped or more just your logo and info on it?" in place of "a full wrap, a half wrap or just decals" again, or "Do you know the year and model on them?" in place of "What vans are they?" again.
    - The one ask:
        - Rule: the reply's one question is the one #WHAT'S MISSING gives for INFO_NEEDED, and a fix never swaps it for a schedule question, an email ask or anything else.
        - Why: the owner can't price a commercial job without it, so getting it is this reply's whole job.
        - How: when a QUESTION line says that ask was already given or answered, take in what they gave in a few words and leave the ask out, with nothing in its place.
    - Prices:
        - Rule: the only numbers are the usual ranges in price_ranges and the design fee, exactly as FLAGGED_RESPONSE has them, and with PRICE_HOLD: yes none at all: how the jobs differ stays said in words, the design fee stays with no amount ("that just adds a design fee"), and the question stays.
        - Why: the owner prices every commercial job himself once he has what he needs, so any other number is a promise he never made.
    - Lead forms:
        - Rule: a first reply to a lead form goes out with the shop's intro in front of it, so the fixed reply starts right with the answer or the question: no greeting, no name, no introducing yourself or the shop and nothing about the form.
        - Why: the intro already greeted them by name, so a second greeting right under it reads like two bots talking over each other."""

#the fix runs on the same commercial prompt the flagged reply was written with
def prompt(interrogator_prompt: str) -> str:
    playbook: str = regen_guide.guide(extra_inputs(), fix_notes())

    return f"""{interrogator_prompt}{playbook}"""
