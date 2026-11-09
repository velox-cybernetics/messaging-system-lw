#IMPORTS

import json
import re
from concurrent.futures import ThreadPoolExecutor

from helpers.media.media_prep import prepare_media
from helpers.media.media_process import process_media
from helpers.state.log import read_messages
from helpers.terminal import prints


#GLOBALS

#a link they typed, up to the first space
URL_PATTERN: str = r"https?://\S+"

#the attachment types instagram sends for a story, one they posted or one they were tagged in
STORY_TYPES: list[str] = ["ig_story", "story", "story_mention"]

#pics or videos of one batch get described at once, so ten pics don't take ten times as long
MAX_MEDIA_WORKERS: int = 8

#how the shops local time is written into the state, so whatever reads it back parses the same text
CURRENT_DATE_TIME_FORMAT: str = "%A, %B %d, %Y at %I:%M %p"

#a lead form carries no media, and only the first reply to one greets
FORM_CHANNELS: list[str] = ["meta-form", "website-form"]

#form labels lowercased with their colon or question mark, and the field each one fills
FORM_LABELS: dict[str, str] = {}

#meta form
FORM_LABELS["which service are you looking for?"] = "service"

FORM_LABELS["when are you looking to get this done?"] = "time"

FORM_LABELS["our services vary depending on vehicle and coverage. where do you see your project falling?"] = "pricing"

FORM_LABELS["full name:"] = "name"

FORM_LABELS["phone number:"] = "phone"

#website form
FORM_LABELS["first name:"] = "first_name"

FORM_LABELS["last name:"] = "last_name"

FORM_LABELS["phone:"] = "phone"

#both forms
FORM_LABELS["vehicle year/make/model:"] = "vehicle"

FORM_LABELS["email:"] = "email"


#STATE HISTORY

#the state as one compact line, accents and emojis kept as they are
def state_to_text(state: dict) -> str:
    return json.dumps(state, ensure_ascii=False, separators=(",", ":"))

#the saved chat laid out turn by turn, each message of theirs next to the shops reply to it
def message_history_form(id: str) -> dict:
    user_messages: list = read_messages(f"usermsg_{id}")

    system_responses: list = read_messages(f"systemres_{id}")

    history: dict = {}

    #the longer side sets the turns, a missing message or response just leaves its key out
    turns: int = max(len(user_messages), len(system_responses))

    for turn in range(turns):
        if(turn < len(user_messages)):
            history[f"user_message_{turn}"] = user_messages[turn]

        if(turn < len(system_responses)):
            history[f"system_response_to_user_message_{turn}"] = system_responses[turn]

    return history


#LINKS

#where each pic or video in the batch lives, so the ones that matter can be sent on to the owner
def media_urls(current_message_batch: list) -> list[str]:
    urls: list[str] = []

    for message in current_message_batch:
        if(not isinstance(message, list)):
            continue

        for item in message:
            if(not isinstance(item, dict)):
                continue

            payload: dict | None = item.get("payload")

            if(not payload):
                payload = {}

            #blooio puts the url on the item, instagram and messenger put it in the payload
            url: str | None = item.get("url")

            if(not url):
                url = payload.get("url")

            if(not url):
                url = payload.get("story_media_url")

            if(url):
                urls.append(url)

    return urls

#every link typed in the batch, with the punctuation that ends a sentence left off
def text_links(current_message_batch: list) -> list[str]:
    links: list[str] = []

    for message in current_message_batch:
        if(isinstance(message, str)):
            for link in re.findall(URL_PATTERN, message):
                links.append(link.rstrip(".,!?)"))

    return links


#COLOR PICS

#the line of a media description that names the service its pic shows or points to
SERVICE_QUES_LABEL: str = "service_ques:"

#the same message minus the service_ques line in every media description, the rest untouched
def without_service_ques(user_message: dict) -> dict:
    color_media: dict = {}

    for element_name, element in user_message.get("user_media", {}).items():
        color_element: dict = {}

        for field_name, field_value in element.items():
            kept_value: object = field_value

            #blooio says media_description, instagram and messenger tack if applicable on the end
            if(field_name.startswith("media_description") and isinstance(field_value, str)):
                kept_lines: list[str] = []

                for line in field_value.split("\n"):
                    if(not line.strip().lower().startswith(SERVICE_QUES_LABEL)):
                        kept_lines.append(line)

                kept_value = "\n".join(kept_lines)

            color_element[field_name] = kept_value

        color_media[element_name] = color_element

    color_message: dict = {}

    for key, value in user_message.items():
        color_message[key] = value

    color_message["user_media"] = color_media

    return color_message


