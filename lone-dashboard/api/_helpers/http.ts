//REPLIES

//json the browser never caches, extra headers ride along on top
export function json(data: unknown, status: number = 200, headers: Record<string, string> = {}): Response {
    const all_headers: Record<string, string> = {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"};

    //extra headers go on top, like the session cookie
    for(const header of Object.entries(headers)) {
        all_headers[header[0]] = header[1];
    }

    return new Response(JSON.stringify(data), {"status": status, "headers": all_headers});
}

//an error reply, just the status and a line saying what broke
export function fail(status: number, error: string): Response {
    return json({"error": error}, status);
}


//REQUESTS

//null when theres no body or it isn't json
export async function read_body(request: Request): Promise<Record<string, unknown> | null> {
    try {
        const data: unknown = await request.json();

        if(typeof data === "object" && data !== null) {
            return data as Record<string, unknown>;
        }

        return null;
    }
    catch {
        return null;
    }
}


//GUARD

//no bare 500s, the page gets told what broke
export async function guarded(work: (request: Request) => Promise<Response>, request: Request): Promise<Response> {
    try {
        return await work(request);
    }
    catch(error: unknown) {
        console.error(error);

        let message: string = "Something broke on the server.";

        if(error instanceof Error) {
            message = error.message;
        }

        return fail(500, message);
    }
}
