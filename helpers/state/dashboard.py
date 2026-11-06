#**********IMPORTS**********
#python's text encoding, json, clock, file buffers, random names and the one background worker, the env, web requests, the image tools with iphone pics, the shop's timezone, the customer's name, the bot's own state and who the owner already had
import base64
import io
import json
import os
import secrets
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
from dotenv import load_dotenv
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from helpers.calendar import open_dates
from helpers.channels import username
from helpers.state import log
from helpers.state import owner



#**********GLOBALS**********
#where the dashboard's own database is, which tab each channel shows under, and how long everything stays


#LOAD ENV
load_dotenv()


#DASHBOARD DATABASE
#the dashboard has its own upstash database, so its polling and pics never use up the bot's
#getenv so the bot still runs before they are in .env, nothing goes to the dashboard till they are
DASH_REDIS_URL: str = os.getenv("DASH_REDIS_URL", "").rstrip("/")

DASH_REDIS_TOKEN: str = os.getenv("DASH_REDIS_TOKEN", "")

ENABLED: bool = DASH_REDIS_URL != "" and DASH_REDIS_TOKEN != ""


#REQUEST TIMES
#the on or off check sits in front of every reply, so it gives up fast and the bot keeps answering
SWITCH_TIMEOUT: int = 3

#every write runs off the reply path, so it can wait a little longer
WRITE_TIMEOUT: int = 10


#TABS
#the dashboard tab a conversation shows under, set by the channel it first came in on
#texts go under forms, since texting is how every form lead gets answered, so a form lead and anyone who texts the shop's number sit together
TABS: dict[str, str] = {"blooio": "forms", "ig": "instagram", "messenger": "messenger", "meta-form": "forms", "website-form": "forms"}


#NAMED CHANNELS
#only instagram and messenger ids need a lookup to read as a name, a text id is already their number
NAMED_CHANNELS: list[str] = ["ig", "messenger"]


#ON ONLY CHANNELS
#channels that only show the people the bot's actually answering, anyone switched off there (or the whole tab) never even makes the board
ON_ONLY_CHANNELS: list[str] = ["ig"]


#KEPT TIMES
#a thread keeps its newest entries and stays a year past its last message
THREAD_MAX: int = 500

CONVO_SECONDS: int = 365 * 86400

#the counts by day and by month stay a little over a year, by year a little over two, the sets behind the hourly counts two days
DAY_SECONDS: int = 400 * 86400

MONTH_SECONDS: int = 400 * 86400

YEAR_SECONDS: int = 800 * 86400

HOUR_SECONDS: int = 2 * 86400

#the copied pics and the states replies were written from stay a month
MEDIA_SECONDS: int = 30 * 86400

STATE_SECONDS: int = 30 * 86400

#a follow up that went out, or a hold, stays two weeks, as long as the follow ups page looks back, and a day more so its oldest day is always whole
FOLLOWUP_SECONDS: int = 15 * 86400


#COUNT HASHES
#the overview reads its counts from these hashes, so a conversation's ledger copies every write to them
COUNT_KEY_STARTS: tuple[str, ...] = ("day:", "month:", "year:")


#HEARTBEAT
#while the server runs it checks in this often, so the overview can tell when it stops
BEAT_SECONDS: int = 300

#the commit render deployed the server from, so the dashboard knows when an upvote's example is live, empty anywhere but render
UP_COMMIT: str = os.getenv("RENDER_GIT_COMMIT", "")


#PIC SIZE
#longest side of a kept pic, big enough to read the color off a car, small enough that a month of pics fits the free plan's 250 MB
#a phone photo comes out around 60 to 110 KB
PIC_MAX_SIDE: int = 1024

PIC_QUALITY: int = 70

#a file bigger than this is never a phone pic, so it stays a link instead of coming down
PIC_MAX_BYTES: int = 25 * 1024 * 1024


#MEDIA TRIES
#instagram's link to a pic can fail for a moment right as the message lands, so the copy gets a few tries a couple seconds apart
MEDIA_TRIES: int = 3

MEDIA_RETRY_SECONDS: int = 2


#PREVIEW
#how much of the last message the conversation list shows
PREVIEW_CHARS: int = 140


#HAND OFF KINDS
#a schedule request counts as booked, every other hand off to the owner as a hil
HIL: str = "hil"

BOOKED: str = "booked"


#WORKER
#one worker writes everything in the order it happened, so a slow pic never puts a thread out of order
WORKER: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dashboard")


#LAST SWITCH
#each customer's last on or off answer, so a dashboard outage leaves the switch where it was
#every heartbeat refills it from the dashboard's whole off list, so a customer switched off stays off through a restart and an outage
LAST_SWITCH: dict[str, bool] = {}


#LAST TAB SWITCH
#each tab's last on or off answer, refilled the same way, so a whole channel switched off stays off through an outage too
LAST_TAB_SWITCH: dict[str, bool] = {}


#NAMES LOOKED UP
#each id's name gets looked up once while the server runs, so a lookup meta refuses isn't asked again on every message
NAMES_LOOKED_UP: set[str] = set()


