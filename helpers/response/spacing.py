#IMPORTS

import re

from helpers.response import cleaners


#GLOBALS

#a question with one of these in it asks them to get on the schedule
BOOKING_WORDS: list[str] = ["schedule", "scheduled", "book", "booked", "booking", "books"]

#a reply asking them for one of these is waiting on a pic
PIC_WORDS: list[str] = ["pic", "pics", "photo", "photos", "picture", "pictures", "video"]

#one of these with a pic word asks for the pic, like send me a pic, never like in the picture
PIC_ASK_WORDS: list[str] = ["send", "shoot", "snap"]

#how a reply says the color books are getting checked for the color they sent
COLOR_CHECK_PATTERN = re.compile(r"\b(let me|i'll|i will) check the color books\b|\bcheck the color books to see\b", re.IGNORECASE)

#a sentence that only says the books are still getting checked and they'll hear back, nothing else
STILL_CHECKING_PATTERN = re.compile(r"^(?:(?:and|also),?\s+)?(?:(?:i'm|im|we're)\s+)?still (?:checking|flipping through|going through|looking through) the colou?r books?(?:\s+(?:on|for)(?:\s+[\w'-]+){1,6})?(?:,?\s+(?:and\s+)?(?:i'll|ill|we'll|i will|we will|will)\s+let you know (?:what|once|when|as soon as|if) (?:i|we) (?:find|hear)(?:\s+(?:out|one|it|back))?)?[^\w?]*$", re.IGNORECASE)

#the i'll let you know what i find line, said on its own
FIND_LINE_PATTERN = re.compile(r"^(?:(?:and|also),?\s+)?(?:i'll|ill|we'll|i will|we will|will)\s+let you know (?:what|once|when|as soon as|if) (?:i|we) (?:find|hear)(?:\s+(?:out|one|it|back))?[^\w?]*$", re.IGNORECASE)

#colors a customer names, so an ask naming one reads as asking for the color they want
COLOR_NAMES: str = r"black|white|gr[ae]y|silver|red|blue|green|yellow|orange|purple|pink|brown|gold|bronze|teal|maroon|burgundy|navy|lime|olive|violet|copper|champagne|nardo"

#the word color on its own, never colored PPF, a color change or the color books
COLOR_WORD: str = r"\bcolou?rs?\b(?!\s+(?:change|changes|book|books)\b)"

COLOR_WORD_PATTERN = re.compile(COLOR_WORD, re.IGNORECASE)

#the word color or a color they could name
COLOR_REF_PATTERN = re.compile(rf"{COLOR_WORD}|\b(?:{COLOR_NAMES})\b", re.IGNORECASE)

#the word color plus one of these asks for the color they want, like what color are you thinking
COLOR_WANT_PATTERN = re.compile(r"\b(?:want|wants|wanting|wanted|thinking|thought|thoughts|like|liking|love|prefer|preference|go|going|leaning|looking|planning|pick|picked|picking|choose|choosing|chose|decide|decided|deciding|considering|favorite|favourite|after)\b", re.IGNORECASE)

#one of these makes it the color it is now instead, like what color is it right now
COLOR_NOW_PATTERN = re.compile(r"\b(?:is it|it is|it's|was it|it was|is the|is your|currently|current|right now|at the moment)\b|'s (?:it|the|your)\b", re.IGNORECASE)

#the color they want asked without the word color, like what you're wanting to go with
GO_WITH_PATTERN = re.compile(r"\b(?:go with|going with|go for|going for|to go)\b", re.IGNORECASE)

#only with them wanting it, never theres two ways to go or you're good to go
GO_WANT_PATTERN = re.compile(r"\b(?:want|wanting|wanted|wanna|thinking|looking|planning|leaning|like|hoping)\b", re.IGNORECASE)

#never the film or service they're going with, like going with the wrap
SERVICE_WORD_PATTERN = re.compile(r"\b(?:wrap|wrapped|ppf|tint|coating|ceramic|route|film)\b", re.IGNORECASE)

#a tint shade is never the color they want, tint has its own drama
SHADE_PATTERN = re.compile(r"\b(?:tint|tints|shade|shades)\b|%", re.IGNORECASE)

#any color you want is the price staying the same, never an ask, unless it asks them
ANY_COLOR_PATTERN = re.compile(r"\bany\s+(?:\w+\s+)?colou?rs?\b", re.IGNORECASE)

ASKS_YOU_PATTERN = re.compile(r"\b(?:have|did|do|are|were|got)\s+you\b", re.IGNORECASE)

