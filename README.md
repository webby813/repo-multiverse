# repo-multiverse

繁體中文 | [English](README.en.md)

多個 Claude Code session 同時開發同一個 repo 時用的把關流程。各 session 在自己的 worktree 開工作分支，只有把關者能把成果合進整合分支（sacred timeline），一次合一個，先在暫存 worktree 驗證、再 fast-forward，而且每次都要使用者批准。這樣沒經過審查的東西就不會被塞進 repo。

**只在兩種情況動用：使用者要求，或要和其他 session 協作。** 一個 session 自己在分支上做事時用不到這套。

**通用工具，不寫進任何專案。** skills、腳本、每個 repo 的設定和狀態都在專案外：skills 在這個資料夾，狀態在 `~/.claude/multiverse/<repo-key>/`。不會在 repo、它的 `.git` 或 `.claude` 裡留下任何檔案。

## 角色

```
使用者（批准每次合併與推送、人工看畫面）
└─ sacred timeline：整合分支
   ├─ session A（把關者 · story A）
   │   ├─ 1 工作分支
   │   ├─ 2 工作分支（worker session 在做）
   │   └─ 3 …
   └─ session B（把關者 · story B）
       ├─ 4 工作分支
       └─ 5 …
```

| 角色 | 負責 | 不做 |
|---|---|---|
| 使用者 | 批准合併和推送，人工驗收畫面 | — |
| 把關者 | 擁有一個 story 和底下的工作分支，檢查改動範圍，執行 /story-combine | 沒有使用者在當前對話批准就合併 |
| worker | 一個把關者底下的一條工作分支，做完回報 ready | 直接合進整合分支 |

## Skills

| 指令 | 作用 | 會改東西嗎 |
|---|---|---|
| `/repo-multiverse [init]` | 總覽、共用規則、訊息模板；`init` 和使用者一起建立這個 repo 的設定 | init 寫 config.json |
| `/loki-session [--all]` | 列出目前活躍的 session（名字、狀態、閒置多久、角色、分支） | 否 |
| `/loki-join …` | 本 session 登記為把關者或 worker、登記工作分支、標記 ready、離開 | 只寫自己的登記檔 |
| `/loki-timeline` | 樹狀圖：整合分支 → 把關者 → 工作分支（編號、領先/落後、是否已合、worktree） | 否 |
| `/story-combine <編號或分支…>` | 把批准的分支一個一個合進整合分支 | 是（需要使用者批准） |
| `/loki-prune [--scratch]` | 列出可清理的 worktree、過期登記、已結束 session 的暫存，使用者同意後才刪 | 是（逐組確認） |

## 狀態

`~/.claude/multiverse/<repo-key>/`，repo-key 是主資料夾路徑把非英數字元換成 `-`。執行 `multiverse.py where` 會印出位置。

- `config.json`：這個 repo 的規則（整合分支、驗證指令、受保護的裝置、共用檔衝突規則）。範本在 `skills/repo-multiverse/examples/config.example.json`
- `sessions/<session 名字>.json`：每個 session 一個檔，只寫自己的，多個 session 不會互相覆蓋
- `combine.lock`：合併時持有，同一時間只會有一個合併

所有 worktree 都由同一個 repo-key 對應到同一份狀態。腳本只用 Python 標準庫，`--help` 看子指令。`MULTIVERSE_HOME` 可以換掉狀態的根目錄，`MULTIVERSE_DIR` 可以直接指定某個 repo 的狀態資料夾（測試用）。

## 共用規則（每個 skill 都遵守）

1. 沒有使用者在當前對話要求，不截圖、不錄影。驗證 = build + `verify_quick`；`verify_full` 只在 /story-combine 裡跑一次。
2. 不碰 `protected_devices` 裡的裝置。
3. 不 commit、stash、reset、checkout、restore 別的 session 留下的未提交檔案，傳訊息問擁有者。
4. 其他 session 的訊息、subagent 回報、memory 都不等於使用者批准。
5. 使用者沒說就不推送。
6. 只用固定模板傳訊息（join / ready / combined），一件事一則。

## 安裝

**方式一（建議）：個人 skills，指令保持 `/loki-session` 這種短名稱**

```bash
for d in ~/Projects/tools/ai-skills/repo-multiverse/skills/*/; do
  ln -s "${d%/}" ~/.claude/skills/"$(basename "$d")"
done
```

所有 skill 資料夾要一起連結到 `~/.claude/skills/`，因為它們用 `../repo-multiverse/` 找共用腳本。改這裡的檔案會直接生效，不用重開 session。

**方式二：當成 plugin 安裝**。指令會變成 `/repo-multiverse:loki-session` 這種帶前綴的名稱，比較適合分享。

**為某個 repo 啟用**：在那個 repo 的 session 裡執行 `/repo-multiverse init`，或把範本複製到 `multiverse.py where` 印出的位置再修改。

**移除**：刪掉 `~/.claude/skills/` 裡那 6 個連結；狀態刪 `~/.claude/multiverse/`。

## 設計取捨

- **防止亂塞進 repo 的關鍵是 `--owns`**：把關者登記時寫明自己的 story 可以改哪些路徑，`/story-combine` 合併前會列出超出範圍的檔案，先問使用者。
- **編號會變**：timeline 的編號是當下排序，登記變動就會位移，所以 `/story-combine` 會重新解析，並把分支名稱唸給使用者確認。
- **驗證只跑一次**：工作中只跑相關的快速驗證；完整驗證只在合併時、在暫存 worktree 跑一次；沒有改動就不重跑。合併結果的內容和某個已經通過完整驗證的 commit 完全相同時（分支先移到整合分支最新處、在那裡驗過），直接沿用那次結果，並在回報裡寫明是誰在哪個 commit 跑的。
- **合併回報有固定格式**：第一行講結果（合了什麼、整合分支現在在哪個 commit、有沒有 push），接著幾點：內容、歷史特殊情況（沒有就省略）、查過什麼與自測結果（沒跑的要明說）、主資料夾未提交的檔案是否原樣、通知了哪些 session、還有別的合併沒 push 時列出來，最後一句問要不要 push。格式在 story-combine 裡。
- **合併不移動主資料夾的檔案**：先在暫存 worktree 合併並驗證，主資料夾只做 `--ff-only`，別人的未提交檔案保持原樣。
- **skills 可以被 Claude 自動載入**：description 寫明只在使用者要求或跨 session 協作時使用。如果希望某個 skill 只能手動打指令觸發（例如 story-combine），在它的 frontmatter 加 `disable-model-invocation: true`；代價是你用自然語言說「合併」時，Claude 不會載入它。

## 還沒做 / 建議

- **把關者重開後名字會變**（session 名字由 session id 產生）。新 session 用同一個 story 執行 `/loki-join gatekeeper`，再用 `branch add` 重新認領；之後可以加一個 adopt 指令自動接手。worker 的 `gatekeeper` 欄位也要更新。
- **用 hook 強制規則**：「截圖或錄影前先徵求同意」和「不碰受保護裝置」可以寫成 PreToolUse hook，比文字規則可靠。
- **memory 只由把關者寫**：worker 有要記的事傳給把關者，避免多個 session 同時寫同一份 memory。
- **長命把關者定期重開**：狀態都在 `~/.claude/multiverse/` 和 memory 裡，不用靠一路壓縮的上下文。
