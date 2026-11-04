//**********IMPORTS**********
//the replies, the database, the sign in check and the feed's shapes
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";



//**********SWITCH**********
//off customers go in the off set, off channels in off_tabs, the system checks both before every send


//FLIP SWITCH
async function flip_switch(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const body: Record<string, unknown> | null = await http.read_body(request);

    if(body === null || typeof body.on !== "boolean") {
        return http.fail(400, "Send on: true or false, with a conversation id or a tab.");
    }

    const on: boolean = body.on === true;

    //a whole channel, no thread entry since its unanswered messages already show as not answered
    if(body.tab !== undefined) {
        const tab: unknown = body.tab;

        if(!shop.is_tab(tab)) {
            return http.fail(400, `Unknown tab "${body.tab}".`);
        }

        let tab_command: redis.COMMAND = ["SADD", "off_tabs", tab];

        if(on) {
            tab_command = ["SREM", "off_tabs", tab];
        }

        await redis.pipeline([tab_command, ["INCR", "version"]]);

        return http.json({"tab": tab, "on": on});
    }

    const id: unknown = body.id;

    if(!shop.valid_id(id)) {
        return http.fail(400, "Send the conversation id and on: true or false.");
    }

    if(redis.as_number(await redis.command(["HEXISTS", "summaries", id])) !== 1) {
        return http.fail(404, "No conversation with that id.");
    }

    const entry: string = JSON.stringify({"at": Date.now(), "kind": "switch", "on": on});

    let off_command: redis.COMMAND = ["SADD", "off", id];

    if(on) {
        off_command = ["SREM", "off", id];
    }

    await redis.pipeline([off_command, ["RPUSH", `thread:${id}`, entry], ["INCR", "version"]]);

    return http.json({"id": id, "on": on});
}



//**********ROUTE**********
//what vercel runs for POST /api/switch


//POST
export function POST(request: Request): Promise<Response> {
    return http.guarded(flip_switch, request);
}
