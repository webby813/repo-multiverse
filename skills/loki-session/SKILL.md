---
name: loki-session
description: Use only when the user asks which Claude sessions are active on this repo, types /loki-session, or when coordinating with other sessions and you need to know who is live before messaging or combining.
argument-hint: "[--all | forget]"
---

# loki-session

Read-only list of live Claude sessions on this repo, with their place in the multiverse.

1. Run `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py sessions $ARGUMENTS`. `--all` includes sessions on other repos. With the argument `forget`, run `multiverse.py forget` instead, report what it removed, and stop.
2. Show the table as printed; `*` marks this session. Then add at most three lines:
   - sessions on this repo shown `(not joined)`: they can run /loki-join
   - no main timeline: /loki-sacred in the session that should look after the others
   - registrations of ended sessions: `/loki-session forget` clears them
   - sessions idle for days: the user can close them to free resources
3. The NAME column is what SendMessage takes. If the script fails, ListAgents shows the same names.

`forget` removes only the registrations of sessions that have ended. Otherwise do not message anyone, write files, or change git state.