#TIMED KEYS
#the keys this server already gave a lifetime, so later writes to a stats key skip its EXPIRE, fewer requests on the free plan
TIMED_KEYS: set[str] = set()



#**********STARTUP**********
#lets the image tools open iphone pics, and says once when the dashboard keys are missing so a quiet dashboard is never a mystery


#HEIC SUPPORT
register_heif_opener()


#MISSING KEYS
if(not ENABLED):
    print("DASHBOARD OFF: DASH_REDIS_URL or DASH_REDIS_TOKEN is not set, nothing goes to the dashboard and nobody can be switched off")



#**********DATABASE**********
#every read and write goes to the dashboard database as redis commands over upstash's rest api


#HEADERS
def dash_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {DASH_REDIS_TOKEN}"}


#TEXT ARGUMENTS
#upstash takes every part of a command as text, numbers included
def text_arguments(arguments: list) -> list[str]:
    texts: list[str] = []

    for argument in arguments:
        texts.append(str(argument))

    return texts


#RESULT
#the answer upstash gives one command, raising on the error it sent instead
def command_result(answer: dict) -> object:
    if("error" in answer):
        raise ValueError(answer["error"])

    return answer.get("result")


#COMMAND
#one command and its result, raising when the database can't be reached or refused it
def command(arguments: list, timeout: int) -> object:
    response: requests.Response = requests.post(DASH_REDIS_URL, headers=dash_headers(), json=text_arguments(arguments), timeout=timeout)

    if(response.status_code >= 400):
        raise ValueError(f"{response.status_code} {response.text[:200]}")

    return command_result(response.json())


#PIPELINE
#many commands in one request, run in order, with every result in that order
def pipeline(commands: list[list], timeout: int = WRITE_TIMEOUT) -> list:
    body: list[list[str]] = []

    for arguments in commands:
        body.append(text_arguments(arguments))

    response: requests.Response = requests.post(f"{DASH_REDIS_URL}/pipeline", headers=dash_headers(), json=body, timeout=timeout)

    if(response.status_code >= 400):
        raise ValueError(f"{response.status_code} {response.text[:200]}")

    results: list = []

    for answer in response.json():
        results.append(command_result(answer))

    #a lifetime that went on file needs no setting again while this server runs
    for arguments in body:
        if(arguments[0] == "EXPIRE"):
            TIMED_KEYS.add(arguments[1])

    return results



#**********BACKGROUND**********
#hands every write to the worker, so the dashboard can never slow down or break a reply


#RUN WORK
#a write that failed is only printed, the bot never hears about it
def run_work(work: Callable[..., None], inputs: tuple) -> None:
    try:
        work(*inputs)

    except Exception as error:
        print(f"DASHBOARD ERROR: {work.__name__} failed, {error}")


#IN BACKGROUND
#the work waits its turn on the worker, nothing runs while the dashboard keys are missing
def in_background(work: Callable[..., None], *inputs) -> None:
    if(not ENABLED):
        return

    WORKER.submit(run_work, work, inputs)



#**********STATS**********
#every count is kept by the hour of its day, the day of its month and the month of its year, each with its total,
#so the overview reads a whole day, month or year back in one command


#NOW
#milliseconds, the way the dashboard's browser code reads time
def now_ms() -> int:
    return int(time.time() * 1000)


#SHOP PLACES
#where a moment falls in the shop's timezone, so a day's counts start at the shop's midnight
def shop_places(at: int) -> dict[str, str]:
    local_time: datetime = datetime.fromtimestamp(at / 1000, open_dates.SHOP_TIMEZONE)

    return {"day": local_time.strftime("%Y-%m-%d"), "hour": local_time.strftime("%H"), "month": local_time.strftime("%Y-%m"), "date": local_time.strftime("%d"), "year": local_time.strftime("%Y"), "month_number": local_time.strftime("%m")}


#LIFETIME
#a stats key gets its lifetime the first time this server writes it, and every later write leaves it be
def lifetime_commands(key: str, seconds: int) -> list[list]:
    if(key in TIMED_KEYS):
        return []

    return [["EXPIRE", key, seconds]]


#COUNT
#adds to the day by its hour, the month by its day and the year by its month, and to each one's total
def count_commands(field: str, amount: int, at: int) -> list[list]:
    places: dict[str, str] = shop_places(at)

    levels: list[tuple[str, str, int]] = [(f"day:{places['day']}", places["hour"], DAY_SECONDS), (f"month:{places['month']}", places["date"], MONTH_SECONDS), (f"year:{places['year']}", places["month_number"], YEAR_SECONDS)]

    commands: list[list] = []

    for key, part, seconds in levels:
        commands.append(["HINCRBY", key, field, amount])

        commands.append(["HINCRBY", key, f"{field}@{part}", amount])

        commands.extend(lifetime_commands(key, seconds))

    return commands


