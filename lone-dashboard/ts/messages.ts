//**********IMPORTS**********
//the api call, page helpers and formats every page shares
import * as shared from "./shared.js";



//**********GLOBALS**********
//shapes from api/convos.ts and api/thread.ts, the page's parts and what's open


//TAB
type TAB = "forms" | "instagram" | "messenger";


//VIEW
//each tab splits into the convos the system answers and the ones switched off
type VIEW = "on" | "off";


//CONVO
type CONVO = {id: string; tab: TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string; off: boolean; flagged_at: number};


//THREAD CONVO
//same convo plus whether its whole channel is switched off
type THREAD_CONVO = {id: string; tab: TAB; channel: string; name: string; last_at: number; last_kind: "in" | "out"; last_text: string; off: boolean; tab_off: boolean; flagged_at: number};


//MEDIA
type MEDIA = {kind: "pic"; id: string; width?: number; height?: number; caption: string} | {kind: "video" | "link"; url: string; caption: string} | {kind: "post"; caption: string};


//PART
type PART = {text?: string; media?: MEDIA};


//ENTRY
type ENTRY = {at: number; kind: "in"; parts: PART[]; off?: boolean} | {at: number; kind: "out"; parts: PART[]; failed?: boolean; ghl?: boolean; sms?: boolean} | {at: number; kind: "hil" | "booked"; reason: string} | {at: number; kind: "switch"; on: boolean; by?: "ghl"} | {at: number; kind: "flag"; feedback: string};


//CONVO PAGE
type CONVO_PAGE = {tab: TAB; view: VIEW; counts: Record<TAB, number>; view_counts: Record<VIEW, number>; off_tabs: TAB[]; more: boolean; convos: CONVO[]};


//THREAD
type THREAD = {convo: THREAD_CONVO; entries: ENTRY[]};


//FLAG RESULT
type FLAG_RESULT = {ok: boolean; sent_to: string; flagged_at: number};


//TAB PARTS
type TAB_PARTS = {button: HTMLButtonElement; count: HTMLSpanElement; off_mark: HTMLSpanElement};


//VIEW PARTS
type VIEW_PARTS = {button: HTMLButtonElement; count: HTMLSpanElement};


//TABS
const TABS: TAB[] = ["forms", "instagram", "messenger"];

const TAB_NAMES: Record<TAB, string> = {"forms": "Forms", "instagram": "Instagram", "messenger": "Messenger"};


//VIEWS
const VIEWS: VIEW[] = ["on", "off"];


//WEB LINK
//only web links get linked, so a customer can't slip a script link in
const WEB_LINK: RegExp = /^https?:\/\//i;


//NEAR BOTTOM
//within this many px of the bottom, a refresh keeps the thread scrolled down
const NEAR_BOTTOM_PX: number = 80;


//LIST PARTS
const PAGE: HTMLElement = shared.by_id<HTMLElement>("messages");

const TABS_NAV: HTMLElement = shared.by_id<HTMLElement>("tabs");

const LIST: HTMLUListElement = shared.by_id<HTMLUListElement>("convos");

const LIST_NOTE: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("list-note");

const MORE_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("more");


//THREAD PARTS
const THREAD_HEAD: HTMLElement = shared.by_id<HTMLElement>("thread-head");

const THREAD_NAME: HTMLHeadingElement = shared.by_id<HTMLHeadingElement>("thread-name");

const THREAD_META: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("thread-meta");

const SWITCH_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("switch");

const SWITCH_LABEL: HTMLSpanElement = shared.by_id<HTMLSpanElement>("switch-label");

const FLAG_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("flag");


//CHANNEL PARTS
const CHANNEL_BAR: HTMLElement = shared.by_id<HTMLElement>("channel-bar");

const CHANNEL_SWITCH: HTMLButtonElement = shared.by_id<HTMLButtonElement>("channel-switch");

const CHANNEL_SWITCH_LABEL: HTMLSpanElement = shared.by_id<HTMLSpanElement>("channel-switch-label");

const LIST_HEAD: HTMLElement = shared.by_id<HTMLElement>("list-head");


//VIEW BUTTONS
const VIEW_ON_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("view-on");

