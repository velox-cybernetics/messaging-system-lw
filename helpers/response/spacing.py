#**********IMPORTS**********
#python's patterns, and the sentence cleanup, to start a reply clean once an opener comes off
import re

from helpers.response import cleaners



#**********GLOBALS**********
#the booking and pic words, the booking question, the drop off days only the booking chain offers, and the openers a reply gets spaced out with


#BOOKING WORDS
#a question with one of these in it asks them to get on the schedule
BOOKING_WORDS: list[str] = ["schedule", "scheduled", "book", "booked", "booking", "books"]


#PIC WORDS
#a reply that asks them for one of these is waiting on a pic ("Send me a pic if you can", "Do you have a photo of it?")
PIC_WORDS: list[str] = ["pic", "pics", "photo", "photos", "picture", "pictures", "video"]


#COLOR CHECK PROMISE
#the way a reply tells them the color books are getting checked for the color they sent ("Let me check the color books to see if we can get something like that done")
COLOR_CHECK_PATTERN: re.Pattern = re.compile(r"\b(let me|i'll|i will) check the color books\b|\bcheck the color books to see\b", re.IGNORECASE)


#COLOR WANT ASKS
#the colors a customer names, so an ask naming one reads as an ask for the color they want ("Do you have an exact green in mind?")
COLOR_NAMES: str = r"black|white|gr[ae]y|silver|red|blue|green|yellow|orange|purple|pink|brown|gold|bronze|teal|maroon|burgundy|navy|lime|olive|violet|copper|champagne|nardo"

#the word color on its own, never colored PPF, a color change or the color books
COLOR_WORD: str = r"\bcolou?rs?\b(?!\s+(?:change|changes|book|books)\b)"

COLOR_WORD_PATTERN: re.Pattern = re.compile(COLOR_WORD, re.IGNORECASE)

#the word color or a color they could name
COLOR_REF_PATTERN: re.Pattern = re.compile(rf"{COLOR_WORD}|\b(?:{COLOR_NAMES})\b", re.IGNORECASE)

#a part of a question with the word color and one of these asks for the color they want ("What color are you thinking?", "Have you picked a color yet?")
COLOR_WANT_PATTERN: re.Pattern = re.compile(r"\b(?:want|wants|wanting|wanted|thinking|thought|thoughts|like|liking|love|prefer|preference|go|going|leaning|looking|planning|pick|picked|picking|choose|choosing|chose|decide|decided|deciding|considering|favorite|favourite|after)\b", re.IGNORECASE)

#one of these makes it the color it is now instead ("What color is it right now?", "What color's the Camry at right now?")
COLOR_NOW_PATTERN: re.Pattern = re.compile(r"\b(?:is it|it is|it's|was it|it was|is the|is your|currently|current|right now|at the moment)\b|'s (?:it|the|your)\b", re.IGNORECASE)

#the color they want asked without the word color, next to the color it is now ("what color it is now and what you're wanting to go with")
GO_WITH_PATTERN: re.Pattern = re.compile(r"\b(?:go with|going with|go for|going for|to go)\b", re.IGNORECASE)

#only with them wanting it, never "there's two ways to go" or "you're good to go"
GO_WANT_PATTERN: re.Pattern = re.compile(r"\b(?:want|wanting|wanted|wanna|thinking|looking|planning|leaning|like|hoping)\b", re.IGNORECASE)

#never the film or service they're going with ("are you wanting to go with the wrap")
SERVICE_WORD_PATTERN: re.Pattern = re.compile(r"\b(?:wrap|wrapped|ppf|tint|coating|ceramic|route|film)\b", re.IGNORECASE)

#a tint shade is never the color they want ("what color tint are you thinking?")
SHADE_PATTERN: re.Pattern = re.compile(r"\b(?:tint|tints|shade|shades)\b|%", re.IGNORECASE)

