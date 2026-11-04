//**********GLOBALS**********
//stuff every page shares, timings, formats, channel names


//SHOP TIME ZONE
//same as api/_helpers/shop.ts
export const SHOP_TIME_ZONE: string = "America/Denver";


//PULSE TIMES
//system waits about 45s before answering a batch, so checking every 15s still looks live
const PULSE_MS: number = 15 * 1000;

//idle screens only check once a minute, saves the db's free monthly requests
const IDLE_AFTER_MS: number = 5 * 60 * 1000;

const IDLE_PULSE_MS: number = 60 * 1000;


//ACTIVITY
//anything that counts as someone using the screen
const ACTIVITY_EVENTS: string[] = ["pointermove", "pointerdown", "keydown", "wheel", "touchstart"];


//TOAST TIME
const TOAST_MS: number = 5000;


//DAY
const DAY_MS: number = 86400 * 1000;


//NUMBER FORMATS
const COMPACT: Intl.NumberFormat = new Intl.NumberFormat("en-US", {"notation": "compact", "maximumFractionDigits": 1});

const WHOLE: Intl.NumberFormat = new Intl.NumberFormat("en-US");


//US NUMBER
const US_NUMBER: RegExp = /^\+1(\d{3})(\d{3})(\d{4})$/;


//CHANNEL NAMES
export const CHANNEL_NAMES: Record<string, string> = {"blooio": "Text", "ig": "Instagram", "messenger": "Messenger", "meta-form": "Meta form", "website-form": "Website form"};


//PULSE
export type PULSE = {version: number; up_last: number};


//MOMENT
//a moment's shop date (YYYY-MM-DD) and time ("3:41 PM")
export type MOMENT = {date: string; time: string};


//BIG NUMBER
export type BIG_NUMBER = {short: string; exact: string};


//CHILD
//null, undefined or false just get left out
type CHILD = Node | string | null | undefined | false;


//TOP BAR
const SIGN_OUT_BUTTON: HTMLButtonElement | null = document.querySelector<HTMLButtonElement>(".sign-out");


//SIGNING IN
//a few calls can 401 at once, only the first one redirects
let SIGNING_IN: boolean = false;


//PULSE STATE
//version is -1 till the first check
let PULSE_VERSION: number = -1;

let PULSE_TIMER: number = 0;

let LAST_ACTIVE: number = Date.now();

let ON_CHANGE: (() => void) | null = null;

let ON_EACH: ((pulse: PULSE) => void) | null = null;


//TOAST TIMER
let TOAST_TIMER: number = 0;



//**********SERVER**********
//every call to this dashboard's own api goes through here


//SERVER ERROR
//the server answered with an error, vs never reaching it
export class ServerError extends Error {}


//ASK SERVER
//a 401 sends them to sign in, then back to this page after
export async function ask_server<T>(path: string, method: string = "GET", body: unknown = null): Promise<T> {
    const options: RequestInit = {"credentials": "same-origin", "method": method, "headers": {"Content-Type": "application/json"}};

    if(body !== null) {
        options.body = JSON.stringify(body);
    }

    const response: Response = await fetch(path, options);

    if(response.status === 401 && location.pathname !== "/login" && !SIGNING_IN) {
        SIGNING_IN = true;

        location.assign(`/login?next=${encodeURIComponent(location.pathname + location.search)}`);
    }

    let data: unknown = null;

    try {
        data = await response.json();
    }

    catch {
        data = null;
    }

    if(!response.ok) {
        let message: string = `The server answered ${response.status}.`;

        if(data !== null && typeof data === "object" && "error" in data) {
            message = String(data.error);
        }

        throw new ServerError(message);
    }

    //shapes come from this dashboard's own api handlers
    return data as T;
}



//**********PULSE**********
//pages poll /api/pulse and only reload when the feed wrote something new


