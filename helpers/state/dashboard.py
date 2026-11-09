#IMPORTS

import base64
import io
import json
import os
import secrets
import time
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


#GLOBALS

load_dotenv()

#the dashboards own upstash, so its polling and pics never use up the systems, empty till set
DASH_REDIS_URL: str = os.getenv("DASH_REDIS_URL", "").rstrip("/")

DASH_REDIS_TOKEN: str = os.getenv("DASH_REDIS_TOKEN", "")

ENABLED: bool = DASH_REDIS_URL != "" and DASH_REDIS_TOKEN != ""

#the on or off check sits in front of every reply, so it bails fast and replies keep going
SWITCH_TIMEOUT: int = 3

#every write runs off the reply path, so it can wait a little longer
WRITE_TIMEOUT: int = 10

#each channels tab, texts sit under forms since every form lead gets answered by text anyway
TABS: dict[str, str] = {"blooio": "forms", "ig": "instagram", "messenger": "messenger", "meta-form": "forms", "website-form": "forms"}

#only instagram and messenger ids need a lookup to read as a name, a text id is already their number
NAMED_CHANNELS: list[str] = ["ig", "messenger"]

#channels where anyone switched off, or on a switched off tab, never even makes the board
ON_ONLY_CHANNELS: list[str] = ["ig"]

#a thread keeps its newest entries and stays a year past its last message
THREAD_MAX: int = 500

CONVO_SECONDS: int = 365 * 86400

#day and month counts keep a bit over a year, year counts over two, the hour sets two days
DAY_SECONDS: int = 400 * 86400

MONTH_SECONDS: int = 400 * 86400

YEAR_SECONDS: int = 800 * 86400

HOUR_SECONDS: int = 2 * 86400

#the copied pics and the states replies were written from stay a month
MEDIA_SECONDS: int = 30 * 86400

STATE_SECONDS: int = 30 * 86400

#sent follow ups and holds stay the pages two weeks plus a day, so its oldest day is whole
FOLLOWUP_SECONDS: int = 15 * 86400

#the overviews count hashes start like this, and the ledger notes every write into them
COUNT_KEY_STARTS: tuple[str, ...] = ("day:", "month:", "year:")

#while the server runs it checks in this often, so the overview can tell when it stops
BEAT_SECONDS: int = 300

#renders commit, tells the dashboard when an upvotes example is live, empty off render
UP_COMMIT: str = os.getenv("RENDER_GIT_COMMIT", "")

#big enough to read a cars color off, small enough that a month of pics fits the free plan
PIC_MAX_SIDE: int = 1024

PIC_QUALITY: int = 70

#a file bigger than this is never a phone pic, so it stays a link instead of coming down
PIC_MAX_BYTES: int = 25 * 1024 * 1024

#instagrams pic link can flake right as the message lands, so the copy gets a few tries
MEDIA_TRIES: int = 3

MEDIA_RETRY_SECONDS: int = 2

#how much of the last message the conversation list shows
PREVIEW_CHARS: int = 140

#a schedule request counts as booked, every other hand off to the owner as a hil
HIL: str = "hil"

BOOKED: str = "booked"

#one worker writes everything in order, so a slow pic never shuffles a thread
WORKER = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dashboard")

#each customers last switch answer, refilled every heartbeat so off stays off through outages
LAST_SWITCH: dict[str, bool] = {}

#same idea per tab, so a whole channel switched off stays off through an outage too
LAST_TAB_SWITCH: dict[str, bool] = {}

#ids already looked up this run, so a name meta refuses isn't asked for on every message
NAMES_LOOKED_UP: set[str] = set()

#keys this run already gave a lifetime, later writes skip the EXPIRE and spare the free plan
TIMED_KEYS: set[str] = set()


#STARTUP

register_heif_opener()

if(not ENABLED):
    print("DASHBOARD OFF: DASH_REDIS_URL or DASH_REDIS_TOKEN is not set, nothing goes to the dashboard and nobody can be switched off")


