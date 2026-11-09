#IMPORTS

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


#GLOBALS

CRITICAL_FIELD_NAMES: list[str] = ["make", "model", "color"]

#the critical fields plus the models of their other vehicles, which only the form intro names
VEHICLE_FIELD_NAMES: list[str] = CRITICAL_FIELD_NAMES + ["other_models"]


#MESSAGE HISTORY

#only the texts of the batch, for when its media breaks the message form
def text_only(current_message_batch: list) -> list:
    text_batch: list = []

    for message in current_message_batch:
        if(isinstance(message, str)):
            text_batch.append(message)

    return text_batch

#the batch as one message, their text and their media described
def user_message_form(current_message_batch: list, channel: str) -> dict:
    try:
        user_message: dict = state_form.message_form(current_message_batch, channel)

        print(user_message)

        return user_message
    except Exception as error:
        #media that breaks is dropped, so the text still gets answered
        print(f"MESSAGE FORM ERROR: {error}")

        return state_form.message_form(text_only(current_message_batch), channel)

#the conversation so far, empty when it can't be read
def message_history_read(id: str) -> dict:
    message_history: dict = {}

    try:
        message_history = state_form.message_history_form(id)
    except Exception as error:
        #without history the message can still be answered on its own
        print(f"HISTORY ERROR: {error}")

    return message_history


#VEHICLE READS

#gives back the color it is now it read, which only ever comes from a pic or video of their vehicle
def critical_info_check(user_message: dict, message_history: dict, id: str) -> str:
    #the shops last reply rides along, so a bare 2020 civic reads as the answer it is
    shop_last_reply: str = spacing.last_sent_reply(message_history)

    user_text: str = user_message["user_text"].strip()

    #the color it is now only comes from a photo or video of there vehicle, a form lead has none
    user_media: dict = user_message.get("user_media", {})

    critical_output: str = models.extract_vehicle(user_text, user_media, shop_last_reply)

    #an answer missing the other models still reads, it just has none on file
    critical_values: list[str] = models.extractor_values(critical_output, VEHICLE_FIELD_NAMES)

    log.write_info(f"criticalInfo_{id}", critical_values, VEHICLE_FIELD_NAMES)

    color_now: str = critical_values[VEHICLE_FIELD_NAMES.index("color")]

    #a pic of there vehicle shows the color it is now over one they typed
    if(color_now != ""):
        log.clear_info(f"criticalInfo_{id}", branches.TYPED_COLOR_INFO_NAMES)

    return color_now

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

#true while the make, the model or the color it is now still isn't on file
def vehicle_missing(critical_info: dict[str, str]) -> bool:
    for field_name in CRITICAL_FIELD_NAMES:
        if(field_name not in critical_info):
            return True

    return False

#the model on file then each other model, once each, so the form intro names every vehicle
def vehicle_models(critical_info: dict[str, str]) -> list[str]:
    read_models: list[str] = [critical_info.get("model", "")] + critical_info.get("other_models", "").split(",")

    kept: list[str] = []

    #each model lowercased, so a model written twice in different capitals is still kept once
    kept_lower: list[str] = []

    for model in read_models:
        #stray spaces and periods come off, the intro ends on its own period
        model = model.strip(" .")

        if(model != "" and model.lower() not in kept_lower):
            kept.append(model)

            kept_lower.append(model.lower())

    return kept

#true when a pic or video read as a color, either the color it is now or the one they want
def critical_info_fill(user_message: dict, message_history: dict, id: str, media: list[str], links: list[str]) -> bool:
    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    color_now: str = ""

    if(vehicle_missing(critical_info)):
        color_now = retry.with_retries("CRITICAL INFO ERROR", critical_info_check, [user_message, message_history, id])

    want: str = ""

    #the exact color they want only ever comes from a pic, screenshot, video or link
    if(len(media) > 0 or len(links) > 0):
        want = retry.with_retries("WANT INFO ERROR", want_check, [user_message, message_history, id, media, links])

    #a want next to a link may have come from the link, so only a linkless want counts as a pic
    want_from_media: bool = want != "" and len(links) == 0

    return user_message.get("user_media", {}) != {} and (color_now != "" or want_from_media)

#service_ques comes off its pics here and on file, so every later turn reads only their color
def color_only_message(user_message: dict, id: str) -> dict:
    color_message: dict = state_form.without_service_ques(user_message)

    log.replace_message(f"usermsg_{id}", user_message, color_message)

    print("COLOR PIC: their pics were read as a color on the color job, so the service_ques comes off them")

    return color_message

#a typed color fills a missing color now, neutral ones right away, others once pic asks run out
def typed_color_fill(user_message: dict, message_history: dict, id: str) -> None:
    if(not branches.color_now_missing(id)):
        return

    retry.with_retries("TYPED COLOR ERROR", branches.typed_color_check, [user_message, message_history, id])


#STATE BUILD

#there message, the conversation so far and the shops local time, the base every branch reads
def state_formulation(user_message: dict, message_history: dict) -> dict:
    shop_time = datetime.now(open_dates.SHOP_TIMEZONE)

    current_date_time: str = shop_time.strftime(state_form.CURRENT_DATE_TIME_FORMAT)

    state: dict = {"current_date_time": current_date_time, "current_user_message": user_message, "message_history": message_history}

    return state

#what they just booked stays in the state till its off file, so branches know the job and day
def add_just_booked(state: dict, id: str) -> dict:
    booked: dict[str, str] = log.read_info(f"booked_{id}")

    if(len(booked) == 0):
        return state

    services_pricing: dict = json.loads(booked.get("services", "{}"))

    state["just_booked"] = {"services_pricing": services_pricing, "drop_off_date": booked.get("drop_off_date", "")}

    return state

#the vehicle check runs first, then the state gets built with anything they just booked
def branch_state(user_message: dict, message_history: dict, id: str, current_message_batch: list) -> tuple[dict, dict[str, str]]:
    #the pics and links they sent go to the owner along with a new exact color they want
    media: list[str] = state_form.media_urls(current_message_batch)

    links: list[str] = state_form.text_links(current_message_batch)

    color_pic: bool = critical_info_fill(user_message, message_history, id, media, links)

    #on a wrap or colored PPF job there pics are only about the color, the one now or the one wanted
    if(color_pic and len(branches.color_job_on_file(id)) > 0):
        user_message = color_only_message(user_message, id)

    #a typed neutral color stands in for a pic right away, any other once two asks got ghosted
    typed_color_fill(user_message, message_history, id)

    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    state: dict = state_formulation(user_message, message_history)

    state = add_just_booked(state, id)

    state = branches.add_color_now(state, critical_info)

    print(state)

    print(f"KEY_INFO: {critical_info}")

    return (state, critical_info)
