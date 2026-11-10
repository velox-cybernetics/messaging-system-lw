#IMPORTS

import os
import re
import time
from urllib.parse import quote

import requests

from helpers.state import dashboard
from helpers.state import ghl


#GLOBALS

BLOOIO_API_KEY: str = os.environ["BLOOIO_API_KEY"]

TEXTBELT_API_KEY: str = os.environ["TEXTBELT_API_KEY"]

INSTAGRAM_ACCESS_TOKEN: str = os.environ["IG_ACCESS_TOKEN"]

MESSENGER_ACCESS_TOKEN: str = os.environ["MESSENGER_ACCESS_TOKEN"]

#hand offs go to the owner here, and on blooio a text from him only ever answers a color check
OWNER_NUMBER: str = os.environ["HIL_RECIPENT"]

#where the developer hears about replies that broke
DEV_NUMBER: str = os.environ["DEV_NUMBER"]

BLOOIO_BASE_URL: str = "https://backend.blooio.com/v2/api"

TEXTBELT_SEND_URL: str = "https://textbelt.com/text"

INSTAGRAM_SEND_URL: str = "https://graph.instagram.com/v25.0/me/messages"

MESSENGER_SEND_URL: str = "https://graph.facebook.com/v25.0/me/messages"

#long enough that the customer actually sees the bubble before the text
TYPING_SECONDS: int = 3

#the wait between texts of one reply
TEXT_GAP_SECONDS: int = 2

#so the bubble never pops up the instant a text comes in or goes out, thats just creepy
TYPING_DELAY_SECONDS: int = 3

#metas own apis, and neither chat gets a typing bubble
META_CHANNELS: list[str] = ["ig", "messenger"]

#blooios cap refusals, only there text or tapback lifts one so a retry just gets refused again
CAP_CODES: list[str] = ["conversation_awaiting_reply", "conversation_streak_limit", "conversation_inactive_paused"]

#textbelt turns down a text longer than this, counting an emoji as two characters
TEXTBELT_MAX_LENGTH: int = 1024

