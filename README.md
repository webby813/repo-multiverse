# repo-multiverse

English | [繁體中文](README.zh-Hant.md)

> Let several Claude Code sessions build in the same repo in parallel, while one clean main line stays protected.

In Marvel's *Loki* series, the Time Variance Authority (TVA) guards a single Sacred Timeline. Whenever a variant makes history branch off into a new timeline, the TVA tracks it down and decides whether it gets pruned or stays. In the end, only the one sitting at the end of time decides which timelines get to exist.

Running several AI sessions on the same repo is much the same. Each session is a variant, growing a new timeline on its own branch. Without someone keeping watch, unreviewed changes can flow straight into the main line, overwrite each other, or get pushed without anyone verifying them.

repo-multiverse borrows that world to give Claude Code a gatekeeping workflow for multiple sessions. Each session works in its own worktree and branch. Only one session at a time sits on the sacred timeline, and only it can combine work into the integration branch. Every combine is verified first and always needs your approval. That is why its commands start with `loki-`.

## The show, mapped

| *Loki* | repo-multiverse |
|---|---|
| Sacred Timeline | The integration branch, where all work ends up |
| Variant | A Claude Code session working in parallel |
| A branched timeline | A session's work branch, each in its own worktree |
| TVA agent | Gatekeeper: owns a story and reviews the scope of the branches under it |
| The throne at the end of time | Sacred timeline holder: the only session that can combine (`/loki-sacred`) |
| Nexus event | The checks before a combine: files outside the owned paths, overlaps with other branches, files someone left uncommitted |
| Pruning | Cleaning up merged worktrees and stale registrations (`/loki-prune`) |

## Core concepts

### Roles

```
You (pick the holder, approve every combine and push)
└─ sacred timeline: the integration branch ← holder session (the only one that combines)
   ├─ gatekeeper A (story A)
   │   ├─ work branch (done by the gatekeeper)
   │   └─ work branch (done by a worker session)
   └─ gatekeeper B (story B)
       └─ work branch
```

| Role | Does |
|---|---|
| You (the user) | Decide which session holds the sacred timeline; approve every combine and push |
| Sacred timeline holder | One at a time; the only session that runs `/story-combine` and moves the integration branch. It can also be a gatekeeper |
| Gatekeeper | Owns a story (one feature area) and its work branches, checks that changes stay in scope, then hands them to the holder |
| Worker | Works on one branch under a gatekeeper and reports ready when done |

### How a combine goes

1. A worker or gatekeeper opens a work branch in its own worktree, starting from the latest commit of the integration branch.
2. When done, it marks the branch ready. The gatekeeper checks the scope and passes it on to the holder.
3. The holder confirms with you which branches to combine this time.
4. Each branch is merged in a scratch worktree and goes through full verification. Only after it passes does the integration branch fast-forward.
5. The holder reports the result and notifies the other sessions. Whether to push is up to you.

### What it guarantees

- **Only one session can combine**: the holder is recorded in a state file, and the script refuses any other session that tries to combine. It doesn't rely on the AI behaving.
- **One combine at a time**: a lock is held during a combine, so two never run at once.
- **Verify before moving**: merging and verification happen in a scratch worktree, and the main folder only fast-forwards, so other people's uncommitted files are never touched.
- **Changes stay in scope**: a gatekeeper registers which paths its story may change. Before a combine, files outside them are listed and you are asked first.
- **Only your word counts**: messages from other sessions and subagent reports never count as approval. Without your consent, nothing is combined or pushed.
- **Nothing written into your project**: config and state live in `~/.claude/multiverse/<repo-key>/`. Nothing is left in the repo, its `.git` or its `.claude`.

## When to use it

Good fit:

- Two or more Claude Code sessions working on different features in the same repo at once
- You want AI sessions to split the work in parallel, but you decide what reaches the main line
- You need a local integration branch that stays clean and only takes verified, approved changes

Not needed:

- A single session doing the work: just work on a branch
- Replacing PR review or CI: repo-multiverse handles local integration before you push; after that, your usual process applies
- Collaborating across computers: it only sees sessions on the same machine

These skills only activate when you ask for them or when sessions need to coordinate, so they stay out of a single session's everyday work.

## Requirements

- Claude Code
- macOS or Linux
- Git 2.31 or later
- Python 3.9 or later (standard library only)
- Node.js (only for installing with npx)

