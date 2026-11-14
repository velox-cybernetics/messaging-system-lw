#IMPORTS

from helpers.chains import booking_chains
from helpers.channels import notify
from helpers.channels import replies
from helpers.channels import senders
from helpers.channels import username
from helpers.media import media_prep
from helpers.models import models
from helpers.models import retry
from helpers.response import spacing
from helpers.response import wording
from helpers.state import owner
from helpers.state import log
from helpers.state import state_build
from helpers.state import state_form
from src import routing


#OWNER ANSWERS

#an answer from the owner that settles no check, so he gets told how to answer
def color_check_unmatched(answer: tuple) -> None:
    if(answer[0] == "which"):
        notify.notify_owner_text("More than one color check is waiting, reply Y or M with its number, like Y 12")

        return

    #a hil came in after the check, so his bare answer might be for that, he gets asked with the number
    if(answer[0] == "unsure"):
        notify.notify_owner_text(f"A HIL came in after color check #{answer[2]}, so reply Y {answer[2]} if we have that exact color, or M {answer[2]} with pics of the closest materials")

        return

    #an old N from before M existed, the closest materials took its job
    if(answer[1] == owner.NO_ANSWER):
        notify.notify_owner_text(f"Reply Y {answer[2]} if we have that exact color, or M {answer[2]} with pics of the closest materials")

        return

    notify.notify_owner_text(f"No color check #{answer[2]} is waiting")

#describes each of the owners pics and names its color, so later replies know what went out
def material_options(pics: list[str]) -> list[dict[str, str]]:
    prepared_media: list[tuple] = []

    for url in pics:
        prepared_media.append(media_prep.prepare_media(url))

    descriptions: list[str] = state_form.describe_media(prepared_media)

    materials: list[dict[str, str]] = []

    for url, description in zip(pics, descriptions):
        #each pic is read the same way as a pic they point to as the color they want
        pic_media: dict = {"media_element_0": {"media_description": description}}

        want_output: str = models.extract_want("this color", pic_media, "")

        name: str = models.extractor_values(want_output, ["want"])[0]

        materials.append({"url": url, "description": description, "name": name})

    return materials

#reads an Ms pics before anything waits on them, empty on a Y, None when nothing goes on file
def prepared_materials(id: str, letter: str, code: str, pics: list[str]) -> list[dict[str, str]] | None:
    if(letter == owner.EXACT_ANSWER):
        return []

    #an M with no pics has nothing to send them, so the check keeps waiting on his pics
    if(len(pics) == 0):
        notify.notify_owner_text(f"No pics came in with M {code}, send M {code} again with the pics of the closest materials")

        return None

    try:
        return material_options(pics)
    except Exception as error:
        print(f"COLOR CHECK ANSWER ERROR: {error}")

        #no customer message here, so the developers text goes out without one
        notify.notify_failure(id, owner.color_check_channel(id), {}, f"COLOR CHECK ANSWER ERROR: {error}")

        return None

#tells the owner his news is on its way, now or with the next reply if one was already going
def news_notice(id: str, channel: str, code: str, news: str, many: bool, replying: bool) -> None:
    user_name: str = username.username(id, channel)

    timing: str = f"going out to {user_name}"

    #a reply was already on its way as he answered, so the news rides the next one
    if(replying):
        timing = f"going out with the next reply to {user_name}"

    going: str = "is"

    if(many):
        going = "are"

    notify.notify_owner_text(f"Got it, {news} for color check #{code} {going} {timing}")

#files a Y or an M with its materials, true once the news is due to go out
def color_check_answered(id: str, letter: str, code: str, materials: list[dict[str, str]], replying: bool) -> bool:
    channel: str = owner.color_check_channel(id)

    try:
        if(letter == owner.EXACT_ANSWER):
            owner.answer_exact(id)

            news_notice(id, channel, code, "the good news", False, replying)

            return True

        owner.answer_materials(id, materials)

        if(len(materials) == 1):
            news_notice(id, channel, code, "the material", False, replying)
        else:
            news_notice(id, channel, code, f"the {len(materials)} materials", True, replying)

        return True
    except Exception as error:
        print(f"COLOR CHECK ANSWER ERROR: {error}")

        #no customer message here, so the developers text goes out without one
        notify.notify_failure(id, channel, {}, f"COLOR CHECK ANSWER ERROR: {error}")

        return False


#MATERIAL PICS

#the line the pics go out with, naming the color they asked about, plus the pick question
def materials_lines(id: str, count: int, after_answer: bool) -> tuple[str, str]:
    opener: str = "So"

    #the line goes on right after an answer, so it picks up with Also
    if(after_answer):
        opener = "Also"

    color: str = "the one you sent"

    want: str = owner.checked_want(id)

    #lowercased the way the owner would text it, but brand names like 3M keep their caps
    if(want != ""):
        words: list[str] = []

        for word in want.split():
            words.append(spacing.flow_case(word))

        color = f"that {' '.join(words)}"

    if(count == 1):
        return (f"{opener} just checked out the color books and the closest color we can get to {color} is this one right here:", "Does that one work for you?")

    return (f"{opener} just checked out the color books and the closest colors we can get to {color} are these right here:", "Which one are you liking?")

