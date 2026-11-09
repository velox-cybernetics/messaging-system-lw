//IMPORTS

import * as shared from "./shared.js";


//GLOBALS

type RANGE = "day" | "week" | "month" | "ytd";

type CHART_KIND = "messaging" | "booking";

//one slot on the chart, same shape the apis overview sends
type BAR = {key: string; future: boolean; din: number; dout: number; dquoted: number; hil: number; booked: number};

type TOTALS = {din: number; dout: number; dquoted: number; hil: number; booked: number; dhil: number; dbooked: number};

type CHECK_IN = {last_seen: number; beat_seconds: number};

//keep in step with the apis overview handler
type OVERVIEW = {range: RANGE; from: string; to: string; today: string; totals: TOTALS; follow_ups_today: number; bars: BAR[]; check_in: CHECK_IN};

type SERIES = {field: "din" | "dout" | "dquoted" | "booked"; name: string; one?: string; class_name: string};

type RANGE_CHOICE = {range: RANGE; label: string; period: string};

const RANGES: RANGE_CHOICE[] = [{"range": "day", "label": "Day", "period": "today"}, {"range": "week", "label": "Week", "period": "this week"}, {"range": "month", "label": "Month", "period": "this month"}, {"range": "ytd", "label": "YTD", "period": "this year"}];

const MESSAGING_SERIES: SERIES[] = [{"field": "din", "name": "Messaged in", "class_name": "is-in"}, {"field": "dout", "name": "Got a reply", "class_name": "is-out"}];

//price comes right before booking, side by side shows how many prices turned into jobs
const BOOKING_SERIES: SERIES[] = [{"field": "dquoted", "name": "Got a price", "class_name": "is-out"}, {"field": "booked", "name": "Booked jobs", "one": "Booked job", "class_name": "is-booked"}];

const CHART_SERIES: Record<CHART_KIND, SERIES[]> = {"messaging": MESSAGING_SERIES, "booking": BOOKING_SERIES};

const SVG: "http://www.w3.org/2000/svg" = "http://www.w3.org/2000/svg";

const CHART_HEIGHT: number = 240;

const AXIS_WIDTH: number = 36;

const LABEL_HEIGHT: number = 26;

//room for the widest label like Oct 10 or 12 AM plus a gap, at 12px
const MIN_LABEL_GAP: number = 48;

//numbers don't need to be to the second, a burst of messages reloads at most this often
const RELOAD_GAP_MS: number = 30000;

const RANGE_NAV: HTMLElement = shared.by_id<HTMLElement>("ranges");

const PICKER: HTMLSelectElement = shared.by_id<HTMLSelectElement>("chart-picker");

const CAPTION: HTMLParagraphElement = shared.by_id<HTMLParagraphElement>("caption");

const HEADLINE: HTMLElement = shared.by_id<HTMLElement>("headline");

const CHART: HTMLElement = shared.by_id<HTMLElement>("chart");

const LEGEND: HTMLUListElement = shared.by_id<HTMLUListElement>("legend");

const FOLLOW_UPS_TODAY: HTMLElement = shared.by_id<HTMLElement>("followups-today");

const PERCENT: Intl.NumberFormat = new Intl.NumberFormat("en-US", {"maximumFractionDigits": 1});

//set from the address at the top of START
let RANGE_PICKED: RANGE = "day";

let KIND: CHART_KIND = "messaging";

let LATEST: OVERVIEW | null = null;

let LAST_LOAD: number = 0;

let RELOAD_TIMER: number = 0;

//bars grow in on first draw and after a pick, never on a refresh or resize
let GROW_NEXT: boolean = true;


//ADDRESS

//the range in the address, day when its missing or made up
function range_from_address(params: URLSearchParams): RANGE {
    for(const each of RANGES) {
        if(each.range === params.get("range")) {
            return each.range;
        }
    }

    return "day";
}

//booking only when the address asks for it, messaging otherwise
function kind_from_address(params: URLSearchParams): CHART_KIND {
    if(params.get("chart") === "booking") {
        return "booking";
    }

    return "messaging";
}

//picks go in the address so a reload shows the same chart, defaults stay out of it
function remember_place(): void {
    const query: URLSearchParams = new URLSearchParams();

    if(RANGE_PICKED !== "day") {
        query.set("range", RANGE_PICKED);
    }

    if(KIND !== "messaging") {
        query.set("chart", KIND);
    }

    const text: string = query.toString();

    let address: string = "/";

    if(text) {
        address = `/?${text}`;
    }

    history.replaceState(null, "", address);
}


