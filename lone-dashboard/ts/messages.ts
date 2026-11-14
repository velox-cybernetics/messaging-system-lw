//IMPORTS

import * as shared from "./shared.js";


//GLOBALS

type TAB = "forms" | "instagram" | "messenger";

//each tab splits into the convos the system answers, the ones with a booked hil and the ones switched off
type VIEW = "on" | "booked" | "off";

//snippet and hits only come with a search, the message it matched in and the words to mark
type CONVO = {id: string; tab: TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string; off: boolean; booked: boolean; flagged_at: number; snippet?: string; hits?: string[]};

//same convo plus whether its whole channel is switched off
type THREAD_CONVO = {id: string; tab: TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string; off: boolean; booked: boolean; tab_off: boolean; flagged_at: number};

type MEDIA = {kind: "pic"; id: string; width?: number; height?: number; caption: string} | {kind: "video" | "link"; url: string; caption: string} | {kind: "post"; caption: string};

type PART = {text?: string; media?: MEDIA};

type ENTRY = {at: number; kind: "in"; parts: PART[]; off?: boolean} | {at: number; kind: "out"; parts: PART[]; failed?: boolean; ghl?: boolean; sms?: boolean} | {at: number; kind: "hil" | "booked"; reason: string} | {at: number; kind: "switch"; on: boolean; by?: "ghl"} | {at: number; kind: "flag"; feedback: string} | {at: number; kind: "upvote"; reason: string; generator: string; example: number};

type CONVO_PAGE = {tab: TAB; view: VIEW; query: string; counts: Record<TAB, number>; view_counts: Record<VIEW, number>; off_tabs: TAB[]; more: boolean; convos: CONVO[]};

type THREAD = {convo: THREAD_CONVO; entries: ENTRY[]};

type FLAG_RESULT = {ok: boolean; sent_to: string; flagged_at: number};

//the prompt file the example went in, its number and the commit it got pushed in
type UPVOTE_RESULT = {ok: boolean; generator: string; example: number; commit: string};

type LIVE_RESULT = {commit: string; running: string; live: boolean};

//writing the example, deploying it, done once the system runs it, or failed on the way
type UPVOTE_STAGE = "idle" | "writing" | "deploying" | "done" | "failed";

//an upvote on its way, after is the threads newest entry when it was sent
type UPVOTE = {id: string; name: string; stage: UPVOTE_STAGE; sent_at: number; commit: string; pushed_at: number; after: number; logged: boolean};

type TAB_PARTS = {button: HTMLButtonElement; count: HTMLSpanElement; off_mark: HTMLSpanElement};

type VIEW_PARTS = {button: HTMLButtonElement; count: HTMLSpanElement};

const TABS: TAB[] = ["forms", "instagram", "messenger"];

const TAB_NAMES: Record<TAB, string> = {"forms": "Forms", "instagram": "Instagram", "messenger": "Messenger"};

const VIEWS: VIEW[] = ["on", "booked", "off"];

//the three lists by name, for what an empty search says
const VIEW_NAMES: Record<VIEW, string> = {"on": "System on", "booked": "Booked HILs", "off": "System off"};

//only web links get linked, so a customer can't slip a script link in
const WEB_LINK: RegExp = /^https?:\/\//i;

