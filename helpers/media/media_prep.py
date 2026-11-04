#**********IMPORTS**********
#text encoding, in-memory files, file types, web downloads, and the image tools that open iphone pics
import base64
import io
import mimetypes

import requests
from PIL import Image
from pillow_heif import register_heif_opener



#**********GLOBALS**********
#which image types can go to the model just as they came in, and the file type each kind of pic is saved as


#SAFE TYPES
#image types the model reads as they are, any other image is converted to jpeg first
SAFE_TYPES: list[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]


#PIC FILE TYPES
#by the format the pic's own bytes are in, its server can say wrong (instagram sends a png as image/jpeg)
PIC_EXTENSIONS: dict[str, str] = {"JPEG": ".jpg", "MPO": ".jpg", "PNG": ".png", "GIF": ".gif", "WEBP": ".webp", "HEIF": ".heic", "AVIF": ".avif", "BMP": ".bmp", "TIFF": ".tiff"}



#**********IMAGE SETUP**********
#lets the image tools open iphone pics, so a heic photo from a customer can still be read


#HEIC SUPPORT
register_heif_opener()



#**********MEDIA HELPERS**********
#small steps for getting the file, fixing odd image types, reading what a pic is and packing it up as text


#DOWNLOAD MEDIA
#the downloaded file, None when the download failed
def download_media(media_url: str) -> requests.Response | None:
    try:
        http_response: requests.Response = requests.get(media_url, timeout=30)

        http_response.raise_for_status()

    except requests.RequestException as error:
        print(f"MEDIA PREP ERROR: download failed, {error}")

        return None

    return http_response


#JPEG CONVERT
#the same image as jpeg bytes, for an image type the model can't read as it is
def convert_to_jpeg(image_bytes: bytes) -> bytes:
    image: Image.Image = Image.open(io.BytesIO(image_bytes))

    rgb_image: Image.Image = image.convert("RGB")

    buffer: io.BytesIO = io.BytesIO()

    rgb_image.save(buffer, format="JPEG")

    return buffer.getvalue()


#PIC FORMAT
#the format the bytes are in (PNG, JPEG...), empty when they aren't a pic the image tools can open
def read_pic_format(media_bytes: bytes) -> str:
    try:
        image: Image.Image = Image.open(io.BytesIO(media_bytes))

    #a video or a broken file only means it isn't a pic, the text it goes with still goes out
    except Exception:
        return ""

    format_name: str | None = image.format

    if(not format_name):
        format_name = ""

    return format_name


#DATA URL
#the file packed up as text with its type in front, the way the model takes a pic or video
def data_url_of(media_bytes: bytes, media_type: str) -> str:
    encoded_bytes: bytes = base64.b64encode(media_bytes)

    media_data: str = encoded_bytes.decode("utf-8")

    return f"data:{media_type};base64,{media_data}"



#**********FILE TYPES**********
#what a downloaded pic or video really is, so a copy of it can be named and served as that


#FILE EXTENSION
#a pic goes by its own bytes, a video by the type its server says, empty when it's neither
def media_file_extension(http_response: requests.Response) -> str:
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



#**********PREPARE MEDIA**********
#downloads a pic or video a customer sent and turns it into something the model can look at


#PREPARE MEDIA
#the data url and "i" for an image or "v" for a video, both empty when it couldn't be downloaded or isn't either
def prepare_media(media_url: str) -> tuple[str, str]:
    if(not media_url):
        print("MEDIA PREP ERROR: no media url was given")

        return ("", "")

    http_response: requests.Response | None = download_media(media_url)

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
