//**********IMPORTS**********
//the feed's json readers
import * as shop from "./shop.js";



//**********GLOBALS**********
//where chat requests go, same as helpers/models/openrouter.py


//CHAT URL
const CHAT_URL: string = "https://openrouter.ai/api/v1/chat/completions";



//**********CHAT REQUESTS**********
//one system prompt and one input to one model, with the key set in vercel as OPENROUTER_API_KEY


//OPENROUTER DETAIL
//openrouter's own message when it sent one, an upstream error can come back inside a 200 too
function openrouter_detail(data: Record<string, unknown>, response: Response): string {
    const message: unknown = shop.fields_of(data.error).message;

    if(typeof message === "string") {
        return message;
    }

    return response.statusText || "no answer in the body";
}


//OPENROUTER TEXT
//the model's plain answer, "" when it came back with no text, throws with what went wrong when it never answered
export async function openrouter_text(system_prompt: string, user_text: string, model: string, effort: string, timeout_ms: number): Promise<string> {
    const body: Record<string, unknown> = {"model": model, "reasoning": {"effort": effort}, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}]};

    let response: Response;

    try {
        response = await fetch(CHAT_URL, {"method": "POST", "headers": {"Authorization": `Bearer ${process.env.OPENROUTER_API_KEY ?? ""}`, "Content-Type": "application/json"}, "body": JSON.stringify(body), "signal": AbortSignal.timeout(timeout_ms)});
    }

    //a timeout or a dropped connection never gets an answer at all
    catch(error: unknown) {
        let message: string = String(error);

        if(error instanceof Error) {
            message = error.message;
        }

        throw new Error(`OpenRouter never answered: ${message}`);
    }

    let data: Record<string, unknown> = {};

    try {
        data = shop.fields_of(await response.json());
    }

    catch {
        data = {};
    }

    if(!response.ok || !Array.isArray(data.choices)) {
        throw new Error(`OpenRouter didn't answer (${response.status}): ${openrouter_detail(data, response)}`);
    }

    const content: unknown = shop.fields_of(shop.fields_of(data.choices[0]).message).content;

    if(typeof content !== "string") {
        return "";
    }

    return content;
}
