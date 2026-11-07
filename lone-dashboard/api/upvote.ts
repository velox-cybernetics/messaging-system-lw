//**********IMPORTS**********
//the replies, the database, the sign in check, the feed's shapes, the repo the system deploys from and the model that writes the example
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";
import * as shop from "./_helpers/shop.js";
import * as github from "./_helpers/github.js";
import * as openrouter from "./_helpers/openrouter.js";



//**********GLOBALS**********
//limits, the keys and model an upvote needs, what the bot notes about a reply, and how a generator's examples are laid out


//REASON MAX
const REASON_MAX: number = 2000;


//SETTINGS
//every key an upvote needs from vercel, checked up front so one try names all that's missing
const SETTINGS: string[] = ["OPENROUTER_API_KEY", "GITHUB_TOKEN"];


//EXAMPLE MODEL
//kimi k3.1 pro, the system's own backup writer, at medium so the example gets thought through
const EXAMPLE_MODEL: string = "moonshotai/kimi-k3.1-pro";

const EXAMPLE_EFFORT: string = "medium";

//4 minutes leaves the push room inside vercel's 5 minute limit
const EXAMPLE_TIMEOUT_MS: number = 240 * 1000;


//EXAMPLES SHOWN
//how many of the file's newest examples the model copies the shape of
const EXAMPLES_SHOWN: number = 3;


//WRITER
//what helpers/state/dashboard.py notes about the system's last reply: when, the prompt file that wrote it ("" when only the code did), what it was handed and the reply
type WRITER = {at: number; generator: string; input: string; reply: string};


//EXAMPLES
//where a file's examples sit, from right after they open to the quotes that close them
type EXAMPLES = {start: number; end: number; text: string};


//PATTERNS
//only one of the system's prompt files ever gets pushed to
const GENERATOR_PATH: RegExp = /^src\/prompts\/[a-z0-9_/]+\.py$/;

//every example in a file opens on its number, "Ex 12:", or "Ex 8a:" for one slotted in by hand
const EXAMPLE_NUMBER: RegExp = /^ {4}Ex (\d+)[a-z]*:$/gm;

//an Ex line the model wrote on its own
const EXAMPLE_LINE: RegExp = /^Ex \d+[a-z]*:$/;

//the line a generator's input carries the conversation on
const STATE_LINE: RegExp = /^\s*STATE: (.+)$/m;

//a commit sha, the only thing the live check takes
const COMMIT_SHA: RegExp = /^[0-9a-f]{40}$/;


//EXAMPLES BLOCK
//every generator's examples are one raw string in its examples(), the new one goes in right before it closes
const EXAMPLES_OPEN: string = 'def examples() -> str:\n    return r"""\n';

const EXAMPLES_CLOSE: string = '"""';

//they sit 4 spaces in
const INDENT: string = "    ";


//EXAMPLE PROMPT
//the model writes the example in the file's own shape, then the state and the reply get filled in exactly
const EXAMPLE_PROMPT: string = `
#ROLE
You write examples for the prompt files of Lone Wraps' texting system, the one that texts the shop's customers as Hazel. The owner read a reply one of its generators wrote and said it was good. You write that reply up as one new example for that generator, in the same shape as its other examples, so it writes more replies like it.

#INPUT
- GENERATOR_FILE: the generator's prompt file with its examples taken out, so you know its rules and what each part of its input is.
- LAST_EXAMPLES: the newest examples in the file. Yours goes right after them and looks just like them.
- GENERATOR_INPUT: exactly what the generator was handed when it wrote the reply.
- REPLY: the reply it wrote.
- WHY_IT_WAS_GOOD: the owner's own words on why the reply was good.

#WHAT YOU WRITE
1. One example's lines, the same ones in the same order as an example in LAST_EXAMPLES, each on its own line, and nothing else: no "Ex" line, no indent, no notes and no code fences.
2. Each input line is one part of GENERATOR_INPUT under its own label, shortened the way LAST_EXAMPLES shorten that part, like the service details written as {"service": "Vinyl Wrap", "service_details": {...}}, one line per service.
3. When GENERATOR_INPUT has a STATE, its line is only STATE: {{STATE}}. The response line is only Response: {{RESPONSE}}. Both get filled in exactly as the generator had them.
4. The REASON line, last and on one line, says why REPLY was right for what the customer said, built on WHY_IT_WAS_GOOD, in the same plain words and about the same length as the REASON lines in LAST_EXAMPLES. A rule from GENERATOR_FILE only gets named when REPLY follows it, the way the examples name rules.

#NEVER
1. Never anything WHY_IT_WAS_GOOD and REPLY don't back up, and never praise.
2. Never three double quotes in a row.
`;



//**********NOTE**********
//what the bot noted about the system's last reply, and whether that reply went out


