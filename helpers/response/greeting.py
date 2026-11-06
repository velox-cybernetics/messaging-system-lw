#**********IMPORTS**********
#the lead form reader and the sentence cleanup, to build the intro and trim what comes after it
from helpers.response import cleaners
from helpers.state import state_form



#**********GLOBALS**********
#the greetings, intro words and openers a reply gets trimmed of, and how each form service is said


#GREETING WORDS
#the ways a reply can open with a hello
GREETINGS: list[str] = ["good morning", "good afternoon", "good evening", "hello", "howdy", "hey", "hi"]


#PUNCTUATION MARKS
#the marks a greeting, an opener or a follower can end on
MARKS: list[str] = [",", ".", "!"]


#INTRODUCTION WORDS
#words only the model's own intro uses, a clause with one of them in it comes off after the set intro
INTRODUCTION_WORDS: list[str] = ["hazel", "lone wraps", "form", "forms", "quote request", "reaching out", "reached out"]


#OPENER WORDS
#the set intro already takes them in, so the answer right after it starts with what it says, never one of these
OPENERS: list[str] = ["for sure", "sounds good", "sweet", "perfect", "awesome", "ooh love that", "ooh", "yess", "yeah", "yep"]

#what an opener can carry with it, "For sure, we can do that, a wrap..." starts right at the wrap
OPENER_FOLLOWERS: list[str] = ["we can do that", "so"]


#FORM SERVICES
#how each service the meta form offers gets said in the intro
FORM_SERVICE_PHRASES: dict[str, str] = {"vinyl wrap": "a vinyl wrap", "commercial wrap": "a commercial wrap", "window tint": "window tint", "paint protection film": "paint protection film"}



#**********GREETING CUT**********
#takes the hello off the front of a reply mid conversation, since hazel only greets where a conversation opens


#FIND GREETING
#the greeting the reply opens with as it's written, a stretched one like "heyy" included, empty when it opens with none
def find_greeting(reply: str) -> str:
    lower_reply: str = reply.lower()

    for greeting in GREETINGS:
        if(not lower_reply.startswith(greeting)):
            continue

        end: int = len(greeting)

        #hazel's "Heyy" stretches the last letter, and it's still the hey greeting
        while(lower_reply[end:end + 1] == greeting[-1]):
            end += 1

        character_after: str = lower_reply[end:end + 1]

        #"hi" at the start of "highway" is not a greeting
        if(not character_after.isalnum()):
            return lower_reply[:end]

    return ""


#REMOVE GREETING
#the reply with its opening greeting cut, and the name or "there" that came with it
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

    #"Hey Kade, " and "Hi there! " lose the name or "there" too
    if(len(words_before_mark) <= 2):
        rest = rest[first_mark:]

    elif(words_before_mark[0].lower() == "there"):
        rest = rest.lstrip()[len("there"):]

    return cleaners.sentence_start(rest)



#**********INTRO CUT**********
#takes off the model's own intro and opener words, so the answer starts right with what it says


#FIRST CLAUSE
#the text up to its first mark, all of it when it has none
def first_clause(text: str) -> str:
    clause: str = ""

    for character in text:
        if(character in ",.!?"):
            return clause

        clause = f"{clause}{character}"

    return clause


#IS INTRODUCTION
#whether a clause is the model introducing itself or the form, like "this is Hazel with the Lone Wraps team"
def is_introduction(clause: str) -> bool:
    words: str = ""

    #every mark turns into a space, so "Hazel's" still reads as hazel and "platform" never reads as form
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


#REMOVE INTRODUCTION
#the reply with every intro clause at its front cut off
def remove_introduction(reply: str) -> str:
    rest: str = reply

    clause: str = first_clause(rest)

    #"this is Hazel with the Lone Wraps team, saw your quote request on the 570S." comes off one clause at a time
    while(is_introduction(clause)):
        rest = rest[len(clause):]

        rest = rest.lstrip(" \n,.!?")

        clause = first_clause(rest)

    return cleaners.sentence_start(rest)


#FOLLOWER START
#the length of the follower the text starts with, 0 when it starts with none
def follower_start(text: str) -> int:
    for follower in OPENER_FOLLOWERS:
        after: str = text[len(follower):len(follower) + 1]

        #"so a wrap" loses the so, "we can do that, a wrap" loses the whole clause, "sometimes" never loses its so
        if(text.lower().startswith(follower) and (after in MARKS or (follower == "so" and after == " "))):
            return len(follower)

    return 0


#REMOVE OPENER
#the reply with the opener at its front cut off, and the followers that came with it
def remove_opener(reply: str) -> str:
    rest: str = reply.strip()

    for opener in OPENERS:
        if(not rest.lower().startswith(opener)):
            continue

        next_character: str = rest[len(opener):len(opener) + 1]

        after_opener: str = rest[len(opener):].lstrip()

        #a mark right after it, or no mark and a follower, so "Perfectly" or "Sweet ride" never lose a word
        if(next_character not in MARKS and not (next_character == " " and follower_start(after_opener) > 0)):
            continue

        rest = after_opener.lstrip(" ,.!")

        follower_length: int = follower_start(rest)

        while(follower_length > 0):
            rest = rest[follower_length:].lstrip(" ,.!")

            follower_length = follower_start(rest)

        return cleaners.sentence_start(rest)

    return reply



