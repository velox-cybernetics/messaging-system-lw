//GLOBALS

//matches the apis shop helper, only for shop clock logic, never for whats shown
export const SHOP_TIME_ZONE: string = "America/Denver";

//system waits about 45s before answering a batch, so checking every 15s still looks live
const PULSE_MS: number = 15 * 1000;

//idle screens only check once a minute, saves the dbs free monthly requests
const IDLE_AFTER_MS: number = 5 * 60 * 1000;

const IDLE_PULSE_MS: number = 60 * 1000;

//anything that counts as someone using the screen
const ACTIVITY_EVENTS: string[] = ["pointermove", "pointerdown", "keydown", "wheel", "touchstart"];

const TOAST_MS: number = 5000;

const DAY_MS: number = 86400 * 1000;

const DAY_MINUTES: number = 24 * 60;

//no time zone means the viewers own clock, wherever they're looking from
const LOCAL_DATE: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-CA", {"year": "numeric", "month": "2-digit", "day": "2-digit"});

const LOCAL_TIME: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"hour": "numeric", "minute": "2-digit"});

const LOCAL_WEEKDAY: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"weekday": "short"});

const LOCAL_MONTH_DAY: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"month": "short", "day": "numeric"});

//the shops clock, for when the system runs and which shop day a moment counts toward
const SHOP_DATE: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-CA", {"timeZone": SHOP_TIME_ZONE, "year": "numeric", "month": "2-digit", "day": "2-digit"});

const SHOP_WALL: Intl.DateTimeFormat = new Intl.DateTimeFormat("en-US", {"timeZone": SHOP_TIME_ZONE, "year": "numeric", "month": "numeric", "day": "numeric", "hour": "numeric", "minute": "numeric", "hourCycle": "h23"});

//day_texts formats, made once per set of options since every row asks for the same few
const DAY_FORMATS: Map<string, Intl.DateTimeFormat> = new Map<string, Intl.DateTimeFormat>();

const COMPACT: Intl.NumberFormat = new Intl.NumberFormat("en-US", {"notation": "compact", "maximumFractionDigits": 1});

const WHOLE: Intl.NumberFormat = new Intl.NumberFormat("en-US");

const US_NUMBER: RegExp = /^\+1(\d{3})(\d{3})(\d{4})$/;

export const CHANNEL_NAMES: Record<string, string> = {"blooio": "Text", "ig": "Instagram", "messenger": "Messenger", "meta-form": "Meta form", "website-form": "Website form"};

export type PULSE = {version: number; up_last: number};

//what local_parts hands back, a moments date and time on the viewers own clock
export type MOMENT = {date: string; time: string};

export type BIG_NUMBER = {short: string; exact: string};

//null, undefined or false just get left out
type CHILD = Node | string | null | undefined | false;

const SIGN_OUT_BUTTON: HTMLButtonElement | null = document.querySelector<HTMLButtonElement>(".sign-out");

//a few calls can 401 at once, only the first one redirects
let SIGNING_IN: boolean = false;

//version is minus one till the first check
let PULSE_VERSION: number = -1;

let PULSE_TIMER: number = 0;

let LAST_ACTIVE: number = Date.now();

let ON_CHANGE: (() => void) | null = null;

let ON_EACH: ((pulse: PULSE) => void) | null = null;

let TOAST_TIMER: number = 0;


//SERVER

//the server answered with an error, vs never reaching it
function server_error(message: string): Error {
    const failure: Error = new Error(message);

    failure.name = "ServerError";

    return failure;
}

//true only for the servers own no, a fetch that never got through stays false
export function is_server_error(failure: unknown): failure is Error {
    return failure instanceof Error && failure.name === "ServerError";
}

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

        throw server_error(message);
    }

    //shapes come from this dashboards own api handlers
    return data as T;
}


//PULSE

//slower once the screen sits idle
function next_pulse_ms(): number {
    if(Date.now() - LAST_ACTIVE > IDLE_AFTER_MS) {
        return IDLE_PULSE_MS;
    }

    return PULSE_MS;
}

//one beat, and the next one only gets lined up while someone can see the tab
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

//coming back to the tab checks right away
function on_visibility(): void {
    if(document.visibilityState === "visible") {
        check_pulse();
    }
}

//using an idle screen again gets fresh numbers right away
function on_activity(): void {
    const was_idle: boolean = Date.now() - LAST_ACTIVE > IDLE_AFTER_MS;

    LAST_ACTIVE = Date.now();

    if(was_idle) {
        check_pulse();
    }
}

//on_change when the feed changed, on_each with every answer, paused while the tabs hidden
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


//ELEMENTS

