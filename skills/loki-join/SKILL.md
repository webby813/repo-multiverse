---
name: loki-join
description: Use only when the user asks this session to join the repo-multiverse workflow (work under a main timeline), to register or update one of its work branches, or to hand a branch in as ready; or when its main timeline assigns it a branch; or when the user types /loki-join.
argument-hint: "[<main timeline name>] | branch <name> [ready]"
---

# loki-join

`S` = `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py`

| Ask | Run |
|---|---|
| join | `S join [--story "<task>"]` |
| join a named main timeline | `S join --to <name> [--story "<task>"]` |
| add a work branch | create its worktree first (below), then `S branch add <branch>` |
| hand a branch in | `S branch status <branch> --status ready --note "<summary>"`, then send the ready template to your main timeline |

## Join outcomes

- `joined <X> as a worker`: send the join template to X.
- exit 4 `CHOOSE`: several main timelines are live. Ask the user which one, then run `S join --to <name>`.
- `is now a main timeline`: no other main timeline was live, so this session became one. Tell the user, and follow /loki-sacred from step 2.
- exit 4 `NOT A TIMELINE`: tell the user; that session becomes one with /loki-sacred.
- A `/rename` line: pass it on to the user.

## Working as a worker

- A new branch starts from the integration branch tip in its own worktree, never in the main folder: `git worktree add -b <branch> <path> <integration>`, then the config's `worktree_setup` there.
- Keep the branch to the task. Unrelated edits (IDE or scheme files, debug switches, changed defaults, stray files) get the branch sent back.
- Commit in small focused commits.
- Before handing in: rebase onto the integration branch tip (only if the branch was never pushed), run the verify once on the final commit, and put the result and its sha in the ready message so the combine can reuse it.
- Then wait for your main timeline's reply. A worker never merges into the integration branch.
- When the combined message says your branch is in and nothing else is left to do, tell the user that /loki-leave wraps this session up.

No config.json yet: point the user to /repo-multiverse init. Template wording and the shared rules: `${CLAUDE_SKILL_DIR}/../repo-multiverse/SKILL.md`.