const VIEW_ON_COUNT: HTMLSpanElement = shared.by_id<HTMLSpanElement>("view-on-count");

const VIEW_OFF_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("view-off");

const VIEW_OFF_COUNT: HTMLSpanElement = shared.by_id<HTMLSpanElement>("view-off-count");

const VIEW_BUTTONS: Record<VIEW, VIEW_PARTS> = {"on": {"button": VIEW_ON_BUTTON, "count": VIEW_ON_COUNT}, "off": {"button": VIEW_OFF_BUTTON, "count": VIEW_OFF_COUNT}};


//LOG
const LOG: HTMLElement = shared.by_id<HTMLElement>("log");

const BACK_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("back");


//COMPOSE PARTS
//texts out from the dashboard go on the blooio line, so only the forms tab gets the box
const COMPOSE_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("compose");

const COMPOSE_TEXT: HTMLTextAreaElement = shared.by_id<HTMLTextAreaElement>("compose-text");

const COMPOSE_SEND: HTMLButtonElement = shared.by_id<HTMLButtonElement>("compose-send");


//FLAG PARTS
const FLAG_DIALOG: HTMLDialogElement = shared.by_id<HTMLDialogElement>("flag-dialog");

const FLAG_TEXT: HTMLTextAreaElement = shared.by_id<HTMLTextAreaElement>("flag-text");

const FLAG_ERROR: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("flag-error");

const FLAG_SEND: HTMLButtonElement = shared.by_id<HTMLButtonElement>("flag-send");

const FLAG_CANCEL: HTMLButtonElement = shared.by_id<HTMLButtonElement>("flag-cancel");

const FLAG_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("flag-form");


//TRASH PARTS
const TRASH_BUTTON: HTMLButtonElement = shared.by_id<HTMLButtonElement>("trash");

const TRASH_DIALOG: HTMLDialogElement = shared.by_id<HTMLDialogElement>("trash-dialog");

const TRASH_NOTE: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("trash-note");

const TRASH_ERROR: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("trash-error");

const TRASH_CONFIRM: HTMLButtonElement = shared.by_id<HTMLButtonElement>("trash-confirm");

const TRASH_CANCEL: HTMLButtonElement = shared.by_id<HTMLButtonElement>("trash-cancel");

const TRASH_FORM: HTMLFormElement = shared.by_id<HTMLFormElement>("trash-form");


//ADDRESS
const ADDRESS: URLSearchParams = new URLSearchParams(location.search);

const ADDRESS_TAB: string | null = ADDRESS.get("tab");


//TAB BUTTONS
//built once in START, so a refresh never pulls focus off the one being used
const TAB_BUTTONS: Map<TAB, TAB_PARTS> = new Map<TAB, TAB_PARTS>();


//PAGE STATE
//tab, view and id get set from the address in START
let CURRENT_TAB: TAB = "forms";

let CURRENT_VIEW: VIEW = "on";

let CURRENT_ID: string = "";

let SHOWN_CONVOS: CONVO[] = [];

let CURRENT_CONVO: THREAD_CONVO | null = null;

//tabs with their whole channel switched off, as of the last list load
let OFF_TABS: Set<TAB> = new Set<TAB>();



//**********PLACE**********
//which tab, view and convo is open, kept in the address


//IS TAB
function is_tab(value: string | null): value is TAB {
    for(const tab of TABS) {
        if(tab === value) {
            return true;
        }
    }

    return false;
}


//CONVO TITLE
function convo_title(convo: CONVO | THREAD_CONVO): string {
    return convo.name || shared.readable_id(convo.id);
}


//REMEMBER PLACE
//so a reload or a link from a flag email opens the same place
function remember_place(): void {
    const query: URLSearchParams = new URLSearchParams({"tab": CURRENT_TAB});

    if(CURRENT_VIEW === "off") {
        query.set("view", "off");
    }

    if(CURRENT_ID) {
        query.set("id", CURRENT_ID);
    }

    history.replaceState(null, "", `/messages?${query}`);
}



//**********THREAD**********
//every message in and reply out for the open convo


//GONE PIC
//copies only last 30 days
function show_gone_pic(image: HTMLImageElement): void {
    image.replaceWith(shared.make_element("span", {"class": "attachment is-gone"}, "Pic no longer kept. Copies last 30 days."));
}


