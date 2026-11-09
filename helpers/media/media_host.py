#IMPORTS

import base64
import mimetypes
import os
import re
import secrets
from urllib.parse import urlparse

from dotenv import load_dotenv

from helpers.media import media_prep
from helpers.state.log import REDIS_CLIENT


#GLOBALS

load_dotenv()

#this servers public address for blooio to fetch from, empty means pics go as there own links
PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

MEDIA_PATH: str = "/media"

#blooio fetches a pic as its text goes out, a day leaves room for a retry or the owner clicking it
HOSTED_SECONDS: int = 86400

#a text customers pics are already on blooio, which always fetches its own links
BLOOIO_HOST: str = "blooio.com"

#the random name a kept pic gets and its file type, so nothing else ever gets looked up
FILE_NAME_PATTERN = re.compile(r"^[0-9a-f]{32}\.[a-z0-9]{2,5}$")


#HOSTING

#true when the link is on blooio or a subdomain of it, so blooio can already fetch it
def blooio_link(media_url: str) -> bool:
    host: str | None = urlparse(media_url).hostname

    if(host is None):
        return False

    if(host == BLOOIO_HOST):
        return True

    return host.endswith(f".{BLOOIO_HOST}")

#the link blooio fetches the pic from, the original when its on blooio already or can't be kept
def host_media(media_url: str) -> str:
    if(blooio_link(media_url)):
        return media_url

    if(PUBLIC_BASE_URL == ""):
        print("MEDIA HOST ERROR: PUBLIC_BASE_URL is not set, the pic goes as its own link")

        return media_url

    http_response = media_prep.download_media(media_url)

    if(http_response is None):
        return media_url

    extension: str = media_prep.media_file_extension(http_response)

    #not a pic or video, so theres nothing to show
    if(extension == ""):
        return media_url

    file_name: str = f"{secrets.token_hex(16)}{extension}"

    media_data: str = base64.b64encode(http_response.content).decode("utf-8")

    try:
        REDIS_CLIENT.set(f"hosted_media_{file_name}", media_data, ex=HOSTED_SECONDS)
    except Exception as error:
        #a video too big to keep or redis down still sends the text, with the pics own link
        print(f"MEDIA HOST ERROR: {error}")

        return media_url

    return f"{PUBLIC_BASE_URL}{MEDIA_PATH}/{file_name}"

#the kept pic and its file type, None when the name was never handed out or its day is up
def hosted_media(file_name: str) -> tuple[bytes, str] | None:
    if(not FILE_NAME_PATTERN.match(file_name)):
        return None

    media_data: str | None = REDIS_CLIENT.get(f"hosted_media_{file_name}")

    if(media_data is None):
        return None

    media_type: str | None = mimetypes.guess_type(file_name)[0]

    if(not media_type):
        media_type = "application/octet-stream"

    return (base64.b64decode(media_data), media_type)