#**********LEAD INTRO**********
#builds the set intro for a form lead, with their first name, the service and their vehicle


#REAL NAME
#whether a word off the public form looks like a real first name
def real_name(name: str) -> bool:
    if(name == "" or len(name) > 20):
        return False

    if(not name[0].isalpha() or not name[-1].isalpha()):
        return False

    #letters only, with an inner ' or - like O'Brien or Mary-Jane
    for character in name:
        if(not character.isalpha() and character not in "'’-"):
            return False

    return True


#FIRST NAME
#the lead's first name off the form, written the way a name is, empty when there's no real one
def form_first_name(form: dict[str, str]) -> str:
    full_name: str = form["name"]

    #the website form splits the name in two
    if(full_name == ""):
        full_name = form["first_name"]

    names: list[str] = full_name.split()

    if(len(names) == 0):
        return ""

    first_name: str = names[0]

    #the form is public, so a name that is not one stays out of the shop's text
    if(not real_name(first_name)):
        return ""

    #"kade" and "KADE" are written the way a name is
    if(first_name.islower() or first_name.isupper()):
        first_name = first_name.capitalize()

    return first_name


#SERVICE PHRASE
#how a service off the meta form gets said in the intro, empty for one with no phrase
def service_phrase(service: str) -> str:
    service_key: str = service.lower().strip()

    #"Vinyl Wraps" on the form is the vinyl wrap phrase
    service_key = service_key.removesuffix("s")

    if(service_key in FORM_SERVICE_PHRASES):
        return FORM_SERVICE_PHRASES[service_key]

    #a service the intro has no phrase for stays out of it, so it never reads as a quote request for a quote
    return ""


#VEHICLE NAMES
#the models as the intro says them, "the Tacoma" for one and "the Tacoma and Telluride" for two, empty for none
def vehicle_names(vehicle_models: list[str]) -> str:
    if(len(vehicle_models) == 0):
        return ""

    if(len(vehicle_models) == 1):
        return f"the {vehicle_models[0]}"

    return f"the {', '.join(vehicle_models[:-1])} and {vehicle_models[-1]}"


#FORM INTRO
#the set intro to a form lead, with their first name, the service they picked and every vehicle on the form
def form_intro(current_message_batch: list, channel: str, vehicle_models: list[str]) -> str:
    form: dict[str, str] = state_form.form_fields(current_message_batch)

    first_name: str = form_first_name(form)

    #hazel's heyy, with their name when the form has a real one
    greeting: str = "Heyy"

    if(first_name != ""):
        greeting = f"Heyy {first_name},"

    request: str = "saw your quote request"

    #the website form names no service, so only the meta intro speaks to the service they picked
    if(channel == "meta-form"):
        service: str = service_phrase(form["service"])

        if(service != ""):
            request = f"{request} for {service}"

    #the models the vehicle extractor read, so "mclaren 570s 2021" goes out as the 570S, never their raw text, and a form with two vehicles names both
    vehicles: str = vehicle_names(vehicle_models)

    if(vehicles != ""):
        request = f"{request} on {vehicles}"

    return f"{greeting} this is Hazel with the Lone Wraps team, {request}."



#**********FIRST REPLY**********
#cuts the greeting off every reply mid conversation, puts the set intro on the first reply to a form lead, and keeps hazel's heyy where a conversation opens


#REPLIED BEFORE
#whether the shop already sent a reply in this conversation, so only its first reply gets the intro
def replied_before(message_history: dict) -> bool:
    for key, value in message_history.items():
        if(key.startswith("system_response") and value != ""):
            return True

        #a summary means older replies were folded into it
        if(isinstance(value, dict) and "conversation_summary" in value):
            return True

    return False


#FIX GREETING
#the reply with its greeting cut mid conversation, on the first reply to a form lead the set intro in front of it, and on a follow up or the first reply to someone who texted first the greeting left on
def fix_greeting(reply: str, channel: str, message_history: dict, current_message_batch: list, vehicle_models: list[str], follow_up: bool = False) -> str:
    first_reply: bool = not replied_before(message_history)

    #hazel's heyy can open the first reply to someone who texted first, and a follow up after the conversation went quiet
    if(follow_up or (first_reply and channel not in state_form.FORM_CHANNELS)):
        return reply

    answer: str = remove_greeting(reply)

    if(answer != reply):
        print(f"GREETING CUT: {reply}")

    #only the first reply to a form lead gets the set intro, and it goes out even when the answer is empty
    if(first_reply):
        intro: str = form_intro(current_message_batch, channel, vehicle_models)

        #the intro takes them in, so the answer after it starts right with what it says
        answer = remove_opener(remove_introduction(answer))

        print(f"FORM INTRO: {intro}")

        return f"{intro} {answer}".strip()

    return answer
