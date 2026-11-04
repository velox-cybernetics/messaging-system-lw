//**********IMPORTS**********
//the replies, the database and the sign in check
import * as http from "./_helpers/http.js";
import * as redis from "./_helpers/redis.js";
import * as session from "./_helpers/session.js";



//**********PULSE**********
//the one cheap read the pages poll, so they only reload when something changed


//READ PULSE
//feed bumps version on every write, up_last is the system's last check in, one MGET for both
async function read_pulse(request: Request): Promise<Response> {
    const refused: Response | null = session.refuse(request);

    if(refused !== null) {
        return refused;
    }

    const values: string[] = redis.as_strings(await redis.command(["MGET", "version", "up_last"]));

    return http.json({"version": redis.as_number(values[0]), "up_last": redis.as_number(values[1])});
}



//**********ROUTE**********
//what vercel runs for GET /api/pulse


//GET
export function GET(request: Request): Promise<Response> {
    return http.guarded(read_pulse, request);
}
