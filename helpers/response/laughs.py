#**********IMPORTS**********
#python's text patterns, to find the laughs the shop never writes
import re



#**********GLOBALS**********
#the laughs the model writes that hazel never does


#OTHER LAUGHS
#hazel only laughs with haha, lol or 😂, so any other laugh the model writes, like "Hahaha", "hehe" or "lmao", is one of these words
OTHER_LAUGHS: re.Pattern[str] = re.compile(r"\b(?!haha\b)(?:a?ha(?:ha)+h?|hah?|heh|he(?:he)+|lmf?ao+)\b", re.IGNORECASE)



#**********LAUGH SWAP**********
#swaps any other laugh in a reply for haha, so it sounds like hazel


#SWAPPED LAUGH
#what a laugh the model wrote goes out as
def swapped_laugh(match: re.Match[str]) -> str:
    #a laugh that opened a sentence stays capitalized, so "Hahaha no" goes out as "Haha no"
    if(match.group(0)[0].isupper()):
        return "Haha"

    return "haha"


#FIX LAUGHS
#the reply with every other laugh in it swapped for haha
def fix_laughs(reply: str) -> str:
    fixed_reply: str = OTHER_LAUGHS.sub(swapped_laugh, reply)

    if(fixed_reply != reply):
        print(f"LAUGH SWAPPED: {reply}")

    return fixed_reply