#DATABASE

#upstash wants the token as a bearer header on every request
def dash_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {DASH_REDIS_TOKEN}"}

#upstash takes every part of a command as text, numbers included
def text_arguments(arguments: list) -> list[str]:
    texts: list[str] = []

    for argument in arguments:
        texts.append(str(argument))

    return texts

#the answer upstash gives one command, raising on the error it sent instead
def command_result(answer: dict) -> object:
    if("error" in answer):
        raise ValueError(answer["error"])

    return answer.get("result")

#one command and its result, raising when the database can't be reached or refused it
def command(arguments: list, timeout: int) -> object:
    response = requests.post(DASH_REDIS_URL, headers=dash_headers(), json=text_arguments(arguments), timeout=timeout)

    if(response.status_code >= 400):
        raise ValueError(f"{response.status_code} {response.text[:200]}")

    return command_result(response.json())

#many commands in one request, run in order, with every result in that order
def pipeline(commands: list[list], timeout: int = WRITE_TIMEOUT) -> list:
    body: list[list[str]] = []

    for arguments in commands:
        body.append(text_arguments(arguments))

    response = requests.post(f"{DASH_REDIS_URL}/pipeline", headers=dash_headers(), json=body, timeout=timeout)

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


#BACKGROUND

#a failed write only gets printed, the reply side never hears about it
def run_work(work, inputs: list) -> None:
    try:
        work(*inputs)
    except Exception as error:
        print(f"DASHBOARD ERROR: {work.__name__} failed, {error}")

#the work waits its turn on the worker, nothing runs while the dashboard keys are missing
def in_background(work, inputs: list) -> None:
    if(not ENABLED):
        return

    WORKER.submit(run_work, work, inputs)


#STATS

#milliseconds, the way the dashboards browser code reads time
def now_ms() -> int:
    return int(time.time() * 1000)

#where a moment falls in the shops timezone, so a days counts start at the shops midnight
def shop_places(at: int) -> dict[str, str]:
    local_time = datetime.fromtimestamp(at / 1000, open_dates.SHOP_TIMEZONE)

    return {"day": local_time.strftime("%Y-%m-%d"), "hour": local_time.strftime("%H"), "month": local_time.strftime("%Y-%m"), "date": local_time.strftime("%d"), "year": local_time.strftime("%Y"), "month_number": local_time.strftime("%m")}

#a stats key gets its lifetime on this runs first write, later writes leave it be
def lifetime_commands(key: str, seconds: int) -> list[list]:
    if(key in TIMED_KEYS):
        return []

    return [["EXPIRE", key, seconds]]

#adds to the day by its hour, the month by its day, the year by its month, and each total
def count_commands(field: str, amount: int, at: int) -> list[list]:
    places: dict[str, str] = shop_places(at)

    levels: list[tuple[str, str, int]] = [(f"day:{places['day']}", places["hour"], DAY_SECONDS), (f"month:{places['month']}", places["date"], MONTH_SECONDS), (f"year:{places['year']}", places["month_number"], YEAR_SECONDS)]

    commands: list[list] = []

    for key, part, seconds in levels:
        commands.append(["HINCRBY", key, field, amount])

        commands.append(["HINCRBY", key, f"{field}@{part}", amount])

        commands.extend(lifetime_commands(key, seconds))

    return commands

