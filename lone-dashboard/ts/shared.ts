//**********GLOBALS**********
//stuff every page shares, timings, formats, channel names


//SHOP TIME ZONE
//same as api/_helpers/shop.ts, only for logic that follows the shop's clock, never for what's shown
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

const DAY_MINUTES: number = 24 * 60;


//TIME FORMATS
//no time zone means the viewer's own clock, wherever they're looking from
const LOCAL_DATE: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-CA", {"year": "numeric", "month": "2-digit", "day": "2-digit"});

const LOCAL_TIME: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"hour": "numeric", "minute": "2-digit"});

const LOCAL_WEEKDAY: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"weekday": "short"});

const LOCAL_MONTH_DAY: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"month": "short", "day": "numeric"});

//the shop's clock, for when the bot runs and which shop day a moment counts toward
const SHOP_DATE: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-CA", {"timeZone": SHOP_TIME_ZONE, "year": "numeric", "month": "2-digit", "day": "2-digit"});

const SHOP_WALL: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"timeZone": SHOP_TIME_ZONE, "year": "numeric", "month": "numeric", "day": "numeric", "hour": "numeric", "minute": "numeric", "hourCycle": "h23"});

//day_text's formats, made once per set of options since render loops ask for the same few every row
const DAY_FORMATS: Map<string, Intl.DateTimeFormat> = new Map<string, Intl.DateTimeFormat>();


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
//a moment's date (YYYY-MM-DD) and time ("3:41 PM") on the viewer's own clock
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


//UTC DAY
//a YYYY-MM-DD or YYYY-MM read as that day and time in utc, hours past 23 roll into the next day
function utc_day(date: string, hour: number = 0, minute: number = 0): number {
    const pieces: string[] = date.split("-");

    const year: number = Number(pieces[0] ?? 1970);

    const month: number = Number(pieces[1] ?? 1);

    const day: number = Number(pieces[2] ?? 1);

    return Date.UTC(year, month - 1, day, hour, minute);
}


//LOCAL DATE
//the viewer's own date for a moment, YYYY-MM-DD
export function local_date(at: number): string {
    return LOCAL_DATE.format(at);
}


//LOCAL TIME
//the viewer's own clock time for a moment, "3:41 PM"
export function local_time(at: number): string {
    return LOCAL_TIME.format(at);
}


//LOCAL PARTS
export function local_parts(at: number): MOMENT {
    return {"date": local_date(at), "time": local_time(at)};
}


//SHOP DATE
//the shop's date for a moment, YYYY-MM-DD, what the server's days are keyed by
export function shop_date(at: number): string {
    return SHOP_DATE.format(at);
}


//SHOP OFFSET
//how far the shop's clock runs ahead of utc at a moment, daylight saving included
function shop_offset(at: number): number {
    let year: number = 1970;

    let month: number = 1;

    let day: number = 1;

    let hour: number = 0;

    let minute: number = 0;

    for(const part of SHOP_WALL.formatToParts(at)) {
        if(part.type === "year") {
            year = Number(part.value);
        }

        else if(part.type === "month") {
            month = Number(part.value);
        }

        else if(part.type === "day") {
            day = Number(part.value);
        }

        else if(part.type === "hour") {
            hour = Number(part.value);
        }

        else if(part.type === "minute") {
            minute = Number(part.value);
        }
    }

    //the clock only shows whole minutes, so seconds can't count toward the offset
    return Date.UTC(year, month - 1, day, hour, minute) - Math.floor(at / 60000) * 60000;
}


//SHOP INSTANT
//the moment the shop's clock reads that time on that shop date, minutes past 59 or below 0 roll over
export function shop_instant(date: string, hour: number, minute: number = 0): number {
    const wall: number = utc_day(date, hour, minute);

    //the offset at the first guess is only off near a daylight saving switch, a second look settles it
    const guess: number = wall - shop_offset(wall);

    return wall - shop_offset(guess);
}


//SHOP HOUR TEXT
//what the viewer's clock reads when the shop's clock reads that time on that shop date, written like hour_text
export function shop_hour_text(date: string, hour: number, minute: number = 0): string {
    const at: number = shop_instant(date, hour, minute);

    //shifting by the gap between the two clocks keeps a shop hour that daylight saving skips readable
    const shift: number = Math.round((-new Date(at).getTimezoneOffset() * 60000 - shop_offset(at)) / 60000);

    const local: number = (((hour * 60 + minute + shift) % DAY_MINUTES) + DAY_MINUTES) % DAY_MINUTES;

    return hour_text(Math.floor(local / 60), local % 60);
}


//WHEN SHORT
//"3:41 PM" today, "Tue" this week, "Oct 12" before that, all on the viewer's own clock
export function when_short(at: number): string {
    const moment: MOMENT = local_parts(at);

    const today: string = local_date(Date.now());

    if(moment.date === today) {
        return moment.time;
    }

    if(Date.now() - at < 6 * DAY_MS) {
        return LOCAL_WEEKDAY.format(at);
    }

    return LOCAL_MONTH_DAY.format(at);
}


//DAY TEXT
//days come as YYYY-MM-DD or YYYY-MM, formatting in utc keeps the day from shifting
export function day_text(date: string, options: Intl.DateTimeFormatOptions): string {
    const key: string = JSON.stringify(options);

    let format: Intl.DateTimeFormat | undefined = DAY_FORMATS.get(key);

    if(format === undefined) {
        format = new Intl.DateTimeFormat("en-US", Object.assign({"timeZone": "UTC"}, options));

        DAY_FORMATS.set(key, format);
    }

    return format.format(utc_day(date));
}


//DAY LABEL
//"Today", "Yesterday", or "Tuesday, Oct 27", for a date on the viewer's own clock
export function day_label(date: string): string {
    const today: string = local_date(Date.now());

    const yesterday: string = local_date(Date.now() - DAY_MS);

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
