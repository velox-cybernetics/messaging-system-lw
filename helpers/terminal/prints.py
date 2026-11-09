#IMPORTS

import io
import sys
from contextvars import copy_context

from helpers.terminal import held_stdout


#INSTALL

#a line printed outside a batch goes out the moment it ends, even into renders piped logs
if(isinstance(held_stdout.TERMINAL, io.TextIOWrapper)):
    held_stdout.TERMINAL.reconfigure(line_buffering=True)

#held_stdouts write and flush become stdout, once, even if this file gets imported again
if(sys.stdout is not held_stdout):
    sys.stdout = held_stdout


#HOLD

#a batchs prints wait in a fresh list from here until release, worker threads included
def hold():
    return held_stdout.HELD_LINES.set([])

#lets everything the batch printed out in one block, reply sent or not
def release(token) -> None:
    lines: list[str] | None = held_stdout.HELD_LINES.get()

    if(not lines):
        lines = []

    held_stdout.HELD_LINES.reset(token)

    with held_stdout.PRINT_LOCK:
        held_stdout.TERMINAL.write("".join(lines))

        held_stdout.TERMINAL.flush()

#new worker threads miss the batchs held lines, so they run in a copy of this context
def batch_context():
    return copy_context()
