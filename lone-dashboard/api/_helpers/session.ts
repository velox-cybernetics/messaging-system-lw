//**********IMPORTS**********
//node's hashing and the error reply
import { createHash, createHmac, timingSafeEqual } from "node:crypto";

import * as http from "./http.js";



//**********GLOBALS**********
//the session cookie and how long a sign in lasts


//COOKIE
const COOKIE_NAME: string = "lw_session";


//SESSION LENGTH
const SESSION_DAYS: number = 30;

const DAY_SECONDS: number = 86400;



//**********PASSWORD**********
//one shared password for everyone, DASH_PASSWORD in vercel


//PASSWORD
function password(): string {
    const value: string = process.env.DASH_PASSWORD ?? "";

    if(value === "") {
        throw new Error("DASH_PASSWORD isn't set in Vercel, so nobody can sign in.");
    }

    return value;
}


//SAME TEXT
//hash both first so the compare takes the same time no matter what got typed
function same_text(given: string, expected: string): boolean {
    const given_hash: Buffer = createHash("sha256").update(given).digest();

    const expected_hash: Buffer = createHash("sha256").update(expected).digest();

    return timingSafeEqual(given_hash, expected_hash);
}


//PASSWORD MATCHES
export function password_matches(given: string): boolean {
    return same_text(given, password());
}



//**********SESSION**********
//a session is just a signed expiry time in an HttpOnly cookie


//SIGN
//key comes from the password, so changing it signs everyone out
function sign(value: string): string {
    const key: Buffer = createHash("sha256").update(`lone-dashboard session:${password()}`).digest();

    return createHmac("sha256", key).update(value).digest("base64url");
}


//SESSION COOKIE
export function session_cookie(): string {
    const expires: string = String(Date.now() + SESSION_DAYS * DAY_SECONDS * 1000);

    return `${COOKIE_NAME}=${expires}.${sign(expires)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${SESSION_DAYS * DAY_SECONDS}`;
}


//CLEARED COOKIE
export function cleared_cookie(): string {
    return `${COOKIE_NAME}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`;
}


//COOKIE VALUE
//last lw_session cookie wins, and its value can hold = too
function cookie_value(request: Request): string {
    let value: string = "";

    const pairs: string[] = (request.headers.get("cookie") ?? "").split(";");

    for(const pair of pairs) {
        const pieces: string[] = pair.trim().split("=");

        if(pieces[0] === COOKIE_NAME) {
            value = pieces.slice(1).join("=");
        }
    }

    return value;
}


//SIGNED IN
function signed_in(request: Request): boolean {
    const pieces: string[] = cookie_value(request).split(".");

    const expires: string = pieces[0] ?? "";

    const signature: string = pieces[1] ?? "";

    if(expires === "" || signature === "" || Number(expires) < Date.now()) {
        return false;
    }

    return same_text(signature, sign(expires));
}


//REFUSE
//401 without a good session, null means go on
export function refuse(request: Request): Response | null {
    if(signed_in(request)) {
        return null;
    }

    return http.fail(401, "Sign in to see the dashboard.");
}