#COUNT PEOPLE
#the customer goes in the hour's, day's, month's and year's set, and each set they weren't in yet counts them once there,
#so ten texts from one person are still one person in every bar and every total
def people_commands(direction: str, id: str, at: int) -> list[list]:
    places: dict[str, str] = shop_places(at)

    day_key: str = f"day:{places['day']}"

    month_key: str = f"month:{places['month']}"

    year_key: str = f"year:{places['year']}"

    field: str = f"d{direction}"

    #each set, how long it stays, and the counts a first time in it adds one to
    levels: list[tuple[str, int, list[tuple[str, str]]]] = [
        (f"hour:{places['day']}T{places['hour']}:{direction}", HOUR_SECONDS, [(day_key, f"{field}@{places['hour']}")]),
        (f"{day_key}:{direction}", DAY_SECONDS, [(day_key, field), (month_key, f"{field}@{places['date']}")]),
        (f"{month_key}:{direction}", MONTH_SECONDS, [(month_key, field), (year_key, f"{field}@{places['month_number']}")]),
        (f"{year_key}:{direction}", YEAR_SECONDS, [(year_key, field)]),
    ]

    adds: list[list] = []

    #where each set's SADD sits, since a set that already has its lifetime has no EXPIRE after it
    positions: list[int] = []

    for level in levels:
        positions.append(len(adds))

        adds.append(["SADD", level[0], id])

        adds.extend(lifetime_commands(level[0], level[1]))

    added: list = pipeline(adds)

    commands: list[list] = []

    for position, level in zip(positions, levels, strict=True):
        #SADD answers 1 only the first time they go in the set
        if(added[position] == 1):
            for key, count_field in level[2]:
                commands.append(["HINCRBY", key, count_field, 1])

            #the conversation's ledger notes the set, so deleting it in the dashboard takes them back out of it
            commands.append(["SADD", f"ledger_sets:{id}", level[0]])

    return commands



#**********LEDGER**********
#each conversation keeps what it added to the overview, so deleting it in the dashboard takes back exactly that (api/thread.ts)


#LEDGER
#every count the write adds goes in the conversation's ledger by the hash and field it went in ("day:2026-10-29|in@14"),
#the people sets it joined are already noted by people_commands, and both stay as long as the year counts they point into
def ledger_commands(id: str, commands: list[list]) -> list[list]:
    ledger: list[list] = []

    for each in commands:
        if(each[0] == "HINCRBY" and str(each[1]).startswith(COUNT_KEY_STARTS)):
            ledger.append(["HINCRBY", f"ledger:{id}", f"{each[1]}|{each[2]}", each[3]])

    noted_sets: bool = any(each[0] == "SADD" and each[1] == f"ledger_sets:{id}" for each in commands)

    if(len(ledger) > 0 or noted_sets):
        ledger.extend([["EXPIRE", f"ledger:{id}", YEAR_SECONDS], ["EXPIRE", f"ledger_sets:{id}", YEAR_SECONDS]])

    return ledger



#**********THREADS**********
#each conversation's entries in order, its one line summary, and the list of conversations each tab shows, newest first


#ENTRY
#the entry goes on the end of their thread, which keeps its newest, and the dashboard sees something changed
def entry_commands(id: str, entry: dict) -> list[list]:
    return [["RPUSH", f"thread:{id}", json.dumps(entry, ensure_ascii=False)], ["LTRIM", f"thread:{id}", -THREAD_MAX, -1], ["EXPIRE", f"thread:{id}", CONVO_SECONDS], ["INCR", "version"]]


#SUMMARY
#every conversation's summary sits in one hash, so a whole tab's list reads back in one command, empty for one the dashboard never saw
#only this worker ever writes a summary, so reading it and writing it back never loses a change
def convo_summary(id: str) -> dict:
    summary_text: object = command(["HGET", "summaries", id], WRITE_TIMEOUT)

    if(not isinstance(summary_text, str)):
        return {}

    return json.loads(summary_text)


#TAB OF
#the tab a channel shows under, forms for a channel the dashboard doesn't know yet
def tab_of(channel: str) -> str:
    return TABS.get(channel, "forms")


#CONVO
#the conversation moves to the top of its tab with its newest message, a year without one takes it off the tab
#the summary comes in already read, since what it says also decides what gets counted
def convo_commands(summary: dict, id: str, channel: str, at: int, kind: str, preview: str) -> list[list]:
    #a conversation with no summary yet is new, even for someone whose old one got deleted in the dashboard
    new_convo: bool = not summary.get("tab")

    #the channel they first came in on picks the tab for good
    if(new_convo):
        summary["tab"] = tab_of(channel)

        summary["first_at"] = at

    #an instagram or messenger name gets looked up once per conversation, and not again on every message after a lookup meta refused
    #a failed lookup gives back their id, which never gets kept
    if(not summary.get("name") and channel in NAMED_CHANNELS and (new_convo or id not in NAMES_LOOKED_UP)):
        NAMES_LOOKED_UP.add(id)

        looked_up: str = username.username(id, channel)

        if(looked_up != id):
            summary["name"] = looked_up

    summary.update({"id": id, "channel": channel, "last_at": at, "last_kind": kind, "last_text": preview[:PREVIEW_CHARS]})

    tab: str = summary["tab"]

    return [["HSET", "summaries", id, json.dumps(summary, ensure_ascii=False)], ["ZADD", f"convos:{tab}", at, id], ["ZREMRANGEBYSCORE", f"convos:{tab}", "-inf", at - CONVO_SECONDS * 1000]]