#one set per hour, day, month and year, so ten texts from one person still count as one
def people_commands(direction: str, id: str, at: int) -> list[list]:
    places: dict[str, str] = shop_places(at)

    day_key: str = f"day:{places['day']}"

    month_key: str = f"month:{places['month']}"

    year_key: str = f"year:{places['year']}"

    field: str = f"d{direction}"

    #each set, how long it stays, and the counts a first time in it adds one to
    levels: list[tuple[str, int, list[tuple[str, str]]]] = []

    levels.append((f"hour:{places['day']}T{places['hour']}:{direction}", HOUR_SECONDS, [(day_key, f"{field}@{places['hour']}")]))

    levels.append((f"{day_key}:{direction}", DAY_SECONDS, [(day_key, field), (month_key, f"{field}@{places['date']}")]))

    levels.append((f"{month_key}:{direction}", MONTH_SECONDS, [(month_key, field), (year_key, f"{field}@{places['month_number']}")]))

    levels.append((f"{year_key}:{direction}", YEAR_SECONDS, [(year_key, field)]))

    adds: list[list] = []

    #where each sets SADD sits, since a set that already has its lifetime has no EXPIRE after it
    positions: list[int] = []

    for level in levels:
        positions.append(len(adds))

        adds.append(["SADD", level[0], id])

        adds.extend(lifetime_commands(level[0], level[1]))

    added: list = pipeline(adds)

    commands: list[list] = []

    for position, level in zip(positions, levels, strict=True):
        #only the first time in the set gets a 1 back from SADD
        if(added[position] == 1):
            for key, count_field in level[2]:
                commands.append(["HINCRBY", key, count_field, 1])

            #the ledger notes the set, so deleting the convo pulls them back out of it
            commands.append(["SADD", f"ledger_sets:{id}", level[0]])

    return commands


#LEDGER

#every count also goes in the ledger by hash and field, so a delete can take it back
def ledger_commands(id: str, commands: list[list]) -> list[list]:
    ledger: list[list] = []

    for each in commands:
        if(each[0] == "HINCRBY" and str(each[1]).startswith(COUNT_KEY_STARTS)):
            ledger.append(["HINCRBY", f"ledger:{id}", f"{each[1]}|{each[2]}", each[3]])

    #sets people_commands already noted need the ledgers lifetime too, even with no counts
    noted_sets: bool = False

    for each in commands:
        if(each[0] == "SADD" and each[1] == f"ledger_sets:{id}"):
            noted_sets = True

            break

    if(len(ledger) > 0 or noted_sets):
        ledger.extend([["EXPIRE", f"ledger:{id}", YEAR_SECONDS], ["EXPIRE", f"ledger_sets:{id}", YEAR_SECONDS]])

    return ledger


#THREADS

#the entry joins there thread, which keeps its newest, and the version bump tells the board
def entry_commands(id: str, entry: dict) -> list[list]:
    return [["RPUSH", f"thread:{id}", json.dumps(entry, ensure_ascii=False)], ["LTRIM", f"thread:{id}", -THREAD_MAX, -1], ["EXPIRE", f"thread:{id}", CONVO_SECONDS], ["INCR", "version"]]

#there summary, empty for someone new, safe to read then write since only this worker writes
def convo_summary(id: str) -> dict:
    summary_text: object = command(["HGET", "summaries", id], WRITE_TIMEOUT)

    if(not isinstance(summary_text, str)):
        return {}

    return json.loads(summary_text)

#the tab a channel shows under, forms for a channel the dashboard doesn't know yet
def tab_of(channel: str) -> str:
    return TABS.get(channel, "forms")

#the convo jumps to the top of its tab, and a year of silence takes it off
def convo_commands(summary: dict, id: str, channel: str, at: int, kind: str, preview: str) -> list[list]:
    #no summary yet means new, even if their old one got deleted in the dashboard
    new_convo: bool = not summary.get("tab")

    #the channel they first came in on picks the tab for good
    if(new_convo):
        summary["tab"] = tab_of(channel)

        summary["first_at"] = at

    #one name lookup per convo, and a no from meta isn't asked again on every message
    if(not summary.get("name") and channel in NAMED_CHANNELS and (new_convo or id not in NAMES_LOOKED_UP)):
        NAMES_LOOKED_UP.add(id)

        looked_up: str = username.username(id, channel)

        #a failed lookup hands back there id, which is no name at all
        if(looked_up != id):
            summary["name"] = looked_up

    summary.update({"id": id, "channel": channel, "last_at": at, "last_kind": kind, "last_text": preview[:PREVIEW_CHARS]})

    tab: str = summary["tab"]

    return [["HSET", "summaries", id, json.dumps(summary, ensure_ascii=False)], ["ZADD", f"convos:{tab}", at, id], ["ZREMRANGEBYSCORE", f"convos:{tab}", "-inf", at - CONVO_SECONDS * 1000]]

