#IMPORTS

from helpers.response import cleaners
from helpers.state import state_form


#GLOBALS

#the ways a reply can open with a hello
GREETINGS: list[str] = ["good morning", "good afternoon", "good evening", "hello", "howdy", "hey", "hi"]

#the marks a greeting, an opener or a follower can end on
MARKS: list[str] = [",", ".", "!"]

#words only the models own intro uses, a clause with one comes off after the set intro
INTRODUCTION_WORDS: list[str] = ["hazel", "lone wraps", "form", "forms", "quote request", "reaching out", "reached out"]

#the set intro already greets them, so the answer after it skips straight to the point
OPENERS: list[str] = ["for sure", "sounds good", "sweet", "perfect", "awesome", "yeah", "yep"]

#what an opener can drag along with it, so the answer starts right at the actual thing
OPENER_FOLLOWERS: list[str] = ["we can do that", "so"]

#how each service the meta form offers gets said in the intro
FORM_SERVICE_PHRASES: dict[str, str] = {"vinyl wrap": "a vinyl wrap", "commercial wrap": "a commercial wrap", "window tint": "window tint", "paint protection film": "paint protection film"}


#GREETING CUT

#the greeting the reply opens with as written, stretched ones like heyy included, empty when none
def find_greeting(reply: str) -> str:
    lower_reply: str = reply.lower()

    for greeting in GREETINGS:
        if(not lower_reply.startswith(greeting)):
            continue

        end: int = len(greeting)

        #a stretched heyy is still the hey greeting
        while(lower_reply[end:end + 1] == greeting[-1]):
            end += 1

        character_after: str = lower_reply[end:end + 1]

        #hi at the start of highway is not a greeting, no matter how friendly the road
        if(not character_after.isalnum()):
            return lower_reply[:end]

    return ""

#the reply with its opening greeting cut, along with the name or there that came with it
def remove_greeting(reply: str) -> str:
    greeting: str = find_greeting(reply)

    if(greeting == ""):
        return reply

    rest: str = reply[len(greeting):]

    first_mark: int = len(rest)

    for mark in MARKS:
        position: int = rest.find(mark)

        if(position != -1 and position < first_mark):
            first_mark = position

    words_before_mark: list[str] = rest[:first_mark].split()

    #hey kade or hi their lose the name or the their too
    if(len(words_before_mark) <= 2):
        rest = rest[first_mark:]
    elif(words_before_mark[0].lower() == "there"):
        rest = rest.lstrip()[len("there"):]

    return cleaners.sentence_start(rest)


#INTRO CUT

#the text up to its first mark, all of it when it has none
def first_clause(text: str) -> str:
    clause: str = ""

    for character in text:
        if(character in ",.!?"):
            return clause

        clause = f"{clause}{character}"

    return clause

#whether a clause is the model introducing itself or the form, like this is hazel with the team
def is_introduction(clause: str) -> bool:
    words: str = ""

    #every mark turns into a space, so hazels still reads as hazel and platform never reads as form
    for character in clause.lower():
        if(character.isalnum()):
            words = f"{words}{character}"
        else:
            words = f"{words} "

    padded_words: str = f" {words} "

    for introduction_word in INTRODUCTION_WORDS:
        if(f" {introduction_word} " in padded_words):
            return True

    return False

#the reply with every intro clause at its front cut off
def remove_introduction(reply: str) -> str:
    rest: str = reply

    clause: str = first_clause(rest)

    #the models own intro comes off one clause at a time until something real shows up
    while(is_introduction(clause)):
        rest = rest[len(clause):]

        rest = rest.lstrip(" \n,.!?")

        clause = first_clause(rest)

    return cleaners.sentence_start(rest)

#the length of the follower the text starts with, 0 when it starts with none
def follower_start(text: str) -> int:
    for follower in OPENER_FOLLOWERS:
        after: str = text[len(follower):len(follower) + 1]

        #a follower needs a mark after it, only so can take a space, and sometimes keeps its so
        if(text.lower().startswith(follower) and (after in MARKS or (follower == "so" and after == " "))):
            return len(follower)

    return 0

#the reply with the opener at its front cut off, and the followers that came with it
def remove_opener(reply: str) -> str:
    rest: str = reply.strip()

    for opener in OPENERS:
        if(not rest.lower().startswith(opener)):
            continue

        next_character: str = rest[len(opener):len(opener) + 1]

        after_opener: str = rest[len(opener):].lstrip()

        #a mark right after it, or a space and a follower, so perfectly or sweet ride stay whole
        if(next_character not in MARKS and not (next_character == " " and follower_start(after_opener) > 0)):
            continue

        rest = after_opener.lstrip(" ,.!")

        follower_length: int = follower_start(rest)

        while(follower_length > 0):
            rest = rest[follower_length:].lstrip(" ,.!")

            follower_length = follower_start(rest)

        return cleaners.sentence_start(rest)

    return reply


