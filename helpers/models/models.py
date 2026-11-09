#IMPORTS

import json
import re

import requests

from helpers.models import chat
from helpers.models import openrouter
from helpers.models import writer
from helpers.response.reasoning import has_reasoning, cut_reasoning
from helpers.response.sanitize import sanitize_reply, sanitize_text
from helpers.state import state_form
from src.prompts.custom.extractors import commercial_wrap_extractor
from src.prompts.custom.extractors import photo_extractor
from src.prompts.custom.extractors import removal_extractor
from src.prompts.contact import contact_extractor
from src.prompts.pricing_confirm import services_extractor
from src.prompts.extractors import typed_color_extractor
from src.prompts.extractors import vehicle_extractor
from src.prompts.extractors import want_extractor
from src.prompts.followup import event_extractor


#GLOBALS

DECISIONS_URL: str = "https://openrouter.ai/api/alpha/decisions"

#the latest alias always points at the newest jev, so upgrades show up on their own
ROUTER_MODEL: str = "~typesafe/jev-latest"

#seconds a decisions request waits before it times out and core runs the whole chain again
DECISIONS_TIMEOUT: int = 10

#flashx writes every reply but the service pricing one, at the effort its branch sets
GENERATOR_MODEL: str = "z-ai/glm-5.3-flashx"

#a reply can think for ages and burn thousands of tokens first, so both limits leave room
GENERATOR_MAX_TOKENS: int = 32000

GENERATOR_TIMEOUT: int = 300

#kimi writes the service pricing reply and its rewrite, the ones where the money talks
S_P_MODEL: str = "moonshotai/kimi-k3"

#a reply with the models own notes in it gets asked for again, up to this many tries in all
LEAK_MAX_ATTEMPTS: int = 3

VEHICLE_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

WANT_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

TYPED_COLOR_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

COMMERCIAL_WRAP_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

MEDIA_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

REMOVAL_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

SERVICE_PRICING_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

CONTACT_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

EVENT_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

#flashx pulls every detail out of there message at high
EXTRACTOR_EFFORT: str = "high"

#a name, an at sign and a domain with a dot, so a quote hugging it never tags along
EMAIL_PATTERN: str = r"[A-Za-z0-9][A-Za-z0-9._%+'-]*@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"


#OPENROUTER REQUESTS

#asks jev every question at once about the state, answers come back by name
def decision_answers(questions: dict, state: dict | str) -> dict:
    payload: dict = {"model": ROUTER_MODEL, "state": state, "questions": questions}

    response = requests.post(DECISIONS_URL, headers=openrouter.openrouter_headers(), json=payload, timeout=DECISIONS_TIMEOUT)

    response.raise_for_status()

    result: dict = response.json()

    return result["answers"]

#one question asked on its own, and jevs answer to it
def decision_answer(name: str, question: dict, state: dict | str) -> dict:
    answers: dict = decision_answers({name: question}, state)

    return answers[name]

#everything a chat request sends but the model, provider and effort, each model sets its own
def chat_body(system_prompt: str, user_text: str) -> dict:
    #the system prompt is cached, so every request with the same prompt reuses it
    system_block: dict = {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}

    system_message: dict = {"role": "system", "content": [system_block]}

    user_message: dict = {"role": "user", "content": user_text}

    return {"messages": [system_message, user_message], "max_tokens": GENERATOR_MAX_TOKENS}


#CLASSIFIERS

#the codes over the threshold, and every questions chance of a yes
def classifier(classifier_questions: dict, state: dict, confidence_threshold: float) -> tuple[list[str], dict[str, float]]:
    answers: dict = decision_answers(classifier_questions, state)

    codes: list[str] = []

    probabilities: dict[str, float] = {}

    for question_name in classifier_questions:
        probability_yes: float = answers[question_name]["noul"]

        probabilities[question_name] = probability_yes

        if(probability_yes > confidence_threshold):
            codes.append(question_name)

    return (codes, probabilities)

#each code with its chance of a yes next to it, the way the terminal shows a decision
def codes_with_probabilities(codes: list[str], probabilities: dict[str, float]) -> list[str]:
    labels: list[str] = []

    for code in codes:
        labels.append(f"{code}({probabilities[code]:.2f})")

    return labels

#details keyed by code so a branch knows which services came up, codes with no details get skipped
def analyzed_details(codes: list[str], detail_dict: dict, general_code: str | None) -> dict[str, dict]:
    details: dict[str, dict] = {}

    for code in codes:
        #the general code gets every detail, its the catch all
        if(code == general_code):
            details[code] = detail_dict
        elif(code in detail_dict):
            details[code] = detail_dict[code]

    return details

#asks a branchs questions about there message, hands back details for every service its about
def analyzer(analyzer_questions: dict, state: dict, detail_dict: dict, general_code: str | None, confidence_threshold: float) -> dict[str, dict]:
    classified: tuple[list[str], dict[str, float]] = classifier(analyzer_questions, state, confidence_threshold)

    details_list: list[str] = classified[0]

    probabilities: dict[str, float] = classified[1]

    #nothing picked up means a general message, so a branch with a general code never comes up empty
    if(details_list == [] and general_code is not None):
        details_list = [general_code]

    print(f"ANALYZER: {codes_with_probabilities(details_list, probabilities)}")

    return analyzed_details(details_list, detail_dict, general_code)