#the first text of the entry, or what kind of thing it was when it had none
def entry_preview(parts: list[dict]) -> str:
    for part in parts:
        if(part.get("text")):
            return part["text"]

    for part in parts:
        if(part.get("media")):
            caption: str | None = part["media"].get("caption")

            if(not caption):
                caption = "Sent media"

            return caption

    return ""


#MEDIA

#a smaller upright jpeg plus its size so the board saves room for it, None if its not a pic
def small_pic(media_bytes: bytes) -> tuple[bytes, int, int] | None:
    try:
        image = Image.open(io.BytesIO(media_bytes))

        image = ImageOps.exif_transpose(image).convert("RGB")

        image.thumbnail((PIC_MAX_SIDE, PIC_MAX_SIDE))

        buffer = io.BytesIO()

        image.save(buffer, format="JPEG", quality=PIC_QUALITY, optimize=True)
    except Exception:
        #a video or a broken file only means theres no pic to keep
        return None

    return (buffer.getvalue(), image.width, image.height)

#headers only for now, so a video gets caught before its body comes down, None when it failed
def open_media(url: str):
    try:
        http_response = requests.get(url, timeout=30, stream=True)

        http_response.raise_for_status()
    except requests.RequestException as error:
        print(f"DASHBOARD MEDIA ERROR: download failed, {error}")

        return None

    return http_response

#pics get a kept copy, videos, huge files and anything still broken after every try stay links
def kept_media(source: dict) -> dict:
    url: str = source.get("url", "")

    caption: str = source.get("caption", "")

    #a reel or a shared link with no url has only its title to show
    if(url == ""):
        return {"kind": "post", "caption": caption}

    for attempt in range(MEDIA_TRIES):
        #a failed try waits a moment first, instagrams link can take a few seconds to start working
        if(attempt > 0):
            time.sleep(MEDIA_RETRY_SECONDS)

        http_response = open_media(url)

        if(http_response is None):
            continue

        with http_response:
            content_type: str = http_response.headers.get("Content-Type", "")

            if(content_type.startswith("video/")):
                return {"kind": "video", "url": url, "caption": caption}

            content_length: str | int | None = http_response.headers.get("Content-Length")

            if(not content_length):
                content_length = 0

            if(int(content_length) > PIC_MAX_BYTES):
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

#a pic, video or post as its own part of the entry
def media_part(source: dict) -> dict:
    return {"media": kept_media(source)}


#INCOMING

#one attachments url and title, blooio keeps the url on the item, meta keeps it in the payload
def attachment_source(item: dict) -> dict:
    payload: dict | None = item.get("payload")

    if(not payload):
        payload = {}

    url: str | None = item.get("url")

    if(not url):
        url = payload.get("url")

    if(not url):
        url = payload.get("story_media_url")

    if(not url):
        url = ""

    caption: str | None = payload.get("title")

    if(not caption):
        caption = ""

    return {"url": url, "caption": caption}

#the ad they wrote in from, its photo or video and its title
def ad_source(referral: dict) -> dict:
    data: dict | None = referral.get("ads_context_data")

    if(not data):
        data = {}

    url: str | None = data.get("photo_url")

    if(not url):
        url = data.get("video_url")

    if(not url):
        url = ""

    caption: str = "Ad"

    if(data.get("ad_title")):
        caption = f"Ad: {data['ad_title']}"

    return {"url": url, "caption": caption}

