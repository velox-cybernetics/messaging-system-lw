//IMPORTS

import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as search from "./_helpers/search.js";
import * as shop from "./_helpers/shop.js";


//GLOBALS

const PAGE_SIZE: number = 50;

//a refresh after show older asks for everything on screen, so the list doesn't snap back
const MAX_LIMIT: number = 500;

//a search reads this many threads per trip to the db, so one answer never gets huge
const THREAD_BATCH: number = 100;

//on is what the system answers, booked got a booked hil, off is the rest of the switched off ones
type VIEW = "on" | "booked" | "off";

const VIEWS: VIEW[] = ["on", "booked", "off"];

type PLACED = {id: string; at: number};

//snippet and hits only come with a search, the message it matched in and the words to mark
type CONVO = {id: string; tab: shop.TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string; off: boolean; booked: boolean; flagged_at: number; snippet?: string; hits?: string[]};

//what the customer wrote in one convo, at is there last_at when it got read
type CUSTOMER_SIDE = {at: number; texts: string[]; words: string[]};

//a convo the search kept and how well it matched
type MATCH = {summary: shop.SUMMARY; score: number};

//every tabs total, the switched off channels, and who's booked or off, read once per request
type BOARD = {counts: Record<shop.TAB, number>; off_tabs: shop.TAB[]; booked: Set<string>; off: Set<string>};

//kept between searches while the server stays warm, a convo only gets read again once its last_at moves
const CUSTOMER_SIDES: Map<string, CUSTOMER_SIDE> = new Map<string, CUSTOMER_SIDE>();


//SORTING

//on, booked or off, anything else is a made up view
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


//SEARCH

//on, booked or off for one convo, booked wins over off like the lists
function view_of(id: string, board: BOARD): VIEW {
    if(board.booked.has(id)) {
        return "booked";
    }

    if(board.off.has(id)) {
        return "off";
    }

    return "on";
}

//just the customers own words, every system hello says Lone Wraps so its replies would match wrap for everyone
function customer_side(at: number, entries: Record<string, unknown>[]): CUSTOMER_SIDE {
    const texts: string[] = [];

    const words: string[] = [];

    for(const entry of entries) {
        if(entry.kind === "in" && Array.isArray(entry.parts)) {
            for(const part of entry.parts) {
                const text: unknown = shop.fields_of(part).text;

                if(typeof text === "string" && text !== "") {
                    texts.push(text);

                    for(const word of search.plain_words(text)) {
                        words.push(word);
                    }
                }
            }
        }
    }

    return {"at": at, "texts": texts, "words": search.unique_words(words)};
}

//the customer side of a convo, empty if it never got read
function side_of(id: string): CUSTOMER_SIDE {
    const kept: CUSTOMER_SIDE | undefined = CUSTOMER_SIDES.get(id);

    if(kept === undefined) {
        return {"at": 0, "texts": [], "words": []};
    }

    return kept;
}

//reads the thread of anyone new or with a message since the last search, the rest come out of memory
async function fill_customer_sides(summaries: shop.SUMMARY[]): Promise<void> {
    const stale: shop.SUMMARY[] = [];

    for(const summary of summaries) {
        const kept: CUSTOMER_SIDE | undefined = CUSTOMER_SIDES.get(summary.id);

        if(kept === undefined || kept.at !== summary.last_at) {
            stale.push(summary);
        }
    }

    //a cold server reads every thread, so they go in batches
    for(let first: number = 0; first < stale.length; first += THREAD_BATCH) {
        const batch: shop.SUMMARY[] = stale.slice(first, first + THREAD_BATCH);

        const commands: redis.COMMAND[] = [];

        for(const summary of batch) {
            commands.push(["LRANGE", `thread:${summary.id}`, 0, -1]);
        }

        const threads: unknown[] = await redis.pipeline(commands);

        for(let index: number = 0; index < batch.length; index++) {
            const summary: shop.SUMMARY | undefined = batch[index];

            if(summary !== undefined) {
                CUSTOMER_SIDES.set(summary.id, customer_side(summary.last_at, shop.parse_entries(threads[index])));
            }
        }
    }
}

//slots it in under every match that scored at least as well, so ties stay newest first
function place_match(matches: MATCH[], match: MATCH): void {
    let spot: number = matches.length;

    while(spot > 0) {
        const before: MATCH | undefined = matches[spot - 1];

        if(before === undefined || before.score >= match.score) {
            break;
        }

        spot--;
    }

    matches.splice(spot, 0, match);
}