## Installation

### With npx (recommended)

```bash
npx skills add webby813/repo-multiverse -g -a claude-code --skill '*'
```

This uses the open-source [skills](https://github.com/vercel-labs/skills) CLI to install all 7 skills into `~/.claude/skills/`. New Claude Code sessions can then use `/loki-session` and the rest.

- `-g`: installs at user level, so nothing is written into the project you are in
- `--skill '*'`: required. The skills share the script in `repo-multiverse`, so they must be installed together

To update later:

```bash
npx skills update -g
```

### Manual installation

```bash
git clone https://github.com/webby813/repo-multiverse.git
cd repo-multiverse
mkdir -p ~/.claude/skills
for d in "$PWD"/skills/*/; do
  ln -s "${d%/}" ~/.claude/skills/"$(basename "$d")"
done
```

Symlinks take effect right after a `git pull`, which suits anyone who wants to modify the skills. Here too, link all the folders together.

### Enable it for a repo

After installing, open a Claude Code session in the repo you want to use it in and run:

```
/repo-multiverse init
```

Claude writes this repo's config with you (integration branch, verification commands and so on), stored outside the repo. A template is in [`skills/repo-multiverse/examples/config.example.json`](skills/repo-multiverse/examples/config.example.json).

## Quick start

```
/repo-multiverse init                   # once: create this repo's config
/loki-sacred                            # in the session that combines: take the sacred timeline
/loki-join gatekeeper <story>           # in a session that owns a feature: register as gatekeeper
/loki-join worker <gatekeeper> <story>  # or register as a worker under a gatekeeper
/loki-join branch <branch> ready        # branch finished: mark it ready
/loki-timeline                          # see every session and branch at a glance
/story-combine 1 2                      # in the holder session: combine branches 1 and 2 from the timeline, in order
/loki-prune                             # wrap up: clean up merged worktrees and stale registrations
```

You can also just tell Claude in plain language, for example "combine branches 1 and 2".

## Commands

| Command | What it does | Changes anything? |
|---|---|---|
| `/repo-multiverse [init]` | Overview and shared rules; `init` creates this repo's config | `init` writes the config |
| `/loki-session [--all]` | Lists live sessions: name, status, idle time, role, branches | No |
| `/loki-join …` | Registers as gatekeeper or worker, registers work branches, marks them ready, leaves | Only its own registration |
| `/loki-sacred [status \| takeover \| release]` | Seats the current session on the sacred timeline; `takeover` takes it from a live holder (needs your approval), `release` steps down | Writes the holder record |
| `/loki-timeline` | Tree: integration branch → gatekeepers → work branches, with numbers, ahead/behind counts and merged state | No |
| `/story-combine <numbers or branches…>` | The holder combines approved branches into the integration branch, in order | Yes, with your approval |
| `/loki-prune [--scratch]` | Lists worktrees, stale registrations and scratch folders that can be cleaned up; deletes only what you approve | Yes, group by group |

## Configuration

`/repo-multiverse init` creates a `config.json`:

| Key | Purpose |
|---|---|
| `integration_branch` | The integration branch, i.e. the sacred timeline |
| `verify_quick` | Quick verification command used while working |
| `verify_full` | Full verification, run once per combine in the scratch worktree |
| `worktree_setup` | Commands to run after a new worktree is created, such as preparing dependencies |
| `extra_locks` | Lock files that must be free before a combine |
| `protected_devices` | Simulators or devices reserved for you, which sessions must not use |
| `shared_files` | Files every story may touch, with the rule for resolving conflicts in them |
| `notes` | Project-specific notes for gatekeepers |

State lives in `~/.claude/multiverse/<repo-key>/`. Run `python3 ~/.claude/skills/repo-multiverse/scripts/multiverse.py where` inside the repo to print the exact location. To move it, set the `MULTIVERSE_HOME` environment variable.

## Uninstall

```bash
npx skills remove -g loki-session loki-join loki-sacred loki-timeline story-combine loki-prune repo-multiverse
```

If you installed manually, delete those 7 links from `~/.claude/skills/`. Each repo's config and state are in `~/.claude/multiverse/`; delete them yourself once you no longer need them.

## Disclaimer

This is an unofficial personal project with no affiliation with Marvel Studios or Disney. Loki, the TVA and related names and concepts belong to their respective owners; they are borrowed here only as inspiration and for naming.