#any color they want is the price staying the same, never an ask ("it's the same price in any color you want"), unless it asks them ("have you seen any colors you like?")
ANY_COLOR_PATTERN: re.Pattern = re.compile(r"\bany\s+(?:\w+\s+)?colou?rs?\b", re.IGNORECASE)

ASKS_YOU_PATTERN: re.Pattern = re.compile(r"\b(?:have|did|do|are|were|got)\s+you\b", re.IGNORECASE)

#a sentence with no question mark still asks for what it says the price needs ("I'll need the make and model and the color you want")
SOLICIT_PATTERN: re.Pattern = re.compile(r"\b(?:need|needs|depends on|depend on|let me know|lmk)\b", re.IGNORECASE)

#the exact color ask's own words: in mind, the green you're thinking, a pic or link of the exact one
IN_MIND_PATTERN: re.Pattern = re.compile(r"\bin mind\b", re.IGNORECASE)

#in mind only asks with a question mark or have or got in front of it, never "just keep in mind a wrap won't match the factory red"
HAVE_IN_MIND_PATTERN: re.Pattern = re.compile(r"\b(?:have|has|had|got)\b.*\bin mind\b", re.IGNORECASE)

ONE_PATTERN: re.Pattern = re.compile(r"\bones?\b", re.IGNORECASE)

NAMED_WANT_PATTERN: re.Pattern = re.compile(rf"(?<!\bany\s)\b(?:colou?rs?|{COLOR_NAMES})\s+(?:that\s+)?(?:you're|you are|youre|you were|you'd|you|u)\s+(?:(?:still|really)\s+)?(?:thinking|wanting|want|wanted|like|liking|picked|leaning|have in mind|had in mind)\b", re.IGNORECASE)

EXACT_ASK_PATTERN: re.Pattern = re.compile(r"\b(?:pics?|photos?|pictures?|screenshots?|links?)\s+(?:or\s+(?:a\s+)?(?:pics?|photos?|pictures?|screenshots?|links?)\s+)?of\s+(?:the|an?|that|your)\s+exact\b", re.IGNORECASE)

#a question asking two things splits into its parts here ("What color is it now, and what color are you wanting to go?")
CLAUSE_BREAK_PATTERN: re.Pattern = re.compile(r"[,;:]|\b(?:and|or|but|so|plus)\b", re.IGNORECASE)

#the second half of the exact color ask, after "Do you have an exact green in mind?"
IF_YOU_DO: str = "if you do"


#BOOKING QUESTION
#the way the owner asks it, a held booking's reply ends on it once its price goes out
BOOKING_QUESTION: str = "Did you want to hop on the schedule?"


#BOOKING YES
#a customer's text that opens with a yes, the way they text one ("yessir", "yeah!", "yesss", "bet", "for sure")
BOOKING_YES_PATTERN: re.Pattern = re.compile(r"^\W*(y+e+s+(\s*sir)?|y+e+a+h*|y+a+h*|y+e+p+|y+u+p+|bet|sure|for sure|sounds good|i'?m down|absolutely|definitely)\b", re.IGNORECASE)


#DAY OFFERS
#a drop off day the way the booking chain offers it ("Monday the 2nd", "Tuesday, November 3rd") or its "open for drop off", only it reads the calendar
DAY_OFFER_PATTERN: re.Pattern = re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday),? (the|january|february|march|april|may|june|july|august|september|october|november|december) \d{1,2}(st|nd|rd|th)?\b|\bopen for drop ?-?offs?\b", re.IGNORECASE)


#SPACING COUNTS
#a reply can't open with the same word as one of the last this many replies
REPLIES_BETWEEN_OPENER: int = 2

#a text holds at most this many sentences, the rest of the reply goes out in the texts after it
TEXT_SENTENCES: int = 3


#YES OPENERS
#the ways a reply opens with a yes, yeah first since it's the usual one and the others stand in for it
YES_OPENERS: list[str] = ["Yeah", "Yess", "Yep"]


