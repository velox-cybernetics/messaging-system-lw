//**********IMPORTS**********
//the replies, the database, the sign in check and the feed's shapes
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";



//**********GLOBALS**********
//blooio and how much of a thread the feed keeps, keep in step with helpers/channels/senders.py and helpers/state/dashboard.py


//BLOOIO
const BLOOIO_BASE_URL: string = "https://backend.blooio.com/v2/api";

const BLOOIO_API_KEY: string = process.env.BLOOIO_API_KEY ?? "";


//THREAD LIMITS
const THREAD_MAX: number = 500;

const CONVO_SECONDS: number = 365 * 86400;

const PREVIEW_CHARS: number = 140;


//TEXT MAX
const TEXT_MAX: number = 2000;



//**********SEND**********
//a text typed in the dashboard goes out on the blooio line, so only a forms tab conversation can get one


//SEND TO BLOOIO
//null when blooio took it, the reason when it didn't
async function send_to_blooio(id: string, text: string): Promise<string | null> {
    try {
        const response: Response = await fetch(`${BLOOIO_BASE_URL}/chats/${encodeURIComponent(id)}/messages`, {"method": "POST", "headers": {"Authorization": `Bearer ${BLOOIO_API_KEY}`, "Content-Type": "application/json"}, "body": JSON.stringify({"text": text})});

        if(response.status >= 400) {
            const detail: string = (await response.text()).slice(0, 300);

            console.error(`[BLOOIO] dashboard send to ${id} failed ${response.status}: ${detail}`);

            return `Blooio refused it (${response.status}).`;
        }

        return null;
    }

    catch(error: unknown) {
        console.error(`[BLOOIO] dashboard send to ${id} errored:`, error);

        return "Couldn't reach Blooio.";
    }
}


//SEND TEXT
//the text shows in their thread either way, marked failed when blooio didn't take it
async function send_text(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    if(BLOOIO_API_KEY === "") {
        return http.fail(500, "BLOOIO_API_KEY isn't set on the dashboard.");
    }

    const body: Record<string, unknown> | null = await http.read_body(request);

    const id: unknown = body?.id;

    if(body === null || !shop.valid_id(id) || typeof body.text !== "string") {
        return http.fail(400, "Send the conversation id and the text.");
    }

    const text: string = body.text.trim();

    if(text === "" || text.length > TEXT_MAX) {
        return http.fail(400, `The text has to be 1 to ${TEXT_MAX} characters.`);
    }

    const summary_text: unknown = await redis.command(["HGET", "summaries", id]);

    const summary: shop.SUMMARY | null = shop.parse_summary(summary_text);

    if(summary === null) {
        return http.fail(404, "No conversation with that id.");
    }

    if(summary.tab !== "forms") {
        return http.fail(400, "Only texts on the Blooio line can be sent from here.");
    }

    const failure: string | null = await send_to_blooio(id, text);

    const at: number = Date.now();

    const entry: Record<string, unknown> = {"at": at, "kind": "out", "parts": [{"text": text}]};

    if(failure !== null) {
        entry["failed"] = true;
    }

    //the rest of the summary stays as the feed wrote it, only the newest message changes
    const fields: Record<string, unknown> = shop.fields_of(shop.parse_json(summary_text));

    Object.assign(fields, {"last_at": at, "last_kind": "out", "last_text": text.slice(0, PREVIEW_CHARS)});

    await redis.pipeline([["RPUSH", `thread:${id}`, JSON.stringify(entry)], ["LTRIM", `thread:${id}`, -THREAD_MAX, -1], ["EXPIRE", `thread:${id}`, CONVO_SECONDS], ["HSET", "summaries", id, JSON.stringify(fields)], ["ZADD", `convos:${summary.tab}`, at, id], ["INCR", "version"]]);

    if(failure !== null) {
        return http.fail(502, failure);
    }

    return http.json({"id": id, "at": at});
}



//**********ROUTE**********
//what vercel runs for POST /api/send


//POST
export function POST(request: Request): Promise<Response> {
    return http.guarded(send_text, request);
}
