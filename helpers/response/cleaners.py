#**********GLOBALS**********
#the quote marks the model can wrap a reply in, straight or curly


#QUOTES
QUOTES: tuple[str, ...] = ("\"", "“", "”")



#**********REPLY CLEANUP**********
#takes off the quotes the model wraps a reply in, and starts what is left of a cut reply clean


#COUNT QUOTES
#how many quote marks of any kind the reply has in it
def count_quotes(reply: str) -> int:
    quote_count: int = 0

    for quote in QUOTES:
        quote_count += reply.count(quote)

    return quote_count


#STRIP QUOTES
#the model sometimes wraps its reply in quotes or leaves one at an end, a paired quote is part of the text
def strip_quotes(reply: str) -> str:
    reply = reply.strip()

    if(len(reply) >= 2 and reply.startswith(QUOTES) and reply.endswith(QUOTES)):
        reply = reply[1:-1].strip()

    #one quote left at an end with nothing to pair with
    quote_count: int = count_quotes(reply)

    if(quote_count % 2 == 1 and reply.endswith(QUOTES)):
        reply = reply[:-1].strip()

    elif(quote_count % 2 == 1 and reply.startswith(QUOTES)):
        reply = reply[1:].strip()

    return reply


#SENTENCE START
#the text with the spaces, commas and marks left at its front taken off, so it reads like a sentence
def sentence_start(text: str) -> str:
    rest: str = text.lstrip(" \n,.!")

    #what is left after a cut starts clean and capitalized
    return f"{rest[:1].upper()}{rest[1:]}"