#ACK OPENERS
#the ways a reply opens acknowledging them, sweet first since it's the usual one and perfect stands in for it
ACK_OPENERS: list[str] = ["Sweet", "Perfect"]

#an ack opener only ever opens the reply, a later part or sentence picks up from what came before with this instead
FLOW_OPENER: str = "And"


#WORRIES OPENER
#the owner's "No worries" lets something go, and "It's all good" stands in for it when one of the last couple of replies already opened with it
WORRIES_OPENER: str = "No worries"

WORRIES_SWAP: str = "It's all good"

#"No worries at all" goes out whole as "It's all good", never "It's all good at all"
WORRIES_TAIL: str = " at all"



#**********SENT REPLIES**********
#pulls the replies that already went out from the conversation


#SENT REPLIES
#every reply the shop already sent in the conversation, oldest first
def sent_replies(message_history: dict) -> list[str]:
    replies: list[str] = []

    for key, value in message_history.items():
        #an empty reply never went out, so it is not counted
        if(key.startswith("system_response_to_user_message_") and isinstance(value, str) and value != ""):
            replies.append(value)

    return replies


#LAST REPLY
#the reply the shop sent last, empty when it hasn't sent one yet
def last_sent_reply(message_history: dict) -> str:
    replies: list[str] = sent_replies(message_history)

    if(len(replies) == 0):
        return ""

    return replies[-1]



#**********TEXT SPLITTING**********
#cuts a reply into sentences, then into the texts it goes out as, a question always in its own text


#SPLIT SENTENCES
#cuts a reply into its sentences, each one keeping its marks and the spaces or line break in front of it
def split_sentences(reply: str) -> list[str]:
    sentences: list[str] = []

    sentence: str = ""

    for position, character in enumerate(reply):
        next_character: str = reply[position + 1:position + 2]

        #a line break ends the sentence before it, so a line with no mark at its end never runs into the next line
        if(character == "\n" and sentence.strip() != ""):
            sentences.append(sentence)

            sentence = ""

        sentence = f"{sentence}{character}"

        #a mark only ends a sentence before a space or the end, so "17.5%" stays whole
        if(character in ".!?" and next_character in ["", " ", "\n"]):
            sentences.append(sentence)

            sentence = ""

    if(sentence != ""):
        sentences.append(sentence)

    return sentences


#END SENTENCE
#a reply that gets more put after it ends its last sentence first, never "full body Did you want"
def end_sentence(text: str) -> str:
    text = text.strip()

    if(text != "" and (text[-1].isalnum() or text[-1] == "%")):
        return f"{text}."

    return text


#JOIN TEXT
#the sentences of one text, with a blank line in front of each one that starts a new part when the reply keeps its parts
def join_text(sentences: list[str], new_part: list[bool], group: list[int], keep_parts: bool) -> str:
    text: str = sentences[group[0]]

    for position in group[1:]:
        separator: str = " "

        if(keep_parts and new_part[position]):
            separator = "\n\n"

        #a line with no mark at its end ends its sentence before the next one goes on after it
        text = f"{end_sentence(text)}{separator}{sentences[position]}"

    return text


#SPLIT TEXTS
#a question always starts its own text and takes what follows it, the sentences before it go out a few to a text
def split_texts(reply: str) -> list[str]:
    pieces: list[str] = []

    for piece in split_sentences(reply):
        if(piece.strip() != ""):
            pieces.append(piece)

    sentences: list[str] = []

    for piece in pieces:
        sentences.append(piece.strip())

    new_part: list[bool] = []

    #split_sentences leaves the line break in front of the sentence after it, so that sentence starts a new part
    for position, piece in enumerate(pieces):
        new_part.append(position > 0 and piece.lstrip(" ").startswith("\n"))

    groups: list[list[int]] = []

    #once a question went out, every sentence after it goes in its text until the next question
    after_question: bool = False

    for position, sentence in enumerate(sentences):
        #a question always starts a text of its own
        if(sentence.endswith("?")):
            groups.append([position])

            after_question = True

        #anything after a question goes out with it, like the pic ask that finishes it, before one a text fills up
        elif(after_question or (len(groups) > 0 and len(groups[-1]) < TEXT_SENTENCES)):
            groups[-1].append(position)

        else:
            groups.append([position])

    #a reply cut into texts already reads in pieces, only one that goes out as a single text spaces its parts out
    keep_parts: bool = len(groups) == 1

    texts: list[str] = []

    for position, group in enumerate(groups):
        text: str = join_text(sentences, new_part, group, keep_parts)

        #a text the reply was cut at never ends on a period, the way the shop texts, the last one stays as written
        if(position < len(groups) - 1):
            text = text.removesuffix(".")

        texts.append(text)

    return texts



