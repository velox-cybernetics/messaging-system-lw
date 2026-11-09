#IMPORTS

from helpers.chains import booking_chains
from helpers.channels import notify
from helpers.channels import replies
from helpers.channels import senders
from helpers.state import dashboard
from helpers.state import log
from helpers.state import state_build
from helpers.state import state_form
from src import branch_replies
from src import followup
from src import in_conversation
from src import reply_checks


#CORE

#one batch in, one reply out, False means held or folded so the server sends it around again
def core(current_message_batch: list, id: str, channel: str, sent_since=None) -> bool:
    #switched off in the dashboard, so hands off this batch entirely
    if(not dashboard.switched_on(id, channel)):
        print(f"SWITCHED OFF: {id} or their channel is off in the dashboard, so their batch gets no reply")

        return True

    #already the owners from before the system showed up, so it keeps its mouth shut
    if(in_conversation.owner_has_them(id)):
        return True

    if(reply_checks.form_repeated(id, channel)):
        return True

    #owners answer is mid landing, so hold the pen until its on file
    if(reply_checks.news_landing(id, channel)):
        print("REPLY HELD: the owner's answer on their color check is landing, so their batch gets answered once it's on file")

        return False

    silent: bool = reply_checks.booking_silent(id)

    #nobody likes a typing bubble that never ends, so only show it when a reply is coming
    if(not silent):
        senders.start_typing(id, channel)

    user_message: dict = state_build.user_message_form(current_message_batch, channel)

    message_history: dict = state_build.message_history_read(id)

    #first we've heard of them, so make sure its not the owners buddy picking back up
    if(in_conversation.picks_up(user_message, message_history, id, channel)):
        return True

    replies.write_message(f"usermsg_{id}", user_message)

    #they wrote in, so the follow up count starts fresh
    followup.note_message(id, channel)

    #a broken reply still counts as answered, the dev already got texted about it
    answered: bool = True

    try:
        #form leads name goes on file so the owner knows whos who
        if(channel in state_form.FORM_CHANNELS):
            notify.note_lead(current_message_batch, id)

        #a folded batch gets redone from the path its reply started on
        folded: str | None = None

        if(sent_since is not None):
            folded = reply_checks.folded_path(id)

        restricted: str | dict = ""

        if(folded is None):
            restricted = log.read_state(f"restricted_{id}")
        else:
            restricted = folded

        date_pending: dict[str, str] = log.read_info(f"date_pending_{id}")

        contact_pending: dict[str, str] = log.read_info(f"contact_pending_{id}")

        if(silent):
            branch_replies.booking_hold_reply(user_message, id, channel)
        elif(restricted):
            answered = branch_replies.restricted_reply(current_message_batch, user_message, message_history, id, channel, restricted, sent_since)
        elif(date_pending):
            branch_replies.pending_reply(booking_chains.date_propose_chain, [], "DATE", current_message_batch, user_message, message_history, id, channel)
        elif(contact_pending):
            #their info only texts the owner once, so a retry here is harmless
            branch_replies.pending_reply(booking_chains.contact_chain, [channel], "CONTACT", current_message_batch, user_message, message_history, id, channel)
        else:
            answered = branch_replies.main_reply(current_message_batch, user_message, message_history, id, channel, sent_since)
    except Exception as error:
        print(f"READ ERROR FOR READING PENDING|RESTRICTED: {error}")

        notify.notify_failure(id, channel, user_message, f"READ ERROR FOR READING PENDING|RESTRICTED: {error}")

    return answered