//TEXT

//which days the numbers cover, in words
function caption_text(data: OVERVIEW): string {
    const short: Intl.DateTimeFormatOptions = {"month": "short", "day": "numeric"};

    switch(data.range) {
        case "day":
            return `Today, ${shared.day_text(data.today, short)}`;

        case "week":
            return `This week, ${shared.day_text(data.from, short)} to ${shared.day_text(data.to, short)}`;

        case "month":
            return `This month, ${shared.day_text(data.from, short)} to ${shared.day_text(data.to, short)}`;

        case "ytd":
            return `This year so far, ${shared.day_text(data.from, short)} to ${shared.day_text(data.today, short)}`;
    }
}

//day bars are the shops hours, told on the viewers own clock
function bar_title(bar: BAR, today: string): string {
    switch(RANGE_PICKED) {
        case "day":
            return `${shared.shop_hour_text(today, Number(bar.key))} to ${shared.shop_hour_text(today, Number(bar.key) + 1)}`;

        case "ytd":
            return shared.day_text(bar.key, {"month": "long"});

        default:
            return shared.day_text(bar.key, {"weekday": "short", "month": "short", "day": "numeric"});
    }
}

//the 1st and every 5th day only
function month_label(bar: BAR): string {
    const day: number = Number(bar.key.slice(8));

    if(day === 1 || day % 5 === 0) {
        return shared.day_text(bar.key, {"month": "short", "day": "numeric"});
    }

    return "";
}

//empty when a label would crowd the axis, day bars show shop hours on the viewers clock
function bar_label(bar: BAR, index: number, today: string): string {
    switch(RANGE_PICKED) {
        case "day":
            if(index % 3 === 0) {
                return shared.shop_hour_text(today, Number(bar.key));
            }

            return "";

        case "week":
            return `${shared.day_text(bar.key, {"weekday": "short"})} ${Number(bar.key.slice(8))}`;

        case "month":
            return month_label(bar);

        case "ytd":
            return shared.day_text(bar.key, {"month": "short"});
    }
}

//en dash when theres nothing to divide by
function share(part: number, whole: number): string {
    if(whole > 0) {
        return `${PERCENT.format(Math.min(100, (part / whole) * 100))}%`;
    }

    return "–";
}

//the picked range in words for the end of a sentence, like this week
function period(): string {
    for(const each of RANGES) {
        if(each.range === RANGE_PICKED) {
            return each.period;
        }
    }

    return "";
}


//PICKS

//a range button got pressed, so the numbers reload for it
function pick_range(range: RANGE, button: HTMLButtonElement): void {
    RANGE_PICKED = range;

    GROW_NEXT = true;

    remember_place();

    for(const other of RANGE_NAV.querySelectorAll(".segment")) {
        other.setAttribute("aria-pressed", String(other === button));
    }

    load();
}

//the dropdown swaps charts, same numbers so no reload needed
function pick_chart(): void {
    if(PICKER.value === "booking") {
        KIND = "booking";
    }
    else {
        KIND = "messaging";
    }

    GROW_NEXT = true;

    remember_place();

    render();
}


//HEADLINE

//booking rate on the booking chart, otherwise whether the systems running
function render_headline(): void {
    if(LATEST === null) {
        return;
    }

    const check_in: CHECK_IN = LATEST.check_in;

    const totals: TOTALS = LATEST.totals;

    if(KIND === "booking") {
        const figure: HTMLParagraphElement = shared.make_element("p", {"class": "headline-figure is-booked"}, [shared.make_element("strong", {}, [share(totals.dbooked, totals.din)]), ` booking rate ${period()}`]);

        const note: HTMLParagraphElement = shared.make_element("p", {"class": "caption"}, [`${shared.big_number(totals.dbooked).exact} of ${shared.big_number(totals.din).exact} customers who messaged in`]);

        HEADLINE.replaceChildren(figure, note);

        return;
    }

    //a check in is due every beat, 2 minutes of slack before it counts as offline
    const running: boolean = check_in.last_seen > 0 && Date.now() - check_in.last_seen < (check_in.beat_seconds + 120) * 1000;

    let status: HTMLElement;

    if(check_in.last_seen === 0) {
        status = shared.make_element("p", {"class": "status"}, [shared.make_element("span", {"class": "dot"}), "Waiting for the system's first check-in"]);
    }
    else if(running) {
        status = shared.make_element("p", {"class": "status is-up"}, [shared.make_element("span", {"class": "dot"}), "System running"]);
    }
    else {
        status = shared.make_element("p", {"class": "status is-down"}, [shared.make_element("span", {"class": "dot"}), `System offline since ${shared.when_short(check_in.last_seen)}`]);
    }

    HEADLINE.replaceChildren(status);
}


