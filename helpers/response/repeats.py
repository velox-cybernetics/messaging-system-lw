#**********IMPORTS**********
#the sentence splitter, to pull the questions out of a reply
from helpers.response import spacing



#**********GLOBALS**********
#the words every question shares and how alike two questions have to be to count as the same


#FILLER WORDS
#words any question can be worded with, so two questions only get compared on what they ask for
FILLER_WORDS: set[str] = {"a", "an", "the", "this", "that", "these", "those", "it", "its", "itll", "they", "them", "their", "theyre", "you", "your", "youre", "youd", "we", "our", "us", "i", "me", "my", "im", "all", "any", "some", "each", "both", "are", "is", "was", "were", "be", "been", "am", "do", "does", "did", "have", "has", "had", "got", "get", "getting", "go", "going", "can", "could", "would", "will", "should", "want", "wanting", "wanted", "looking", "look", "thinking", "think", "leaning", "towards", "toward", "need", "needing", "like", "know", "done", "what", "whats", "which", "who", "how", "when", "where", "why", "and", "or", "but", "so", "if", "of", "on", "in", "to", "at", "for", "from", "with", "about", "as", "by", "then", "too", "also", "just", "only", "again", "yeah", "yep", "yessir", "sweet", "perfect", "sure", "ok", "okay", "cool", "awesome", "quick", "question", "hey", "well", "now", "right", "there"}


#REPEAT COUNTS
#two questions sharing at least this much of what they ask for are the same question asked the same way
REPEAT_SIMILARITY: float = 0.5

#a short question shares too little to tell, so it only counts as the same when it asks for the very same words
MIN_ASKED_WORDS: int = 3



#**********QUESTION WORDS**********
#pulls the questions out of a reply and boils each one down to the words of what it asks for


#QUESTION SENTENCES
#the sentences of a reply that end on a question mark
def question_sentences(reply: str) -> list[str]:
    questions: list[str] = []

    for sentence in spacing.split_sentences(reply):
        if(sentence.strip().endswith("?")):
            questions.append(sentence.strip())

    return questions


#PLAIN WORDS
#a text's words, lowercase, with its marks taken out
def plain_words(text: str) -> list[str]:
    plain_text: str = ""

    for character in text.lower():
        #an apostrophe joins the word back up, so "what's" reads as whats
        if(character in "'’"):
            continue

        elif(character.isalnum()):
            plain_text = f"{plain_text}{character}"

        else:
            plain_text = f"{plain_text} "

    return plain_text.split()


#ASKED WORDS
#the words of what a question asks for, every filler word and number left out
def asked_words(question: str) -> set[str]:
    words: set[str] = set()

    for word in plain_words(question):
        #a number is how many it's for, never what it asks, so "on the 19 vans" asks the same as "on the vans"
        if(word in FILLER_WORDS or word.isdigit()):
            continue

        asked_word: str = word

        #decals and decal ask for the same thing
        if(len(word) > 3 and word.endswith("s") and not word.endswith("ss")):
            asked_word = word[:-1]

        words.add(asked_word)

    return words


#SAME QUESTION
#whether two questions ask for the same thing, the same words or most of them
def same_question(question: str, asked: str) -> bool:
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

    #reworded with the same options, like "full wrap, half wrap or just decals" on them and then on the vans and trucks
    return len(shared_words) / len(all_words) >= REPEAT_SIMILARITY



#**********REPEATED QUESTIONS**********
#finds the questions a reply asks again that the shop already asked, and takes them out of it


#REPEATED QUESTIONS
#a question can go out again until it's answered, never in the words or the manner of one the shop already asked
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


#DROP QUESTIONS
#the reply with these questions taken out of it
def drop_questions(reply: str, questions: list[str]) -> str:
    kept_reply: str = ""

    for sentence in spacing.split_sentences(reply):
        if(sentence.strip() not in questions):
            kept_reply = f"{kept_reply}{sentence}"

    return kept_reply.strip()


#ASKED IN
#whether the reply that went out asked this question, its first word left off since the opener can get swapped
def asked_in(question: str, reply: str) -> bool:
    words: list[str] = plain_words(question)

    if(len(words) > 1):
        words = words[1:]

    if(len(words) == 0):
        return False

    question_text: str = " ".join(words)

    reply_text: str = " ".join(plain_words(reply))

    return f" {question_text} " in f" {reply_text} "
