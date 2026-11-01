#**********IMPORTS**********
#python's json and text patterns, the notes check every reply already gets when it's written, and the shop's details files
import json
import re

from helpers.response import reasoning
from src import branches



#**********ADDRESSES**********
#what a street address looks like in a reply, and the shop's own written the same way, so any other one is made up


#STREET TYPES
#the words that end a street name, spelled out or short
#drive, road and trail are left out, in a reply they're a vehicle's trim far more often than a street, like the F-250 4 Wheel Drive, the Wrangler 392 Off Road or the Silverado 1500 LT Trail Boss
STREET_TYPES: str = r"St|Street|Ave|Avenue|Blvd|Boulevard|Ln|Lane|Way|Hwy|Highway|Pkwy|Parkway|Ct|Court|Cir|Circle|Pl|Place|Ter|Terrace|Loop"


#STREET ADDRESS
#a house number, up to four capitalized words and the street type, like 123 Main St or 105 S 700 E St
STREET_ADDRESS: re.Pattern[str] = re.compile(rf"\b\d{{2,6}}(?:\s+[A-Z0-9][\w'.-]*){{0,4}}?\s+(?:{STREET_TYPES})\b")


#DIRECTIONS
DIRECTIONS: str = r"N|S|E|W|North|South|East|West"


#GRID ADDRESS
#utah's grid addresses are a house number, a direction, a block number and a direction, like 105 S 700 E, with no street type needed
GRID_ADDRESS: re.Pattern[str] = re.compile(rf"\b\d{{1,5}}\s+(?:{DIRECTIONS})\.?\s+\d{{1,5}}\s+(?:{DIRECTIONS})\b")


#SHORT WORDS
#a direction or street type spelled out reads the same as its short form, so 105 South 700 East is the shop's 105 S 700 E
SHORT_WORDS: dict[str, str] = {"north": "n", "south": "s", "east": "e", "west": "w", "street": "st", "avenue": "ave", "boulevard": "blvd", "lane": "ln", "highway": "hwy", "parkway": "pkwy", "court": "ct", "circle": "cir", "place": "pl", "terrace": "ter"}


#ADDRESS WORDS
#an address as lowercase words with its marks off and every long word shortened, one space between each and one on each end
def address_words(text: str) -> str:
    words: list[str] = []

    for word in re.sub(r"[.,#]", " ", text.lower()).split():
        words.append(SHORT_WORDS.get(word, word))

    return f" {' '.join(words)} "


#SHOP ADDRESSES
#every address the business details give, from the same file the replies answer from so the two never drift apart
def shop_addresses() -> list[str]:
    addresses: list[str] = []

    for details in branches.BUSINESS_DETAILS.values():
        for address in details.get("Shop Address", []):
            addresses.append(address_words(address))

    return addresses


#SHOP ADDRESS WORDS
SHOP_ADDRESSES: list[str] = shop_addresses()


#SHOP ADDRESS
#True when the address is the shop's or a piece of it, like 105 S 700 E out of 105 S 700 E St Unit E
def is_shop_address(address: str) -> bool:
    for shop_address in SHOP_ADDRESSES:
        if(address_words(address) in shop_address):
            return True

    return False


#UNKNOWN ADDRESS
#the first address in the reply that isn't the shop's, empty when there is none
def unknown_address(reply: str) -> str:
    for pattern in [STREET_ADDRESS, GRID_ADDRESS]:
        for found in pattern.finditer(reply):
            if(not is_shop_address(found.group())):
                return found.group()

    return ""



#**********LINKS**********
#what a link looks like in a reply, and the shop's own sites, so a link anywhere else is made up


#LINK ENDINGS
#the endings a phone turns into a tappable link even with no https:// in front, everyday words like "in" or "to" are left out
LINK_ENDINGS: str = r"com|net|org|info|biz|xyz|io|co|ly|us|me|tv|ai|gg|app|dev|link|site|online|shop|store|live|page|club"


#LINK
#"https://...", "www...." or a bare "site.com/path", the domain of an email like lonewraps@gmail.com and a handle like @lone.wraps are never links
LINK: re.Pattern[str] = re.compile(rf"(?<![\w@.-])(?:(?:https?://|www\.)[^\s<>\"']+|(?:[a-z0-9-]+\.)+(?:{LINK_ENDINGS})\b[^\s<>\"']*)", re.IGNORECASE)


#LINK END MARKS
#a mark right after a link ends the sentence, it's never part of the link
LINK_END_MARKS: str = ".,;:!?)"


#LINK HOST
#the site a link goes to, lowercase with no https, no www and nothing after it, "lonewraps.com" for "https://www.lonewraps.com/quote."
def link_host(link: str) -> str:
    host: str = link.lower().rstrip(LINK_END_MARKS)

    host = host.split("://", 1)[-1]

    host = re.split(r"[/?#:]", host, maxsplit=1)[0]

    return host.removeprefix("www.")


#SHOP LINK HOSTS
#every site the shop's details link to, from the same files the replies answer from so the two never drift apart
def shop_link_hosts() -> set[str]:
    hosts: set[str] = set()

    for details in [branches.BUSINESS_DETAILS, branches.PRICING_DETAILS, branches.CUSTOM_DETAILS]:
        for link in LINK.findall(json.dumps(details)):
            hosts.add(link_host(link))

    return hosts


#SHOP SITES
SHOP_LINK_HOSTS: set[str] = shop_link_hosts()


#UNKNOWN LINK
#the first link in the reply that goes somewhere other than the shop's own sites, empty when there is none
def unknown_link(reply: str) -> str:
    for link in LINK.findall(reply):
        if(link_host(link) not in SHOP_LINK_HOSTS):
            return link.rstrip(LINK_END_MARKS)

    return ""



#**********FINAL CHECK**********
#the last look at a reply before it reaches a customer, nothing it stops ever goes out


#BLOCKED REASON
#why the reply can't go out, written the way the owner reads it, empty when it can
#a reply written in parts can have line breaks, so only the model's notes themselves stop it
def blocked_reason(reply: str) -> str:
    if(reasoning.has_reasoning(reply, True)):
        return "The reply had the model's own notes in it"

    address: str = unknown_address(reply)

    if(address != ""):
        return f"The reply gave an address that isn't the shop's ({address})"

    link: str = unknown_link(reply)

    if(link != ""):
        return f"The reply linked somewhere that isn't the shop's ({link})"

    return ""
