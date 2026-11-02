//**********IMPORTS**********
//the api call, page helpers and shop clock every page shares
import * as shared from "./shared.js";



//**********GLOBALS**********
//shapes from api/follow-ups.ts, the track's size and the page's parts


//FOLLOW UP
//number is which one in a row it is, counted since the customer last wrote
type FOLLOW_UP = {at: number; number: number};


//CUSTOMER
type CUSTOMER = {id: string; name: string; channel: string; tab: string | null; due: FOLLOW_UP | null; sent: FOLLOW_UP[]};


//FOLLOW UPS
//recheck_minutes is how long before the send the morning's check reads anyone the night's pick missed
type FOLLOW_UPS = {pick_hour: number; send_hour: number; recheck_minutes: number; customers: CUSTOMER[]};


//DAY
//what one customer has on one day, the ones that went out and the next one
type DAY = {sent: FOLLOW_UP[]; due: FOLLOW_UP | null};


//DAYS BACK
//today and the 13 days before it, then tomorrow for the next ones
const DAYS_BACK: number = 13;


//PHONE
//keep in step with the phone layout in base.css, phones don't load this page
const PHONE: string = "(max-width: 640px)";

const PHONE_QUERY: MediaQueryList = window.matchMedia(PHONE);


//RELOAD GAP
//follow ups barely change, so busy messages reload them at most every 30s
const RELOAD_GAP_MS: number = 30 * 1000;


//PAGE PARTS
const LINEUP: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("lineup");

const SCHEDULE: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("schedule");

const TRACK: HTMLElement = shared.by_id<HTMLElement>("track");


//ORDINALS
const ORDINALS: Intl.PluralRules = new Intl.PluralRules("en-US", {"type": "ordinal"});

const SUFFIXES: Record<string, string> = {"one": "st", "two": "nd", "few": "rd", "other": "th"};


//FORMATS
//"Thu, Oct 29, 10:02 AM"
const MOMENT_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"timeZone": shared.SHOP_TIME_ZONE, "weekday": "short", "month": "short", "day": "numeric", "hour": "numeric", "minute": "2-digit"});

const SHOP_CLOCK: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"timeZone": shared.SHOP_TIME_ZONE, "hour": "numeric", "minute": "numeric", "hourCycle": "h23"});


//DAY MINUTES
const DAY_MINUTES: number = 24 * 60;


//PAGE STATE
let LATEST: FOLLOW_UPS | null = null;

let LAST_LOAD: number = 0;

let RELOAD_TIMER: number = 0;

//shop day the track was drawn for, midnight moves every column
let DRAWN_FOR: string = "";

//every send already drawn, so a new one fills in, null before the first draw
let DRAWN_SENT: Set<string> | null = null;



//**********DATES**********
//ordinals, shop day math and the words for when


//NTH
//"1st", "2nd", "3rd", "4th"
function nth(number: number): string {
    return `${number}${SUFFIXES[ORDINALS.select(number)] ?? "th"}`;
}


//ADD DAYS
//calendar math on YYYY-MM-DD so daylight saving never skips or repeats a day
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


//WHEN WORDS
//"today at 10 AM", "tomorrow at 10 AM", or the day spelled out
function when_words(at: number): string {
    const today: string = shared.shop_parts(Date.now()).date;

    const moment: shared.MOMENT = shared.shop_parts(at);

    let day: string = shared.day_text(moment.date, {"weekday": "long", "month": "short", "day": "numeric"});

    if(moment.date === today) {
        day = "today";
    }

    else if(moment.date === add_days(today, 1)) {
        day = "tomorrow";
    }

    else if(moment.date === add_days(today, -1)) {
        day = "yesterday";
    }

    //"10:00 AM" reads as "10 AM"
    return `${day} at ${moment.time.replace(/:00(?=\s)/, "")}`;
}


//SHOP MINUTE
//minutes since midnight on the shop's clock
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


//MINUTES SINCE
//how long ago the shop's clock last showed that minute of the day, 0 right at it
function minutes_since(now: number, minute_of_day: number): number {
    return (now - minute_of_day + DAY_MINUTES) % DAY_MINUTES;
}


//RECHECK TEXT
//"9:50 AM", the morning's check recheck_minutes before the send
function recheck_text(data: FOLLOW_UPS): string {
    const minutes: number = data.send_hour * 60 - data.recheck_minutes;

    return shared.hour_text(Math.floor(minutes / 60), minutes % 60);
}


