---
name: loki-join
description: Use only when the user asks this session to join, change its role in, or leave the repo-multiverse workflow, to register or update one of its work branches, or when its gatekeeper assigns it a branch.
argument-hint: "gatekeeper <story> | worker <gatekeeper> <story> | branch <name> [ready] | leave"
---

# loki-join

Registers this session in `~/.claude/multiverse/<repo-key>/sessions/<name>.json`, outside the repo. It writes only this session's own file.

`S` = `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py`

| Ask | Run |
|---|---|
| join as gatekeeper | `S join --role gatekeeper --story "<story>" --sim <udid> --owns "<glob>"` (repeat `--owns`) |
| join as worker | `S join --role worker --gatekeeper <name> --story "<story>" --sim <udid>` |
| add a work branch | create the worktree first (see below), then `S branch add <branch>` |
| branch is ready | `S branch status <branch> --status ready --note "<summary>"`, then send the ready template: a worker to its gatekeeper, a gatekeeper to the sacred timeline holder (`S sacred status`). Skip it when the receiver is this session |
| leave | `S leave` |

- New work branches start from the integration branch tip, each in its own worktree, never in the main folder: `git worktree add -b <branch> <path> <integration>`, then run the config's `worktree_setup` commands there.
- `--owns` globs are the paths this story may change. /story-combine flags any file outside them. Ask the user when unsure.
- `--sim` must be your own simulator. The script refuses protected devices.
- A worker sends the join template to its gatekeeper (SendMessage; names from /loki-session). A gatekeeper sends nothing.
- No config.json yet: stop and point the user to /repo-multiverse init.
- Template wording and the shared rules: `${CLAUDE_SKILL_DIR}/../repo-multiverse/SKILL.md`.