#REPLY WRITING

#one try down the lineup, with the junk the model leaks after its reply cut off
def generator_reply(label: str, lineup: list[tuple[str, str]], body: dict) -> str:
    #a typed out backslash n becomes a real line break, before the junk cut eats the backslash
    reply: str = chat.lineup_text(label, lineup, body, GENERATOR_TIMEOUT).replace("\\n", "\n")

    #models sometimes leak gibberish after the reply, it gets cut before anyone sees it
    return sanitize_reply(reply)

#the reply the lineup wrote, asked for again while the models own notes leak into it
def written_reply(label: str, lineup: list[tuple[str, str]], system_prompt: str, user_text: str, line_breaks: bool) -> str:
    #the generator gets noted, so an upvote in the dashboard knows whose examples to add it to
    writer.note_generator(system_prompt, user_text)

    body: dict = chat_body(system_prompt, user_text)

    reply: str = generator_reply(label, lineup, body)

    attempt: int = 1

    #a reply wiht the models own notes in it gets asked for again, the customer only gets the reply
    while(has_reasoning(reply, line_breaks) and attempt < LEAK_MAX_ATTEMPTS):
        print(f"{label} REASONING LEAK: {reply}")

        reply = generator_reply(label, lineup, body)

        attempt += 1

    #every try leaked, so only the part after the notes goes out, or nothing if it can't be found
    if(has_reasoning(reply, line_breaks)):
        print(f"{label} REASONING LEAK: {reply}")

        reply = cut_reasoning(reply, line_breaks)

    print(f"{label}: {reply}")

    return reply

