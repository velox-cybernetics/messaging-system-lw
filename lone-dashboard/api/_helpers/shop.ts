//**********GLOBALS**********
//what the python feed writes, keep in step with helpers/state/dashboard.py


//SHOP TIME ZONE
//same as helpers/calendar/open_dates.py
export const SHOP_TIME_ZONE: string = "America/Denver";


//TABS
//forms holds texts too, form leads get answered by text
export type TAB = "forms" | "instagram" | "messenger";

export const TABS: TAB[] = ["forms", "instagram", "messenger"];


//CHANNEL TABS
//same as TABS in helpers/state/dashboard.py
const CHANNEL_TABS: Record<string, TAB> = {"blooio": "forms", "ig": "instagram", "messenger": "messenger", "meta-form": "forms", "website-form": "forms"};


//SUMMARY
export type SUMMARY = {id: string; tab: TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string};


//CLOCK
export type CLOCK = {date: string; hour: number; minute: number};


//ID PATTERN
//any printable text is fine, ids only land in redis keys, encoded urls and textContent
const ID_PATTERN: RegExp = /^[^\u0000-\u001f\u007f]{3,64}$/;


//DAY
const DAY_MS: number = 86400 * 1000;



//**********TABS**********
//which tab a conversation lands under


//IS TAB
export function is_tab(value: unknown): value is TAB {
    for(const tab of TABS) {
        if(value === tab) {
            return true;
        }
    }

    return false;
}


//TAB OF
//forms for a channel it doesn't know yet
export function tab_of(channel: string): TAB {
    return CHANNEL_TABS[channel] ?? "forms";
}



//**********PARSING**********
//reads what the feed wrote, every field gets checked before it's used


//FIELDS OF
//any json object as plain fields, empty for anything else
export function fields_of(value: unknown): Record<string, unknown> {
    if(value !== null && typeof value === "object" && !Array.isArray(value)) {
        return Object.fromEntries(Object.entries(value));
    }

    return {};
}


//PARSE JSON
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


//PARSE SUMMARY
//null when it's missing its id or tab
export function parse_summary(text: unknown): SUMMARY | null {
    const fields: Record<string, unknown> = fields_of(parse_json(text));

    if(typeof fields.id !== "string" || !is_tab(fields.tab)) {
        return null;
    }

    let last_kind: "in" | "out" = "in";

    if(fields.last_kind === "out") {
        last_kind = "out";
    }

    return {"id": fields.id, "tab": fields.tab, "channel": String(fields.channel ?? ""), "name": String(fields.name ?? ""), "last_at": Number(fields.last_at ?? 0), "last_kind": last_kind, "last_text": String(fields.last_text ?? "")};
}


//PARSE ENTRIES
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


//VALID ID
//a blooio or meta id, or a phone number just how a lead typed it on a quote form ("(303) 555-1234")
export function valid_id(value: unknown): value is string {
    return typeof value === "string" && ID_PATTERN.test(value);
}



//**********SHOP TIME**********
//dates in the shop's timezone, so a day starts at the shop's midnight


//CLOCK PART
function clock_part(parts: Intl.DateTimeFormatPart[], type: string): string {
    for(const part of parts) {
        if(part.type === type) {
            return part.value;
        }
    }

    return "00";
}


//SHOP CLOCK
//the shop's date (YYYY-MM-DD), hour and minute at that moment
export function shop_clock(at: Date): CLOCK {
    const parts: Intl.DateTimeFormatPart[] = new Intl.DateTimeFormat("en-CA", {"timeZone": SHOP_TIME_ZONE, "year": "numeric", "month": "2-digit", "day": "2-digit", "hour": "2-digit", "minute": "2-digit", "hourCycle": "h23"}).formatToParts(at);

    const date: string = `${clock_part(parts, "year")}-${clock_part(parts, "month")}-${clock_part(parts, "day")}`;

    return {"date": date, "hour": Number(clock_part(parts, "hour")), "minute": Number(clock_part(parts, "minute"))};
}


//UTC DAY
//day math in utc so daylight saving never skips or repeats a day
function utc_day(date: string): number {
    const pieces: string[] = date.split("-");

    const year: number = Number(pieces[0] ?? 1970);

    const month: number = Number(pieces[1] ?? 1);

    const day: number = Number(pieces[2] ?? 1);

    return Date.UTC(year, month - 1, day);
}


//DAY START
//denver changes clocks at 2 AM, so its offset at midnight matches the evening before
export function day_start(date: string): number {
    const utc_midnight: number = utc_day(date);

    const clock: CLOCK = shop_clock(new Date(utc_midnight));

    const shop_time: number = utc_day(clock.date) + (clock.hour * 60 + clock.minute) * 60 * 1000;

    return utc_midnight + (utc_midnight - shop_time);
}


//ADD DAYS
export function add_days(date: string, days: number): string {
    return new Date(utc_day(date) + days * DAY_MS).toISOString().slice(0, 10);
}


//WEEKDAY INDEX
//0 is monday, 6 is sunday
export function weekday_index(date: string): number {
    return (new Date(utc_day(date)).getUTCDay() + 6) % 7;
}


//DAYS IN MONTH
export function days_in_month(month: string): number {
    const pieces: string[] = month.split("-");

    const year: number = Number(pieces[0] ?? 1970);

    const number: number = Number(pieces[1] ?? 1);

    return new Date(Date.UTC(year, number, 0)).getUTCDate();
}
