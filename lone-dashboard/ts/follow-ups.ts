//IMPORTS

import * as shared from "./shared.js";


//GLOBALS

//number is its place in the row since they last wrote, sms went out on the shops ghl number
type FOLLOW_UP = {at: number; number: number; sms: boolean};

//held is when blooio started holding their texts till they text back or react, null when it isn't
type CUSTOMER = {id: string; name: string; channel: string; tab: string | null; due: FOLLOW_UP | null; sent: FOLLOW_UP[]; held: number | null};

type FOLLOW_UPS = {customers: CUSTOMER[]};

//what one customer has on one day, the ones that went out, the next one, and when blooio held them
type DAY = {sent: FOLLOW_UP[]; due: FOLLOW_UP | null; held: number | null};

//today and the 13 days before it, then tomorrow for the next ones
const DAYS_BACK: number = 13;

//keep in step with the phone layout in the base css, phones don't load this page
const PHONE: string = "(max-width: 640px)";

const PHONE_QUERY: MediaQueryList = window.matchMedia(PHONE);

//follow ups barely change, so busy messages reload them at most every 30s
const RELOAD_GAP_MS: number = 30 * 1000;

const TRACK: HTMLElement = shared.by_id<HTMLElement>("track");

//rows per page, arrows flip through the rest
const PAGE_SIZE: number = 25;

const PAGER: HTMLElement = shared.by_id<HTMLElement>("pager");

const PREVIOUS: HTMLButtonElement = shared.by_id<HTMLButtonElement>("previous");

const NEXT: HTMLButtonElement = shared.by_id<HTMLButtonElement>("next");

const PAGE_LABEL: HTMLSpanElement = shared.by_id<HTMLSpanElement>("page");

const ORDINALS: Intl.PluralRules = new Intl.PluralRules("en-US", {"type": "ordinal"});

const SUFFIXES: Record<string, string> = {"one": "st", "two": "nd", "few": "rd", "other": "th"};

//short weekday, date and clock time, on the viewers own clock
const MOMENT_FORMAT: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"weekday": "short", "month": "short", "day": "numeric", "hour": "numeric", "minute": "2-digit"});

let LATEST: FOLLOW_UPS | null = null;

let LAST_LOAD: number = 0;

let RELOAD_TIMER: number = 0;

//page on screen, starts at 0, survives reloads so a refresh doesn't kick you back
let PAGE: number = 0;

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

//one page of the two week track, newest first, plus the arrows under it
function render(): void {
    if(!LATEST) {
        return;
    }

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
        PAGER.hidden = true;

        TRACK.replaceChildren(shared.make_element("p", {"class": "track-note"}, ["No follow ups went out in the last two weeks."]));

        return;
    }

    //last page can shrink after a reload, so pull the page back in if it fell off the end
    const page_count: number = Math.ceil(rows.length / PAGE_SIZE);

    if(PAGE > page_count - 1) {
        PAGE = page_count - 1;
    }

    const page_rows: HTMLTableRowElement[] = [];

    for(let index: number = PAGE * PAGE_SIZE; index < rows.length && index < (PAGE + 1) * PAGE_SIZE; index++) {
        const row: HTMLTableRowElement | undefined = rows[index];

        if(row !== undefined) {
            page_rows.push(row);
        }
    }

    PAGE_LABEL.textContent = `${PAGE + 1} / ${page_count}`;

    PREVIOUS.disabled = PAGE === 0;

    NEXT.disabled = PAGE === page_count - 1;

    //one page needs no arrows
    PAGER.hidden = page_count === 1;

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

    const body: HTMLTableSectionElement = shared.make_element("tbody", {}, page_rows);

    TRACK.replaceChildren(shared.make_element("table", {}, [caption, colgroup, head, body]));

    if(focused_id) {
        const link: HTMLAnchorElement | null = TRACK.querySelector<HTMLAnchorElement>(`a[data-id="${CSS.escape(focused_id)}"]`);

        if(link !== null) {
            link.focus();
        }
    }
}

//arrow clicks, -1 back a page, 1 forward
function flip_page(step: number): void {
    PAGE = PAGE + step;

    if(PAGE < 0) {
        PAGE = 0;
    }

    render();
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

        //nothing up yet, so the error takes the tracks spot, otherwise the old page stays
        if(!LATEST) {
            TRACK.replaceChildren(shared.make_element("p", {"class": "track-note"}, [message]));
        }
    }
}

//new activity reloads, at most once every RELOAD_GAP_MS
function reload_soon(): void {
    window.clearTimeout(RELOAD_TIMER);

    RELOAD_TIMER = window.setTimeout(load, Math.max(0, LAST_LOAD + RELOAD_GAP_MS - Date.now()));
}

//the viewers midnight moves every column
function tick(): void {
    if(LATEST && shared.local_date(Date.now()) !== DRAWN_FOR) {
        render();
    }
}

//phones wait till the screen gets wide enough, nothing loads before then
function start_page(): void {
    PREVIOUS.addEventListener("click", function(): void { flip_page(-1); });

    NEXT.addEventListener("click", function(): void { flip_page(1); });

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
