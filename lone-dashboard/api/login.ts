//**********IMPORTS**********
//the replies, the database and the password check
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";



//**********GLOBALS**********
//how many wrong passwords lock an address out, and for how long


//LOCKOUT
//10 wrong from one address locks it out for 15 minutes
const MAX_FAILURES: number = 10;

const LOCKOUT_SECONDS: number = 900;



//**********SIGN IN**********
//checks the password and hands back a session cookie


//ADDRESS OF
//first address vercel lists, "local" when there's none
function address_of(request: Request): string {
    const forwarded: string = request.headers.get("x-forwarded-for") ?? "local";

    return (forwarded.split(",")[0] ?? "").trim();
}


//SIGN IN
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



//**********ROUTE**********
//what vercel runs for POST /api/login


//POST
export function POST(request: Request): Promise<Response> {
    return http.guarded(sign_in, request);
}