#splits one raw message, or a quote forms lines, into its texts and its media
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

#their restricted state, set while a person has them, a failed read counts them as free
def restricted_state(id: str) -> dict | str:
    try:
        return log.read_state(f"restricted_{id}")
    except Exception as error:
        print(f"DASHBOARD ERROR: restricted check failed for {id}, {error}")

        return {}

#there message joins the thread, and only counts if it was the systems to answer
def write_incoming(id: str, channel: str, texts: list[str], sources: list[dict], at: int, switched: bool, counted: bool) -> None:
    parts: list[dict] = []

    #a quote forms lines read as one message
    if(len(texts) > 0):
        parts.append({"text": "\n".join(texts)})

    for source in sources:
        parts.append(media_part(source))

    entry: dict = {"at": at, "kind": "in", "parts": parts}

    if(not switched):
        entry["off"] = True

    commands: list[list] = entry_commands(id, entry)

    summary: dict = convo_summary(id)

    #kept on the summary so the replies and hand offs that answer it count the same way
    summary["counted"] = counted

    commands.extend(convo_commands(summary, id, channel, at, "in", entry_preview(parts)))

    if(counted):
        commands.extend(count_commands("in", 1, at))

        commands.extend(people_commands("in", id, at))

    commands.extend(ledger_commands(id, commands))

    pipeline(commands)

#there message hits the board, True when they and their channel are on so the system answers
def take_in(id: str, channel: str, message: list) -> bool:
    switched: bool = switched_on(id, channel)

    #the system won't touch it, so on instagram it skips the board instead of piling up
    if(not switched and channel in ON_ONLY_CHANNELS):
        return switched

    #read the moment it lands, same as the system reads it
    restricted: dict | str = restricted_state(id)

    #the owner had them first, so the system stays quiet and so does the board
    if(restricted == owner.CONVO_STATE):
        return switched

    #switched off or a person having them keeps it off the numbers
    counted: bool = switched and not restricted

    #read now since the batch keeps growing, an odd shape only misses the board, not the reply
    try:
        message_parts: tuple[list[str], list[dict]] = message_sources(message)

        texts: list[str] = message_parts[0]

        sources: list[dict] = message_parts[1]
    except Exception as error:
        print(f"DASHBOARD ERROR: message_sources failed, {error}")

        return switched

    in_background(write_incoming, [id, channel, texts, sources, now_ms(), switched, counted])

    return switched


#FORGET

#takes their numbers back off the overview, keep in step with the dashboards take_back_commands
def take_back_commands(id: str) -> list[list]:
    ledger_parts: list = pipeline([["HGETALL", f"ledger:{id}"], ["SMEMBERS", f"ledger_sets:{id}"]])

    ledger: list | None = ledger_parts[0]

    if(not ledger):
        ledger = []

    ledger_sets: list | None = ledger_parts[1]

    if(not ledger_sets):
        ledger_sets = []

    counts: list[tuple[str, str, int]] = []

    #upstash hands it back flat, place then amount, a place is hash and field split by a pipe
    for position in range(0, len(ledger) - 1, 2):
        place: str = str(ledger[position])

        cut: int = place.rfind("|")

        amount: int = int(ledger[position + 1])

        if(cut > 0 and amount != 0):
            counts.append((place[:cut], place[cut + 1:], amount))

    hash_keys: list[str] = []

    for count in counts:
        if(count[0] not in hash_keys):
            hash_keys.append(count[0])

    #a hash that already aged out gets skipped, so an old day never goes negative
    live: set[str] = set()

    if(len(hash_keys) > 0):
        exists_commands: list[list] = []

        for key in hash_keys:
            exists_commands.append(["EXISTS", key])

        found: list = pipeline(exists_commands)

        for key, exists in zip(hash_keys, found):
            if(int(exists) == 1):
                live.add(key)

    commands: list[list] = []

    for key, field, amount in counts:
        if(key in live):
            commands.append(["HINCRBY", key, field, -amount])

    for key in ledger_sets:
        commands.append(["SREM", key, id])

    commands.append(["DEL", f"ledger:{id}", f"ledger_sets:{id}"])

    return commands

