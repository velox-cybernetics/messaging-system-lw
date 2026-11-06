#**********IMPORTS**********
#python's clock, the web request errors, the texts that tell the developer a reply was lost, the dashboard that keeps the state each reply came from, and the note on which generator wrote it
import time
from collections.abc import Callable

import requests

from helpers.channels import notify
from helpers.state import dashboard
from helpers.models import writer



#**********GLOBALS**********
#how many tries a slow request gets and which errors are worth another try


#RETRY LIMITS
MAX_ATTEMPTS: int = 3

WAIT_SECONDS: int = 5


#TEMPORARY ERRORS
#a slow openrouter or a dropped connection is never the request's fault, so it can go through on another try
TEMPORARY_ERRORS: list[type] = [requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError]



#**********RETRY RULES**********
#decides if a failed request is worth another try, and waits a little longer before each one


#TEMPORARY ERROR
#True for a timeout, a dropped connection, too many requests or a provider that's down
def is_temporary_error(error: Exception) -> bool:
    for temporary_error in TEMPORARY_ERRORS:
        if(isinstance(error, temporary_error)):
            return True

    if(isinstance(error, requests.exceptions.HTTPError) and error.response is not None):
        status_code: int = error.response.status_code

        #408 is openrouter timing out, 429 is too many requests at once, a 5xx is the provider being down
        if(status_code == 408 or status_code == 429 or status_code >= 500):
            return True

    return False


#SHOULD RETRY
#False once the last try is used up or the error would only happen again
def should_retry(error: Exception, attempt: int) -> bool:
    if(attempt >= MAX_ATTEMPTS):
        return False

    #a bad key or no credits fails the same way every time, so only a temporary error is tried again
    return is_temporary_error(error)


#RETRY WAIT
#sleeps before the next try, the wait grows with each failed one
def wait_before_retry(attempt: int) -> None:
    #each wait is longer than the one before, so a busy openrouter gets time to catch up
    wait_seconds: int = WAIT_SECONDS * attempt

    print(f"RETRY: attempt {attempt} of {MAX_ATTEMPTS} failed, trying again in {wait_seconds} seconds")

    time.sleep(wait_seconds)



#**********RETRY LOOPS**********
#runs a check or a whole reply chain again on a slow connection, so one bad request never loses it


#WITH RETRIES
#check_inputs are handed to the check in order, and when it gives up the message still gets answered without it, so it gives back ""
def with_retries(label: str, check: Callable[..., str], check_inputs: list) -> str:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return check(*check_inputs)

        except Exception as error:
            print(f"{label}: {error}")

            if(not should_retry(error, attempt)):
                break

            wait_before_retry(attempt)

    return ""


#RUN CHAIN
#the chain gets the state and the id first, then extra_inputs in order, and an empty reply means it gave up
def run_chain(chain: Callable[..., str], state: dict, id: str, extra_inputs: list, channel: str, error_label: str) -> str:
    #a conversation flagged in the dashboard emails the state its last reply was written from
    dashboard.note_state(id, state)

    system_response: str = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        #each try notes the generator that writes it from scratch
        writer.start_note()

        try:
            system_response = chain(state, id, *extra_inputs)

            break

        except Exception as error:
            print(f"{error_label}: {error}")

            #a bad key, no credits or the last try failing means the reply is lost, so the developer gets texted
            if(not should_retry(error, attempt)):
                notify.notify_failure(id, channel, state["current_user_message"], f"{error_label}: {error}")

                break

            wait_before_retry(attempt)

    #the generator that wrote it goes to the dashboard with the reply, so an upvote there adds its example to that generator
    writer.save_note(id, system_response)

    return system_response