#no question mark but still asking, like i'll need the make and model and the color
SOLICIT_PATTERN = re.compile(r"\b(?:need|needs|depends on|depend on|let me know|lmk)\b", re.IGNORECASE)

#the exact color asks own words, in mind, the green you're thinking, a pic of the exact one
IN_MIND_PATTERN = re.compile(r"\bin mind\b", re.IGNORECASE)

#in mind only asks with have or got in front, never keep in mind a wrap won't match factory red
HAVE_IN_MIND_PATTERN = re.compile(r"\b(?:have|has|had|got)\b.*\bin mind\b", re.IGNORECASE)

ONE_PATTERN = re.compile(r"\bones?\b", re.IGNORECASE)

NAMED_WANT_PATTERN = re.compile(rf"(?<!\bany\s)\b(?:colou?rs?|{COLOR_NAMES})\s+(?:that\s+)?(?:you're|you are|youre|you were|you'd|you|u)\s+(?:(?:still|really)\s+)?(?:thinking|wanting|want|wanted|like|liking|picked|leaning|have in mind|had in mind)\b", re.IGNORECASE)

EXACT_ASK_PATTERN = re.compile(r"\b(?:pics?|photos?|pictures?|screenshots?|links?)\s+(?:or\s+(?:a\s+)?(?:pics?|photos?|pictures?|screenshots?|links?)\s+)?of\s+(?:the|an?|that|your)\s+exact\b", re.IGNORECASE)

#the shop only sends them online for the exact color, so liking one online is that ask
ONLINE_PATTERN = re.compile(r"\bonline\b", re.IGNORECASE)

LIKING_PATTERN = re.compile(r"\byou(?:'re|'ve been|'ve| are| were| have been)?\s+(?:(?:still|really)\s+)?(?:want|wanting|wanted|like|liking|love|loving|eyeing)\b", re.IGNORECASE)

#a question asking two things splits into its parts here, color now and color wanted
CLAUSE_BREAK_PATTERN = re.compile(r"[,;:]|\b(?:and|or|but|so|plus)\b", re.IGNORECASE)

#the second half of the exact color ask, right after the in mind question
IF_YOU_DO: str = "if you do"

#the way the owner asks it, a held bookings reply ends on it once its price goes out
BOOKING_QUESTION: str = "Did you want to hop on the schedule?"

#a customers text that opens with a yes, however many ss they felt like typing
BOOKING_YES_PATTERN = re.compile(r"^\W*(y+e+s+(\s*sir)?|y+e+a+h*|y+a+h*|y+e+p+|y+u+p+|bet|sure|for sure|sounds good|i'?m down|absolutely|definitely)\b", re.IGNORECASE)

#asking what else they want to know is never one of the shops questions, like does that help
OFF_LIST_ASK_PATTERN = re.compile(r"\b(?:any|other|more)\s+(?:other\s+|more\s+)?questions?\b|\b(?:anything|something|what)\s+else\b.*\b(?:know|ask|help|need|curious|wonder\w*)\b|\b(?:anything|something)\s+else\s*\?|\bdoes\s+that\s+(?:help|make\s+sense)\b", re.IGNORECASE)

#a let me know sign off hands it back to them, same ask with no question mark
LET_ME_KNOW_PATTERN = re.compile(r"^(?:let me know|lmk|feel free)\b", re.IGNORECASE)

#a drop off day the way the booking chain offers it, only that chain reads the calendar
DAY_OFFER_PATTERN = re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday),? (the|january|february|march|april|may|june|july|august|september|october|november|december) \d{1,2}(st|nd|rd|th)?\b|\bopen for drop ?-?offs?\b", re.IGNORECASE)

#a reply can't open with the same word as one of the last this many replies
REPLIES_BETWEEN_OPENER: int = 2

#a text holds at most this many sentences, the rest of the reply goes out in the texts after it
TEXT_SENTENCES: int = 3

#the ways a reply opens with a yes, yeah first since its the usual one
YES_OPENERS: list[str] = ["Yeah", "Yess", "Yep"]

#the ways a reply opens acknowledging them, sweet first since its the usual one
ACK_OPENERS: list[str] = ["Sweet", "Perfect"]

#ack openers only open the reply, later parts or sentences pick up with this instead
FLOW_OPENER: str = "And"

#the owners no worries, swapped for its all good when a recent reply already opened with it
WORRIES_OPENER: str = "No worries"

WORRIES_SWAP: str = "It's all good"

