---
name: loki-leave
description: Use only when the user asks this session to leave the repo-multiverse workflow or wrap up its part in it (its work is merged or dropped), or types /loki-leave.
---

# loki-leave

Ends this session's part in the multiverse and leaves no abandoned test environment on the user's machine. Its registration goes, and so do the worktrees of its merged branches. Branches are kept.

`S` = `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py`

1. Run `S leave`. It removes this session's registration and lists the branches it held, each `merged` or `not merged`, with its worktree.
2. For each `merged` branch with a worktree: `git worktree remove <path>`. Never `--force`; if git refuses because of uncommitted files, leave it and tell the user. Skip the worktree this session itself runs in; it can go once the session is closed.
3. Remove every abandoned test environment this session made. One counts when all three hold: this session made it; it served only testing, apart from the user's own working setup (its own simulator or emulator, a test container or database, test data seeded into those); the user didn't ask to keep it. Look at each before removing it. Never touch the user's own devices and data, the main folder, branches, or anything another session made; when it's unclear whose something is, ask the user.
4. A `not merged` branch stays as it is, worktree included, and shows under unclaimed worktrees in /loki-timeline. Name it to the user.
5. A worker sends the left template to its main timeline. If the script listed workers left without a main timeline (this session was one), send each of them one line asking them to run /loki-join again.
6. Tell the user in one or two lines what was removed and what stayed.

Template wording and the shared rules: `${CLAUDE_SKILL_DIR}/../repo-multiverse/SKILL.md`.