//PARSE WRITER
//null when it's missing or isn't what the bot writes
function parse_writer(text: unknown): WRITER | null {
    const fields: Record<string, unknown> = shop.fields_of(shop.parse_json(text));

    if(typeof fields.at !== "number" || typeof fields.generator !== "string" || typeof fields.input !== "string" || typeof fields.reply !== "string") {
        return null;
    }

    return {"at": fields.at, "generator": fields.generator, "input": fields.input, "reply": fields.reply};
}


//WENT OUT
//the reply the note is on went out once the system sent something after it, a text a person sent from ghl never counts
function went_out(entries: Record<string, unknown>[], at: number): boolean {
    for(const entry of entries) {
        if(entry.kind === "out" && entry.ghl !== true && Number(entry.at) > at) {
            return true;
        }
    }

    return false;
}



//**********EXAMPLES**********
//finds a generator's examples in its file and puts the new one last


//FIND EXAMPLES
//throws when the file doesn't lay them out the way every generator does
function find_examples(file_text: string, path: string): EXAMPLES {
    const open: number = file_text.indexOf(EXAMPLES_OPEN);

    if(open === -1) {
        throw new Error(`${path} has no examples() raw string for the example to go in.`);
    }

    const start: number = open + EXAMPLES_OPEN.length;

    const end: number = file_text.indexOf(EXAMPLES_CLOSE, start);

    //the closing quotes sit on their own line, so the new example goes right in front of them
    if(end === -1 || file_text[end - 1] !== "\n") {
        throw new Error(`${path}'s examples don't close on a line of their own, so the example can't go in.`);
    }

    return {"start": start, "end": end, "text": file_text.slice(start, end)};
}


//NEXT NUMBER
//one past the highest example number in the file
function next_number(examples: EXAMPLES): number {
    let highest: number = 0;

    for(const found of examples.text.matchAll(EXAMPLE_NUMBER)) {
        highest = Math.max(highest, Number(found[1]));
    }

    return highest + 1;
}


//LAST EXAMPLES
//the file's newest few, the shape the model copies
function last_examples(examples: EXAMPLES): string {
    const starts: number[] = [];

    for(const found of examples.text.matchAll(EXAMPLE_NUMBER)) {
        starts.push(found.index ?? 0);
    }

    const first: number = starts[Math.max(0, starts.length - EXAMPLES_SHOWN)] ?? 0;

    return examples.text.slice(first).trim();
}


//WITH EXAMPLE
//the file with the new example last in its examples, a blank line after the one before it like the rest
function with_example(file_text: string, examples: EXAMPLES, number: number, lines: string[]): string {
    let example: string = `\n${INDENT}Ex ${number}:\n`;

    for(const line of lines) {
        example += `${INDENT}${line}\n`;
    }

    return file_text.slice(0, examples.end) + example + file_text.slice(examples.end);
}



//**********WRITING**********
//the model writes the example, then the state and the reply go in exactly as the generator had them


//STATE OF
//the conversation exactly as the generator got it, "" for an input with no state line
function state_of(input: string): string {
    const found: RegExpMatchArray | null = input.match(STATE_LINE);

    if(found === null) {
        return "";
    }

    return found[1] ?? "";
}


//EXAMPLE LINES
//the model's lines with the state and the reply filled in, throws when it left out either one the example needs
function example_lines(written: string, writer: WRITER): string[] {
    const state: string = state_of(writer.input);

    const lines: string[] = [];

    let has_response: boolean = false;

    let reason: string = "";

    for(const written_line of written.split("\n")) {
        const line: string = written_line.trim();

        //code fences, blank lines and an Ex line of its own never go in, the number gets put on here
        if(line === "" || line.startsWith("```") || EXAMPLE_LINE.test(line)) {
            continue;
        }

        //the reason runs to the end, kept on one line like every example's
        if(line.startsWith("REASON:") || reason !== "") {
            reason = `${reason} ${line}`.trim();
        }

        //a line break in the reply is written \n, the way every example's response has them
        else if(line.startsWith("Response:")) {
            lines.push(`Response: "${writer.reply.trim().replace(/\r?\n/g, "\\n")}"`);

            has_response = true;
        }

        //anything between the response and the reason is the reply spilling onto more lines, and it's already in
        else if(has_response) {
            continue;
        }

        else if(line.startsWith("STATE:") && state !== "") {
            lines.push(`STATE: ${state}`);
        }

        else {
            lines.push(line);
        }
    }

    if(!has_response || reason === "") {
        throw new Error("The example came back without its Response or REASON line, so nothing got pushed.");
    }

    lines.push(reason);

    //three quotes in a row would close the examples early and break the file
    if(lines.join("\n").includes('"""')) {
        throw new Error("The example came back with three quotes in a row, which would break the file, so nothing got pushed.");
    }

    return lines;
}


