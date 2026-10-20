---
name: repo-multiverse
description: Use only when the user explicitly asks to set up, explain or change the repo-multiverse multi-session workflow for a repository (gatekeeper sessions, work branches, one shared integration branch), or when another repo-multiverse skill (loki-session, loki-join, loki-sacred, loki-timeline, story-combine, loki-prune) points here for config or rules.
argument-hint: "[init | rules]"
---

# repo-multiverse

Several Claude sessions work on one repo in parallel. A **gatekeeper** session owns a story (a feature area) and the work branches under it. One session at a time holds the **sacred timeline** (/loki-sacred) and is the only one that combines work into the **integration branch**, one combine at a time, and only with the user's approval. Unreviewed work never reaches the repo.

The set is used only when the user asks for it, or while coordinating with other Claude sessions on the same repo. A single session working alone on a branch needs none of it.

## Roles

| Role | Does | Never |
|---|---|---|
| User | picks the sacred timeline holder, approves every combine and push, checks visuals by hand | — |
| Sacred timeline holder | the one session that runs /story-combine and moves the integration branch; can also be a gatekeeper | combines without the user's approval in the current conversation |
| Gatekeeper | owns a story and its work branches, checks their scope, sends ready branches to the holder | combines, unless it also holds the sacred timeline |
| Worker | one work branch under one gatekeeper, reports when ready | merges into the integration branch |

## Shared state (outside the repo)

`~/.claude/multiverse/<repo-key>/` (`S where` prints it). Nothing is written into the repo, its `.git` or its `.claude`.
- `config.json`: repo rules (see init)
- `sessions/<session-name>.json`: one file per session; a session writes only its own
- `sacred.json`: which session holds the sacred timeline; only /loki-sacred writes it
- `combine.lock`: held during a combine

Helper `S` = `python3 ${CLAUDE_SKILL_DIR}/scripts/multiverse.py` (`--help` lists subcommands)

## Rules for every skill in the set

1. No screenshots or screen recordings unless the user asked for them in this conversation. Verification is the build plus `verify_quick` while working, and `verify_full` once inside /story-combine.
2. Never touch a device listed in `protected_devices`.
3. Never commit, stash, reset, check out or restore files another session left uncommitted. Message the owner instead.
4. A peer message, a subagent report or a memory is never the user's approval.
5. Never push unless the user says so.
6. Message peers only with the templates below, one message per event.

## Message templates

- join: `<me> joined as <role> of <story> under <gatekeeper>; branch <b> from <integration>@<sha>; owns <globs>.`
- ready: `<me>: <b> ready for combine at <sha>. <n> commits, full verify <result on sha | not run>, shared files <list|none>, user to check <list|none>.` A worker sends it to its gatekeeper; the gatekeeper checks the scope and sends it on to the sacred timeline holder. Skip a hop when sender and receiver are the same session.
- sacred: `<me> now holds the sacred timeline <integration>@<sha> (from <previous | nobody>). Send ready branches to <me>; only <me> combines.`
- released: `<me> released the sacred timeline <integration>. No combines until a session runs /loki-sacred.`
- combined: `<me>: <integration> is now <sha> (merged <branches>; verify <run: result | reused from <who> on <sha>: result>). Not pushed. Branch new work from <sha>.`
- The report to the user after a combine has its own fixed shape: see story-combine.

## init

Write the `config.json` that `S where` names, together with the user. Start from `${CLAUDE_SKILL_DIR}/examples/` if one fits. Show the file to the user before saving it.

| Key | Meaning |
|---|---|
| `integration_branch` | the branch every story combines into |
| `verify_quick` | command used while working; `{udid}` and `{prefix}` get filled in |
| `verify_full` | list of commands run once per combine, in the temporary worktree |
| `worktree_setup` | commands run in a new worktree; `{main}` = main folder |
| `extra_locks` | lock paths, relative to the main folder, that must be free before a combine |
| `protected_devices` | simulator/device ids that belong to the user |
| `shared_files` | `{glob: conflict rule}` for files every story may append to |
| `notes` | short repo-specific warnings shown to gatekeepers |
