//IMPORTS

import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";


//GLOBALS

//ten wrong from one address locks it out for 15 minutes
const MAX_FAILURES: number = 10;

const LOCKOUT_SECONDS: number = 900;


//SIGN IN

//first address vercel lists, local when theres none
function address_of(request: Request): string {
    let forwarded: string | null = request.headers.get("x-forwarded-for");

    if(forwarded === null) {
        forwarded = "local";
    }

    let first: string | undefined = forwarded.split(",")[0];

    if(first === undefined) {
        first = "";
    }

    return first.trim();
}

//a locked out address gets refused before the password is even checked
async function sign_in(request: Request): Promise<Response> {
    const failures_key: string = `login_failures:${address_of(request)}`;

    if(redis.as_number(await redis.command(["GET", failures_key])) >= MAX_FAILURES) {
        return http.fail(429, "Too many wrong passwords. Try again in 15 minutes.");
    }

    const body: Record<string, unknown> | null = await http.read_body(request);

    //every wrong one counts toward the lockout
    if(body === null || typeof body.password !== "string" || !session.password_matches(body.password)) {
        await redis.pipeline([["INCR", failures_key], ["EXPIRE", failures_key, LOCKOUT_SECONDS]]);

        return http.fail(401, "Wrong password.");
    }

    return http.json({"ok": true}, 200, {"Set-Cookie": session.session_cookie()});
}


//ROUTE

//sign in with the dashboard password, the cookie comes back on success
export function POST(request: Request): Promise<Response> {
    return http.guarded(sign_in, request);
}