//MEDIA NODE
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

        image.addEventListener("error", (): void => { show_gone_pic(image); });

        return shared.make_element("a", {"class": "pic", "href": src, "target": "_blank", "rel": "noopener"}, image);
    }

    if(media.kind === "post") {
        return shared.make_element("span", {"class": "attachment"}, media.caption || "Shared post");
    }

    let label: string = "Attachment";

    if(media.kind === "video") {
        label = "Video";
    }

    let link: HTMLAnchorElement | string = label;

    if(WEB_LINK.test(media.url)) {
        link = shared.make_element("a", {"href": media.url, "target": "_blank", "rel": "noopener noreferrer"}, label);
    }

    //empty caption gets left out
    let caption: string = "";

    if(media.caption) {
        caption = ` ${media.caption}`;
    }

    return shared.make_element("span", {"class": "attachment"}, link, caption);
}


//PART NODES
function part_nodes(parts: PART[], from_customer: boolean): HTMLElement[] {
    const nodes: HTMLElement[] = [];

    for(const part of parts) {
        if(part.text) {
            nodes.push(shared.make_element("p", {"class": "bubble"}, part.text));
        }

        if(part.media) {
            nodes.push(media_node(part.media, from_customer));
        }
    }

    return nodes;
}


//MESSAGE NOTE
//false gets left out of the footer
function message_note(show: boolean | undefined, text: string): HTMLSpanElement | false {
    if(show) {
        return shared.make_element("span", {"class": "msg-note is-off"}, text);
    }

    return false;
}


//SENDER NOTE
//a text sent from ghl was a person, not the system, and an sms follow up went out from the shop's ghl number instead of hazel's line, false gets left out of the footer
function sender_note(from_ghl: boolean | undefined, sms: boolean | undefined): HTMLSpanElement | false {
    if(from_ghl) {
        return shared.make_element("span", {"class": "msg-note"}, "Sent from GHL");
    }

    if(sms) {
        return shared.make_element("span", {"class": "msg-note is-sms"}, "SMS follow up");
    }

    return false;
}



//ENTRY NODE
function entry_node(entry: ENTRY): HTMLElement {
    const time: HTMLTimeElement = shared.make_element("time", {"datetime": new Date(entry.at).toISOString()}, shared.shop_parts(entry.at).time);

    if(entry.kind === "in") {
        const footer: HTMLElement = shared.make_element("footer", {}, time, message_note(entry.off, "System was off, not answered"));

        return shared.make_element("article", {"class": "msg is-in"}, ...part_nodes(entry.parts, true), footer);
    }

    if(entry.kind === "out") {
        const footer: HTMLElement = shared.make_element("footer", {}, sender_note(entry.ghl, entry.sms), message_note(entry.failed, "Not delivered"), time);

        let class_name: string = "msg is-out";

        //sms follow ups show in green so they stand apart from hazel's texts
        if(entry.sms) {
            class_name = "msg is-out is-sms";
        }

        return shared.make_element("article", {"class": class_name}, ...part_nodes(entry.parts, false), footer);
    }

    if(entry.kind === "hil") {
        return shared.make_element("p", {"class": "event is-hil"}, `HIL: ${entry.reason}`, time);
    }

    if(entry.kind === "booked") {
        return shared.make_element("p", {"class": "event is-booked"}, `Booked HIL: ${entry.reason}`, time);
    }

    if(entry.kind === "switch") {
        if(entry.on) {
            return shared.make_element("p", {"class": "event"}, "System switched back on from the dashboard.", time);
        }

        //the owner texting them from ghl switches them off on its own
        if(entry.by === "ghl") {
            return shared.make_element("p", {"class": "event is-off"}, "System switched off: the owner texted them from GHL.", time);
        }

        return shared.make_element("p", {"class": "event is-off"}, "System switched off from the dashboard.", time);
    }

    if(entry.kind === "flag") {
        return shared.make_element("p", {"class": "event is-hil"}, `Flagged: ${entry.feedback}`, time);
    }

    return shared.make_element("p", {"class": "event"}, "An entry this dashboard doesn't know how to show.");
}