//NEXT PULSE
//slower once the screen sits idle
function next_pulse_ms(): number {
    if(Date.now() - LAST_ACTIVE > IDLE_AFTER_MS) {
        return IDLE_PULSE_MS;
    }

    return PULSE_MS;
}


//CHECK PULSE
async function check_pulse(): Promise<void> {
    window.clearTimeout(PULSE_TIMER);

    try {
        const pulse: PULSE = await ask_server<PULSE>("/api/pulse");

        if(ON_EACH !== null) {
            ON_EACH(pulse);
        }

        if(PULSE_VERSION !== -1 && pulse.version !== PULSE_VERSION && ON_CHANGE !== null) {
            ON_CHANGE();
        }

        PULSE_VERSION = pulse.version;
    }

    catch {
        //missed one, next beat tries again
    }

    //cleared again so a check from them coming back can't leave two timers going
    window.clearTimeout(PULSE_TIMER);

    if(document.visibilityState === "visible") {
        PULSE_TIMER = window.setTimeout(check_pulse, next_pulse_ms());
    }
}


//VISIBILITY
//coming back to the tab checks right away
function on_visibility(): void {
    if(document.visibilityState === "visible") {
        check_pulse();
    }
}


//ACTIVITY
//using an idle screen again gets fresh numbers right away
function on_activity(): void {
    const was_idle: boolean = Date.now() - LAST_ACTIVE > IDLE_AFTER_MS;

    LAST_ACTIVE = Date.now();

    if(was_idle) {
        check_pulse();
    }
}


//ON PULSE
//on_change when the feed wrote something new, on_each with every answer, paused while the tab's hidden
export function on_pulse(on_change: () => void, on_each: ((pulse: PULSE) => void) | null = null): void {
    ON_CHANGE = on_change;

    ON_EACH = on_each;

    PULSE_VERSION = -1;

    LAST_ACTIVE = Date.now();

    document.addEventListener("visibilitychange", on_visibility);

    for(const type of ACTIVITY_EVENTS) {
        window.addEventListener(type, on_activity, {"passive": true});
    }

    check_pulse();
}



//**********ELEMENTS**********
//builds elements safely and finds the ones the page already has


//MAKE ELEMENT
//text always goes in as text, so nothing a customer sends can turn into markup
export function make_element<K extends keyof HTMLElementTagNameMap>(tag: K, attributes: Record<string, string | boolean | undefined> = {}, ...children: CHILD[]): HTMLElementTagNameMap[K] {
    const element: HTMLElementTagNameMap[K] = document.createElement(tag);

    for(const attribute of Object.entries(attributes)) {
        const name: string = attribute[0];

        const value: string | boolean | undefined = attribute[1];

        //true is an attribute with no value, false or undefined leaves it off
        if(value === true) {
            element.setAttribute(name, "");
        }

        else if(typeof value === "string") {
            element.setAttribute(name, value);
        }
    }

    for(const child of children) {
        if(child) {
            element.append(child);
        }
    }

    return element;
}


//BY ID
//throws when it's missing so a broken page shows right away
export function by_id<T extends HTMLElement>(id: string): T {
    const found: HTMLElement | null = document.getElementById(id);

    if(found === null) {
        throw new Error(`The page is missing #${id}.`);
    }

    return found as T;
}


//TOAST
//note at the bottom for 5s, red when something went wrong
export function toast(message: string, is_error: boolean = false): void {
    const old_note: Element | null = document.querySelector(".toast");

    if(old_note !== null) {
        old_note.remove();
    }

    window.clearTimeout(TOAST_TIMER);

    let class_name: string = "toast";

    let role: string = "status";

    if(is_error) {
        class_name = "toast is-error";

        role = "alert";
    }

    const note: HTMLDivElement = make_element("div", {"class": class_name, "role": role}, message);

    document.body.append(note);

    TOAST_TIMER = window.setTimeout((): void => note.remove(), TOAST_MS);
}



//**********FORMATTING**********
//numbers, times and ids the way the pages show them


