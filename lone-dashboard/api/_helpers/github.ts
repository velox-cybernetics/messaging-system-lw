//**********IMPORTS**********
//the feed's json readers
import * as shop from "./shop.js";



//**********GLOBALS**********
//the repo render deploys the system from, and github's api


//REPO
//same repo and branch render.yaml deploys from, so every push to main goes out on its own
const REPO: string = "velox-cybernetics/messaging-system-lw";

const BRANCH: string = "main";


//API
const API_URL: string = "https://api.github.com";

const API_VERSION: string = "2022-11-28";


//FILE MODE
//a plain file, never executable
const FILE_MODE: string = "100644";


//HEAD
//the newest commit on main and the tree of files it points at
export type HEAD = {commit: string; tree: string};



//**********REQUESTS**********
//every call to github goes out with the token set in vercel as GITHUB_TOKEN


//GITHUB DETAIL
//github's own message when it sent one, else the status text
async function github_detail(response: Response): Promise<string> {
    let data: unknown = null;

    try {
        data = await response.json();
    }

    catch {
        data = null;
    }

    const message: unknown = shop.fields_of(data).message;

    if(typeof message === "string") {
        return message;
    }

    return response.statusText;
}


//ASK GITHUB
//throws with what github said when it refused, accept is the shape the answer comes back in
async function ask_github(path: string, method: string = "GET", body: unknown = null, accept: string = "application/vnd.github+json"): Promise<Response> {
    const options: RequestInit = {"method": method, "headers": {"Authorization": `Bearer ${process.env.GITHUB_TOKEN ?? ""}`, "Accept": accept, "X-GitHub-Api-Version": API_VERSION, "User-Agent": "lone-dashboard"}};

    if(body !== null) {
        options.body = JSON.stringify(body);
    }

    const response: Response = await fetch(`${API_URL}/repos/${REPO}${path}`, options);

    if(!response.ok) {
        throw new Error(`GitHub refused it (${response.status}): ${await github_detail(response)}`);
    }

    return response;
}


//GITHUB FIELDS
//the answer as plain fields
async function github_fields(path: string, method: string = "GET", body: unknown = null): Promise<Record<string, unknown>> {
    const response: Response = await ask_github(path, method, body);

    return shop.fields_of(await response.json());
}



//**********FILES**********
//reads a file off main and pushes it back changed in one commit


//READ HEAD
export async function read_head(): Promise<HEAD> {
    const branch: Record<string, unknown> = await github_fields(`/branches/${BRANCH}`);

    const commit: Record<string, unknown> = shop.fields_of(branch.commit);

    const tree: Record<string, unknown> = shop.fields_of(shop.fields_of(commit.commit).tree);

    return {"commit": String(commit.sha ?? ""), "tree": String(tree.sha ?? "")};
}


//READ FILE
//raw, so a prompt file past the 1 MB github's json answers stop at still comes back whole
export async function read_file(head: HEAD, path: string): Promise<string> {
    const response: Response = await ask_github(`/contents/${path}?ref=${head.commit}`, "GET", null, "application/vnd.github.raw+json");

    return response.text();
}


//PUSH FILE
//one commit on top of head with the file changed, main only moves when nothing else got pushed since, the new commit comes back
export async function push_file(head: HEAD, path: string, text: string, message: string): Promise<string> {
    const tree: Record<string, unknown> = await github_fields("/git/trees", "POST", {"base_tree": head.tree, "tree": [{"path": path, "mode": FILE_MODE, "type": "blob", "content": text}]});

    const commit: Record<string, unknown> = await github_fields("/git/commits", "POST", {"message": message, "tree": tree.sha, "parents": [head.commit]});

    await ask_github(`/git/refs/heads/${BRANCH}`, "PATCH", {"sha": commit.sha});

    return String(commit.sha ?? "");
}


//HAS COMMIT
//true once the commit running is this one or one after it on main
export async function has_commit(running: string, commit: string): Promise<boolean> {
    if(running === commit) {
        return true;
    }

    const compare: Record<string, unknown> = await github_fields(`/compare/${commit}...${running}`);

    return compare.status === "identical" || compare.status === "ahead";
}
