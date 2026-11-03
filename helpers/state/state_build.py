#**********IMPORTS**********
#python's date tools, plus the helpers that read their message, their vehicle and what's on file
import json
from datetime import datetime

from helpers.calendar import open_dates
from helpers.models import models
from helpers.models import retry
from helpers.response import spacing
from helpers.state import owner
from helpers.state import log
from helpers.state import state_form
from src import branches



#**********GLOBALS**********
#the vehicle details every price needs, and what the vehicle check reads


#CRITICAL FIELDS
CRITICAL_FIELD_NAMES: list[str] = ["make", "model", "color"]


#VEHICLE FIELDS
#the critical fields and the models of their other vehicles named next to the model, which only the form intro names
VEHICLE_FIELD_NAMES: list[str] = [*CRITICAL_FIELD_NAMES, "other_models"]



#**********MESSAGE AND HISTORY**********
#reads the batch they just sent into one message and the conversation so far out of the saved history


#TEXT ONLY
#only the texts of the batch, for when its media breaks the message form
def text_only(current_message_batch: list) -> list:
    text_batch: list = []

    for message in current_message_batch:
        if(isinstance(message, str)):
            text_batch.append(message)

    return text_batch


#USER MESSAGE
#the batch as one message, their text and their media described
def user_message_form(current_message_batch: list, channel: str) -> dict:
    try:
        user_message: dict = state_form.message_form(current_message_batch, channel)

        print(user_message)

        return user_message

    #media that breaks is dropped, so the text still gets answered
    except Exception as error:
        print(f"MESSAGE FORM ERROR: {error}")

        return state_form.message_form(text_only(current_message_batch), channel)


#MESSAGE HISTORY
#the conversation so far, empty when it can't be read
def message_history_read(id: str) -> dict:
    message_history: dict = {}

    try:
        message_history = state_form.message_history_form(id)

    #without history the message can still be answered on its own
    except Exception as error:
        print(f"HISTORY ERROR: {error}")

    return message_history



#**********VEHICLE READS**********
#reads their make, model, color now and the exact color they want out of the message and saves them, and the color now they typed, right away when it's neutral or once the pic asks run out


#VEHICLE CHECK
#gives back the color it is now it read, which only ever comes from a pic or video of their vehicle
def critical_info_check(user_message: dict, message_history: dict, id: str) -> str:
    #the shop's last reply goes with it, so a short answer like "2020 civic" reads as what it answers
    shop_last_reply: str = spacing.last_sent_reply(message_history)

    user_text: str = user_message["user_text"].strip()

    #the color it is now only comes from a photo or video of their vehicle, a form lead has none
    user_media: dict = user_message.get("user_media", {})

    critical_output: str = models.extract_vehicle(user_text, user_media, shop_last_reply)

    #an answer missing the other models still reads, it just has none on file
    critical_values: list[str] = models.extractor_values(critical_output, VEHICLE_FIELD_NAMES)

    log.write_info(f"criticalInfo_{id}", critical_values, VEHICLE_FIELD_NAMES)

    color_now: str = critical_values[VEHICLE_FIELD_NAMES.index("color")]

    #a pic of their vehicle shows the color it is now over one they typed
    if(color_now != ""):
        log.clear_info(f"criticalInfo_{id}", branches.TYPED_COLOR_INFO_NAMES)

    return color_now


#WANT CHECK
#gives back the exact color they want it read, empty when the message sent none
def want_check(user_message: dict, message_history: dict, id: str, media: list[str], links: list[str]) -> str:
    #a pic sent right after the shop asked for the exact color reads as that color
    shop_last_reply: str = spacing.last_sent_reply(message_history)

    user_text: str = user_message["user_text"].strip()

    user_media: dict = user_message.get("user_media", {})

    want_output: str = models.extract_want(user_text, user_media, shop_last_reply)

    want: str = models.extractor_values(want_output, ["want"])[0]

    owner.note_wanted_color(id, want, media, links)

    return want


#VEHICLE MISSING
#True while the make, the model or the color it is now still isn't on file
def vehicle_missing(critical_info: dict[str, str]) -> bool:
    for field_name in CRITICAL_FIELD_NAMES:
        if(field_name not in critical_info):
            return True

    return False


