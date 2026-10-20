---
name: loki-timeline
description: Use only when the user asks to see how collaborating sessions are organised (gatekeeper sessions and the work branches under each), types /loki-timeline, or right before planning a /story-combine.
argument-hint: "[--days N]"
---

# loki-timeline

Read-only tree: integration branch → gatekeeper sessions → their work branches, numbered.

1. Run `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py timeline $ARGUMENTS`.
2. Show the tree as printed. The first line names the sacred timeline holder, the only session that combines. Legend: `+a/-b` = commits ahead/behind the integration branch; `merged` = already contained; `wt` = worktree; status = working / ready / blocked / merged; `gone` = the session has ended.
3. Add at most three lines:
   - branches marked `ready`: give their numbers as /story-combine candidates
   - branches far behind the integration branch
   - the `unclaimed` section: work with no gatekeeper, which could reach the repo unreviewed. Ask the user who owns it.
   - nobody holds the sacred timeline, or its holder is gone: /loki-sacred in the session that should combine

The numbers are positions in this listing and can shift when registrations change. /story-combine resolves them again before it acts.

Do not message anyone, write files, or change git state.
