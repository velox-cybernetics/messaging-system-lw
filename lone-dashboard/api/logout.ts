//**********IMPORTS**********
//the replies and the cookie that signs someone out
import * as http from "./_helpers/http.js";
import * as session from "./_helpers/session.js";



//**********ROUTE**********
//what vercel runs for POST /api/logout, swaps the session for an expired cookie


//POST
export function POST(): Response {
    return http.json({"ok": true}, 200, {"Set-Cookie": session.cleared_cookie()});
}
