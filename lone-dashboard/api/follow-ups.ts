//**********IMPORTS**********
//the replies, the database, the sign in check and the feed's shapes
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";



//**********GLOBALS**********
//when follow ups get picked and sent, and what a customer looks like


//HOURS
//keep in step with PREP_HOUR, FOLLOWUP_HOUR and RECHECK_MINUTES in src/followup.py, picked at night, checked again that many minutes before the morning's send, shop time
const PICK_HOUR: number = 22;

const SEND_HOUR: number = 10;

const RECHECK_MINUTES: number = 10;


//FOLLOW UP
//number is which follow up in a row it is, counted since they last wrote
type FOLLOW_UP = {at: number; number: number};


//CUSTOMER
//tab is where their conversation sits on Messages, null once it was deleted there
type CUSTOMER = {id: string; name: string; channel: string; tab: shop.TAB | null; due: FOLLOW_UP | null; sent: FOLLOW_UP[]};



//**********CUSTOMERS**********
//reads the feed's follow ups and groups them by customer


//FOLLOW UP OF
//a follow up as the feed writes it (helpers/state/dashboard.py), null for anything else
function follow_up_of(fields: Record<string, unknown>): FOLLOW_UP | null {
    const at: number = Number(fields.at);

    const number: number = Number(fields.number);

    if(!Number.isFinite(at) || at <= 0) {
        return null;
    }

    let count: number = 1;

    if(Number.isInteger(number) && number > 0) {
        count = number;
    }

    return {"at": at, "number": count};
}


//CUSTOMER IN
function customer_in(customers: Map<string, CUSTOMER>, id: string, channel: string): CUSTOMER {
    let customer: CUSTOMER | undefined = customers.get(id);

    if(customer === undefined) {
        customer = {"id": id, "name": "", "channel": channel, "tab": null, "due": null, "sent": []};

        customers.set(id, customer);
    }

    //lines are read oldest first, so this ends on the channel of their newest follow up
    if(channel) {
        customer.channel = channel;
    }

    return customer;
}


//NEWEST SENT
function newest_sent(customer: CUSTOMER): number {
    const last: FOLLOW_UP | undefined = customer.sent[customer.sent.length - 1];

    if(last === undefined) {
        return 0;
    }

    return last.at;
}


//BY NEXT
//the ones getting a follow up first, soonest first, then everyone else by their newest one
function by_next(a: CUSTOMER, b: CUSTOMER): number {
    if(a.due !== null && b.due !== null) {
        return a.due.at - b.due.at || newest_sent(b) - newest_sent(a);
    }

    if(a.due !== null) {
        return -1;
    }

    if(b.due !== null) {
        return 1;
    }

    return newest_sent(b) - newest_sent(a);
}



//**********FOLLOW UPS**********
//who gets one at the next morning's send, and every one that went out in the last two weeks


//READ FOLLOW UPS
//someone switched off, or on a channel switched off, gets nothing in the morning, so they don't show as getting one
async function read_follow_ups(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const results: unknown[] = await redis.pipeline([["HGETALL", "followups:due"], ["ZRANGE", "followups:sent", 0, -1], ["SMEMBERS", "off"], ["SMEMBERS", "off_tabs"]]);

    const off: Set<string> = new Set(redis.as_strings(results[2]));

    const off_tabs: Set<string> = new Set(redis.as_strings(results[3]));

    const customers: Map<string, CUSTOMER> = new Map();

    for(const line of redis.as_strings(results[1])) {
        const fields: Record<string, unknown> = shop.fields_of(shop.parse_json(line));

        const sent: FOLLOW_UP | null = follow_up_of(fields);

        if(typeof fields.id === "string" && sent !== null) {
            customer_in(customers, fields.id, String(fields.channel ?? "")).sent.push(sent);
        }
    }

    const due_entries: [string, string][] = Object.entries(redis.as_object(results[0]));

    for(const entry of due_entries) {
        const id: string = entry[0];

        const fields: Record<string, unknown> = shop.fields_of(shop.parse_json(entry[1]));

        const due: FOLLOW_UP | null = follow_up_of(fields);

        const channel: string = String(fields.channel ?? "");

        if(due !== null && !off.has(id) && !off_tabs.has(shop.tab_of(channel))) {
            customer_in(customers, id, channel).due = due;
        }
    }

    const ids: string[] = [];

    for(const id of customers.keys()) {
        ids.push(id);
    }

    let summaries: string[] = [];

    if(ids.length > 0) {
        summaries = redis.as_strings(await redis.command(["HMGET", "summaries", ...ids]));
    }

    for(let index: number = 0; index < ids.length; index++) {
        const id: string = ids[index] ?? "";

        const summary: shop.SUMMARY | null = shop.parse_summary(summaries[index]);

        const customer: CUSTOMER | undefined = customers.get(id);

        if(summary !== null && customer !== undefined) {
            customer.name = summary.name;

            customer.tab = summary.tab;
        }
    }

    const list: CUSTOMER[] = [];

    for(const customer of customers.values()) {
        list.push(customer);
    }

    list.sort(by_next);

    return http.json({"pick_hour": PICK_HOUR, "send_hour": SEND_HOUR, "recheck_minutes": RECHECK_MINUTES, "customers": list});
}



//**********ROUTE**********
//what vercel runs for GET /api/follow-ups


//GET
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_follow_ups, request);
}