#PREVIEW
#the first text of the entry, or what kind of thing it was when it had none
def entry_preview(parts: list[dict]) -> str:
    for part in parts:
        if(part.get("text")):
            return part["text"]

    for part in parts:
        if(part.get("media")):
            return part["media"].get("caption") or "Sent media"

    return ""



#**********MEDIA**********
#keeps a copy of each pic for a month, since the channel's own link to it stops working, a video stays a link


#SMALL PIC
#the pic as a smaller jpeg turned the way the phone took it, with its width and height so the dashboard saves its space before it loads
#None when the bytes aren't a pic
def small_pic(media_bytes: bytes) -> tuple[bytes, int, int] | None:
    try:
        image: Image.Image = Image.open(io.BytesIO(media_bytes))

        image = ImageOps.exif_transpose(image).convert("RGB")

        image.thumbnail((PIC_MAX_SIDE, PIC_MAX_SIDE))

        buffer: io.BytesIO = io.BytesIO()

        image.save(buffer, format="JPEG", quality=PIC_QUALITY, optimize=True)

    #a video or a broken file only means there's no pic to keep
    except Exception:
        return None

    return (buffer.getvalue(), image.width, image.height)


#OPEN MEDIA
#the download with only its headers read, so a video is known before its body ever comes down, None when it failed
def open_media(url: str) -> requests.Response | None:
    try:
        http_response: requests.Response = requests.get(url, timeout=30, stream=True)

        http_response.raise_for_status()

    except requests.RequestException as error:
        print(f"DASHBOARD MEDIA ERROR: download failed, {error}")

        return None

    return http_response


#KEPT MEDIA
#a pic gets its copy kept, a video or anything too big stays its own link, and so does anything that still won't download or open after every try
def kept_media(source: dict) -> dict:
    url: str = source.get("url", "")

    caption: str = source.get("caption", "")

    #a reel or a shared link with no url has only its title to show
    if(url == ""):
        return {"kind": "post", "caption": caption}

    for attempt in range(MEDIA_TRIES):
        #a failed try waits a moment first, instagram's link can take a few seconds to start working
        if(attempt > 0):
            time.sleep(MEDIA_RETRY_SECONDS)

        http_response: requests.Response | None = open_media(url)

        if(http_response is None):
            continue

        with http_response:
            content_type: str = http_response.headers.get("Content-Type", "")

            if(content_type.startswith("video/")):
                return {"kind": "video", "url": url, "caption": caption}

            if(int(http_response.headers.get("Content-Length") or 0) > PIC_MAX_BYTES):
                return {"kind": "link", "url": url, "caption": caption}

            #the body comes down here, and a connection that drops partway is one more failed try
            try:
                media_bytes: bytes = http_response.content

            except requests.RequestException as error:
                print(f"DASHBOARD MEDIA ERROR: download broke off, {error}")

                continue

        pic: tuple[bytes, int, int] | None = small_pic(media_bytes)

        if(pic is None):
            print(f"DASHBOARD MEDIA ERROR: try {attempt + 1} didn't open as a pic, {content_type}, {len(media_bytes)} bytes")

            continue

        media_id: str = secrets.token_hex(16)

        command(["SET", f"media:{media_id}", base64.b64encode(pic[0]).decode("utf-8"), "EX", MEDIA_SECONDS], WRITE_TIMEOUT)

        return {"kind": "pic", "id": media_id, "width": pic[1], "height": pic[2], "caption": caption}

    return {"kind": "link", "url": url, "caption": caption}


#MEDIA PART
#a pic, video or post as its own part of the entry
def media_part(source: dict) -> dict:
    return {"media": kept_media(source)}



#**********INCOMING**********
#every message a customer sends shows up in the dashboard the moment it lands, before the bot batches it, unless the bot will never answer them


#ATTACHMENT SOURCE
#where one attachment lives and its title, blooio puts the url on the item, instagram and messenger in the payload
def attachment_source(item: dict) -> dict:
    payload: dict = item.get("payload") or {}

    url: str = item.get("url") or payload.get("url") or payload.get("story_media_url") or ""

    return {"url": url, "caption": payload.get("title") or ""}


#AD SOURCE
#the ad they wrote in from, its photo or video and its title
def ad_source(referral: dict) -> dict:
    data: dict = referral.get("ads_context_data") or {}

    url: str = data.get("photo_url") or data.get("video_url") or ""

    caption: str = "Ad"

    if(data.get("ad_title")):
        caption = f"Ad: {data['ad_title']}"

    return {"url": url, "caption": caption}


