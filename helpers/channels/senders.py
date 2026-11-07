#**********IMPORTS**********
#the env keys, the clock for waits, link patterns, url safe text, the shape a send comes back as, web requests that send the texts, the dashboard that shows them, and ghl that logs the ones customers get over blooio
import os
import re
import time
from typing import TypeAlias
from urllib.parse import quote

import requests

from helpers.state import dashboard
from helpers.state import ghl



#**********GLOBALS**********
#the keys, phone numbers and addresses every text goes out through, how long each wait lasts, and how long a textbelt text can run


#ACCESS TOKENS
BLOOIO_API_KEY: str = os.environ["BLOOIO_API_KEY"]

TEXTBELT_API_KEY: str = os.environ["TEXTBELT_API_KEY"]

INSTAGRAM_ACCESS_TOKEN: str = os.environ["IG_ACCESS_TOKEN"]

MESSENGER_ACCESS_TOKEN: str = os.environ["MESSENGER_ACCESS_TOKEN"]


#OWNER NUMBER
#every conversation a person has to take from here gets texted to the owner at this number, and on blooio a text from it only ever answers a color check, it never gets a reply like a customer's
OWNER_NUMBER: str = os.environ["HIL_RECIPENT"]


#DEV NUMBER
#a reply that never went out because something broke gets texted to the developer at this number
DEV_NUMBER: str = os.environ["DEV_NUMBER"]


#SEND URLS
BLOOIO_BASE_URL: str = "https://backend.blooio.com/v2/api"

TEXTBELT_SEND_URL: str = "https://textbelt.com/text"

INSTAGRAM_SEND_URL: str = "https://graph.instagram.com/v25.0/me/messages"

MESSENGER_SEND_URL: str = "https://graph.facebook.com/v25.0/me/messages"


#TYPING TIME
#the typing bubble stays up this long before the text goes out, so the customer actually sees it
TYPING_SECONDS: int = 3


#TEXT GAP
#a reply split into texts sends each one after the first this long after the one before it
TEXT_GAP_SECONDS: int = 2


#TYPING DELAY
#every typing bubble waits this long before it goes up, so it never pops up the moment a text comes in or goes out
TYPING_DELAY_SECONDS: int = 3


#META CHANNELS
#instagram and messenger send through meta's own apis, and neither chat gets a typing bubble
META_CHANNELS: list[str] = ["ig", "messenger"]


#CAP CODES
#blooio turns a text down with one of these once a chat used up the texts it takes in a row with no answer, only their text or tapback lifts it, so a retry only gets turned down again
CAP_CODES: list[str] = ["conversation_awaiting_reply", "conversation_streak_limit", "conversation_inactive_paused"]


#DELIVERY
#what a send comes back as: each text that went out in order, whether every text and pic went out, and whether blooio held the rest back for the chat's cap
DELIVERY: TypeAlias = tuple[list[str], bool, bool]


#TEXTBELT LIMIT
#textbelt turns down a text longer than this, counting an emoji as two characters
TEXTBELT_MAX_LENGTH: int = 1024


