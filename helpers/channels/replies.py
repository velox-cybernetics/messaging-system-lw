#IMPORTS

from helpers.channels import notify
from helpers.channels import senders
from helpers.response import final_check
from helpers.response import spacing
from helpers.state import log
from helpers.state import state_form
from src import branches


#SAVING

#saves a message under its key, a failed save only gets printed, the reply still goes out
def write_message(key: str, message: dict | str) -> None:
    try:
        log.save_message(key, message)
    except Exception as error:
        print(f"WRITE ERROR: {error}")

#a dollar sign means they've seen a price, the booking branch waits for that
def write_price_sent(id: str, system_response: str) -> None:
    if("$" not in system_response):
        return

    try:
        log.write_info(f"price_sent_{id}", ["sent"], ["status"])
    except Exception as error:
        print(f"PRICE SENT ERROR: {error}")

#a pic ask while there current color isn't on file counts toward giving up on the pic
def write_color_pic_ask(id: str, system_response: str) -> None:
    try:
        branches.note_color_pic_ask(id, system_response)
    except Exception as error:
        print(f"COLOR PIC ASK ERROR: {error}")

#the owner typed it, but on file its the systems words, so the next reply picks up from their
def write_dashboard_text(id: str, text: str) -> None:
    try:
        log.add_system_text(id, text)
    except Exception as error:
        print(f"WRITE ERROR: {error}")

    #a price or pic ask from the boss counts the same as one from the system
    write_price_sent(id, text)

    write_color_pic_ask(id, text)


#SENDING

#the reply as it goes out, or empty when the final check stops it and the owner takes over
def cleared_reply(id: str, channel: str, system_response: str) -> str:
    reason: str = final_check.blocked_reason(system_response)

    if(reason == ""):
        return system_response

    print(f"REPLY BLOCKED: {reason}, so it never goes out: {system_response}")

    notify.notify_blocked(id, channel, system_response, reason)

    return ""

#texts the reply out, an empty one sends nothing but still gets saved
def send_response(id: str, system_response: str, channel: str) -> None:
    #core is done with the reply, so its typing bubble comes down before the texts put up their own
    senders.stop_typing(id, channel)

    #a blocked reply is saved empty like one the shop let be, so later replies know it never went
    system_response = cleared_reply(id, channel, system_response)

    if(system_response != ""):
        #at most 3 sentences a text, and a question always starts its own text
        texts: list[str] = spacing.split_texts(system_response)

        #blooio only takes 3 texts before a form lead answers, so it all goes out as one
        if(channel in state_form.FORM_CHANNELS):
            texts = [spacing.one_text(texts)]

        senders.send_texts(id, channel, texts)

        print()

        print(f"SYSTEM SENT: {system_response}")

        print()

    write_message(f"systemres_{id}", system_response)

    write_price_sent(id, system_response)

    write_color_pic_ask(id, system_response)
