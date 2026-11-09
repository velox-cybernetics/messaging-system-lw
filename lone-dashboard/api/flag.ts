//IMPORTS

import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as email from "./_helpers/email.js";
import * as shop from "./_helpers/shop.js";


//GLOBALS

const FEEDBACK_MAX: number = 4000;

const CHANNEL_NAMES: Record<string, string> = {"blooio": "Text", "ig": "Instagram", "messenger": "Messenger", "meta-form": "Meta form", "website-form": "Website form"};

type REPLY = {at: number; text: string};

type SECTION = {title: string; body: string};


//TEXT

//one character as its numbered html code
function html_code(character: string): string {
    return `&#${character.charCodeAt(0)};`;
}

//safe to drop into the emails html, quotes included
function escape_html(text: string): string {
    return text.replace(/[&<>"']/g, html_code);
}

//when it happened on the shops clock, written the way people read it
function shop_time(at: number): string {
    return new Intl.DateTimeFormat("en-US", {"timeZone": shop.SHOP_TIME_ZONE, "dateStyle": "medium", "timeStyle": "short"}).format(at);
}


//EMAIL

//newest reply in the thread as its texts, with when it went out
function last_reply(entries: Record<string, unknown>[]): REPLY | null {
    for(let index: number = entries.length - 1; index >= 0; index--) {
        let entry: Record<string, unknown> | undefined = entries[index];

        if(entry === undefined) {
            entry = {};
        }

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

        let text: string = texts.join("\n");

        if(!text) {
            text = "(pics only)";
        }

        return {"at": Number(entry.at), "text": text};
    }

    return null;
}

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

//what went wrong, who it was, the reply and its state, in the order the email reads
function email_sections(summary: shop.SUMMARY, feedback: string, link: string, reply: REPLY | null, state_text: unknown): SECTION[] {
    let name: string = summary.name;

    if(!name) {
        name = "not known";
    }

    let channel_name: string | undefined = CHANNEL_NAMES[summary.channel];

    if(channel_name === undefined) {
        channel_name = summary.channel;
    }

    const customer: string = [`Name: ${name}`, `Id: ${summary.id}`, `Channel: ${channel_name}`, `Open it: ${link}`].join("\n");

    let response: SECTION = {"title": "Response", "body": "No reply has gone out in this conversation yet."};

    if(reply !== null) {
        response = {"title": `Response, sent ${shop_time(reply.at)}`, "body": reply.text};
    }

    return [{"title": "What went wrong", "body": feedback}, {"title": "Customer", "body": customer}, response, state_section(state_text, reply)];
}


//FLAG

//emails the flag out first, the conversation only gets marked once it actually sent
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

    let who: string = summary.name;

    if(!who) {
        who = id;
    }

    let channel_name: string | undefined = CHANNEL_NAMES[summary.channel];

    if(channel_name === undefined) {
        channel_name = summary.channel;
    }

    try {
        await email.send_email(`Flag: ${who} on ${channel_name}`, text, html);
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


//ROUTE

//a flag on a reply that went wrong
export function POST(request: Request): Promise<Response> {
    return http.guarded(send_flag, request);
}
