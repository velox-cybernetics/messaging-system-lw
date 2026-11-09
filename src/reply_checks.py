#IMPORTS

from datetime import datetime, timedelta

from helpers.calendar import open_dates
from helpers.state import log
from helpers.state import owner
from helpers.state import state_form


#FORM REPEATS

#a second form inside this many hours gets no second reply
FORM_REPEAT_HOURS: int = 24

#same form twice before they ever texted back is a repeat, a text from them resets it
def form_repeated(id: str, channel: str) -> bool:
    if(channel not in state_form.FORM_CHANNELS):
        log.clear_state(f"form_sent_{id}")

        return False

    if(log.read_state(f"form_sent_{id}")):
        print(f"FORM REPEATED: {id} sent the quote form again before texting back, so it gets no second reply")

        return True

    log.write_state(f"form_sent_{id}", "sent")

    log.expire_at(f"form_sent_{id}", datetime.now(open_dates.SHOP_TIMEZONE) + timedelta(hours=FORM_REPEAT_HOURS))

    return False


#HELD REPLIES

#form leads never wait on the owner, they only get the one reply anyway
def news_landing(id: str, channel: str) -> bool:
    return channel not in state_form.FORM_CHANNELS and owner.news_landing(id)

#owners color answer landed mid write, so there message goes back for the redo
def reply_held(id: str, channel: str) -> bool:
    if(not news_landing(id, channel)):
        return False

    log.remove_last_message(f"usermsg_{id}")

    print("REPLY HELD: the owner answered their color check while this reply was being written, so it gets written again carrying what he found")

    return True


#FOLDED REPLIES

#way more than needed, the next batch shows up long before this runs out
FOLD_MINUTES: int = 30

#empty string is the main path, None is nothing folded, and its gone once read
def folded_path(id: str) -> str | None:
    folded: dict | str = log.read_state(f"folded_{id}")

    if(not isinstance(folded, dict) or "restricted" not in folded):
        return None

    log.clear_state(f"folded_{id}")

    return folded["restricted"]

#only safe to redo a reply that didn't already put a step on file
def path_kept(id: str, restricted_start: str) -> bool:
    if(log.read_info(f"date_pending_{id}") or log.read_info(f"contact_pending_{id}")):
        return False

    if(log.read_state(f"convo_ended_{id}") or log.read_info(f"side_ask_notify_{id}")):
        return False

    return restricted_start == "" or bool(log.read_state(f"restricted_{id}"))

#they kept typing while we wrote, so this reply gets tossed and the next batch answers it all
def reply_folded(id: str, has_reply: bool, restricted_start: str, sent_since) -> bool:
    #lead forms pass None since they never fold
    if(sent_since is None or not has_reply or not sent_since(id)):
        return False

    if(not path_kept(id, restricted_start)):
        print("REPLY NOT FOLDED: they sent more while it was written, but it started a step that's already on file, so it goes out as written")

        return False

    log.remove_last_message(f"usermsg_{id}")

    log.write_state(f"folded_{id}", {"restricted": restricted_start})

    log.expire_at(f"folded_{id}", datetime.now(open_dates.SHOP_TIMEZONE) + timedelta(minutes=FOLD_MINUTES))

    print("REPLY FOLDED: they sent more while this reply was written, so it never goes out and their next batch answers it all at once")

    return True


#BOOKING SILENCE

#a person is fitting them in, but a folded batch still owes them a reply
def booking_silent(id: str) -> bool:
    try:
        if(log.read_state(f"folded_{id}")):
            return False

        return owner.booking_held(id)
    except Exception as error:
        #a broken read never silences anyone, better chatty than ghosting
        print(f"BOOKING HOLD READ ERROR: {error}")

        return False
