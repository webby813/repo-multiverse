---
name: loki-sacred
description: Use only when the user asks this session to become, or stop being, a main timeline in the repo-multiverse workflow (the session that looks after other sessions, reviews their work and combines it into the integration branch), or types /loki-sacred.
argument-hint: "[off] [story]"
---

# loki-sacred

Makes this session a main timeline right away. There are no checks and no questions: several main timelines can exist, and the user decides where one runs.

`S` = `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py`

| Argument | Run |
|---|---|
| (none) or a story | `S sacred` or `S sacred --story "<story>"` |
| `off` | `S sacred off` |

## Become a main timeline

1. Run it. The script prints the integration branch tip and the other live main timelines.
2. Send the timeline template once to each other main timeline it printed. With none, send nothing.
3. Tell the user in one or two lines: this session is now a main timeline of `<integration>` at `<sha>`, plus the other main timelines if any. Pass on the `/rename` line if the script printed one. With no config yet, add that /repo-multiverse init is needed before the first combine.

## Stop being one

`S sacred off`. If it lists workers left without a main timeline, send each of them one line asking them to run /loki-join again, and tell the user.

## While a main timeline

- Workers hand in with the ready template. Review each hand-in before it is combined; send it back with the returned template when it strays from its task.
- A worker's question template goes to the user in your next reply, under the worker's name. Send the user's answer back with the answer template.
- Combine only through /story-combine, and only what the user asked for in this conversation. The rhythm is the user's: each hand-in as it arrives, or several at once. /story-combine takes one branch or many.
- A main timeline can also do work itself on its own branches (/loki-join branch …).
- Answer the user's questions about the code from `facts/` or a research subagent (shared rules 9 and 10), so this long-lived session doesn't fill up with code it read.

Template wording and the shared rules: `${CLAUDE_SKILL_DIR}/../repo-multiverse/SKILL.md`.
