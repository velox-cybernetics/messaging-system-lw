//IMPORTS

import * as shared from "./shared.js";


//GLOBALS

//number is its place in the row since they last wrote, sms went out on the shops ghl number
type FOLLOW_UP = {at: number; number: number; sms: boolean};

//held is when blooio started holding their texts till they text back or react, null when it isn't
type CUSTOMER = {id: string; name: string; channel: string; tab: string | null; due: FOLLOW_UP | null; sent: FOLLOW_UP[]; held: number | null};

//recheck_minutes before the send, the mornings check reads anyone the nights pick missed
type FOLLOW_UPS = {pick_hour: number; send_hour: number; recheck_minutes: number; customers: CUSTOMER[]};

//what one customer has on one day, the ones that went out, the next one, and when blooio held them
type DAY = {sent: FOLLOW_UP[]; due: FOLLOW_UP | null; held: number | null};

//today and the 13 days before it, then tomorrow for the next ones
const DAYS_BACK: number = 13;

//keep in step with the phone layout in the base css, phones don't load this page
const PHONE: string = "(max-width: 640px)";

const PHONE_QUERY: MediaQueryList = window.matchMedia(PHONE);

//follow ups barely change, so busy messages reload them at most every 30s
const RELOAD_GAP_MS: number = 30 * 1000;

const LINEUP: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("lineup");

const SCHEDULE: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("schedule");

const TRACK: HTMLElement = shared.by_id<HTMLElement>("track");

const ORDINALS: Intl.PluralRules = new Intl.PluralRules("en-US", {"type": "ordinal"});

const SUFFIXES: Record<string, string> = {"one": "st", "two": "nd", "few": "rd", "other": "th"};

//short weekday, date and clock time, on the viewers own clock
const MOMENT_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"weekday": "short", "month": "short", "day": "numeric", "hour": "numeric", "minute": "2-digit"});

//the system picks, rechecks and sends on the shops clock, so todays runs go by it
const SHOP_CLOCK: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"timeZone": shared.SHOP_TIME_ZONE, "hour": "numeric", "minute": "numeric", "hourCycle": "h23"});

const DAY_MINUTES: number = 24 * 60;

let LATEST: FOLLOW_UPS | null = null;

let LAST_LOAD: number = 0;

let RELOAD_TIMER: number = 0;

//viewers day the track was drawn for, their midnight moves every column
let DRAWN_FOR: string = "";

//every send already drawn, so a new one fills in, null before the first draw
let DRAWN_SENT: Set<string> | null = null;


//DATES

//ordinals like 1st, 2nd, 3rd and 4th
function nth(number: number): string {
    let suffix: string | undefined = SUFFIXES[ORDINALS.select(number)];

    if(suffix === undefined) {
        suffix = "th";
    }

    return `${number}${suffix}`;
}

//calendar math on the date string so daylight saving never skips or repeats a day
function add_days(date: string, days: number): string {
    const pieces: string[] = date.split("-");

    let year: number = 1970;

    let month: number = 1;

    let day: number = 1;

    if(pieces[0] !== undefined) {
        year = Number(pieces[0]);
    }

    if(pieces[1] !== undefined) {
        month = Number(pieces[1]);
    }

    if(pieces[2] !== undefined) {
        day = Number(pieces[2]);
    }

    return new Date(Date.UTC(year, month - 1, day + days)).toISOString().slice(0, 10);
}

//today, tomorrow, yesterday, or the day spelled out, next to the viewers today
function day_word(date: string, today: string): string {
    if(date === today) {
        return "today";
    }

    if(date === add_days(today, 1)) {
        return "tomorrow";
    }

    if(date === add_days(today, -1)) {
        return "yesterday";
    }

    return shared.day_text(date, {"weekday": "long", "month": "short", "day": "numeric"});
}

//when in words like today at 10 AM, on the viewers own clock
function when_words(at: number): string {
    const moment: shared.MOMENT = shared.local_parts(at);

    const day: string = day_word(moment.date, shared.local_date(Date.now()));

    //right on the hour drops the double zero, so just 10 AM
    return `${day} at ${moment.time.replace(/:00(?=\s)/, "")}`;
}

//like today at 10 AM, for the send on that shop date, told on the viewers own clock
function send_words(data: FOLLOW_UPS, date: string): string {
    const at: number = shared.shop_instant(date, data.send_hour);

    return `${day_word(shared.local_date(at), shared.local_date(Date.now()))} at ${shared.shop_hour_text(date, data.send_hour)}`;
}

