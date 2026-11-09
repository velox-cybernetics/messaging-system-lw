//IMPORTS

import * as shop from "./shop.js";


//GLOBALS

const CHAT_URL: string = "https://openrouter.ai/api/v1/chat/completions";


//CHAT REQUESTS

//openrouters own message when it sent one, an upstream error can come back inside a 200 too
function openrouter_detail(data: Record<string, unknown>, response: Response): string {
    const message: unknown = shop.fields_of(data.error).message;

    if(typeof message === "string") {
        return message;
    }

    let detail: string = response.statusText;

    if(!detail) {
        detail = "no answer in the body";
    }

    return detail;
}

//the models plain answer, empty when it had no text, throws when it never answered at all
export async function openrouter_text(system_prompt: string, user_text: string, model: string, effort: string, timeout_ms: number): Promise<string> {
    const body: Record<string, unknown> = {"model": model, "reasoning": {"effort": effort}, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}]};

    let response: Response;

    const key: string = shop.setting(process.env.OPENROUTER_API_KEY, "");

    try {
        response = await fetch(CHAT_URL, {"method": "POST", "headers": {"Authorization": `Bearer ${key}`, "Content-Type": "application/json"}, "body": JSON.stringify(body), "signal": AbortSignal.timeout(timeout_ms)});
    }
    catch(error: unknown) {
        //a timeout or a dropped connection never gets an answer at all
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