#**********OPENER SPACING**********
#keeps a reply from opening with the same word as the last couple of replies, swapping or cutting it


#OPENS WITH
#whether the reply's first word is this word
def opens_with(reply: str, word: str) -> bool:
    start: str = reply.strip().lower()

    if(not start.startswith(word)):
        return False

    character_after: str = start[len(word):len(word) + 1]

    #"sweetest" does not open with the word sweet
    return not character_after.isalpha()


#OPENED RECENTLY
#whether one of the last couple of replies the shop sent opened with this word
def opened_recently(message_history: dict, word: str) -> bool:
    recent_replies: list[str] = sent_replies(message_history)[-REPLIES_BETWEEN_OPENER:]

    #the word at reply N means N+1 and N+2 open without it
    for recent_reply in recent_replies:
        if(opens_with(recent_reply, word)):
            return True

    return False


#REPEATS OPENER
#whether the reply opens with a word the last couple of replies already opened with
def repeats_opener(reply: str, message_history: dict, word: str) -> bool:
    return opens_with(reply, word) and opened_recently(message_history, word)


#OPENER REST
#what an opener leads into, "Sweet, so the price is" leads into "the price is"
def opener_rest(reply: str, word: str) -> str:
    rest: str = reply.strip()[len(word):].lstrip(" ,.!")

    if(rest.lower().startswith("so ")):
        return rest[len("so "):]

    if(rest.lower().startswith("and ")):
        return rest[len("and "):]

    return rest


#CUT OPENER
#cuts a repeated opener off the front of the reply, so it starts with what the opener led into
def cut_opener(reply: str, message_history: dict, word: str) -> str:
    if(not repeats_opener(reply, message_history, word)):
        return reply

    #"Sweet, so the price is" reads as "The price is" once sweet is cut
    rest: str = opener_rest(reply, word)

    #a reply that is only the word keeps it, so something still goes out
    if(rest.strip() == ""):
        return reply

    print(f"{word.upper()} CUT: {reply}")

    return cleaners.sentence_start(rest)


#SWAP OPENER
#a reply opening with the same word as a recent one gets another opener from its group, or loses it when they all went out lately
def swap_opener(reply: str, message_history: dict, openers: list[str]) -> str:
    for opener in openers:
        word: str = opener.lower()

        if(not repeats_opener(reply, message_history, word)):
            continue

        #a repeated opener swaps for the first one in its group not used lately, "Perfect, so" goes out as "Sweet, so"
        for swap in openers:
            if(not opened_recently(message_history, swap.lower())):
                print(f"{word.upper()} SWAPPED FOR {swap.upper()}: {reply}")

                return f"{swap}{reply.strip()[len(word):]}"

        #every opener in the group opened a recent reply, so the word just gets cut
        return cut_opener(reply, message_history, word)

    return reply


