# repo-multiverse

English | [繁體中文](README.zh-Hant.md)

> Let several Claude Code sessions build in the same repo in parallel, while one clean main line stays protected.

In Marvel's *Loki* series, the Time Variance Authority (TVA) guards a single Sacred Timeline. Whenever a variant makes history branch off into a new timeline, the TVA tracks it down and decides whether it gets pruned or stays. In the end, only the one sitting at the end of time decides which timelines get to exist.

Running several AI sessions on the same repo is much the same. Each session is a variant, growing a new timeline on its own branch. Without someone keeping watch, unreviewed changes can flow straight into the main line, overwrite each other, or get pushed without anyone verifying them.

repo-multiverse borrows that world to let Claude Code manage several sessions on one repo. Each session works in its own worktree and branch. A main timeline session looks after the sessions that joined it: it reviews what they hand in, and it is the one that combines their work into the integration branch, verified once and only when you ask. Several main timelines can run side by side. That is why its commands start with `loki-`.

## Core ideas

Read this before changing anything. These are the reasons the tool exists, and every change should keep them.

1. **It manages sessions; it is not a git tool.** Its job is to know which sessions are working on the repo and who looks after whom, and to bring a session's result into the target branch when the time is right. Anything Claude can already do with plain git commands stays a plain git command in a skill's steps, not a new script feature.
2. **Simple beats complete.** A few commands that are easy to understand are worth more than a framework that covers every case. Before adding a check, a lock, a role or a config key, ask whether real use has needed it. When in doubt, leave it out. Keep what already works, and change only what real use shows is wrong.
3. **Spend as little as possible.** The point is to save time and tokens, not to spend more. Verify once per change and reuse a result that already passed; never re-run a check without a change in between. Ask the user only when the answer changes what happens next.
4. **No screenshots for self-checks.** An AI accepting its own work from a screenshot or a screen recording costs a lot and proves little. Checks are builds and the repo's own verify commands. Screenshots and recordings happen only when the user asks for them, for documentation.
5. **Nothing reaches the main line unreviewed.** The workflow grew out of a real session that kept other sessions from slipping work into the repo. Every hand-in is reviewed by a main timeline first, and stray edits go back to their owner.
6. **The user decides.** Only the user's own words count as approval to combine or push. A message from another session, a subagent report or a memory never does.
7. **Only when asked.** The skills stay out of a single session's everyday work. They activate when the user asks for them or when sessions need to coordinate.
8. **A general tool that stays out of your project.** It works for any repo, and its config and state live outside the repo. Repo-specific rules belong in that repo's config, never in the tool.

### What was taken out, and why

Earlier versions grew a combine lock, pre-combine scope checks, conflict scans, branch-number resolving and a cleanup command, because the tool was mistaken for git automation. Version 0.3.0 removed them: they made the flow harder to follow and cost more, while Claude can do the same with plain git commands. Please don't add them back without a real need.

## The show, mapped

| *Loki* | repo-multiverse |
|---|---|
| Sacred Timeline | The integration branch, where all work ends up |
| Variant | A Claude Code session working in parallel |
| A branched timeline | A session's work branch, each in its own worktree |
| TVA agent | Main timeline: a session that looks after the sessions under it, reviews their work and combines it (`/loki-sacred`) |
| The one at the end of time | You: you decide what gets combined and when it is pushed |
| Nexus event | A branch that strays from its task: its main timeline sends it back |
| Pruning | Removing a merged worktree once its owner is done; the branch stays |

## Core concepts

### Roles

```
You (say what gets combined and when to push)
└─ integration branch
   ├─ main timeline loki-agent-1
   │   ├─ its own work branch
   │   └─ worker loki-agent-2
   │       └─ work branch
   └─ main timeline loki-agent-3
       └─ worker loki-agent-4
           └─ work branch
```

| Role | Does |
|---|---|
| You (the user) | Start sessions; say what gets combined and when to push |
| Main timeline | Looks after the sessions that joined it: reviews every hand-in, sends back work that strays, combines with `/story-combine`, tells the other sessions. Several can exist; they announce their combines to each other |
| Worker | Does one task on its own branch under a main timeline, hands it in when ready, never merges itself |

### Names

Sessions are addressed by name, and the standard name is `loki-agent-N`. Start Claude Code with the bundled `loki` launcher to get the next free one, or `/rename` a running session. A session keeps its place after a rename or a resume, because registrations are keyed by session id.

### How a combine goes

