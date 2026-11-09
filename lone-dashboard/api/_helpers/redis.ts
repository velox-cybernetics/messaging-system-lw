//IMPORTS

import * as shop from "./shop.js";


//GLOBALS

//one part of a command, upstash gets them all as text anyway
export type ARGUMENT = string | number;

export type COMMAND = ARGUMENT[];

//vercels integration names these KV_REST_API, a db linked by hand uses UPSTASH_REDIS_REST
const DATABASE_URL: string = shop.setting(process.env.KV_REST_API_URL, shop.setting(process.env.UPSTASH_REDIS_REST_URL, "")).replace(/\/$/, "");

const DATABASE_TOKEN: string = shop.setting(process.env.KV_REST_API_TOKEN, shop.setting(process.env.UPSTASH_REDIS_REST_TOKEN, ""));


//DATABASE

//upstash wants every part as text, numbers too
function text_arguments(parts: COMMAND): string[] {
    const texts: string[] = [];

    for(const part of parts) {
        texts.push(String(part));
    }

    return texts;
}

//upstashs complaint when the answer is one, null when its happy
function error_in(answer: unknown): string | null {
    if(answer !== null && typeof answer === "object" && "error" in answer) {
        return String(answer.error);
    }

    return null;
}

//throws on the error upstash sent back instead
function command_result(answer: unknown): unknown {
    const error: string | null = error_in(answer);

    if(error !== null) {
        throw new Error(`Database error: ${error}`);
    }

    if(answer !== null && typeof answer === "object" && "result" in answer) {
        return answer.result;
    }

    return null;
}

//one post to upstash, the answer comes back raw
async function send(path: string, body: string[] | string[][]): Promise<unknown> {
    if(DATABASE_URL === "" || DATABASE_TOKEN === "") {
        throw new Error("The dashboard database isn't connected. Set KV_REST_API_URL and KV_REST_API_TOKEN in Vercel.");
    }

    const response: Response = await fetch(`${DATABASE_URL}${path}`, {"method": "POST", "headers": {"Authorization": `Bearer ${DATABASE_TOKEN}`, "Content-Type": "application/json"}, "body": JSON.stringify(body)});

    let data: unknown = null;

    //an answer that isn't json just counts as nothing
    try {
        data = await response.json();
    }
    catch {
        data = null;
    }

    if(!response.ok) {
        let detail: string | null = error_in(data);

        if(detail === null) {
            detail = response.statusText;
        }

        throw new Error(`Database refused the request: ${detail}`);
    }

    return data;
}

//a single command and its result, throws when upstash complains
export async function command(parts: COMMAND): Promise<unknown> {
    return command_result(await send("", text_arguments(parts)));
}

//many commands in one request, results come back in the same order
export async function pipeline(commands: COMMAND[]): Promise<unknown[]> {
    const results: unknown[] = [];

    if(commands.length === 0) {
        return results;
    }

    const body: string[][] = [];

    for(const parts of commands) {
        body.push(text_arguments(parts));
    }

    const answers: unknown = await send("/pipeline", body);

    if(!Array.isArray(answers)) {
        return results;
    }

    for(const answer of answers) {
        results.push(command_result(answer));
    }

    return results;
}


//READERS

//every item as text, empty when it isn't a list at all
export function as_strings(value: unknown): string[] {
    const texts: string[] = [];

    if(!Array.isArray(value)) {
        return texts;
    }

    for(const item of value) {
        texts.push(String(item));
    }

    return texts;
}

//zero for nothing or anything that isn't a number
export function as_number(value: unknown): number {
    let number: number = 0;

    if(value !== undefined && value !== null) {
        number = Number(value);
    }

    if(Number.isFinite(number)) {
        return number;
    }

    return 0;
}

//hgetall comes back flat, field then value, so pair them back up
export function as_object(flat: unknown): Record<string, string> {
    const fields: Record<string, string> = {};

    const items: string[] = as_strings(flat);

    for(let index: number = 0; index + 1 < items.length; index += 2) {
        let field: string | undefined = items[index];

        if(field === undefined) {
            field = "";
        }

        let value: string | undefined = items[index + 1];

        if(value === undefined) {
            value = "";
        }

        fields[field] = value;
    }

    return fields;
}