#no worries at all goes out whole as its all good, never its all good at all
WORRIES_TAIL: str = " at all"


#SENT REPLIES

#every reply the shop already sent in the conversation, oldest first
def sent_replies(message_history: dict) -> list[str]:
    replies: list[str] = []

    for key, value in message_history.items():
        #an empty reply never went out, so it is not counted
        if(key.startswith("system_response_to_user_message_") and isinstance(value, str) and value != ""):
            replies.append(value)

    return replies

#the reply the shop sent last, empty when it hasn't sent one yet
def last_sent_reply(message_history: dict) -> str:
    replies: list[str] = sent_replies(message_history)

    if(len(replies) == 0):
        return ""

    return replies[-1]


#TEXT SPLITTING

#cuts a reply into sentences, each keeping its marks and the space or line break in front of it
def split_sentences(reply: str) -> list[str]:
    sentences: list[str] = []

    sentence: str = ""

    for position, character in enumerate(reply):
        next_character: str = reply[position + 1:position + 2]

        #a line break ends the sentence before it, so a markless line never runs into the next one
        if(character == "\n" and sentence.strip() != ""):
            sentences.append(sentence)

            sentence = ""

        sentence = f"{sentence}{character}"

        #a mark only ends a sentence before a space or the end, so a decimal price stays whole
        if(character in ".!?" and next_character in ["", " ", "\n"]):
            sentences.append(sentence)

            sentence = ""

    if(sentence != ""):
        sentences.append(sentence)

    return sentences

#ends the last sentence before more gets put after it, so it never runs into the next one
def end_sentence(text: str) -> str:
    text = text.strip()

    if(text != "" and (text[-1].isalnum() or text[-1] == "%")):
        return f"{text}."

    return text

#the sentences of one text, a blank line before each new part when the reply keeps its parts
def join_text(sentences: list[str], new_part: list[bool], group: list[int], keep_parts: bool) -> str:
    text: str = sentences[group[0]]

    for position in group[1:]:
        separator: str = " "

        if(keep_parts and new_part[position]):
            separator = "\n\n"

        #a line with no mark at its end ends its sentence before the next one goes on after it
        text = f"{end_sentence(text)}{separator}{sentences[position]}"

    return text

#a question always starts its own text and takes what follows, the rest go out a few to a text
def split_texts(reply: str) -> list[str]:
    pieces: list[str] = []

    for piece in split_sentences(reply):
        if(piece.strip() != ""):
            pieces.append(piece)

    sentences: list[str] = []

    for piece in pieces:
        sentences.append(piece.strip())

    new_part: list[bool] = []

    #split_sentences leaves the line break in front of the next sentence, so that one starts a part
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
        elif(after_question or (len(groups) > 0 and len(groups[-1]) < TEXT_SENTENCES)):
            #anything after a question rides along with it, like the pic ask that finishes it
            groups[-1].append(position)
        else:
            groups.append([position])

    #several texts already read in pieces, only a single text spaces its parts out
    keep_parts: bool = len(groups) == 1

    texts: list[str] = []

    for position, group in enumerate(groups):
        text: str = join_text(sentences, new_part, group, keep_parts)

        #every text but the last drops its period, thats how the shop texts
        if(position < len(groups) - 1):
            text = text.removesuffix(".")

        texts.append(text)

    return texts

#the texts back together a blank line apart, for a chat where every text counts toward blooios cap
def one_text(texts: list[str]) -> str:
    return "\n\n".join(texts)


#OPENER SPACING

#whether the replys first word is this word
def opens_with(reply: str, word: str) -> bool:
    start: str = reply.strip().lower()

    if(not start.startswith(word)):
        return False

    character_after: str = start[len(word):len(word) + 1]

    #sweetest doesn't open with sweet, no matter how sweet it is
    return not character_after.isalpha()

#whether one of the last couple of replies the shop sent opened with this word
def opened_recently(message_history: dict, word: str) -> bool:
    recent_replies: list[str] = sent_replies(message_history)[-REPLIES_BETWEEN_OPENER:]

    #the word at one reply means the next two open without it
    for recent_reply in recent_replies:
        if(opens_with(recent_reply, word)):
            return True

    return False

#whether the reply opens with a word the last couple of replies already opened with
def repeats_opener(reply: str, message_history: dict, word: str) -> bool:
    return opens_with(reply, word) and opened_recently(message_history, word)

