#**********IMPORTS**********
#text encoding, file types, random names and link parsing, the env, the saved state, and the media downloader
import base64
import mimetypes
import os
import re
import secrets
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from helpers.media import media_prep
from helpers.state.log import REDIS_CLIENT



#**********GLOBALS**********
#where this server is reached from the internet, and how long the pics it keeps stay up


#LOAD ENV
load_dotenv()


#PUBLIC URL
#the address this server is reached at from the internet (the ngrok url while testing), blooio fetches the pics from it
#getenv so the server still starts before it is in .env, the pics then go as their own links
PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")


#MEDIA PATH
MEDIA_PATH: str = "/media"


#KEPT TIME
#blooio fetches a pic the moment its text goes out, a day leaves room for a retry or the owner opening its link
HOSTED_SECONDS: int = 86400


#BLOOIO HOST
#a text customer's pics are already on blooio, which always fetches its own links
BLOOIO_HOST: str = "blooio.com"


#FILE NAME
#the random name a kept pic gets and its file type, so nothing else ever gets looked up
FILE_NAME_PATTERN: re.Pattern = re.compile(r"^[0-9a-f]{32}\.[a-z0-9]{2,5}$")



#**********HOSTING**********
#keeps a copy of a customer's pic on this server, instagram's own link to it never opens for blooio


#BLOOIO LINK
#True when the link is on blooio or one of its subdomains, so blooio can already fetch it
def blooio_link(media_url: str) -> bool:
    host: str | None = urlparse(media_url).hostname

    if(host is None):
        return False

    return host == BLOOIO_HOST or host.endswith(f".{BLOOIO_HOST}")


#HOST MEDIA
#the link blooio fetches the pic from, its own link when it's already on blooio or no copy could be kept
def host_media(media_url: str) -> str:
    if(blooio_link(media_url)):
        return media_url

    if(PUBLIC_BASE_URL == ""):
        print("MEDIA HOST ERROR: PUBLIC_BASE_URL is not set, the pic goes as its own link")

        return media_url

    http_response: requests.Response | None = media_prep.download_media(media_url)

    if(http_response is None):
        return media_url

    extension: str = media_prep.media_file_extension(http_response)

    #not a pic or video, so there's nothing to show
    if(extension == ""):
        return media_url

    file_name: str = f"{secrets.token_hex(16)}{extension}"

    media_data: str = base64.b64encode(http_response.content).decode("utf-8")

    try:
        REDIS_CLIENT.set(f"hosted_media_{file_name}", media_data, ex=HOSTED_SECONDS)

    #a video too big to keep or redis down still sends the text, with the pic's own link
    except Exception as error:
        print(f"MEDIA HOST ERROR: {error}")

        return media_url

    return f"{PUBLIC_BASE_URL}{MEDIA_PATH}/{file_name}"


#HOSTED MEDIA
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
