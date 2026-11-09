#IMPORTS

import os

import requests
from dotenv import load_dotenv


#GLOBALS

load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY")

CHAT_URL: str = "https://openrouter.ai/api/v1/chat/completions"


#CHAT REQUESTS

#the key and json type every openrouter request carries, the decisions requests use them too
def openrouter_headers() -> dict:
    return {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}

#glm goes to its own maker first, everyone else gets whatever openrouter picks
def provider_settings(model: str) -> dict:
    if(model.startswith("z-ai/")):
        return {"order": ["z-ai"], "allow_fallbacks": True}

    return {"allow_fallbacks": True}

#sends the body with the model, provider and effort on top, empty string when no text came back
def openrouter_text(body: dict, model: str, effort: str, timeout: int) -> str:
    payload: dict = {}

    for key in body:
        payload[key] = body[key]

    payload["model"] = model

    payload["provider"] = provider_settings(model)

    payload["reasoning"] = {"effort": effort}

    response = requests.post(CHAT_URL, headers=openrouter_headers(), json=payload, timeout=timeout)

    response.raise_for_status()

    result: dict = response.json()

    #upstream errors like to hide inside a 200, so the whole body gets printed
    if("choices" not in result):
        raise ValueError(f"no answer in the body: {result}")

    text: str | None = result["choices"][0]["message"]["content"]

    #a reply cut off while the model was still thinking comes back with no text
    if(text is None):
        return ""

    return text
