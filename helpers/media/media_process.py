#**********IMPORTS**********
#the model lineups, the reply cleaner, and the prompts that ask for a pic or video write up
from helpers.models import chat
from helpers.response.sanitize import sanitize_reply
from src.prompts.media import describe



#**********GLOBALS**********
#which model looks at the media, how hard it thinks, and what comes back when it fails


#MEDIA MODEL
MODEL_NAME: str = "z-ai/glm-5.3-flashx"

MEDIA_EFFORT: str = "high"

#a high effort read of a pic or video can think for over a minute before it writes
MEDIA_TIMEOUT: int = 300


#MEDIA ERROR
#the model sees this text as it is, typo included
MEDIA_ERROR: str = "ERROR: MEDIA COULT NOT BE PROCESSED"



#**********MODEL REQUEST**********
#builds the message with the right prompt for a pic or a video and sends it down its lineup


#MEDIA CONTENT
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


#MEDIA LINEUP
#flashx reads it and kimi k3.1 pro steps in when flashx errors or comes back empty on a pic, and a video only goes to flashx
def media_lineup(media_type: str) -> list[tuple[str, str]]:
    if(media_type == "v"):
        return [(MODEL_NAME, MEDIA_EFFORT)]

    return [(MODEL_NAME, MEDIA_EFFORT), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]


#MEDIA TEXT
#the model's write up of the pic or video, "" when every model came back empty
def media_text(content: list, media_type: str) -> str:
    message: dict = {"role": "user", "content": content}

    return chat.lineup_text("MEDIA PROCESS", media_lineup(media_type), {"messages": [message]}, MEDIA_TIMEOUT)



#**********PROCESS MEDIA**********
#sends a pic or video to the model and gets back a written description of it for the conversation


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

    #the description stays in the conversation for good, so junk the model leaks after it is cut first
    description = sanitize_reply(description)

    print(f"MEDIA PROCESS: {description}")

    return description