#SWAP WORRIES
#"No worries" opening a reply like one of the last couple did goes out as "It's all good", and comes off when that went out lately too
def swap_worries(reply: str, message_history: dict) -> str:
    word: str = WORRIES_OPENER.lower()

    if(not repeats_opener(reply, message_history, word)):
        return reply

    rest: str = reply.strip()[len(word):].removeprefix(WORRIES_TAIL)

    #it's all good opened a recent reply too, so the reply starts with what no worries led into
    if(opened_recently(message_history, WORRIES_SWAP.lower())):
        cut_rest: str = rest.lstrip(" ,.!")

        #a reply that is only the words keeps them, so something still goes out
        if(cut_rest.strip() == ""):
            return reply

        print(f"{word.upper()} CUT: {reply}")

        return cleaners.sentence_start(cut_rest)

    print(f"{word.upper()} SWAPPED FOR {WORRIES_SWAP.upper()}: {reply}")

    return f"{WORRIES_SWAP}{rest}"



#**********FLOW OPENERS**********
#turns a later sweet or perfect into "And", so only the reply's first word acknowledges them


#ACK OPENER
#the ack opener a sentence opens with ("Sweet, so", "Perfect!"), never one that's part of what it says ("Perfect for")
def ack_opener(sentence: str) -> str:
    start: str = sentence.strip().lower()

    for opener in ACK_OPENERS:
        word: str = opener.lower()

        after: str = start[len(word):]

        if(opens_with(start, word) and (after == "" or after.startswith((",", ".", "!", " so ", " and ")))):
            return word

    return ""


#FLOW CASE
#a word capitalized only for starting its sentence goes lowercase after "And", while "PPF", "I'll" and "McLaren" stay
def flow_case(text: str) -> str:
    first_word: str = text.split(" ", 1)[0]

    if(len(first_word) > 1 and first_word[0].isupper() and first_word[1].isalpha() and first_word[1:].islower()):
        return f"{text[:1].lower()}{text[1:]}"

    return text


#FLOW OPENERS
#a sweet or perfect opening a later part or sentence goes out as "And", picking up from what the reply just said
def flow_openers(reply: str) -> str:
    flowed: str = ""

    #a lone "Sweet!" goes with the sentence after it, and one with nothing after it comes off
    carried: str = ""

    for piece in split_sentences(reply):
        sentence: str = f"{carried}{piece}"

        carried = ""

        word: str = ack_opener(sentence)

        #the reply's first sentence keeps its opener, swap_opener spaces those out
        if(word == "" or flowed.strip() == ""):
            flowed = f"{flowed}{sentence}"

            continue

        rest: str = opener_rest(sentence, word)

        if(rest.strip() == ""):
            carried = sentence

            continue

        body: str = sentence.lstrip()

        #what came after "Sweet!" started its own sentence, after "And" it's the same one
        if(body[len(word):len(word) + 1] in [".", "!"]):
            rest = flow_case(rest)

        print(f"{word.upper()} SWAPPED FOR {FLOW_OPENER.upper()}: {reply}")

        #the line break or space in front of it stays, so the part it opens stays its own part
        flowed = f"{flowed}{sentence[:len(sentence) - len(body)]}{FLOW_OPENER} {rest}"

    return flowed


#DOUBLE AND
#"And" never opens two sentences in a row, so the second one starts clean, whether flow_openers put it in or the model wrote it
def no_double_and(reply: str) -> str:
    kept_reply: str = ""

    last_sentence: str = ""

    for piece in split_sentences(reply):
        sentence: str = piece

        if(opens_with(sentence, FLOW_OPENER.lower()) and opens_with(last_sentence, FLOW_OPENER.lower())):
            body: str = sentence.lstrip()

            print(f"{FLOW_OPENER.upper()} CUT, THE SENTENCE BEFORE OPENS WITH IT: {reply}")

            #the line break or space in front of it stays, so the part it opens stays its own part
            sentence = f"{sentence[:len(sentence) - len(body)]}{cleaners.sentence_start(body[len(FLOW_OPENER):])}"

        kept_reply = f"{kept_reply}{sentence}"

        last_sentence = sentence

    return kept_reply



#**********BOOKING ASKS**********
#spots the booking and pic asks and a color books check in a reply, drops or adds the booking question, and cuts drop off days no calendar gave


