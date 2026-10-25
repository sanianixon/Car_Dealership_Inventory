#!/usr/bin/env python3
"""Rebuild PROMPTS.md from the Claude Code session transcripts.

Run from the repository root:

    python3 docs/make_prompts.py > PROMPTS.md

This is a format conversion, not an edit. Every message is reproduced exactly
as it was written; nothing is paraphrased, shortened, reordered or summarised.
The script is committed so that anyone can re-run it against the same
transcripts and confirm that.

What it drops, and why, is stated in the generated file's own header: tool
output, the CLI's injected system blocks, and the model's private reasoning
blocks. None of those is chat.

Transcripts live in ~/.claude/projects/<slugified-cwd>/<session-id>.jsonl and
are written by Claude Code, not by this project.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")

SESSIONS = [
    {
        "heading": "Session 2 — Context review (Claude Code)",
        "intro": "Opens with the full text of session 1, pasted in by hand.",
        "path": f"{HOME}/.claude/projects/-Users-sania/"
                "6ccacb33-7822-461a-931a-a1bdd820e151.jsonl",
    },
    {
        "heading": "Session 3 — Implementation (Claude Code)",
        "intro": "The build itself: planning, then every phase of the work.",
        "path": f"{HOME}/.claude/projects/-Users-sania-Desktop-incubyte/"
                "da845000-75ff-441b-8bf4-8d8253706fd5.jsonl",
    },
]

SHARE_LINK = "https://claude.ai/share/ac1545f4-8f98-4ebc-9e7a-1a2909b77819"

SYSTEM_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
IDE_SELECTION = re.compile(r"<ide_selection>.*?</ide_selection>", re.DOTALL)


def describe_tool(block):
    """One line naming a tool call, standing in for its omitted output."""
    name = block.get("name", "tool")
    args = block.get("input") or {}
    hint = ""
    if name == "Bash":
        hint = args.get("description") or args.get("command", "")[:80]
    elif name in ("Read", "Write", "Edit"):
        hint = args.get("file_path", "")
    elif name == "AskUserQuestion":
        questions = args.get("questions") or []
        hint = questions[0].get("question", "") if questions else ""
    elif name == "ToolSearch":
        hint = args.get("query", "")
    hint = " ".join(str(hint).split())
    return f"_[tool: {name}{' — ' + hint if hint else ''}]_"


def clean(text):
    """Strip the blocks the CLI injects into a turn; leave everything else."""
    return IDE_SELECTION.sub("", SYSTEM_REMINDER.sub("", text)).strip()


def turns(path):
    """Yield (role, timestamp, markdown) for each real conversational turn."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("type") not in ("user", "assistant") or record.get("isMeta"):
                continue

            message = record.get("message") or {}
            if message.get("role") not in ("user", "assistant"):
                continue

            content = message.get("content")
            blocks = content if isinstance(content, list) else [
                {"type": "text", "text": str(content)}
            ]

            parts = []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text = clean(block.get("text") or "")
                    if text:
                        parts.append(text)
                elif block.get("type") == "tool_use":
                    parts.append(describe_tool(block))
                # tool_result and thinking blocks are dropped; see the header.

            body = "\n\n".join(parts).strip()
            if body:
                stamp = (record.get("timestamp") or "")[:19].replace("T", " ")
                yield message["role"], stamp, body


def header():
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""# AI Prompt Logs

Required by the kata brief: the raw, unedited AI conversations behind this
project. Three sessions, in order.

| # | Session | Where | What happened |
| --- | --- | --- | --- |
| 1 | Planning | claude.ai | Chose the stack, drafted the API contract and the TDD order |
| 2 | Context review | Claude Code | Read session 1 back in, agreed how to work |
| 3 | Implementation | Claude Code | Everything in this repository |

Session 1 was also shared as a public link:
<{SHARE_LINK}>

That page is rendered by JavaScript behind a bot check, so it could not be read
programmatically. Its full text was therefore pasted into session 2 and appears
verbatim below, which is why session 2 opens with a long quotation.

## What is and is not in this file

Every message is reproduced **exactly as written**. Nothing is paraphrased,
shortened, reordered or summarised, and no wording has been altered. This file
is generated by [`docs/make_prompts.py`](docs/make_prompts.py), which is
committed so the conversion can be re-run and checked.

Left out, with the reason:

- **Tool output.** Each tool call appears as a one-line marker such as
  `_[tool: Bash — Run the test suite]_`. The commands and their results are not
  chat, and including them ran to roughly 110 pages of terminal output. The work
  they produced is in this repository's commit history, which records it better.
- **Harness internals.** Editor state, file snapshots and the automatic
  `<system-reminder>` blocks the CLI injects into each turn. Neither participant
  wrote these.
- **Assistant reasoning blocks.** The private "thinking" the model does before
  replying.
- **Personal data.** An unrelated email address and a listing of my home
  directory appeared in tool output captured by the transcript. They are absent
  because the tool output is absent; none of it concerned this project.

The conversation itself is complete and unedited.

Generated {generated}. The final exchange of the last session is necessarily
absent, since the transcript is still being written while this file is produced.

"""


def main():
    out = [header()]
    for session in SESSIONS:
        if not os.path.exists(session["path"]):
            print(f"missing transcript: {session['path']}", file=sys.stderr)
            continue
        out.append(f"## {session['heading']}\n\n{session['intro']}\n")
        for role, stamp, body in turns(session["path"]):
            who = "Sania" if role == "user" else "Claude"
            out.append(f"### {who}" + (f"  ·  {stamp} UTC" if stamp else ""))
            out.append("")
            out.append(body)
            out.append("")
        out.append("\n---\n")
    print("\n".join(out[:-1]))


if __name__ == "__main__":
    main()