#DESCRIBING MEDIA

#descriptions come back in the order the media came, so media_element_N stays the Nth one sent
def describe_media(data_urls_types: list[tuple]) -> list[str]:
    if(len(data_urls_types) == 0):
        return []

    worker_count: int = min(len(data_urls_types), MAX_MEDIA_WORKERS)

    descriptions: list[str] = []

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures: list = []

        for data_url_type in data_urls_types:
            #each worker prints into the same block as the message batch the media came with
            batch_context = prints.batch_context()

            submitted = executor.submit(batch_context.run, process_media, data_url_type[0], data_url_type[1])

            futures.append(submitted)

        #read back in the order they were sent off, not the order they finish
        for future in futures:
            descriptions.append(future.result())

    return descriptions

#a group of attachments is read item by item, a lone attachment is read from its first item
def attachment_items(attachment: list) -> list:
    if(len(attachment) > 1):
        return attachment
    else:
        return [attachment[0]]


#META CHANNELS

#meta sends the story link in url, fall back to story_media_url if it is missing
def story_url(payload: dict) -> str | None:
    url: str | None = payload.get("url")

    if(not url):
        url = payload.get("story_media_url")

    return url

#prepared media or empty string if it wasn't downloaded, and its caption, for one instagram item
def instagram_attachment(item: dict, in_group: bool) -> list:
    media_type: str | None = item.get("type")

    payload: dict | None = item.get("payload")

    if(media_type == "ig_post"):
        return [prepare_media(payload.get("url")), payload.get("title")]
    elif(media_type in STORY_TYPES):
        data_url_and_type: tuple = prepare_media(story_url(payload))

        #a story inside a group of attachments gets no caption, a lone story keeps its title
        if(in_group):
            return [data_url_and_type, ""]
        else:
            return [data_url_and_type, payload.get("title")]
    elif(media_type in ["image", "video"]):
        return [prepare_media(payload.get("url")), ""]
    elif(media_type == "ig_reel"):
        #reels are not downloaded, there title is the caption
        return ["", payload.get("title")]
    else:
        return ["", ""]

#the ad they wrote in from, its photo or video prepared with the ads title as its caption
def instagram_referral(referral: dict) -> list:
    data: dict = referral.get("ads_context_data", {})

    if(data.get("photo_url")):
        return [prepare_media(data.get("photo_url")), data.get("ad_title")]
    elif(data.get("video_url")):
        return [prepare_media(data.get("video_url")), data.get("ad_title")]
    else:
        return ["", ""]

#prepared media or empty string if it wasn't downloaded, and its caption, for one messenger item
def messenger_attachment(item: dict) -> list:
    media_type: str | None = item.get("type")

    payload: dict | None = item.get("payload")

    if(not payload):
        payload = {}

    title: str | None = payload.get("title")

    if(not title):
        title = ""

    #photos, videos, and shared posts are downloaded, a shared post keeps its caption
    if(media_type in ["image", "video", "post", "ig_post"]):
        return [prepare_media(payload.get("url")), title]
    elif(media_type in ["fallback", "reel", "ig_reel"]):
        #shared links and reels are not downloaded, there title is the caption
        return ["", title]
    else:
        #audio, files, and anything else cannot be described
        return ["", ""]

#video_url is the thumbnail of the ad video, so both are images
def messenger_referral(referral: dict) -> list:
    data: dict | None = referral.get("ads_context_data")

    if(not data):
        data = {}

    ad_url: str | None = data.get("photo_url")

    if(not ad_url):
        ad_url = data.get("video_url")

    if(not ad_url):
        ad_url = ""

    ad_title: str | None = data.get("ad_title")

    if(not ad_title):
        ad_title = ""

    if(ad_url):
        return [prepare_media(ad_url), ad_title]
    else:
        return ["", ad_title]


#MEDIA ELEMENTS

#instagram and messenger share these two fields, so prompts read a post or ad the same on both
def post_media_elements(media_processed: list[list]) -> list[dict]:
    #only prepared media is described, anything not downloaded keeps an empty description
    prepared: list[tuple] = []

    for media in media_processed:
        if(media[0] != ""):
            prepared.append(media[0])

    descriptions: list[str] = describe_media(prepared)

    media_elements: list[dict] = []

    for media in media_processed:
        media_description: str = ""

        if(media[0] != ""):
            media_description = descriptions.pop(0)

        media_elements.append({"media_description(if applicable)": media_description, "post_description(if applicable)": media[1]})

    return media_elements