#LINK PATTERN
#a link or bare domain anywhere in an alert ("https://instagram.com/p/abc", "www.3m.com", "jake@millerplumbing.com"), which textbelt won't send on a key not cleared for links
LINK_PATTERN: re.Pattern = re.compile(r"(?:https?://|www\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.IGNORECASE)



#**********SENDING**********
#the one request every text, pic and alert goes out with on blooio, instagram and messenger


#POST MESSAGE
#every channel takes the text as json behind a bearer token, a failed send is logged and still comes back so blooio's reason can be read, None when it never got an answer
def post_message(label: str, recipient: str, send_url: str, access_token: str, payload: dict) -> requests.Response | None:
    headers: dict[str, str] = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    try:
        response: requests.Response = requests.post(send_url, headers=headers, json=payload, timeout=20)

    except Exception as error:
        print(f"[{label}] send to {recipient} errored: {error}")

        return None

    if(response.status_code >= 400):
        print(f"[{label}] send to {recipient} failed {response.status_code}: {response.text[:300]}")

    return response


#WENT OUT
#the channel answered and took the text
def went_out(response: requests.Response | None) -> bool:
    return response is not None and response.status_code < 400


#SEND MESSAGE
#one text, pic or alert, False when it failed
def send_message(label: str, recipient: str, send_url: str, access_token: str, payload: dict) -> bool:
    return went_out(post_message(label, recipient, send_url, access_token, payload))


#CHAT CAPPED
#blooio turned the text down because the chat used up the texts it takes with no answer, not because anything broke
def chat_capped(response: requests.Response | None) -> bool:
    if(response is None or response.status_code < 400):
        return False

    try:
        body: object = response.json()

    #a refusal that isn't json never names a cap
    except ValueError:
        return False

    return isinstance(body, dict) and body.get("code") in CAP_CODES



#**********INSTAGRAM SENDS**********
#sends the reply to an instagram customer through instagram's own api, text by text with its pics


#INSTAGRAM SENDER
#one text to their instagram chat, False when it failed
def send_instagram_message(recipient_id: str, text: str) -> bool:
    payload: dict = {"recipient": {"id": recipient_id}, "message": {"text": text}}

    return send_message("IG", recipient_id, INSTAGRAM_SEND_URL, INSTAGRAM_ACCESS_TOKEN, payload)


#INSTAGRAM PIC
#each pic goes out as its own message, instagram pulls it from the url, so it has to be a png or jpeg it can reach
def send_instagram_pic(recipient_id: str, url: str) -> bool:
    payload: dict = {"recipient": {"id": recipient_id}, "message": {"attachment": {"type": "image", "payload": {"url": url}}}}

    return send_message("IG", recipient_id, INSTAGRAM_SEND_URL, INSTAGRAM_ACCESS_TOKEN, payload)


#INSTAGRAM TEXTS
#texts go out in order a gap apart so they never land all at once, pics go right after the text at their position, and every text that went out comes back
def send_instagram_texts(recipient: str, texts: list[str], attachments: dict[int, list[str]] | None = None) -> DELIVERY:
    texts_sent: list[str] = []

    all_sent: bool = True

    for position, text in enumerate(texts):
        #instagram gets no typing bubble, so the gap alone spaces the texts out
        if(position > 0):
            time.sleep(TEXT_GAP_SECONDS)

        #a text that failed is logged and the rest still go out, so they get as much of the reply as can be sent
        if(send_instagram_message(recipient, text)):
            texts_sent.append(text)

        else:
            all_sent = False

        #pics go right after their text, so they show up right under it
        if(attachments and position in attachments):
            for url in attachments[position]:
                if(not send_instagram_pic(recipient, url)):
                    all_sent = False

    #instagram has no cap like blooio's, so nothing is ever held back
    return (texts_sent, all_sent, False)



#**********MESSENGER SENDS**********
#sends the reply to a messenger customer through facebook's own api, text by text with its pics


#MESSENGER SENDER
#one text to their messenger chat, False when it failed
def send_messenger_message(recipient_id: str, text: str) -> bool:
    payload: dict = {"recipient": {"id": recipient_id}, "messaging_type": "RESPONSE", "message": {"text": text}}

    return send_message("MESSENGER", recipient_id, MESSENGER_SEND_URL, MESSENGER_ACCESS_TOKEN, payload)


#MESSENGER PIC
#each pic goes out as its own message, messenger pulls it from the url, so it has to be a pic it can reach
def send_messenger_pic(recipient_id: str, url: str) -> bool:
    payload: dict = {"recipient": {"id": recipient_id}, "messaging_type": "RESPONSE", "message": {"attachment": {"type": "image", "payload": {"url": url}}}}

    return send_message("MESSENGER", recipient_id, MESSENGER_SEND_URL, MESSENGER_ACCESS_TOKEN, payload)


#MESSENGER TEXTS
#texts go out in order a gap apart so they never land all at once, pics go right after the text at their position, and every text that went out comes back
def send_messenger_texts(recipient: str, texts: list[str], attachments: dict[int, list[str]] | None = None) -> DELIVERY:
    texts_sent: list[str] = []

    all_sent: bool = True

    for position, text in enumerate(texts):
        #messenger gets no typing bubble, so the gap alone spaces the texts out
        if(position > 0):
            time.sleep(TEXT_GAP_SECONDS)

        #a text that failed is logged and the rest still go out, so they get as much of the reply as can be sent
        if(send_messenger_message(recipient, text)):
            texts_sent.append(text)

        else:
            all_sent = False

        #pics go right after their text, so they show up right under it
        if(attachments and position in attachments):
            for url in attachments[position]:
                if(not send_messenger_pic(recipient, url)):
                    all_sent = False

    #messenger has no cap like blooio's, so nothing is ever held back
    return (texts_sent, all_sent, False)



#**********TYPING BUBBLE**********
#shows the typing bubble on a text chat for a few seconds, so the reply feels like a person wrote it


#TYPING REQUEST
#a post shows the bubble and a delete takes it down, None when the request errored or failed
def typing_request(method: str, action: str, recipient: str) -> requests.Response | None:
    typing_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/typing"

    headers: dict[str, str] = {"Authorization": f"Bearer {BLOOIO_API_KEY}"}

    try:
        response: requests.Response = requests.request(method, typing_url, headers=headers, timeout=10)

    except Exception as error:
        print(f"[BLOOIO] {action} typing for {recipient} errored: {error}")

        return None

    if(response.status_code >= 400):
        print(f"[BLOOIO] {action} typing for {recipient} failed {response.status_code}: {response.text[:300]}")

        return None

    return response


#START TYPING
#puts the bubble up after a short wait, False when it failed or the chat never shows it
def start_blooio_typing(recipient: str) -> bool:
    #the wait comes before every bubble, even on an rcs chat where it never shows
    time.sleep(TYPING_DELAY_SECONDS)

    response: requests.Response | None = typing_request("post", "start", recipient)

    if(response is None):
        return False

    #an rcs chat answers with a warning and never shows the bubble, so there is nothing to wait on
    if("warning" in response.text):
        print(f"[BLOOIO] typing not shown for {recipient}: {response.text[:300]}")

        return False

    return True


#STOP TYPING
#takes the bubble down, False when the request failed
def stop_blooio_typing(recipient: str) -> bool:
    response: requests.Response | None = typing_request("delete", "stop", recipient)

    return response is not None


#SHOW TYPING
#the bubble stays up for the seconds given, False when it never showed, like on an rcs chat
def show_blooio_typing(recipient: str, seconds: int) -> bool:
    typing_started: bool = start_blooio_typing(recipient)

    #the bubble only gets its few seconds on screen when it actually started
    if(typing_started):
        time.sleep(seconds)

        stop_blooio_typing(recipient)

    return typing_started


#TYPING ON
#only a text chat over blooio has the bubble, an instagram or messenger chat gets none
def start_typing(recipient: str, channel: str) -> bool:
    if(channel in META_CHANNELS):
        return False

    return start_blooio_typing(recipient)


#TYPING OFF
#takes a text chat's bubble down, an instagram or messenger chat never had one
def stop_typing(recipient: str, channel: str) -> bool:
    if(channel in META_CHANNELS):
        return False

    return stop_blooio_typing(recipient)



#**********BLOOIO SENDS**********
#sends the reply to a text or form lead customer over blooio, each text behind a typing bubble, and logs every one that went out in ghl


#BLOOIO SENDER
#texts go out in order behind a typing bubble, pics ride along with the text at their position, and every text that went out comes back
def send_blooio_texts(recipient: str, texts: list[str], attachments: dict[int, list[str]] | None = None) -> DELIVERY:
    send_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/messages"

    texts_sent: list[str] = []

    all_sent: bool = True

    capped: bool = False

    #only what actually went out gets logged in ghl
    sent: list[ghl.SENT] = []

    for position, text in enumerate(texts):
        #the customer sees the typing bubble for a moment right before the reply goes out
        if(position == 0):
            show_blooio_typing(recipient, TYPING_SECONDS)

        #a chat with no bubble still gets the gap, so the texts never land all at once
        elif(not show_blooio_typing(recipient, TEXT_GAP_SECONDS)):
            time.sleep(TEXT_GAP_SECONDS)

        payload: dict = {"text": text}

        #pics go along with their text, so they show up right under it
        if(attachments and position in attachments):
            payload["attachments"] = attachments[position]

        response: requests.Response | None = post_message("BLOOIO", recipient, send_url, BLOOIO_API_KEY, payload)

        #blooio turns down every text to a chat that hit its cap till they text back or react, so the rest never get tried
        if(chat_capped(response)):
            all_sent = False

            capped = True

            break

        #a text that failed for any other reason is logged and the rest still go out, so they get as much of the reply as can be sent
        if(not went_out(response)):
            all_sent = False

        else:
            texts_sent.append(text)

            sent.append((text, payload.get("attachments", []), time.time()))

    #ghl never sees blooio, so every text they got goes in their conversation there too
    ghl.log_sent(recipient, sent)

    return (texts_sent, all_sent, capped)



#**********CUSTOMER SENDS**********
#sends the reply to the customer on the channel they wrote in on, in order and one at a time, and the owner's texts from ghl and the dashboard on the blooio line


#SEND ON CHANNEL
#the reply goes out where they wrote in, instagram and messenger through their own apis, a text or a form lead over blooio
def send_on_channel(recipient: str, channel: str, texts: list[str], attachments: dict[int, list[str]] | None) -> DELIVERY:
    if(channel == "ig"):
        return send_instagram_texts(recipient, texts, attachments)

    if(channel == "messenger"):
        return send_messenger_texts(recipient, texts, attachments)

    return send_blooio_texts(recipient, texts, attachments)


#SERVICE
#who carries a text on the channel, instagram and messenger themselves and blooio for a text or a form lead, so a print names who turned one down
def service_of(channel: str) -> str:
    if(channel in META_CHANNELS):
        return channel

    return "blooio"


#SEND TEXTS
#nothing reaches a customer switched off in the dashboard, or anyone on a channel switched off there, not even a reply already written, and everything that does go out shows there
#is_followup is True for the system's own follow up, which shows in their thread but never counts as a reply, and only the part of it that reached them shows
def send_texts(recipient: str, channel: str, texts: list[str], attachments: dict[int, list[str]] | None = None, is_followup: bool = False) -> DELIVERY:
    if(not dashboard.switched_on(recipient, channel)):
        print(f"SWITCHED OFF: {recipient} or their channel is off in the dashboard, so nothing was sent")

        return ([], False, False)

    texts_sent, all_sent, capped = send_on_channel(recipient, channel, texts, attachments)

    #a follow up is the shop reaching out on its own, so one that never reached them never shows in their thread, and of one that half went out only that half does
    if(is_followup):
        if(len(texts_sent) > 0):
            dashboard.log_outgoing(recipient, channel, texts_sent, None, True, True)

        return (texts_sent, all_sent, capped)

    dashboard.log_outgoing(recipient, channel, texts, attachments, all_sent, is_followup)

    return (texts_sent, all_sent, capped)


#GHL TEXT
#a text the owner sent from ghl goes out over blooio from the number the bot texts from, even to someone switched off, since a person wrote it
#no typing bubble, and never logged back in ghl where it was written, but it shows in the dashboard
def send_ghl_text(recipient: str, text: str, attachments: list[str]) -> bool:
    send_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/messages"

    payload: dict = {"text": text}

    #his pics go along with his text, the way he sent them from ghl
    if(attachments):
        payload["attachments"] = attachments

    sent: bool = send_message("GHL TEXT", recipient, send_url, BLOOIO_API_KEY, payload)

    dashboard.log_outgoing(recipient, "blooio", [text], {0: attachments}, sent, False, from_ghl=True)

    return sent


#DASHBOARD TEXT
#the owner typed it in the dashboard, but it leaves from hazel's number and lands in ghl on her channel, so nobody can tell he grabbed the wheel
def send_dashboard_text(recipient: str, text: str) -> bool:
    send_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/messages"

    #no typing bubble, he already did the typing
    sent: bool = send_message("DASHBOARD TEXT", recipient, send_url, BLOOIO_API_KEY, {"text": text})

    #ghl never sees blooio, so it goes in their conversation there like every text hazel sends
    if(sent):
        ghl.log_sent(recipient, [(text, [], time.time())])

    return sent



#**********SMS SENDS**********
#a follow up from the shop's own number in ghl once blooio is done with them, ghl keeps it in their conversation there on its own


#SMS TEXT
#nothing reaches a customer switched off in the dashboard, and one that went out shows there in green so the sms ones stand out, False when ghl turned it down
def send_sms_text(recipient: str, channel: str, contact: str, text: str) -> bool:
    if(not dashboard.switched_on(recipient, channel)):
        print(f"SWITCHED OFF: {recipient} or their channel is off in the dashboard, so nothing was sent")

        return False

    sent: bool = True

    try:
        ghl.send_sms(contact, text)

    except Exception as error:
        print(f"[GHL SMS] send to {recipient} failed: {error}")

        sent = False

    #a follow up ghl turned down never reached them, so it never shows in their thread
    if(sent):
        dashboard.log_outgoing(recipient, channel, [text], None, True, True, sms=True)

    return sent



#**********TEXTBELT SENDS**********
#texts the owner over textbelt's sms, so the hand offs and bookings he only reads land apart from the color check thread he answers on blooio


#FITTING END
#how many characters from the front of the text fit in one textbelt text, an emoji or any other character past the basic plane counts as two the way textbelt counts it
def fitting_end(text: str) -> int:
    length: int = 0

    for position, character in enumerate(text):
        length += 1

        if(ord(character) > 0xFFFF):
            length += 1

        if(length > TEXTBELT_MAX_LENGTH):
            return position

    return len(text)


#TEXTBELT PARTS
#a text too long for textbelt goes out in parts, each cut at the last space or line break that fits so no word gets split
def textbelt_parts(text: str) -> list[str]:
    parts: list[str] = []

    rest: str = text.strip()

    end: int = fitting_end(rest)

    while(end < len(rest)):
        #a space or line break right where it stops fitting still works as the cut, since the cut never goes out
        cut: int = max(rest.rfind(" ", 0, end + 1), rest.rfind("\n", 0, end + 1))

        #a word longer than a whole text gets cut right where it stops fitting
        if(cut <= 0):
            cut = end

        parts.append(rest[:cut].rstrip())

        rest = rest[cut:].lstrip()

        end = fitting_end(rest)

    if(rest != ""):
        parts.append(rest)

    return parts


#TEXTBELT SENDER
#one text over textbelt, which answers a 200 with success false when it didn't send it, like a key out of credits, a link it won't send or a text too long
def send_textbelt_text(label: str, recipient: str, text: str) -> bool:
    payload: dict[str, str] = {"phone": recipient, "message": text, "key": TEXTBELT_API_KEY}

    try:
        response: requests.Response = requests.post(TEXTBELT_SEND_URL, data=payload, timeout=20)

        if(response.status_code >= 400 or not response.json().get("success")):
            print(f"[{label}] textbelt send to {recipient} failed {response.status_code}: {response.text[:300]}")

            return False

        return True

    except Exception as error:
        print(f"[{label}] textbelt send to {recipient} errored: {error}")

        return False


#BROKEN LINK
#the link still reads the same to the owner, but with hxxp and [.] textbelt never sees it as one
def break_link(match: re.Match) -> str:
    link: str = re.sub(r"^http", "hxxp", match.group(0), flags=re.IGNORECASE)

    return link.replace(".", "[.]")


#TEXTBELT TEXTS
#links get broken first so textbelt never turns the alert down, then the parts go out in order a gap apart so they land in order, False if any failed
def send_textbelt_texts(label: str, recipient: str, text: str) -> bool:
    all_sent: bool = True

    for position, part in enumerate(textbelt_parts(LINK_PATTERN.sub(break_link, text))):
        if(position > 0):
            time.sleep(TEXT_GAP_SECONDS)

        #a part that failed is logged and the rest still go out, so the owner gets as much of it as can be sent
        if(not send_textbelt_text(label, recipient, part)):
            all_sent = False

    return all_sent



#**********OWNER ALERTS**********
#texts the owner or developer when a person has to step in, an estimate is ready, or a reply broke


#ALERT
#the owner's color checks and the developer's alerts go out over blooio with no typing bubble, neither is a customer waiting on a reply, and the owner answers a color check right in that thread
def send_alert(label: str, recipient: str, text: str, attachments: list[str] | None = None) -> bool:
    send_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/messages"

    payload: dict = {"text": text}

    #pics go along as attachments, so they show up right in the text
    if(attachments):
        payload["attachments"] = attachments

    return send_message(label, recipient, send_url, BLOOIO_API_KEY, payload)


#OWNER NOTIFY
#a person has to take this conversation, so the owner gets who it is, where it came in, what they said and why
def notify_owner(user: str, channel: str, details: str, reason: str) -> bool:
    text: str = f"HIL ALERT\nUser: {user}\nChannel: {channel}\nDetails: {details}\nReason: {reason}"

    return send_textbelt_texts("OWNER NOTIFY", OWNER_NUMBER, text)


#BLOCKED NOTIFY
#the final check stopped a reply, so the owner gets who it was for, the reply that never went out and why, to answer them himself
def notify_blocked(user: str, channel: str, reply: str, reason: str) -> bool:
    text: str = f"REPLY BLOCKED\nUser: {user}\nChannel: {channel}\nReply: {reply}\nReason: {reason}"

    return send_textbelt_texts("BLOCKED NOTIFY", OWNER_NUMBER, text)


#DEV NOTIFY
#the customer got no reply because something broke, so the developer gets who it was, what they said and the error
def notify_dev(user: str, channel: str, details: str, error: str) -> bool:
    text: str = f"REPLY FAILED\nUser: {user}\nChannel: {channel}\nDetails: {details}\nError: {error}"

    return send_alert("DEV NOTIFY", DEV_NUMBER, text)


#SIDE ASK NOTIFY
#something small the details have no answer for, like the wifi or parking, got the new girl's line, so the developer gets who asked, what they said and what went out, and the bot keeps the chat
def notify_side_ask(user: str, channel: str, details: str, reply: str) -> bool:
    text: str = f"SIDE QUESTION\nUser: {user}\nChannel: {channel}\nDetails: {details}\nReply: {reply}"

    return send_alert("SIDE ASK NOTIFY", DEV_NUMBER, text)


#ESTIMATE NOTIFY
#they gave their contact info for the invoice, so the owner gets the job, the day and how to reach them
def notify_estimate(user: str, channel: str, services: str, vehicle: str, drop_off_date: str, name: str, number: str, email: str) -> bool:
    text: str = f"READY TO SEND ESTIMATE\nChannel: {channel}\nCustomer: {user}\nServices: {services}\nVehicle: {vehicle}\nDrop Off: {drop_off_date}\nName: {name}\nNumber: {number}\nEmail: {email}"

    return send_textbelt_texts("ESTIMATE NOTIFY", OWNER_NUMBER, text)


#SCHEDULE NOTIFY
#they want to get on the schedule, so the owner gets who it is, the job, the vehicle and what they said to fit them a day
def notify_schedule_request(user: str, channel: str, name: str, vehicle: str, services: str, details: str) -> bool:
    text: str = f"SCHEDULE REQUEST\nChannel: {channel}\nCustomer: {user}\nName: {name}\nVehicle: {vehicle}\nServices: {services}\nDetails: {details}"

    return send_textbelt_texts("SCHEDULE NOTIFY", OWNER_NUMBER, text)


#COLOR CHECK
#the owner gets their color pics and links, and answers Y and the code if the shop has it, or M and the code
def notify_color_check(code: str, channel: str, user: str, customer: str, service: str, media: list[str], links: list[str]) -> bool:
    text: str = f"Channel: {channel}\nUser: {user}\nCustomer: {customer}"

    if(len(links) > 0):
        text = f"{text}\nLinks: {' '.join(links)}"

    text = f"{text}\nREASON: Customer wants to know if you have this color for the {service}\nANSWERS: Y {code}, M {code}"

    if(send_alert("COLOR CHECK", OWNER_NUMBER, text, media)):
        return True

    #a pic blooio won't attach still reaches the owner as its link
    if(len(media) > 0):
        return send_alert("COLOR CHECK", OWNER_NUMBER, f"{text}\nPics: {' '.join(media)}")

    return False