#MESSAGE SOURCES
#one message as it came in, [text, attachments, referral] or a quote form's lines, split into its texts and its media
def message_sources(message: list) -> tuple[list[str], list[dict]]:
    texts: list[str] = []

    sources: list[dict] = []

    for element in message:
        if(isinstance(element, str) and element.strip() != ""):
            texts.append(element.strip())

        elif(isinstance(element, list)):
            for item in element:
                if(isinstance(item, dict)):
                    sources.append(attachment_source(item))

        elif(isinstance(element, dict) and element):
            sources.append(ad_source(element))

    return (texts, sources)


#RESTRICTED
#the bot's restricted state, set while a person has the conversation and the bot only answers a few things, or for good when the owner had them before the bot showed up
#a read that fails counts them as free, so the message still shows
def restricted_state(id: str) -> dict | str:
    try:
        return log.read_state(f"restricted_{id}")

    except Exception as error:
        print(f"DASHBOARD ERROR: restricted check failed for {id}, {error}")

        return {}


#WRITE INCOMING
#their message goes in their thread, marked when they were switched off
#it only counts toward the day's inbound when it was the system's to answer, so a customer switched off or one a person has never moves the numbers
#the summary keeps which it was, so the replies and hand offs that answer it count the same way
def write_incoming(id: str, channel: str, texts: list[str], sources: list[dict], at: int, switched: bool, counted: bool) -> None:
    parts: list[dict] = []

    #a quote form's lines read as one message
    if(len(texts) > 0):
        parts.append({"text": "\n".join(texts)})

    for source in sources:
        parts.append(media_part(source))

    entry: dict = {"at": at, "kind": "in", "parts": parts}

    if(not switched):
        entry["off"] = True

    commands: list[list] = entry_commands(id, entry)

    summary: dict = convo_summary(id)

    summary["counted"] = counted

    commands.extend(convo_commands(summary, id, channel, at, "in", entry_preview(parts)))

    if(counted):
        commands.extend(count_commands("in", 1, at))

        commands.extend(people_commands("in", id, at))

    commands.extend(ledger_commands(id, commands))

    pipeline(commands)


#TAKE IN
#every message they send shows in the dashboard, True when they and their channel are switched on so it goes on to the bot
#except anyone the bot will never answer: the owner's from before the bot, or switched off on an ON_ONLY_CHANNELS channel
def take_in(id: str, channel: str, message: list) -> bool:
    switched: bool = switched_on(id, channel)

    #the bot's not touching this one, so on instagram it stays off the board entirely instead of piling up as off messages
    if(not switched and channel in ON_ONLY_CHANNELS):
        return switched

    #read the moment it lands, the same as the bot reads it
    restricted: dict | str = restricted_state(id)

    #the owner had them before the bot showed up, so the bot never says a word and the board never hears of them either
    if(restricted == owner.CONVO_STATE):
        return switched

    #switched off or a person having them keeps it off the numbers
    counted: bool = switched and not restricted

    #read right away, the batch the message joins keeps growing after this
    #a message shaped some way the dashboard doesn't expect still goes on to the bot, it only misses the dashboard
    try:
        texts, sources = message_sources(message)

    except Exception as error:
        print(f"DASHBOARD ERROR: message_sources failed, {error}")

        return switched

    in_background(write_incoming, id, channel, texts, sources, now_ms(), switched, counted)

    return switched



#**********FORGET**********
#someone the bot turns out to never answer comes off the board, the same way deleting them in the dashboard does it (api/thread.ts)


#TAKE BACK
#what their conversation added to the overview comes back off, keep in step with take_back_commands in api/thread.ts
#upstash gives the ledger back as place, amount, place, amount, and a count hash that already aged out gets skipped so an old day never goes negative
def take_back_commands(id: str) -> list[list]:
    ledger, ledger_sets = pipeline([["HGETALL", f"ledger:{id}"], ["SMEMBERS", f"ledger_sets:{id}"]])

    counts: list[tuple[str, str, int]] = []

    #places look like "day:2026-10-29|in@14"
    for position in range(0, len(ledger or []) - 1, 2):
        place: str = str(ledger[position])

        cut: int = place.rfind("|")

        amount: int = int(ledger[position + 1])

        if(cut > 0 and amount != 0):
            counts.append((place[:cut], place[cut + 1:], amount))

    hash_keys: list[str] = list(dict.fromkeys(count[0] for count in counts))

    live: set[str] = set()

    if(len(hash_keys) > 0):
        found: list = pipeline([["EXISTS", key] for key in hash_keys])

        live = {key for key, exists in zip(hash_keys, found) if int(exists) == 1}

    commands: list[list] = [["HINCRBY", key, field, -amount] for key, field, amount in counts if key in live]

    commands.extend(["SREM", key, id] for key in ledger_sets or [])

    commands.append(["DEL", f"ledger:{id}", f"ledger_sets:{id}"])

    return commands


#PIC KEYS
#the kept copy of every pic in their thread, an entry that can't be read has none
def pic_keys(entries: list) -> list[str]:
    keys: list[str] = []

    for entry in entries or []:
        try:
            parts: list = json.loads(entry).get("parts") or []

        except (AttributeError, TypeError, ValueError):
            continue

        for part in parts:
            media: dict = (part.get("media") or {}) if isinstance(part, dict) else {}

            if(media.get("kind") == "pic" and media.get("id")):
                keys.append(f"media:{media['id']}")

    return keys


