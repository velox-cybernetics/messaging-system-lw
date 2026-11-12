//IMPORTS

import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";


//GLOBALS

//number counts follow ups in a row since they last wrote, sms means it went out from ghl
type FOLLOW_UP = {at: number; number: number; sms: boolean};

//tab is null once deleted from Messages, held is when blooio started holding their texts
type CUSTOMER = {id: string; name: string; channel: string; tab: shop.TAB | null; due: FOLLOW_UP | null; sent: FOLLOW_UP[]; held: number | null};


//CUSTOMERS

//a follow up the way the feed writes it, null for anything else
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

    return {"at": at, "number": count, "sms": fields.sms === true};
}

//there spot in the map, made blank the first time they show up
function customer_in(customers: Map<string, CUSTOMER>, id: string, channel: string): CUSTOMER {
    let customer: CUSTOMER | undefined = customers.get(id);

    if(customer === undefined) {
        customer = {"id": id, "name": "", "channel": channel, "tab": null, "due": null, "sent": [], "held": null};

        customers.set(id, customer);
    }

    //lines are read oldest first, so this ends on the channel of their newest follow up
    if(channel) {
        customer.channel = channel;
    }

    return customer;
}

//their newest point on the track, the next one, the last one sent, or when blooio started holding them
function newest(customer: CUSTOMER): number {
    const last: FOLLOW_UP | undefined = customer.sent[customer.sent.length - 1];

    let at: number = 0;

    if(customer.held !== null) {
        at = customer.held;
    }

    if(last !== undefined && last.at > at) {
        at = last.at;
    }

    if(customer.due !== null && customer.due.at > at) {
        at = customer.due.at;
    }

    return at;
}


//FOLLOW UPS

//anyone switched off, or on an off channel, gets nothing, so they never show as due or held
async function read_follow_ups(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const results: unknown[] = await redis.pipeline([["HGETALL", "followups:due"], ["ZRANGE", "followups:sent", 0, -1], ["SMEMBERS", "off"], ["SMEMBERS", "off_tabs"], ["HGETALL", "followups:held"]]);

    const off: Set<string> = new Set(redis.as_strings(results[2]));

    const off_tabs: Set<string> = new Set(redis.as_strings(results[3]));

    const customers: Map<string, CUSTOMER> = new Map();

    for(const line of redis.as_strings(results[1])) {
        const fields: Record<string, unknown> = shop.fields_of(shop.parse_json(line));

        const sent: FOLLOW_UP | null = follow_up_of(fields);

        if(typeof fields.id === "string" && sent !== null) {
            let channel: unknown = fields.channel;

            if(channel === undefined || channel === null) {
                channel = "";
            }

            customer_in(customers, fields.id, String(channel)).sent.push(sent);
        }
    }

    const due_entries: [string, string][] = Object.entries(redis.as_object(results[0]));

    for(const entry of due_entries) {
        const id: string = entry[0];

        const fields: Record<string, unknown> = shop.fields_of(shop.parse_json(entry[1]));

        const due: FOLLOW_UP | null = follow_up_of(fields);

        let channel_field: unknown = fields.channel;

        if(channel_field === undefined || channel_field === null) {
            channel_field = "";
        }

        const channel: string = String(channel_field);

        if(due !== null && !off.has(id) && !off_tabs.has(shop.tab_of(channel))) {
            customer_in(customers, id, channel).due = due;
        }
    }

    const held_entries: [string, string][] = Object.entries(redis.as_object(results[4]));

    for(const entry of held_entries) {
        const id: string = entry[0];

        const fields: Record<string, unknown> = shop.fields_of(shop.parse_json(entry[1]));

        const held: number = Number(fields.at);

        let channel_field: unknown = fields.channel;

        if(channel_field === undefined || channel_field === null) {
            channel_field = "";
        }

        const channel: string = String(channel_field);

        if(Number.isFinite(held) && held > 0 && !off.has(id) && !off_tabs.has(shop.tab_of(channel))) {
            customer_in(customers, id, channel).held = held;
        }
    }

    const ids: string[] = [];

    for(const id of customers.keys()) {
        ids.push(id);
    }

    let summaries: string[] = [];

    if(ids.length > 0) {
        const summaries_command: redis.COMMAND = ["HMGET", "summaries"];

        for(const id of ids) {
            summaries_command.push(id);
        }

        summaries = redis.as_strings(await redis.command(summaries_command));
    }

    for(let index: number = 0; index < ids.length; index++) {
        let id: string | undefined = ids[index];

        if(id === undefined) {
            id = "";
        }

        const summary: shop.SUMMARY | null = shop.parse_summary(summaries[index]);

        const customer: CUSTOMER | undefined = customers.get(id);

        if(summary !== null && customer !== undefined) {
            customer.name = summary.name;

            customer.tab = summary.tab;
        }
    }

    const list: CUSTOMER[] = [];

    for(const customer of customers.values()) {
        let spot: number = list.length;

        //walks back past everyone older than them, ties keep the order they came in
        while(spot > 0) {
            const before: CUSTOMER | undefined = list[spot - 1];

            if(before === undefined || newest(before) >= newest(customer)) {
                break;
            }

            spot--;
        }

        list.splice(spot, 0, customer);
    }

    return http.json({"customers": list});
}


//ROUTE

//who gets a follow up next and who already got one
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_follow_ups, request);
}