//text always goes in as text, so nothing a customer sends can turn into markup
export function make_element<K extends keyof HTMLElementTagNameMap>(tag: K, attributes: Record<string, string | boolean | undefined> = {}, children: CHILD[] = []): HTMLElementTagNameMap[K] {
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

//throws when its missing so a broken page shows right away
export function by_id<T extends HTMLElement>(id: string): T {
    const found: HTMLElement | null = document.getElementById(id);

    if(found === null) {
        throw new Error(`The page is missing #${id}.`);
    }

    return found as T;
}

//a toasts 5s are up, off it goes
function remove_toast(note: HTMLDivElement): void {
    note.remove();
}

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

    const note: HTMLDivElement = make_element("div", {"class": class_name, "role": role}, [message]);

    document.body.append(note);

    TOAST_TIMER = window.setTimeout(remove_toast, TOAST_MS, note);
}


//FORMATTING

//counts from 10K up get the short form, the exact one goes in the title
export function big_number(value: number): BIG_NUMBER {
    let short: string = WHOLE.format(value);

    if(value >= 10000) {
        short = COMPACT.format(value);
    }

    return {"short": short, "exact": WHOLE.format(value)};
}

//a date or month string read as that day and time in utc, hours past 23 roll over
function utc_day(date: string, hour: number = 0, minute: number = 0): number {
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

    return Date.UTC(year, month - 1, day, hour, minute);
}

//the viewers own date for a moment, year first so it sorts and compares as text
export function local_date(at: number): string {
    return LOCAL_DATE.format(at);
}

//the viewers own clock time for a moment, hour and minutes with AM or PM
export function local_time(at: number): string {
    return LOCAL_TIME.format(at);
}

//date and clock time for a moment in one go, both on the viewers clock
export function local_parts(at: number): MOMENT {
    return {"date": local_date(at), "time": local_time(at)};
}

//the shops date for a moment, what the servers days are keyed by
export function shop_date(at: number): string {
    return SHOP_DATE.format(at);
}

//how far the shops clock runs ahead of utc at a moment, daylight saving included
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

//when the shops clock shows that time on that date, minutes past 59 or below 0 roll over
export function shop_instant(date: string, hour: number, minute: number = 0): number {
    const wall: number = utc_day(date, hour, minute);

    //the first guess is only off near a daylight saving switch, a second look settles it
    const guess: number = wall - shop_offset(wall);

    return wall - shop_offset(guess);
}

//the viewers clock reading for that shop time on that shop date, written like hour_text
export function shop_hour_text(date: string, hour: number, minute: number = 0): string {
    const at: number = shop_instant(date, hour, minute);

    //shifting by the gap between both clocks keeps a shop hour daylight saving skips readable
    const shift: number = Math.round((-new Date(at).getTimezoneOffset() * 60000 - shop_offset(at)) / 60000);

    const local: number = (((hour * 60 + minute + shift) % DAY_MINUTES) + DAY_MINUTES) % DAY_MINUTES;

    return hour_text(Math.floor(local / 60), local % 60);
}

//time if its today, weekday this week, month and day before that, on the viewers clock
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

//days come as plain date strings, formatting them in utc keeps the day from shifting
export function day_text(date: string, options: Intl.DateTimeFormatOptions): string {
    const key: string = JSON.stringify(options);

    let format: Intl.DateTimeFormat | undefined = DAY_FORMATS.get(key);

    if(format === undefined) {
        format = new Intl.DateTimeFormat("en-US", Object.assign({"timeZone": "UTC"}, options));

        DAY_FORMATS.set(key, format);
    }

    return format.format(utc_day(date));
}

//today, yesterday or the weekday and date, for a date on the viewers own clock
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

//just the hour like 10 AM, the minutes only show up when its past the hour
export function hour_text(hour: number, minute: number = 0): string {
    let twelve_hour: number = hour % 12;

    //noon and midnight come out as 0, clocks say 12
    if(!twelve_hour) {
        twelve_hour = 12;
    }

    let half: string = "PM";

    if(hour < 12) {
        half = "AM";
    }

    if(minute > 0) {
        return `${twelve_hour}:${String(minute).padStart(2, "0")} ${half}`;
    }

    return `${twelve_hour} ${half}`;
}

//us numbers get the usual area code look, anything else stays how it came
export function readable_id(id: string): string {
    const us: RegExpExecArray | null = US_NUMBER.exec(id);

    if(us === null) {
        return id;
    }

    return `(${us[1]}) ${us[2]}-${us[3]}`;
}


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


//START

if(SIGN_OUT_BUTTON !== null) {
    SIGN_OUT_BUTTON.addEventListener("click", sign_out);
}
