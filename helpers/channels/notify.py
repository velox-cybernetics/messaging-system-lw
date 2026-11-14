#IMPORTS

import json

from helpers.channels import senders
from helpers.channels import username
from helpers.media import media_host
from helpers.state import owner
from helpers.state import dashboard
from helpers.state import log
from helpers.state import state_form
from src import branches


#GLOBALS

#a text conversation that came in from a lead form reads as Form, channel_name has the rest
CHANNEL_NAMES: dict[str, str] = {"blooio": "Text", "meta-form": "Form", "website-form": "Form", "ig": "IG", "messenger": "FB"}

#the job a color check is for, by the route on file
COLOR_SERVICES: dict[str, str] = {branches.WRAP_ROUTE: "wrap", branches.COLORED_PPF_ROUTE: "colored PPF"}


#CUSTOMER DETAILS

#what they sent written out for the owner, there text and how many photos or videos came with it
def notify_details(user_message: dict) -> str:
    details: str = user_message.get("user_text", "").strip()

    media_count: int = len(user_message.get("user_media", {}))

    #a photo or video with no text still tells the owner something came in
    if(media_count > 0):
        details = f"{details} (+{media_count} photo or video)".strip()

    return details

#the make and model plus the color it is now, a bright one is more work, and if it was only typed
def vehicle_text(id: str) -> str:
    critical_info: dict[str, str] = log.read_info(f"criticalInfo_{id}")

    vehicle: str = f"{critical_info.get('make', '')} {critical_info.get('model', '')}".strip()

    if(critical_info.get("color")):
        vehicle = f"{vehicle}, {critical_info['color']} now"

    #they typed the color instead of sending a pic, so the owner shouldn't trust it blindly
    if(critical_info.get("color_from") == branches.TYPED_COLOR_SOURCE):
        vehicle = f"{vehicle} (typed, no pic)"

    return vehicle

#a form leads full name and that they came from a form stay on file for the owners texts
def note_lead(current_message_batch: list, id: str) -> None:
    form: dict[str, str] = state_form.form_fields(current_message_batch)

    name: str = state_form.form_name(form)

    log.write_info(f"lead_{id}", [name, "form"], ["name", "source"])

    #the dashboard lists them by the name off the form instead of there number
    dashboard.name_convo(id, name)

#someone who first came in from a form reads as Form, even when they text
def channel_name(id: str, channel: str) -> str:
    if(log.read_info(f"lead_{id}").get("source", "") == "form"):
        return "Form"

    return CHANNEL_NAMES.get(channel, channel)

#the full name they gave on a form, Not given when they never filled one out
def customer_name(id: str) -> str:
    name: str = log.read_info(f"lead_{id}").get("name", "")

    if(name == ""):
        return "Not given"

    return name

#the job the color check is for, a wrap when no route was kept on the check
def color_service(id: str) -> str:
    route: str = log.read_info(f"color_check_{id}").get("route", "")

    return COLOR_SERVICES.get(route, "wrap")

#the pics or links kept on file one per line, with the empty lines left out
def saved_lines(text: str) -> list[str]:
    lines: list[str] = []

    for line in text.split("\n"):
        if(line != ""):
            lines.append(line)

    return lines


#OWNER TEXTS

#color check texts go in his blooio thread, the same one he answers them in
def notify_owner_text(text: str) -> None:
    senders.send_owner_line("OWNER NOTIFY", owner.CHECK_TEXT, text)

#the exact color they sent goes to the owner with who it is, the job and the number he answers with
def notify_color_check(id: str, channel: str) -> None:
    color_check: dict[str, str] = owner.take_color_check_alert(id, channel)

    if(len(color_check) == 0):
        return

    media: list[str] = []

    #blooio never gets the pic from instagrams link to it, so it gets this servers copy
    for url in saved_lines(color_check.get("media", "")):
        media.append(media_host.host_media(url))

    links: list[str] = saved_lines(color_check.get("links", ""))

    code: str = color_check.get("code", "")

    channel_text: str = channel_name(id, channel)

    name: str = customer_name(id)

    service: str = color_service(id)

    user_name: str = username.username(id, channel)

    senders.notify_color_check(code, channel_text, user_name, name, service, media, links)

    #the owner checking the color books has the conversation, so its a hil
    dashboard.log_hand_off(id, dashboard.HIL, f"Color check #{code} sent to the owner")

