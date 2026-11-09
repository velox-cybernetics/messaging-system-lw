#IMPORTS

import json
import re

from helpers.response import reasoning
from src import branches


#ADDRESSES

#street name endings, minus drive, road and trail since those are usually trims like Off Road
STREET_TYPES: str = r"St|Street|Ave|Avenue|Blvd|Boulevard|Ln|Lane|Way|Hwy|Highway|Pkwy|Parkway|Ct|Court|Cir|Circle|Pl|Place|Ter|Terrace|Loop"

#a house number, up to four capitalized words and the street type, like 123 Main St
STREET_ADDRESS = re.compile(rf"\b\d{{2,6}}(?:\s+[A-Z0-9][\w'.-]*){{0,4}}?\s+(?:{STREET_TYPES})\b")

DIRECTIONS: str = r"N|S|E|W|North|South|East|West"

#utah grid addresses like 105 S 700 E, no street type needed because utah is special
GRID_ADDRESS = re.compile(rf"\b\d{{1,5}}\s+(?:{DIRECTIONS})\.?\s+\d{{1,5}}\s+(?:{DIRECTIONS})\b")

#spelled out reads the same as short, so 105 South 700 East is still the shop
SHORT_WORDS: dict[str, str] = {"north": "n", "south": "s", "east": "e", "west": "w", "street": "st", "avenue": "ave", "boulevard": "blvd", "lane": "ln", "highway": "hwy", "parkway": "pkwy", "court": "ct", "circle": "cir", "place": "pl", "terrace": "ter"}

#an address as lowercase short words with the marks off, padded with a space on each end
def address_words(text: str) -> str:
    words: list[str] = []

    for word in re.sub(r"[.,#]", " ", text.lower()).split():
        words.append(SHORT_WORDS.get(word, word))

    return f" {' '.join(words)} "

#every address in the business details, same file the replies use so they never drift apart
def shop_addresses() -> list[str]:
    addresses: list[str] = []

    for details in branches.BUSINESS_DETAILS.values():
        for address in details.get("Shop Address", []):
            addresses.append(address_words(address))

    return addresses

SHOP_ADDRESSES: list[str] = shop_addresses()

#true when the address is the shops or a piece of it, like the address without the unit
def is_shop_address(address: str) -> bool:
    for shop_address in SHOP_ADDRESSES:
        if(address_words(address) in shop_address):
            return True

    return False

#the first address in the reply that isn't the shops, empty when there is none
def unknown_address(reply: str) -> str:
    for pattern in [STREET_ADDRESS, GRID_ADDRESS]:
        for found in pattern.finditer(reply):
            if(not is_shop_address(found.group())):
                return found.group()

    return ""


#LINKS

#endings a phone links even without https in front, everyday words like in or to are left out
LINK_ENDINGS: str = r"com|net|org|info|biz|xyz|io|co|ly|us|me|tv|ai|gg|app|dev|link|site|online|shop|store|live|page|club"

#full links, www ones or bare site dot com ones, emails and handles are never links
LINK = re.compile(rf"(?<![\w@.-])(?:(?:https?://|www\.)[^\s<>\"']+|(?:[a-z0-9-]+\.)+(?:{LINK_ENDINGS})\b[^\s<>\"']*)", re.IGNORECASE)

#a mark right after a link ends the sentence, its never part of the link
LINK_END_MARKS: str = ".,;:!?)"

#the bare site a link goes to, lowercase with no https, no www and nothing after it
def link_host(link: str) -> str:
    host: str = link.lower().rstrip(LINK_END_MARKS)

    host = host.split("://", 1)[-1]

    host = re.split(r"[/?#:]", host, maxsplit=1)[0]

    return host.removeprefix("www.")

#every site the shops details link to, same files the replies use so they never drift apart
def shop_link_hosts() -> set[str]:
    hosts: set[str] = set()

    for details in [branches.BUSINESS_DETAILS, branches.PRICING_DETAILS, branches.CUSTOM_DETAILS]:
        for link in LINK.findall(json.dumps(details)):
            hosts.add(link_host(link))

    return hosts

SHOP_LINK_HOSTS: set[str] = shop_link_hosts()

#the first link in the reply that isn't one of the shops sites, empty when there is none
def unknown_link(reply: str) -> str:
    for link in LINK.findall(reply):
        if(link_host(link) not in SHOP_LINK_HOSTS):
            return link.rstrip(LINK_END_MARKS)

    return ""


#FINAL CHECK

#why the reply can't go out in the owners words, line breaks are fine since replies come in parts
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