#a link or bare domain anywhere in an alert, textbelt won't send those on a key not cleared for it
LINK_PATTERN = re.compile(r"(?:https?://|www\.)?(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.IGNORECASE)

#filled once the dev heard textbelt quit sending, emptied when it sends again, one text per outage
TEXTBELT_DOWN: list[str] = []


#SENDING

#posts json behind a bearer token, a failed send still comes back so blooios reason can be read
def post_message(label: str, recipient: str, send_url: str, access_token: str, payload: dict):
    headers: dict[str, str] = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    try:
        response = requests.post(send_url, headers=headers, json=payload, timeout=20)
    except Exception as error:
        print(f"[{label}] send to {recipient} errored: {error}")

        return None

    if(response.status_code >= 400):
        print(f"[{label}] send to {recipient} failed {response.status_code}: {response.text[:300]}")

    return response

#the channel answered and took the text
def went_out(response) -> bool:
    return response is not None and response.status_code < 400

#one text, pic or alert, false when it failed
def send_message(label: str, recipient: str, send_url: str, access_token: str, payload: dict) -> bool:
    return went_out(post_message(label, recipient, send_url, access_token, payload))

#blooio refused because the chat hit its no answer cap, not because anything broke
def chat_capped(response) -> bool:
    if(response is None or response.status_code < 400):
        return False

    try:
        body: object = response.json()
    except ValueError:
        #a refusal that isn't json never names a cap
        return False

    return isinstance(body, dict) and body.get("code") in CAP_CODES


#INSTAGRAM SENDS

#one text to their instagram chat, false when it failed
def send_instagram_message(recipient_id: str, text: str) -> bool:
    payload: dict = {"recipient": {"id": recipient_id}, "message": {"text": text}}

    return send_message("IG", recipient_id, INSTAGRAM_SEND_URL, INSTAGRAM_ACCESS_TOKEN, payload)

#instagram pulls the pic from the url, so it has to be a png or jpeg it can reach
def send_instagram_pic(recipient_id: str, url: str) -> bool:
    payload: dict = {"recipient": {"id": recipient_id}, "message": {"attachment": {"type": "image", "payload": {"url": url}}}}

    return send_message("IG", recipient_id, INSTAGRAM_SEND_URL, INSTAGRAM_ACCESS_TOKEN, payload)

#texts in order a gap apart, pics right after there text, gives back the sent texts and flags
def send_instagram_texts(recipient: str, texts: list[str], attachments: dict[int, list[str]] | None = None) -> tuple:
    texts_sent: list[str] = []

    all_sent: bool = True

    for position, text in enumerate(texts):
        #no typing bubble here, so the gap alone spaces the texts out
        if(position > 0):
            time.sleep(TEXT_GAP_SECONDS)

        #a failed text doesn't stop the rest, they get as much of the reply as can be sent
        if(send_instagram_message(recipient, text)):
            texts_sent.append(text)
        else:
            all_sent = False

        if(attachments and position in attachments):
            for url in attachments[position]:
                if(not send_instagram_pic(recipient, url)):
                    all_sent = False

    #instagram has no cap like blooios, so nothing is ever held back
    return (texts_sent, all_sent, False)


#MESSENGER SENDS

#one text to their messenger chat, false when it failed
def send_messenger_message(recipient_id: str, text: str) -> bool:
    payload: dict = {"recipient": {"id": recipient_id}, "messaging_type": "RESPONSE", "message": {"text": text}}

    return send_message("MESSENGER", recipient_id, MESSENGER_SEND_URL, MESSENGER_ACCESS_TOKEN, payload)

#messenger pulls the pic from the url, so it has to be one it can reach
def send_messenger_pic(recipient_id: str, url: str) -> bool:
    payload: dict = {"recipient": {"id": recipient_id}, "messaging_type": "RESPONSE", "message": {"attachment": {"type": "image", "payload": {"url": url}}}}

    return send_message("MESSENGER", recipient_id, MESSENGER_SEND_URL, MESSENGER_ACCESS_TOKEN, payload)

#same deal as instagram, texts a gap apart with pics right after, then the sent texts and flags
def send_messenger_texts(recipient: str, texts: list[str], attachments: dict[int, list[str]] | None = None) -> tuple:
    texts_sent: list[str] = []

    all_sent: bool = True

    for position, text in enumerate(texts):
        #no typing bubble here, so the gap alone spaces the texts out
        if(position > 0):
            time.sleep(TEXT_GAP_SECONDS)

        #a failed text doesn't stop the rest, they get as much of the reply as can be sent
        if(send_messenger_message(recipient, text)):
            texts_sent.append(text)
        else:
            all_sent = False

        if(attachments and position in attachments):
            for url in attachments[position]:
                if(not send_messenger_pic(recipient, url)):
                    all_sent = False

    #messenger has no cap like blooios, so nothing is ever held back
    return (texts_sent, all_sent, False)


#TYPING BUBBLE

#a post puts the bubble up and a delete takes it down, none when it errored or failed
def typing_request(method: str, action: str, recipient: str):
    typing_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/typing"

    headers: dict[str, str] = {"Authorization": f"Bearer {BLOOIO_API_KEY}"}

    try:
        response = requests.request(method, typing_url, headers=headers, timeout=10)
    except Exception as error:
        print(f"[BLOOIO] {action} typing for {recipient} errored: {error}")

        return None

    if(response.status_code >= 400):
        print(f"[BLOOIO] {action} typing for {recipient} failed {response.status_code}: {response.text[:300]}")

        return None

    return response

#puts the bubble up after a short wait, false when it failed or the chat never shows it
def start_blooio_typing(recipient: str) -> bool:
    #the wait comes before every bubble, even on an rcs chat where it never shows
    time.sleep(TYPING_DELAY_SECONDS)

    response = typing_request("post", "start", recipient)

    if(response is None):
        return False

    #an rcs chat answers with a warning and never shows the bubble, so their is nothing to wait on
    if("warning" in response.text):
        print(f"[BLOOIO] typing not shown for {recipient}: {response.text[:300]}")

        return False

    return True

#takes the bubble down, false when the request failed
def stop_blooio_typing(recipient: str) -> bool:
    response = typing_request("delete", "stop", recipient)

    return response is not None

#keeps the bubble up for the seconds given, false when it never showed, like on an rcs chat
def show_blooio_typing(recipient: str, seconds: int) -> bool:
    typing_started: bool = start_blooio_typing(recipient)

    if(typing_started):
        time.sleep(seconds)

        stop_blooio_typing(recipient)

    return typing_started

#only a text chat over blooio has the bubble, instagram and messenger get none
def start_typing(recipient: str, channel: str) -> bool:
    if(channel in META_CHANNELS):
        return False

    return start_blooio_typing(recipient)

#takes a text chats bubble down, instagram and messenger never had one
def stop_typing(recipient: str, channel: str) -> bool:
    if(channel in META_CHANNELS):
        return False

    return stop_blooio_typing(recipient)


#BLOOIO SENDS

#texts in order behind a bubble with pics riding along, then the sent texts and both flags
def send_blooio_texts(recipient: str, texts: list[str], attachments: dict[int, list[str]] | None = None) -> tuple:
    send_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/messages"

    texts_sent: list[str] = []

    all_sent: bool = True

    capped: bool = False

    #only what actually went out gets logged in ghl, each one a text, its pics and when
    sent: list[tuple] = []

    for position, text in enumerate(texts):
        if(position == 0):
            show_blooio_typing(recipient, TYPING_SECONDS)
        elif(not show_blooio_typing(recipient, TEXT_GAP_SECONDS)):
            #a chat with no bubble still gets the gap, so the texts never land all at once
            time.sleep(TEXT_GAP_SECONDS)

        payload: dict = {"text": text}

        if(attachments and position in attachments):
            payload["attachments"] = attachments[position]

        response = post_message("BLOOIO", recipient, send_url, BLOOIO_API_KEY, payload)

        #a capped chat refuses everything till they text back or react, so why bother with the rest
        if(chat_capped(response)):
            all_sent = False

            capped = True

            break

        #any other failure doesn't stop the rest, they get as much of the reply as can be sent
        if(not went_out(response)):
            all_sent = False
        else:
            texts_sent.append(text)

            sent.append((text, payload.get("attachments", []), time.time()))

    #ghl never sees blooio, so every text they got goes in there conversation there too
    ghl.log_sent(recipient, sent)

    return (texts_sent, all_sent, capped)


#CUSTOMER SENDS

#the reply goes out where they wrote in, a text or a form lead over blooio
def send_on_channel(recipient: str, channel: str, texts: list[str], attachments: dict[int, list[str]] | None) -> tuple:
    if(channel == "ig"):
        return send_instagram_texts(recipient, texts, attachments)

    if(channel == "messenger"):
        return send_messenger_texts(recipient, texts, attachments)

    return send_blooio_texts(recipient, texts, attachments)

#who carries a text on the channel, so a print names who turned one down
def service_of(channel: str) -> str:
    if(channel in META_CHANNELS):
        return channel

    return "blooio"

#nothing reaches anyone switched off in the dashboard, and whatever goes out shows their
def send_texts(recipient: str, channel: str, texts: list[str], attachments: dict[int, list[str]] | None = None, is_followup: bool = False) -> tuple:
    if(not dashboard.switched_on(recipient, channel)):
        print(f"SWITCHED OFF: {recipient} or their channel is off in the dashboard, so nothing was sent")

        return ([], False, False)

    delivery: tuple = send_on_channel(recipient, channel, texts, attachments)

    texts_sent: list[str] = delivery[0]

    all_sent: bool = delivery[1]

    capped: bool = delivery[2]

    #a follow up only shows the part that reached them, and never counts as a reply
    if(is_followup):
        if(len(texts_sent) > 0):
            dashboard.log_outgoing(recipient, channel, texts_sent, None, True, True)

        return (texts_sent, all_sent, capped)

    dashboard.log_outgoing(recipient, channel, texts, attachments, all_sent, is_followup)

    return (texts_sent, all_sent, capped)

#the owners ghl text goes out from the systems number with no bubble, even to someone switched off
def send_ghl_text(recipient: str, text: str, attachments: list[str]) -> bool:
    send_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/messages"

    payload: dict = {"text": text}

    if(attachments):
        payload["attachments"] = attachments

    sent: bool = send_message("GHL TEXT", recipient, send_url, BLOOIO_API_KEY, payload)

    #shows in the dashboard but never goes back to ghl, thats where he wrote it
    dashboard.log_outgoing(recipient, "blooio", [text], {0: attachments}, sent, False, from_ghl=True)

    return sent

#the owner typed it in the dashboard, but it leaves as the system so nobody sees him grab the wheel
def send_dashboard_text(recipient: str, text: str) -> bool:
    send_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/messages"

    #no typing bubble, he already did the typing
    sent: bool = send_message("DASHBOARD TEXT", recipient, send_url, BLOOIO_API_KEY, {"text": text})

    #ghl never sees blooio, so it goes in there conversation their like every text the system sends
    if(sent):
        ghl.log_sent(recipient, [(text, [], time.time())])

    return sent


#SMS SENDS

#an sms follow up through ghl, it shows in green on the dashboard, false when ghl turned it down
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


#TEXTBELT SENDS

#how much of the text fits in one textbelt text, an emoji counts as two like textbelt counts it
def fitting_end(text: str) -> int:
    length: int = 0

    for position, character in enumerate(text):
        length += 1

        if(ord(character) > 0xFFFF):
            length += 1

        if(length > TEXTBELT_MAX_LENGTH):
            return position

    return len(text)

#a long text goes out in parts, each cut at the last space or line break so no word gets split
def textbelt_parts(text: str) -> list[str]:
    parts: list[str] = []

    rest: str = text.strip()

    end: int = fitting_end(rest)

    while(end < len(rest)):
        #a space right where it stops fitting still works, the cut itself never goes out
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

#one text over textbelt, which happily answers a 200 with success false when it didn't send it
def send_textbelt_text(label: str, recipient: str, text: str) -> bool:
    payload: dict[str, str] = {"phone": recipient, "message": text, "key": TEXTBELT_API_KEY}

    try:
        response = requests.post(TEXTBELT_SEND_URL, data=payload, timeout=20)

        if(response.status_code >= 400 or not response.json().get("success")):
            #textbelts refill link carries the key, so it comes out before the reason hits the logs
            reason: str = response.text.replace(TEXTBELT_API_KEY, "KEY")[:300]

            print(f"[{label}] textbelt send to {recipient} failed {response.status_code}: {reason}")

            return False

        return True
    except Exception as error:
        print(f"[{label}] textbelt send to {recipient} errored: {error}")

        return False

#the link still reads fine to the owner, but with hxxp and bracketed dots textbelt can't spot it
def break_link(match) -> str:
    link: str = re.sub(r"^http", "hxxp", match.group(0), flags=re.IGNORECASE)

    return link.replace(".", "[.]")

#links get broken first so textbelt takes it, then the parts go out a gap apart, false if any failed
def send_textbelt_texts(label: str, recipient: str, text: str) -> bool:
    all_sent: bool = True

    for position, part in enumerate(textbelt_parts(LINK_PATTERN.sub(break_link, text))):
        if(position > 0):
            time.sleep(TEXT_GAP_SECONDS)

        #a failed part doesn't stop the rest, the owner gets as much of it as can be sent
        if(not send_textbelt_text(label, recipient, part)):
            all_sent = False

    return all_sent


#OWNER ALERTS

#color checks and dev alerts go over blooio with no bubble, nobodys waiting on a reply there
def send_alert(label: str, recipient: str, text: str, attachments: list[str] | None = None) -> bool:
    send_url: str = f"{BLOOIO_BASE_URL}/chats/{quote(recipient, safe='')}/messages"

    payload: dict = {"text": text}

    if(attachments):
        payload["attachments"] = attachments

    return send_message(label, recipient, send_url, BLOOIO_API_KEY, payload)

#the owners texts go over textbelt, and the first one it won't send tells the dev its down
def send_owner_text(label: str, text: str) -> bool:
    if(send_textbelt_texts(label, OWNER_NUMBER, text)):
        #textbelt is back, so the next time it quits the dev hears about it again
        TEXTBELT_DOWN.clear()

        return True

    #only the dev hears, the owners blooio thread caps at 4 unanswered texts and his color checks need it
    if(len(TEXTBELT_DOWN) == 0):
        TEXTBELT_DOWN.append(label)

        send_alert("DEV NOTIFY", DEV_NUMBER, f"OWNER TEXT FAILED\nLabel: {label}\nTextbelt would not send it, so the owner gets no texts till it's fixed, the logs say why")

    return False

#a person has to take this one, so the owner gets who, where, what they said and why
def notify_owner(user: str, channel: str, details: str, reason: str) -> bool:
    text: str = f"HIL ALERT\nUser: {user}\nChannel: {channel}\nDetails: {details}\nReason: {reason}"

    return send_owner_text("OWNER NOTIFY", text)

#the owner gets the reply the final check stopped and why, so he can answer them himself
def notify_blocked(user: str, channel: str, reply: str, reason: str) -> bool:
    text: str = f"REPLY BLOCKED\nUser: {user}\nChannel: {channel}\nReply: {reply}\nReason: {reason}"

    return send_owner_text("BLOCKED NOTIFY", text)

#something broke and they got no reply, so the developer gets who, what they said and the error
def notify_dev(user: str, channel: str, details: str, error: str) -> bool:
    text: str = f"REPLY FAILED\nUser: {user}\nChannel: {channel}\nDetails: {details}\nError: {error}"

    return send_alert("DEV NOTIFY", DEV_NUMBER, text)

#a small ask like wifi or parking got the new girl line, the developer hears and the system keeps it
def notify_side_ask(user: str, channel: str, details: str, reply: str) -> bool:
    text: str = f"SIDE QUESTION\nUser: {user}\nChannel: {channel}\nDetails: {details}\nReply: {reply}"

    return send_alert("SIDE ASK NOTIFY", DEV_NUMBER, text)

#they gave there contact info, so the owner gets the job, the day and how to reach them
def notify_estimate(user: str, channel: str, services: str, vehicle: str, drop_off_date: str, name: str, number: str, email: str) -> bool:
    text: str = f"READY TO SEND ESTIMATE\nChannel: {channel}\nCustomer: {user}\nServices: {services}\nVehicle: {vehicle}\nDrop Off: {drop_off_date}\nName: {name}\nNumber: {number}\nEmail: {email}"

    return send_owner_text("ESTIMATE NOTIFY", text)

#they want on the schedule, so the owner gets who, the job, the vehicle and what they said
def notify_schedule_request(user: str, channel: str, name: str, vehicle: str, services: str, details: str) -> bool:
    text: str = f"SCHEDULE REQUEST\nChannel: {channel}\nCustomer: {user}\nName: {name}\nVehicle: {vehicle}\nServices: {services}\nDetails: {details}"

    return send_owner_text("SCHEDULE NOTIFY", text)

#the owner gets their color pics and links, and answers Y or M with the code
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
