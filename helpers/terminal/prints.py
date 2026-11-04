#**********IMPORTS**********
#the terminal, thread locks, and the memory that keeps each message batch's prints together
import io
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import Context, ContextVar, Token, copy_context
from typing import TextIO



#**********GLOBALS**********
#the real terminal, the lines a batch holds back, and the print lock


#TERMINAL
#the real terminal, kept before the held stdout goes in, every line ends up here
TERMINAL: TextIO = sys.stdout


#HELD LINES
#what the message batch being answered printed so far, None outside a batch so those prints go straight out
HELD_LINES: ContextVar[list[str] | None] = ContextVar("held_lines", default=None)


#PRINT LOCK
#two batches finishing at once never mix their lines, one block prints at a time
PRINT_LOCK: threading.Lock = threading.Lock()



#**********HELD PRINTS**********
#holds back what a message batch prints and lets it out in one block, so batches never mix


#HELD STDOUT
#every print goes through here, a batch's lines wait for the batch to finish and everything else prints right away
class HeldStdout:
    #WRITE
    #a batch's text waits in its held lines, anything printed outside a batch goes straight to the terminal
    def write(self, text: str) -> int:
        lines: list[str] | None = HELD_LINES.get()

        if(lines is None):
            with PRINT_LOCK:
                return TERMINAL.write(text)

        lines.append(text)

        return len(text)

    #FLUSH
    #held lines wait for their batch, so only the real terminal gets flushed
    def flush(self) -> None:
        TERMINAL.flush()

    #EVERYTHING ELSE
    #anything else a stream gets asked for (isatty, fileno, encoding) comes from the real terminal
    def __getattr__(self, name: str) -> object:
        return getattr(TERMINAL, name)



#**********INSTALL**********
#sets up printing once when first imported, every print from then on goes through the held stdout


#LINE BY LINE
#a line printed outside a batch goes out the moment it ends, even when the terminal is a pipe like render's logs
#anything printed before this file got imported goes out here too
if(isinstance(TERMINAL, io.TextIOWrapper)):
    TERMINAL.reconfigure(line_buffering=True)


#INSTALL
#put in only once even if the file gets imported again
if(not isinstance(sys.stdout, HeldStdout)):
    sys.stdout = HeldStdout()



#**********HOLD**********
#everything a message batch prints comes out together once it's done


#HOLD
#a batch's prints, its worker threads included, come out in one block once its reply went out or it failed
@contextmanager
def held() -> Iterator[None]:
    token: Token = HELD_LINES.set([])

    try:
        yield

    finally:
        lines: list[str] | None = HELD_LINES.get()

        if(not lines):
            lines = []

        HELD_LINES.reset(token)

        with PRINT_LOCK:
            TERMINAL.write("".join(lines))

            TERMINAL.flush()


#BATCH CONTEXT
#a new worker thread starts without the batch's held lines, so it runs in a copy to print into the same block
def batch_context() -> Context:
    return copy_context()