#WRITE FORGET
#their thread, pics, summary and counts all come off, their switch stays as it is
#only someone the bot never answered gets here, so there's no follow up of theirs to take off
def write_forget(id: str) -> None:
    entries: object = command(["LRANGE", f"thread:{id}", 0, -1], WRITE_TIMEOUT)

    commands: list[list] = take_back_commands(id)

    commands.extend([["DEL", f"thread:{id}", f"state:{id}", f"writer:{id}", *pic_keys(entries)], ["HDEL", "summaries", id], ["HDEL", "flagged", id]])

    commands.extend(["ZREM", f"convos:{tab}", id] for tab in sorted(set(TABS.values())))

    commands.append(["INCR", "version"])

    pipeline(commands)


#FORGET
#waits behind the writes that put their messages on the board, so it takes those off too
def forget(id: str) -> None:
    in_background(write_forget, id)



#**********OUTGOING**********
#every text that goes out to a customer shows up in their thread with the pics that went with it


#HAS PRICE
#the same test the bot uses to know they've seen a price (replies.write_price_sent), a $ anywhere in what went out
def has_price(texts: list[str]) -> bool:
    for text in texts:
        if("$" in text):
            return True

    return False


#WRITE OUTGOING
#each text is its own part with its pics right after it, the way the customer got them
#from_ghl is a text sent from ghl itself, which shows in their thread but was never the system's reply, and sms is a follow up that went out from the shop's ghl number
def write_outgoing(id: str, channel: str, texts: list[str], attachments: dict[int, list[str]], at: int, sent: bool, is_followup: bool, from_ghl: bool, sms: bool) -> None:
    parts: list[dict] = []

    for position, text in enumerate(texts):
        parts.append({"text": text})

        for url in attachments.get(position, []):
            parts.append(media_part({"url": url, "caption": ""}))

    entry: dict = {"at": at, "kind": "out", "parts": parts}

    #a text sent from ghl shows as a person's in their thread, not the system's
    if(from_ghl):
        entry["ghl"] = True

    #an sms follow up came from the shop's ghl number, not hazel's line, so it shows in green in their thread
    if(sms):
        entry["sms"] = True

    #the customer may have gotten none of it, so it shows as failed and never counts as outbound
    if(not sent):
        entry["failed"] = True

    commands: list[list] = entry_commands(id, entry)

    summary: dict = convo_summary(id)

    #a reply to a message that wasn't the system's to answer doesn't count either
    if(sent and summary.get("counted", True)):
        #a follow up is the system reaching out on its own and a text from ghl is a person, so neither counts as the system replying
        if(not is_followup and not from_ghl):
            commands.extend(count_commands("out", 1, at))

            commands.extend(people_commands("out", id, at))

        #the customer got a price, the step before booking, counted once per customer
        if(has_price(texts)):
            commands.extend(people_commands("quoted", id, at))

    commands.extend(convo_commands(summary, id, channel, at, "out", entry_preview(parts)))

    commands.extend(ledger_commands(id, commands))

    pipeline(commands)


#LOG OUTGOING
#sent is False when the channel refused any of the texts, is_followup is True for a follow up rather than a reply, from_ghl is True for a text sent from ghl, sms is True for a follow up sent from the shop's ghl number
def log_outgoing(id: str, channel: str, texts: list[str], attachments: dict[int, list[str]] | None, sent: bool, is_followup: bool, from_ghl: bool = False, sms: bool = False) -> None:
    in_background(write_outgoing, id, channel, list(texts), dict(attachments or {}), now_ms(), sent, is_followup, from_ghl, sms)



#**********SWITCH**********
#a customer switched off in the dashboard gets nothing at all from the bot, not even a hold reply, and so does everyone on a tab switched off there, and the owner texting them from ghl switches them off the same way


#SWITCHED ON
#False once the dashboard switched them or their whole tab off, both read in one request
#the last answers stand in when it can't be reached, and anyone or any tab it never answered for stays on
def switched_on(id: str, channel: str) -> bool:
    if(not ENABLED):
        return True

    tab: str = tab_of(channel)

    try:
        answers: list = pipeline([["SISMEMBER", "off", id], ["SISMEMBER", "off_tabs", tab]], SWITCH_TIMEOUT)

    except Exception as error:
        print(f"DASHBOARD SWITCH ERROR: {error}, {id} and the {tab} tab stay where the dashboard last had them")

        return LAST_SWITCH.get(id, True) and LAST_TAB_SWITCH.get(tab, True)

    LAST_SWITCH[id] = answers[0] != 1

    LAST_TAB_SWITCH[tab] = answers[1] != 1

    return LAST_SWITCH[id] and LAST_TAB_SWITCH[tab]