//RENDER LOG
//a day heading every time the shop date changes
function render_log(entries: ENTRY[]): void {
    const nodes: HTMLElement[] = [];

    let last_date: string = "";

    for(const entry of entries) {
        const date: string = shared.shop_parts(entry.at).date;

        if(date !== last_date) {
            nodes.push(shared.make_element("h3", {"class": "day"}, shared.day_label(date)));

            last_date = date;
        }

        nodes.push(entry_node(entry));
    }

    if(nodes.length === 0) {
        nodes.push(shared.make_element("p", {"class": "log-note"}, "Nothing is kept for this conversation anymore. Threads last a year after the last message."));
    }

    LOG.replaceChildren(...nodes);
}


//RENDER HEAD
function render_head(convo: THREAD_CONVO): void {
    THREAD_HEAD.hidden = false;

    THREAD_NAME.textContent = convo_title(convo);

    const where: string = shared.CHANNEL_NAMES[convo.channel] ?? convo.channel;

    let meta: string = where;

    if(convo.name) {
        meta = `${where}, ${shared.readable_id(convo.id)}`;
    }

    THREAD_META.textContent = meta;

    //whole channel off outranks the customer's own switch, so it shows that and waits for the channel
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
}


//LOAD THREAD
//fresh means a newly opened convo, a refresh only scrolls down if they were near the bottom
async function load_thread(fresh: boolean): Promise<void> {
    if(!CURRENT_ID) {
        return;
    }

    const id: string = CURRENT_ID;

    PAGE.classList.add("show-thread");

    if(fresh) {
        THREAD_HEAD.hidden = true;

        LOG.replaceChildren(shared.make_element("p", {"class": "log-note"}, "Loading messages…"));
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

        if(fresh || near_bottom) {
            LOG.scrollTop = LOG.scrollHeight;
        }
    }

    catch(error: unknown) {
        let message: string = "Couldn't load this conversation. It retries on its own.";

        if(error instanceof shared.ServerError) {
            message = error.message;
        }

        LOG.replaceChildren(shared.make_element("p", {"class": "log-note"}, message));
    }
}


//SHOW LIST
function show_list(): void {
    PAGE.classList.remove("show-thread");

    THREAD_HEAD.hidden = true;

    COMPOSE_FORM.hidden = true;

    CURRENT_CONVO = null;

    LOG.replaceChildren(shared.make_element("p", {"class": "log-note"}, "Pick a conversation to see every message in and every reply out."));
}



//**********LIST**********
//the open tab's convos, its counts and its channel switch


//PRESS VIEW
//the tab's convos split by their own switch into System on and System off
function press_view(): void {
    for(const view of VIEWS) {
        VIEW_BUTTONS[view].button.setAttribute("aria-pressed", String(view === CURRENT_VIEW));
    }
}


