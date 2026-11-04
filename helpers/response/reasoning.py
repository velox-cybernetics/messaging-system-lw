#**********IMPORTS**********
#python's text patterns, to spot and cut the model's notes out of a reply
import re



#**********GLOBALS**********
#the words and marks that give away the model's notes, never a real text to a customer


#LEAK MARKERS
#words and marks only prompts and model notes use, like the = in "$700 each = $1400", never a customer text
LEAK_MARKERS: list[str] = ["_", "#", "missing:", "reason:", "response:", "reply:", "state:", "what's missing", "the customer", "the user", "pricing rule", "ppf rule", "tint rule", "coating rule", "question rule", "questions rule", "conversation rule", "tone rule", "service rule", "sales rule", "price rule", "→", "=", " + ", "...", "…"]


#TAX PRICES
#the shop writes a price "$450 + tax", so the + in it is never the one notes use, like "$700 each + $200"
TAX_PRICES: re.Pattern[str] = re.compile(r"\$\d[\d,]*(?:\.\d+)? \+ tax")


#DRAFT QUOTE
#the owner never puts a quote in a text, so one means the model drafted its reply in quotes next to its notes or quoted the rules, and a " right after a number is inches, like 22" wheels
DRAFT_QUOTE: re.Pattern[str] = re.compile(r"(?<!\d)\"")


#DRAFT LENGTH
#a reply it drafted in quotes is a whole text, so a couple of words in quotes is only a word it put in quotes, like our "standard" price
DRAFT_MIN_WORDS: int = 3


#NOTE PHRASES
#notes say these and a customer text never does, so one is enough, like "first reply"
NOTE_PHRASES: list[str] = ["my reply", "this reply", "my response", "first reply", "last reply", "next reply", "one reply", "two replies", "regular reply", "whole reply", "reply asked", "reply asks", "reply ended", "asked nothing", "first message", "message history", "no history", "lead form", "no greeting", "schedule question", "booking question", "price question", "pricing question", "pic question", "coverage question", "grouped question", "question waits", "question needed", "question fits", "question spacing", "no schedule", "price goes out", "price waits", "price held", "no price yet", "selling line", "selling lines", "sell lines", "selling point", "selling points", "coverage line", "steps line", "end without", "gets asked", "gets answered", "gets said", "gets named", "gets written", "stays empty", "not asked", "isn't asked", "per rule", "from details", "per ex", "like ex", "examples show", "true case", "false case", "small inference", "two system", "system responses", "they asked", "they answered", "they typed", "they wrote", "they named", "ask vehicle", "ask color", "ask for pic", "ask grouped", "need pic", "needs pic", "windows named", "service named", "vehicle known", "offer windshield", "windshield offered", "answer briefly", "answer straight", "answer only", "answers it", "acknowledge", "acknowledges", "keep short", "keep it short", "keep simple", "keep it tight", "maybe ask", "maybe mention", "could mention", "let me rewrite", "let me redo", "let me revise", "let me reread", "let me reconsider", "let me draft", "rewrite", "rewritten", "final answer", "i'll answer", "i will answer", "i'll reply", "i'll respond", "i'll mention", "i'll note", "i'll write", "i'll draft", "i'll lead with", "i'll open with", "i'll end with", "i'll end on", "i'll close with", "i'll address"]


#HINT PHRASES
#a text to a customer can say one of these, like "they want" in "What did they want done?", so it takes two to be notes
HINT_PHRASES: list[str] = ["they want", "they ask", "they said", "they sent", "they gave", "they told", "they bring", "they picked", "they haven't", "they didn't", "they're asking", "they're leaning", "they're weighing", "they're deciding", "whether they", "all they", "color they", "look they", "theirs", "their vehicle", "their truck", "their car", "their text", "their answer", "their question", "their pick", "the reply", "the response", "the question", "goes out", "gone out", "went out", "left out", "no number", "no vehicle", "no info", "yes or no", "price stands", "price needs", "one line", "the shop's", "current color", "desired color", "all info", "rule", "rules say", "details say", "details have", "ex", "example", "examples", "isn't listed", "that's allowed", "ask for", "ask which", "ask about", "ask what vehicle", "could ask", "should i", "should we", "give prices", "answer from", "just answer", "could say", "could end", "maybe end", "i'll say", "i'd say", "something like", "keep it simple", "draft", "nothing about", "the intro"]

#how many hint phrases it takes for a reply to read as notes
HINTS_NEEDED: int = 2


#THOUGHT WORDS
#words the model says to itself as a whole thought, like the "Wait" in "Wait — hold the wrap price."
THOUGHT_WORDS: list[str] = ["wait", "hmm", "hm", "hmmm", "no wait", "oh wait", "wait no", "actually wait", "wait actually", "hmm wait"]


#THOUGHT MARKS
#the marks that end a thought, so a thought word only counts when it stands alone
THOUGHT_MARKS: list[str] = [".", ",", "?", "!", ":", ";", "—", "–", "-", "\"", "“", "”", "(", ")", "…"]



#**********PLAIN NOTES**********
#reads a reply word by word to catch notes the model wrote in plain words with no marker in them


