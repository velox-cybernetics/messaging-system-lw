//**********IMPORTS**********
//the replies, the database, the sign in check and the feed's shapes
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";



//**********GLOBALS**********
//what a ledger count turns into


//COUNT
//one count to take back, the hash, the field in it and how much
type COUNT = {key: string; field: string; amount: number};



//**********CLEANUP**********
//everything a deleted conversation left behind


//PIC KEYS
//the pic copies a thread kept, so deleting it takes them too
function pic_keys(entries: Record<string, unknown>[]): string[] {
    const keys: string[] = [];

    for(const entry of entries) {
        let parts: unknown[] = [];

        if(Array.isArray(entry.parts)) {
            parts = entry.parts;
        }

        for(const part of parts) {
            const media: Record<string, unknown> = shop.fields_of(shop.fields_of(part).media);

            if(media.kind === "pic" && typeof media.id === "string") {
                keys.push(`media:${media.id}`);
            }
        }
    }

    return keys;
}


//TAKE BACK
//keep in step with ledger_commands in dashboard.py, aged out hashes get skipped so old days never go negative
async function take_back_commands(id: string): Promise<redis.COMMAND[]> {
    const ledger: unknown[] = await redis.pipeline([["HGETALL", `ledger:${id}`], ["SMEMBERS", `ledger_sets:${id}`]]);

    const counts: COUNT[] = [];

    //places look like "day:2026-10-29|in@14"
    for(const entry of Object.entries(redis.as_object(ledger[0]))) {
        const place: string = entry[0];

        const cut: number = place.lastIndexOf("|");

        const amount: number = redis.as_number(entry[1]);

        if(cut > 0 && amount !== 0) {
            counts.push({"key": place.slice(0, cut), "field": place.slice(cut + 1), "amount": amount});
        }
    }

    const hash_keys: string[] = [];

    for(const count of counts) {
        if(!hash_keys.includes(count.key)) {
            hash_keys.push(count.key);
        }
    }

    const exists_commands: redis.COMMAND[] = [];

    for(const key of hash_keys) {
        exists_commands.push(["EXISTS", key]);
    }

    const exists: unknown[] = await redis.pipeline(exists_commands);

    const live: Set<string> = new Set();

    for(let index: number = 0; index < hash_keys.length; index++) {
        if(redis.as_number(exists[index]) === 1) {
            live.add(hash_keys[index] ?? "");
        }
    }

    const commands: redis.COMMAND[] = [];

    for(const count of counts) {
        if(live.has(count.key)) {
            commands.push(["HINCRBY", count.key, count.field, -count.amount]);
        }
    }

    for(const key of redis.as_strings(ledger[1])) {
        commands.push(["SREM", key, id]);
    }

    commands.push(["DEL", `ledger:${id}`, `ledger_sets:${id}`]);

    return commands;
}


//FOLLOW UPS
//a picked one the system still sends shows up again with the new conversation it starts
async function follow_up_commands(id: string): Promise<redis.COMMAND[]> {
    const theirs: string[] = [];

    for(const line of redis.as_strings(await redis.command(["ZRANGE", "followups:sent", 0, -1]))) {
        if(shop.fields_of(shop.parse_json(line)).id === id) {
            theirs.push(line);
        }
    }

    const commands: redis.COMMAND[] = [["HDEL", "followups:due", id]];

    if(theirs.length > 0) {
        commands.push(["ZREM", "followups:sent", ...theirs]);
    }

    return commands;
}



//**********THREAD**********
//one conversation, read whole or deleted whole


//READ THREAD
//summary, every entry oldest first, whether it or its channel is off, and its flag
async function read_thread(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const id: string | null = new URL(request.url).searchParams.get("id");

    if(!shop.valid_id(id)) {
        return http.fail(400, "That conversation id isn't valid.");
    }

    const results: unknown[] = await redis.pipeline([["HGET", "summaries", id], ["LRANGE", `thread:${id}`, 0, -1], ["SISMEMBER", "off", id], ["SMEMBERS", "off_tabs"], ["HGET", "flagged", id]]);

    const summary: shop.SUMMARY | null = shop.parse_summary(results[0]);

    if(summary === null) {
        return http.fail(404, "No conversation with that id. It was deleted or is over a year old.");
    }

    const convo: Record<string, unknown> = {"id": summary.id, "tab": summary.tab, "channel": summary.channel, "name": summary.name, "last_at": summary.last_at, "last_kind": summary.last_kind, "last_text": summary.last_text, "off": redis.as_number(results[2]) === 1, "tab_off": redis.as_strings(results[3]).includes(summary.tab), "flagged_at": redis.as_number(results[4])};

    return http.json({"convo": convo, "entries": shop.parse_entries(results[1])});
}


//DELETE THREAD
//takes everything kept for it and its overview counts, but the customer's switch stays so off stays off
async function delete_thread(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const id: string | null = new URL(request.url).searchParams.get("id");

    if(!shop.valid_id(id)) {
        return http.fail(400, "That conversation id isn't valid.");
    }

    //all three reads at once
    const reads: [unknown, redis.COMMAND[], redis.COMMAND[]] = await Promise.all([redis.command(["LRANGE", `thread:${id}`, 0, -1]), take_back_commands(id), follow_up_commands(id)]);

    const pics: string[] = pic_keys(shop.parse_entries(reads[0]));

    const commands: redis.COMMAND[] = [...reads[1], ...reads[2], ["DEL", `thread:${id}`, `state:${id}`, `writer:${id}`, ...pics], ["HDEL", "summaries", id], ["HDEL", "flagged", id]];

    for(const tab of shop.TABS) {
        commands.push(["ZREM", `convos:${tab}`, id]);
    }

    commands.push(["INCR", "version"]);

    await redis.pipeline(commands);

    return http.json({"id": id, "deleted": true});
}



//**********ROUTE**********
//what vercel runs for GET and DELETE /api/thread


//GET
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_thread, request);
}


//DELETE
export function DELETE(request: Request): Promise<Response> {
    return http.guarded(delete_thread, request);
}
