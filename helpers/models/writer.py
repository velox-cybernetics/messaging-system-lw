#IMPORTS

import importlib
import inspect
from contextvars import ContextVar
from pathlib import Path

from helpers.state import dashboard


#GLOBALS

#prompt files go by their path from the project folder, same as github and the dashboard
PROJECT_FOLDER = Path(__file__).resolve().parents[2]

PROMPTS_FOLDER = PROJECT_FOLDER / "src" / "prompts"

#asked again only rewords one ask in someone elses reply, so it never takes the credit
REWORDERS: list[str] = ["src/prompts/asked_again/generator.py"]

#whos writing the current chains reply and from what, None outside a chain
NOTE = ContextVar("note", default=None)


#GENERATORS

#every prompt file that builds its prompt alone, ones that need parts handed in don't count
def find_generators() -> list[tuple[str, str]]:
    generators: list[tuple[str, str]] = []

    for path in sorted(PROMPTS_FOLDER.rglob("*.py")):
        file: str = path.relative_to(PROJECT_FOLDER).as_posix()

        module = importlib.import_module(file.removesuffix(".py").replace("/", "."))

        prompt = getattr(module, "prompt", None)

        if(not hasattr(module, "examples") or prompt is None or len(inspect.signature(prompt).parameters) > 0):
            continue

        generators.append((prompt(), file))

    return generators

#each generators prompt with its file
GENERATORS: list[tuple[str, str]] = find_generators()

#the generator whose prompt the system prompt starts with, a regen counts as its generator
def generator_file(system_prompt: str) -> str:
    found_file: str = ""

    found_length: int = 0

    for prompt_text, file in GENERATORS:
        #the longest match wins, so a prompt that happens to start another one can't steal it
        if(system_prompt.startswith(prompt_text) and len(prompt_text) > found_length):
            found_file = file

            found_length = len(prompt_text)

    return found_file


#NOTES

#every try starts with a clean note, so a try that broke halfway leaves nothing behind
def start_note() -> None:
    NOTE.set({})

#a regen of the same generator keeps the first input, a different generator takes over
def note_generator(system_prompt: str, user_text: str) -> None:
    note: dict[str, str] | None = NOTE.get()

    #a reply written outside a chain never goes to the dashboard
    if(note is None):
        return

    file: str = generator_file(system_prompt)

    if(file == "" or file in REWORDERS or file == note.get("generator")):
        return

    NOTE.set({"generator": file, "input": user_text})

#sends the note with the reply, an empty reply leaves the last real one alone
def save_note(id: str, reply: str) -> None:
    note: dict[str, str] | None = NOTE.get()

    NOTE.set(None)

    if(note is None or reply.strip() == ""):
        return

    dashboard.note_writer(id, note.get("generator", ""), note.get("input", ""), reply)
