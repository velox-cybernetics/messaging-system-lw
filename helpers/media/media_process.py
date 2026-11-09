#IMPORTS

from helpers.models import chat
from helpers.response.sanitize import sanitize_reply
from src.prompts.media import describe


#GLOBALS

MODEL_NAME: str = "z-ai/glm-5.3-flashx"

MEDIA_EFFORT: str = "high"

#a high effort read of a pic or video can think for over a minute before it writes
MEDIA_TIMEOUT: int = 300

#the model sees this text as it is, typo included
MEDIA_ERROR: str = "ERROR: MEDIA COULT NOT BE PROCESSED"


#MODEL REQUEST

#the write up prompt and the media itself, None when the media type is neither a pic nor a video
def media_content(data_url: str, media_type: str) -> list | None:
    media_info: dict = {"url": data_url}

    if(media_type == "i"):
        prompt: str = describe.image_prompt()

        media_block: dict = {"type": "image_url", "image_url": media_info}
    elif(media_type == "v"):
        prompt = describe.video_prompt()

        media_block = {"type": "video_url", "video_url": media_info}
    else:
        return None

    text_block: dict = {"type": "text", "text": prompt}

    return [text_block, media_block]

#flashx first, the backup model covers a pic when flashx errors or blanks, videos are flashx only
def media_lineup(media_type: str) -> list[tuple[str, str]]:
    if(media_type == "v"):
        return [(MODEL_NAME, MEDIA_EFFORT)]

    return [(MODEL_NAME, MEDIA_EFFORT), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

#the models write up of the pic or video, empty string when every model came back empty
def media_text(content: list, media_type: str) -> str:
    message: dict = {"role": "user", "content": content}

    return chat.lineup_text("MEDIA PROCESS", media_lineup(media_type), {"messages": [message]}, MEDIA_TIMEOUT)


#PROCESS MEDIA

#the cleaned up description, or the media error text when it couldn't be read
def process_media(data_url: str, media_type: str) -> str:
    content: list | None = media_content(data_url, media_type)

    if(content is None):
        return MEDIA_ERROR

    try:
        description: str = media_text(content, media_type)
    except chat.ANSWER_ERRORS as error:
        print(f"MEDIA PROCESS ERROR: {error}")

        return MEDIA_ERROR

    if(description.strip() == ""):
        print("MEDIA PROCESS ERROR: no description came back")

        return MEDIA_ERROR

    #the description stays in the conversation for good, so any junk the model leaks gets cut first
    description = sanitize_reply(description)

    print(f"MEDIA PROCESS: {description}")

    return description
