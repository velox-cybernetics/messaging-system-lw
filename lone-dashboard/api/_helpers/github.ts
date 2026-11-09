//IMPORTS

import * as shop from "./shop.js";


//GLOBALS

//same repo and branch the render yaml deploys from, so every push to main goes out on its own
const REPO: string = "velox-cybernetics/messaging-system-lw";

const BRANCH: string = "main";

const API_URL: string = "https://api.github.com";

const API_VERSION: string = "2022-11-28";

//a plain file, never executable
const FILE_MODE: string = "100644";

//the newest commit on main and the tree of files it points at
export type HEAD = {commit: string; tree: string};


//REQUESTS

//githubs own message when it sent one, else the status text
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

//throws with what github said when it refused, accept is the shape the answer comes back in
async function ask_github(path: string, method: string = "GET", body: unknown = null, accept: string = "application/vnd.github+json"): Promise<Response> {
    const token: string = shop.setting(process.env.GITHUB_TOKEN, "");

    const options: RequestInit = {"method": method, "headers": {"Authorization": `Bearer ${token}`, "Accept": accept, "X-GitHub-Api-Version": API_VERSION, "User-Agent": "lone-dashboard"}};

    if(body !== null) {
        options.body = JSON.stringify(body);
    }

    const response: Response = await fetch(`${API_URL}/repos/${REPO}${path}`, options);

    if(!response.ok) {
        throw new Error(`GitHub refused it (${response.status}): ${await github_detail(response)}`);
    }

    return response;
}

//the answer as plain fields
async function github_fields(path: string, method: string = "GET", body: unknown = null): Promise<Record<string, unknown>> {
    const response: Response = await ask_github(path, method, body);

    return shop.fields_of(await response.json());
}


//FILES

//where main is right now, its newest commit and that commits tree
export async function read_head(): Promise<HEAD> {
    const branch: Record<string, unknown> = await github_fields(`/branches/${BRANCH}`);

    const commit: Record<string, unknown> = shop.fields_of(branch.commit);

    const tree: Record<string, unknown> = shop.fields_of(shop.fields_of(commit.commit).tree);

    let commit_sha: unknown = commit.sha;

    if(commit_sha === undefined || commit_sha === null) {
        commit_sha = "";
    }

    let tree_sha: unknown = tree.sha;

    if(tree_sha === undefined || tree_sha === null) {
        tree_sha = "";
    }

    return {"commit": String(commit_sha), "tree": String(tree_sha)};
}

//raw, so a prompt file past the 1 MB githubs json answers stop at still comes back whole
export async function read_file(head: HEAD, path: string): Promise<string> {
    const response: Response = await ask_github(`/contents/${path}?ref=${head.commit}`, "GET", null, "application/vnd.github.raw+json");

    return response.text();
}

//one commit on head with the file changed, main only moves if nothing else landed since
export async function push_file(head: HEAD, path: string, text: string, message: string): Promise<string> {
    const tree: Record<string, unknown> = await github_fields("/git/trees", "POST", {"base_tree": head.tree, "tree": [{"path": path, "mode": FILE_MODE, "type": "blob", "content": text}]});

    const commit: Record<string, unknown> = await github_fields("/git/commits", "POST", {"message": message, "tree": tree.sha, "parents": [head.commit]});

    await ask_github(`/git/refs/heads/${BRANCH}`, "PATCH", {"sha": commit.sha});

    let commit_sha: unknown = commit.sha;

    if(commit_sha === undefined || commit_sha === null) {
        commit_sha = "";
    }

    return String(commit_sha);
}

//true once the commit running is this one or one after it on main
export async function has_commit(running: string, commit: string): Promise<boolean> {
    if(running === commit) {
        return true;
    }

    const compare: Record<string, unknown> = await github_fields(`/compare/${commit}...${running}`);

    return compare.status === "identical" || compare.status === "ahead";
}