#each pics number and color, the way there history notes them
def material_colors(materials: list[dict[str, str]]) -> str:
    color_texts: list[str] = []

    for position, material in enumerate(materials, start=1):
        name: str = material["name"]

        if(not name):
            name = "color not read"

        color_texts.append(f"{position}. {name}")

    return ", ".join(color_texts)

#sends the answer, then the pics and pick question, and returns what went out with each pics color
def send_materials(id: str, answer: str, channel: str) -> str:
    materials: list[dict[str, str]] = owner.color_materials(id)

    lines: tuple[str, str] = materials_lines(id, len(materials), answer != "")

    texts: list[str] = []

    if(answer != ""):
        texts = spacing.split_texts(answer)

    pic_urls: list[str] = []

    for material in materials:
        pic_urls.append(material["url"])

    #the pics go out with the line right after the answers texts
    attachments: dict[int, list[str]] = {len(texts): pic_urls}

    all_texts: list[str] = texts + [lines[0], lines[1]]

    senders.stop_typing(id, channel)

    senders.send_texts(id, channel, all_texts, attachments)

    colors: str = material_colors(materials)

    sent: str = f"{lines[0]} [pics: {colors}] {lines[1]}"

    if(answer != ""):
        sent = f"{answer}\n{sent}"

    print()

    print(f"SYSTEM SENT: {sent}")

    print()

    return sent

#materials go right after the answer to their message, so the pick question is the only question
def materials_reply(id: str, system_response: str, channel: str, message_history: dict, current_message_batch: list, vehicle_models: list[str]) -> None:
    answer: str = booking_chains.answer_only(system_response)

    answer = wording.wording_rules(answer, channel, message_history, current_message_batch, vehicle_models)

    #an answer the final check stops stays home, the materials still go out alone
    answer = replies.cleared_reply(id, channel, answer)

    sent: str = send_materials(id, answer, channel)

    replies.write_message(f"systemres_{id}", sent)

    replies.write_price_sent(id, sent)

    owner.news_given(id)


#GOOD NEWS

#puts the good news on the reply to their text, the reply goes out plain if the news won't write
def good_news_reply(system_response: str, state: dict, id: str, channel: str) -> tuple[str, bool]:
    reply: str = retry.run_chain(routing.with_good_news, state, id, [system_response], channel, "GOOD NEWS CHAIN ERROR")

    if(reply == ""):
        return (system_response, False)

    return (reply, True)

#writes the good news from the conversation when they've said nothing new, empty if it fails
def send_good_news(id: str, channel: str) -> str:
    empty_message: dict = {"user_media": {}, "user_text": ""}

    message_history: dict = state_build.message_history_read(id)

    state: dict = state_build.state_formulation(empty_message, message_history)

    sent: str = retry.run_chain(routing.with_good_news, state, id, [""], channel, "GOOD NEWS CHAIN ERROR")

    #news the final check stops waits for there next text, same as news that never got written
    sent = replies.cleared_reply(id, channel, sent)

    if(sent == ""):
        return sent

    texts: list[str] = spacing.split_texts(sent)

    senders.send_texts(id, channel, texts)

    print(f"SYSTEM SENT: {sent}")

    #its schedule question answers a booking held for the color
    log.clear_info(f"booking_held_{id}", ["status"])

    return sent

#sends what the owner found on its own, when no reply of theirs allready carried it
def send_color_news(id: str) -> None:
    channel: str = owner.color_check_channel(id)

    try:
        #a text of theirs already got it with its reply
        if(not owner.news_due(id)):
            return

        sent: str = ""

        if(owner.color_check_status(id) == owner.MATERIALS_STATUS):
            sent = send_materials(id, "", channel)
        elif(log.read_state(f"restricted_{id}")):
            #a person took them after the owners yes, so the schedule question stays home
            print("COLOR NEWS HELD: a person has them now, so the good news waits and nothing asks them onto the schedule")

            return
        else:
            sent = send_good_news(id, channel)

        #the good news didn't get written, so it waits for the reply to their next text
        if(sent == ""):
            return

        #nothing of theirs came in first, so it joins the shops last reply in there history
        log.add_to_last_message(f"systemres_{id}", sent)

        owner.news_given(id)
    except Exception as error:
        print(f"COLOR NEWS ERROR: {error}")

        #no customer message here, so the developers text goes out without one
        notify.notify_failure(id, channel, {}, f"COLOR NEWS ERROR: {error}")


#MISSED CHECKS

#the reply promised a color book check but nothing got read, so the owner gets their pics anyway
def check_missed_color(system_response: str, id: str, current_message_batch: list) -> None:
    if(not spacing.promises_color_check(system_response) or owner.color_check_status(id) != ""):
        return

    media: list[str] = state_form.media_urls(current_message_batch)

    links: list[str] = state_form.text_links(current_message_batch)

    #nothing came with there message for him to check, so a person takes it from here
    if(len(media) == 0 and len(links) == 0):
        owner.restrict(id, owner.REASONS["color_check_missed"])

        return

    route: str = log.read_info(f"criticalInfo_{id}").get("route", "")

    owner.request_unread_color_check(id, route, media, links)

    print("COLOR CHECK MISSED: the reply says the color books are getting checked but no color got read off what they sent, so the owner gets their pics to check anyway")