#the kept copy of every pic in their thread, an entry that can't be read has none
def pic_keys(entries: list) -> list[str]:
    keys: list[str] = []

    if(not entries):
        entries = []

    for entry in entries:
        try:
            parts: list | None = json.loads(entry).get("parts")
        except (AttributeError, TypeError, ValueError):
            continue

        if(not parts):
            parts = []

        for part in parts:
            media: dict | None = None

            if(isinstance(part, dict)):
                media = part.get("media")

                if(not media):
                    media = {}
            else:
                media = {}

            if(media.get("kind") == "pic" and media.get("id")):
                keys.append(f"media:{media['id']}")

    return keys

#everything but there switch comes off, nobody here was ever answered so theres no follow up
def write_forget(id: str) -> None:
    entries: object = command(["LRANGE", f"thread:{id}", 0, -1], WRITE_TIMEOUT)

    commands: list[list] = take_back_commands(id)

    commands.extend([["DEL", f"thread:{id}", f"state:{id}", f"writer:{id}"] + pic_keys(entries), ["HDEL", "summaries", id], ["HDEL", "flagged", id]])

    for tab in sorted(set(TABS.values())):
        commands.append(["ZREM", f"convos:{tab}", id])

    commands.append(["INCR", "version"])

    pipeline(commands)

#waits behind the writes that put there messages on the board, so it takes those off too
def forget(id: str) -> None:
    in_background(write_forget, [id])


#OUTGOING

#a dollar sign anywhere means they saw a price, the same test write_price_sent uses
def has_price(texts: list[str]) -> bool:
    for text in texts:
        if("$" in text):
            return True

    return False

#each text with its pics right after it, the way the customer got them
def write_outgoing(id: str, channel: str, texts: list[str], attachments: dict[int, list[str]], at: int, sent: bool, is_followup: bool, from_ghl: bool, sms: bool) -> None:
    parts: list[dict] = []

    for position, text in enumerate(texts):
        parts.append({"text": text})

        for url in attachments.get(position, []):
            parts.append(media_part({"url": url, "caption": ""}))

    entry: dict = {"at": at, "kind": "out", "parts": parts}

    #a text sent from ghl shows as a persons in there thread, not the systems
    if(from_ghl):
        entry["ghl"] = True

    #an sms follow up came from the shops ghl number, not hazels line, so it shows green
    if(sms):
        entry["sms"] = True

    #the customer may have gotten none of it, so it shows as failed and never counts as outbound
    if(not sent):
        entry["failed"] = True

    commands: list[list] = entry_commands(id, entry)

    summary: dict = convo_summary(id)

    #a reply to a message that wasn't the systems to answer doesn't count either
    if(sent and summary.get("counted", True)):
        #a follow up is unprompted and a ghl text is a person, so neither counts as a reply
        if(not is_followup and not from_ghl):
            commands.extend(count_commands("out", 1, at))

            commands.extend(people_commands("out", id, at))

        #the customer got a price, the step before booking, counted once per customer
        if(has_price(texts)):
            commands.extend(people_commands("quoted", id, at))

    commands.extend(convo_commands(summary, id, channel, at, "out", entry_preview(parts)))

    commands.extend(ledger_commands(id, commands))

    pipeline(commands)

#sent is False when the channel refused any text, the other flags jsut say what kind it was
def log_outgoing(id: str, channel: str, texts: list[str], attachments: dict[int, list[str]] | None, sent: bool, is_followup: bool, from_ghl: bool = False, sms: bool = False) -> None:
    if(not attachments):
        attachments = {}

    in_background(write_outgoing, [id, channel, list(texts), dict(attachments), now_ms(), sent, is_followup, from_ghl, sms])


