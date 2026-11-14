//GLOBALS

//letters and numbers make a word, apostrophes stay inside so don't and dont read the same
const WORD: RegExp = /[\p{L}\p{N}'’]+/gu;

//accent marks come off once a letter gets split from them, so jose finds José
const ACCENTS: RegExp = /\p{M}/gu;

const APOSTROPHES: RegExp = /['’]/g;

const LETTERS_ONLY: RegExp = /^\p{L}+$/u;

const NOT_DIGITS: RegExp = /\D/g;

const SPACE: RegExp = /\s/;

//a quote forms lines, so a snippet can join them with a dot instead of running them together
const LINE_BREAKS: RegExp = /\s*\n\s*/g;

//a long search gets cut, nobody types more than this into a search box
const MAX_QUERY_CHARS: number = 100;

const MAX_QUERY_WORDS: number = 8;

//how good a match is, a word that starts with whats typed beats one that has it inside, which beats a typo
const STARTS_WITH: number = 3;

const INSIDE: number = 2;

const TYPO: number = 1;

//a hit past this many characters in gets the text before it cut, so the row still shows it
const SNIPPET_LEAD: number = 40;

const SNIPPET_BEFORE: number = 24;

const SNIPPET_MAX: number = 220;

//what a search looks for, its words and what each word already scored against, so a word in many convos only gets checked once
export type SEARCH = {words: string[]; seen: Map<string, number>[]};

//one word of a text, where it sits and the plain form searches compare
type WORD_SPOT = {start: number; end: number; plain: string};


//WORDS

//lowercase, no accents and no apostrophes, the same on the page so its marks land on the same words
export function plain_word(word: string): string {
    return word.normalize("NFD").replace(ACCENTS, "").replace(APOSTROPHES, "").toLowerCase();
}

//every word in a text with where it starts and ends
function word_spots(text: string): WORD_SPOT[] {
    const spots: WORD_SPOT[] = [];

    for(const found of text.matchAll(WORD)) {
        const plain: string = plain_word(found[0]);

        //a lone apostrophe isn't a word
        if(plain !== "") {
            spots.push({"start": found.index, "end": found.index + found[0].length, "plain": plain});
        }
    }

    return spots;
}

//just the plain words of a text, repeats left in
export function plain_words(text: string): string[] {
    const words: string[] = [];

    for(const spot of word_spots(text)) {
        words.push(spot.plain);
    }

    return words;
}

//each word once, in the order they first show up
export function unique_words(words: string[]): string[] {
    const kept: Set<string> = new Set<string>();

    for(const word of words) {
        kept.add(word);
    }

    return Array.from(kept);
}

//a phone number id with only its digits left, so 801 851 0843 still finds +18018510843
export function number_digits(id: string): string {
    return id.replace(NOT_DIGITS, "");
}


//TYPOS

//one spot of the flat typo table, never undefined
function cell(table: number[], index: number): number {
    const value: number | undefined = table[index];

    if(value === undefined) {
        return 0;
    }

    return value;
}

//how many typos the token is from the closest start of the word, two swapped letters count as one
function typos(token: string, word: string): number {
    const rows: number = token.length + 1;

    const columns: number = word.length + 1;

    //row i column j is the typos between the first i letters of the token and the first j of the word
    const table: number[] = [];

    for(let row: number = 0; row < rows; row++) {
        for(let column: number = 0; column < columns; column++) {
            if(row === 0) {
                table.push(column);
            }
            else if(column === 0) {
                table.push(row);
            }
            else {
                let change: number = 1;

                if(token[row - 1] === word[column - 1]) {
                    change = 0;
                }

                const removed: number = cell(table, (row - 1) * columns + column) + 1;

                const added: number = cell(table, row * columns + column - 1) + 1;

                const changed: number = cell(table, (row - 1) * columns + column - 1) + change;

                let best: number = Math.min(removed, added, changed);

                if(row > 1 && column > 1 && token[row - 1] === word[column - 2] && token[row - 2] === word[column - 1]) {
                    best = Math.min(best, cell(table, (row - 2) * columns + column - 2) + 1);
                }

                table.push(best);
            }
        }
    }

    //the word can keep going past whats been typed so far, so the best spot on the last row wins
    let fewest: number = cell(table, (rows - 1) * columns);

    for(let column: number = 1; column < columns; column++) {
        fewest = Math.min(fewest, cell(table, (rows - 1) * columns + column));
    }

    return fewest;
}

//STARTS_WITH, INSIDE, TYPO or 0 when the word is nothing like the token
export function match_kind(token: string, word: string): number {
    if(word.startsWith(token)) {
        return STARTS_WITH;
    }

    //two letters inside a word would match half the dictionary
    if(token.length >= 3 && word.includes(token)) {
        return INSIDE;
    }

    //numbers never get typos, 2021 finding 2023 would be worse than nothing
    let allowed: number = 0;

    if(LETTERS_ONLY.test(token) && token.length >= 8) {
        allowed = 2;
    }
    else if(LETTERS_ONLY.test(token) && token.length >= 4) {
        allowed = 1;
    }

    //first letter has to be right, keeps wrap from finding trap
    if(allowed === 0 || word[0] !== token[0] || word.length < token.length - allowed) {
        return 0;
    }

    if(typos(token, word) <= allowed) {
        return TYPO;
    }

    return 0;
}


//SEARCH

//the words to look for, none when the search is empty or just punctuation
export function new_search(query: string): SEARCH {
    const words: string[] = unique_words(plain_words(query.slice(0, MAX_QUERY_CHARS))).slice(0, MAX_QUERY_WORDS);

    const seen: Map<string, number>[] = [];

    for(let index: number = 0; index < words.length; index++) {
        seen.push(new Map<string, number>());
    }

    return {"words": words, "seen": seen};
}

//match_kind for the searchs word at that index, remembered so the next convo with the same word skips the work
function kind_for(search: SEARCH, index: number, word: string): number {
    const token: string | undefined = search.words[index];

    const seen: Map<string, number> | undefined = search.seen[index];

    if(token === undefined || seen === undefined) {
        return 0;
    }

    let kind: number | undefined = seen.get(word);

    if(kind === undefined) {
        kind = match_kind(token, word);

        seen.set(word, kind);
    }

    return kind;
}

//the best kind any of the words gets for the searchs word at that index
function best_kind(search: SEARCH, index: number, words: string[]): number {
    let best: number = 0;

    for(const word of words) {
        best = Math.max(best, kind_for(search, index, word));

        if(best === STARTS_WITH) {
            break;
        }
    }

    return best;
}

//0 when any searched word is nowhere in the convo, a better match always wins, the same match in there name or number wins a tie
export function convo_score(search: SEARCH, name_words: string[], digits: string, customer_words: string[]): number {
    let score: number = 0;

    for(let index: number = 0; index < search.words.length; index++) {
        let token: string | undefined = search.words[index];

        if(token === undefined) {
            token = "";
        }

        let name_kind: number = best_kind(search, index, name_words);

        //a few digits anywhere in there phone number is as good as there name
        if(digits !== "" && token.length >= 3 && number_digits(token) === token && digits.includes(token)) {
            name_kind = STARTS_WITH;
        }

        const text_kind: number = best_kind(search, index, customer_words);

        let word_score: number = text_kind * 2;

        //kinds count double so the extra point only breaks a tie, a typo in there name never beats a real word they wrote
        if(name_kind > 0) {
            word_score = Math.max(word_score, name_kind * 2 + 1);
        }

        //every word has to show up somewhere
        if(word_score === 0) {
            return 0;
        }

        score += word_score;
    }

    return score;
}

//every one of the words that matched something searched, so the page can mark them
export function hit_words(search: SEARCH, words: string[]): string[] {
    const hits: string[] = [];

    for(const word of words) {
        for(let index: number = 0; index < search.words.length; index++) {
            if(kind_for(search, index, word) > 0 && !hits.includes(word)) {
                hits.push(word);
            }
        }
    }

    return hits;
}

//the newest message with the most hits in it, cut to start near the first one, empty when none of them have any
export function snippet(texts: string[], hits: string[]): string {
    let best_text: string = "";

    let best_count: number = 0;

    let best_start: number = 0;

    //newest first, so a tie keeps the newest
    for(let index: number = texts.length - 1; index >= 0; index--) {
        let text: string | undefined = texts[index];

        if(text === undefined) {
            text = "";
        }

        const found: Set<string> = new Set<string>();

        let first_start: number = -1;

        for(const spot of word_spots(text)) {
            if(hits.includes(spot.plain)) {
                found.add(spot.plain);

                if(first_start === -1) {
                    first_start = spot.start;
                }
            }
        }

        if(found.size > best_count) {
            best_text = text;

            best_count = found.size;

            best_start = first_start;
        }
    }

    if(best_count === 0) {
        return "";
    }

    //a hit deep in a long quote form gets the lines before it cut, backing up to a space so it starts on a whole word
    if(best_start > SNIPPET_LEAD) {
        let cut: number = best_start - SNIPPET_BEFORE;

        while(cut > best_start - SNIPPET_LEAD && !SPACE.test(best_text.charAt(cut))) {
            cut--;
        }

        best_text = `…${best_text.slice(cut).trim()}`;
    }

    return best_text.slice(0, SNIPPET_MAX).replace(LINE_BREAKS, " · ");
}
