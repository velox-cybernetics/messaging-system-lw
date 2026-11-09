//IMPORTS

import * as shared from "./shared.js";


//GLOBALS

const LOGIN_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("login-form");

const PASSWORD_INPUT: HTMLInputElement = shared.by_id<HTMLInputElement>("password");

const LOGIN_ERROR: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("login-error");

const LOGIN_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("login-button");


//SIGN IN

//only ever a page on this site, a real url parse catches sneaky paths that lead off it
function safe_destination(): string {
    try {
        let wanted: string | null = new URLSearchParams(location.search).get("next");

        if(wanted === null) {
            wanted = "/";
        }

        const next: URL = new URL(wanted, location.origin);

        if(next.origin === location.origin) {
            return next.pathname + next.search + next.hash;
        }

        return "/";
    }
    catch {
        return "/";
    }
}

//wrong password or a lockout shows the servers words, anything else means it couldn't be reached
async function send_login(event: SubmitEvent): Promise<void> {
    event.preventDefault();

    LOGIN_ERROR.hidden = true;

    LOGIN_BUTTON.disabled = true;

    try {
        await shared.ask_server("/api/login", "POST", {"password": PASSWORD_INPUT.value});

        location.assign(safe_destination());
    }
    catch(failure: unknown) {
        let message: string = "Couldn't reach the server. Check your connection and try again.";

        if(shared.is_server_error(failure)) {
            message = failure.message;
        }

        LOGIN_ERROR.textContent = message;

        LOGIN_ERROR.hidden = false;

        PASSWORD_INPUT.select();
    }
    finally {
        LOGIN_BUTTON.disabled = false;
    }
}


//START

PASSWORD_INPUT.focus();

LOGIN_FORM.addEventListener("submit", send_login);