#SWITCH

#false once they or their tab got switched off, last known answers stand in when its down
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

#the owner texted them from ghl, so off they go, written now so a waiting batch sees it
def switch_off(id: str) -> None:
    #the fallback answer when the dashboard is down, so they stay off then too
    LAST_SWITCH[id] = False

    if(not ENABLED):
        return

    commands: list[list] = [["SADD", "off", id]]

    commands.extend(entry_commands(id, {"at": now_ms(), "kind": "switch", "on": False, "by": "ghl"}))

    #it sits in front of his text going out, so it gives up as fast as the on or off check
    pipeline(commands, SWITCH_TIMEOUT)


#HAND OFFS

#counted per customer too, so the overview can show what share needed a person or booked
def write_hand_off(id: str, kind: str, reason: str, at: int) -> None:
    commands: list[list] = entry_commands(id, {"at": at, "kind": kind, "reason": reason})

    #a hand off while a person already has them was never the systems to count
    if(convo_summary(id).get("counted", True)):
        commands.extend(count_commands(kind, 1, at))

        commands.extend(people_commands(kind, id, at))

    commands.extend(ledger_commands(id, commands))

    pipeline(commands)

#kind is BOOKED for a schedule request and HIL for every other hand off
def log_hand_off(id: str, kind: str, reason: str) -> None:
    in_background(write_hand_off, [id, kind, reason, now_ms()])


#FOLLOW UPS

#onto the mornings list with when, where and which follow up in a row it is
def write_followup_picked(id: str, channel: str, number: int, due_at: int) -> None:
    due: str = json.dumps({"at": due_at, "channel": channel, "number": number}, ensure_ascii=False)

    pipeline([["HSET", "followups:due", id, due], ["INCR", "version"]])

#due_at is the mornings send in seconds, the way the follow ups keep time
def log_followup_picked(id: str, channel: str, number: int, due_at: float) -> None:
    in_background(write_followup_picked, [id, channel, number, int(due_at * 1000)])

#takes them off the mornings list, and the version bump lets the board know
def write_followup_dropped(id: str) -> None:
    pipeline([["HDEL", "followups:due", id], ["INCR", "version"]])

#they wrote in before theirs went out, so they come off the mornings list
def log_followup_dropped(id: str) -> None:
    in_background(write_followup_dropped, [id])

#moves them from the mornings list to the sent ones, which drop anything past FOLLOWUP_SECONDS
def write_followup_sent(id: str, channel: str, number: int, at: int, sms: bool) -> None:
    line: dict = {"id": id, "channel": channel, "number": number, "at": at}

    #the follow ups page draws an sms one in green
    if(sms):
        line["sms"] = True

    sent: str = json.dumps(line, ensure_ascii=False)

    pipeline([["HDEL", "followups:due", id], ["ZADD", "followups:sent", at, sent], ["ZREMRANGEBYSCORE", "followups:sent", "-inf", at - FOLLOWUP_SECONDS * 1000], ["INCR", "version"]])

#number is which follow up in a row since they last wrote, sms means the shops ghl sent it
def log_followup_sent(id: str, channel: str, number: int, sms: bool = False) -> None:
    in_background(write_followup_sent, [id, channel, number, now_ms(), sms])

#ids due or held by at, upstash sends them flat as id then line, a garbled line counts as due
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

#anything due by now already went out or got called off, so it all comes off the list
def write_past_followups(at: int) -> None:
    past: list[str] = due_by(command(["HGETALL", "followups:due"], WRITE_TIMEOUT), at)

    if(len(past) > 0):
        pipeline([["HDEL", "followups:due"] + past, ["INCR", "version"]])

#runs between the morning send and the night pick, so nothing stale lingers on the list
def clear_past_followups() -> None:
    in_background(write_past_followups, [now_ms()])