//CHART

//svg needs its own namespace, plain createElement makes duds
function make_svg<K extends keyof SVGElementTagNameMap>(tag: K, attributes: Record<string, string | number>): SVGElementTagNameMap[K] {
    const element: SVGElementTagNameMap[K] = document.createElementNS(SVG, tag);

    for(const attribute of Object.entries(attributes)) {
        element.setAttribute(attribute[0], String(attribute[1]));
    }

    return element;
}

//a round axis top that splits into 4 whole steps, like 0, 20, 40, 60, 80
function nice_top(max: number): number {
    if(max <= 4) {
        return 4;
    }

    const step: number = max / 4;

    const power: number = 10 ** Math.floor(Math.log10(step));

    for(const multiple of [1, 2, 2.5, 4, 5, 8, 10]) {
        const candidate: number = multiple * power;

        if(candidate >= step && Number.isInteger(candidate)) {
            return candidate * 4;
        }
    }

    return 40 * power;
}

//takes the tip down if ones up
function remove_tip(): void {
    const tip: Element | null = CHART.querySelector(".tip");

    if(tip !== null) {
        tip.remove();
    }
}

//the numbers for one bar, above it when theres room
function show_tip(bar: BAR, series: SERIES[], today: string, slot_left: number, slot_width: number, bar_top: number): void {
    const rows: HTMLParagraphElement[] = [];

    for(const each of series) {
        let name: string = each.name;

        if(bar[each.field] === 1 && each.one) {
            name = each.one;
        }

        rows.push(shared.make_element("p", {"class": `tip-row ${each.class_name}-key`}, [shared.make_element("strong", {}, [String(bar[each.field])]), shared.make_element("span", {}, [name])]));
    }

    const title: HTMLParagraphElement = shared.make_element("p", {"class": "tip-title"}, [bar_title(bar, today)]);

    const tip: HTMLDivElement = shared.make_element("div", {"class": "tip"}, [title].concat(rows));

    remove_tip();

    CHART.append(tip);

    const gap: number = 10;

    let left: number = slot_left + slot_width / 2 - tip.offsetWidth / 2;

    let top: number = bar_top - tip.offsetHeight - gap;

    //no room above the bar, so it sits beside the slot instead of covering it
    if(top < 0) {
        top = 0;

        if(slot_left + slot_width + gap + tip.offsetWidth <= CHART.clientWidth) {
            left = slot_left + slot_width + gap;
        }
        else {
            left = slot_left - gap - tip.offsetWidth;
        }
    }

    tip.style.left = `${Math.min(Math.max(0, left), CHART.clientWidth - tip.offsetWidth)}px`;

    tip.style.top = `${top}px`;
}

//tip down and the bars highlight off
function hide_tip(): void {
    remove_tip();

    const active: Element | null = CHART.querySelector(".slot.is-active");

    if(active !== null) {
        active.classList.remove("is-active");
    }
}

//one bar gets the highlight and the tip, whatever had them loses them
function point_at_bar(group: SVGGElement, bar: BAR, series: SERIES[], today: string, left: number, slot: number, bar_top: number): void {
    hide_tip();

    group.classList.add("is-active");

    show_tip(bar, series, today, left, slot, bar_top);
}

//a lifted finger counts as leaving, so on touch the numbers stay till another tap
function leave_chart(event: PointerEvent): void {
    if(event.pointerType === "mouse") {
        hide_tip();
    }
}