#ASKS BOOKING
#whether the sentence is a question asking them to get on the schedule
def asks_booking(sentence: str) -> bool:
    if(not sentence.strip().endswith("?")):
        return False

    for word in sentence.lower().split():
        if(word.strip(",.?!") in BOOKING_WORDS):
            return True

    return False


#PIC ASK
#a reply that asks them for a pic, a photo or a video anywhere in it, as a question or not
def asks_for_pic(reply: str) -> bool:
    for word in reply.lower().split():
        if(word.strip(",.?!") in PIC_WORDS):
            return True

    return False


#COLOR CHECK PROMISED
#a reply that tells them the color books are getting checked for the color they sent
def promises_color_check(reply: str) -> bool:
    return COLOR_CHECK_PATTERN.search(reply) is not None


#BOOKING LEAD IN
#a sweet or perfect taking something in with no price ("Perfect, we can get the 750S wrapped in that one") only leads into the booking question, while "Sweet, so" leads into an answer
def booking_lead_in(sentence: str) -> bool:
    word: str = ack_opener(sentence)

    if(word == "" or "$" in sentence or sentence.strip().endswith("?")):
        return False

    rest: str = sentence.strip()[len(word):].lstrip(" ,.!")

    return not rest.lower().startswith("so ")


#DROP BOOKING
#takes the booking question out of a reply, and what only led into it
def drop_booking_question(reply: str) -> str:
    kept_sentences: list[str] = []

    cut_questions: list[str] = []

    cut_lead_ins: list[str] = []

    for sentence in split_sentences(reply):
        if(not asks_booking(sentence)):
            kept_sentences.append(sentence)

            continue

        cut_questions.append(sentence.strip())

        #what only led into the question comes off with it, unless it's all the reply has left
        if(len(kept_sentences) > 0 and booking_lead_in(kept_sentences[-1]) and "".join(kept_sentences[:-1]).strip() != ""):
            cut_lead_ins.append(kept_sentences.pop().strip())

    kept_reply: str = "".join(kept_sentences)

    #a reply that is only the booking question is how a go ahead gets answered, so it stays and something goes out
    if(kept_reply.strip() == ""):
        return reply

    for sentence in cut_questions:
        print(f"BOOKING QUESTION CUT: {sentence}")

    for sentence in cut_lead_ins:
        print(f"BOOKING LEAD IN CUT: {sentence}")

    return kept_reply.strip()


#BOOKING ASKED
#whether any sentence of the reply asks them to get on the schedule
def asks_booking_question(reply: str) -> bool:
    for sentence in split_sentences(reply):
        if(asks_booking(sentence)):
            return True

    return False


#BOOKING YES
#their text opens with a yes and the shop's last reply asked whether they want to get on the schedule
def yes_to_booking_question(user_text: str, message_history: dict) -> bool:
    return BOOKING_YES_PATTERN.match(user_text) is not None and asks_booking_question(last_sent_reply(message_history))


#BOOKING END
#a reply that has to end on the booking question gets it put at its end
def end_on_booking_question(reply: str) -> str:
    if(asks_booking_question(reply)):
        return reply

    kept_reply: str = ""

    #the booking question is the one question it ends on, so any other comes off unless a price is in it
    for sentence in split_sentences(reply):
        if(not sentence.strip().endswith("?") or "$" in sentence):
            kept_reply = f"{kept_reply}{sentence}"

    return f"{end_sentence(kept_reply)} {BOOKING_QUESTION}"


#OFFERS DAYS
#whether the sentence offers a drop off day
def offers_days(sentence: str) -> bool:
    return DAY_OFFER_PATTERN.search(sentence) is not None


#DROP DAYS
#only the booking chain reads the calendar, so a drop off day any other reply offers is made up and its sentence comes off
def drop_day_offers(reply: str) -> str:
    if(not offers_days(reply)):
        return reply

    kept_reply: str = ""

    for sentence in split_sentences(reply):
        if(offers_days(sentence)):
            print(f"MADE UP DAYS CUT: {sentence.strip()}")

        else:
            kept_reply = f"{kept_reply}{sentence}"

    return kept_reply.strip()



