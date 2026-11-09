#IMPORTS

import json
import time
import uuid

from helpers.state import log


#GLOBALS

#a message over a day old never gets replayed, metas 24 hour window is shut by then anyway
REPLAY_SECONDS: int = 24 * 3600


#JOURNAL

#one per conversation per channel, the channels in the name so the replay knows where it goes
def journal_key(channel: str, id: str) -> str:
    return f"journal_{channel}_{id}"

#files the message and hands back its entry, empty if saving failed, it still gets answered
def save(channel: str, id: str, message: list) -> str:
    entry: str = uuid.uuid4().hex

    saved_text: str = json.dumps({"at": time.time(), "message": message}, ensure_ascii=False)

    try:
        log.write_info(journal_key(channel, id), [saved_text], [entry])
    except Exception as error:
        print(f"JOURNAL SAVE ERROR: {error}")

        return ""

    return entry

#there batch got answered, so off file it goes and a restart won't answer it twice
def clear(channel: str, id: str, entries: list[str]) -> None:
    try:
        log.clear_info(journal_key(channel, id), entries)
    except Exception as error:
        #a clear that fails only means a restart answers them again
        print(f"JOURNAL CLEAR ERROR: {error}")


#REPLAY

#one entrys time and message, None when whats on file can't be read as one
def entry_parts(saved_text: str) -> tuple[float, list] | None:
    try:
        saved: dict = json.loads(saved_text)

        return (float(saved["at"]), saved["message"])
    except (ValueError, KeyError, TypeError) as error:
        print(f"JOURNAL READ ERROR: {error}")

        return None

#one convos messages still worth answering, oldest first, stale or garbled ones get tossed
def waiting_messages(key: str, now: float) -> list[tuple[str, list]]:
    timed: list[tuple[float, str, list]] = []

    stale_entries: list[str] = []

    for entry, saved_text in log.read_info(key).items():
        parts: tuple[float, list] | None = entry_parts(saved_text)

        if(parts is None or now - parts[0] > REPLAY_SECONDS):
            stale_entries.append(entry)
        else:
            timed.append((parts[0], entry, parts[1]))

    log.clear_info(key, stale_entries)

    messages: list[tuple[str, list]] = []

    #every entry is its own random name, so two messages never tie past their time
    for waiting_message in sorted(timed):
        messages.append((waiting_message[1], waiting_message[2]))

    return messages

#each convo still owed a reply as channel, id and messages, empty when the journal won't read
def pending() -> list[tuple]:
    waiting: list[tuple] = []

    now: float = time.time()

    try:
        for key in log.matching_keys("journal_*"):
            #a channel never has an underscore in it, so the id is everything after the first one
            key_parts: list[str] = key.removeprefix("journal_").split("_", 1)

            messages: list[tuple[str, list]] = waiting_messages(key, now)

            if(len(messages) > 0):
                waiting.append((key_parts[0], key_parts[1], messages))
    except Exception as error:
        print(f"JOURNAL READ ERROR: {error}")

    return waiting
