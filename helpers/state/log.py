#**********IMPORTS**********
#python's json and clock, the redis database, the model lineups and the junk cleaner for summaries
import json
from datetime import datetime

from dotenv import load_dotenv
from upstash_redis import Redis
from upstash_redis.client import Pipeline

from helpers.models import chat
from helpers.response.sanitize import sanitize_reply



#**********GLOBALS**********
#the database connection, how long a chat history may get, and the model that shortens it


#LOAD ENV
load_dotenv()


#REDIS CLIENT
REDIS_CLIENT: Redis = Redis.from_env()


#HISTORY LIMITS
MAX_ENTRIES: int = 12

#once a list is full, every turn except the last KEEP_RECENT is folded into one summary entry
KEEP_RECENT: int = 4


#SUMMARY MODEL
#kimi k3 sums it up at max, the summary takes the place of the folded turns for good
SUMMARY_MODEL: str = "moonshotai/kimi-k3"

SUMMARY_EFFORT: str = "max"


#SUMMARY PROMPT
#every fact the extractors, the analyzers and the replies read back out of a summary, so folding turns never makes the bot ask for something again
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



#**********READING HISTORY**********
#reads back what they wrote and what the shop answered, one list each per conversation


#READ MESSAGES
#every entry on the list, oldest first, a saved message comes back as a dict and a plain reply as text
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



#**********SUMMARIES**********
#shortens a long chat history into one paragraph, so the bot keeps the facts but not every message


#FOLD TURNS
#the oldest turns laid out the way the history is, for the summary model to read
def fold_turns(user_messages: list, system_responses: list, fold_count: int) -> dict:
    conversation: dict = {}

    for turn in range(fold_count):
        conversation[f"user_message_{turn}"] = user_messages[turn]

        conversation[f"system_response_to_user_message_{turn}"] = system_responses[turn]

    return conversation


#ASK SUMMARY
#the summary model's paragraph, cleaned of junk, raising when nothing usable comes back
def ask_summary(conversation: dict) -> str:
    system_message: dict = {"role": "system", "content": SUMMARY_PROMPT}

    user_message: dict = {"role": "user", "content": json.dumps(conversation, ensure_ascii=False)}

    #kimi k3 sums it up at max, and kimi k3.1 pro steps in when kimi k3 errors or comes back empty
    lineup: list[tuple[str, str]] = [(SUMMARY_MODEL, SUMMARY_EFFORT), (chat.BACKUP_MODEL, chat.BACKUP_EFFORT)]

    body: dict = {"messages": [system_message, user_message], "max_tokens": 32000}

    #a max effort summary can think for over a minute before it writes
    summary: str = chat.lineup_text("SUMMARY", lineup, body, 300)

    if(summary.strip() == ""):
        raise ValueError("empty summary")

    #the summary takes the place of the folded turns for good, so junk the model leaks after it is cut first
    summary = sanitize_reply(summary)

    if(summary == ""):
        raise ValueError("summary was only junk")

    print(f"SUMMARY: {summary}")

    return summary


#SWAP SUMMARY
#the folded turns come off both lists and the summary takes their place at the front
def swap_summary(user_key: str, system_key: str, fold_count: int, summary: str) -> None:
    summary_entry: str = json.dumps({"conversation_summary": summary.strip()}, ensure_ascii=False)

    #one transaction, so anything pushed meanwhile stays at the end
    transaction: Pipeline = REDIS_CLIENT.multi()

    transaction.ltrim(user_key, fold_count, -1)

    transaction.lpush(user_key, summary_entry)

    transaction.ltrim(system_key, fold_count, -1)

    transaction.lpush(system_key, "")

    transaction.exec()


#SUMMARIZE
#folds every turn but the last few into one summary entry, the history stays as it was when anything fails
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

    #on any failure every message is kept as is and the next system reply tries again
    except Exception as error:
        print(f"SUMMARY ERROR: {error}")

    finally:
        REDIS_CLIENT.delete(lock_key)



#**********SAVING HISTORY**********
#adds to, changes and takes off what they wrote and what the shop answered, folding a full history into a summary first


#SAVE MESSAGE
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


#JOIN LAST
#a reply with nothing of theirs before it joins the shop's last reply, so every message keeps its answer
def add_to_last_message(key: str, text: str) -> None:
    last_messages: list[str] = REDIS_CLIENT.lrange(key, -1, -1)

    #nothing went out before it, so it's the first one
    if(len(last_messages) == 0):
        REDIS_CLIENT.rpush(key, text)

        return

    #a last reply that was empty never went out, so it's only this one
    REDIS_CLIENT.lset(key, -1, f"{last_messages[0]}\n{text}".strip())


