#IMPORTS

import os

import requests
from dotenv import load_dotenv


#GLOBALS

load_dotenv()

INSTAGRAM_ACCESS_TOKEN: str = os.environ["IG_ACCESS_TOKEN"]

MESSENGER_ACCESS_TOKEN: str = os.environ["MESSENGER_ACCESS_TOKEN"]


#USERNAMES

#their instagram handle, looked up from the id their messages come in with
def username_instagram(instagram_id: str) -> str:
    headers: dict[str, str] = {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}

    profile_url: str = f"https://graph.instagram.com/v25.0/{instagram_id}"

    params: dict[str, str] = {"fields": "username"}

    response = requests.get(profile_url, headers=headers, params=params, timeout=20)

    response.raise_for_status()

    return response.json()["username"]

#messenger has no usernames, so the name comes from the pages conversation with them
def username_messenger(messenger_id: str) -> str:
    headers: dict[str, str] = {"Authorization": f"Bearer {MESSENGER_ACCESS_TOKEN}"}

    conversations_url: str = "https://graph.facebook.com/v25.0/me/conversations"

    params: dict[str, str] = {"user_id": messenger_id, "fields": "participants"}

    response = requests.get(conversations_url, headers=headers, params=params, timeout=20)

    response.raise_for_status()

    conversations: list[dict] = response.json().get("data", [])

    for conversation in conversations:
        participants: list[dict] = conversation.get("participants", {}).get("data", [])

        for participant in participants:
            if(participant.get("id") == messenger_id):
                return participant.get("name", messenger_id)

    #no conversation with them came back, so their messenger id stands in for the name
    return messenger_id

#the id is good enough when the lookup dies, and a blooio id is already there number
def username(id: str, channel: str) -> str:
    try:
        if(channel == "ig"):
            return username_instagram(id)
        elif(channel == "messenger"):
            return username_messenger(id)
    except Exception as error:
        print(f"[{channel.upper()}] name lookup for {id} failed: {error}")

    return id
