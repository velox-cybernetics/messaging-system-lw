//IMPORTS

import * as shop from "./shop.js";


//GLOBALS

//till a domain is verified in resend, has to be the address the resend account signed up with
export const FLAG_EMAIL: string = shop.setting(process.env.FLAG_EMAIL, "");

const FROM: string = shop.setting(process.env.RESEND_FROM, "Lone Wraps Dashboard <onboarding@resend.dev>");

const RESEND_URL: string = "https://api.resend.com/emails";


//SENDING

//resends own message when it sent one, else the status text
async function resend_detail(response: Response): Promise<string> {
    let data: unknown = null;

    try {
        data = await response.json();
    }
    catch {
        data = null;
    }

    if(data !== null && typeof data === "object" && "message" in data) {
        return String(data.message);
    }

    return response.statusText;
}

//one email through resend, throws when a setting is missing or resend says no
export async function send_email(subject: string, text: string, html: string): Promise<void> {
    const key: string = shop.setting(process.env.RESEND_API_KEY, "");

    if(key === "") {
        throw new Error("RESEND_API_KEY isn't set in Vercel, so flags can't be emailed.");
    }

    if(FLAG_EMAIL === "") {
        throw new Error("FLAG_EMAIL isn't set in Vercel, so flags can't be emailed.");
    }

    const response: Response = await fetch(RESEND_URL, {"method": "POST", "headers": {"Authorization": `Bearer ${key}`, "Content-Type": "application/json"}, "body": JSON.stringify({"from": FROM, "to": [FLAG_EMAIL], "subject": subject, "text": text, "html": html})});

    if(!response.ok) {
        throw new Error(`Resend refused the email: ${await resend_detail(response)}`);
    }
}
