#**********IMPORTS**********
#the sender that texts the customer, the owner's texts, the reply splitter and its final check, the conversation on file, and the color job a pic ask counts toward
from helpers.channels import notify
from helpers.channels import senders
from helpers.response import final_check
from helpers.response import spacing
from helpers.state import log
from src import branches



#**********SAVING**********
#saves what came in and what went out to the conversation on file


#SAVE MESSAGE
#adds a message to the conversation on file under its key, a failed save is only printed so it never stops a reply
def write_message(key: str, message: dict | str) -> None:
    try:
        log.save_message(key, message)

    except Exception as error:
        print(f"WRITE ERROR: {error}")


#PRICE SENT
#a reply with a $ in it is a price they've seen, the booking branch only books them once one went out
def write_price_sent(id: str, system_response: str) -> None:
    if("$" not in system_response):
        return

    try:
        log.write_info(f"price_sent_{id}", ["sent"], ["status"])

    except Exception as error:
        print(f"PRICE SENT ERROR: {error}")


#COLOR PIC ASK
#a reply asking for a pic while the color it is now isn't on file counts toward the asks before a color they type stands in for one
def write_color_pic_ask(id: str, system_response: str) -> None:
    try:
        branches.note_color_pic_ask(id, system_response)

    except Exception as error:
        print(f"COLOR PIC ASK ERROR: {error}")



#**********SENDING**********
#puts the finished reply on their phone a few sentences at a time, then saves it, once the final check lets it through


#FINAL CHECK
#the reply as it goes out, or empty when the final check stops it, then the owner gets it to answer them himself
def cleared_reply(id: str, channel: str, system_response: str) -> str:
    reason: str = final_check.blocked_reason(system_response)

    if(reason == ""):
        return system_response

    print(f"REPLY BLOCKED: {reason}, so it never goes out: {system_response}")

    notify.notify_blocked(id, channel, system_response, reason)

    return ""


#SEND REPLY
#texts the reply to them, an empty one sends nothing but is still saved, then notes a price or a pic ask in it
def send_response(id: str, system_response: str, channel: str) -> None:
    #core is done with the reply, so its typing bubble comes down before the texts put up their own
    senders.stop_typing(id, channel)

    #a reply the final check stops is saved empty, the same as a message the shop let be, so no reply after it thinks they read it
    system_response = cleared_reply(id, channel, system_response)

    if(system_response != ""):
        #at most 3 sentences a text, and a question always starts its own text
        texts: list[str] = spacing.split_texts(system_response)

        #it goes out on the channel they wrote in on
        senders.send_texts(id, channel, texts)

        print()

        print(f"SYSTEM SENT: {system_response}")

        print()

    write_message(f"systemres_{id}", system_response)

    write_price_sent(id, system_response)

    write_color_pic_ask(id, system_response)