//minutes since midnight on the shops clock
function shop_minute(at: number): number {
    let hour: number = 0;

    let minute: number = 0;

    for(const part of SHOP_CLOCK.formatToParts(at)) {
        if(part.type === "hour") {
            hour = Number(part.value);
        }
        else if(part.type === "minute") {
            minute = Number(part.value);
        }
    }

    return hour * 60 + minute;
}

//how long ago the shops clock last showed that minute of the day, 0 right at it
function minutes_since(now: number, minute_of_day: number): number {
    return (now - minute_of_day + DAY_MINUTES) % DAY_MINUTES;
}

//the mornings check on that shop date, recheck_minutes before the send, on the viewers clock
function recheck_text(data: FOLLOW_UPS, date: string): string {
    const minutes: number = data.send_hour * 60 - data.recheck_minutes;

    return shared.shop_hour_text(date, Math.floor(minutes / 60), minutes % 60);
}

//who gets the next ones and when, or that nobodys lined up
function lineup_text(data: FOLLOW_UPS): string {
    const due: number[] = [];

    for(const customer of data.customers) {
        if(customer.due) {
            due.push(customer.due.at);
        }
    }

    if(due.length > 0) {
        let next: number = Infinity;

        for(const at of due) {
            next = Math.min(next, at);
        }

        const when: string = when_words(next);

        if(next > Date.now()) {
            if(due.length === 1) {
                return `1 customer gets a follow up ${when}.`;
            }

            return `${due.length} customers get a follow up ${when}.`;
        }

        //morning send still going, or the system was down when they were due
        if(due.length === 1) {
            return `1 follow up due ${when} hasn't gone out yet.`;
        }

        return `${due.length} follow ups due ${when} haven't gone out yet.`;
    }

    //where the shops clock is since the last send, the nights pick and the mornings check
    const now: number = shop_minute(Date.now());

    const shop_today: string = shared.shop_date(Date.now());

    const since_send: number = minutes_since(now, data.send_hour * 60);

    //the mornings check ran after the last send and lined nobody up either
    if(minutes_since(now, data.send_hour * 60 - data.recheck_minutes) < since_send) {
        return `Nobody gets a follow up ${send_words(data, shop_today)}.`;
    }

    //the nights pick lined nobody up, but the mornings check can still add late texters
    if(minutes_since(now, data.pick_hour * 60) < since_send) {
        let send_date: string = add_days(shop_today, 1);

        if(now < data.send_hour * 60) {
            send_date = shop_today;
        }

        return `Nobody is lined up for ${send_words(data, send_date)} yet, the ${recheck_text(data, send_date)} check can still add anyone who texts overnight.`;
    }

    return "Nobody is lined up for a follow up yet.";
}

//how many on the track blooio holds till they text back or react, empty when nobody
function held_text(data: FOLLOW_UPS): string {
    const first_day: string = add_days(shared.local_date(Date.now()), -DAYS_BACK);

    let held: number = 0;

    for(const customer of data.customers) {
        if(customer.held !== null && shared.local_date(customer.held) >= first_day) {
            held++;
        }
    }

    if(held === 0) {
        return "";
    }

    if(held === 1) {
        return "1 customer is on hold till they text back or react, Blooio won't take more texts to them before then.";
    }

    return `${held} customers are on hold till they text back or react, Blooio won't take more texts to them before then.`;
}

//the lineup, then whos on hold
function headline(data: FOLLOW_UPS): string {
    const held: string = held_text(data);

    if(held === "") {
        return lineup_text(data);
    }

    return `${lineup_text(data)} ${held}`;
}


//TRACK

//a columns heading, a narrow weekday and the date, the full day for screen readers
function day_head(date: string, today: string): HTMLTableCellElement {
    const full: string = shared.day_text(date, {"weekday": "long", "month": "long", "day": "numeric"});

    let class_name: string = "day";

    if(date === today) {
        class_name = "day is-today";
    }
    else if(date > today) {
        class_name = "day is-later";
    }

    const weekday: HTMLSpanElement = shared.make_element("span", {"class": "weekday", "aria-hidden": "true"}, [shared.day_text(date, {"weekday": "narrow"})]);

    const day_number: HTMLSpanElement = shared.make_element("span", {"class": "date", "aria-hidden": "true"}, [shared.day_text(date, {"day": "numeric"})]);

    const hidden: HTMLSpanElement = shared.make_element("span", {"class": "visually-hidden"}, [full]);

    return shared.make_element("th", {"scope": "col", "class": class_name, "title": full}, [weekday, day_number, hidden]);
}