#SYSTEM TEXT
#a text that goes on file as the system's own reply, the answer to their last message if a broken reply left it hanging, else tacked onto our last one
def add_system_text(id: str, text: str) -> None:
    system_key: str = f"systemres_{id}"

    #their last message never got its reply on file, so this is it, the folding can wait for the next real reply
    if(REDIS_CLIENT.llen(f"usermsg_{id}") > REDIS_CLIENT.llen(system_key)):
        REDIS_CLIENT.rpush(system_key, text)

        return

    add_to_last_message(system_key, text)


#REPLACE MESSAGE
#the newest copy of a message on file becomes its new form, so the turns after this one read what this one read
def replace_message(key: str, old_value: dict, new_value: dict) -> None:
    old_text: str = json.dumps(old_value, ensure_ascii=False)

    values_as_text: list[str] = REDIS_CLIENT.lrange(key, 0, -1)

    #from the newest back, since the message went on file at the end right before this turn read it
    for position in range(len(values_as_text) - 1, -1, -1):
        if(values_as_text[position] == old_text):
            REDIS_CLIENT.lset(key, position, json.dumps(new_value, ensure_ascii=False))

            return


#DROP LAST
#the newest message comes off, so a turn whose reply never went out leaves nothing of it behind
def remove_last_message(key: str) -> None:
    REDIS_CLIENT.rpop(key)



#**********SAVED STATE**********
#keeps where each conversation is at, so the next message picks up from the same spot


#WRITE STATE
#where the conversation is at goes on file as json, replacing what was there, a key set to come off file on its own keeps that time
def write_state(key: str, value: dict | str) -> None:
    json_text: str = json.dumps(value)

    #a hand off during the schedule hold writes restricted again, and the hold still ends when it was set to
    REDIS_CLIENT.set(key, json_text, keepttl=True)


#READ STATE
#a restricted conversation stores the plain string "HIL" instead of a state, it means a person (the owner) has the chat
#an empty dict when nothing is on file
def read_state(key: str) -> dict | str:
    raw_text: bytes | None = REDIS_CLIENT.get(key)

    if(raw_text is None):
        return {}

    state: dict | str = json.loads(raw_text)

    return state


#CLEAR STATE
#the key comes off file, so a read after it is empty again
def clear_state(key: str) -> None:
    REDIS_CLIENT.delete(key)



#**********CUSTOMER INFO**********
#saves and reads the details they gave us, like their name and car, one field at a time


#WRITE INFO
#each value goes into the field with the same position in field_names
def write_info(main_key: str, values: list[str], field_names: list[str]) -> None:
    data: dict[str, str] = {}

    for position, name in enumerate(field_names):
        #skip fields that have no value, an empty one never wipes what is already stored
        if(position < len(values) and values[position].strip() != ""):
            data[name] = values[position]

    if(len(data) > 0):
        REDIS_CLIENT.hset(main_key, values=data)


#CLEAR INFO
#the named fields come off the key
def clear_info(main_key: str, field_names: list[str]) -> None:
    #only the fields named come off file, everything else stays
    if(len(field_names) > 0):
        REDIS_CLIENT.hdel(main_key, *field_names)


#TAKE INFO
#the field comes off the key, True only for the one call that took it off, so two runs never both act on it
def take_info(main_key: str, field_name: str) -> bool:
    return REDIS_CLIENT.hdel(main_key, field_name) == 1


#READ INFO
#every field on the key, an empty dict when nothing is on file
def read_info(main_key: str) -> dict[str, str]:
    data: dict[str, str] = REDIS_CLIENT.hgetall(main_key)

    return data



#**********COUNTERS AND TIMERS**********
#hands out numbers in order and makes saved keys disappear on their own at a set time


#NEXT COUNT
#one atomic step, so two counts taken at the same time never get the same number
def next_count(key: str) -> int:
    return int(REDIS_CLIENT.incr(key))


#READ COUNT
#where a count is at, 0 before next_count ever took one
def read_count(key: str) -> int:
    raw_text: str | None = REDIS_CLIENT.get(key)

    if(raw_text is None):
        return 0

    return int(raw_text)


#EXPIRE AT
#the key comes off file on its own at clear_time, and a time already gone takes it off right away
def expire_at(key: str, clear_time: datetime) -> None:
    REDIS_CLIENT.expireat(key, clear_time)



#**********KEYS**********
#finds the keys on file whose names fit a pattern, like every conversation's journal


#MATCHING KEYS
#every key whose name fits the pattern, read a page at a time so a big database never comes back in one answer
def matching_keys(pattern: str) -> list[str]:
    keys: list[str] = []

    cursor: int = 0

    while(True):
        scanned: tuple = REDIS_CLIENT.scan(cursor, match=pattern, count=1000)

        cursor = int(scanned[0])

        keys.extend(scanned[1])

        if(cursor == 0):
            return keys
