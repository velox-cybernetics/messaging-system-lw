#IMPORTS

import json

from dotenv import load_dotenv
from upstash_redis import Redis

from helpers.models import chat
from helpers.response.sanitize import sanitize_reply


#GLOBALS

load_dotenv()

REDIS_CLIENT = Redis.from_env()

MAX_ENTRIES: int = 12

#once a list is full, every turn except the last KEEP_RECENT is folded into one summary entry
KEEP_RECENT: int = 4

#kimi k3 sums it up at max, the summary takes the place of the folded turns for good
SUMMARY_MODEL: str = "moonshotai/kimi-k3"

SUMMARY_EFFORT: str = "max"

#every fact later reads need from a summary, so folding never makes the system ask again
SUMMARY_PROMPT: str = """

Summarize this text conversation between Lone Wraps, a car customization shop, and one customer, so the shop's system can keep going without the full history.
The input is JSON, oldest first: user_message_N is the customer and system_response_to_user_message_N is the shop's reply to it. A conversation_summary entry already covers even earlier messages, merge it in.
Write one short plain text paragraph, under 120 words, that keeps every one of these that came up and never mentions one that didn't:
- the customer's vehicle (year, make, model) exactly as they typed it, and the color it is now, saying whether they typed it or a photo showed it
- every service discussed and every price the shop quoted, with the exact numbers written like the shop does ($299, not 299$), and anything the shop said comes with it
- the color and finish they want, any film they picked from the shop's options, and whether they're going with a vinyl wrap or colored PPF
- every photo or video they sent and what it showed, saying whether it's their vehicle, the look they want or the shop's own post. One whose description starts with ERROR still counts as sent, it just couldn't be read
- how long their current wrap or film has been on
- for a commercial job, how many vehicles, decals or a half or full wrap, and whether they have the logo as a vector file
- anything they said they don't have or can't send (no photo, no vector file)
- what the customer decided, asked for, or is still waiting on (booking, the shop checking on something, a hand off to the owner)
Only use facts from the conversation. No greeting, no advice, no markdown, no em dashes.

"""


#READING HISTORY

#every entry, oldest first, a saved message comes back as a dict and a plain reply as text
def read_messages(key: str) -> list:
    values_as_text: list[str] = REDIS_CLIENT.lrange(key, 0, -1)

    values: list = []

    for value_as_text in values_as_text:
        try:
            value: dict = json.loads(value_as_text)

            values.append(value)
        except json.JSONDecodeError:
            values.append(value_as_text)

    return values


#SUMMARIES

#the oldest turns laid out the way the history is, for the summary model to read
def fold_turns(user_messages: list, system_responses: list, fold_count: int) -> dict:
    conversation: dict = {}

    for turn in range(fold_count):
        conversation[f"user_message_{turn}"] = user_messages[turn]

        conversation[f"system_response_to_user_message_{turn}"] = system_responses[turn]

    return conversation

