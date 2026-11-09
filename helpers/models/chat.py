#IMPORTS

import requests

from helpers.models import openrouter


#GLOBALS

#kimi rides second on every request, the understudy only goes on when the lead flops
BACKUP_MODEL: str = "moonshotai/kimi-k3.1-pro"

#a fallback reply still gets thought through, being second string is no excuse
BACKUP_EFFORT: str = "medium"

#a failed request, or a 200 with an upstream error in its body instead of an answer
ANSWER_ERRORS: tuple = (requests.RequestException, ValueError, KeyError, IndexError, TypeError)


#LINEUPS

#tries each model in order, nobody answering raises the first error unless one came back empty
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