//BIG NUMBER
//1.2M for big counts, the exact one goes in the title
export function big_number(value: number): BIG_NUMBER {
    let short: string = WHOLE.format(value);

    if(value >= 10000) {
        short = COMPACT.format(value);
    }

    return {"short": short, "exact": WHOLE.format(value)};
}


//SHOP PARTS
export function shop_parts(at: number): MOMENT {
    const date: string = new Intl.DateTimeFormat("en-CA", {"timeZone": SHOP_TIME_ZONE, "year": "numeric", "month": "2-digit", "day": "2-digit"}).format(at);

    const time: string = new Intl.DateTimeFormat("en-US", {"timeZone": SHOP_TIME_ZONE, "hour": "numeric", "minute": "2-digit"}).format(at);

    return {"date": date, "time": time};
}


//WHEN SHORT
//"3:41 PM" today, "Tue" this week, "Oct 12" before that
export function when_short(at: number): string {
    const moment: MOMENT = shop_parts(at);

    const today: string = shop_parts(Date.now()).date;

    if(moment.date === today) {
        return moment.time;
    }

    if(Date.now() - at < 6 * DAY_MS) {
        return new Intl.DateTimeFormat("en-US", {"timeZone": SHOP_TIME_ZONE, "weekday": "short"}).format(at);
    }

    return new Intl.DateTimeFormat("en-US", {"timeZone": SHOP_TIME_ZONE, "month": "short", "day": "numeric"}).format(at);
}


//DAY TEXT
//shop days come as YYYY-MM-DD or YYYY-MM, formatting in utc keeps the day from shifting
export function day_text(date: string, options: Intl.DateTimeFormatOptions): string {
    const pieces: string[] = date.split("-");

    const year: number = Number(pieces[0] ?? 1970);

    const month: number = Number(pieces[1] ?? 1);

    const day: number = Number(pieces[2] ?? 1);

    const utc_options: Intl.DateTimeFormatOptions = Object.assign({"timeZone": "UTC"}, options);

    return new Intl.DateTimeFormat("en-US", utc_options).format(Date.UTC(year, month - 1, day));
}


//DAY LABEL
//"Today", "Yesterday", or "Tuesday, Oct 27"
export function day_label(date: string): string {
    const today: string = shop_parts(Date.now()).date;

    const yesterday: string = shop_parts(Date.now() - DAY_MS).date;

    if(date === today) {
        return "Today";
    }

    if(date === yesterday) {
        return "Yesterday";
    }

    return day_text(date, {"weekday": "long", "month": "short", "day": "numeric"});
}


//HOUR TEXT
//"10 AM", "10 PM", and "9:50 AM" when it's past the hour
export function hour_text(hour: number, minute: number = 0): string {
    const twelve_hour: number = hour % 12 || 12;

    let half: string = "PM";

    if(hour < 12) {
        half = "AM";
    }

    if(minute > 0) {
        return `${twelve_hour}:${String(minute).padStart(2, "0")} ${half}`;
    }

    return `${twelve_hour} ${half}`;
}


//READABLE ID
//us numbers read as (555) 123-4567, anything else stays how it came
export function readable_id(id: string): string {
    const us: RegExpExecArray | null = US_NUMBER.exec(id);

    if(us === null) {
        return id;
    }

    return `(${us[1]}) ${us[2]}-${us[3]}`;
}



//**********SIGN OUT**********
//the sign out button in the top bar of every page


//SIGN OUT
//leaves even when the server can't be reached
async function sign_out(): Promise<void> {
    try {
        await ask_server("/api/logout", "POST");
    }

    catch {
        //clearing the cookie is just a courtesy, still leave
    }

    location.assign("/login");
}



//**********START**********
//sign out works on any page that loads this


//SIGN OUT BUTTON
if(SIGN_OUT_BUTTON !== null) {
    SIGN_OUT_BUTTON.addEventListener("click", sign_out);
}