#SWITCH OFF
#the owner texted them from ghl, so they go off the same as switching them off in the dashboard, with a note in their thread that ghl did it
#written right away rather than in the background, so a batch of theirs already counting down reads them off
def switch_off(id: str) -> None:
    #the answer the bot falls back on when the dashboard can't be reached, so they stay off then too
    LAST_SWITCH[id] = False

    if(not ENABLED):
        return

    commands: list[list] = [["SADD", "off", id]]

    commands.extend(entry_commands(id, {"at": now_ms(), "kind": "switch", "on": False, "by": "ghl"}))

    #it sits in front of his text going out, so it gives up as fast as the on or off check
    pipeline(commands, SWITCH_TIMEOUT)



#**********HAND OFFS**********
#the owner got texted to take a conversation, so it shows in their thread and counts toward the hils or booked jobs


#WRITE HAND OFF
#each customer counts once too, so the overview can say what share of the people who messaged needed a person or booked
def write_hand_off(id: str, kind: str, reason: str, at: int) -> None:
    commands: list[list] = entry_commands(id, {"at": at, "kind": kind, "reason": reason})

    #a hand off while a person already has them was never the system's to count
    if(convo_summary(id).get("counted", True)):
        commands.extend(count_commands(kind, 1, at))

        commands.extend(people_commands(kind, id, at))

    commands.extend(ledger_commands(id, commands))

    pipeline(commands)


#LOG HAND OFF
#kind is BOOKED for a schedule request and HIL for every other hand off
def log_hand_off(id: str, kind: str, reason: str) -> None:
    in_background(write_hand_off, id, kind, reason, now_ms())



#**********FOLLOW UPS**********
#who the system follows up with and when: the morning's list the night picks, one line per conversation, every follow up that went out, and everyone blooio holds till they answer


#WRITE FOLLOW UP PICKED
#they go on the morning's list with when theirs goes out, the channel it goes out on and which follow up in a row it is
def write_followup_picked(id: str, channel: str, number: int, due_at: int) -> None:
    due: str = json.dumps({"at": due_at, "channel": channel, "number": number}, ensure_ascii=False)

    pipeline([["HSET", "followups:due", id, due], ["INCR", "version"]])


#LOG FOLLOW UP PICKED
#due_at is the morning's send in seconds, the way the follow ups keep time
def log_followup_picked(id: str, channel: str, number: int, due_at: float) -> None:
    in_background(write_followup_picked, id, channel, number, int(due_at * 1000))


#WRITE FOLLOW UP DROPPED
def write_followup_dropped(id: str) -> None:
    pipeline([["HDEL", "followups:due", id], ["INCR", "version"]])


#LOG FOLLOW UP DROPPED
#they wrote in before theirs went out, so they come off the morning's list
def log_followup_dropped(id: str) -> None:
    in_background(write_followup_dropped, id)


#WRITE FOLLOW UP SENT
#theirs went out, so they come off the morning's list and it joins the ones sent, where anything older than FOLLOWUP_SECONDS comes off
#an sms one is marked so the follow ups page draws it in green
def write_followup_sent(id: str, channel: str, number: int, at: int, sms: bool) -> None:
    line: dict = {"id": id, "channel": channel, "number": number, "at": at}

    if(sms):
        line["sms"] = True

    sent: str = json.dumps(line, ensure_ascii=False)

    pipeline([["HDEL", "followups:due", id], ["ZADD", "followups:sent", at, sent], ["ZREMRANGEBYSCORE", "followups:sent", "-inf", at - FOLLOWUP_SECONDS * 1000], ["INCR", "version"]])


#LOG FOLLOW UP SENT
#number is which follow up in a row it was, counted since they last wrote, sms is True for one sent from the shop's ghl number
def log_followup_sent(id: str, channel: str, number: int, sms: bool = False) -> None:
    in_background(write_followup_sent, id, channel, number, now_ms(), sms)


#DUE BY
#the ids on the morning's list whose follow up was due by at, or on the held list held by then, upstash gives either back as id, line, id, line
#a line that can't be read counts as due, so it comes off too
def due_by(due_list: object, at: int) -> list[str]:
    past: list[str] = []

    if(not isinstance(due_list, list)):
        return past

    for position in range(0, len(due_list) - 1, 2):
        try:
            due_at: int = int(json.loads(due_list[position + 1]).get("at", 0))

        except (AttributeError, TypeError, ValueError):
            due_at = 0

        if(due_at <= at):
            past.append(due_list[position])

    return past


#WRITE PAST FOLLOW UPS
#every follow up due by now either went out, and already moved to the ones sent, or got called off, so none of them stays on the list
def write_past_followups(at: int) -> None:
    past: list[str] = due_by(command(["HGETALL", "followups:due"], WRITE_TIMEOUT), at)

    if(len(past) > 0):
        pipeline([["HDEL", "followups:due", *past], ["INCR", "version"]])


#CLEAR PAST FOLLOW UPS
#runs after the morning's send and before the night's pick, so a follow up called off, or a morning the server missed, never stays on the list
def clear_past_followups() -> None:
    in_background(write_past_followups, now_ms())


