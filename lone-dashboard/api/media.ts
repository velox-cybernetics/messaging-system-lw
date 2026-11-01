//**********IMPORTS**********
//the replies, the database and the sign in check
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";



//**********GLOBALS**********
//what a pic id looks like and how long the browser keeps a pic


//PIC ID
//the feed names every copy with 32 hex characters
const PIC_ID: RegExp = /^[0-9a-f]{32}$/;


//PIC CACHE
//a copy never changes, so the browser can keep it the whole 30 days
const PIC_CACHE: string = "private, max-age=2592000, immutable";



//**********PICS**********
//pics the feed kept a copy of, jpegs that expire 30 days after they came in


//READ PIC
async function read_pic(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const id: string = new URL(request.url).searchParams.get("id") ?? "";

    if(!PIC_ID.test(id)) {
        return http.fail(400, "That pic id isn't valid.");
    }

    const data: unknown = await redis.command(["GET", `media:${id}`]);

    if(typeof data !== "string") {
        return http.fail(404, "This pic is past its 30 days and is no longer kept.");
    }

    return new Response(Buffer.from(data, "base64"), {"headers": {"Content-Type": "image/jpeg", "Cache-Control": PIC_CACHE}});
}



//**********ROUTE**********
//what vercel runs for GET /api/media


//GET
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_pic, request);
}
