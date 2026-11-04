#**********IMPORTS**********
#the env key and web requests every openrouter request goes out with
import os

import requests
from dotenv import load_dotenv



#**********GLOBALS**********
#the openrouter key and where its chat requests go


#LOAD ENV
load_dotenv()


#API KEY
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY")


#CHAT URL
CHAT_URL: str = "https://openrouter.ai/api/v1/chat/completions"



#**********CHAT REQUESTS**********
#sends one chat request to one model through openrouter and hands back its plain answer


#HEADERS
#the key and json type every openrouter request carries, the decisions requests use them too
def openrouter_headers() -> dict:
    return {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}


#PROVIDER SETTINGS
#z-ai serves glm first, every other model is left to openrouter's own routing
def provider_settings(model: str) -> dict:
    if(model.startswith("z-ai/")):
        return {"order": ["z-ai"], "allow_fallbacks": True}

    return {"allow_fallbacks": True}


#OPENROUTER TEXT
#the chat body goes out with the model, its provider and its effort laid over it, "" when it came back with no text
def openrouter_text(body: dict, model: str, effort: str, timeout: int) -> str:
    payload: dict = {**body, "model": model, "provider": provider_settings(model), "reasoning": {"effort": effort}}

    response: requests.Response = requests.post(CHAT_URL, headers=openrouter_headers(), json=payload, timeout=timeout)

    response.raise_for_status()

    result: dict = response.json()

    #an upstream error can come back inside a 200 body instead of an answer, so its body is what gets printed
    if("choices" not in result):
        raise ValueError(f"no answer in the body: {result}")

    text: str | None = result["choices"][0]["message"]["content"]

    #a reply cut off while the model was still thinking comes back with no text
    if(text is None):
        return ""

    return text