#what an opener leads into, so sweet so the price is leads into the price is
def opener_rest(reply: str, word: str) -> str:
    rest: str = reply.strip()[len(word):].lstrip(" ,.!")

    if(rest.lower().startswith("so ")):
        return rest[len("so "):]

    if(rest.lower().startswith("and ")):
        return rest[len("and "):]

    return rest

#cuts a repeated opener off the front of the reply, so it starts with what the opener led into
def cut_opener(reply: str, message_history: dict, word: str) -> str:
    if(not repeats_opener(reply, message_history, word)):
        return reply

    #sweet so the price is reads as the price is once sweet is cut
    rest: str = opener_rest(reply, word)

    #a reply that is only the word keeps it, so something still goes out
    if(rest.strip() == ""):
        return reply

    print(f"{word.upper()} CUT: {reply}")

    return cleaners.sentence_start(rest)

#a repeated opener gets another from its group, or gets cut when they all went out lately
def swap_opener(reply: str, message_history: dict, openers: list[str]) -> str:
    for opener in openers:
        word: str = opener.lower()

        if(not repeats_opener(reply, message_history, word)):
            continue

        #swaps for the first one in its group not used lately
        for swap in openers:
            if(not opened_recently(message_history, swap.lower())):
                print(f"{word.upper()} SWAPPED FOR {swap.upper()}: {reply}")

                return f"{swap}{reply.strip()[len(word):]}"

        #every opener in the group opened a recent reply, so the word just gets cut
        return cut_opener(reply, message_history, word)

    return reply

#a repeated no worries goes out as its all good, and comes off when that went out lately too
def swap_worries(reply: str, message_history: dict) -> str:
    word: str = WORRIES_OPENER.lower()

    if(not repeats_opener(reply, message_history, word)):
        return reply

    rest: str = reply.strip()[len(word):].removeprefix(WORRIES_TAIL)

    #its all good opened a recent reply too, so the reply starts with what no worries led into
    if(opened_recently(message_history, WORRIES_SWAP.lower())):
        cut_rest: str = rest.lstrip(" ,.!")

        #a reply that is only the words keeps them, so something still goes out
        if(cut_rest.strip() == ""):
            return reply

        print(f"{word.upper()} CUT: {reply}")

        return cleaners.sentence_start(cut_rest)

    print(f"{word.upper()} SWAPPED FOR {WORRIES_SWAP.upper()}: {reply}")

    return f"{WORRIES_SWAP}{rest}"


#FLOW OPENERS

#the ack opener a sentence opens with, never one thats part of what it says like perfect for
def ack_opener(sentence: str) -> str:
    start: str = sentence.strip().lower()

    for opener in ACK_OPENERS:
        word: str = opener.lower()

        after: str = start[len(word):]

        if(opens_with(start, word) and (after == "" or after.startswith((",", ".", "!", " so ", " and ")))):
            return word

    return ""

#a word capitalized just for starting the sentence goes lowercase after and, PPF and McLaren stay
def flow_case(text: str) -> str:
    first_word: str = text.split(" ", 1)[0]

    if(len(first_word) > 1 and first_word[0].isupper() and first_word[1].isalpha() and first_word[1:].islower()):
        return f"{text[:1].lower()}{text[1:]}"

    return text

#a sweet or perfect opening a later part or sentence goes out as and, picking up from before
def flow_openers(reply: str) -> str:
    flowed: str = ""

    #a lone sweet goes with the sentence after it, and one with nothing after it comes off
    carried: str = ""

    for piece in split_sentences(reply):
        sentence: str = f"{carried}{piece}"

        carried = ""

        word: str = ack_opener(sentence)

        #the replys first sentence keeps its opener, swap_opener spaces those out
        if(word == "" or flowed.strip() == ""):
            flowed = f"{flowed}{sentence}"

            continue

        rest: str = opener_rest(sentence, word)

        if(rest.strip() == ""):
            carried = sentence

            continue

        body: str = sentence.lstrip()

        #what came after a sweet with a mark started its own sentence, after and its the same one
        if(body[len(word):len(word) + 1] in [".", "!"]):
            rest = flow_case(rest)

        print(f"{word.upper()} SWAPPED FOR {FLOW_OPENER.upper()}: {reply}")

        #the line break or space in front of it stays, so the part it opens stays its own part
        flowed = f"{flowed}{sentence[:len(sentence) - len(body)]}{FLOW_OPENER} {rest}"

    return flowed

#and never opens two sentences in a row, whether flow_openers put it there or the model did
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


#BOOKING ASKS