#every service with its quoted price, then the total and the deposit when every one has a price
def estimate_services(confirmed_services: dict[str, str]) -> str:
    service_texts: list[str] = []

    for service in confirmed_services:
        price: str = confirmed_services[service]

        #a service that never got a price still goes in, so the owner prices it on the estimate
        if(price == ""):
            price = "no price yet"

        service_texts.append(f"{service} ({price})")

    services: str = ", ".join(service_texts)

    total: str = branches.services_total(confirmed_services)

    if(total != ""):
        deposit: str = branches.services_deposit(confirmed_services)

        services = f"{services}\nTotal: {total}\nDeposit: {deposit}"

    return services

#they gave their name, number and email, so the owner gets everything he needs to send the estimate
def notify_estimate(id: str, channel: str) -> None:
    estimate: dict[str, str] = owner.take_estimate_alert(id)

    if(len(estimate) == 0):
        return

    confirmed_services: dict[str, str] = json.loads(estimate.get("services", "{}"))

    services: str = estimate_services(confirmed_services)

    vehicle: str = vehicle_text(id)

    drop_off_date: str = estimate.get("drop_off_date", "")

    name: str = estimate.get("name", "")

    number: str = estimate.get("number", "")

    email: str = estimate.get("email", "")

    user_name: str = username.username(id, channel)

    senders.notify_estimate(user_name, channel, services, vehicle, drop_off_date, name, number, email)

#they want on the schedule, so the owner gets the quoted job, the vehicle and what they said
def notify_schedule_request(id: str, channel: str, user_message: dict) -> None:
    schedule_request: dict[str, str] = owner.take_schedule_request(id)

    if(len(schedule_request) == 0):
        return

    confirmed_services: dict[str, str] = json.loads(schedule_request.get("services", "{}"))

    services: str = estimate_services(confirmed_services)

    channel_text: str = channel_name(id, channel)

    user_name: str = username.username(id, channel)

    name: str = customer_name(id)

    vehicle: str = vehicle_text(id)

    details: str = notify_details(user_message)

    senders.notify_schedule_request(user_name, channel_text, name, vehicle, services, details)

    #a schedule request is the hand off a booking makes
    dashboard.log_hand_off(id, dashboard.BOOKED, "Schedule request sent to the owner")

#a small side ask got the new girl line, so the developer hears about it and nobody takes the chat
def notify_side_ask(id: str, channel: str, user_message: dict) -> None:
    reply: str = owner.take_side_ask_alert(id)

    if(reply == ""):
        return

    user_name: str = username.username(id, channel)

    senders.notify_side_ask(user_name, channel, notify_details(user_message), reply)

#after the reply goes out, everyone who needs to hear about this one hears about it
def notify_hand_off(id: str, channel: str, user_message: dict) -> None:
    reason: str = owner.take_notify_reason(id)

    #an empty reason means nobody needs a person this time, so the owner gets to keep his peace
    if(reason != ""):
        user_name: str = username.username(id, channel)

        senders.notify_owner(user_name, channel, notify_details(user_message), reason)

        dashboard.log_hand_off(id, dashboard.HIL, reason)

    notify_side_ask(id, channel, user_message)

    notify_color_check(id, channel)

    notify_estimate(id, channel)

    notify_schedule_request(id, channel, user_message)

#the final check stopped there reply, so the owner answers them himself and it counts as a hand off
def notify_blocked(id: str, channel: str, system_response: str, reason: str) -> None:
    user_name: str = username.username(id, channel)

    senders.notify_blocked(user_name, channel, system_response, reason)

    dashboard.log_hand_off(id, dashboard.HIL, reason)


#DEVELOPER TEXTS

#the developer hears when a reply broke, the error cut short so it fits in a text
def notify_failure(id: str, channel: str, user_message: dict, error: str) -> None:
    #the customer isn't getting a reply, so the typing bubble core put up comes down
    senders.stop_typing(id, channel)

    user_name: str = username.username(id, channel)

    senders.notify_dev(user_name, channel, notify_details(user_message), error[:300])