#WORDS ONLY
#the text lowercased with only its words left, one space between each and one on each end
def words_only(text: str) -> str:
    lowered_text: str = text.lower().replace("’", "'")

    kept_text: str = ""

    #every mark turns into a space, so "reply," and "reply" are the same word
    for character in lowered_text:
        if(character.isalpha() or character == "'"):
            kept_text = f"{kept_text}{character}"

        else:
            kept_text = f"{kept_text} "

    words: list[str] = kept_text.split()

    spaced_text: str = " ".join(words)

    #a space on each end lets a phrase match whole words only, so "they want" never matches "they wanted"
    return f" {spaced_text} "


#COUNT PHRASES
#how many of the phrases show up in the text as whole words
def count_phrases(text: str, phrases: list[str]) -> int:
    spaced_text: str = words_only(text)

    phrase_count: int = 0

    for phrase in phrases:
        if(f" {phrase} " in spaced_text):
            phrase_count += 1

    return phrase_count


#SPLIT THOUGHTS
#the text cut into thoughts at every mark, lowercase, empty ones left out
def split_thoughts(text: str) -> list[str]:
    marked_text: str = text.lower()

    #every mark ends a thought, so "Wait — hold the wrap price." splits into "wait" and "hold the wrap price"
    for mark in THOUGHT_MARKS:
        marked_text = marked_text.replace(mark, "\n")

    thoughts: list[str] = []

    for line in marked_text.split("\n"):
        thought: str = line.strip()

        if(thought != ""):
            thoughts.append(thought)

    return thoughts


#THINKS ALOUD
#whether the model talked to itself in the text, like "Wait" or "Hmm" on its own
def thinks_aloud(text: str) -> bool:
    #only a whole thought counts, so "Can't wait to see it" is never the model talking to itself
    for thought in split_thoughts(text):
        if(thought in THOUGHT_WORDS):
            return True

    return False


#PLAIN NOTES
#whether the text has notes the model wrote in plain words, with no marker in them
def has_plain_notes(text: str) -> bool:
    if(thinks_aloud(text)):
        return True

    if(count_phrases(text, NOTE_PHRASES) > 0):
        return True

    #one hint can be part of a real text, two together are notes
    return count_phrases(text, HINT_PHRASES) >= HINTS_NEEDED



#**********REASONING CHECK**********
#decides if a reply has the model's notes in it, and cuts the reply out from around them


#STRAIGHT QUOTES
#the text with its curly quotes turned into straight ones
def straight_quotes(text: str) -> str:
    straight_text: str = text.replace("“", "\"")

    return straight_text.replace("”", "\"")


#HAS REASONING
#only a reply written in parts can have a line break, in any other reply one is the model's notes
def has_reasoning(reply: str, line_breaks: bool) -> bool:
    if(not line_breaks and "\n" in reply):
        return True

    #curly quotes read as straight ones, so a reply drafted in “ ” quotes after the notes is caught the same way
    lowered_reply: str = TAX_PRICES.sub("", straight_quotes(reply.lower()))

    for marker in LEAK_MARKERS:
        if(marker in lowered_reply):
            return True

    #the reply it drafted in quotes after its notes, like I'll answer the brands question. "The wrap uses..."
    if(DRAFT_QUOTE.search(lowered_reply)):
        return True

    #notes written in plain words have no marker, like "Satin black is the color they want, ask for pic of theirs."
    return has_plain_notes(reply)


#DRAFT QUOTE SPOTS
#where each quote around a draft is, inches left out
def draft_quote_spots(text: str) -> list[int]:
    spots: list[int] = []

    for quote in DRAFT_QUOTE.finditer(text):
        spots.append(quote.start())

    return spots


#CUT REASONING
#the reply cut out from around the model's notes, empty when no clean reply can be cut out
def cut_reasoning(reply: str, line_breaks: bool) -> str:
    kept_reply: str = straight_quotes(reply)

    reason_spot: int = kept_reply.lower().find("reason:")

    #notes written after the reply, like the REASON line in the examples, come off with everything after them
    if(reason_spot != -1):
        kept_reply = kept_reply[:reason_spot]

    kept_reply = kept_reply.strip()

    quote_spots: list[int] = draft_quote_spots(kept_reply)

    #a quote left at the end with nothing to pair with closes nothing, so it comes off before the quotes get paired
    if(len(quote_spots) % 2 == 1 and quote_spots[-1] == len(kept_reply) - 1):
        kept_reply = kept_reply[:-1].rstrip()

        quote_spots = quote_spots[:-1]

    #a reply in quotes with notes after it, like "What car is it?" First reply., is only the quoted text
    if(len(quote_spots) >= 2 and quote_spots[0] == 0):
        kept_reply = kept_reply[1:quote_spots[1]]

    #notes written before the reply end where the reply starts, so it's the last thing in quotes, notes after it come off too
    elif(len(quote_spots) >= 2 and len(quote_spots) % 2 == 0):
        kept_reply = kept_reply[quote_spots[-2] + 1:quote_spots[-1]]

    #a quote that never closed opened the reply, so it runs from there to the end
    elif(len(quote_spots) % 2 == 1):
        kept_reply = kept_reply[quote_spots[-1] + 1:]

    #a couple of words in quotes is never the reply it drafted, so no piece of it goes out
    if(len(quote_spots) > 0 and len(kept_reply.split()) < DRAFT_MIN_WORDS):
        return ""

    kept_reply = kept_reply.strip()

    #a cut that still has notes in it, or has nothing left, never goes out
    if(kept_reply == "" or has_reasoning(kept_reply, line_breaks)):
        return ""

    return kept_reply