#line_breaks is only on for replies written in parts, anywhere else a line break means notes leaked
def generator(label: str, system_prompt: str, user_text: str, max_tokens: int, effort: str, line_breaks: bool) -> str:
    #flashx writes it at the branchs effort, kimi steps in when flashx errors or comes back empty
    lineup: list[tuple[str, str]] = [(GENERATOR_MODEL, effort), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

    return written_reply(label, lineup, system_prompt, user_text, line_breaks)

#the service pricing reply and its rewrite, kimi k3 leads and the backup kimi steps in if it flops
def s_p_generator(label: str, system_prompt: str, user_text: str, max_tokens: int, effort: str, line_breaks: bool) -> str:
    lineup: list[tuple[str, str]] = [(S_P_MODEL, effort), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

    return written_reply(label, lineup, system_prompt, user_text, line_breaks)


#REPLY CHECKS

#true when the reply sticks close enough to the branchs details to go out
def checker(checker_instruction: str, state: dict, details_label: str, details: str, confidence_threshold: float) -> bool:
    checker_question: dict = {"type": "noul", "instructions": checker_instruction}

    state_as_text: str = state_form.state_to_text(state)

    #the details go in front under there branch label, so the reply gets judged against them
    check_state: str = f"{details_label}:\n{details}\nSTATE: {state_as_text}"

    probability_yes: float = decision_answer("checker_A", checker_question, check_state)["noul"]

    check_result: bool = probability_yes > confidence_threshold

    print(f"CHECKER: {check_result}({probability_yes:.2f})")

    return check_result


#EXTRACTORS

#every extractor sends the same request, only the label, the model, the prompt and the text change
def extract(label: str, model: str, system_prompt: str, user_text: str) -> str:
    #the extractors model reads it, the backup kimi steps in when it errors or comes back empty
    lineup: list[tuple[str, str]] = [(model, EXTRACTOR_EFFORT), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

    #junk leaked after the format would end up inside the last value, so it gets cut
    extractor_output: str = sanitize_text(chat.lineup_text(label, lineup, chat_body(system_prompt, user_text), GENERATOR_TIMEOUT))

    print(f"{label}: {extractor_output}")

    return extractor_output

#there make, model, current color and other vehicles, out of their message, media and the shops ask
def extract_vehicle(user_text: str, user_media: dict, shop_last_reply: str) -> str:
    #no text and no media means nothing to read, the model would only ask for some anyway
    if(user_text.strip() == "" and user_media == {}):
        return "MAKE: | MODEL: | COLOR: | OTHER_MODELS:"

    media_as_text: str = json.dumps(user_media, ensure_ascii=False, separators=(",", ":"))

    #the shops last reply goes in too, so a bare year and model reads as the answer to it
    vehicle_text: str = f"SHOP_LAST_REPLY: {shop_last_reply}\nUSER_MESSAGE: {user_text}\nUSER_MEDIA: {media_as_text}"

    system_prompt: str = vehicle_extractor.prompt()

    return extract("VEHICLE EXTRACTOR", VEHICLE_EXTRACTOR_MODEL, system_prompt, vehicle_text)

#the exact color or finish they want, out of there message and the pics or links they sent
def extract_want(user_text: str, user_media: dict, shop_last_reply: str) -> str:
    media_as_text: str = json.dumps(user_media, ensure_ascii=False, separators=(",", ":"))

    #the shops last reply goes in too, so a pic sent right after it asked reads as the exact color
    want_text: str = f"SHOP_LAST_REPLY: {shop_last_reply}\nUSER_MESSAGE: {user_text}\nUSER_MEDIA: {media_as_text}"

    system_prompt: str = want_extractor.prompt()

    return extract("WANT EXTRACTOR", WANT_EXTRACTOR_MODEL, system_prompt, want_text)

#the whole conversation goes in, they may have typed their current color way before the pic ask
def extract_typed_color(conversation_text: str) -> str:
    system_prompt: str = typed_color_extractor.prompt()

    return extract("TYPED COLOR EXTRACTOR", TYPED_COLOR_EXTRACTOR_MODEL, system_prompt, f"STATE: {conversation_text}")

#a commercial wraps type, vehicle count, makes and models, and whether they have logo files
def extract_commercial_wrap(user_text: str) -> str:
    system_prompt: str = commercial_wrap_extractor.prompt()

    return extract("COMMERCIAL WRAP EXTRACTOR", COMMERCIAL_WRAP_EXTRACTOR_MODEL, system_prompt, user_text)

#whether a custom jobs photo came in, out of their message
def extract_photo(user_text: str) -> str:
    system_prompt: str = photo_extractor.prompt()

    return extract("MEDIA EXTRACTOR", MEDIA_EXTRACTOR_MODEL, system_prompt, user_text)

#an old wrap or film coming off, whether its photo came in and how long its been on
def extract_removal(user_text: str) -> str:
    system_prompt: str = removal_extractor.prompt()

    return extract("REMOVAL EXTRACTOR", REMOVAL_EXTRACTOR_MODEL, system_prompt, user_text)

#every service they want with the price the shop quoted, as service and price pairs on one line
def extract_services(user_text: str) -> str:
    system_prompt: str = services_extractor.prompt()

    return extract("SERVICE PRICING EXTRACTOR", SERVICE_PRICING_EXTRACTOR_MODEL, system_prompt, user_text)

#there name, number and email, out of there message and what the shop last asked
def extract_contact(user_text: str, shop_last_reply: str) -> str:
    #the shops last reply goes in too, so a bare name or number answering it reads as theirs
    contact_text: str = f"SHOP_LAST_REPLY: {shop_last_reply}\nUSER_MESSAGE: {user_text}"

    system_prompt: str = contact_extractor.prompt()

    return extract("CONTACT EXTRACTOR", CONTACT_EXTRACTOR_MODEL, system_prompt, contact_text)

#what a quiet customer is waiting on and when it lands, out of the whole chat
def extract_event(event_text: str) -> str:
    system_prompt: str = event_extractor.prompt()

    return extract("EVENT EXTRACTOR", EVENT_EXTRACTOR_MODEL, system_prompt, event_text)


#EXTRACTED VALUES

#the value after each field name on the extractors first line, in the order the names are given
def extractor_values(extractor_output: str, field_names: list[str]) -> list[str]:
    output_lines: list[str] = extractor_output.strip().splitlines()

    #only the first line is the format, anything the model adds under it is never info
    format_line: str = output_lines[0]

    elements: list[str] = format_line.split("|")

    values: list[str] = []

    for field_name, element in zip(field_names, elements):
        label_and_value: list[str] = element.split(":", 1)

        label: str = label_and_value[0].strip().lower()

        #a reply that chats instead of giving the format gets dropped, it never gets written as info
        if(label != field_name):
            raise ValueError(f"not the {field_name} format, got {extractor_output}")

        value: str = label_and_value[1].strip()

        values.append(value)

    return values

#the price for each service on the pricing extractors line, keyed by the service
def services_pricing_values(extractor_output: str) -> dict[str, str]:
    output_lines: list[str] = extractor_output.strip().splitlines()

    #only the first line is the format, anything the model adds under it is never info
    format_line: str = output_lines[0]

    elements: list[str] = format_line.split("|")

    services_pricing: dict[str, str] = {}

    service: str = ""

    for element in elements:
        label_and_value: list[str] = element.split(":", 1)

        label: str = label_and_value[0].strip().lower()

        #a reply that talks instead of giving the format gets dropped, so it never gets used as info
        if(label != "service" and label != "price"):
            raise ValueError(f"not the service and price format, got {extractor_output}")

        value: str = label_and_value[1].strip()

        #each service comes right before its price, so the price goes under the last service read
        if(label == "service"):
            service = value
        elif(label == "price" and service != ""):
            services_pricing[service] = value

    return services_pricing

#their email exactly as typed, empty string when there isn't one
def email_value(user_text: str) -> str:
    #the email straight from their text, so the owner never gets an address a model reworded
    email_match = re.search(EMAIL_PATTERN, user_text)

    if(email_match is None):
        return ""

    return email_match.group(0)
