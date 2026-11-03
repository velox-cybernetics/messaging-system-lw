#**********IMPORTS**********
#python's json and patterns, web requests, the model lineups, the reply cleaners, every extractor's instructions and the leak question
import json
import re

import requests

from helpers.models import chat
from helpers.models import openrouter
from helpers.response.reasoning import has_reasoning, cut_reasoning
from helpers.response.sanitize import sanitize_reply, sanitize_text
from helpers.state import state_form
from src.prompts import shared
from src.prompts.custom.extractors import commercial_wrap_extractor
from src.prompts.custom.extractors import photo_extractor
from src.prompts.custom.extractors import removal_extractor
from src.prompts.contact import contact_extractor
from src.prompts.pricing_confirm import services_extractor
from src.prompts.extractors import typed_color_extractor
from src.prompts.extractors import vehicle_extractor
from src.prompts.extractors import want_extractor



#**********GLOBALS**********
#which model does which job, how long each may take, and what an email is


#DECISIONS MODEL
DECISIONS_URL: str = "https://openrouter.ai/api/alpha/decisions"

#the ~ alias always resolves to the newest jev release, so a new version gets picked up without a change here
ROUTER_MODEL: str = "~typesafe/jev-latest"

#seconds a decisions request waits before it times out and core runs the whole chain again
DECISIONS_TIMEOUT: int = 10


#GENERATOR MODEL
#flashx writes every reply but the service pricing one, at the effort its branch sets
GENERATOR_MODEL: str = "z-ai/glm-5.3-flashx"

#a reply can think for a while and spend thousands of tokens before it writes, so both limits leave room
GENERATOR_MAX_TOKENS: int = 32000

GENERATOR_TIMEOUT: int = 300


#S_P MODEL
#kimi writes the service pricing reply and its rewrite, the replies the most rides on, at the effort the pricing branch sets
S_P_MODEL: str = "moonshotai/kimi-k3"


#LEAK ATTEMPTS
#a reply with the model's own notes in it gets asked for again, up to this many tries in all
LEAK_MAX_ATTEMPTS: int = 3


#EXTRACTOR MODELS
VEHICLE_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

WANT_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

TYPED_COLOR_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

COMMERCIAL_WRAP_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

MEDIA_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

REMOVAL_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

SERVICE_PRICING_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

CONTACT_EXTRACTOR_MODEL: str = "z-ai/glm-5.3-flashx"

#flashx pulls every detail out of their message at high
EXTRACTOR_EFFORT: str = "high"


#EMAIL PATTERN
#a name starting with a letter or number, an @ and a domain with a dot in it, so a quote around it never comes along
EMAIL_PATTERN: str = r"[A-Za-z0-9][A-Za-z0-9._%+'-]*@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"



#**********OPENROUTER REQUESTS**********
#builds and sends the requests to openrouter and hands back the plain answers


#DECISION ANSWERS
#asks jev every question at once about the state, and hands back its answer to each by name
def decision_answers(questions: dict, state: dict | str) -> dict:
    payload: dict = {"model": ROUTER_MODEL, "state": state, "questions": questions}

    response: requests.Response = requests.post(DECISIONS_URL, headers=openrouter.openrouter_headers(), json=payload, timeout=DECISIONS_TIMEOUT)

    response.raise_for_status()

    result: dict = response.json()

    return result["answers"]


#DECISION ANSWER
#one question asked on its own, and jev's answer to it
def decision_answer(name: str, question: dict, state: dict | str) -> dict:
    answers: dict = decision_answers({name: question}, state)

    return answers[name]


#CHAT BODY
#everything a chat request sends but the model, its provider and its effort, which each model in a lineup sets for itself
def chat_body(system_prompt: str, user_text: str) -> dict:
    #the system prompt is cached, so every request with the same prompt reuses it
    system_block: dict = {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}

    system_message: dict = {"role": "system", "content": [system_block]}

    user_message: dict = {"role": "user", "content": user_text}

    return {"messages": [system_message, user_message], "max_tokens": GENERATOR_MAX_TOKENS}



#**********CLASSIFIERS**********
#asks yes or no questions about their message to find out what it's about