#the summary models paragraph, cleaned of junk, raising when nothing usable comes back
def ask_summary(conversation: dict) -> str:
    system_message: dict = {"role": "system", "content": SUMMARY_PROMPT}

    user_message: dict = {"role": "user", "content": json.dumps(conversation, ensure_ascii=False)}

    #kimi k3 sums it up at max, the backup steps in when it errors or comes back empty
    lineup: list[tuple[str, str]] = [(SUMMARY_MODEL, SUMMARY_EFFORT), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

    body: dict = {"messages": [system_message, user_message], "max_tokens": 32000}

    #a max effort summary can think for over a minute before it writes
    summary: str = chat.lineup_text("SUMMARY", lineup, body, 300)

    if(summary.strip() == ""):
        raise ValueError("empty summary")

    #the summary replaces the folded turns for good, so leaked junk gets cut first
    summary = sanitize_reply(summary)

    if(summary == ""):
        raise ValueError("summary was only junk")

    print(f"SUMMARY: {summary}")

    return summary

#the folded turns come off both lists and the summary takes there place at the front
def swap_summary(user_key: str, system_key: str, fold_count: int, summary: str) -> None:
    summary_entry: str = json.dumps({"conversation_summary": summary.strip()}, ensure_ascii=False)

    #one transaction, so anything pushed meanwhile stays at the end
    transaction = REDIS_CLIENT.multi()

    transaction.ltrim(user_key, fold_count, -1)

    transaction.lpush(user_key, summary_entry)

    transaction.ltrim(system_key, fold_count, -1)

    transaction.lpush(system_key, "")

    transaction.exec()

#folds all but the last few turns into one summary, the history stays put if anything fails
def summarize(id: str) -> None:
    user_key: str = f"usermsg_{id}"

    system_key: str = f"systemres_{id}"

    lock_key: str = f"summarizing_{id}"

    #only one summary per conversation at a time, the lock removes itself after 120 seconds
    if(not REDIS_CLIENT.set(lock_key, "1", nx=True, ex=120)):
        return

    try:
        user_messages: list = read_messages(user_key)

        system_responses: list = read_messages(system_key)

        #only fold complete turns so user and system turns stay paired
        complete_turns: int = min(len(user_messages), len(system_responses))

        fold_count: int = complete_turns - KEEP_RECENT

        if(fold_count < 2):
            return

        conversation: dict = fold_turns(user_messages, system_responses, fold_count)

        summary: str = ask_summary(conversation)

        swap_summary(user_key, system_key, fold_count, summary)
    except Exception as error:
        #on any failure every message is kept as is and the next system reply tries again
        print(f"SUMMARY ERROR: {error}")
    finally:
        REDIS_CLIENT.delete(lock_key)


#SAVING HISTORY

#adds one entry at the end of the list, a dict goes on as json text and a plain reply as it is
def save_message(key: str, value: dict | str) -> None:
    #folded when the system reply is stored, so a summary never delays a reply
    if(key.startswith("systemres_") and REDIS_CLIENT.llen(key) >= MAX_ENTRIES):
        id: str = key.removeprefix("systemres_")

        summarize(id)

    if(isinstance(value, dict)):
        value_as_text: str = json.dumps(value, ensure_ascii=False)

        REDIS_CLIENT.rpush(key, value_as_text)
    else:
        REDIS_CLIENT.rpush(key, value)

#a reply with no message of theirs before it joins our last reply, one answer per message
def add_to_last_message(key: str, text: str) -> None:
    last_messages: list[str] = REDIS_CLIENT.lrange(key, -1, -1)

    #nothing went out before it, so its the first one
    if(len(last_messages) == 0):
        REDIS_CLIENT.rpush(key, text)

        return

    #a last reply that was empty never went out, so its only this one
    REDIS_CLIENT.lset(key, -1, f"{last_messages[0]}\n{text}".strip())

#a text filed as the systems own reply, answering a hanging message or tacked onto our last one
def add_system_text(id: str, text: str) -> None:
    system_key: str = f"systemres_{id}"

    #there last message never got its reply on file, so this is it, folding can wait
    if(REDIS_CLIENT.llen(f"usermsg_{id}") > REDIS_CLIENT.llen(system_key)):
        REDIS_CLIENT.rpush(system_key, text)

        return

    add_to_last_message(system_key, text)

#the newest copy of a message becomes its new form, so later turns read what this one read
def replace_message(key: str, old_value: dict, new_value: dict) -> None:
    old_text: str = json.dumps(old_value, ensure_ascii=False)

    values_as_text: list[str] = REDIS_CLIENT.lrange(key, 0, -1)

    #from the newest back, since the message went on file at the end right before this turn read it
    for position in range(len(values_as_text) - 1, -1, -1):
        if(values_as_text[position] == old_text):
            REDIS_CLIENT.lset(key, position, json.dumps(new_value, ensure_ascii=False))

            return

#the newest message comes off, so a turn whose reply never went out leaves nothing of it behind
def remove_last_message(key: str) -> None:
    REDIS_CLIENT.rpop(key)


#SAVED STATE

#where the conversation is at goes on file as json, a key set to expire keeps its time
def write_state(key: str, value: dict | str) -> None:
    json_text: str = json.dumps(value)

    #a hand off during the schedule hold writes restricted again, the hold still ends on time
    REDIS_CLIENT.set(key, json_text, keepttl=True)

#a state dict, plain HIL when the owner has the chat, empty dict when nothing is on file
def read_state(key: str) -> dict | str:
    raw_text: bytes | None = REDIS_CLIENT.get(key)

    if(raw_text is None):
        return {}

    state: dict | str = json.loads(raw_text)

    return state

#the key comes off file, so a read after it is empty again
def clear_state(key: str) -> None:
    REDIS_CLIENT.delete(key)


#CUSTOMER INFO

#each value goes into the field with the same position in field_names
def write_info(main_key: str, values: list[str], field_names: list[str]) -> None:
    data: dict[str, str] = {}

    for position, name in enumerate(field_names):
        #skip fields that have no value, an empty one never wipes what is already stored
        if(position < len(values) and values[position].strip() != ""):
            data[name] = values[position]

    if(len(data) > 0):
        REDIS_CLIENT.hset(main_key, values=data)

#the named fields come off the key
def clear_info(main_key: str, field_names: list[str]) -> None:
    if(len(field_names) > 0):
        REDIS_CLIENT.hdel(main_key, *field_names)

#true only for the one call that took the field off, so two runs never both act on it
def take_info(main_key: str, field_name: str) -> bool:
    return REDIS_CLIENT.hdel(main_key, field_name) == 1

#every field on the key, an empty dict when nothing is on file
def read_info(main_key: str) -> dict[str, str]:
    data: dict[str, str] = REDIS_CLIENT.hgetall(main_key)

    return data


#COUNTERS

#one atomic step, so two counts taken at the same time never get the same number
def next_count(key: str) -> int:
    return int(REDIS_CLIENT.incr(key))

#where a count is at, 0 before next_count ever took one
def read_count(key: str) -> int:
    raw_text: str | None = REDIS_CLIENT.get(key)

    if(raw_text is None):
        return 0

    return int(raw_text)

#the key comes off file on its own at clear_time, and a time already gone takes it off right away
def expire_at(key: str, clear_time) -> None:
    REDIS_CLIENT.expireat(key, clear_time)


#KEYS

#every key fitting the pattern, a page at a time so a big database never comes back in one go
def matching_keys(pattern: str) -> list[str]:
    keys: list[str] = []

    cursor: int = 0

    while(True):
        scanned: tuple = REDIS_CLIENT.scan(cursor, match=pattern, count=1000)

        cursor = int(scanned[0])

        keys.extend(scanned[1])

        if(cursor == 0):
            return keys