//same words and plain forms as the apis search helper, so a mark lands on the exact word it matched
const WORD: RegExp = /[\p{L}\p{N}'’]+/gu;

const ACCENTS: RegExp = /\p{M}/gu;

const APOSTROPHES: RegExp = /['’]/g;

//within this many px of the bottom, a refresh keeps the thread scrolled down
const NEAR_BOTTOM_PX: number = 80;

//the search waits till typing stops this long, so a fast typist sends one search not ten
const SEARCH_WAIT_MS: number = 250;

//render takes a few minutes to deploy, so the check goes every 15s and gives up after 15 minutes
const UPVOTE_CHECK_MS: number = 15 * 1000;

const UPVOTE_WAIT_MS: number = 15 * 60 * 1000;

//the rings css takes 600ms to close, its line goes in the log right after
const UPVOTE_FILL_MS: number = 700;

//a full ring stays a moment after its line goes in, then the arrow goes back to how it was
const UPVOTE_HOLD_MS: number = 2500;

//a failed one stays red as long as its toast shows, then clears
const UPVOTE_RED_MS: number = 5000;

//the ring creeps toward each fill, slowing as it goes so it never looks done early
const WRITING_FILL: number = 0.4;

const WRITING_PACE_MS: number = 12 * 1000;

const DEPLOYING_FILL: number = 0.92;

const DEPLOYING_PACE_MS: number = 75 * 1000;

//it moves on every second, the css glides it between
const UPVOTE_TICK_MS: number = 1000;

//a deploying upvote is kept in the tabs storage, so a reload picks its ring back up
const UPVOTE_KEY: string = "upvote";

//the only commit a kept upvote can carry
const COMMIT_SHA: RegExp = /^[0-9a-f]{40}$/;

//the line an upvote leaves in the conversation once its ring fills
const UPWEIGHTED: string = "Response up-weighted!";

//what the arrow says at each stage when you hover it
const UPVOTE_TITLES: Record<UPVOTE_STAGE, string> = {"idle": "Up-weight the last response", "writing": "Up-weighting…", "deploying": "Up-weighting, the system is updating…", "done": UPWEIGHTED, "failed": "The up-weight didn't go through"};

const PAGE: HTMLElement = shared.by_id<HTMLElement>("messages");

const TABS_NAV: HTMLElement = shared.by_id<HTMLElement>("tabs");

const LIST: HTMLUListElement = shared.by_id<HTMLUListElement>("convos");

const LIST_PANE: HTMLElement = shared.by_id<HTMLElement>("list-pane");

const LIST_NOTE: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("list-note");

const MORE_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("more");

const THREAD_HEAD: HTMLElement = shared.by_id<HTMLElement>("thread-head");

const THREAD_NAME: HTMLHeadingElement = shared.by_id<HTMLHeadingElement>("thread-name");

const THREAD_META: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("thread-meta");

const SWITCH_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("switch");

const SWITCH_LABEL: HTMLSpanElement = shared.by_id<HTMLSpanElement>("switch-label");

const UPVOTE_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("upvote");

const FLAG_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("flag");

const CHANNEL_BAR: HTMLElement = shared.by_id<HTMLElement>("channel-bar");

const CHANNEL_SWITCH: HTMLButtonElement = shared.by_id<HTMLButtonElement>("channel-switch");

const CHANNEL_SWITCH_LABEL: HTMLSpanElement = shared.by_id<HTMLSpanElement>("channel-switch-label");

const LIST_HEAD: HTMLElement = shared.by_id<HTMLElement>("list-head");

const VIEW_ON_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("view-on");

const VIEW_ON_COUNT: HTMLSpanElement = shared.by_id<HTMLSpanElement>("view-on-count");

const VIEW_BOOKED_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("view-booked");

const VIEW_BOOKED_COUNT: HTMLSpanElement = shared.by_id<HTMLSpanElement>("view-booked-count");

const VIEW_OFF_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("view-off");

const VIEW_OFF_COUNT: HTMLSpanElement = shared.by_id<HTMLSpanElement>("view-off-count");

const VIEW_BUTTONS: Record<VIEW, VIEW_PARTS> = {"on": {"button": VIEW_ON_BUTTON, "count": VIEW_ON_COUNT}, "booked": {"button": VIEW_BOOKED_BUTTON, "count": VIEW_BOOKED_COUNT}, "off": {"button": VIEW_OFF_BUTTON, "count": VIEW_OFF_COUNT}};

const SEARCH_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("search");

const SEARCH_TEXT: HTMLInputElement = shared.by_id<HTMLInputElement>("search-text");

const SEARCH_CLEAR: HTMLButtonElement = shared.by_id<HTMLButtonElement>("search-clear");

const LOG: HTMLElement = shared.by_id<HTMLElement>("log");

const BACK_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("back");

//texts out from the dashboard go on the blooio line, so only the forms tab gets the box
const COMPOSE_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("compose");

const COMPOSE_TEXT: HTMLTextAreaElement = shared.by_id<HTMLTextAreaElement>("compose-text");

const COMPOSE_SEND: HTMLButtonElement = shared.by_id<HTMLButtonElement>("compose-send");

const FLAG_DIALOG: HTMLDialogElement = shared.by_id<HTMLDialogElement>("flag-dialog");

const FLAG_TEXT: HTMLTextAreaElement = shared.by_id<HTMLTextAreaElement>("flag-text");

const FLAG_ERROR: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("flag-error");

const FLAG_SEND: HTMLButtonElement = shared.by_id<HTMLButtonElement>("flag-send");

const FLAG_CANCEL: HTMLButtonElement = shared.by_id<HTMLButtonElement>("flag-cancel");

const FLAG_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("flag-form");

const UPVOTE_DIALOG: HTMLDialogElement = shared.by_id<HTMLDialogElement>("upvote-dialog");

const UPVOTE_TEXT: HTMLTextAreaElement = shared.by_id<HTMLTextAreaElement>("upvote-text");

const UPVOTE_ERROR: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("upvote-error");

const UPVOTE_CANCEL: HTMLButtonElement = shared.by_id<HTMLButtonElement>("upvote-cancel");

const UPVOTE_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("upvote-form");

const TRASH_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("trash");

const TRASH_DIALOG: HTMLDialogElement = shared.by_id<HTMLDialogElement>("trash-dialog");

const TRASH_NOTE: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("trash-note");

const TRASH_ERROR: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("trash-error");

const TRASH_CONFIRM: HTMLButtonElement = shared.by_id<HTMLButtonElement>("trash-confirm");

const TRASH_CANCEL: HTMLButtonElement = shared.by_id<HTMLButtonElement>("trash-cancel");

const TRASH_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("trash-form");

const ADDRESS: URLSearchParams = new URLSearchParams(location.search);

const ADDRESS_TAB: string | null = ADDRESS.get("tab");

//built once in START, so a refresh never pulls focus off the one being used
const TAB_BUTTONS: Map<TAB, TAB_PARTS> = new Map<TAB, TAB_PARTS>();

//tab, view and id get set from the address in START
let CURRENT_TAB: TAB = "forms";

let CURRENT_VIEW: VIEW = "on";

let CURRENT_ID: string = "";

let SHOWN_CONVOS: CONVO[] = [];

let CURRENT_CONVO: THREAD_CONVO | null = null;

//tabs with there whole channel switched off, as of the last list load
let OFF_TABS: Set<TAB> = new Set<TAB>();

//whats in the search box trimmed, empty means the plain list
let CURRENT_QUERY: string = "";

//the wait before a search goes out
let SEARCH_TIMER: number = 0;

//the words each search result matched by convo id, so a thread opened from the results gets them marked too
const HITS: Map<string, string[]> = new Map<string, string[]>();

//the hits the open thread has marked right now, so a list refresh only redoes the thread when they change
let LOG_MARKS: string = "";

//the one upvote going, null till theres one
let CURRENT_UPVOTE: UPVOTE | null = null;

//moves the ring on every second while the open convos upvote is going, 0 when it isn't
let UPVOTE_TICKER: number = 0;

//the open threads newest entry, an upvotes own line is anything newer than this was
let NEWEST_AT: number = 0;


//PLACE

//true for one of the three tabs, so a made up tab in the address gets ignored
function is_tab(value: string | null): value is TAB {
    for(const tab of TABS) {
        if(tab === value) {
            return true;
        }
    }

    return false;
}

//there name, or their id dressed up when the channel never gave one
function convo_title(convo: CONVO | THREAD_CONVO): string {
    let title: string = convo.name;

    if(!title) {
        title = shared.readable_id(convo.id);
    }

    return title;
}

//so a reload or a link from a flag email opens the same place
function remember_place(): void {
    const query: URLSearchParams = new URLSearchParams({"tab": CURRENT_TAB});

    if(CURRENT_VIEW !== "on") {
        query.set("view", CURRENT_VIEW);
    }

    if(CURRENT_QUERY) {
        query.set("q", CURRENT_QUERY);
    }

    if(CURRENT_ID) {
        query.set("id", CURRENT_ID);
    }

    history.replaceState(null, "", `/messages?${query}`);
}


//MARKS

//lowercase, no accents and no apostrophes, same as plain_word in the apis search helper
function plain_word(word: string): string {
    return word.normalize("NFD").replace(ACCENTS, "").replace(APOSTROPHES, "").toLowerCase();
}

//the text with every hit word wrapped in a mark, just the text when theres nothing to mark
function marked(text: string, hits: string[]): (string | HTMLElement)[] {
    const pieces: (string | HTMLElement)[] = [];

    let last: number = 0;

    if(hits.length > 0) {
        for(const found of text.matchAll(WORD)) {
            if(hits.includes(plain_word(found[0]))) {
                pieces.push(text.slice(last, found.index));

                pieces.push(shared.make_element("mark", {}, [found[0]]));

                last = found.index + found[0].length;
            }
        }
    }

    pieces.push(text.slice(last));

    return pieces;
}

//the open convos hits, none without a search or when it isn't one of the results
function open_hits(): string[] {
    const hits: string[] | undefined = HITS.get(CURRENT_ID);

    if(CURRENT_QUERY === "" || hits === undefined) {
        return [];
    }

    return hits;
}

//marks the hits in what the customer wrote in the open thread, or takes them off once the search is gone
function mark_log(): void {
    const hits: string[] = open_hits();

    LOG_MARKS = hits.join(" ");

    for(const bubble of LOG.querySelectorAll<HTMLElement>(".msg.is-in .bubble")) {
        let text: string | null = bubble.textContent;

        if(text === null) {
            text = "";
        }

        bubble.replaceChildren();

        for(const piece of marked(text, hits)) {
            bubble.append(piece);
        }
    }
}

//the newest marked message in the open thread, null when nothing is marked
function newest_mark(): HTMLElement | null {
    const marks: NodeListOf<HTMLElement> = LOG.querySelectorAll<HTMLElement>(".msg.is-in mark");

    if(marks.length === 0) {
        return null;
    }

    return marks.item(marks.length - 1).closest<HTMLElement>(".msg");
}

//scrolls the log so that message sits in the middle of it
function center_in_log(message: HTMLElement): void {
    const box: DOMRect = message.getBoundingClientRect();

    LOG.scrollTop += box.top - LOG.getBoundingClientRect().top - (LOG.clientHeight - box.height) / 2;
}


//THREAD

//pic copies only last 30 days, an old one turns into a note
function show_gone_pic(image: HTMLImageElement): void {
    image.replaceWith(shared.make_element("span", {"class": "attachment is-gone"}, ["Pic no longer kept. Copies last 30 days."]));
}

//a pic, video, link or shared post, ready to go in a message
function media_node(media: MEDIA, from_customer: boolean): HTMLElement {
    if(media.kind === "pic") {
        const src: string = `/api/media?id=${encodeURIComponent(media.id)}`;

        let alt: string = "Pic the system sent";

        if(from_customer) {
            alt = "Pic the customer sent";
        }

        const attributes: Record<string, string> = {"src": src, "alt": alt, "loading": "lazy"};

        //size kept with the copy holds its space before it loads, so the thread doesn't jump
        if(media.width && media.height) {
            attributes["width"] = String(media.width);

            attributes["height"] = String(media.height);
        }

        const image: HTMLImageElement = shared.make_element("img", attributes);

        //a pic that won't load gets the gone note instead
        function on_gone(): void {
            show_gone_pic(image);
        }

        image.addEventListener("error", on_gone);

        return shared.make_element("a", {"class": "pic", "href": src, "target": "_blank", "rel": "noopener"}, [image]);
    }

    if(media.kind === "post") {
        let post_text: string = media.caption;

        if(!post_text) {
            post_text = "Shared post";
        }

        return shared.make_element("span", {"class": "attachment"}, [post_text]);
    }

    let label: string = "Attachment";

    if(media.kind === "video") {
        label = "Video";
    }

    let link: HTMLAnchorElement | string = label;

    if(WEB_LINK.test(media.url)) {
        link = shared.make_element("a", {"href": media.url, "target": "_blank", "rel": "noopener noreferrer"}, [label]);
    }

    //empty caption gets left out
    let caption: string = "";

    if(media.caption) {
        caption = ` ${media.caption}`;
    }

    return shared.make_element("span", {"class": "attachment"}, [link, caption]);
}

//a messages text bubbles and attachments, in the order they came
function part_nodes(parts: PART[], from_customer: boolean): HTMLElement[] {
    const nodes: HTMLElement[] = [];

    for(const part of parts) {
        if(part.text) {
            nodes.push(shared.make_element("p", {"class": "bubble"}, [part.text]));
        }

        if(part.media) {
            nodes.push(media_node(part.media, from_customer));
        }
    }

    return nodes;
}

//false gets left out of the footer
function message_note(show: boolean | undefined, text: string): HTMLSpanElement | false {
    if(show) {
        return shared.make_element("span", {"class": "msg-note is-off"}, [text]);
    }

    return false;
}

//ghl texts came from a person, sms ones went out on the shops follow up line, not hazels line
function sender_note(from_ghl: boolean | undefined, sms: boolean | undefined): HTMLSpanElement | false {
    if(from_ghl) {
        return shared.make_element("span", {"class": "msg-note"}, ["Sent from GHL"]);
    }

    if(sms) {
        return shared.make_element("span", {"class": "msg-note is-sms"}, ["Follow up line"]);
    }

    return false;
}

//a note from the system between the messages, its words then its time
function event_node(class_name: string, text: string, time: HTMLTimeElement | false): HTMLParagraphElement {
    return shared.make_element("p", {"class": class_name}, [shared.make_element("span", {"class": "event-text"}, [text]), time]);
}

//one thread entry, a message in or out, or a note between them
function entry_node(entry: ENTRY): HTMLElement {
    const time: HTMLTimeElement = shared.make_element("time", {"datetime": new Date(entry.at).toISOString()}, [shared.local_time(entry.at)]);

    if(entry.kind === "in") {
        const footer: HTMLElement = shared.make_element("footer", {}, [time, message_note(entry.off, "System was off, not answered")]);

        const nodes: HTMLElement[] = part_nodes(entry.parts, true);

        nodes.push(footer);

        return shared.make_element("article", {"class": "msg is-in"}, nodes);
    }

    if(entry.kind === "out") {
        const footer: HTMLElement = shared.make_element("footer", {}, [sender_note(entry.ghl, entry.sms), message_note(entry.failed, "Not delivered"), time]);

        let class_name: string = "msg is-out";

        //texts off the follow up line show in green so they stand apart from hazels line
        if(entry.sms) {
            class_name = "msg is-out is-sms";
        }

        const nodes: HTMLElement[] = part_nodes(entry.parts, false);

        nodes.push(footer);

        return shared.make_element("article", {"class": class_name}, nodes);
    }

    if(entry.kind === "hil") {
        return event_node("event is-hil", `HIL: ${entry.reason}`, time);
    }

    if(entry.kind === "booked") {
        return event_node("event is-booked", `Booked HIL: ${entry.reason}`, time);
    }

    if(entry.kind === "switch") {
        if(entry.on) {
            return event_node("event", "System switched back on from the dashboard.", time);
        }

        //the owner texting them from ghl switches them off on its own
        if(entry.by === "ghl") {
            return event_node("event is-off", "System switched off: the owner texted them from GHL.", time);
        }

        return event_node("event is-off", "System switched off from the dashboard.", time);
    }

    if(entry.kind === "flag") {
        return event_node("event is-hil", `Flagged: ${entry.feedback}`, time);
    }

    if(entry.kind === "upvote") {
        return event_node("event is-upvote", UPWEIGHTED, time);
    }

    return event_node("event", "An entry this dashboard doesn't know how to show.", false);
}

//a day heading every time the viewers date changes, and an upvotes own line waits on its ring
function render_log(entries: ENTRY[]): void {
    const nodes: HTMLElement[] = [];

    let last_date: string = "";

    NEWEST_AT = 0;

    for(const entry of entries) {
        NEWEST_AT = Math.max(NEWEST_AT, entry.at);

        if(is_waiting(entry)) {
            continue;
        }

        const date: string = shared.local_date(entry.at);

        if(date !== last_date) {
            nodes.push(shared.make_element("h3", {"class": "day"}, [shared.day_label(date)]));

            last_date = date;
        }

        nodes.push(entry_node(entry));
    }

    if(nodes.length === 0) {
        nodes.push(shared.make_element("p", {"class": "log-note"}, ["Nothing is kept for this conversation anymore. Threads last a year after the last message."]));
    }

    LOG.replaceChildren();

    for(const node of nodes) {
        LOG.append(node);
    }

    //what the customer wrote gets the search hits marked
    mark_log();
}

//everything above the open thread, name, channel, switch, flag and the upvote ring
function render_head(convo: THREAD_CONVO): void {
    THREAD_HEAD.hidden = false;

    THREAD_NAME.textContent = convo_title(convo);

    let where: string | undefined = shared.CHANNEL_NAMES[convo.channel];

    if(where === undefined) {
        where = convo.channel;
    }

    let meta: string = where;

    if(convo.name) {
        meta = `${where}, ${shared.readable_id(convo.id)}`;
    }

    THREAD_META.textContent = meta;

    //whole channel off outranks there own switch, so it shows that and waits for the channel
    const channel_name: string = TAB_NAMES[convo.tab];

    SWITCH_BUTTON.disabled = convo.tab_off;

    SWITCH_BUTTON.setAttribute("aria-checked", String(!convo.off && !convo.tab_off));

    let switch_text: string = "System on";

    if(convo.tab_off) {
        switch_text = `${channel_name} off`;
    }
    else if(convo.off) {
        switch_text = "System off";
    }

    SWITCH_LABEL.textContent = switch_text;

    let switch_title: string = "";

    if(convo.tab_off) {
        switch_title = `System is off for all of ${channel_name}. Switch it back on at the top of the ${channel_name} list.`;
    }

    SWITCH_BUTTON.title = switch_title;

    FLAG_BUTTON.classList.toggle("is-flagged", convo.flagged_at > 0);

    let flag_title: string = "Flag this conversation";

    if(convo.flagged_at > 0) {
        flag_title = `Flagged ${shared.when_short(convo.flagged_at)}. Flag again`;
    }

    FLAG_BUTTON.title = flag_title;

    COMPOSE_FORM.hidden = convo.tab !== "forms";

    render_upvote();
}

//fresh means a newly opened convo, a refresh only scrolls down if they were near the bottom
async function load_thread(fresh: boolean): Promise<void> {
    if(!CURRENT_ID) {
        return;
    }

    const id: string = CURRENT_ID;

    PAGE.classList.add("show-thread");

    if(fresh) {
        THREAD_HEAD.hidden = true;

        LOG.replaceChildren(shared.make_element("p", {"class": "log-note"}, ["Loading messages…"]));
    }

    const near_bottom: boolean = LOG.scrollHeight - LOG.scrollTop - LOG.clientHeight < NEAR_BOTTOM_PX;

    try {
        const data: THREAD = await shared.ask_server<THREAD>(`/api/thread?id=${encodeURIComponent(id)}`);

        //another convo got picked while this one loaded
        if(id !== CURRENT_ID) {
            return;
        }

        CURRENT_CONVO = data.convo;

        render_head(data.convo);

        render_log(data.entries);

        const mark: HTMLElement | null = newest_mark();

        //a search result opens on the message it matched in, anything else on the newest message
        if(fresh && mark !== null) {
            center_in_log(mark);
        }
        else if(fresh || near_bottom) {
            LOG.scrollTop = LOG.scrollHeight;
        }
    }
    catch(error: unknown) {
        let message: string = "Couldn't load this conversation. It retries on its own.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        LOG.replaceChildren(shared.make_element("p", {"class": "log-note"}, [message]));
    }
}

//nothing open, the log just asks them to pick a conversation
function show_list(): void {
    PAGE.classList.remove("show-thread");

    THREAD_HEAD.hidden = true;

    COMPOSE_FORM.hidden = true;

    CURRENT_CONVO = null;

    LOG.replaceChildren(shared.make_element("p", {"class": "log-note"}, ["Pick a conversation to see every message in and every reply out."]));
}


//LIST

//the tabs convos split three ways, System on, Booked HILs and System off
function press_view(): void {
    for(const view of VIEWS) {
        VIEW_BUTTONS[view].button.setAttribute("aria-pressed", String(view === CURRENT_VIEW));
    }
}

//off means the system answers nobody on the tabs channels till its switched back on
function render_channel(): void {
    const name: string = TAB_NAMES[CURRENT_TAB];

    const off: boolean = OFF_TABS.has(CURRENT_TAB);

    CHANNEL_BAR.hidden = false;

    LIST_HEAD.hidden = false;

    CHANNEL_BAR.classList.toggle("is-off", off);

    CHANNEL_SWITCH.setAttribute("aria-checked", String(!off));

    CHANNEL_SWITCH.setAttribute("aria-label", `System replies on ${name}`);

    let label: string = "System on";

    if(off) {
        label = "System off";
    }

    CHANNEL_SWITCH_LABEL.textContent = label;

    for(const entry of TAB_BUTTONS) {
        entry[1].off_mark.hidden = !OFF_TABS.has(entry[0]);
    }
}

//what an empty search says, plus how many matched under the other two lists
function search_note(view_counts: Record<VIEW, number>): string {
    const elsewhere: string[] = [];

    for(const view of VIEWS) {
        if(view !== CURRENT_VIEW && view_counts[view] > 0) {
            elsewhere.push(`${view_counts[view]} under ${VIEW_NAMES[view]}`);
        }
    }

    if(elsewhere.length === 0) {
        return `Nothing on ${TAB_NAMES[CURRENT_TAB]} matches "${CURRENT_QUERY}".`;
    }

    return `Nothing under ${VIEW_NAMES[CURRENT_VIEW]} matches "${CURRENT_QUERY}", ${elsewhere.join(" and ")}.`;
}

//what an empty list says for the open view
function empty_note(view_counts: Record<VIEW, number>): string {
    if(CURRENT_QUERY !== "") {
        return search_note(view_counts);
    }

    const name: string = TAB_NAMES[CURRENT_TAB];

    if(CURRENT_VIEW === "booked") {
        return `No ${name} conversations have a Booked HIL yet. They move here once a customer asks to get on the schedule.`;
    }

    if(CURRENT_VIEW === "off") {
        return `No ${name} conversations are switched off.`;
    }

    if(view_counts.booked > 0 && view_counts.off > 0) {
        return `Every ${name} conversation is under Booked HILs or System off.`;
    }

    if(view_counts.booked > 0) {
        return `Every ${name} conversation has a Booked HIL. They're under Booked HILs.`;
    }

    if(view_counts.off > 0) {
        return `Every ${name} conversation is switched off. They're under System off.`;
    }

    return `No ${name} conversations yet. They show up here the moment a customer messages in.`;
}

//the clicked rows convo opens, and only that row gets marked current
function open_convo(id: string, button: HTMLButtonElement): void {
    CURRENT_ID = id;

    remember_place();

    for(const row of LIST.querySelectorAll(".convo")) {
        row.setAttribute("aria-current", String(row === button));
    }

    load_thread(true);
}

//is_new lights up a convo that got a new message since the last load
function convo_row(convo: CONVO, is_new: boolean): HTMLLIElement {
    let row_class: string = "convo";

    if(is_new) {
        row_class = "convo is-new";
    }

    let hits: string[] = [];

    if(convo.hits !== undefined) {
        hits = convo.hits;
    }

    const name: HTMLSpanElement = shared.make_element("span", {"class": "convo-name"}, marked(convo_title(convo), hits));

    const time: HTMLTimeElement = shared.make_element("time", {"datetime": new Date(convo.last_at).toISOString()}, [shared.when_short(convo.last_at)]);

    const top: HTMLSpanElement = shared.make_element("span", {"class": "convo-top"}, [name, time]);

    let preview_class: string = "convo-preview";

    let preview_text: string = convo.last_text;

    //only a search snippet gets marks, the plain preview can be the systems words and those never get searched
    let preview_hits: string[] = [];

    if(!preview_text) {
        preview_text = "Sent media";
    }

    if(convo.last_kind === "out") {
        preview_class = "convo-preview is-reply";

        preview_text = `System: ${convo.last_text}`;
    }

    //a search shows the message it matched in instead of the last one
    if(convo.snippet) {
        preview_class = "convo-preview";

        preview_text = convo.snippet;

        preview_hits = hits;
    }

    const preview: HTMLSpanElement = shared.make_element("span", {"class": preview_class}, marked(preview_text, preview_hits));

    //false gets left out
    let badges: HTMLSpanElement | false = false;

    if(convo.flagged_at > 0) {
        badges = shared.make_element("span", {"class": "convo-badges"}, [shared.make_element("span", {"class": "badge is-flagged"}, ["Flagged"])]);
    }

    const button: HTMLButtonElement = shared.make_element("button", {"type": "button", "class": row_class, "data-id": convo.id, "aria-current": String(convo.id === CURRENT_ID)}, [top, preview, badges]);

    //each row opens its own convo
    function open_row(): void {
        open_convo(convo.id, button);
    }

    button.addEventListener("click", open_row);

    return shared.make_element("li", {}, [button]);
}

//append is for Show older, anything else rebuilds the list
async function load_list(append: boolean = false): Promise<void> {
    //a search breathes its own glass, so the loading note is only for the plain list
    if(CURRENT_QUERY !== "") {
        SEARCH_FORM.classList.add("is-busy");
    }
    else if(!append && SHOWN_CONVOS.length === 0) {
        LIST_NOTE.textContent = "Loading conversations…";

        LIST_NOTE.hidden = false;
    }

    try {
        //a refresh asks for everything on screen, so a list grown past 50 stays that long
        let paging: string = `limit=${Math.max(50, SHOWN_CONVOS.length)}`;

        if(append) {
            paging = `start=${SHOWN_CONVOS.length}`;
        }

        //only sent with a search, the plain list asks the same as always
        if(CURRENT_QUERY !== "") {
            paging = `${paging}&q=${encodeURIComponent(CURRENT_QUERY)}`;
        }

        const data: CONVO_PAGE = await shared.ask_server<CONVO_PAGE>(`/api/convos?tab=${CURRENT_TAB}&view=${CURRENT_VIEW}&${paging}`);

        //another tab, view or search got picked while this one loaded
        if(data.tab !== CURRENT_TAB || data.view !== CURRENT_VIEW || data.query !== CURRENT_QUERY) {
            return;
        }

        SEARCH_FORM.classList.remove("is-busy");

        for(const entry of TAB_BUTTONS) {
            let count: number = data.counts[entry[0]];

            if(count === undefined || count === null) {
                count = 0;
            }

            entry[1].count.textContent = String(count);
        }

        for(const view of VIEWS) {
            let count: number = data.view_counts[view];

            if(count === undefined || count === null) {
                count = 0;
            }

            VIEW_BUTTONS[view].count.textContent = String(count);
        }

        OFF_TABS = new Set<TAB>(data.off_tabs);

        render_channel();

        const last_seen: Map<string, number> = new Map<string, number>();

        for(const convo of SHOWN_CONVOS) {
            last_seen.set(convo.id, convo.last_at);
        }

        let focused_id: string | undefined = undefined;

        if(document.activeElement instanceof HTMLElement) {
            focused_id = document.activeElement.dataset.id;
        }

        if(append) {
            SHOWN_CONVOS = SHOWN_CONVOS.concat(data.convos);
        }
        else {
            SHOWN_CONVOS = data.convos;
        }

        if(!append) {
            LIST.replaceChildren();
        }

        for(const convo of data.convos) {
            const seen: number | undefined = last_seen.get(convo.id);

            const is_new: boolean = !append && seen !== undefined && convo.last_at > seen;

            LIST.append(convo_row(convo, is_new));
        }

        if(!append) {
            HITS.clear();
        }

        for(const convo of data.convos) {
            if(convo.hits !== undefined) {
                HITS.set(convo.id, convo.hits);
            }
        }

        //the open thread only gets redone when its marks changed
        if(open_hits().join(" ") !== LOG_MARKS) {
            mark_log();
        }

        //a refresh rebuilds the rows, so the one that had focus gets it back
        if(focused_id) {
            const focused_row: HTMLButtonElement | null = LIST.querySelector<HTMLButtonElement>(`.convo[data-id="${CSS.escape(focused_id)}"]`);

            if(focused_row !== null) {
                focused_row.focus();
            }
        }

        LIST_NOTE.textContent = empty_note(data.view_counts);

        LIST_NOTE.hidden = SHOWN_CONVOS.length > 0;

        MORE_BUTTON.hidden = !data.more;

        let more_text: string = "Show older conversations";

        if(CURRENT_QUERY !== "") {
            more_text = "Show more matches";
        }

        MORE_BUTTON.textContent = more_text;
    }
    catch(error: unknown) {
        SEARCH_FORM.classList.remove("is-busy");

        let message: string = "Couldn't load conversations. It retries on its own.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        LIST_NOTE.textContent = message;

        LIST_NOTE.hidden = false;
    }
}


//PICKING

//switching tabs starts over, nothing open and the list loads fresh
function pick_tab(tab: TAB): void {
    if(tab === CURRENT_TAB) {
        return;
    }

    CURRENT_TAB = tab;

    //every channel opens on the convos the system answers
    CURRENT_VIEW = "on";

    CURRENT_ID = "";

    SHOWN_CONVOS = [];

    remember_place();

    show_list();

    for(const entry of TAB_BUTTONS) {
        entry[1].button.setAttribute("aria-pressed", String(entry[0] === tab));
    }

    press_view();

    render_channel();

    load_list();
}

//red dot on a channel thats switched off, so it shows from every tab
function build_tab(tab: TAB): void {
    const count: HTMLSpanElement = shared.make_element("span", {"class": "tab-count"}, [""]);

    const off_mark: HTMLSpanElement = shared.make_element("span", {"class": "tab-off", "hidden": true}, [shared.make_element("span", {"class": "visually-hidden"}, ["System off"])]);

    const button: HTMLButtonElement = shared.make_element("button", {"type": "button", "class": "tab", "aria-pressed": String(tab === CURRENT_TAB)}, [TAB_NAMES[tab], off_mark, count]);

    //each tab button picks its own tab
    function pick_this_tab(): void {
        pick_tab(tab);
    }

    button.addEventListener("click", pick_this_tab);

    TAB_BUTTONS.set(tab, {"button": button, "count": count, "off_mark": off_mark});

    TABS_NAV.append(button);
}

//switching between System on, Booked HILs and System off reloads the list from the top
function pick_view(view: VIEW): void {
    if(view === CURRENT_VIEW) {
        return;
    }

    CURRENT_VIEW = view;

    SHOWN_CONVOS = [];

    remember_place();

    press_view();

    load_list();
}

//the Show older button, the next page goes under whats their
function show_more(): void {
    load_list(true);
}

//the back button, the thread closes and no row stays marked
function go_back(): void {
    CURRENT_ID = "";

    remember_place();

    show_list();

    for(const row of LIST.querySelectorAll(".convo")) {
        row.setAttribute("aria-current", "false");
    }
}


//SEARCH

//the wait is over or enter got pressed, the list starts over from the top for whats in the box now
function run_search(): void {
    window.clearTimeout(SEARCH_TIMER);

    const query: string = SEARCH_TEXT.value.trim();

    if(query === CURRENT_QUERY) {
        return;
    }

    CURRENT_QUERY = query;

    SHOWN_CONVOS = [];

    remember_place();

    LIST_PANE.scrollTop = 0;

    load_list();
}

//each key waits a moment for the next one, an emptied box brings the plain list back right away
function wait_search(): void {
    window.clearTimeout(SEARCH_TIMER);

    SEARCH_CLEAR.hidden = SEARCH_TEXT.value === "";

    if(SEARCH_TEXT.value.trim() === "") {
        run_search();
    }
    else {
        SEARCH_TIMER = window.setTimeout(run_search, SEARCH_WAIT_MS);
    }
}

//enter searches right away and puts a phones keyboard away so the results show
function submit_search(event: SubmitEvent): void {
    event.preventDefault();

    run_search();

    SEARCH_TEXT.blur();
}

//the x empties the box and leaves it ready for the next search
function clear_search(): void {
    SEARCH_TEXT.value = "";

    SEARCH_CLEAR.hidden = true;

    run_search();

    SEARCH_TEXT.focus();
}

//escape empties the box, or leaves it when its already empty
function search_keys(event: KeyboardEvent): void {
    if(event.key !== "Escape") {
        return;
    }

    event.preventDefault();

    if(SEARCH_TEXT.value !== "") {
        clear_search();
    }
    else {
        SEARCH_TEXT.blur();
    }
}


//SWITCHES

//just this customer
async function flip_switch(): Promise<void> {
    if(CURRENT_CONVO === null) {
        return;
    }

    const convo: THREAD_CONVO = CURRENT_CONVO;

    const on: boolean = convo.off;

    SWITCH_BUTTON.disabled = true;

    try {
        await shared.ask_server("/api/switch", "POST", {"id": convo.id, "on": on});

        convo.off = !on;

        render_head(convo);

        let message: string = `System switched off for ${convo_title(convo)}. Nothing goes out to them now,`;

        let ending: string = "and they're under System off.";

        if(on) {
            message = `System switched on for ${convo_title(convo)}. It answers their next message,`;

            ending = "and they're back under System on.";
        }

        //a booked one doesn't budge, whichever way its switch went
        if(convo.booked) {
            ending = "and they stay under Booked HILs.";
        }

        shared.toast(`${message} ${ending}`);

        load_thread(false);

        load_list();
    }
    catch(error: unknown) {
        let message: string = "The switch didn't change. Try again.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        shared.toast(message, true);
    }
    finally {
        //stays off while the whole channel is off
        let disabled: boolean = false;

        if(CURRENT_CONVO !== null) {
            disabled = CURRENT_CONVO.tab_off;
        }

        SWITCH_BUTTON.disabled = disabled;
    }
}

//everyone on the open tabs channels
async function flip_channel(): Promise<void> {
    const tab: TAB = CURRENT_TAB;

    const name: string = TAB_NAMES[tab];

    const on: boolean = OFF_TABS.has(tab);

    CHANNEL_SWITCH.disabled = true;

    try {
        await shared.ask_server("/api/switch", "POST", {"tab": tab, "on": on});

        if(on) {
            OFF_TABS.delete(tab);
        }
        else {
            OFF_TABS.add(tab);
        }

        render_channel();

        let message: string = `System switched off for all of ${name}. Nothing goes out there now.`;

        if(on) {
            message = `System switched on for ${name}. It answers the next message that comes in there.`;
        }

        shared.toast(message);

        load_list();

        load_thread(false);
    }
    catch(error: unknown) {
        let message: string = "The switch didn't change. Try again.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        shared.toast(message, true);
    }
    finally {
        CHANNEL_SWITCH.disabled = false;
    }
}


//DELETE

//the delete box spells out what goes before anything does
function open_trash(): void {
    if(CURRENT_CONVO === null) {
        return;
    }

    TRASH_NOTE.textContent = `Every message, reply, pic and follow up kept for ${convo_title(CURRENT_CONVO)} comes off the dashboard for good, and the Overview's numbers drop by what this conversation added. Their switch stays as it is, and a new message from them starts a new conversation.`;

    TRASH_ERROR.hidden = true;

    TRASH_DIALOG.showModal();
}

//changed there mind, nothing gets deleted
function close_trash(): void {
    TRASH_DIALOG.close();
}

//deletes the open conversation for good, then its back to the list
async function send_trash(event: SubmitEvent): Promise<void> {
    event.preventDefault();

    if(CURRENT_CONVO === null) {
        return;
    }

    const convo: THREAD_CONVO = CURRENT_CONVO;

    TRASH_CONFIRM.disabled = true;

    try {
        await shared.ask_server(`/api/thread?id=${encodeURIComponent(convo.id)}`, "DELETE");

        TRASH_DIALOG.close();

        shared.toast(`Deleted the conversation with ${convo_title(convo)}.`);

        CURRENT_ID = "";

        remember_place();

        show_list();

        load_list();
    }
    catch(error: unknown) {
        let message: string = "It didn't delete. Check your connection and try again.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        TRASH_ERROR.textContent = message;

        TRASH_ERROR.hidden = false;
    }
    finally {
        TRASH_CONFIRM.disabled = false;
    }
}


//FLAG

//the flag box opens empty every time
function open_flag(): void {
    if(CURRENT_CONVO === null) {
        return;
    }

    FLAG_ERROR.hidden = true;

    FLAG_TEXT.value = "";

    FLAG_DIALOG.showModal();
}

//no flag after all, the box just closes
function close_flag(): void {
    FLAG_DIALOG.close();
}

//sends what went wrong, and the toast says who it went to
async function send_flag(event: SubmitEvent): Promise<void> {
    event.preventDefault();

    if(CURRENT_CONVO === null) {
        return;
    }

    const feedback: string = FLAG_TEXT.value.trim();

    if(feedback === "") {
        FLAG_ERROR.textContent = "Write what went wrong first.";

        FLAG_ERROR.hidden = false;

        return;
    }

    FLAG_SEND.disabled = true;

    FLAG_SEND.textContent = "Sending…";

    try {
        const result: FLAG_RESULT = await shared.ask_server<FLAG_RESULT>("/api/flag", "POST", {"id": CURRENT_CONVO.id, "feedback": feedback});

        FLAG_DIALOG.close();

        shared.toast(`Flag sent to ${result.sent_to}.`);

        load_thread(false);

        load_list();
    }
    catch(error: unknown) {
        let message: string = "The flag didn't send. Check your connection and try again.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        FLAG_ERROR.textContent = message;

        FLAG_ERROR.hidden = false;
    }
    finally {
        FLAG_SEND.disabled = false;

        FLAG_SEND.textContent = "Send flag";
    }
}


//UPVOTE

//how much of the ring is filled, from how long the stage its on has been going
function upvote_fill(upvote: UPVOTE, now: number): number {
    if(upvote.stage === "writing") {
        return WRITING_FILL * (1 - Math.exp((upvote.sent_at - now) / WRITING_PACE_MS));
    }

    if(upvote.stage === "deploying") {
        return WRITING_FILL + (DEPLOYING_FILL - WRITING_FILL) * (1 - Math.exp((upvote.pushed_at - now) / DEPLOYING_PACE_MS));
    }

    return 1;
}

//the ring only shows on its own convo, filled by time so a reload picks up where it was
function render_upvote(): void {
    let stage: UPVOTE_STAGE = "idle";

    let fill: number = 0;

    if(CURRENT_UPVOTE !== null && CURRENT_UPVOTE.id === CURRENT_ID) {
        stage = CURRENT_UPVOTE.stage;

        fill = upvote_fill(CURRENT_UPVOTE, Date.now());
    }

    UPVOTE_BUTTON.dataset.stage = stage;

    UPVOTE_BUTTON.style.setProperty("--fill", String(fill));

    UPVOTE_BUTTON.title = UPVOTE_TITLES[stage];

    const going: boolean = stage === "writing" || stage === "deploying";

    if(going && UPVOTE_TICKER === 0) {
        UPVOTE_TICKER = window.setInterval(render_upvote, UPVOTE_TICK_MS);
    }
    else if(!going && UPVOTE_TICKER !== 0) {
        window.clearInterval(UPVOTE_TICKER);

        UPVOTE_TICKER = 0;
    }
}

//an upvotes own line stays out of the log till its ring fills
function is_waiting(entry: ENTRY): boolean {
    if(entry.kind !== "upvote" || CURRENT_UPVOTE === null || CURRENT_UPVOTE.logged) {
        return false;
    }

    return CURRENT_UPVOTE.id === CURRENT_ID && entry.at > CURRENT_UPVOTE.after;
}

//the upvote box opens empty, unless one is still going
function open_upvote(): void {
    if(CURRENT_CONVO === null) {
        return;
    }

    //one at a time, a second push would land while render is still deploying the first
    if(CURRENT_UPVOTE !== null && (CURRENT_UPVOTE.stage === "writing" || CURRENT_UPVOTE.stage === "deploying")) {
        shared.toast("Still up-weighting the last one. This one can go once its ring fills.");

        return;
    }

    UPVOTE_ERROR.hidden = true;

    UPVOTE_TEXT.value = "";

    UPVOTE_DIALOG.showModal();
}

//second thoughts, no upvote goes out
function close_upvote(): void {
    UPVOTE_DIALOG.close();
}

//the box closes right away, and the ring around the arrow shows the rest
async function send_upvote(event: SubmitEvent): Promise<void> {
    event.preventDefault();

    if(CURRENT_CONVO === null) {
        return;
    }

    const reason: string = UPVOTE_TEXT.value.trim();

    if(reason === "") {
        UPVOTE_ERROR.textContent = "Write a reason first.";

        UPVOTE_ERROR.hidden = false;

        return;
    }

    const upvote: UPVOTE = {"id": CURRENT_CONVO.id, "name": convo_title(CURRENT_CONVO), "stage": "writing", "sent_at": Date.now(), "commit": "", "pushed_at": 0, "after": NEWEST_AT, "logged": false};

    CURRENT_UPVOTE = upvote;

    UPVOTE_DIALOG.close();

    render_upvote();

    try {
        const result: UPVOTE_RESULT = await shared.ask_server<UPVOTE_RESULT>("/api/upvote", "POST", {"id": upvote.id, "reason": reason});

        upvote.stage = "deploying";

        upvote.commit = result.commit;

        upvote.pushed_at = Date.now();

        save_upvote(upvote);

        render_upvote();

        check_upvote(upvote);
    }
    catch(error: unknown) {
        let message: string = "The up-weight didn't go through. Check your connection.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        fail_upvote(upvote, message);
    }
}

//asks every 15s whether the system is running the push yet, till it is or the wait runs out
async function check_upvote(upvote: UPVOTE): Promise<void> {
    try {
        const live: LIVE_RESULT = await shared.ask_server<LIVE_RESULT>(`/api/upvote?commit=${upvote.commit}`);

        if(live.live) {
            fill_upvote(upvote);

            return;
        }
    }
    catch {
        //missed one, the next check tries again
    }

    if(Date.now() - upvote.pushed_at > UPVOTE_WAIT_MS) {
        fail_upvote(upvote, "The example got pushed, but the system still isn't running it after 15 minutes. Check its deploy on Render.");

        return;
    }

    window.setTimeout(check_upvote, UPVOTE_CHECK_MS, upvote);
}

//the system runs it, so the ring closes all the way, and only then does the conversation log it
function fill_upvote(upvote: UPVOTE): void {
    upvote.stage = "done";

    forget_upvote();

    render_upvote();

    window.setTimeout(log_upvote, UPVOTE_FILL_MS, upvote);
}

//its line goes in the open thread, or a toast from anywhere else, then the arrow resets
async function log_upvote(upvote: UPVOTE): Promise<void> {
    upvote.logged = true;

    window.setTimeout(clear_upvote, UPVOTE_HOLD_MS, upvote);

    if(upvote.id !== CURRENT_ID) {
        shared.toast(`Response up-weighted for ${upvote.name}.`);

        return;
    }

    await load_thread(false);

    //another convo got picked while it loaded
    if(upvote.id !== CURRENT_ID) {
        return;
    }

    const lines: NodeListOf<HTMLElement> = LOG.querySelectorAll<HTMLElement>(".event.is-upvote");

    const last_line: HTMLElement | undefined = lines[lines.length - 1];

    if(last_line !== undefined) {
        last_line.classList.add("is-arriving");
    }
}

//the ring goes red while the toast says what broke, then clears
function fail_upvote(upvote: UPVOTE, message: string): void {
    upvote.stage = "failed";

    forget_upvote();

    render_upvote();

    shared.toast(message, true);

    window.setTimeout(clear_upvote, UPVOTE_RED_MS, upvote);
}

//the arrow goes back to how it was
function clear_upvote(upvote: UPVOTE): void {
    //a newer upvote already took its place
    if(CURRENT_UPVOTE !== upvote) {
        return;
    }

    CURRENT_UPVOTE = null;

    render_upvote();

    //a push that went out but never went live still gets its line
    if(!upvote.logged && upvote.id === CURRENT_ID) {
        load_thread(false);
    }
}

//kept in the tabs storage so a reload can pick the ring back up
function save_upvote(upvote: UPVOTE): void {
    try {
        sessionStorage.setItem(UPVOTE_KEY, JSON.stringify(upvote));
    }
    catch {
        //storage is off, the ring just won't make it through a reload
    }
}

//nothing left for a reload to pick back up
function forget_upvote(): void {
    try {
        sessionStorage.removeItem(UPVOTE_KEY);
    }
    catch {
        //storage is off, so nothing was kept
    }
}

//null when nothings kept or it isn't a deploying upvote this page wrote
function saved_upvote(): UPVOTE | null {
    let saved: unknown = null;

    try {
        let kept: string | null = sessionStorage.getItem(UPVOTE_KEY);

        if(kept === null) {
            kept = "null";
        }

        saved = JSON.parse(kept);
    }
    catch {
        return null;
    }

    if(saved === null || typeof saved !== "object") {
        return null;
    }

    const fields: Record<string, unknown> = saved as Record<string, unknown>;

    if(typeof fields.id !== "string" || typeof fields.name !== "string" || fields.stage !== "deploying" || typeof fields.sent_at !== "number" || typeof fields.commit !== "string" || !COMMIT_SHA.test(fields.commit) || typeof fields.pushed_at !== "number" || typeof fields.after !== "number") {
        return null;
    }

    return {"id": fields.id, "name": fields.name, "stage": "deploying", "sent_at": fields.sent_at, "commit": fields.commit, "pushed_at": fields.pushed_at, "after": fields.after, "logged": false};
}

//a reload mid deploy picks the checks back up, the ring still fills and its line still waits
function resume_upvote(): void {
    const upvote: UPVOTE | null = saved_upvote();

    if(upvote === null) {
        forget_upvote();

        return;
    }

    CURRENT_UPVOTE = upvote;

    check_upvote(upvote);
}


//COMPOSE

//a text out from the dashboard, the thread and list reload either way
async function send_text(event: SubmitEvent): Promise<void> {
    event.preventDefault();

    const text: string = COMPOSE_TEXT.value.trim();

    if(CURRENT_CONVO === null || text === "" || COMPOSE_SEND.disabled) {
        return;
    }

    COMPOSE_SEND.disabled = true;

    COMPOSE_SEND.textContent = "Sending…";

    try {
        await shared.ask_server("/api/send", "POST", {"id": CURRENT_CONVO.id, "text": text});

        COMPOSE_TEXT.value = "";

        fit_compose();
    }
    catch(error: unknown) {
        let message: string = "The text didn't send. Check your connection and try again.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        shared.toast(message);
    }
    finally {
        COMPOSE_SEND.disabled = false;

        COMPOSE_SEND.textContent = "Send";

        LOG.scrollTop = LOG.scrollHeight;

        load_thread(false);

        load_list();
    }
}

//enter sends, shift enter starts a new line
function send_on_enter(event: KeyboardEvent): void {
    if(event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();

        COMPOSE_FORM.requestSubmit();
    }
}

//the box grows with whats typed till it hits its max height, then scrolls
function fit_compose(): void {
    COMPOSE_TEXT.style.height = "auto";

    COMPOSE_TEXT.style.height = `${COMPOSE_TEXT.scrollHeight + COMPOSE_TEXT.offsetHeight - COMPOSE_TEXT.clientHeight}px`;
}


//PULSE

//something changed in the feed, so the list and the open thread reload
function refresh(): void {
    load_list();

    load_thread(false);
}


//START

//tab, view and convo come from the address
if(is_tab(ADDRESS_TAB)) {
    CURRENT_TAB = ADDRESS_TAB;
}

const address_view: string | null = ADDRESS.get("view");

if(address_view === "booked" || address_view === "off") {
    CURRENT_VIEW = address_view;
}

let address_id: string | null = ADDRESS.get("id");

if(address_id === null) {
    address_id = "";
}

CURRENT_ID = address_id;

//a search in the address comes back in the box
let address_query: string | null = ADDRESS.get("q");

if(address_query === null) {
    address_query = "";
}

SEARCH_TEXT.value = address_query;

SEARCH_CLEAR.hidden = address_query === "";

CURRENT_QUERY = address_query.trim();

for(const tab of TABS) {
    build_tab(tab);
}

for(const view of VIEWS) {
    //each view button picks its own view
    function pick_this_view(): void {
        pick_view(view);
    }

    VIEW_BUTTONS[view].button.addEventListener("click", pick_this_view);
}

press_view();

MORE_BUTTON.addEventListener("click", show_more);

BACK_BUTTON.addEventListener("click", go_back);

SWITCH_BUTTON.addEventListener("click", flip_switch);

CHANNEL_SWITCH.addEventListener("click", flip_channel);

TRASH_BUTTON.addEventListener("click", open_trash);

TRASH_CANCEL.addEventListener("click", close_trash);

TRASH_FORM.addEventListener("submit", send_trash);

FLAG_BUTTON.addEventListener("click", open_flag);

FLAG_CANCEL.addEventListener("click", close_flag);

FLAG_FORM.addEventListener("submit", send_flag);

UPVOTE_BUTTON.addEventListener("click", open_upvote);

UPVOTE_CANCEL.addEventListener("click", close_upvote);

UPVOTE_FORM.addEventListener("submit", send_upvote);

COMPOSE_FORM.addEventListener("submit", send_text);

COMPOSE_TEXT.addEventListener("keydown", send_on_enter);

COMPOSE_TEXT.addEventListener("input", fit_compose);

SEARCH_FORM.addEventListener("submit", submit_search);

SEARCH_TEXT.addEventListener("input", wait_search);

SEARCH_TEXT.addEventListener("keydown", search_keys);

SEARCH_CLEAR.addEventListener("click", clear_search);

//a reload mid upvote picks its ring back up first, so its line keeps waiting in the first draw
resume_upvote();

remember_place();

load_list();

if(CURRENT_ID) {
    load_thread(true);
}
else {
    show_list();
}

shared.on_pulse(refresh);