//the whole svg chart, drawn again from scratch on every render or resize
function render_chart(): void {
    //phones hide the chart so it has no width, the resize observer draws it once it shows
    const width: number = CHART.clientWidth;

    if(LATEST === null || width === 0) {
        return;
    }

    const series: SERIES[] = CHART_SERIES[KIND];

    const bars: BAR[] = LATEST.bars;

    //the shop date the day ranges hours are on
    const today: string = LATEST.today;

    let tallest: number = 0;

    for(const bar of bars) {
        for(const each of series) {
            tallest = Math.max(tallest, bar[each.field]);
        }
    }

    const top: number = nice_top(tallest);

    const plot_height: number = CHART_HEIGHT - 8;

    const slot: number = (width - AXIS_WIDTH) / bars.length;

    const bar_width: number = Math.max(2, Math.min(28, (slot * 0.72) / series.length - 2));

    const group_width: number = bar_width * series.length + (series.length - 1) * 3;

    let grow_class: string = "";

    if(GROW_NEXT) {
        grow_class = "grow";
    }

    const drawing: SVGSVGElement = make_svg("svg", {"width": width, "height": CHART_HEIGHT + LABEL_HEIGHT, "viewBox": `0 0 ${width} ${CHART_HEIGHT + LABEL_HEIGHT}`, "role": "img", "class": grow_class});

    GROW_NEXT = false;

    for(const quarter of [0, 1, 2, 3, 4]) {
        const y: number = CHART_HEIGHT - (quarter / 4) * plot_height;

        let line_class: string = "grid";

        if(quarter === 0) {
            line_class = "axis";
        }

        drawing.append(make_svg("line", {"x1": AXIS_WIDTH, "x2": width, "y1": y, "y2": y, "class": line_class}));

        const tick: SVGTextElement = make_svg("text", {"x": AXIS_WIDTH - 10, "y": y + 4, "class": "tick", "text-anchor": "end"});

        tick.textContent = shared.big_number((top * quarter) / 4).short;

        drawing.append(tick);
    }

    //narrow screens skip some labels so the shown ones never run together
    let last_label_x: number = -Infinity;

    let index: number = 0;

    for(const bar of bars) {
        const left: number = AXIS_WIDTH + index * slot;

        const group: SVGGElement = make_svg("g", {"class": "slot"});

        group.append(make_svg("rect", {"x": left, "y": 0, "width": slot, "height": CHART_HEIGHT, "class": "hit"}));

        let bar_top: number = CHART_HEIGHT;

        if(bar.future) {
            group.append(make_svg("rect", {"x": left + (slot - group_width) / 2, "y": CHART_HEIGHT - 2, "width": group_width, "height": 2, "class": "later"}));
        }
        else {
            let position: number = 0;

            for(const each of series) {
                const height: number = (bar[each.field] / top) * plot_height;

                const y: number = CHART_HEIGHT - height;

                bar_top = Math.min(bar_top, y);

                group.append(make_svg("rect", {"x": left + (slot - group_width) / 2 + position * (bar_width + 3), "y": y, "width": bar_width, "height": height, "rx": Math.min(2, bar_width / 4), "class": `column ${each.class_name}`}));

                position = position + 1;
            }

            const final_top: number = bar_top;

            //hovering or tapping a bar brings up its numbers
            function point_here(): void {
                point_at_bar(group, bar, series, today, left, slot, final_top);
            }

            group.addEventListener("pointerenter", point_here);

            group.addEventListener("pointerdown", point_here);
        }

        drawing.append(group);

        const label: string = bar_label(bar, index, today);

        const label_x: number = left + slot / 2;

        if(label && label_x - last_label_x >= MIN_LABEL_GAP) {
            const text: SVGTextElement = make_svg("text", {"x": label_x, "y": CHART_HEIGHT + 18, "class": "tick", "text-anchor": "middle"});

            text.textContent = label;

            drawing.append(text);

            last_label_x = label_x;
        }

        index = index + 1;
    }

    drawing.addEventListener("pointerleave", leave_chart);

    const sums: string[] = [];

    for(const each of series) {
        let sum: number = 0;

        for(const bar of bars) {
            sum = sum + bar[each.field];
        }

        sums.push(`${sum} ${each.name.toLowerCase()}`);
    }

    let chart_name: string = "Activity";

    const picked: HTMLOptionElement | undefined = PICKER.selectedOptions[0];

    if(picked !== undefined && picked !== null) {
        chart_name = picked.text;
    }

    drawing.setAttribute("aria-label", `${chart_name}, ${CAPTION.textContent}: ${sums.join(", ")}`);

    let quiet: boolean = true;

    for(const bar of bars) {
        for(const each of series) {
            if(bar[each.field] !== 0) {
                quiet = false;
            }
        }
    }

    let note: string = `No prices or bookings yet ${period()}.`;

    if(KIND === "messaging") {
        note = `No messages yet ${period()}.`;
    }

    //the note only shows when the range has nothing yet
    if(quiet) {
        CHART.replaceChildren(drawing, shared.make_element("p", {"class": "chart-note"}, [note]));
    }
    else {
        CHART.replaceChildren(drawing, "");
    }

    const keys: HTMLLIElement[] = [];

    for(const each of series) {
        keys.push(shared.make_element("li", {"class": `${each.class_name}-key`}, [each.name]));
    }

    LEGEND.replaceChildren();

    for(const key of keys) {
        LEGEND.append(key);
    }
}


