//**********IMPORTS**********
//the replies, the database, the sign in check and the shop's dates
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";



//**********GLOBALS**********
//the ranges, the fields the feed counts and the shape of a plan


//BEAT SECONDS
//keep in step with BEAT_SECONDS in helpers/state/dashboard.py, a check in later than this means it's offline
const BEAT_SECONDS: number = 300;


//RANGES
type RANGE = "day" | "week" | "month" | "ytd";

const RANGES: RANGE[] = ["day", "week", "month", "ytd"];


//CALENDAR
const HOURS_IN_DAY: number = 24;

const DAYS_IN_WEEK: number = 7;

const MONTHS_IN_YEAR: number = 12;


//FIELDS
//feed keeps a set of these per hour, day, month and year, each counted once as a d field ("in" becomes "din")
const PEOPLE: string[] = ["in", "out", "quoted", "hil", "booked"];

//what each chart bar carries
const BAR_FIELDS: string[] = ["din", "dout", "dquoted", "hil", "booked"];

//the strip needs these totals too
const TOTAL_FIELDS: string[] = [...BAR_FIELDS, "dhil", "dbooked"];

//plain counts add up across a week's days, the once per customer ones don't
const SUMMED_FIELDS: string[] = ["hil", "booked"];


//PLAN TYPES
//hash is which of the plan's hashes the bar reads, suffix is where its numbers sit in it
type BAR_PLAN = {key: string; hash: number; suffix: string; future: boolean};

type PLAN = {from: string; to: string; hashes: string[]; bars: BAR_PLAN[]; week_dates: string[]};



//**********COUNTS**********
//reads the numbers out of the feed's hashes


//COUNTS
function counts(fields: string[], hash: Record<string, string>, suffix: string): Record<string, number> {
    const values: Record<string, number> = {};

    for(const field of fields) {
        values[field] = redis.as_number(hash[`${field}${suffix}`]);
    }

    return values;
}


//IS RANGE
function is_range(value: string | null): value is RANGE {
    for(const range of RANGES) {
        if(range === value) {
            return true;
        }
    }

    return false;
}


//TWO DIGITS
function two_digits(number: number): string {
    return String(number).padStart(2, "0");
}



//**********PLANS**********
//which hashes to read and where each bar's numbers sit, the feed keeps a day by hour, a month by day and a year by month


//PLAN DAY
function plan_day(today: string, hour: number): PLAN {
    const bars: BAR_PLAN[] = [];

    for(let each: number = 0; each < HOURS_IN_DAY; each++) {
        const key: string = two_digits(each);

        bars.push({"key": key, "hash": 0, "suffix": `@${key}`, "future": each > hour});
    }

    return {"from": today, "to": today, "hashes": [`day:${today}`], "bars": bars, "week_dates": []};
}


//PLAN WEEK
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

    return {"from": monday, "to": dates[6] ?? today, "hashes": hashes, "bars": bars, "week_dates": week_dates};
}


//PLAN MONTH
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


//PLAN YEAR
//year to date, a month is in the future once it's past this one
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


//PLAN
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



//**********OVERVIEW**********
//the numbers for a range, the bars behind them, today's follow ups and the last check in


//WEEK SETS
//a week's once per customer totals come from the day sets, so someone who wrote monday and friday counts once
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


//MAKE BAR
function make_bar(bar: BAR_PLAN, hash: Record<string, string>): Record<string, string | boolean | number> {
    const made: Record<string, string | boolean | number> = {"key": bar.key, "future": bar.future};

    const values: Record<string, number> = counts(BAR_FIELDS, hash, bar.suffix);

    for(const field of BAR_FIELDS) {
        made[field] = values[field] ?? 0;
    }

    return made;
}


//WEEK TOTALS
//starts at zero, adds up the plain counts of the days so far, then the d fields are the set sizes
function week_totals(layout: PLAN, hashes: Record<string, string>[], results: unknown[], sets_at: number): Record<string, number> {
    const totals: Record<string, number> = counts(TOTAL_FIELDS, {}, "");

    for(const bar of layout.bars) {
        if(bar.future) {
            continue;
        }

        const day: Record<string, number> = counts(SUMMED_FIELDS, hashes[bar.hash] ?? {}, bar.suffix);

        for(const field of SUMMED_FIELDS) {
            totals[field] = (totals[field] ?? 0) + (day[field] ?? 0);
        }
    }

    for(let index: number = 0; index < PEOPLE.length; index++) {
        totals[`d${PEOPLE[index]}`] = redis.as_strings(results[sets_at + index]).length;
    }

    return totals;
}


//READ OVERVIEW
async function read_overview(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const range: string = new URL(request.url).searchParams.get("range") ?? "day";

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

    commands.push(...week_sets(layout.week_dates));

    const results: unknown[] = await redis.pipeline(commands);

    const hashes: Record<string, string>[] = [];

    for(let index: number = 0; index < layout.hashes.length; index++) {
        hashes.push(redis.as_object(results[index]));
    }

    //the hash results come first, then up_last, then today's follow ups, then the week sets
    const at: number = layout.hashes.length;

    const up_last: number = redis.as_number(results[at]);

    const follow_ups_today: number = redis.as_number(results[at + 1]);

    const bars: Record<string, string | boolean | number>[] = [];

    for(const bar of layout.bars) {
        bars.push(make_bar(bar, hashes[bar.hash] ?? {}));
    }

    let totals: Record<string, number> = {};

    if(range === "week") {
        totals = week_totals(layout, hashes, results, at + 2);
    }

    else {
        totals = counts(TOTAL_FIELDS, hashes[0] ?? {}, "");
    }

    return http.json({"range": range, "from": layout.from, "to": layout.to, "today": clock.date, "totals": totals, "follow_ups_today": follow_ups_today, "bars": bars, "check_in": {"last_seen": up_last, "beat_seconds": BEAT_SECONDS}});
}



//**********ROUTE**********
//what vercel runs for GET /api/overview


//GET
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_overview, request);
}
