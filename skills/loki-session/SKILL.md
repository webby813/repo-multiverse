---
name: loki-session
description: Use only when the user asks which Claude sessions are active on this repo, types /loki-session, or when coordinating with other sessions and you need to know who is live before messaging or combining.
argument-hint: "[--all]"
---

# loki-session

Read-only list of live Claude sessions on this repo, with their role in the multiverse.

1. Run `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py sessions $ARGUMENTS`. `--all` includes sessions on other repos.
2. Show the table as printed; `*` marks this session. Then add at most three lines:
   - sessions shown `(not joined)` that work on this repo: the user can ask them to run /loki-join
   - stale registrations: /loki-prune removes them
   - sessions idle for days: the user can close them to free resources
   - nobody holds the sacred timeline, or its holder is gone: no combine can run until a session runs /loki-sacred
3. The NAME column is what SendMessage takes. If the script fails, ListAgents shows the same names.

Do not message anyone, write files, or change git state.
