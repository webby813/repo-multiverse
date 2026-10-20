---
name: loki-prune
description: Use only when the user asks to clean up finished collaboration leftovers (merged or prunable worktrees, temporary combine worktrees, registrations of ended sessions, scratch folders of ended sessions), or types /loki-prune.
argument-hint: "[--scratch]"
---

# loki-prune

1. Run `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py prune-plan $ARGUMENTS`. It deletes nothing; it prints commands, each with its reason. `--scratch` adds scratch folders of ended sessions, with sizes.
2. Show the list grouped (worktrees / registrations / scratch) and ask the user which groups to run.
3. Run only what the user approved. `git worktree remove` refuses a dirty worktree: report it and never add `--force`.

Never delete branches, never touch the main folder, and never remove the worktree or scratch folder of a live session.