//dot when one went out, green by sms, ring for the next, amber ring when held, times on hover
function day_cell(day: DAY | undefined, class_name: string, is_new: boolean): HTMLTableCellElement {
    if(!day) {
        return shared.make_element("td", {"class": class_name});
    }

    const lines: string[] = [];

    for(const each of day.sent) {
        let how: string = "sent";

        if(each.sms) {
            how = "sent by SMS";
        }

        lines.push(`${nth(each.number)} follow up in a row, ${how} ${MOMENT_FORMAT.format(each.at)}`);
    }

    if(day.due) {
        lines.push(`${nth(day.due.number)} follow up in a row, goes out ${MOMENT_FORMAT.format(day.due.at)}`);
    }

    if(day.held !== null) {
        lines.push(`On hold since ${MOMENT_FORMAT.format(day.held)}, Blooio takes no more texts till they text back or react`);
    }

    let mark_class: string = "mark is-due";

    //a hold is where they are now, so it shows over a send that day
    if(day.held !== null) {
        mark_class = "mark is-held";
    }
    else if(day.sent.length > 0) {
        mark_class = "mark is-sent";

        for(const each of day.sent) {
            if(each.sms) {
                mark_class = "mark is-sent is-sms";
            }
        }
    }

    if(is_new && day.held === null) {
        mark_class += " is-new";
    }

    const hidden: HTMLSpanElement = shared.make_element("span", {"class": "visually-hidden"}, [lines.join(". ")]);

    const mark: HTMLSpanElement = shared.make_element("span", {"class": mark_class, "title": lines.join("\n")}, [hidden]);

    return shared.make_element("td", {"class": class_name}, [mark]);
}

//the viewers day a moment falls on, made empty the first time
function day_of(by_date: Map<string, DAY>, at: number): DAY {
    const date: string = shared.local_date(at);

    let day: DAY | undefined = by_date.get(date);

    if(day === undefined) {
        day = {"sent": [], "due": null, "held": null};
    }

    by_date.set(date, day);

    return day;
}

//a send that wasn't drawn last time gets marked new
function has_new_send(customer: CUSTOMER, day: DAY | undefined): boolean {
    if(DRAWN_SENT === null || day === undefined) {
        return false;
    }

    for(const each of day.sent) {
        if(!DRAWN_SENT.has(`${customer.id}@${each.at}`)) {
            return true;
        }
    }

    return false;
}

//null when all of theirs is older than the first day
function customer_row(customer: CUSTOMER, days: string[], today: string): HTMLTableRowElement | null {
    const by_date: Map<string, DAY> = new Map<string, DAY>();

    for(const sent of customer.sent) {
        day_of(by_date, sent.at).sent.push(sent);
    }

    if(customer.due) {
        day_of(by_date, customer.due.at).due = customer.due;
    }

    if(customer.held !== null) {
        day_of(by_date, customer.held).held = customer.held;
    }

    let in_range: boolean = false;

    for(const date of days) {
        if(by_date.has(date)) {
            in_range = true;

            break;
        }
    }

    if(!in_range) {
        return null;
    }

    let title: string = customer.name;

    if(!title) {
        title = shared.readable_id(customer.id);
    }

    //deleted on Messages means nowhere to link to
    let who: HTMLElement = shared.make_element("span", {"class": "who-name"}, [title]);

    if(customer.tab) {
        const query: URLSearchParams = new URLSearchParams({"tab": customer.tab, "id": customer.id});

        who = shared.make_element("a", {"class": "who-name", "href": `/messages?${query}`, "data-id": customer.id}, [title]);
    }

    const cells: HTMLTableCellElement[] = [];

    for(const date of days) {
        const day: DAY | undefined = by_date.get(date);

        let class_name: string = "day";

        if(date === today) {
            class_name = "day is-today";
        }

        cells.push(day_cell(day, class_name, has_new_send(customer, day)));
    }

    const name_cell: HTMLTableCellElement = shared.make_element("th", {"scope": "row", "class": "who", "title": title}, [who]);

    let channel: string | undefined = shared.CHANNEL_NAMES[customer.channel];

    if(channel === undefined) {
        channel = customer.channel;
    }

    const channel_cell: HTMLTableCellElement = shared.make_element("td", {"class": "channel"}, [channel]);

    return shared.make_element("tr", {}, [name_cell, channel_cell].concat(cells));
}