#LEAD INTRO

#whether a word off the public form looks like a real first name
def real_name(name: str) -> bool:
    if(name == "" or len(name) > 20):
        return False

    if(not name[0].isalpha() or not name[-1].isalpha()):
        return False

    #letters only, an inner apostrophe or dash is fine for the o'briens of the world
    for character in name:
        if(not character.isalpha() and character not in "'’-"):
            return False

    return True

#the leads first name off the form, written the way a name is, empty when theres no real one
def form_first_name(form: dict[str, str]) -> str:
    full_name: str = form["name"]

    #the website form splits the name in two
    if(full_name == ""):
        full_name = form["first_name"]

    names: list[str] = full_name.split()

    if(len(names) == 0):
        return ""

    first_name: str = names[0]

    #the form is public, so a name that is not one stays out of the shops text
    if(not real_name(first_name)):
        return ""

    #all lowercase or all caps names get written the way a name is
    if(first_name.islower() or first_name.isupper()):
        first_name = first_name.capitalize()

    return first_name

#how a service off the meta form gets said in the intro, empty for one with no phrase
def service_phrase(service: str) -> str:
    service_key: str = service.lower().strip()

    #vinyl wraps on the form is the vinyl wrap phrase
    service_key = service_key.removesuffix("s")

    if(service_key in FORM_SERVICE_PHRASES):
        return FORM_SERVICE_PHRASES[service_key]

    #no phrase means it stays out, so it never reads as a quote request for a quote
    return ""

#the models as the intro says them, the tacoma for one, the tacoma and telluride for two
def vehicle_names(vehicle_models: list[str]) -> str:
    if(len(vehicle_models) == 0):
        return ""

    if(len(vehicle_models) == 1):
        return f"the {vehicle_models[0]}"

    return f"the {', '.join(vehicle_models[:-1])} and {vehicle_models[-1]}"

#the set intro to a form lead, with their first name, the service and every vehicle on the form
def form_intro(current_message_batch: list, channel: str, vehicle_models: list[str]) -> str:
    form: dict[str, str] = state_form.form_fields(current_message_batch)

    first_name: str = form_first_name(form)

    #a plain hey, with their name when the form has a real one
    greeting: str = "Hey"

    if(first_name != ""):
        greeting = f"Hey {first_name},"

    request: str = "saw your quote request"

    #the website form names no service, so only the meta intro speaks to the service they picked
    if(channel == "meta-form"):
        service: str = service_phrase(form["service"])

        if(service != ""):
            request = f"{request} for {service}"

    #models the vehicle extractor read, never there raw text, and two vehicles get named both
    vehicles: str = vehicle_names(vehicle_models)

    if(vehicles != ""):
        request = f"{request} on {vehicles}"

    return f"{greeting} this is Hazel with the Lone Wraps team, {request}."


#FIRST REPLY

#whether the shop already sent a reply in this conversation, so only its first reply gets the intro
def replied_before(message_history: dict) -> bool:
    for key, value in message_history.items():
        if(key.startswith("system_response") and value != ""):
            return True

        #a summary means older replies were folded into it
        if(isinstance(value, dict) and "conversation_summary" in value):
            return True

    return False

#cuts the greeting mid conversation, and puts the set intro on the first reply to a form lead
def fix_greeting(reply: str, channel: str, message_history: dict, current_message_batch: list, vehicle_models: list[str], follow_up: bool = False) -> str:
    first_reply: bool = not replied_before(message_history)

    #a hey can open a first reply to someone who texted first, or a follow up after things went quiet
    if(follow_up or (first_reply and channel not in state_form.FORM_CHANNELS)):
        return reply

    answer: str = remove_greeting(reply)

    if(answer != reply):
        print(f"GREETING CUT: {reply}")

    #only the first reply to a form lead gets the intro, even when the answer is empty
    if(first_reply):
        intro: str = form_intro(current_message_batch, channel, vehicle_models)

        #the intro takes them in, so the answer after it starts right with what it says
        answer = remove_opener(remove_introduction(answer))

        print(f"FORM INTRO: {intro}")

        return f"{intro} {answer}".strip()

    return answer