//LINEUP TEXT
//who gets the next ones and when, or that nobody's lined up
function lineup_text(data: FOLLOW_UPS): string {
    const due: number[] = [];

    for(const customer of data.customers) {
        if(customer.due) {
            due.push(customer.due.at);
        }
    }

    if(due.length > 0) {
        const next: number = Math.min(...due);

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

    //where the shop's clock is since the last send, the night's pick and the morning's check
    const now: number = shop_minute(Date.now());

    const since_send: number = minutes_since(now, data.send_hour * 60);

    const send_text: string = shared.hour_text(data.send_hour);

    //the morning's check ran after the last send and lined nobody up either
    if(minutes_since(now, data.send_hour * 60 - data.recheck_minutes) < since_send) {
        return `Nobody gets a follow up today at ${send_text}.`;
    }

    //the night's pick lined nobody up, and the morning's check can still add anyone who texts overnight
    if(minutes_since(now, data.pick_hour * 60) < since_send) {
        let which_day: string = "tomorrow";

        if(now < data.send_hour * 60) {
            which_day = "today";
        }

        return `Nobody is lined up for ${which_day} at ${send_text} yet, the ${recheck_text(data)} check can still add anyone who texts overnight.`;
    }

    return "Nobody is lined up for a follow up yet.";
}



//**********TRACK**********
//the table of customers by day


//DAY HEAD
function day_head(date: string, today: string): HTMLTableCellElement {
    const full: string = shared.day_text(date, {"weekday": "long", "month": "long", "day": "numeric"});

    let class_name: string = "day";

    if(date === today) {
        class_name = "day is-today";
    }

    else if(date > today) {
        class_name = "day is-later";
    }

    const weekday: HTMLSpanElement = shared.make_element("span", {"class": "weekday", "aria-hidden": "true"}, shared.day_text(date, {"weekday": "narrow"}));

    const day_number: HTMLSpanElement = shared.make_element("span", {"class": "date", "aria-hidden": "true"}, shared.day_text(date, {"day": "numeric"}));

    const hidden: HTMLSpanElement = shared.make_element("span", {"class": "visually-hidden"}, full);

    return shared.make_element("th", {"scope": "col", "class": class_name, "title": full}, weekday, day_number, hidden);
}


//DAY CELL
//dot for one that went out, ring for the next one, exact times in the tooltip
function day_cell(day: DAY | undefined, class_name: string, is_new: boolean): HTMLTableCellElement {
    if(!day) {
        return shared.make_element("td", {"class": class_name});
    }

    const lines: string[] = [];

    for(const each of day.sent) {
        lines.push(`${nth(each.number)} follow up in a row, sent ${MOMENT_FORMAT.format(each.at)}`);
    }

    if(day.due) {
        lines.push(`${nth(day.due.number)} follow up in a row, goes out ${MOMENT_FORMAT.format(day.due.at)}`);
    }

    let mark_class: string = "mark is-due";

    if(day.sent.length > 0) {
        mark_class = "mark is-sent";
    }

    if(is_new) {
        mark_class += " is-new";
    }

    const hidden: HTMLSpanElement = shared.make_element("span", {"class": "visually-hidden"}, lines.join(". "));

    const mark: HTMLSpanElement = shared.make_element("span", {"class": mark_class, "title": lines.join("\n")}, hidden);

    return shared.make_element("td", {"class": class_name}, mark);
}


//DAY OF
//the day a moment falls on, made empty the first time
function day_of(by_date: Map<string, DAY>, at: number): DAY {
    const date: string = shared.shop_parts(at).date;

    const day: DAY = by_date.get(date) ?? {"sent": [], "due": null};

    by_date.set(date, day);

    return day;
}


//HAS NEW SEND
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


//CUSTOMER ROW
//null when all of theirs is older than the first day
function customer_row(customer: CUSTOMER, days: string[], today: string): HTMLTableRowElement | null {
    const by_date: Map<string, DAY> = new Map<string, DAY>();

    for(const sent of customer.sent) {
        day_of(by_date, sent.at).sent.push(sent);
    }

    if(customer.due) {
        day_of(by_date, customer.due.at).due = customer.due;
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

    const title: string = customer.name || shared.readable_id(customer.id);

    //deleted on Messages means nowhere to link to
    let who: HTMLElement = shared.make_element("span", {"class": "who-name"}, title);

    if(customer.tab) {
        const query: URLSearchParams = new URLSearchParams({"tab": customer.tab, "id": customer.id});

        who = shared.make_element("a", {"class": "who-name", "href": `/messages?${query}`, "data-id": customer.id}, title);
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

    const name_cell: HTMLTableCellElement = shared.make_element("th", {"scope": "row", "class": "who", "title": title}, who);

    const channel_cell: HTMLTableCellElement = shared.make_element("td", {"class": "channel"}, shared.CHANNEL_NAMES[customer.channel] ?? customer.channel);

    return shared.make_element("tr", {}, name_cell, channel_cell, ...cells);
}


//RENDER
function render(): void {
    if(!LATEST) {
        return;
    }

    LINEUP.textContent = lineup_text(LATEST);

    SCHEDULE.textContent = `Picked every night at ${shared.hour_text(LATEST.pick_hour)}, checked again at ${recheck_text(LATEST)} for anyone who texted overnight, sent at ${shared.hour_text(LATEST.send_hour)}.`;

    const today: string = shared.shop_parts(Date.now()).date;

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
        TRACK.replaceChildren(shared.make_element("p", {"class": "track-note"}, "No follow ups went out in the last two weeks."));

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

    const caption: HTMLTableCaptionElement = shared.make_element("caption", {"class": "visually-hidden"}, "Follow ups by customer and day");

    const colgroup: HTMLTableColElement = shared.make_element("colgroup", {}, shared.make_element("col", {"class": "who-column"}), shared.make_element("col", {"class": "channel-column"}), ...day_columns);

    const customer_head: HTMLTableCellElement = shared.make_element("th", {"scope": "col"}, shared.make_element("span", {"class": "visually-hidden"}, "Customer"));

    const channel_head: HTMLTableCellElement = shared.make_element("th", {"scope": "col"}, shared.make_element("span", {"class": "visually-hidden"}, "Channel"));

    const head: HTMLTableSectionElement = shared.make_element("thead", {}, shared.make_element("tr", {}, customer_head, channel_head, ...day_heads));

    const body: HTMLTableSectionElement = shared.make_element("tbody", {}, ...rows);

    TRACK.replaceChildren(shared.make_element("table", {}, caption, colgroup, head, body));

    if(focused_id) {
        const link: HTMLAnchorElement | null = TRACK.querySelector<HTMLAnchorElement>(`a[data-id="${CSS.escape(focused_id)}"]`);

        if(link !== null) {
            link.focus();
        }
    }
}



//**********LOADING**********
//fetching, throttled reloads and the clock


//LOAD
async function load(): Promise<void> {
    LAST_LOAD = Date.now();

    try {
        LATEST = await shared.ask_server<FOLLOW_UPS>("/api/follow-ups");

        render();
    }

    catch(error: unknown) {
        let message: string = "Couldn't load follow ups. It retries on its own.";

        if(error instanceof shared.ServerError) {
            message = error.message;
        }

        //what's on screen stays up, error goes under it
        if(LATEST) {
            SCHEDULE.textContent = message;
        }

        else {
            LINEUP.textContent = message;
        }
    }
}


//RELOAD SOON
//new activity reloads, at most once every RELOAD_GAP_MS
function reload_soon(): void {
    window.clearTimeout(RELOAD_TIMER);

    RELOAD_TIMER = window.setTimeout(load, Math.max(0, LAST_LOAD + RELOAD_GAP_MS - Date.now()));
}


//TICK
//sentence moves with the clock, midnight moves every column
function tick(): void {
    if(!LATEST) {
        return;
    }

    if(shared.shop_parts(Date.now()).date !== DRAWN_FOR) {
        render();
    }

    else {
        LINEUP.textContent = lineup_text(LATEST);
    }
}


//START PAGE
function start_page(): void {
    load();

    shared.on_pulse(reload_soon);

    window.setInterval(tick, 60 * 1000);
}



//**********START**********
//phones wait till the screen grows, everything else starts now


//PHONE GATE
if(PHONE_QUERY.matches) {
    PHONE_QUERY.addEventListener("change", start_page, {"once": true});
}

else {
    start_page();
}
