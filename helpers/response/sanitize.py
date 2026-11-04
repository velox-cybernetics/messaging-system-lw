#**********IMPORTS**********
#the quote cleanup and the sentence splitter, to cut junk off a reply cleanly
from helpers.response import cleaners
from helpers.response import spacing



#**********GLOBALS**********
#the characters that only show up when the model leaks code, tokens or another alphabet


#JUNK MARKS
#a text from the shop never has these, they only show up when the model leaks code or tokens like "} or <|endoftext|>
JUNK_MARKS: list[str] = ["{", "}", "<", "`", "\\"]


#LATIN LIMIT
#a letter past 591 is not from a latin alphabet, like the hebrew in "תקלה" or the chinese the model can slip into
LATIN_LIMIT: int = 591



#**********JUNK CHECKS**********
#spots a junk character in a text and cuts the text off where the first one shows up


#IS JUNK
#whether a character is a junk mark or a letter from another alphabet
def is_junk(character: str) -> bool:
    if(character in JUNK_MARKS):
        return True

    return character.isalpha() and ord(character) > LATIN_LIMIT


#HAS JUNK
#whether the text has any junk character in it
def has_junk(text: str) -> bool:
    for character in text:
        if(is_junk(character)):
            return True

    return False


#CUT JUNK
#the text up to its first junk character
def cut_junk(text: str) -> str:
    kept_text: str = ""

    #the model never comes back to the text once it slips, so everything from the first junk character on is cut
    for character in text:
        if(is_junk(character)):
            return kept_text

        kept_text = f"{kept_text}{character}"

    return kept_text



#**********SANITIZE**********
#cleans the junk out of a text or a reply, so a reply only goes out as whole sentences


#SANITIZE TEXT
#the text with everything from its first junk character on cut, and its wrapping quotes taken off
def sanitize_text(text: str) -> str:
    if(has_junk(text)):
        print(f"JUNK CUT: {text}")

    kept_text: str = cut_junk(text)

    #quotes the model wraps the text in, or the one it opened the junk with like the " in "}, come off too
    return cleaners.strip_quotes(kept_text)


#SANITIZE REPLY
#the reply cleaned of junk, ending on its last whole sentence when the junk cut one in half
def sanitize_reply(reply: str) -> str:
    kept_reply: str = sanitize_text(reply)

    #a reply with no junk in it is kept whole, even when it does not end on a mark
    if(not has_junk(reply)):
        return kept_reply

    if(kept_reply.endswith((".", "!", "?"))):
        return kept_reply

    sentences: list[str] = spacing.split_sentences(kept_reply)

    #the only sentence stays even when unfinished, so a short reply like "Sounds good" still goes out
    if(len(sentences) < 2):
        return kept_reply

    whole_reply: str = ""

    #the junk cut into the last sentence, so the reply ends on the whole sentence before it
    for sentence in sentences[:-1]:
        whole_reply = f"{whole_reply}{sentence}"

    return whole_reply.strip()
