#IMPORTS

from helpers.response import spacing


#GLOBALS

#words any question can be worded with, so two questions only get compared on what they ask for
FILLER_WORDS: set[str] = {"a", "an", "the", "this", "that", "these", "those", "it", "its", "itll", "they", "them", "their", "theyre", "you", "your", "youre", "youd", "we", "our", "us", "i", "me", "my", "im", "all", "any", "some", "each", "both", "are", "is", "was", "were", "be", "been", "am", "do", "does", "did", "have", "has", "had", "got", "get", "getting", "go", "going", "can", "could", "would", "will", "should", "want", "wanting", "wanted", "looking", "look", "thinking", "think", "leaning", "towards", "toward", "need", "needing", "like", "know", "done", "what", "whats", "which", "who", "how", "when", "where", "why", "and", "or", "but", "so", "if", "of", "on", "in", "to", "at", "for", "from", "with", "about", "as", "by", "then", "too", "also", "just", "only", "again", "yeah", "yep", "yessir", "sweet", "perfect", "sure", "ok", "okay", "cool", "awesome", "quick", "question", "hey", "well", "now", "right", "there"}

#two questions sharing at least this much of what they ask for are the same question
REPEAT_SIMILARITY: float = 0.5

#a short question shares too little to tell, so only teh very same words count
MIN_ASKED_WORDS: int = 3


#QUESTION WORDS

#the sentences of a reply that end on a question mark
def question_sentences(reply: str) -> list[str]:
    questions: list[str] = []

    for sentence in spacing.split_sentences(reply):
        if(sentence.strip().endswith("?")):
            questions.append(sentence.strip())

    return questions

#a texts words, lowercase, with its marks taken out
def plain_words(text: str) -> list[str]:
    plain_text: str = ""

    for character in text.lower():
        #an apostrophe joins the word back up, so whats reads as whats
        if(character in "'’"):
            continue
        elif(character.isalnum()):
            plain_text = f"{plain_text}{character}"
        else:
            plain_text = f"{plain_text} "

    return plain_text.split()

#the words of what a question asks for, every filler word and number left out
def asked_words(question: str) -> set[str]:
    words: set[str] = set()

    for word in plain_words(question):
        #a number is how many, never what it asks, so on the 19 vans is the same as on the vans
        if(word in FILLER_WORDS or word.isdigit()):
            continue

        asked_word: str = word

        #decals and decal ask for the same thing
        if(len(word) > 3 and word.endswith("s") and not word.endswith("ss")):
            asked_word = word[:-1]

        words.add(asked_word)

    return words

#whether two questions ask for the same thing, the same words or most of them
def same_question(question: str, asked: str) -> bool:
    #the very same words always ask the same thing, even a question thats all filler
    if(plain_words(question) == plain_words(asked)):
        return True

    words: set[str] = asked_words(question)

    asked_before: set[str] = asked_words(asked)

    if(len(words) == 0 or len(asked_before) == 0):
        return False

    if(words == asked_before):
        return True

    if(min(len(words), len(asked_before)) < MIN_ASKED_WORDS):
        return False

    shared_words: set[str] = words & asked_before

    all_words: set[str] = words | asked_before

    #mostly the same words is the same question reworded, and the customer would notice
    return len(shared_words) / len(all_words) >= REPEAT_SIMILARITY


#REPEATED QUESTIONS

#a question can go out again until answered, never worded like one the shop already asked
def repeated_questions(reply: str, earlier_replies: list[str]) -> list[str]:
    asked_before: list[str] = []

    for earlier_reply in earlier_replies:
        asked_before.extend(question_sentences(earlier_reply))

    repeated: list[str] = []

    for question in question_sentences(reply):
        for asked in asked_before:
            if(same_question(question, asked)):
                repeated.append(question)

                break

    return repeated

#the reply with these questions taken out of it
def drop_questions(reply: str, questions: list[str]) -> str:
    kept_reply: str = ""

    for sentence in spacing.split_sentences(reply):
        if(sentence.strip() not in questions):
            kept_reply = f"{kept_reply}{sentence}"

    return kept_reply.strip()

#whether the reply that went out asked this, first word skipped since the opener can get swapped
def asked_in(question: str, reply: str) -> bool:
    words: list[str] = plain_words(question)

    if(len(words) > 1):
        words = words[1:]

    if(len(words) == 0):
        return False

    question_text: str = " ".join(words)

    reply_text: str = " ".join(plain_words(reply))

    return f" {question_text} " in f" {reply_text} "


#ASKS

#a sentence with a line break in front of it starts another part of the reply
def starts_part(sentence: str) -> bool:
    lead: str = sentence[:len(sentence) - len(sentence.lstrip())]

    return "\n" in lead

#where a questions ask ends, past the sentences right after it that finish it in the same part
def ask_end(sentences: list[str], question_position: int) -> int:
    end: int = question_position + 1

    while(end < len(sentences) and not starts_part(sentences[end]) and spacing.finishes_ask(sentences[end].strip())):
        end += 1

    return end

#every ask in a reply, each question with the sentences that finish it, like the pic follow up
def asks(reply: str) -> list[str]:
    sentences: list[str] = spacing.split_sentences(reply)

    reply_asks: list[str] = []

    for position, sentence in enumerate(sentences):
        if(sentence.strip().endswith("?")):
            reply_asks.append("".join(sentences[position:ask_end(sentences, position)]).strip())

    return reply_asks

#the first sentence of the ask and the one after its last, none when the reply doesn't ask it
def ask_spot(sentences: list[str], question: str) -> tuple[int, int] | None:
    for position, sentence in enumerate(sentences):
        if(sentence.strip() == question):
            return (position, ask_end(sentences, position))

    return None

#the reply with that ask reworded, or taken out when their are no new words
def swap_ask(sentences: list[str], spot: tuple[int, int], wording: str) -> str:
    before: str = "".join(sentences[:spot[0]])

    after: str = "".join(sentences[spot[1]:])

    if(wording == ""):
        return f"{before}{after}".strip()

    #the new words keep the space or line break the ask had, so the reply keeps its parts
    first_sentence: str = sentences[spot[0]]

    lead: str = first_sentence[:len(first_sentence) - len(first_sentence.lstrip())]

    #new words that stop with no period never run into a sentence that follows them in the same part
    if(after.strip() != "" and not starts_part(after)):
        wording = spacing.end_sentence(wording)

    return f"{before}{lead}{wording}{after}".strip()