#CLASSIFIER
#the codes over the threshold, and every question's chance of a yes
def classifier(classifier_questions: dict, state: dict, confidence_threshold: float) -> tuple[list[str], dict[str, float]]:
    answers: dict = decision_answers(classifier_questions, state)

    #codes the message is about
    codes: list[str] = []

    probabilities: dict[str, float] = {}

    for question_name in classifier_questions:
        probability_yes: float = answers[question_name]["noul"]

        probabilities[question_name] = probability_yes

        if(probability_yes > confidence_threshold):
            codes.append(question_name)

    return (codes, probabilities)


#CODES WITH PROBABILITIES
#each code with its chance of a yes next to it, the way the terminal shows a decision
def codes_with_probabilities(codes: list[str], probabilities: dict[str, float]) -> list[str]:
    labels: list[str] = []

    for code in codes:
        labels.append(f"{code}({probabilities[code]:.2f})")

    return labels


#ANALYZED DETAILS
#details keyed by their code so a branch can tell which services came up, one with no details yet is skipped
def analyzed_details(codes: list[str], detail_dict: dict, general_code: str | None) -> dict[str, dict]:
    details: dict[str, dict] = {}

    for code in codes:
        #the general code is all of the information, every detail sub-listed within it
        if(code == general_code):
            details[code] = detail_dict

        elif(code in detail_dict):
            details[code] = detail_dict[code]

    return details


#ANALYZER
#asks a branch's questions about their message and hands back the details of every service it's about
def analyzer(analyzer_questions: dict, state: dict, detail_dict: dict, general_code: str | None, confidence_threshold: float) -> dict[str, dict]:
    classified: tuple[list[str], dict[str, float]] = classifier(analyzer_questions, state, confidence_threshold)

    details_list: list[str] = classified[0]

    probabilities: dict[str, float] = classified[1]

    #a message no question picked up is a general one, so a branch with a general code never comes back with nothing
    if(details_list == [] and general_code is not None):
        details_list = [general_code]

    print(f"ANALYZER: {codes_with_probabilities(details_list, probabilities)}")

    return analyzed_details(details_list, detail_dict, general_code)



#**********REPLY WRITING**********
#writes the shop's reply and asks again when the model's own notes leak into it


#GENERATOR REPLY
#one try down the lineup, with the junk the model leaks after its reply cut off
def generator_reply(label: str, lineup: list[tuple[str, str]], body: dict) -> str:
    #a line break the model typed out as \n is a real one, before the junk cut reads its \ as junk
    reply: str = chat.lineup_text(label, lineup, body, GENERATOR_TIMEOUT).replace("\\n", "\n")

    #the model can leak junk after its reply like "} ulaşana, so it is cut before the enforcer or the customer sees it
    return sanitize_reply(reply)


#WRITTEN REPLY
#the reply the lineup wrote, asked for again while the model's own notes leak into it
def written_reply(label: str, lineup: list[tuple[str, str]], system_prompt: str, user_text: str, line_breaks: bool) -> str:
    body: dict = chat_body(system_prompt, user_text)

    reply: str = generator_reply(label, lineup, body)

    attempt: int = 1

    #a reply with the model's own notes in it gets asked for again, so the customer only ever gets the reply
    while(has_reasoning(reply, line_breaks) and attempt < LEAK_MAX_ATTEMPTS):
        print(f"{label} REASONING LEAK: {reply}")

        reply = generator_reply(label, lineup, body)

        attempt += 1

    #every try leaked, so only the reply after the notes goes out, or nothing when it can't be pulled out
    if(has_reasoning(reply, line_breaks)):
        print(f"{label} REASONING LEAK: {reply}")

        reply = cut_reasoning(reply, line_breaks)

    print(f"{label}: {reply}")

    return reply