//every convo on the tab checked against the search, best match first, view_counts become how many matched under each list
async function search_page(tab: shop.TAB, view: VIEW, query: string, searched: search.SEARCH, start: number, limit: number, board: BOARD): Promise<Response> {
    //newest first, so convos that tie stay that way
    const ids: string[] = redis.as_strings(await redis.command(["ZREVRANGE", `convos:${tab}`, 0, -1]));

    const summaries: shop.SUMMARY[] = [];

    if(ids.length > 0) {
        const summaries_command: redis.COMMAND = ["HMGET", "summaries"];

        for(const id of ids) {
            summaries_command.push(id);
        }

        for(const text of redis.as_strings(await redis.command(summaries_command))) {
            const summary: shop.SUMMARY | null = shop.parse_summary(text);

            if(summary !== null) {
                summaries.push(summary);
            }
        }
    }

    await fill_customer_sides(summaries);

    const view_counts: Record<VIEW, number> = {"on": 0, "booked": 0, "off": 0};

    const matches: MATCH[] = [];

    for(const summary of summaries) {
        //only forms ids are phone numbers, instagram and messenger ids are long random numbers
        let digits: string = "";

        if(summary.tab === "forms") {
            digits = search.number_digits(summary.id);
        }

        const score: number = search.convo_score(searched, search.plain_words(summary.name), digits, side_of(summary.id).words);

        if(score > 0) {
            const each_view: VIEW = view_of(summary.id, board);

            view_counts[each_view] += 1;

            if(each_view === view) {
                place_match(matches, {"summary": summary, "score": score});
            }
        }
    }

    const page: MATCH[] = matches.slice(start, start + limit);

    const convos: CONVO[] = [];

    if(page.length > 0) {
        const flagged_command: redis.COMMAND = ["HMGET", "flagged"];

        for(const match of page) {
            flagged_command.push(match.summary.id);
        }

        const flagged_at: string[] = redis.as_strings(await redis.command(flagged_command));

        for(let index: number = 0; index < page.length; index++) {
            const match: MATCH | undefined = page[index];

            if(match !== undefined) {
                const summary: shop.SUMMARY = match.summary;

                const side: CUSTOMER_SIDE = side_of(summary.id);

                //there name and everything they wrote, the hits get marked on the page
                const words: string[] = search.plain_words(summary.name);

                for(const word of side.words) {
                    words.push(word);
                }

                const hits: string[] = search.hit_words(searched, words);

                convos.push({"id": summary.id, "tab": summary.tab, "channel": summary.channel, "name": summary.name, "last_at": summary.last_at, "last_kind": summary.last_kind, "last_text": summary.last_text, "off": board.off.has(summary.id), "booked": board.booked.has(summary.id), "flagged_at": redis.as_number(flagged_at[index]), "snippet": search.snippet(side.texts, hits), "hits": hits});
            }
        }
    }

    const more: boolean = start + page.length < matches.length;

    return http.json({"tab": tab, "view": view, "query": query, "counts": board.counts, "view_counts": view_counts, "off_tabs": board.off_tabs, "more": more, "convos": convos});
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

    //whats typed in the search box, sent back as is so the page can tell an old answer from a new one
    let query: string | null = params.get("q");

    if(query === null) {
        query = "";
    }

    query = query.trim();

    const commands: redis.COMMAND[] = [["SMEMBERS", "off"], ["SMEMBERS", "off_tabs"]];

    //everyone who got a booked hil, this year and last in one go
    const booked_command: redis.COMMAND = ["SUNION"];

    for(const key of shop.booked_keys(shop.shop_clock(new Date()).date)) {
        booked_command.push(key);
    }

    commands.push(booked_command);

    for(const each of shop.TABS) {
        commands.push(["ZCARD", `convos:${each}`]);
    }

    const results: unknown[] = await redis.pipeline(commands);

    const off_ids: string[] = redis.as_strings(results[0]);

    const booked_ids: string[] = redis.as_strings(results[2]);

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

        tab_counts[each] = redis.as_number(results[index + 3]);
    }

    const off_set: Set<string> = new Set(off_ids);

    const booked_set: Set<string> = new Set(booked_ids);

    //something typed in the search box, every convo on the tab gets checked instead of one page of the list
    const searched: search.SEARCH = search.new_search(query);

    if(searched.words.length > 0) {
        const board: BOARD = {"counts": tab_counts, "off_tabs": off_tabs, "booked": booked_set, "off": off_set};

        return await search_page(tab, view, query, searched, start, limit, board);
    }

    //booked wins over off, so a booked one thats switched off only gets asked about once
    const listed: string[] = [];

    for(const booked_id of booked_ids) {
        listed.push(booked_id);
    }

    for(const off_id of off_ids) {
        if(!booked_set.has(off_id)) {
            listed.push(off_id);
        }
    }

    //the booked and off lists stay short, so they come back whole
    const booked_here: string[] = [];

    const off_here: string[] = [];

    if(listed.length > 0) {
        const score_command: redis.COMMAND = ["ZMSCORE", `convos:${tab}`];

        for(const id of listed) {
            score_command.push(id);
        }

        for(const id of newest_first(listed, await redis.command(score_command))) {
            if(booked_set.has(id)) {
                booked_here.push(id);
            }
            else {
                off_here.push(id);
            }
        }
    }

    const view_counts: Record<VIEW, number> = {"on": tab_counts[tab] - booked_here.length - off_here.length, "booked": booked_here.length, "off": off_here.length};

    let ids: string[] = [];

    if(view === "booked") {
        ids = booked_here.slice(start, start + limit);
    }
    else if(view === "off") {
        ids = off_here.slice(start, start + limit);
    }
    else {
        //booked and off ones come out and later ones move up, so this many off the top fills the page
        const top: string[] = redis.as_strings(await redis.command(["ZREVRANGE", `convos:${tab}`, 0, start + limit + booked_here.length + off_here.length - 1]));

        const kept: string[] = [];

        for(const id of top) {
            if(!booked_set.has(id) && !off_set.has(id)) {
                kept.push(id);
            }
        }

        ids = kept.slice(start, start + limit);
    }

    const more: boolean = start + ids.length < view_counts[view];

    const convos: CONVO[] = [];

    if(ids.length === 0) {
        return http.json({"tab": tab, "view": view, "query": query, "counts": tab_counts, "view_counts": view_counts, "off_tabs": off_tabs, "more": more, "convos": convos});
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
            convos.push({"id": summary.id, "tab": summary.tab, "channel": summary.channel, "name": summary.name, "last_at": summary.last_at, "last_kind": summary.last_kind, "last_text": summary.last_text, "off": off_set.has(summary.id), "booked": booked_set.has(summary.id), "flagged_at": redis.as_number(flagged_at[index])});
        }
    }

    return http.json({"tab": tab, "view": view, "query": query, "counts": tab_counts, "view_counts": view_counts, "off_tabs": off_tabs, "more": more, "convos": convos});
}


//ROUTE

//the conversation list, signed in only
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_convos, request);
}
