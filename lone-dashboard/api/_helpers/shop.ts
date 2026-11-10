//GLOBALS

//same zone the python calendar helpers use
export const SHOP_TIME_ZONE: string = "America/Denver";

//forms holds texts too, form leads get answered by text
export type TAB = "forms" | "instagram" | "messenger";

export const TABS: TAB[] = ["forms", "instagram", "messenger"];

//same as TABS in the python dashboard state helper
const CHANNEL_TABS: Record<string, TAB> = {"blooio": "forms", "ig": "instagram", "messenger": "messenger", "meta-form": "forms", "website-form": "forms"};

export type SUMMARY = {id: string; tab: TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string};

export type CLOCK = {date: string; hour: number; minute: number};

//any printable text is fine, ids only land in redis keys, encoded urls and textContent
const ID_PATTERN: RegExp = /^[^\u0000-\u001f\u007f]{3,64}$/;

const DAY_MS: number = 86400 * 1000;


//SETTINGS

//a vercel setting, or the fallback when it was never set at all
export function setting(value: string | undefined, fallback: string): string {
    if(value === undefined) {
        return fallback;
    }

    return value;
}


//TABS

//true only for one of the three tabs, everything else is a typo
export function is_tab(value: unknown): value is TAB {
    for(const tab of TABS) {
        if(value === tab) {
            return true;
        }
    }

    return false;
}

//forms for a channel it doesn't know yet
export function tab_of(channel: string): TAB {
    const tab: TAB | undefined = CHANNEL_TABS[channel];

    if(tab === undefined) {
        return "forms";
    }

    return tab;
}


//PARSING

//any json object as plain fields, empty for anything else
export function fields_of(value: unknown): Record<string, unknown> {
    if(value !== null && typeof value === "object" && !Array.isArray(value)) {
        return Object.fromEntries(Object.entries(value));
    }

    return {};
}

//null when it isn't text or isn't json
export function parse_json(text: unknown): unknown {
    if(typeof text !== "string") {
        return null;
    }

    try {
        return JSON.parse(text);
    }
    catch {
        return null;
    }
}

//null when its missing its id or tab
export function parse_summary(text: unknown): SUMMARY | null {
    const fields: Record<string, unknown> = fields_of(parse_json(text));

    if(typeof fields.id !== "string" || !is_tab(fields.tab)) {
        return null;
    }

    let last_kind: "in" | "out" = "in";

    if(fields.last_kind === "out") {
        last_kind = "out";
    }

    let channel: unknown = fields.channel;

    if(channel === undefined || channel === null) {
        channel = "";
    }

    let name: unknown = fields.name;

    if(name === undefined || name === null) {
        name = "";
    }

    let last_at: unknown = fields.last_at;

    if(last_at === undefined || last_at === null) {
        last_at = 0;
    }

    let last_text: unknown = fields.last_text;

    if(last_text === undefined || last_text === null) {
        last_text = "";
    }

    return {"id": fields.id, "tab": fields.tab, "channel": String(channel), "name": String(name), "last_at": Number(last_at), "last_kind": last_kind, "last_text": String(last_text)};
}

//oldest first, skips any line the feed didn't write
export function parse_entries(list: unknown): Record<string, unknown>[] {
    const entries: Record<string, unknown>[] = [];

    if(!Array.isArray(list)) {
        return entries;
    }

    for(const text of list) {
        const fields: Record<string, unknown> = fields_of(parse_json(text));

        if(typeof fields.kind === "string" && typeof fields.at === "number") {
            entries.push(fields);
        }
    }

    return entries;
}

//a blooio or meta id, or a phone number typed any which way on a quote form
export function valid_id(value: unknown): value is string {
    return typeof value === "string" && ID_PATTERN.test(value);
}


//SHOP TIME

//one piece of the formatted clock, 00 if intl somehow left it out
function clock_part(parts: Intl.DateTimeFormatPart[], type: string): string {
    for(const part of parts) {
        if(part.type === type) {
            return part.value;
        }
    }

    return "00";
}

//the shops date, hour and minute at that moment
export function shop_clock(at: Date): CLOCK {
    const parts: Intl.DateTimeFormatPart[] = new Intl.DateTimeFormat("en-CA", {"timeZone": SHOP_TIME_ZONE, "year": "numeric", "month": "2-digit", "day": "2-digit", "hour": "2-digit", "minute": "2-digit", "hourCycle": "h23"}).formatToParts(at);

    const date: string = `${clock_part(parts, "year")}-${clock_part(parts, "month")}-${clock_part(parts, "day")}`;

    return {"date": date, "hour": Number(clock_part(parts, "hour")), "minute": Number(clock_part(parts, "minute"))};
}

//day math in utc so daylight saving never skips or repeats a day
function utc_day(date: string): number {
    const pieces: string[] = date.split("-");

    let year: number = 1970;

    const year_piece: string | undefined = pieces[0];

    if(year_piece !== undefined) {
        year = Number(year_piece);
    }

    let month: number = 1;

    const month_piece: string | undefined = pieces[1];

    if(month_piece !== undefined) {
        month = Number(month_piece);
    }

    let day: number = 1;

    const day_piece: string | undefined = pieces[2];

    if(day_piece !== undefined) {
        day = Number(day_piece);
    }

    return Date.UTC(year, month - 1, day);
}

//denver changes clocks at 2 AM, so its offset at midnight matches the evening before
export function day_start(date: string): number {
    const utc_midnight: number = utc_day(date);

    const clock: CLOCK = shop_clock(new Date(utc_midnight));

    const shop_time: number = utc_day(clock.date) + (clock.hour * 60 + clock.minute) * 60 * 1000;

    return utc_midnight + (utc_midnight - shop_time);
}

//the date that many days later, or earlier when days is negative
export function add_days(date: string, days: number): string {
    return new Date(utc_day(date) + days * DAY_MS).toISOString().slice(0, 10);
}

//monday is 0 and sunday is 6, the way the shop counts a week
export function weekday_index(date: string): number {
    return (new Date(utc_day(date)).getUTCDay() + 6) % 7;
}

//how many days that month has, day 0 of the next month is its last
export function days_in_month(month: string): number {
    const pieces: string[] = month.split("-");

    let year: number = 1970;

    const year_piece: string | undefined = pieces[0];

    if(year_piece !== undefined) {
        year = Number(year_piece);
    }

    let number: number = 1;

    const number_piece: string | undefined = pieces[1];

    if(number_piece !== undefined) {
        number = Number(number_piece);
    }

    return new Date(Date.UTC(year, number, 0)).getUTCDate();
}

//this shop year and the one before, so january still shows decembers bookings
export function booked_keys(date: string): string[] {
    const year: number = Number(date.slice(0, 4));

    return [`year:${year}:booked`, `year:${year - 1}:booked`];
}
