//IMPORTS

import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";


//GLOBALS

//keep in step with BEAT_SECONDS in the dashboard state file, later than this means offline
const BEAT_SECONDS: number = 300;

type RANGE = "day" | "week" | "month" | "ytd";

const RANGES: RANGE[] = ["day", "week", "month", "ytd"];

const HOURS_IN_DAY: number = 24;

const DAYS_IN_WEEK: number = 7;

const MONTHS_IN_YEAR: number = 12;

//the feed keeps a set of these per hour, day, month and year, counted once as din and so on
const PEOPLE: string[] = ["in", "out", "quoted", "hil", "booked"];

//what each chart bar carries
const BAR_FIELDS: string[] = ["din", "dout", "dquoted", "hil", "booked"];

//the strip needs these totals too
const TOTAL_FIELDS: string[] = BAR_FIELDS.concat(["dhil", "dbooked"]);

//plain counts add up across a weeks days, the once per customer ones don't
const SUMMED_FIELDS: string[] = ["hil", "booked"];

//hash is which of the plans hashes the bar reads, suffix is where its numbers sit in it
type BAR_PLAN = {key: string; hash: number; suffix: string; future: boolean};

type PLAN = {from: string; to: string; hashes: string[]; bars: BAR_PLAN[]; week_dates: string[]};


//COUNTS

//each fields number in a hash at one suffix, zero for any it doesn't have
function counts(fields: string[], hash: Record<string, string>, suffix: string): Record<string, number> {
    const values: Record<string, number> = {};

    for(const field of fields) {
        values[field] = redis.as_number(hash[`${field}${suffix}`]);
    }

    return values;
}

//day, week, month or ytd, nothing else gets a chart
function is_range(value: string | null): value is RANGE {
    for(const range of RANGES) {
        if(range === value) {
            return true;
        }
    }

    return false;
}

//pads to two digits, so seven becomes 07
function two_digits(number: number): string {
    return String(number).padStart(2, "0");
}


//PLANS

//one bar per hour today, the ones past the current hour are future
function plan_day(today: string, hour: number): PLAN {
    const bars: BAR_PLAN[] = [];

    for(let each: number = 0; each < HOURS_IN_DAY; each++) {
        const key: string = two_digits(each);

        bars.push({"key": key, "hash": 0, "suffix": `@${key}`, "future": each > hour});
    }

    return {"from": today, "to": today, "hashes": [`day:${today}`], "bars": bars, "week_dates": []};
}

//a week can cross into the next month, so it may read two month hashes
function plan_week(today: string): PLAN {
    const monday: string = shop.add_days(today, -shop.weekday_index(today));

    const dates: string[] = [];

    for(let each: number = 0; each < DAYS_IN_WEEK; each++) {
        dates.push(shop.add_days(monday, each));
    }

    const months: string[] = [];

    for(const date of dates) {
        const month: string = date.slice(0, 7);

        if(!months.includes(month)) {
            months.push(month);
        }
    }

    const bars: BAR_PLAN[] = [];

    for(const date of dates) {
        bars.push({"key": date, "hash": months.indexOf(date.slice(0, 7)), "suffix": `@${date.slice(8)}`, "future": date > today});
    }

    const hashes: string[] = [];

    for(const month of months) {
        hashes.push(`month:${month}`);
    }

    const week_dates: string[] = [];

    for(const date of dates) {
        if(date <= today) {
            week_dates.push(date);
        }
    }

    let to: string | undefined = dates[6];

    if(to === undefined) {
        to = today;
    }

    return {"from": monday, "to": to, "hashes": hashes, "bars": bars, "week_dates": week_dates};
}

//one bar per day of this month, the last day is where it ends
function plan_month(today: string): PLAN {
    const month: string = today.slice(0, 7);

    const length: number = shop.days_in_month(month);

    const bars: BAR_PLAN[] = [];

    for(let each: number = 0; each < length; each++) {
        const date: string = `${month}-${two_digits(each + 1)}`;

        bars.push({"key": date, "hash": 0, "suffix": `@${date.slice(8)}`, "future": date > today});
    }

    let to: string = today;

    const last: BAR_PLAN | undefined = bars[bars.length - 1];

    if(last !== undefined) {
        to = last.key;
    }

    return {"from": `${month}-01`, "to": to, "hashes": [`month:${month}`], "bars": bars, "week_dates": []};
}

//year to date, a month is in the future once its past this one
function plan_year(today: string): PLAN {
    const month: string = today.slice(0, 7);

    const year: string = today.slice(0, 4);

    const bars: BAR_PLAN[] = [];

    for(let each: number = 0; each < MONTHS_IN_YEAR; each++) {
        const number: string = two_digits(each + 1);

        bars.push({"key": `${year}-${number}`, "hash": 0, "suffix": `@${number}`, "future": `${year}-${number}` > month});
    }

    return {"from": `${year}-01-01`, "to": today, "hashes": [`year:${year}`], "bars": bars, "week_dates": []};
}