//WRITE EXAMPLE
//written from the file's rules, its newest examples, what the generator was handed, its reply and why the owner liked it
async function write_example(writer: WRITER, reason: string, file_text: string, examples: EXAMPLES): Promise<string[]> {
    const rules: string = file_text.slice(0, examples.start) + file_text.slice(examples.end);

    const parts: string[] = [`GENERATOR_FILE:\n${rules}`, `LAST_EXAMPLES:\n${last_examples(examples)}`, `GENERATOR_INPUT:\n${writer.input}`, `REPLY:\n${writer.reply}`, `WHY_IT_WAS_GOOD:\n${reason}`];

    const written: string = await openrouter.openrouter_text(EXAMPLE_PROMPT, parts.join("\n\n"), EXAMPLE_MODEL, EXAMPLE_EFFORT, EXAMPLE_TIMEOUT_MS);

    return example_lines(written, writer);
}



//**********UPVOTE**********
//the system's last reply goes in as an example for the generator that wrote it, and the push to main sends it out to the system


//MISSING SETTINGS
//like "OPENROUTER_API_KEY and GITHUB_TOKEN", "" when every one is set
function missing_settings(): string {
    const missing: string[] = [];

    for(const name of SETTINGS) {
        if((process.env[name] ?? "") === "") {
            missing.push(name);
        }
    }

    return missing.join(" and ");
}


//SEND UPVOTE
async function send_upvote(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const missing: string = missing_settings();

    if(missing !== "") {
        return http.fail(500, `Set ${missing} in Vercel first, an up-weight needs them to write the example and push it.`);
    }

    const body: Record<string, unknown> | null = await http.read_body(request);

    let reason: string = "";

    let id: unknown = undefined;

    if(body !== null) {
        id = body.id;

        if(typeof body.reason === "string") {
            reason = body.reason.trim();
        }
    }

    if(!shop.valid_id(id) || reason === "") {
        return http.fail(400, "Write a reason before up-weighting.");
    }

    if(reason.length > REASON_MAX) {
        return http.fail(400, `Keep it under ${REASON_MAX} characters.`);
    }

    const results: unknown[] = await redis.pipeline([["GET", `writer:${id}`], ["LRANGE", `thread:${id}`, -100, -1]]);

    const writer: WRITER | null = parse_writer(results[0]);

    if(writer === null) {
        return http.fail(404, "No generator is on file for this conversation's last reply. Only replies written since up-weighting came in have one, and it's kept 30 days.");
    }

    if(writer.generator === "") {
        return http.fail(409, "The system's last reply was put together by the code, not a generator, so there are no examples to add it to.");
    }

    if(!GENERATOR_PATH.test(writer.generator)) {
        return http.fail(409, `${writer.generator} isn't one of the system's prompt files, so nothing got pushed.`);
    }

    if(!went_out(shop.parse_entries(results[1]), writer.at)) {
        return http.fail(409, "The system's newest reply never went out, so there's nothing to up-weight till one does.");
    }

    //read off the newest commit, so the push only lands if nothing else did first
    const head: github.HEAD = await github.read_head();

    const file_text: string = await github.read_file(head, writer.generator);

    const examples: EXAMPLES = find_examples(file_text, writer.generator);

    const number: number = next_number(examples);

    const lines: string[] = await write_example(writer, reason, file_text, examples);

    const commit: string = await github.push_file(head, writer.generator, with_example(file_text, examples, number, lines), `upvoted reply added as Ex ${number} in ${writer.generator}`);

    const at: number = Date.now();

    await redis.pipeline([["RPUSH", `thread:${id}`, JSON.stringify({"at": at, "kind": "upvote", "reason": reason, "generator": writer.generator, "example": number})], ["INCR", "version"]]);

    return http.json({"ok": true, "generator": writer.generator, "example": number, "commit": commit});
}



//**********LIVE**********
//whether the system is running the push yet, the bot says what commit render deployed every time it checks in


//READ LIVE
//live once the commit running is the one the example went out in, or one after it
async function read_live(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const commit: string = new URL(request.url).searchParams.get("commit") ?? "";

    if(!COMMIT_SHA.test(commit)) {
        return http.fail(400, "That commit isn't valid.");
    }

    const running: string = String(await redis.command(["GET", "up_commit"]) ?? "");

    let live: boolean = false;

    //nothing on file means the system hasn't checked in from render yet
    if(running !== "") {
        live = await github.has_commit(running, commit);
    }

    return http.json({"commit": commit, "running": running, "live": live});
}



//**********ROUTE**********
//what vercel runs for POST and GET /api/upvote


//POST
export function POST(request: Request): Promise<Response> {
    return http.guarded(send_upvote, request);
}


//GET
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_live, request);
}
