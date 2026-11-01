//**********IMPORTS**********
//the replies, the database, the sign in check, the feed's shapes and the flag email
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as email from "./_helpers/email.js";
import * as shop from "./_helpers/shop.js";



//**********GLOBALS**********
//limits, channel names and the shapes the email is built from


//FEEDBACK MAX
const FEEDBACK_MAX: number = 4000;


//CHANNEL NAMES
const CHANNEL_NAMES: Record<string, string> = {"blooio": "Text", "ig": "Instagram", "messenger": "Messenger", "meta-form": "Meta form", "website-form": "Website form"};


//EMAIL SHAPES
type REPLY = {at: number; text: string};

type SECTION = {title: string; body: string};



//**********TEXT**********
//small pieces of the email


//HTML CODE
//one character as its numbered html code
function html_code(character: string): string {
    return `&#${character.charCodeAt(0)};`;
}


//ESCAPE HTML
function escape_html(text: string): string {
    return text.replace(/[&<>"']/g, html_code);
}


//SHOP TIME
function shop_time(at: number): string {
    return new Intl.DateTimeFormat("en-US", {"timeZone": shop.SHOP_TIME_ZONE, "dateStyle": "medium", "timeStyle": "short"}).format(at);
}



//**********EMAIL**********
//the sections of the flag email


//LAST REPLY
//newest reply in the thread as its texts, with when it went out
function last_reply(entries: Record<string, unknown>[]): REPLY | null {
    for(let index: number = entries.length - 1; index >= 0; index--) {
        const entry: Record<string, unknown> = entries[index] ?? {};

        if(entry.kind !== "out" || !Array.isArray(entry.parts)) {
            continue;
        }

        const texts: string[] = [];

        for(const part of entry.parts) {
            const text: unknown = shop.fields_of(part).text;

            if(typeof text === "string") {
                texts.push(text);
            }
        }

        return {"at": Number(entry.at), "text": texts.join("\n") || "(pics only)"};
    }

    return null;
}


//STATE SECTION
//state gets noted right before a reply is written, so one newer than the last reply never went out
function state_section(state_text: unknown, reply: REPLY | null): SECTION {
    const state: Record<string, unknown> = shop.fields_of(shop.parse_json(state_text));

    if(!("state" in state)) {
        return {"title": "State", "body": "No state is kept for this conversation. States are kept 30 days after a reply."};
    }

    const at: number = Number(state.at);

    let title: string = `State the reply was written from, ${shop_time(at)}`;

    if(reply !== null && at > reply.at) {
        title = `State from ${shop_time(at)}, newer than the last reply, so its reply never went out`;
    }

    return {"title": title, "body": JSON.stringify(state.state, null, 2)};
}


//EMAIL SECTIONS
function email_sections(summary: shop.SUMMARY, feedback: string, link: string, reply: REPLY | null, state_text: unknown): SECTION[] {
    const customer: string = [`Name: ${summary.name || "not known"}`, `Id: ${summary.id}`, `Channel: ${CHANNEL_NAMES[summary.channel] ?? summary.channel}`, `Open it: ${link}`].join("\n");

    let response: SECTION = {"title": "Response", "body": "No reply has gone out in this conversation yet."};

    if(reply !== null) {
        response = {"title": `Response, sent ${shop_time(reply.at)}`, "body": reply.text};
    }

    return [{"title": "What went wrong", "body": feedback}, {"title": "Customer", "body": customer}, response, state_section(state_text, reply)];
}



//**********FLAG**********
//emails the feedback, the last reply and its state, then marks the conversation flagged


//SEND FLAG
async function send_flag(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const body: Record<string, unknown> | null = await http.read_body(request);

    let feedback: string = "";

    let id: unknown = undefined;

    if(body !== null) {
        id = body.id;

        if(typeof body.feedback === "string") {
            feedback = body.feedback.trim();
        }
    }

    if(!shop.valid_id(id) || feedback === "") {
        return http.fail(400, "Write what went wrong before sending the flag.");
    }

    if(feedback.length > FEEDBACK_MAX) {
        return http.fail(400, `Keep it under ${FEEDBACK_MAX} characters.`);
    }

    const results: unknown[] = await redis.pipeline([["HGET", "summaries", id], ["GET", `state:${id}`], ["LRANGE", `thread:${id}`, -100, -1]]);

    const summary: shop.SUMMARY | null = shop.parse_summary(results[0]);

    if(summary === null) {
        return http.fail(404, "No conversation with that id.");
    }

    const link: string = `${new URL(request.url).origin}/messages?tab=${summary.tab}&id=${encodeURIComponent(id)}`;

    const sections: SECTION[] = email_sections(summary, feedback, link, last_reply(shop.parse_entries(results[2])), results[1]);

    const text_parts: string[] = [];

    let html: string = "";

    for(const section of sections) {
        text_parts.push(`${section.title}\n${section.body}`);

        html += `<h3 style="margin:24px 0 6px;font:600 15px sans-serif">${escape_html(section.title)}</h3><pre style="margin:0;white-space:pre-wrap;font:13px/1.5 monospace">${escape_html(section.body)}</pre>`;
    }

    const text: string = text_parts.join("\n\n");

    try {
        await email.send_email(`Flag: ${summary.name || id} on ${CHANNEL_NAMES[summary.channel] ?? summary.channel}`, text, html);
    }

    catch(error: unknown) {
        let message: string = "";

        if(error instanceof Error) {
            message = error.message;
        }

        return http.fail(502, `The flag email didn't send. ${message}`.trim());
    }

    const at: number = Date.now();

    await redis.pipeline([["HSET", "flagged", id, at], ["RPUSH", `thread:${id}`, JSON.stringify({"at": at, "kind": "flag", "feedback": feedback})], ["INCR", "version"]]);

    return http.json({"ok": true, "sent_to": email.FLAG_EMAIL, "flagged_at": at});
}



//**********ROUTE**********
//what vercel runs for POST /api/flag


//POST
export function POST(request: Request): Promise<Response> {
    return http.guarded(send_flag, request);
}
