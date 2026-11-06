#**********IMPORTS**********
#python's module loading and file paths, the memory that keeps each reply chain's note, and the dashboard the note goes to
import importlib
import inspect
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from types import ModuleType

from helpers.state import dashboard



#**********GLOBALS**********
#where the prompt files are, the one generator that only rewords another's reply, and the note on the reply being written


#PROMPT FOLDERS
#a prompt file goes by its path from the project folder, the way github and the dashboard name it ("src/prompts/pricing/generator.py")
PROJECT_FOLDER: Path = Path(__file__).resolve().parents[2]

PROMPTS_FOLDER: Path = PROJECT_FOLDER / "src" / "prompts"


#REWORDERS
#asked again only rewords one ask in a reply another generator wrote, so the reply stays that generator's
REWORDERS: list[str] = ["src/prompts/asked_again/generator.py"]


#NOTE
#the generator that wrote the reply a chain is writing and what it was handed, None outside a chain so nothing else gets noted
NOTE: ContextVar[dict[str, str] | None] = ContextVar("note", default=None)



#**********GENERATORS**********
#every prompt file with examples of its own, known by the prompt it builds, found once when the bot starts


#FIND GENERATORS
#a prompt built from parts handed to it, like the shared interrogator one, is never a generator on its own
def find_generators() -> list[tuple[str, str]]:
    generators: list[tuple[str, str]] = []

    for path in sorted(PROMPTS_FOLDER.rglob("*.py")):
        file: str = path.relative_to(PROJECT_FOLDER).as_posix()

        module: ModuleType = importlib.import_module(file.removesuffix(".py").replace("/", "."))

        prompt: Callable[..., str] | None = getattr(module, "prompt", None)

        if(not hasattr(module, "examples") or prompt is None or len(inspect.signature(prompt).parameters) > 0):
            continue

        generators.append((prompt(), file))

    return generators


#GENERATORS
#each generator's prompt with its file
GENERATORS: list[tuple[str, str]] = find_generators()


#GENERATOR FILE
#the file whose prompt the system prompt starts with, a regen's prompt is its generator's with the fixes on the end, "" when it's no generator's
def generator_file(system_prompt: str) -> str:
    found_file: str = ""

    found_length: int = 0

    for prompt_text, file in GENERATORS:
        #the longest one wins, so a prompt that happens to start another one never takes its place
        if(system_prompt.startswith(prompt_text) and len(prompt_text) > found_length):
            found_file = file

            found_length = len(prompt_text)

    return found_file



#**********NOTES**********
#which generator wrote a chain's reply, noted as it's written and handed to the dashboard once the chain is done, so an upvote there knows where its example goes


#START NOTE
#every try of a chain starts with nothing noted, so a try that broke halfway never leaves its generator behind
def start_note() -> None:
    NOTE.set({})


#NOTE GENERATOR
#the first generator keeps its input, so a regen fixing its draft never takes its place, and a different one after it wrote the reply on top of its answer
def note_generator(system_prompt: str, user_text: str) -> None:
    note: dict[str, str] | None = NOTE.get()

    #a reply written outside a chain never goes to the dashboard
    if(note is None):
        return

    file: str = generator_file(system_prompt)

    if(file == "" or file in REWORDERS or file == note.get("generator")):
        return

    NOTE.set({"generator": file, "input": user_text})


#SAVE NOTE
#an empty reply goes nowhere, so the note on the last one that did stays, and a reply only the code wrote goes with no generator
def save_note(id: str, reply: str) -> None:
    note: dict[str, str] | None = NOTE.get()

    NOTE.set(None)

    if(note is None or reply.strip() == ""):
        return

    dashboard.note_writer(id, note.get("generator", ""), note.get("input", ""), reply)