#GENERATOR
#line_breaks is True only for the replies written in parts, any other reply with a line break is the model's notes
def generator(label: str, system_prompt: str, user_text: str, max_tokens: int, effort: str, line_breaks: bool) -> str:
    #flashx writes it at the branch's effort and kimi k3.1 pro steps in when flashx errors or comes back empty
    lineup: list[tuple[str, str]] = [(GENERATOR_MODEL, effort), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

    return written_reply(label, lineup, system_prompt, user_text, line_breaks)


#S_P GENERATOR
#the service pricing reply and its rewrite, kimi k3 writes it at the branch's effort and kimi k3.1 pro steps in when kimi k3 errors or comes back empty
def s_p_generator(label: str, system_prompt: str, user_text: str, max_tokens: int, effort: str, line_breaks: bool) -> str:
    lineup: list[tuple[str, str]] = [(S_P_MODEL, effort), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

    return written_reply(label, lineup, system_prompt, user_text, line_breaks)



#**********REPLY CHECKS**********
#makes sure a reply sticks to the shop's details and rules before it goes out


#CHECKER
#True when the reply sticks to the branch's details closely enough to go out
def checker(checker_instruction: str, state: dict, details_label: str, details: str, confidence_threshold: float) -> bool:
    checker_question: dict = {"type": "noul", "instructions": checker_instruction}

    state_as_text: str = state_form.state_to_text(state)

    #the details go in front under their branch label (SERVICE_DETAILS, BUSINESS_DETAILS) so it's judged against them
    check_state: str = f"{details_label}:\n{details}\nSTATE: {state_as_text}"

    probability_yes: float = decision_answer("checker_A", checker_question, check_state)["noul"]

    check_result: bool = probability_yes > confidence_threshold

    print(f"CHECKER: {check_result}({probability_yes:.2f})")

    return check_result


#ENFORCER
#how likely the reply breaks a rule or has the model's own notes in it, shop_last_reply is None for a branch whose rules never check a line its last reply said going out again
def enforcer(enforce_instruction: str, state: dict, response: str, shop_last_reply: str | None) -> float:
    #the leak question rides in the same request as the branch's rules, asked on its own so notes never get lost among them
    questions: dict = {"enforce_A": {"type": "noul", "instructions": enforce_instruction}, "leak": {"type": "noul", "instructions": shared.leak_question()}}

    state_as_text: str = state_form.state_to_text(state)

    enforce_state: str = f"STATE: {state_as_text}\nSYSTEM_RESPONSE:\n{response}"

    #the shop's last reply goes in on its own, so a line from it said again is easy to spot next to the reply
    if(shop_last_reply is not None):
        enforce_state = f"STATE: {state_as_text}\nSHOP_LAST_REPLY:\n{shop_last_reply}\nSYSTEM_RESPONSE:\n{response}"

    answers: dict = decision_answers(questions, enforce_state)

    leak_probability: float = answers["leak"]["noul"]

    print(f"LEAK CHECK: {leak_probability:.2f}")

    #a reply with the model's notes in it gets written again the same as one that breaks a rule
    return max(answers["enforce_A"]["noul"], leak_probability)



#**********EXTRACTORS**********
#pulls their car, the color they want, the services and their contact info out of their message


#EXTRACTOR
#every extractor sends the same request, only the label, the model, the prompt and the text change
def extract(label: str, model: str, system_prompt: str, user_text: str) -> str:
    #the extractor's model reads it and kimi k3.1 pro steps in when that model errors or comes back empty
    lineup: list[tuple[str, str]] = [(model, EXTRACTOR_EFFORT), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

    #junk the model leaks after the format like "} would be written in as part of the last value
    extractor_output: str = sanitize_text(chat.lineup_text(label, lineup, chat_body(system_prompt, user_text), GENERATOR_TIMEOUT))

    print(f"{label}: {extractor_output}")

    return extractor_output


#VEHICLE EXTRACTOR
#their make, model and the color it is now, and the models of their other vehicles named for the work, out of their message, their media and what the shop last asked
def extract_vehicle(user_text: str, user_media: dict, shop_last_reply: str) -> str:
    #a message with no text and no media has nothing to analyze, the model would only ask for one, so nothing goes out
    if(user_text.strip() == "" and user_media == {}):
        return "MAKE: | MODEL: | COLOR: | OTHER_MODELS:"

    media_as_text: str = json.dumps(user_media, ensure_ascii=False, separators=(",", ":"))

    #the shop's last reply goes in too, so a short answer like "2020 civic" gets read as what it answers
    vehicle_text: str = f"SHOP_LAST_REPLY: {shop_last_reply}\nUSER_MESSAGE: {user_text}\nUSER_MEDIA: {media_as_text}"

    system_prompt: str = vehicle_extractor.prompt()

    return extract("VEHICLE EXTRACTOR", VEHICLE_EXTRACTOR_MODEL, system_prompt, vehicle_text)


#WANT EXTRACTOR
#the exact color or finish they want, out of their message and the pics or links they sent
def extract_want(user_text: str, user_media: dict, shop_last_reply: str) -> str:
    media_as_text: str = json.dumps(user_media, ensure_ascii=False, separators=(",", ":"))

    #the shop's last reply goes in too, so a pic or link sent right after it asked for the exact color reads as that one
    want_text: str = f"SHOP_LAST_REPLY: {shop_last_reply}\nUSER_MESSAGE: {user_text}\nUSER_MEDIA: {media_as_text}"

    system_prompt: str = want_extractor.prompt()

    return extract("WANT EXTRACTOR", WANT_EXTRACTOR_MODEL, system_prompt, want_text)


#TYPED COLOR EXTRACTOR
#the whole conversation goes in, since the color it is now they typed can be from before the shop's asks for a pic
def extract_typed_color(conversation_text: str) -> str:
    system_prompt: str = typed_color_extractor.prompt()

    return extract("TYPED COLOR EXTRACTOR", TYPED_COLOR_EXTRACTOR_MODEL, system_prompt, f"STATE: {conversation_text}")


#COMMERCIAL EXTRACTOR
#a commercial wrap's type, how many vehicles, their makes and models, and whether they have the logo files
def extract_commercial_wrap(user_text: str) -> str:
    system_prompt: str = commercial_wrap_extractor.prompt()

    return extract("COMMERCIAL WRAP EXTRACTOR", COMMERCIAL_WRAP_EXTRACTOR_MODEL, system_prompt, user_text)


#MEDIA EXTRACTOR
#whether a custom job's photo came in, out of their message
def extract_photo(user_text: str) -> str:
    system_prompt: str = photo_extractor.prompt()

    return extract("MEDIA EXTRACTOR", MEDIA_EXTRACTOR_MODEL, system_prompt, user_text)


#REMOVAL EXTRACTOR
#an old wrap or film coming off: whether its photo came in and how long it's been on
def extract_removal(user_text: str) -> str:
    system_prompt: str = removal_extractor.prompt()

    return extract("REMOVAL EXTRACTOR", REMOVAL_EXTRACTOR_MODEL, system_prompt, user_text)


#PRICING EXTRACTOR
#every service they want with the price the shop quoted for it, as service and price pairs on one line
def extract_services(user_text: str) -> str:
    system_prompt: str = services_extractor.prompt()

    return extract("SERVICE PRICING EXTRACTOR", SERVICE_PRICING_EXTRACTOR_MODEL, system_prompt, user_text)


#CONTACT EXTRACTOR
#their name, number and email, out of their message and what the shop last asked
def extract_contact(user_text: str, shop_last_reply: str) -> str:
    #the shop's last reply goes in too, so a bare name or number answering it reads as theirs
    contact_text: str = f"SHOP_LAST_REPLY: {shop_last_reply}\nUSER_MESSAGE: {user_text}"

    system_prompt: str = contact_extractor.prompt()

    return extract("CONTACT EXTRACTOR", CONTACT_EXTRACTOR_MODEL, system_prompt, contact_text)



#**********EXTRACTED VALUES**********
#reads the values out of an extractor's line, and finds their email exactly as they typed it


#EXTRACTOR VALUES
#the value after each field name on the extractor's first line, in the order the names are given
def extractor_values(extractor_output: str, field_names: list[str]) -> list[str]:
    output_lines: list[str] = extractor_output.strip().splitlines()

    #only the first line is the format, anything the model adds under it is never info
    format_line: str = output_lines[0]

    elements: list[str] = format_line.split("|")

    values: list[str] = []

    for field_name, element in zip(field_names, elements):
        label_and_value: list[str] = element.split(":", 1)

        label: str = label_and_value[0].strip().lower()

        #a reply that talks instead of giving the format gets dropped, so it never gets written as info
        if(label != field_name):
            raise ValueError(f"not the {field_name} format, got {extractor_output}")

        value: str = label_and_value[1].strip()

        values.append(value)

    return values


#PRICING VALUES
#the price for each service on the pricing extractor's line, keyed by the service
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

        #each service comes right before its price, so the price is stored under the service read just before it
        if(label == "service"):
            service = value

        elif(label == "price" and service != ""):
            services_pricing[service] = value

    return services_pricing


#EMAIL VALUE
#their email exactly as they typed it, "" when there isn't one
def email_value(user_text: str) -> str:
    #the first email exactly as they typed it, so the owner never gets an address a model reworded
    email_match: re.Match | None = re.search(EMAIL_PATTERN, user_text)

    #nothing in their text is written out like an email
    if(email_match is None):
        return ""

    return email_match.group(0)
