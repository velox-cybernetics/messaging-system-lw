#IMPORTS

from helpers.response import cleaners
from helpers.response import spacing


#GLOBALS

#a text from the shop never has these, they only show up when the model leaks code or tokens
JUNK_MARKS: list[str] = ["{", "}", "<", "`", "\\"]

#a letter past 591 isn't latin, like hebrew or the chinese the model can slip into
LATIN_LIMIT: int = 591


#JUNK CHECKS

#whether a character is a junk mark or a letter from another alphabet
def is_junk(character: str) -> bool:
    if(character in JUNK_MARKS):
        return True

    return character.isalpha() and ord(character) > LATIN_LIMIT

#whether the text has any junk character in it
def has_junk(text: str) -> bool:
    for character in text:
        if(is_junk(character)):
            return True

    return False

#the text up to its first junk character
def cut_junk(text: str) -> str:
    kept_text: str = ""

    #the model never recovers once it slips, so everything from the first junk on goes
    for character in text:
        if(is_junk(character)):
            return kept_text

        kept_text = f"{kept_text}{character}"

    return kept_text


#SANITIZE

#the text with everything from its first junk character on cut, and its wrapping quotes taken off
def sanitize_text(text: str) -> str:
    if(has_junk(text)):
        print(f"JUNK CUT: {text}")

    kept_text: str = cut_junk(text)

    #wrapping quotes come off too, along with the one it opened the junk with
    return cleaners.strip_quotes(kept_text)

#the reply cleaned of junk, ending on its last whole sentence when the junk cut one in half
def sanitize_reply(reply: str) -> str:
    kept_reply: str = sanitize_text(reply)

    #a reply with no junk in it is kept whole, even when it does not end on a mark
    if(not has_junk(reply)):
        return kept_reply

    if(kept_reply.endswith((".", "!", "?"))):
        return kept_reply

    sentences: list[str] = spacing.split_sentences(kept_reply)

    #a lone sentence stays even unfinished, so a short sounds good still goes out
    if(len(sentences) < 2):
        return kept_reply

    whole_reply: str = ""

    #the junk cut into the last sentence, so the reply ends on the whole sentence before it
    for sentence in sentences[:-1]:
        whole_reply = f"{whole_reply}{sentence}"

    return whole_reply.strip()
