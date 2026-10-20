---
name: loki-timeline
description: Use only when the user asks to see how collaborating sessions are organised (main timelines, the workers under each and their work branches), types /loki-timeline, or right before planning a /story-combine.
---

# loki-timeline

Read-only tree: integration branch → main timelines → their own branches and their workers → the workers' branches, with branches numbered.

1. Run `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py timeline`.
2. Show the tree as printed. Legend: `+a/-b` = commits ahead/behind the integration branch; `merged` = already contained; `wt` = worktree; status = working / ready / blocked / merged; `gone` = the session has ended.
3. Add at most three lines:
   - branches marked `ready`: give their numbers as /story-combine candidates for their main timeline
   - branches far behind the integration branch
   - `workers without a main timeline`: they can run /loki-join again
   - `unclaimed worktrees`: work nobody registered, which could reach the repo unreviewed. Ask the user who owns it.

The numbers are positions in this listing and shift when registrations change. /story-combine reads them again before it acts.

Do not message anyone, write files, or change git state.
