#IMPORTS

import time

import requests

from helpers.channels import notify
from helpers.state import dashboard
from helpers.models import writer


#GLOBALS

MAX_ATTEMPTS: int = 3

WAIT_SECONDS: int = 5

#a slow openrouter or a dropped connection is never the requests fault, so another try is fair
TEMPORARY_ERRORS: list[type] = [requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError]


#RETRY RULES

#true for timeouts, dropped connections, 429s and providers having a bad day
def is_temporary_error(error: Exception) -> bool:
    for temporary_error in TEMPORARY_ERRORS:
        if(isinstance(error, temporary_error)):
            return True

    if(isinstance(error, requests.exceptions.HTTPError) and error.response is not None):
        status_code: int = error.response.status_code

        #a 408 is openrouter timing out, a 429 is us being pushy, a 5xx is the provider being down
        if(status_code == 408 or status_code == 429 or status_code >= 500):
            return True

    return False

#false once we're out of tries, or the error would just happen again anyway
def should_retry(error: Exception, attempt: int) -> bool:
    if(attempt >= MAX_ATTEMPTS):
        return False

    #a bad key or no credits fails the same every time, no point retrying
    return is_temporary_error(error)

#sleeps a bit longer after each failed try, so a busy openrouter gets time to breathe
def wait_before_retry(attempt: int) -> None:
    wait_seconds: int = WAIT_SECONDS * attempt

    print(f"RETRY: attempt {attempt} of {MAX_ATTEMPTS} failed, trying again in {wait_seconds} seconds")

    time.sleep(wait_seconds)


#RETRY LOOPS

#runs a check with its inputs, giving up just means the message gets answered without it
def with_retries(label: str, check, check_inputs: list) -> str:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return check(*check_inputs)
        except Exception as error:
            print(f"{label}: {error}")

            if(not should_retry(error, attempt)):
                break

            wait_before_retry(attempt)

    return ""

#runs a chain with the state, id and extras, an empty reply means it gave up
def run_chain(chain, state: dict, id: str, extra_inputs: list, channel: str, error_label: str) -> str:
    #a conversation flagged in the dashboard emails the state its last reply came from
    dashboard.note_state(id, state)

    system_response: str = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        #every try starts its generator note from scratch
        writer.start_note()

        try:
            system_response = chain(state, id, *extra_inputs)

            break
        except Exception as error:
            print(f"{error_label}: {error}")

            #the reply is lost for good here, so the developer gets texted
            if(not should_retry(error, attempt)):
                notify.notify_failure(id, channel, state["current_user_message"], f"{error_label}: {error}")

                break

            wait_before_retry(attempt)

    #the generator goes to the dashboard with the reply, so an upvote lands on the right one
    writer.save_note(id, system_response)

    return system_response
