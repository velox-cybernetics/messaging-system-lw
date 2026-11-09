#IMPORTS

import re


#GLOBALS

#hazel laughs with haha, lol or the emoji, anything else like hehe or lmao gets caught
OTHER_LAUGHS = re.compile(r"\b(?!haha\b)(?:a?ha(?:ha)+h?|hah?|heh|he(?:he)+|lmf?ao+)\b", re.IGNORECASE)


#LAUGH SWAP

#what a laugh the model wrote goes out as
def swapped_laugh(match) -> str:
    #a laugh that opened a sentence stays capitalized
    if(match.group(0)[0].isupper()):
        return "Haha"

    return "haha"

#the reply with every other laugh in it swapped for haha
def fix_laughs(reply: str) -> str:
    fixed_reply: str = OTHER_LAUGHS.sub(swapped_laugh, reply)

    if(fixed_reply != reply):
        print(f"LAUGH SWAPPED: {reply}")

    return fixed_reply
