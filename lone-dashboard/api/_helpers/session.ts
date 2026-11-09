//IMPORTS

import { createHash, createHmac, timingSafeEqual } from "node:crypto";

import * as http from "./http.js";
import * as shop from "./shop.js";


//GLOBALS

const COOKIE_NAME: string = "lw_session";

const SESSION_DAYS: number = 30;

const DAY_SECONDS: number = 86400;


//PASSWORD

//the dashboard password from vercel, no password means no way in at all
function password(): string {
    const value: string = shop.setting(process.env.DASH_PASSWORD, "");

    if(value === "") {
        throw new Error("DASH_PASSWORD isn't set in Vercel, so nobody can sign in.");
    }

    return value;
}

//hash both first so the compare takes the same time no matter what got typed
function same_text(given: string, expected: string): boolean {
    const given_hash: Buffer = createHash("sha256").update(given).digest();

    const expected_hash: Buffer = createHash("sha256").update(expected).digest();

    return timingSafeEqual(given_hash, expected_hash);
}

//true when what got typed is the dashboard password
export function password_matches(given: string): boolean {
    return same_text(given, password());
}


//SESSION

//key comes from the password, so changing it signs everyone out
function sign(value: string): string {
    const key: Buffer = createHash("sha256").update(`lone-dashboard session:${password()}`).digest();

    return createHmac("sha256", key).update(value).digest("base64url");
}

//a signed cookie good for 30 days, the signature is the whole lock
export function session_cookie(): string {
    const expires: string = String(Date.now() + SESSION_DAYS * DAY_SECONDS * 1000);

    return `${COOKIE_NAME}=${expires}.${sign(expires)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${SESSION_DAYS * DAY_SECONDS}`;
}

//an empty cookie thats already expired, so the browser forgets it
export function cleared_cookie(): string {
    return `${COOKIE_NAME}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`;
}

//last lw_session cookie wins, and its value can hold an equals sign too
function cookie_value(request: Request): string {
    let value: string = "";

    let header: string | null = request.headers.get("cookie");

    if(header === null) {
        header = "";
    }

    const pairs: string[] = header.split(";");

    for(const pair of pairs) {
        const pieces: string[] = pair.trim().split("=");

        if(pieces[0] === COOKIE_NAME) {
            value = pieces.slice(1).join("=");
        }
    }

    return value;
}

//true for a cookie that hasn't expired and carries the right signature
function signed_in(request: Request): boolean {
    const pieces: string[] = cookie_value(request).split(".");

    let expires: string | undefined = pieces[0];

    if(expires === undefined) {
        expires = "";
    }

    let signature: string | undefined = pieces[1];

    if(signature === undefined) {
        signature = "";
    }

    if(expires === "" || signature === "" || Number(expires) < Date.now()) {
        return false;
    }

    return same_text(signature, sign(expires));
}

//a 401 without a good session, null means go on
export function refuse(request: Request): Response | null {
    if(signed_in(request)) {
        return null;
    }

    return http.fail(401, "Sign in to see the dashboard.");
}
