#GLOBALS

#straight or curly, the model isn't picky about which quotes it wraps a reply in
QUOTES: tuple[str, ...] = ("\"", "“", "”")


#REPLY CLEANUP

#how many quote marks of any kind the reply has in it
def count_quotes(reply: str) -> int:
    quote_count: int = 0

    for quote in QUOTES:
        quote_count += reply.count(quote)

    return quote_count

#peels off the quotes the model loves wrapping replies in, a paired quote inside stays
def strip_quotes(reply: str) -> str:
    reply = reply.strip()

    if(len(reply) >= 2 and reply.startswith(QUOTES) and reply.endswith(QUOTES)):
        reply = reply[1:-1].strip()

    #one lonely quote left at an end with nothing to pair with
    quote_count: int = count_quotes(reply)

    if(quote_count % 2 == 1 and reply.endswith(QUOTES)):
        reply = reply[:-1].strip()
    elif(quote_count % 2 == 1 and reply.startswith(QUOTES)):
        reply = reply[1:].strip()

    return reply

#whats left after a cut starts clean and capitalized, like a real sentence
def sentence_start(text: str) -> str:
    rest: str = text.lstrip(" \n,.!")

    return f"{rest[:1].upper()}{rest[1:]}"
