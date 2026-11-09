//IMPORTS

import * as http from "./_helpers/http.js";
import * as session from "./_helpers/session.js";


//ROUTE

//signs out by handing the browser a cookie thats already expired
export function POST(): Response {
    return http.json({"ok": true}, 200, {"Set-Cookie": session.cleared_cookie()});
}
