//**********IMPORTS**********
//the api call and page lookups every page shares
import * as shared from "./shared.js";



//**********GLOBALS**********
//the sign in form's parts


//FORM PARTS
const LOGIN_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("login-form");

const PASSWORD_INPUT: HTMLInputElement = shared.by_id<HTMLInputElement>("password");

const LOGIN_ERROR: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("login-error");

const LOGIN_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("login-button");



//**********SIGN IN**********
//sends the password, then back to the page they came from


//SAFE DESTINATION
//only ever a page on this site, parsing it as a url catches tricks like "/\evil.com" that browsers read as "//evil.com"
function safe_destination(): string {
    try {
        const next: URL = new URL(new URLSearchParams(location.search).get("next") ?? "/", location.origin);

        if(next.origin === location.origin) {
            return next.pathname + next.search + next.hash;
        }

        return "/";
    }

    catch {
        return "/";
    }
}


//SEND LOGIN
//wrong password or a lockout shows the server's words, anything else means it couldn't be reached
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

        if(failure instanceof shared.ServerError) {
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



//**********START**********
//cursor in the password box, then wait for the form


//FOCUS
PASSWORD_INPUT.focus();


//SUBMIT
LOGIN_FORM.addEventListener("submit", send_login);