#blooio capped the chat, so they move to the held list till they text back or react
def write_followup_held(id: str, channel: str, at: int) -> None:
    held: str = json.dumps({"at": at, "channel": channel}, ensure_ascii=False)

    #holds older than the page looks back get cleared out first
    stale: list[str] = due_by(command(["HGETALL", "followups:held"], WRITE_TIMEOUT), at - FOLLOWUP_SECONDS * 1000)

    commands: list[list] = [["HDEL", "followups:due", id]]

    if(len(stale) > 0):
        commands.append(["HDEL", "followups:held"] + stale)

    commands.extend([["HSET", "followups:held", id, held], ["INCR", "version"]])

    pipeline(commands)

#blooio said no to their follow up, so onto the held list they go
def log_followup_held(id: str, channel: str) -> None:
    in_background(write_followup_held, [id, channel, now_ms()])

#off the held list, and the version bump lets the board know
def write_followup_released(id: str) -> None:
    pipeline([["HDEL", "followups:held", id], ["INCR", "version"]])

#they texted back or reacted, so blooio takes texts to them again and they come off the held ones
def log_followup_released(id: str) -> None:
    in_background(write_followup_released, [id])


#HEARTBEAT

#copies the dashboards whole off list, so switched_on has a fallback during an outage
def remember_switches(off_ids: object) -> None:
    if(not isinstance(off_ids, list)):
        return

    off: set[str] = set(off_ids)

    #someone switched back on since their last check
    for id in list(LAST_SWITCH):
        LAST_SWITCH[id] = id not in off

    for id in off:
        LAST_SWITCH[id] = False

#the tabs switched off right now, every tab not on the list is on
def remember_tab_switches(off_tabs: object) -> None:
    if(not isinstance(off_tabs, list)):
        return

    for tab in set(TABS.values()):
        LAST_TAB_SWITCH[tab] = tab not in off_tabs

#notes when the system was last seen and its commit, and reads back both off lists
def write_beat(at: int) -> None:
    #the off lists go first, so their answers are always the first two results
    commands: list[list] = [["SMEMBERS", "off"], ["SMEMBERS", "off_tabs"], ["SET", "up_last", at]]

    #a server run off render has no commit, so it never covers up the one render is running
    if(UP_COMMIT != ""):
        commands.append(["SET", "up_commit", UP_COMMIT])

    results: list = pipeline(commands)

    remember_switches(results[0])

    remember_tab_switches(results[1])

#called by the server every BEAT_SECONDS while it runs
def beat() -> None:
    in_background(write_beat, [now_ms()])


#FLAG DETAILS

#parks the state for a month, in case the reply gets flagged
def write_state(id: str, state_text: str) -> None:
    command(["SET", f"state:{id}", state_text, "EX", STATE_SECONDS], WRITE_TIMEOUT)

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

    in_background(write_state, [id, state_text])

#the form lands before the system answers it, so the summary is already there for the name
def write_name(id: str, name: str) -> None:
    summary: dict = convo_summary(id)

    summary["name"] = name

    pipeline([["HSET", "summaries", id, json.dumps(summary, ensure_ascii=False)], ["INCR", "version"]])

#the name the conversation shows under, like the full name off a quote form
def name_convo(id: str, name: str) -> None:
    if(name.strip() == ""):
        return

    in_background(write_name, [id, name.strip()])


#UPVOTE DETAILS

#what wrote the reply, kept as long as the state it came from
def write_writer(id: str, writer_text: str) -> None:
    command(["SET", f"writer:{id}", writer_text, "EX", STATE_SECONDS], WRITE_TIMEOUT)

#generator is the prompt file behind the reply, empty string when the code wrote it alone
def note_writer(id: str, generator: str, generator_input: str, reply: str) -> None:
    if(not ENABLED):
        return

    writer_text: str = json.dumps({"at": now_ms(), "generator": generator, "input": generator_input, "reply": reply}, ensure_ascii=False)

    in_background(write_writer, [id, writer_text])
