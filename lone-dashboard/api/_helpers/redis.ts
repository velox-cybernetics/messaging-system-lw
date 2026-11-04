//**********GLOBALS**********
//the dashboard's own upstash database and what a command looks like


//COMMAND TYPES
//one part of a command, upstash gets them all as text anyway
export type ARGUMENT = string | number;

export type COMMAND = ARGUMENT[];


//DATABASE
//vercel's integration names these KV_REST_API_*, a db linked by hand uses UPSTASH_REDIS_REST_*
const DATABASE_URL: string = (process.env.KV_REST_API_URL ?? process.env.UPSTASH_REDIS_REST_URL ?? "").replace(/\/$/, "");

const DATABASE_TOKEN: string = process.env.KV_REST_API_TOKEN ?? process.env.UPSTASH_REDIS_REST_TOKEN ?? "";



//**********DATABASE**********
//sends redis commands to upstash over its rest api


//TEXT ARGUMENTS
//upstash wants every part as text, numbers too
function text_arguments(parts: COMMAND): string[] {
    const texts: string[] = [];

    for(const part of parts) {
        texts.push(String(part));
    }

    return texts;
}


//ERROR IN
function error_in(answer: unknown): string | null {
    if(answer !== null && typeof answer === "object" && "error" in answer) {
        return String(answer.error);
    }

    return null;
}


//RESULT
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


//SEND
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
        throw new Error(`Database refused the request: ${error_in(data) ?? response.statusText}`);
    }

    return data;
}


//COMMAND
export async function command(parts: COMMAND): Promise<unknown> {
    return command_result(await send("", text_arguments(parts)));
}


//PIPELINE
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



//**********READERS**********
//turns what upstash sends back into shapes the handlers can use


//AS STRINGS
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


//AS NUMBER
//0 for nothing or anything that isn't a number
export function as_number(value: unknown): number {
    const number: number = Number(value ?? 0);

    if(Number.isFinite(number)) {
        return number;
    }

    return 0;
}


//AS OBJECT
//HGETALL comes back flat, field then value, so pair them back up
export function as_object(flat: unknown): Record<string, string> {
    const fields: Record<string, string> = {};

    const items: string[] = as_strings(flat);

    for(let index: number = 0; index + 1 < items.length; index += 2) {
        fields[items[index] ?? ""] = items[index + 1] ?? "";
    }

    return fields;
}
