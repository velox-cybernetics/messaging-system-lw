#IMPORTS

import sys
import threading
from contextvars import ContextVar


#GLOBALS

#the real terminal, grabbed before this file takes over as stdout
TERMINAL = sys.stdout

#what the batch being answered printed so far, None outside a batch so it prints right away
HELD_LINES = ContextVar("held_lines", default=None)

#one block prints at a time, so two batches finishing together never mix lines
PRINT_LOCK = threading.Lock()


#STDOUT PARTS

#print lands here, a batchs text waits in its held lines and the rest goes right out
def write(text: str) -> int:
    lines: list[str] | None = HELD_LINES.get()

    if(lines is None):
        with PRINT_LOCK:
            return TERMINAL.write(text)

    lines.append(text)

    return len(text)

#held lines wait for there batch, so only the real terminal gets flushed
def flush() -> None:
    TERMINAL.flush()

#isatty, fileno, encoding and whatever else gets asked of stdout come off the real terminal
def __getattr__(name: str) -> object:
    return getattr(TERMINAL, name)