#WRITE FOLLOW UP HELD
#blooio turned theirs down for the chat's cap, so they come off the morning's list and go on the held ones till they text back or react
#anyone held longer ago than the page looks back comes off first, the way the follow ups that went out do
def write_followup_held(id: str, channel: str, at: int) -> None:
    held: str = json.dumps({"at": at, "channel": channel}, ensure_ascii=False)

    stale: list[str] = due_by(command(["HGETALL", "followups:held"], WRITE_TIMEOUT), at - FOLLOWUP_SECONDS * 1000)

    commands: list[list] = [["HDEL", "followups:due", id]]

    if(len(stale) > 0):
        commands.append(["HDEL", "followups:held", *stale])

    commands.extend([["HSET", "followups:held", id, held], ["INCR", "version"]])

    pipeline(commands)


#LOG FOLLOW UP HELD
def log_followup_held(id: str, channel: str) -> None:
    in_background(write_followup_held, id, channel, now_ms())


#WRITE FOLLOW UP RELEASED
def write_followup_released(id: str) -> None:
    pipeline([["HDEL", "followups:held", id], ["INCR", "version"]])


#LOG FOLLOW UP RELEASED
#they texted back or reacted, so blooio takes texts to them again and they come off the held ones
def log_followup_released(id: str) -> None:
    in_background(write_followup_released, id)



#**********HEARTBEAT**********
#the server checks in every few minutes while it runs, so the overview shows whether the system is up


#REMEMBER SWITCHES
#the dashboard's whole off list as it is right now, so switched_on falls back on it when the dashboard can't be reached
def remember_switches(off_ids: object) -> None:
    if(not isinstance(off_ids, list)):
        return

    off: set[str] = set(off_ids)

    #someone switched back on since their last check
    for id in list(LAST_SWITCH):
        LAST_SWITCH[id] = id not in off

    for id in off:
        LAST_SWITCH[id] = False


#REMEMBER TAB SWITCHES
#the tabs switched off right now, every tab not on the list is on
def remember_tab_switches(off_tabs: object) -> None:
    if(not isinstance(off_tabs, list)):
        return

    for tab in set(TABS.values()):
        LAST_TAB_SWITCH[tab] = tab not in off_tabs


#WRITE BEAT
#notes when the bot was last seen and the commit it runs, and reads back both off lists
def write_beat(at: int) -> None:
    #the off lists go first, so their answers are always the first two results
    commands: list[list] = [["SMEMBERS", "off"], ["SMEMBERS", "off_tabs"], ["SET", "up_last", at]]

    #a server run off render has no commit, so it never covers up the one render is running
    if(UP_COMMIT != ""):
        commands.append(["SET", "up_commit", UP_COMMIT])

    results: list = pipeline(commands)

    remember_switches(results[0])

    remember_tab_switches(results[1])


#BEAT
#called by the server every BEAT_SECONDS while it runs
def beat() -> None:
    in_background(write_beat, now_ms())



#**********FLAG DETAILS**********
#what a flagged conversation's email shows, the state the bot wrote the reply from and who the customer is


#WRITE STATE
def write_state(id: str, state_text: str) -> None:
    command(["SET", f"state:{id}", state_text, "EX", STATE_SECONDS], WRITE_TIMEOUT)


#NOTE STATE
#the state a reply gets written from, turned to text right away since the chain can still change it
def note_state(id: str, state: dict) -> None:
    if(not ENABLED):
        return

    #a state that won't turn into text only misses the flag email, the reply still gets written
    try:
        state_text: str = json.dumps({"at": now_ms(), "state": state}, ensure_ascii=False, default=str)

    except (TypeError, ValueError) as error:
        print(f"DASHBOARD ERROR: state note failed, {error}")

        return

    in_background(write_state, id, state_text)


#WRITE NAME
#the form comes in before the bot answers it, so its summary is already on file to put the name on
def write_name(id: str, name: str) -> None:
    summary: dict = convo_summary(id)

    summary["name"] = name

    pipeline([["HSET", "summaries", id, json.dumps(summary, ensure_ascii=False)], ["INCR", "version"]])


#NAME CONVO
#the name the conversation shows under, like the full name off a quote form
def name_convo(id: str, name: str) -> None:
    if(name.strip() == ""):
        return

    in_background(write_name, id, name.strip())



#**********UPVOTE DETAILS**********
#what an upvote in the dashboard writes its example from, the generator that wrote the reply, what it was handed and the reply it wrote


#WRITE WRITER
def write_writer(id: str, writer_text: str) -> None:
    command(["SET", f"writer:{id}", writer_text, "EX", STATE_SECONDS], WRITE_TIMEOUT)


#NOTE WRITER
#generator is the prompt file that wrote the reply, "" when only the code did, kept as long as the state it was written from
def note_writer(id: str, generator: str, generator_input: str, reply: str) -> None:
    if(not ENABLED):
        return

    writer_text: str = json.dumps({"at": now_ms(), "generator": generator, "input": generator_input, "reply": reply}, ensure_ascii=False)

    in_background(write_writer, id, writer_text)