1. A worker opens a work branch in its own worktree, starting from the latest commit of the integration branch.
2. When done, it rebases onto the integration branch, runs the verification once and hands the branch in to its main timeline.
3. The main timeline reviews the diff. Work that strays from the task goes back to its owner.
4. When you ask, the main timeline tells the other main timelines, merges each branch in a scratch worktree, verifies it once (reusing the worker's result when the tree is identical), and only then fast-forwards the integration branch.
5. It reports the result in a fixed shape and tells the other sessions. Whether to push is up to you.

### What it guarantees

- **Every hand-in is reviewed**: workers never merge. A main timeline reads the diff first and sends back edits outside the task.
- **You decide**: nothing is combined unless you asked for it, and nothing is pushed without you. Messages from other sessions and subagent reports never count as approval.
- **Verify before moving, once**: merging and verification happen in a scratch worktree, and the main folder only fast-forwards, so other people's uncommitted files are never touched. A passing result is reused when nothing changed.
- **History stays readable**: branches keep their own commits, never squashed, and pushed commits are never rewritten.
- **No screenshots for self-checks**: checks are builds and your verify commands. Screenshots or recordings happen only when you ask.
- **Nothing written into your project**: config and state live in `~/.claude/multiverse/<repo-key>/`. Nothing is left in the repo, its `.git` or its `.claude`.

## When to use it

Good fit:

- Two or more Claude Code sessions working on different features in the same repo at once
- You want AI sessions to split the work in parallel, but you decide what reaches the main line
- You need a local integration branch that stays clean and only takes reviewed, verified changes

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

This uses the open-source [skills](https://github.com/vercel-labs/skills) CLI to install all 6 skills into `~/.claude/skills/`. New Claude Code sessions can then use `/loki-session` and the rest.

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

### Standard session names (optional)

```bash
ln -s ~/.claude/skills/repo-multiverse/scripts/loki ~/.local/bin/loki   # any folder on your PATH
loki                                                                    # = claude -n loki-agent-N
```

Other arguments pass straight through to `claude`.

### Enable it for a repo

After installing, open a Claude Code session in the repo you want to use it in and run:

```
/repo-multiverse init
```

Claude writes this repo's config with you (integration branch, verification commands and so on), stored outside the repo. A template is in [`skills/repo-multiverse/examples/config.example.json`](skills/repo-multiverse/examples/config.example.json).

## Quick start

```
/repo-multiverse init              # once: create this repo's config
/loki-sacred                       # in the session that looks after the others: become a main timeline
/loki-join                         # in each other session: join it (asks only when several main timelines are live)
/loki-join branch <branch> ready   # branch finished: hand it in
/loki-timeline                     # see every session and branch at a glance
/story-combine 1 2                 # in the main timeline: combine branches 1 and 2 from the timeline, in order
```

`/loki-join` with no main timeline live makes the session one. You can also just tell Claude in plain language, for example "combine branches 1 and 2".

## Commands

| Command | What it does | Changes anything? |
|---|---|---|
| `/repo-multiverse [init]` | Overview and shared rules; `init` creates this repo's config | `init` writes the config |
| `/loki-session [--all \| forget]` | Lists live sessions: name, status, idle time, role, main timeline, branches; `forget` clears registrations of ended sessions | Only `forget` |
| `/loki-sacred [off]` | Makes this session a main timeline right away; `off` steps down | Only its own registration |
| `/loki-join [name] …` | Joins a main timeline (the only live one, or the one you name; becomes one when none is live), registers work branches, hands them in, leaves | Only its own registration |
| `/loki-timeline` | Tree: integration branch → main timelines → workers → branches, with numbers, ahead/behind counts and merged state | No |
| `/story-combine <numbers or branches…>` | A main timeline combines reviewed branches into the integration branch, in order | Yes, when you ask |

## Configuration

`/repo-multiverse init` creates a `config.json`:

| Key | Purpose |
|---|---|
| `integration_branch` | The integration branch, i.e. the sacred timeline |
| `verify_quick` | Quick verification command used while working |
| `verify_full` | Full verification, run once per combine in the scratch worktree |
| `worktree_setup` | Commands to run after a new worktree is created, such as preparing dependencies |
| `shared_files` | Files every story may touch, with the rule for resolving conflicts in them |
| `notes` | Repo-specific rules every session follows, such as a device that belongs to you |

State lives in `~/.claude/multiverse/<repo-key>/`. Run `python3 ~/.claude/skills/repo-multiverse/scripts/multiverse.py where` inside the repo to print the exact location. To move it, set the `MULTIVERSE_HOME` environment variable.

State from 0.2 (gatekeepers and `sacred.json`) is read as main timelines, and each session moves to the new format the next time it writes its registration.

## Uninstall

```bash
npx skills remove -g loki-session loki-join loki-sacred loki-timeline story-combine repo-multiverse
```

If you installed manually, delete those 6 links from `~/.claude/skills/`, plus the `loki` link if you made one. Each repo's config and state are in `~/.claude/multiverse/`; delete them yourself once you no longer need them.

## License

[MIT](LICENSE)

## Disclaimer

This is an unofficial personal project with no affiliation with Marvel Studios or Disney. Loki, the TVA and related names and concepts belong to their respective owners; they are borrowed here only as inspiration and for naming.
