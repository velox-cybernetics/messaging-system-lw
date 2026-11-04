#**********IMPORTS**********
#web request errors, and openrouter, where every chat request goes out
import requests

from helpers.models import openrouter



#**********GLOBALS**********
#the model that steps in when the one ahead of it can't answer, and what counts as not answering


#BACKUP MODEL
#kimi k3.1 pro goes through openrouter like every other model, second string on every chat request, it only answers when the model ahead of it errors or comes back empty
BACKUP_MODEL: str = "moonshotai/kimi-k3.1-pro"

#medium on every fallback, so a reply kimi k3.1 pro steps in on still gets thought through before it goes out
BACKUP_EFFORT: str = "medium"


#ANSWER ERRORS
#a failed request, or a 200 with an upstream error in its body instead of an answer
ANSWER_ERRORS: tuple = (requests.RequestException, ValueError, KeyError, IndexError, TypeError)



#**********LINEUPS**********
#sends one chat request down a lineup of models and hands back the first real answer


#LINEUP TEXT
#each (model, effort) gets the same body in order until one answers, every model failing raises the first one's error so a retry still sees why the lead failed, and an empty answer from every model comes back as ""
def lineup_text(label: str, lineup: list[tuple[str, str]], body: dict, timeout: int) -> str:
    first_error: Exception | None = None

    came_back_empty: bool = False

    for model, effort in lineup:
        try:
            text: str = openrouter.openrouter_text(body, model, effort, timeout)

        except ANSWER_ERRORS as error:
            print(f"{label} {model} FAILED: {error}")

            if(first_error is None):
                first_error = error

            continue

        if(text.strip() != ""):
            return text

        print(f"{label} {model} CAME BACK EMPTY")

        came_back_empty = True

    if(first_error is not None and not came_back_empty):
        raise first_error

    return ""
