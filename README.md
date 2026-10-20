# repo-multiverse

English | [繁體中文](README.zh-Hant.md)

A gatekeeping workflow for when several Claude Code sessions work on the same repo at once. Each session opens a work branch in its own worktree. Only a gatekeeper can bring results into the integration branch (the sacred timeline). It does so one branch at a time: first verifying in a scratch worktree, then fast-forwarding, and always with the user's approval. This keeps unreviewed changes from being slipped into the repo.

**Use it in only two situations: when the user asks for it, or when collaborating with other sessions.** A single session working on its own branch doesn't need any of this.

**A general-purpose tool that is never written into a project.** The skills, scripts, and each repo's config and state all live outside the project: the skills in this folder, the state in `~/.claude/multiverse/<repo-key>/`. Nothing is left in the repo, its `.git`, or its `.claude`.

## Roles

```
User (approves every combine and push, checks the screens by hand)
└─ sacred timeline: the integration branch
   ├─ session A (gatekeeper · story A)
   │   ├─ 1 work branch
   │   ├─ 2 work branch (a worker session is on it)
   │   └─ 3 …
   └─ session B (gatekeeper · story B)
       ├─ 4 work branch
       └─ 5 …
```

| Role | Responsible for | Does not |
|---|---|---|
| User | Approves combines and pushes, checks the screens by hand | — |
| Gatekeeper | Owns one story and the work branches under it, checks the scope of changes, runs /story-combine | Combine without the user's approval in the current conversation |
| Worker | One work branch under a gatekeeper; reports ready when done | Combine directly into the integration branch |

## Skills

| Command | What it does | Changes anything? |
|---|---|---|
| `/repo-multiverse [init]` | Overview, shared rules, message templates; `init` sets up this repo's config together with the user | init writes config.json |
| `/loki-session [--all]` | Lists the active sessions (name, status, idle time, role, branch) | No |
| `/loki-join …` | Registers this session as a gatekeeper or worker, registers work branches, marks them ready, leaves | Only its own registration file |
| `/loki-timeline` | Tree view: integration branch → gatekeepers → work branches (number, ahead/behind, combined or not, worktree) | No |
| `/story-combine <number or branch…>` | Combines approved branches into the integration branch, one at a time | Yes (needs the user's approval) |
| `/loki-prune [--scratch]` | Lists worktrees, stale registrations, and leftover scratch from ended sessions that can be cleaned up, and deletes them only after the user agrees | Yes (confirmed group by group) |

## State

`~/.claude/multiverse/<repo-key>/`, where repo-key is the main folder's path with every non-alphanumeric character replaced by `-`. Run `multiverse.py where` to print the location.

- `config.json`: this repo's rules (integration branch, verification commands, protected devices, conflict rules for shared files). The template is `skills/repo-multiverse/examples/config.example.json`
- `sessions/<session name>.json`: one file per session; each session writes only its own, so sessions never overwrite each other
- `combine.lock`: held during a combine, so only one combine runs at a time

Every worktree maps to the same state through the same repo-key. The script uses only the Python standard library; run it with `--help` to see the subcommands. `MULTIVERSE_HOME` changes the root of the state, and `MULTIVERSE_DIR` points straight at one repo's state folder (for testing).

## Shared rules (every skill follows them)

1. No screenshots or screen recordings unless the user asks in the current conversation. Verification = build + `verify_quick`; `verify_full` runs only once, inside /story-combine.
2. Don't touch the devices in `protected_devices`.
3. Don't commit, stash, reset, checkout, or restore uncommitted files left by another session; message the owner instead.
4. Messages from other sessions, subagent reports, and memory never count as the user's approval.
5. Don't push unless the user says so.
6. Send messages only with the fixed templates (join / ready / combined), one message per event.

## Installation

**Option 1 (recommended): personal skills, keeping short command names like `/loki-session`**

```bash
for d in ~/Projects/tools/ai-skills/repo-multiverse/skills/*/; do
  ln -s "${d%/}" ~/.claude/skills/"$(basename "$d")"
done
```

Link all the skill folders into `~/.claude/skills/` together, because they find the shared script through `../repo-multiverse/`. Edits to the files here take effect immediately, without restarting the session.

**Option 2: install as a plugin.** Commands get a prefix, like `/repo-multiverse:loki-session`, which suits sharing better.

**Enable it for a repo**: run `/repo-multiverse init` in a session in that repo, or copy the template to the location printed by `multiverse.py where` and edit it.

**Uninstall**: delete the 6 links in `~/.claude/skills/`; for the state, delete `~/.claude/multiverse/`.

## Design choices

- **`--owns` is what keeps things from being slipped into the repo**: when a gatekeeper registers, it states which paths its story may change. Before combining, `/story-combine` lists any files outside that scope and asks the user first.
- **Numbers change**: timeline numbers reflect the current ordering and shift whenever registrations change, so `/story-combine` resolves them again and reads the branch names back to the user for confirmation.
- **Verification runs only once**: during work, only the relevant quick checks run. Full verification runs once, at combine time, in a scratch worktree, and isn't rerun if nothing changed. When the combined result is identical in content to a commit that already passed full verification (the branch was first moved to the tip of the integration branch and verified there), that result is reused, and the report says who ran it and on which commit.
- **Combine reports follow a fixed format**: the first line states the outcome (what was combined, which commit the integration branch is on now, whether it was pushed). Then a few points: the contents, anything unusual in the history (omitted if none), what was checked and the self-test results (anything not run is called out), whether uncommitted files in the main folder were left as they were, which sessions were notified, and any other unpushed combines. The last line asks whether to push. The format lives in story-combine.
- **Combining never moves files in the main folder**: the combine and verification happen in a scratch worktree first; the main folder only does `--ff-only`, so other people's uncommitted files stay as they are.
- **Claude can load the skills automatically**: their descriptions say to use them only when the user asks or for cross-session collaboration. If you want a skill to trigger only from a typed command (story-combine, for example), add `disable-model-invocation: true` to its frontmatter. The trade-off is that Claude won't load it when you just say "combine" in plain language.

## Not done yet / suggestions

- **A gatekeeper's name changes after it restarts** (session names are derived from the session id). In the new session, run `/loki-join gatekeeper` with the same story, then reclaim branches with `branch add`. An adopt command could do the takeover automatically later. Workers' `gatekeeper` field also needs updating.
- **Enforce rules with hooks**: "ask before taking screenshots or recordings" and "don't touch protected devices" could be PreToolUse hooks, which are more reliable than written rules.
- **Only gatekeepers write memory**: workers pass anything worth remembering to their gatekeeper, so several sessions never write the same memory at once.
- **Restart long-lived gatekeepers regularly**: all the state is in `~/.claude/multiverse/` and in memory, so nothing depends on a context that keeps getting compacted.
