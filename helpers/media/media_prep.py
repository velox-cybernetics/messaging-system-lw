#IMPORTS

import base64
import io
import mimetypes

import requests
from PIL import Image
from pillow_heif import register_heif_opener


#GLOBALS

#image types the model reads as they are, any other image is converted to jpeg first
SAFE_TYPES: list[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]

#keyed by the format in the pics own bytes, servers lie, instagram sends a png labeled as jpeg
PIC_EXTENSIONS: dict[str, str] = {"JPEG": ".jpg", "MPO": ".jpg", "PNG": ".png", "GIF": ".gif", "WEBP": ".webp", "HEIF": ".heic", "AVIF": ".avif", "BMP": ".bmp", "TIFF": ".tiff"}


#IMAGE SETUP

register_heif_opener()


#MEDIA HELPERS

#the downloaded file, None when the download failed
def download_media(media_url: str):
    try:
        http_response = requests.get(media_url, timeout=30)

        http_response.raise_for_status()
    except requests.RequestException as error:
        print(f"MEDIA PREP ERROR: download failed, {error}")

        return None

    return http_response

#the same image as jpeg bytes, for an image type the model can't read as it is
def convert_to_jpeg(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))

    rgb_image = image.convert("RGB")

    buffer = io.BytesIO()

    rgb_image.save(buffer, format="JPEG")

    return buffer.getvalue()

#the format name the bytes are in, like PNG or JPEG, empty when the image tools can't open them
def read_pic_format(media_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(media_bytes))
    except Exception:
        #a video or a broken file only means it isn't a pic, the text it goes with still goes out
        return ""

    format_name: str | None = image.format

    if(not format_name):
        format_name = ""

    return format_name

#the file packed up as text with its type in front, the way the model takes a pic or video
def data_url_of(media_bytes: bytes, media_type: str) -> str:
    encoded_bytes: bytes = base64.b64encode(media_bytes)

    media_data: str = encoded_bytes.decode("utf-8")

    return f"data:{media_type};base64,{media_data}"


#FILE TYPES

#a pic goes by its own bytes, a video by the type its server says, empty when its neither
def media_file_extension(http_response) -> str:
    pic_format: str = read_pic_format(http_response.content)

    if(pic_format in PIC_EXTENSIONS):
        return PIC_EXTENSIONS[pic_format]

    media_type: str = http_response.headers.get("Content-Type", "").split(";")[0]

    if(not media_type.startswith(("image/", "video/"))):
        return ""

    extension: str | None = mimetypes.guess_extension(media_type)

    if(not extension):
        extension = ""

    return extension


#PREPARE MEDIA

#the data url plus i for an image or v for a video, both empty when the download or type flops
def prepare_media(media_url: str) -> tuple[str, str]:
    if(not media_url):
        print("MEDIA PREP ERROR: no media url was given")

        return ("", "")

    http_response = download_media(media_url)

    if(http_response is None):
        return ("", "")

    media_bytes: bytes = http_response.content

    content_type: str = http_response.headers.get("Content-Type", "")

    media_type: str = content_type.split(";")[0]

    if(not media_type.startswith("image/") and not media_type.startswith("video/")):
        print(f"MEDIA PREP ERROR: not an image or video, content type was {content_type}")

        return ("", "")

    if(media_type.startswith("image/") and media_type not in SAFE_TYPES):
        try:
            media_bytes = convert_to_jpeg(media_bytes)
        except Exception as error:
            print(f"MEDIA PREP ERROR: could not convert image to jpeg, {error}")

            return ("", "")

        media_type = "image/jpeg"

    data_url: str = data_url_of(media_bytes, media_type)

    if(media_type.startswith("image/")):
        return (data_url, "i")
    else:
        return (data_url, "v")