//STRIP

//the totals strip, every element marked data total or data rate gets its number
function render_strip(totals: TOTALS, follow_ups: number): void {
    for(const element of document.querySelectorAll<HTMLElement>("[data-total]")) {
        let count: number = totals[element.dataset.total as keyof TOTALS];

        if(count === undefined || count === null) {
            count = 0;
        }

        const value: shared.BIG_NUMBER = shared.big_number(count);

        element.textContent = value.short;

        element.title = value.exact;

        //so it reads 1 booked job and 3 booked jobs
        const label: Element | null = element.nextElementSibling;

        if(label instanceof HTMLElement && label.dataset.one) {
            if(label.dataset.many === undefined) {
                let many: string | null = label.textContent;

                if(many === null) {
                    many = "";
                }

                label.dataset.many = many;
            }

            if(count === 1) {
                label.textContent = label.dataset.one;
            }
            else {
                label.textContent = label.dataset.many;
            }
        }
    }

    for(const element of document.querySelectorAll<HTMLElement>("[data-rate]")) {
        let part: number = totals[element.dataset.rate as keyof TOTALS];

        if(part === undefined || part === null) {
            part = 0;
        }

        element.textContent = share(part, totals.din);
    }

    //todays, whatever range is picked
    const sent: shared.BIG_NUMBER = shared.big_number(follow_ups);

    FOLLOW_UPS_TODAY.textContent = sent.short;

    FOLLOW_UPS_TODAY.title = sent.exact;
}


//LOADING

//everything on the page from the last load
function render(): void {
    if(LATEST === null) {
        return;
    }

    CAPTION.textContent = caption_text(LATEST);

    render_headline();

    render_chart();

    render_strip(LATEST.totals, LATEST.follow_ups_today);
}

//fetches the picked range, an answer for an old pick gets dropped
async function load(): Promise<void> {
    const asked: RANGE = RANGE_PICKED;

    LAST_LOAD = Date.now();

    try {
        const data: OVERVIEW = await shared.ask_server<OVERVIEW>(`/api/overview?range=${asked}`);

        //another range got picked while this one loaded
        if(asked !== RANGE_PICKED) {
            return;
        }

        LATEST = data;

        render();
    }
    catch(error: unknown) {
        let message: string = "Couldn't load the numbers. It retries on its own.";

        if(shared.is_server_error(error)) {
            message = error.message;
        }

        CAPTION.textContent = message;
    }
}

//the waits over, the numbers reload
function reload_now(): void {
    load();
}

//new messages reload the numbers, at most once every RELOAD_GAP_MS
function reload_soon(): void {
    window.clearTimeout(RELOAD_TIMER);

    RELOAD_TIMER = window.setTimeout(reload_now, Math.max(0, LAST_LOAD + RELOAD_GAP_MS - Date.now()));
}

//a new width means new bar sizes, so the chart redraws
function on_resize(): void {
    render_chart();
}

//a tap outside the chart puts its numbers away
function tap_outside(event: PointerEvent): void {
    if(event.target instanceof Node && !CHART.contains(event.target)) {
        hide_tip();
    }
}

//every pulse has the last check in, so System running never goes stale between reloads
function on_beat(pulse: shared.PULSE): void {
    if(LATEST === null) {
        return;
    }

    if(pulse.up_last !== LATEST.check_in.last_seen) {
        LATEST.check_in.last_seen = pulse.up_last;

        render_headline();
    }
}


//START

const PARAMS: URLSearchParams = new URLSearchParams(location.search);

RANGE_PICKED = range_from_address(PARAMS);

KIND = kind_from_address(PARAMS);

for(const each of RANGES) {
    const button: HTMLButtonElement = shared.make_element("button", {"type": "button", "class": "segment", "aria-pressed": String(each.range === RANGE_PICKED)}, [each.label]);

    //each button picks its own range
    function pick_this_range(): void {
        pick_range(each.range, button);
    }

    button.addEventListener("click", pick_this_range);

    RANGE_NAV.append(button);
}

PICKER.value = KIND;

PICKER.addEventListener("change", pick_chart);

new ResizeObserver(on_resize).observe(CHART);

document.addEventListener("pointerdown", tap_outside);

window.setInterval(render_headline, 30000);

remember_place();

load();

shared.on_pulse(reload_soon, on_beat);