#whether the sentence is a question asking them to get on the schedule
def asks_booking(sentence: str) -> bool:
    if(not sentence.strip().endswith("?")):
        return False

    for word in sentence.lower().split():
        if(word.strip(",.?!") in BOOKING_WORDS):
            return True

    return False

#whether the sentence has one of the words in it, a mark stuck to the word never hides it
def has_word(sentence: str, words: list[str]) -> bool:
    for word in sentence.lower().split():
        if(word.strip(",.?!") in words):
            return True

    return False

#a reply that asks them for a pic, a photo or a video, never one that only mentions theirs
def asks_for_pic(reply: str) -> bool:
    for sentence in split_sentences(reply):
        if(not has_word(sentence, PIC_WORDS)):
            continue

        #a question about a pic asks for it, and so does telling them to send, shoot or snap one
        if(sentence.strip().endswith("?") or has_word(sentence, PIC_ASK_WORDS)):
            return True

    return False

#a reply that tells them the color books are getting checked for the color they sent
def promises_color_check(reply: str) -> bool:
    return COLOR_CHECK_PATTERN.search(reply) is not None

#a sweet or perfect with no price just leads into the booking question, sweet so leads to an answer
def booking_lead_in(sentence: str) -> bool:
    word: str = ack_opener(sentence)

    if(word == "" or "$" in sentence or sentence.strip().endswith("?")):
        return False

    rest: str = sentence.strip()[len(word):].lstrip(" ,.!")

    return not rest.lower().startswith("so ")

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

        #what only led into the question comes off with it, unless its all the reply has left
        if(len(kept_sentences) > 0 and booking_lead_in(kept_sentences[-1]) and "".join(kept_sentences[:-1]).strip() != ""):
            cut_lead_ins.append(kept_sentences.pop().strip())

    kept_reply: str = "".join(kept_sentences)

    #only the booking question is how a go ahead gets answered, so it stays and something goes out
    if(kept_reply.strip() == ""):
        return reply

    for sentence in cut_questions:
        print(f"BOOKING QUESTION CUT: {sentence}")

    for sentence in cut_lead_ins:
        print(f"BOOKING LEAD IN CUT: {sentence}")

    return kept_reply.strip()

#whether any sentence of the reply asks them to get on the schedule
def asks_booking_question(reply: str) -> bool:
    for sentence in split_sentences(reply):
        if(asks_booking(sentence)):
            return True

    return False

#their text opens with a yes and the shops last reply asked about getting on the schedule
def yes_to_booking_question(user_text: str, message_history: dict) -> bool:
    return BOOKING_YES_PATTERN.match(user_text) is not None and asks_booking_question(last_sent_reply(message_history))

#a reply that has to end on the booking question gets it put at its end
def end_on_booking_question(reply: str) -> str:
    if(asks_booking_question(reply)):
        return reply

    kept_reply: str = ""

    #the booking question is the one question it ends on, others go unless a price is in them
    for sentence in split_sentences(reply):
        if(not sentence.strip().endswith("?") or "$" in sentence):
            kept_reply = f"{kept_reply}{sentence}"

    return f"{end_sentence(kept_reply)} {BOOKING_QUESTION}"

#whether the sentence offers a drop off day
def offers_days(sentence: str) -> bool:
    return DAY_OFFER_PATTERN.search(sentence) is not None

#only the booking chain reads the calendar, any other day offer is made up and its sentence goes
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


#HELD PRICES

#on a first reply that holds every price, any sentence with a dollar sign comes off
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


#WANTED COLOR

#whether part of an ask goes after the color they want, never the color now or any color
def wants_color_part(part: str, about_color: bool) -> bool:
    if(COLOR_NOW_PATTERN.search(part) is not None or SHADE_PATTERN.search(part) is not None):
        return False

    if(ANY_COLOR_PATTERN.search(part) is not None and ASKS_YOU_PATTERN.search(part) is None):
        return False

    if(COLOR_WORD_PATTERN.search(part) is not None and COLOR_WANT_PATTERN.search(part) is not None):
        return True

    #wanting to go with only counts in a sentence about color, never the film they're going with
    if(not about_color or GO_WITH_PATTERN.search(part) is None or SERVICE_WORD_PATTERN.search(part) is not None):
        return False

    return GO_WANT_PATTERN.search(part) is not None

