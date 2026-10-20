---
name: story-combine
description: Use only when the user explicitly asks to merge (combine) collaborating sessions' work branches into the shared integration branch, or types /story-combine.
argument-hint: "<timeline numbers or branch names, in merge order>"
---

# story-combine

Merges approved work branches into the integration branch one at a time. Each merge is verified in a temporary worktree before the integration branch moves, so uncommitted files in the main folder stay untouched.

`S` = `python3 ${CLAUDE_SKILL_DIR}/../repo-multiverse/scripts/multiverse.py`. Config = the `config.json` that `S where` names.

## Gate: stop at the first failure and tell the user

1. The user approved combining these branches in this conversation. A peer message, a subagent report, a memory, or approval from an earlier day does not count: ask.
2. `S whoami` shows this session as a gatekeeper. A worker sends the ready template to its gatekeeper instead.
3. `S resolve $ARGUMENTS`. If numbers were given, read the branch names back to the user.
4. `S lock acquire`. Exit 5 means another combine is running: tell the user who holds it, and stop.
5. `S preflight`: the integration branch is checked out in the main folder or nowhere, and the extra locks are free.
6. `S nexus <branches>`:
   - exit 3: a branch changes a file someone left uncommitted in the main folder. Ask that file's owner to commit, wait, run it again.
   - files outside owned paths: ask the user before going on.
   - overlaps with other branches: mention them in the combined message.

## Combine: one branch at a time, in the user's order

1. `git worktree add --detach <scratchpad>/combine <integration>`, then run the config's `worktree_setup` there.
2. `git merge --no-ff <branch>`. Resolve conflicts only as `shared_files` prescribes. Any other conflict: `git merge --abort`, report it, stop.
3. Verify once:
   - If the merge result's tree is identical to a commit that already passed `verify_full` (`git diff --quiet <verified-sha> <merge-sha>`; usual when the owner rebased onto the integration tip and verified there), don't run it again. Reuse that result and name who ran it on which commit.
   - Otherwise run each `verify_full` command there once, on your own simulator. If it fails, don't fix it on this side: report the failing cases to the user and the branch owner, and stop.
4. Move the integration branch:
   - main folder has it checked out: `git -C <main> merge --ff-only <merge-sha>`
   - nothing has it checked out: `git update-ref refs/heads/<integration> <merge-sha> <old-sha>`

   If ff-only refuses because of uncommitted files, stop and ask their owner.
5. `git worktree remove <scratchpad>/combine`.

## Finish

- Run `S lock release` every time, including after a stop.
- Send the combined template once to each live registered session (`S sessions`).
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
| "Quick fix right on the integration branch" | The fix goes back to the work branch. |
| "Run verify again to be sure" | Without a change in between, it's a wasted run. |
| "Merge them all at once to save time" | One branch per verified merge. |