//RENDER CHANNEL
//off means the system answers nobody on the tab's channels till it's switched back on
function render_channel(): void {
    const name: string = TAB_NAMES[CURRENT_TAB];

    const off: boolean = OFF_TABS.has(CURRENT_TAB);

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


//EMPTY NOTE
//what an empty list says for the open view
function empty_note(view_counts: Record<VIEW, number>): string {
    const name: string = TAB_NAMES[CURRENT_TAB];

    if(CURRENT_VIEW === "off") {
        return `No ${name} conversations are switched off.`;
    }

    if(view_counts.off > 0) {
        return `Every ${name} conversation is switched off. They're under System off.`;
    }

    return `No ${name} conversations yet. They show up here the moment a customer messages in.`;
}


//OPEN CONVO
function open_convo(id: string, button: HTMLButtonElement): void {
    CURRENT_ID = id;

    remember_place();

    for(const row of LIST.querySelectorAll(".convo")) {
        row.setAttribute("aria-current", String(row === button));
    }

    load_thread(true);
}


//CONVO ROW
//is_new lights up a convo that got a new message since the last load
function convo_row(convo: CONVO, is_new: boolean): HTMLLIElement {
    let row_class: string = "convo";

    if(is_new) {
        row_class = "convo is-new";
    }

    const name: HTMLSpanElement = shared.make_element("span", {"class": "convo-name"}, convo_title(convo));

    const time: HTMLTimeElement = shared.make_element("time", {"datetime": new Date(convo.last_at).toISOString()}, shared.when_short(convo.last_at));

    const top: HTMLSpanElement = shared.make_element("span", {"class": "convo-top"}, name, time);

    let preview_class: string = "convo-preview";

    let preview_text: string = convo.last_text || "Sent media";

    if(convo.last_kind === "out") {
        preview_class = "convo-preview is-reply";

        preview_text = `System: ${convo.last_text}`;
    }

    const preview: HTMLSpanElement = shared.make_element("span", {"class": preview_class}, preview_text);

    //false gets left out
    let badges: HTMLSpanElement | false = false;

    if(convo.flagged_at > 0) {
        badges = shared.make_element("span", {"class": "convo-badges"}, shared.make_element("span", {"class": "badge is-flagged"}, "Flagged"));
    }

    const button: HTMLButtonElement = shared.make_element("button", {"type": "button", "class": row_class, "data-id": convo.id, "aria-current": String(convo.id === CURRENT_ID)}, top, preview, badges);

    button.addEventListener("click", (): void => { open_convo(convo.id, button); });

    return shared.make_element("li", {}, button);
}


//LOAD LIST
//append is "Show older", anything else rebuilds the list
async function load_list(append: boolean = false): Promise<void> {
    if(!append && SHOWN_CONVOS.length === 0) {
        LIST_NOTE.textContent = "Loading conversations…";

        LIST_NOTE.hidden = false;
    }

    try {
        //a refresh asks for everything on screen, so a list opened past 50 with "Show older" stays open
        let query: string = `limit=${Math.max(50, SHOWN_CONVOS.length)}`;

        if(append) {
            query = `start=${SHOWN_CONVOS.length}`;
        }

        const data: CONVO_PAGE = await shared.ask_server<CONVO_PAGE>(`/api/convos?tab=${CURRENT_TAB}&view=${CURRENT_VIEW}&${query}`);

        //another tab or view got picked while this one loaded
        if(data.tab !== CURRENT_TAB || data.view !== CURRENT_VIEW) {
            return;
        }

        for(const entry of TAB_BUTTONS) {
            entry[1].count.textContent = String(data.counts[entry[0]] ?? 0);
        }

        for(const view of VIEWS) {
            VIEW_BUTTONS[view].count.textContent = String(data.view_counts[view] ?? 0);
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
            SHOWN_CONVOS = [...SHOWN_CONVOS, ...data.convos];
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
    }

    catch(error: unknown) {
        let message: string = "Couldn't load conversations. It retries on its own.";

        if(error instanceof shared.ServerError) {
            message = error.message;
        }

        LIST_NOTE.textContent = message;

        LIST_NOTE.hidden = false;
    }
}



//**********PICKING**********
//tabs, views, older convos and the back button


//PICK TAB
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


//BUILD TAB
//red dot on a channel that's switched off, so it shows from every tab
function build_tab(tab: TAB): void {
    const count: HTMLSpanElement = shared.make_element("span", {"class": "tab-count"}, "");

    const off_mark: HTMLSpanElement = shared.make_element("span", {"class": "tab-off", "hidden": true}, shared.make_element("span", {"class": "visually-hidden"}, "System off"));

    const button: HTMLButtonElement = shared.make_element("button", {"type": "button", "class": "tab", "aria-pressed": String(tab === CURRENT_TAB)}, TAB_NAMES[tab], off_mark, count);

    button.addEventListener("click", (): void => { pick_tab(tab); });

    TAB_BUTTONS.set(tab, {"button": button, "count": count, "off_mark": off_mark});

    TABS_NAV.append(button);
}


//PICK VIEW
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


//SHOW MORE
function show_more(): void {
    load_list(true);
}


//GO BACK
function go_back(): void {
    CURRENT_ID = "";

    remember_place();

    show_list();

    for(const row of LIST.querySelectorAll(".convo")) {
        row.setAttribute("aria-current", "false");
    }
}



//**********SWITCHES**********
//off means the system sends nothing till it's switched back on


//FLIP SWITCH
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

        let message: string = `System switched off for ${convo_title(convo)}. Nothing goes out to them now, and they're under System off.`;

        if(on) {
            message = `System switched on for ${convo_title(convo)}. It answers their next message, and they're back under System on.`;
        }

        shared.toast(message);

        load_thread(false);

        load_list();
    }

    catch(error: unknown) {
        let message: string = "The switch didn't change. Try again.";

        if(error instanceof shared.ServerError) {
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


//FLIP CHANNEL
//everyone on the open tab's channels
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

        if(error instanceof shared.ServerError) {
            message = error.message;
        }

        shared.toast(message, true);
    }

    finally {
        CHANNEL_SWITCH.disabled = false;
    }
}



//**********DELETE**********
//after an are-you-sure, everything kept for the convo goes and the overview drops what it added


//OPEN TRASH
function open_trash(): void {
    if(CURRENT_CONVO === null) {
        return;
    }

    TRASH_NOTE.textContent = `Every message, reply, pic and follow up kept for ${convo_title(CURRENT_CONVO)} comes off the dashboard for good, and the Overview's numbers drop by what this conversation added. Their switch stays as it is, and a new message from them starts a new conversation.`;

    TRASH_ERROR.hidden = true;

    TRASH_DIALOG.showModal();
}


//CLOSE TRASH
function close_trash(): void {
    TRASH_DIALOG.close();
}


//SEND TRASH
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

        if(error instanceof shared.ServerError) {
            message = error.message;
        }

        TRASH_ERROR.textContent = message;

        TRASH_ERROR.hidden = false;
    }

    finally {
        TRASH_CONFIRM.disabled = false;
    }
}



