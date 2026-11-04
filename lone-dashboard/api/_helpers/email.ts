//**********GLOBALS**********
//where flag emails go and who they come from, both set in vercel


//FLAG EMAIL
//till a domain is verified in resend, has to be the address the resend account signed up with
export const FLAG_EMAIL: string = process.env.FLAG_EMAIL ?? "";


//FROM
const FROM: string = process.env.RESEND_FROM ?? "Lone Wraps Dashboard <onboarding@resend.dev>";


//RESEND
const RESEND_URL: string = "https://api.resend.com/emails";



//**********SENDING**********
//flag emails go out through resend's http api


//RESEND DETAIL
//resend's own message when it sent one, else the status text
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


//SEND EMAIL
export async function send_email(subject: string, text: string, html: string): Promise<void> {
    const key: string = process.env.RESEND_API_KEY ?? "";

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
