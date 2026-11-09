//IMPORTS

import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";


//GLOBALS

const PAGE_SIZE: number = 50;

//a refresh after show older asks for everything on screen, so the list doesn't snap back
const MAX_LIMIT: number = 500;

//on is what the system answers, off is the ones switched off
type VIEW = "on" | "off";

const VIEWS: VIEW[] = ["on", "off"];

type PLACED = {id: string; at: number};

type CONVO = {id: string; tab: shop.TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string; off: boolean; flagged_at: number};


//SORTING

//on or off, anything else is a made up view
function is_view(value: unknown): value is VIEW {
    for(const view of VIEWS) {
        if(value === view) {
            return true;
        }
    }

    return false;
}

//only the ids that have a place in the tab, newest first by their last message
function newest_first(ids: string[], scores: unknown): string[] {
    const placed: PLACED[] = [];

    let list: unknown[] = [];

    if(Array.isArray(scores)) {
        list = scores;
    }

    for(let index: number = 0; index < ids.length; index++) {
        if(list[index] !== null && list[index] !== undefined) {
            let id: string | undefined = ids[index];

            if(id === undefined) {
                id = "";
            }

            const each: PLACED = {"id": id, "at": Number(list[index])};

            let spot: number = placed.length;

            //walks back past the older ones, ties keep the order they came in like sort did
            while(spot > 0) {
                const before: PLACED | undefined = placed[spot - 1];

                if(before === undefined || !(each.at > before.at)) {
                    break;
                }

                spot--;
            }

            placed.splice(spot, 0, each);
        }
    }

    const sorted: string[] = [];

    for(const each of placed) {
        sorted.push(each.id);
    }

    return sorted;
}


//CONVOS

//one page of a tabs conversations plus every count the tabs show
async function read_convos(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const params: URLSearchParams = new URL(request.url).searchParams;

    let tab: string | null = params.get("tab");

    if(tab === null) {
        tab = "forms";
    }

    if(!shop.is_tab(tab)) {
        return http.fail(400, `Unknown tab "${tab}".`);
    }

    let view: string | null = params.get("view");

    if(view === null) {
        view = "on";
    }

    if(!is_view(view)) {
        return http.fail(400, `Unknown view "${view}".`);
    }

    let start: number = 0;

    const start_text: string | null = params.get("start");

    if(start_text !== null) {
        start = Number(start_text);
    }

    start = Math.floor(start);

    //a plain falsy check on purpose, NaN falls back too
    if(!start) {
        start = 0;
    }

    start = Math.max(0, start);

    let limit: number = PAGE_SIZE;

    const limit_text: string | null = params.get("limit");

    if(limit_text !== null) {
        limit = Number(limit_text);
    }

    limit = Math.floor(limit);

    if(!limit) {
        limit = PAGE_SIZE;
    }

    limit = Math.min(MAX_LIMIT, Math.max(1, limit));

    const commands: redis.COMMAND[] = [["SMEMBERS", "off"], ["SMEMBERS", "off_tabs"]];

    for(const each of shop.TABS) {
        commands.push(["ZCARD", `convos:${each}`]);
    }

    const results: unknown[] = await redis.pipeline(commands);

    const off_ids: string[] = redis.as_strings(results[0]);

    const off_tabs: shop.TAB[] = [];

    for(const each of redis.as_strings(results[1])) {
        if(shop.is_tab(each)) {
            off_tabs.push(each);
        }
    }

    const tab_counts: Record<shop.TAB, number> = {"forms": 0, "instagram": 0, "messenger": 0};

    for(let index: number = 0; index < shop.TABS.length; index++) {
        let each: shop.TAB | undefined = shop.TABS[index];

        if(each === undefined) {
            each = "forms";
        }

        tab_counts[each] = redis.as_number(results[index + 2]);
    }

    //the off list stays short, so it comes back whole
    let off_here: string[] = [];

    if(off_ids.length > 0) {
        const score_command: redis.COMMAND = ["ZMSCORE", `convos:${tab}`];

        for(const off_id of off_ids) {
            score_command.push(off_id);
        }

        off_here = newest_first(off_ids, await redis.command(score_command));
    }

    const view_counts: Record<VIEW, number> = {"on": tab_counts[tab] - off_here.length, "off": off_here.length};

    let ids: string[] = [];

    if(view === "off") {
        ids = off_here.slice(start, start + limit);
    }
    else {
        const off_here_set: Set<string> = new Set(off_here);

        //taking the off ones out only pulls later ones up, so this many from the top fills the page
        const top: string[] = redis.as_strings(await redis.command(["ZREVRANGE", `convos:${tab}`, 0, start + limit + off_here.length - 1]));

        const kept: string[] = [];

        for(const id of top) {
            if(!off_here_set.has(id)) {
                kept.push(id);
            }
        }

        ids = kept.slice(start, start + limit);
    }

    const more: boolean = start + ids.length < view_counts[view];

    const convos: CONVO[] = [];

    if(ids.length === 0) {
        return http.json({"tab": tab, "view": view, "counts": tab_counts, "view_counts": view_counts, "off_tabs": off_tabs, "more": more, "convos": convos});
    }

    const summaries_command: redis.COMMAND = ["HMGET", "summaries"];

    const flagged_command: redis.COMMAND = ["HMGET", "flagged"];

    for(const id of ids) {
        summaries_command.push(id);

        flagged_command.push(id);
    }

    const rows: unknown[] = await redis.pipeline([summaries_command, flagged_command]);

    const summaries: string[] = redis.as_strings(rows[0]);

    const flagged_at: string[] = redis.as_strings(rows[1]);

    for(let index: number = 0; index < summaries.length; index++) {
        const summary: shop.SUMMARY | null = shop.parse_summary(summaries[index]);

        if(summary !== null) {
            convos.push({"id": summary.id, "tab": summary.tab, "channel": summary.channel, "name": summary.name, "last_at": summary.last_at, "last_kind": summary.last_kind, "last_text": summary.last_text, "off": view === "off", "flagged_at": redis.as_number(flagged_at[index])});
        }
    }

    return http.json({"tab": tab, "view": view, "counts": tab_counts, "view_counts": view_counts, "off_tabs": off_tabs, "more": more, "convos": convos});
}


//ROUTE

//the conversation list, signed in only
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_convos, request);
}