//the lineup, the schedule line and the whole two week track
function render(): void {
    if(!LATEST) {
        return;
    }

    LINEUP.textContent = headline(LATEST);

    //the systems hours run on the shops clock, todays shop date gets daylight saving right
    const shop_today: string = shared.shop_date(Date.now());

    SCHEDULE.textContent = `Picked every night at ${shared.shop_hour_text(shop_today, LATEST.pick_hour)}, checked again at ${recheck_text(LATEST, shop_today)} for anyone who texted overnight, sent at ${shared.shop_hour_text(shop_today, LATEST.send_hour)}.`;

    const today: string = shared.local_date(Date.now());

    const days: string[] = [];

    for(let index: number = 0; index < DAYS_BACK + 2; index++) {
        days.push(add_days(today, index - DAYS_BACK));
    }

    const rows: HTMLTableRowElement[] = [];

    for(const customer of LATEST.customers) {
        const row: HTMLTableRowElement | null = customer_row(customer, days, today);

        if(row !== null) {
            rows.push(row);
        }
    }

    DRAWN_FOR = today;

    const drawn_sent: Set<string> = new Set<string>();

    for(const customer of LATEST.customers) {
        for(const each of customer.sent) {
            drawn_sent.add(`${customer.id}@${each.at}`);
        }
    }

    DRAWN_SENT = drawn_sent;

    if(rows.length === 0) {
        TRACK.replaceChildren(shared.make_element("p", {"class": "track-note"}, ["No follow ups went out in the last two weeks."]));

        return;
    }

    //redraw replaces the rows, so the focused name gets focus back
    let focused_id: string | undefined = undefined;

    if(document.activeElement instanceof HTMLElement) {
        focused_id = document.activeElement.dataset.id;
    }

    const day_columns: HTMLTableColElement[] = [];

    const day_heads: HTMLTableCellElement[] = [];

    for(const date of days) {
        day_columns.push(shared.make_element("col", {}));

        day_heads.push(day_head(date, today));
    }

    const caption: HTMLTableCaptionElement = shared.make_element("caption", {"class": "visually-hidden"}, ["Follow ups by customer and day"]);

    const columns: HTMLTableColElement[] = [shared.make_element("col", {"class": "who-column"}), shared.make_element("col", {"class": "channel-column"})];

    const colgroup: HTMLTableColElement = shared.make_element("colgroup", {}, columns.concat(day_columns));

    const customer_head: HTMLTableCellElement = shared.make_element("th", {"scope": "col"}, [shared.make_element("span", {"class": "visually-hidden"}, ["Customer"])]);

    const channel_head: HTMLTableCellElement = shared.make_element("th", {"scope": "col"}, [shared.make_element("span", {"class": "visually-hidden"}, ["Channel"])]);

    const head: HTMLTableSectionElement = shared.make_element("thead", {}, [shared.make_element("tr", {}, [customer_head, channel_head].concat(day_heads))]);

    const body: HTMLTableSectionElement = shared.make_element("tbody", {}, rows);

    TRACK.replaceChildren(shared.make_element("table", {}, [caption, colgroup, head, body]));

    if(focused_id) {
        const link: HTMLAnchorElement | null = TRACK.querySelector<HTMLAnchorElement>(`a[data-id="${CSS.escape(focused_id)}"]`);

        if(link !== null) {
            link.focus();
        }
    }
}


//LOADING

//fetches everything for the page, an error never wipes whats already up
async function load(): Promise<void> {
    LAST_LOAD = Date.now();

    try {
        LATEST = await shared.ask_server<FOLLOW_UPS>("/api/follow-ups");

        render();
    }
    catch(error: unknown) {
        let message: string = "Couldn't load follow ups. It retries on its own.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        //whats on screen stays up, error goes under it
        if(LATEST) {
            SCHEDULE.textContent = message;
        }
        else {
            LINEUP.textContent = message;
        }
    }
}

//new activity reloads, at most once every RELOAD_GAP_MS
function reload_soon(): void {
    window.clearTimeout(RELOAD_TIMER);

    RELOAD_TIMER = window.setTimeout(load, Math.max(0, LAST_LOAD + RELOAD_GAP_MS - Date.now()));
}

//sentence moves with the clock, the viewers midnight moves every column
function tick(): void {
    if(!LATEST) {
        return;
    }

    if(shared.local_date(Date.now()) !== DRAWN_FOR) {
        render();
    }
    else {
        LINEUP.textContent = headline(LATEST);
    }
}

//phones wait till the screen gets wide enough, nothing loads before then
function start_page(): void {
    load();

    shared.on_pulse(reload_soon);

    window.setInterval(tick, 60 * 1000);
}


//START

if(PHONE_QUERY.matches) {
    PHONE_QUERY.addEventListener("change", start_page, {"once": true});
}
else {
    start_page();
}