#VEHICLE MODELS
#the model on file and then each other model of theirs read next to it, each once, so the form intro names every vehicle on the form
def vehicle_models(critical_info: dict[str, str]) -> list[str]:
    read_models: list[str] = [critical_info.get("model", ""), *critical_info.get("other_models", "").split(",")]

    kept: list[str] = []

    #each model lowercased, so a model written twice in different capitals is still kept once
    kept_lower: list[str] = []

    for model in read_models:
        #"Telluride." comes out as Telluride, the intro ends on its own period
        model = model.strip(" .")

        if(model != "" and model.lower() not in kept_lower):
            kept.append(model)

            kept_lower.append(model.lower())

    return kept


#VEHICLE FILL
#True when a pic or video they sent was read as a color: their vehicle showing the color it is now, or the exact color they want
def critical_info_fill(user_message: dict, message_history: dict, id: str, media: list[str], links: list[str]) -> bool:
    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    color_now: str = ""

    if(vehicle_missing(critical_info)):
        color_now = retry.with_retries("CRITICAL INFO ERROR", critical_info_check, [user_message, message_history, id])

    want: str = ""

    #the exact color they want only ever comes from a pic, screenshot, video or link
    if(len(media) > 0 or len(links) > 0):
        want = retry.with_retries("WANT INFO ERROR", want_check, [user_message, message_history, id, media, links])

    #a want read next to a link may have come from the link, so only one with no link says a pic was the color
    want_from_media: bool = want != "" and len(links) == 0

    return user_message.get("user_media", {}) != {} and (color_now != "" or want_from_media)


#COLOR ONLY
#its pics come off with no service_ques, here and in the copy on file, so this turn and every later one read only their color
def color_only_message(user_message: dict, id: str) -> dict:
    color_message: dict = state_form.without_service_ques(user_message)

    log.replace_message(f"usermsg_{id}", user_message, color_message)

    print("COLOR PIC: their pics were read as a color on the color job, so the service_ques comes off them")

    return color_message


#TYPED COLOR FILL
#a neutral color they typed goes on file right away and any other once the shop's asks for a pic ran out, while the color it is now is still missing after this message's vehicle check
def typed_color_fill(user_message: dict, message_history: dict, id: str) -> None:
    if(not branches.color_now_missing(id)):
        return

    retry.with_retries("TYPED COLOR ERROR", branches.typed_color_check, [user_message, message_history, id])



#**********STATE BUILD**********
#puts their message, the conversation so far and the shop's time together for every branch to read


#STATE
#their message, the conversation so far and the shop's local time, the base every branch reads
def state_formulation(user_message: dict, message_history: dict) -> dict:
    shop_time: datetime = datetime.now(open_dates.SHOP_TIMEZONE)

    current_date_time: str = shop_time.strftime(state_form.CURRENT_DATE_TIME_FORMAT)

    state: dict = {"current_date_time": current_date_time, "current_user_message": user_message, "message_history": message_history}

    return state


#JUST BOOKED
#what they just booked stays in the state till it comes off file, so every branch knows the job and the day
def add_just_booked(state: dict, id: str) -> dict:
    booked: dict[str, str] = log.read_info(f"booked_{id}")

    if(len(booked) == 0):
        return state

    services_pricing: dict = json.loads(booked.get("services", "{}"))

    state["just_booked"] = {"services_pricing": services_pricing, "drop_off_date": booked.get("drop_off_date", "")}

    return state


#BRANCH STATE
#the vehicle check runs first, then the state gets built with anything they just booked
def branch_state(user_message: dict, message_history: dict, id: str, current_message_batch: list) -> tuple[dict, dict[str, str]]:
    #the pics and links they sent go to the owner along with a new exact color they want
    media: list[str] = state_form.media_urls(current_message_batch)

    links: list[str] = state_form.text_links(current_message_batch)

    color_pic: bool = critical_info_fill(user_message, message_history, id, media, links)

    #on a wrap or colored PPF job a pic of the color they want, or of their vehicle for the color it is now, is only about that color
    if(color_pic and len(branches.color_job_on_file(id)) > 0):
        user_message = color_only_message(user_message, id)

    #a neutral color they typed stands in for a pic of their vehicle right away, any other once two asks for one went unanswered
    typed_color_fill(user_message, message_history, id)

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    state: dict = state_formulation(user_message, message_history)

    state = add_just_booked(state, id)

    state = branches.add_color_now(state, critical_info)

    print(state)

    print(f"KEY_INFO: {critical_info}")

    return (state, critical_info)