//the layout for whichever range got picked, ytd is whats left
function plan(range: RANGE, today: string, hour: number): PLAN {
    if(range === "day") {
        return plan_day(today, hour);
    }

    if(range === "week") {
        return plan_week(today);
    }

    if(range === "month") {
        return plan_month(today);
    }

    return plan_year(today);
}


//OVERVIEW

//once per customer week totals come from day sets, so writing monday and friday counts once
function week_sets(week_dates: string[]): redis.COMMAND[] {
    const commands: redis.COMMAND[] = [];

    if(week_dates.length === 0) {
        return commands;
    }

    for(const direction of PEOPLE) {
        const union: redis.COMMAND = ["SUNION"];

        for(const date of week_dates) {
            union.push(`day:${date}:${direction}`);
        }

        commands.push(union);
    }

    return commands;
}

//one chart bar, its key, whether its still ahead and its numbers
function make_bar(bar: BAR_PLAN, hash: Record<string, string>): Record<string, string | boolean | number> {
    const made: Record<string, string | boolean | number> = {"key": bar.key, "future": bar.future};

    const values: Record<string, number> = counts(BAR_FIELDS, hash, bar.suffix);

    for(const field of BAR_FIELDS) {
        let value: number | undefined = values[field];

        if(value === undefined) {
            value = 0;
        }

        made[field] = value;
    }

    return made;
}

//starts at zero, adds up the plain counts of the days so far, then the d fields are the set sizes
function week_totals(layout: PLAN, hashes: Record<string, string>[], results: unknown[], sets_at: number): Record<string, number> {
    const totals: Record<string, number> = counts(TOTAL_FIELDS, {}, "");

    for(const bar of layout.bars) {
        if(bar.future) {
            continue;
        }

        let hash: Record<string, string> | undefined = hashes[bar.hash];

        if(hash === undefined) {
            hash = {};
        }

        const day: Record<string, number> = counts(SUMMED_FIELDS, hash, bar.suffix);

        for(const field of SUMMED_FIELDS) {
            let total: number | undefined = totals[field];

            if(total === undefined) {
                total = 0;
            }

            let added: number | undefined = day[field];

            if(added === undefined) {
                added = 0;
            }

            totals[field] = total + added;
        }
    }

    for(let index: number = 0; index < PEOPLE.length; index++) {
        totals[`d${PEOPLE[index]}`] = redis.as_strings(results[sets_at + index]).length;
    }

    return totals;
}

//the chart, its totals and the systems check in for the picked range
async function read_overview(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    let range: string | null = new URL(request.url).searchParams.get("range");

    if(range === null) {
        range = "day";
    }

    if(!is_range(range)) {
        return http.fail(400, `Pick a range: ${RANGES.join(", ")}.`);
    }

    const clock: shop.CLOCK = shop.shop_clock(new Date());

    const layout: PLAN = plan(range, clock.date, clock.hour);

    const commands: redis.COMMAND[] = [];

    for(const key of layout.hashes) {
        commands.push(["HGETALL", key]);
    }

    commands.push(["GET", "up_last"]);

    commands.push(["ZCOUNT", "followups:sent", shop.day_start(clock.date), "+inf"]);

    for(const set_command of week_sets(layout.week_dates)) {
        commands.push(set_command);
    }

    const results: unknown[] = await redis.pipeline(commands);

    const hashes: Record<string, string>[] = [];

    for(let index: number = 0; index < layout.hashes.length; index++) {
        hashes.push(redis.as_object(results[index]));
    }

    //the hash results come first, then up_last, then todays follow ups, then the week sets
    const at: number = layout.hashes.length;

    const up_last: number = redis.as_number(results[at]);

    const follow_ups_today: number = redis.as_number(results[at + 1]);

    const bars: Record<string, string | boolean | number>[] = [];

    for(const bar of layout.bars) {
        let hash: Record<string, string> | undefined = hashes[bar.hash];

        if(hash === undefined) {
            hash = {};
        }

        bars.push(make_bar(bar, hash));
    }

    let totals: Record<string, number> = {};

    if(range === "week") {
        totals = week_totals(layout, hashes, results, at + 2);
    }
    else {
        let first_hash: Record<string, string> | undefined = hashes[0];

        if(first_hash === undefined) {
            first_hash = {};
        }

        totals = counts(TOTAL_FIELDS, first_hash, "");
    }

    return http.json({"range": range, "from": layout.from, "to": layout.to, "today": clock.date, "totals": totals, "follow_ups_today": follow_ups_today, "bars": bars, "check_in": {"last_seen": up_last, "beat_seconds": BEAT_SECONDS}});
}


//ROUTE

//numbers for the overview page
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_overview, request);
}
