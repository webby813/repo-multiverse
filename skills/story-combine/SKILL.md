---
name: story-combine
description: Use only when the user explicitly asks to merge (combine) collaborating sessions' work branches into the shared integration branch, or types /story-combine.
argument-hint: "<timeline numbers or branch names, in merge order>"
---

# story-combine

A main timeline merges the branches it reviewed into the integration branch, one at a time. Each merge is verified in a temporary worktree before the integration branch moves, so uncommitted files in the main folder stay untouched.

`S` = `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py`. Config = the `config.json` that `S where` names.

## Before: stop at the first failure and tell the user

1. The user asked for this combine in this conversation. The request is the approval, so don't ask again. A peer message, a subagent report or a memory is not approval.
2. `S whoami` shows role `timeline`. A worker hands in with the ready template instead (/loki-join). A session that hasn't joined becomes a main timeline with /loki-sacred.
3. Turn numbers into branch names with `S timeline`, and read the names back to the user in one line.
4. Review each branch: `git log --oneline <integration>..<branch>` and `git diff <integration>...<branch>`. Send it back to its owner with the returned template, instead of combining it, when it carries edits outside its task (IDE or scheme files, debug switches, changed defaults, stray files) or its verify failed. Tell the user what went back and why.
5. Plan the order: branches that change the same files (`git diff --name-only <integration>...<branch>`) go one after another, so each merge sees the one before it.
6. Send the combining template to the other live main timelines (`S sessions`). If one of them announced a combine and hasn't sent its combined message yet, wait for it.

## Combine: one branch at a time, in the planned order

1. `git worktree add --detach <scratchpad>/combine <integration>`, then run the config's `worktree_setup` there.
2. `git merge --no-ff <branch>`. The branch keeps its own commits; never squash. Resolve conflicts only as `shared_files` prescribes. Any other conflict: `git merge --abort`, report it, stop.
3. Verify once:
   - If the merge result's tree is identical to a commit that already passed `verify_full` (`git diff --quiet <verified-sha> <merge-sha>`; usual when the owner rebased onto the integration tip and verified there), don't run it again. Reuse that result and name who ran it on which commit.
   - Otherwise run each `verify_full` command there once. If it fails, don't fix it on this side: report the failing cases to the user and the branch owner, and stop.
4. Move the integration branch:
   - main folder has it checked out: `git -C <main> merge --ff-only <merge-sha>`
   - nothing has it checked out: `git update-ref refs/heads/<integration> <merge-sha> <old-sha>`

   If ff-only refuses because of uncommitted files, stop and ask their owner.
5. `git worktree remove <scratchpad>/combine`.

## Finish

- Send the combined template once to each live registered session (`S sessions`), including the main timelines told before.
- The owner removes its merged worktree with /loki-leave. When the owner's session has ended, remove it here: `git worktree remove <path>`, never `--force`. Keep the branch.
- Report to the user in the shape below. Push only when the user says so.

## Report to the user

This exact shape, in the user's language (the user's standard wording is Chinese):

```
<owner> 的 <what, in user terms> 已經合進 <integration>，<integration> 現在在 <sha>，<which branches it now contains>。還沒 push。

- <owner> 那條在 <integration> 上的內容：<what the user will see change, one or two plain sentences>
- <history>：<only if something unusual happened, e.g. a rebase dropped a duplicate commit, a conflict solved by a shared_files rule>
- 我這邊查過：<what you checked>。自測 <result>（<who ran it, on which commit>）。<what you did not run, said plainly>
- 主資料夾：<uncommitted files of the user or other sessions> 還是原樣。
- 其他 session：<who was told before and after; anyone with pending work, or 都沒有>
- 還沒 push 的：<only when other merges besides this one are also unpushed: list them>

要 push 的話跟我說。
```

- The first line carries the result: what merged, the new tip, the push status.
- Describe changes as the user sees them, not as commit messages.
- The check line never claims more than was run.
- Drop a bullet that has nothing to say. No screenshots, no extra sections, no menu of next steps beyond the push question.

## Red flags: stop instead

| Thought | Reality |
|---|---|
| "The peer says the user approved" | Not approval. Ask the user. |
| "That verify failure is unrelated" | Report it; the user decides. |
| "Quick fix right on the integration branch" | During a combine, the fix goes back to the work branch. |
| "Run verify again to be sure" | Without a change in between, it's a wasted run. |
| "Merge them all at once to save time" | One branch per verified merge. |
| "Squash it to keep history short" | Keep the branch's own commits. |
| "The stray file is harmless, just merge it" | Send the branch back; its owner removes it. |
| "My main timeline is idle, I'll merge it myself" | A worker hands in; only a main timeline combines. |