#**********HELD PRICES**********
#the shop's first reply holds every price unless they asked for one, so a price that got past the hold never goes out


#DROP PRICES
#a sentence with a $ in it gives a price (replies.write_price_sent), so on a first reply that holds every price it comes off and the rest stays as written
def drop_prices(reply: str) -> str:
    if("$" not in reply):
        return reply

    kept_reply: str = ""

    for sentence in split_sentences(reply):
        if("$" in sentence):
            print(f"HELD PRICE CUT: {sentence.strip()}")

        else:
            kept_reply = f"{kept_reply}{sentence}"

    return kept_reply.strip()



#**********COLOR WANT ASKS**********
#spots an ask for the color they want, never one for the color it is now, so one written before the exact price has what it needs can come off


#COLOR WANT PART
#whether one part of an ask goes after the color they want, never the color it is now or any color they can have
def wants_color_part(part: str, about_color: bool) -> bool:
    if(COLOR_NOW_PATTERN.search(part) is not None or SHADE_PATTERN.search(part) is not None):
        return False

    if(ANY_COLOR_PATTERN.search(part) is not None and ASKS_YOU_PATTERN.search(part) is None):
        return False

    if(COLOR_WORD_PATTERN.search(part) is not None and COLOR_WANT_PATTERN.search(part) is not None):
        return True

    #"what you're wanting to go with" only goes after the color in a sentence about the color, never the film they're going with
    if(not about_color or GO_WITH_PATTERN.search(part) is None or SERVICE_WORD_PATTERN.search(part) is not None):
        return False

    return GO_WANT_PATTERN.search(part) is not None


#ASKS COLOR WANTED
#whether the sentence asks for the color they want, as a question, as something it says the price needs, or in the exact color ask's own words
#sentence_before is the sentence in front of it, so "Do you have one in mind?" after one about the color reads as asking it
def asks_color_wanted(sentence: str, sentence_before: str) -> bool:
    text: str = sentence.replace("’", "'").strip()

    #"a pic or link of the exact one", never a pic showing the color it is now
    if(EXACT_ASK_PATTERN.search(text) is not None and COLOR_NOW_PATTERN.search(text) is None):
        return True

    if(IN_MIND_PATTERN.search(text) is not None and (text.endswith("?") or HAVE_IN_MIND_PATTERN.search(text) is not None)):
        if(COLOR_REF_PATTERN.search(text) is not None):
            return True

        if(ONE_PATTERN.search(text) is not None and COLOR_WORD_PATTERN.search(sentence_before) is not None):
            return True

    asking: bool = text.endswith("?") or SOLICIT_PATTERN.search(text) is not None

    #"the exact matte black you're thinking" asks for it in a question or a pic ask
    if((asking or asks_for_pic(text)) and NAMED_WANT_PATTERN.search(text) is not None):
        return True

    if(not asking):
        return False

    about_color: bool = COLOR_WORD_PATTERN.search(text) is not None

    for part in CLAUSE_BREAK_PATTERN.split(text):
        if(wants_color_part(part, about_color)):
            return True

    return False


#COLOR WANT ASKS
#the sentences of the reply asking for the color they want, with the pic or the "If you do" that finishes each one
def color_want_asks(reply: str) -> list[str]:
    asks: list[str] = []

    sentence_before: str = ""

    ask_before: bool = False

    for sentence in split_sentences(reply):
        text: str = sentence.strip()

        if(text == ""):
            continue

        #"Send me a pic if you can" or "If you do, can you shoot a pic of it over" right after it is part of the same ask
        finishes_ask: bool = ask_before and not text.endswith("?") and (text.lower().startswith(IF_YOU_DO) or asks_for_pic(text))

        ask_before = finishes_ask or asks_color_wanted(text, sentence_before)

        if(ask_before):
            asks.append(text)

        sentence_before = text

    return asks
