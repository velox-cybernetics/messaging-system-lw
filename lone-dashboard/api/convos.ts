//**********IMPORTS**********
//the replies, the database, the sign in check and the feed's shapes
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";



//**********GLOBALS**********
//page sizes and the two views a tab has


//PAGE SIZES
const PAGE_SIZE: number = 50;

//a refresh after "Show older conversations" asks for everything on screen, so the list doesn't snap back to 50
const MAX_LIMIT: number = 500;


//VIEWS
//on is what the system answers, off is the ones switched off
type VIEW = "on" | "off";

const VIEWS: VIEW[] = ["on", "off"];


//PLACED
type PLACED = {id: string; at: number};


//CONVO
type CONVO = {id: string; tab: shop.TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string; off: boolean; flagged_at: number};



//**********SORTING**********
//which views exist and the order ids show in


//IS VIEW
function is_view(value: unknown): value is VIEW {
    for(const view of VIEWS) {
        if(value === view) {
            return true;
        }
    }

    return false;
}


//NEWEST ORDER
function newest_order(a: PLACED, b: PLACED): number {
    return b.at - a.at;
}


//NEWEST FIRST
//only the ids that have a place in the tab, newest first by their last message
function newest_first(ids: string[], scores: unknown): string[] {
    const placed: PLACED[] = [];

    let list: unknown[] = [];

    if(Array.isArray(scores)) {
        list = scores;
    }

    for(let index: number = 0; index < ids.length; index++) {
        if(list[index] !== null && list[index] !== undefined) {
            placed.push({"id": ids[index] ?? "", "at": Number(list[index])});
        }
    }

    placed.sort(newest_order);

    const sorted: string[] = [];

    for(const each of placed) {
        sorted.push(each.id);
    }

    return sorted;
}



//**********CONVOS**********
//one tab's conversations in one view, limit at a time, with the counts and the switched off tabs


//READ CONVOS
async function read_convos(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const params: URLSearchParams = new URL(request.url).searchParams;

    const tab: string = params.get("tab") ?? "forms";

    if(!shop.is_tab(tab)) {
        return http.fail(400, `Unknown tab "${tab}".`);
    }

    const view: string = params.get("view") ?? "on";

    if(!is_view(view)) {
        return http.fail(400, `Unknown view "${view}".`);
    }

    //|| on purpose, NaN falls back too
    const start: number = Math.max(0, Math.floor(Number(params.get("start") ?? 0)) || 0);

    const limit: number = Math.min(MAX_LIMIT, Math.max(1, Math.floor(Number(params.get("limit") ?? PAGE_SIZE)) || PAGE_SIZE));

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
        const each: shop.TAB = shop.TABS[index] ?? "forms";

        tab_counts[each] = redis.as_number(results[index + 2]);
    }

    //the off list stays short, so it comes back whole
    let off_here: string[] = [];

    if(off_ids.length > 0) {
        off_here = newest_first(off_ids, await redis.command(["ZMSCORE", `convos:${tab}`, ...off_ids]));
    }

    const view_counts: Record<VIEW, number> = {"on": tab_counts[tab] - off_here.length, "off": off_here.length};

    let ids: string[] = [];

    if(view === "off") {
        ids = off_here.slice(start, start + limit);
    }

    else {
        const off_here_set: Set<string> = new Set(off_here);

        //taking the off ones out only pulls later ones forward, so this many from the top always fills the page
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

    const rows: unknown[] = await redis.pipeline([["HMGET", "summaries", ...ids], ["HMGET", "flagged", ...ids]]);

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



//**********ROUTE**********
//what vercel runs for GET /api/convos


//GET
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_convos, request);
}