#every pic or video they sent on blooio, described
def blooio_media_elements(attachments: list) -> list[dict]:
    data_urls_types: list[tuple] = []

    for attachment in attachments:
        for item in attachment_items(attachment):
            data_urls_types.append(prepare_media(item.get("url")))

    media_elements: list[dict] = []

    for media_description in describe_media(data_urls_types):
        media_elements.append({"media_description": media_description})

    return media_elements

#every attachment and ad they sent on instagram, prepared and then described
def instagram_media_elements(attachments: list, referrals: list) -> list[dict]:
    media_processed: list[list] = []

    for attachment in attachments:
        in_group: bool = len(attachment) > 1

        for item in attachment_items(attachment):
            media_processed.append(instagram_attachment(item, in_group))

    for referral in referrals:
        media_processed.append(instagram_referral(referral))

    return post_media_elements(media_processed)

#every attachment and ad they sent on messenger, prepared and then described
def messenger_media_elements(attachments: list, referrals: list) -> list[dict]:
    media_processed: list[list] = []

    for attachment in attachments:
        for item in attachment:
            media_processed.append(messenger_attachment(item))

    for referral in referrals:
        media_processed.append(messenger_referral(referral))

    return post_media_elements(media_processed)

#the media of the batch described the way its channel sends it, None for any other channel
def media_element_form(attachments: list, referrals: list, channel: str) -> list[dict] | None:
    if(channel == "blooio"):
        return blooio_media_elements(attachments)
    elif(channel == "ig"):
        return instagram_media_elements(attachments, referrals)
    elif(channel == "messenger"):
        return messenger_media_elements(attachments, referrals)
    else:
        return None


#LEAD FORMS

#every field the forms labeled lines fill, empty when the form doesn't have it
def form_fields(current_message_batch: list) -> dict[str, str]:
    form: dict[str, str] = {"name": "", "first_name": "", "last_name": "", "service": "", "time": "", "pricing": "", "vehicle": "", "phone": "", "email": ""}

    #a later line for the same field wins, so a resubmitted form replaces the old one
    for message in current_message_batch:
        if(isinstance(message, str)):
            for label, field in FORM_LABELS.items():
                if(message.lower().startswith(label)):
                    form[field] = message[len(label):].strip()

                    break

    return form

#the full name they typed on the form, the website form splits it in two
def form_name(form: dict[str, str]) -> str:
    name: str = form["name"]

    if(not name):
        name = f"{form['first_name']} {form['last_name']}".strip()

    return name

#a lead form written as the message they'd have typed, so it reads like any other first message
def form_message(current_message_batch: list, channel: str) -> dict:
    form: dict[str, str] = form_fields(current_message_batch)

    name: str = form_name(form)

    #meta form gets the full quote, website form just name and vehicle, phone and email stay out
    if(channel == "meta-form"):
        #time and price range sit out for now, only the service and the vehicle go in
        text: str = f"hello my name is {name}, I am looking to get the service of {form['service']} the vehicle I have is {form['vehicle']}"
    else:
        text = f"hello my name is {name}, I am interested in your services, the vehicle I have is {form['vehicle']}."

    return {"user_text": text}


#MESSAGE FORM

#each pic, video, post or ad of the batch as media_element_N, empty when they sent none
def chat_media(current_attachments: list, current_referrals: list, channel: str) -> dict:
    media: dict = {}

    if(current_attachments != [] or current_referrals != []):
        media_elements: list[dict] = media_element_form(current_attachments, current_referrals, channel)

        for position, media_element in enumerate(media_elements):
            media[f"media_element_{position}"] = media_element

    return media

#their texts joined line by line and their media described
def chat_message(current_message_batch: list, channel: str) -> dict:
    current_text: list = []

    current_attachments: list = []

    current_referrals: list = []

    #a batch mixes texts, attachment lists, and ad referrals, empty ones are dropped
    for message in current_message_batch:
        if(isinstance(message, list) and message != []):
            current_attachments.append(message)
        elif(isinstance(message, str)):
            current_text.append(message)
        elif(isinstance(message, dict) and message != {}):
            current_referrals.append(message)

    media: dict = chat_media(current_attachments, current_referrals, channel)

    text_lines: list[str] = []

    for sent_text in current_text:
        if(sent_text.strip() != ""):
            text_lines.append(sent_text.strip())

    #each text keeps its own line, so color change probably then gray never reads as one sentence
    text: str = "\n".join(text_lines)

    return {"user_media": media, "user_text": text}

#the batch as the message the system reads, chat text and media or a lead form put into words
def message_form(current_message_batch: list, channel: str) -> dict:
    if(channel not in FORM_CHANNELS):
        return chat_message(current_message_batch, channel)
    else:
        return form_message(current_message_batch, channel)