//**********FLAG**********
//what went wrong, emailed with the last reply and the state it came from


//OPEN FLAG
function open_flag(): void {
    if(CURRENT_CONVO === null) {
        return;
    }

    FLAG_ERROR.hidden = true;

    FLAG_TEXT.value = "";

    FLAG_DIALOG.showModal();
}


//CLOSE FLAG
function close_flag(): void {
    FLAG_DIALOG.close();
}


//SEND FLAG
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

        if(error instanceof shared.ServerError) {
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



//**********COMPOSE**********
//a text from the shop, sent right from the dashboard over blooio


//SEND TEXT
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
    }

    catch(error: unknown) {
        let message: string = "The text didn't send. Check your connection and try again.";

        if(error instanceof shared.ServerError) {
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


//SEND ON ENTER
//enter sends, shift enter starts a new line
function send_on_enter(event: KeyboardEvent): void {
    if(event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();

        COMPOSE_FORM.requestSubmit();
    }
}



//**********PULSE**********
//the feed wrote something new


//REFRESH
function refresh(): void {
    load_list();

    load_thread(false);
}



//**********START**********
//read the address, build the tabs, wire everything, then the first loads


//PLACE
//tab, view and convo come from the address
if(is_tab(ADDRESS_TAB)) {
    CURRENT_TAB = ADDRESS_TAB;
}

if(ADDRESS.get("view") === "off") {
    CURRENT_VIEW = "off";
}

CURRENT_ID = ADDRESS.get("id") ?? "";


//TABS
for(const tab of TABS) {
    build_tab(tab);
}


//VIEWS
for(const view of VIEWS) {
    VIEW_BUTTONS[view].button.addEventListener("click", (): void => { pick_view(view); });
}

press_view();


//MORE
MORE_BUTTON.addEventListener("click", show_more);


//BACK
BACK_BUTTON.addEventListener("click", go_back);


//SWITCHES
SWITCH_BUTTON.addEventListener("click", flip_switch);

CHANNEL_SWITCH.addEventListener("click", flip_channel);


//DELETE
TRASH_BUTTON.addEventListener("click", open_trash);

TRASH_CANCEL.addEventListener("click", close_trash);

TRASH_FORM.addEventListener("submit", send_trash);


//FLAG
FLAG_BUTTON.addEventListener("click", open_flag);

FLAG_CANCEL.addEventListener("click", close_flag);

FLAG_FORM.addEventListener("submit", send_flag);


//COMPOSE
COMPOSE_FORM.addEventListener("submit", send_text);

COMPOSE_TEXT.addEventListener("keydown", send_on_enter);


//FIRST LOAD
remember_place();

load_list();

if(CURRENT_ID) {
    load_thread(true);
}

else {
    show_list();
}


//PULSE
shared.on_pulse(refresh);