#whether the sentence asks for the color they want, sentence_before gives a bare one its color
def asks_color_wanted(sentence: str, sentence_before: str) -> bool:
    text: str = sentence.replace("’", "'").strip()

    #a pic or link of the exact one, never a pic showing the color it is now
    if(EXACT_ASK_PATTERN.search(text) is not None and COLOR_NOW_PATTERN.search(text) is None):
        return True

    if(IN_MIND_PATTERN.search(text) is not None and (text.endswith("?") or HAVE_IN_MIND_PATTERN.search(text) is not None)):
        if(COLOR_REF_PATTERN.search(text) is not None):
            return True

        if(ONE_PATTERN.search(text) is not None and COLOR_WORD_PATTERN.search(sentence_before) is not None):
            return True

    asking: bool = False

    if(text.endswith("?") or SOLICIT_PATTERN.search(text) is not None):
        asking = True

    #the exact matte black you're thinking asks for it in a question or a pic ask
    if((asking or asks_for_pic(text)) and NAMED_WANT_PATTERN.search(text) is not None):
        return True

    if(not asking):
        return False

    #the online hunt is always for the exact color, never a tint shade
    if(ONLINE_PATTERN.search(text) is not None and LIKING_PATTERN.search(text) is not None):
        if(COLOR_NOW_PATTERN.search(text) is None and SHADE_PATTERN.search(text) is None):
            return True

    about_color: bool = COLOR_WORD_PATTERN.search(text) is not None

    for part in CLAUSE_BREAK_PATTERN.split(text):
        if(wants_color_part(part, about_color)):
            return True

    return False

#a pic ask or an if you do right after a question finishes that ask, never its own question
def finishes_ask(text: str) -> bool:
    return not text.endswith("?") and (text.lower().startswith(IF_YOU_DO) or asks_for_pic(text))

#the sentences asking for the color they want, plus the pic or if you do that finishes each
def color_want_asks(reply: str) -> list[str]:
    asks: list[str] = []

    sentence_before: str = ""

    ask_before: bool = False

    for sentence in split_sentences(reply):
        text: str = sentence.strip()

        if(text == ""):
            continue

        #a pic ask or an if you do right after it is part of the same ask
        finishing: bool = ask_before and finishes_ask(text)

        if(finishing or asks_color_wanted(text, sentence_before)):
            ask_before = True
        else:
            ask_before = False

        if(ask_before):
            asks.append(text)

        sentence_before = text

    return asks


#CURRENT COLOR

#whether the sentence asks what color there vehicle is now or for a pic of it, any pic ask counts
def asks_color_now(sentence: str) -> bool:
    text: str = sentence.replace("’", "'").strip()

    #any pic ask counts, they're all after the same thing
    if(asks_for_pic(text)):
        return True

    if(not text.endswith("?")):
        return False

    #one part with both the word color and what makes it the color it is now
    for part in CLAUSE_BREAK_PATTERN.split(text):
        if(COLOR_WORD_PATTERN.search(part) is not None and COLOR_NOW_PATTERN.search(part) is not None):
            return True

    return False

#the sentences asking for the color now or a pic of it, never the exact color ask or its pic
def color_now_asks(reply: str) -> list[str]:
    #the if you do pic ask belongs to the color they want, so the whole exact color ask stays out
    want_asks: list[str] = color_want_asks(reply)

    asks: list[str] = []

    for sentence in split_sentences(reply):
        text: str = sentence.strip()

        if(text != "" and text not in want_asks and asks_color_now(text)):
            asks.append(text)

    return asks


#ANYTHING ELSE

#the sentences asking what else they want to know, as a question or a let me know sign off
def off_list_asks(reply: str) -> list[str]:
    asks: list[str] = []

    for sentence in split_sentences(reply):
        text: str = sentence.replace("’", "'").strip()

        asks_them: bool = False

        if(text.endswith("?") or LET_ME_KNOW_PATTERN.match(text) is not None):
            asks_them = True

        if(asks_them and OFF_LIST_ASK_PATTERN.search(text) is not None):
            asks.append(sentence.strip())

    return asks


#STILL CHECKING

#the sentences that only say the books are still getting checked or that they'll hear back
def still_checking_lines(reply: str) -> list[str]:
    lines: list[str] = []

    for sentence in split_sentences(reply):
        text: str = sentence.replace("’", "'").strip()

        if(STILL_CHECKING_PATTERN.match(text) is not None or FIND_LINE_PATTERN.match(text) is not None):
            lines.append(sentence.strip())

    return lines

#whether the shop already told them the color books are getting checked, the first time or since
def color_check_sent(message_history: dict) -> bool:
    for reply in sent_replies(message_history):
        if(promises_color_check(reply) or len(still_checking_lines(reply)) > 0):
            return True

    return False
