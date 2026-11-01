#**********IMPORTS**********
#python's json, clock and random names, the shape a waiting conversation comes back in, and the bot's database
import json
import time
import uuid
from typing import TypeAlias

from helpers.state import log



#**********GLOBALS**********
#what a waiting conversation comes back as, and how long a message stays worth answering after a restart


#WAITING
#one conversation's messages still on file: the channel, their id, and each message's entry with the message, oldest first
WAITING: TypeAlias = tuple[str, str, list[tuple[str, list]]]


#REPLAY WINDOW
#a message over a day old is never answered out of nowhere after a restart, meta's 24 hour window to answer it has closed by then anyway
REPLAY_SECONDS: int = 24 * 3600



#**********JOURNAL**********
#every message waiting in a batch stays on file till its batch is answered, so a restart never loses one


#JOURNAL KEY
#one per conversation on each channel, named <what it is>_<id> like every key of theirs, with the channel in it so the replay knows where it goes
def journal_key(channel: str, id: str) -> str:
    return f"journal_{channel}_{id}"


#SAVE
#the message goes on file under its own entry with when it came in, and the entry comes back so its batch can clear it
#empty when it couldn't be saved, redis down never drops the message, it still gets answered, only a restart before then loses it
def save(channel: str, id: str, message: list) -> str:
    entry: str = uuid.uuid4().hex

    saved_text: str = json.dumps({"at": time.time(), "message": message}, ensure_ascii=False)

    try:
        log.write_info(journal_key(channel, id), [saved_text], [entry])

    except Exception as error:
        print(f"JOURNAL SAVE ERROR: {error}")

        return ""

    return entry


#CLEAR
#their batch got answered, so its messages come off file and a restart never answers them again
#a message that couldn't be saved has an empty entry, and taking that off file does nothing
def clear(channel: str, id: str, entries: list[str]) -> None:
    try:
        log.clear_info(journal_key(channel, id), entries)

    #a clear that fails only means a restart answers them again
    except Exception as error:
        print(f"JOURNAL CLEAR ERROR: {error}")



#**********REPLAY**********
#reads back every message still waiting when the server starts, so each one goes back in its batch


#ENTRY PARTS
#one entry's time and message, None when what's on file can't be read as one
def entry_parts(saved_text: str) -> tuple[float, list] | None:
    try:
        saved: dict = json.loads(saved_text)

        return (float(saved["at"]), saved["message"])

    except (ValueError, KeyError, TypeError) as error:
        print(f"JOURNAL READ ERROR: {error}")

        return None


#WAITING MESSAGES
#one conversation's messages still worth answering, oldest first, the ones too old or that can't be read come off file
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


#PENDING
#every conversation with a message still waiting on its reply, read when the server starts, empty when the journal can't be read
def pending() -> list[WAITING]:
    waiting: list[WAITING] = []

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
