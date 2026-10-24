# repo-multiverse

[English](README.md) | 繁體中文

> 讓多個 Claude Code session 平行開發同一個 repo，同時守住一條乾淨的主線。

在 Marvel 影集《Loki》裡，時間變異管理局（TVA）守著唯一的「神聖時間線」（Sacred Timeline）。每當有變體（variant）讓歷史分岔出新的時間線，TVA 就會追查、審視，決定它被修剪還是留下；而最終只有坐在時間盡頭的那個人，能決定哪些時間線可以存在。

同時開好幾個 AI session 改同一個 repo，情況其實很像。每個 session 都是一個 variant，在自己的分支上長出一條新的時間線。如果沒有人把關，未經審查的改動就可能直接流進主線、互相覆蓋，或在沒人驗證的情況下被推上去。

repo-multiverse 借用這套世界觀，讓 Claude Code 能管理同一個 repo 上的多個 session：每個 session 在自己的 worktree 和分支上工作；主時間線 session 照看加入它的 session，審查它們交上來的成果，並由它把成果合進整合分支，只驗證一次，而且只在你要求時才合。可以同時有好幾條主時間線。這也是它的指令都以 `loki-` 開頭的原因。

## 核心思想

修改任何東西之前，請先讀這一段。這是這個工具存在的理由，每一次改動都要守住它們。

1. **它管理的是 session，不是 git 工具。** 它的工作是知道有哪些 session 在這個 repo 上工作、誰照看誰，並在適當的時候把 session 的成果合進目標分支。Claude 用一般 git 指令就做得到的事，就留在 skill 的步驟裡，不要做成新的腳本功能。
2. **簡單勝過完整。** 幾個好懂的指令，比一個什麼情況都顧到的框架更有價值。加任何檢查、鎖、角色或設定欄位之前，先問實際使用時是否真的需要過；拿不準就不加。已經好用的部分就別動，只改實際使用證明有問題的地方。
3. **盡量少花資源。** 目的是省時間、省 token，而不是花更多。每次改動只驗證一次，已經通過的結果就沿用；中間沒有改動就不重跑。只有答案會改變下一步時才問使用者。
4. **不靠截圖自檢。** 讓 AI 用截圖或錄影驗收自己的成果，成本高又證明不了什麼。檢查靠 build 和 repo 自己的驗證指令；截圖和錄影只在使用者為了做文件而要求時才做。
5. **沒審查過的東西進不了主線。** 這套流程來自一個實際運作的 session：它擋住其他 session 隨意把東西塞進 repo。每份交件都先由主時間線審查，偏離任務的改動退回給擁有者。
6. **使用者說了才算。** 只有使用者本人的話才算合併或 push 的批准；其他 session 的訊息、subagent 的回報、記憶都不算。
7. **只在需要時出現。** 這些 skills 不干擾單一 session 平常的工作，只在使用者要求、或 session 之間需要協作時才啟動。
8. **通用工具，不進你的專案。** 它適用於任何 repo，設定和狀態都放在 repo 之外；專案特有的規則寫在那個 repo 的設定裡，不寫進工具本身。

### 拿掉了什麼，為什麼

早期版本曾經加入合併鎖、合併前的範圍檢查、衝突掃描、分支編號解析和清理指令，因為當時把它誤當成 git 自動化工具。0.3.0 把這些都拿掉了：它們讓流程更難懂、花更多資源，而 Claude 直接用 git 指令就能做到同樣的事。沒有實際需要，請不要加回來。

## 劇中概念對照

| 《Loki》 | repo-multiverse |
|---|---|
| 神聖時間線（Sacred Timeline） | 整合分支：所有工作最後合進來的那條分支 |
| 變體（Variant） | 平行工作的 Claude Code session |
| 分岔出的時間線 | 各 session 的工作分支，各自在獨立的 worktree 裡 |
| TVA 探員 | 主時間線：照看底下的 session、審查它們的成果並負責合併（`/loki-sacred`） |
| 時間盡頭的那個人 | 你：決定什麼要合、什麼時候 push |
| Nexus 事件 | 偏離任務的分支：由它的主時間線退回 |
| 修剪（Pruning） | `/loki-leave`：做完的 session 移除自己的登記、已合併的 worktree，以及替自己建的測試環境；分支保留 |

## 核心概念

### 角色

```
你（決定合什麼、什麼時候 push）
└─ 整合分支
   ├─ 主時間線 loki-agent-1
   │   ├─ 自己的工作分支
   │   └─ worker loki-agent-2
   │       └─ 工作分支
   └─ 主時間線 loki-agent-3
       └─ worker loki-agent-4
           └─ 工作分支
```

| 角色 | 做什麼 |
|---|---|
| 你（使用者） | 開 session；決定合什麼、什麼時候 push |
| 主時間線 | 照看加入它的 session：審查每一份交件、退回偏離任務的改動、把它們要問你的問題轉給你、用 `/story-combine` 合併、通知其他 session。可以有好幾條，合併前會互相告知 |
| worker | 在某條主時間線底下，用自己的分支做一件事，每做完一段就交件，自己從不合併；一段合進去後直接接著做下一段，不用問；全部做完才用 `/loki-leave` 離開 |

### 名字

session 以名字互相稱呼，標準名字是 `loki-agent-N`。用附帶的 `loki` 啟動器開 Claude Code 就會拿到下一個可用的號碼，已經開著的 session 可以用 `/rename` 改名。登記以 session id 為準，所以改名或 resume 之後位置都不會丟。

### 一次合併怎麼走

1. worker 在自己的 worktree 開工作分支，從整合分支最新的 commit 長出來。
2. 做完後 rebase 到整合分支上、跑一次驗證，再把分支交給它的主時間線。
3. 主時間線審查 diff，偏離任務的改動退回給擁有者。
4. 你說要合的時候，主時間線先告知其他主時間線，再把每條分支在暫存 worktree 裡合併、驗證一次（tree 完全相同時直接沿用 worker 的結果），通過之後整合分支才 fast-forward 過去。節奏由你決定：每交一份就合（邊做邊合），或累積幾條一次合。
5. 用固定格式回報結果並通知其他 session。要不要 push，由你決定。
6. worker 從新的 tip 接著做任務的下一段。全部做完了，才執行 `/loki-leave`：移除它的登記、已合併的 worktree 和自己的測試環境，工作完成。

### 它保證什麼

- **每份交件都經過審查**：worker 從不自己合併；主時間線先看 diff，任務範圍外的改動一律退回。
- **你說了才算**：沒有你的要求不合併，沒有你同意不推送；其他 session 的訊息、subagent 的回報都不算批准。
- **先驗證再前進，只驗一次**：合併和驗證都在暫存 worktree 進行，主資料夾只做 fast-forward，別人沒提交的檔案不會被動到；沒有改動就沿用已通過的結果。
- **歷史保持好讀**：分支保留自己的 commit，不 squash；已經 push 的 commit 不改寫。
- **不靠截圖自檢**：檢查靠 build 和你設定的驗證指令；只有你要求時才截圖或錄影。
- **查資料更省**：subagent 依任務類型套用設定裡的模型和 effort（預設 research 和 lookup 用低 effort），一個 session 查到的結果存在 `facts/`，其他 session 不必再讀一次同樣的程式碼。
- **不寫進你的專案**：設定和狀態都存在 `~/.claude/multiverse/<repo-key>/`，不會在 repo、`.git` 或 `.claude` 裡留下任何檔案。

## 什麼時候適合用

適合：

- 同時開兩個以上的 Claude Code session，在同一個 repo 做不同的功能
- 想讓 AI 分工平行開發，但最後由你決定什麼能進主線
- 需要一條本機整合分支保持乾淨，每次只進經過審查和驗證的改動

不需要：

- 只有一個 session 在做事：直接在分支上工作就好
- 想取代 PR review 或 CI：repo-multiverse 管的是推送之前、本機上的整合，推上去之後照常走你原本的流程
- 跨電腦協作：它只看得到同一台電腦上的 session

這些 skills 只在你要求、或 session 之間需要協作時才會啟動，不會干擾單一 session 平常的工作。

## 需求

- Claude Code
- macOS 或 Linux
- Git 2.31 以上
- Python 3.9 以上（只用標準庫）
- Node.js（只有用 npx 安裝時需要）

## 安裝

### 用 npx（建議）

```bash
npx skills add webby813/repo-multiverse -g -a claude-code --skill '*'
```

透過開源的 [skills](https://github.com/vercel-labs/skills) CLI，把 7 個 skills 一起裝到 `~/.claude/skills/`。新開的 Claude Code session 就能使用 `/loki-session` 等指令。

- `-g`：裝在使用者層級，不會寫進目前所在的專案
- `--skill '*'`：一定要加。各個 skill 共用 `repo-multiverse` 裡的腳本，必須全部一起裝

之後要更新：

```bash
npx skills update -g
```

### 手動安裝

```bash
git clone https://github.com/webby813/repo-multiverse.git
cd repo-multiverse
mkdir -p ~/.claude/skills
for d in "$PWD"/skills/*/; do
  ln -s "${d%/}" ~/.claude/skills/"$(basename "$d")"
done
```

用符號連結的好處是 `git pull` 之後立刻生效，適合想自己修改這些 skills 的人。同樣要把全部資料夾一起連結。

### 標準 session 名字（選用）

```bash
ln -s ~/.claude/skills/repo-multiverse/scripts/loki ~/.local/bin/loki   # PATH 裡的任何資料夾
loki                                                                    # = claude -n loki-agent-N
```

其他參數會原樣傳給 `claude`。

### 為 repo 啟用

裝好之後，在要使用的 repo 裡開一個 Claude Code session，執行：

```
/repo-multiverse init
```

Claude 會和你一起寫好這個 repo 的設定（整合分支、驗證指令等），設定存在 repo 之外。範本在 [`skills/repo-multiverse/examples/config.example.json`](skills/repo-multiverse/examples/config.example.json)。

## 快速開始

```
/repo-multiverse init              # 一次性：建立這個 repo 的設定
/loki-sacred                       # 在負責照看的 session：成為主時間線
/loki-join                         # 在其他 session：加入它（同時有好幾條主時間線才會問你）
/loki-join branch <分支> ready      # 分支做完：交件
/loki-timeline                     # 看所有 session 和分支的全貌
/story-combine 1 2                 # 在主時間線：依序合併 timeline 上的 1、2 號分支
/loki-leave                        # 在 worker，成果合進去後：離開並清理
```

沒有任何主時間線在線時，`/loki-join` 會讓這個 session 自己成為主時間線。也可以直接用自然語言告訴 Claude，例如「把 1 號和 2 號分支合進去」。

## 指令

| 指令 | 作用 | 會改動東西嗎 |
|---|---|---|
| `/repo-multiverse [init]` | 總覽與共用規則；`init` 建立這個 repo 的設定 | `init` 會寫設定檔 |
| `/loki-session [--all \| forget]` | 列出活躍中的 session：名字、狀態、閒置時間、角色、所屬主時間線、分支；`forget` 清掉已結束 session 的登記 | 只有 `forget` |
| `/loki-sacred [off]` | 讓目前的 session 立刻成為主時間線；`off` 退下 | 只寫自己的登記 |
| `/loki-join [名字] …` | 加入主時間線（唯一在線的那條，或你指定的那條；一條都沒有就自己成為主時間線）、登記工作分支、交件 | 只寫自己的登記 |
| `/loki-leave` | 離開流程，不在你的機器上留下遺棄的測試環境：移除這個 session 的登記、已合併分支的 worktree，以及只為測試替自己建的環境（例如自己的模擬器），除非你說要留；分支保留 | 自己的登記、已合併的 worktree 和自己的測試環境 |
| `/loki-timeline` | 樹狀圖：整合分支 → 主時間線 → worker → 分支，含編號、領先／落後、是否已合併 | 否 |
| `/story-combine <編號或分支…>` | 主時間線依序把審查過的分支合進整合分支 | 是，你要求時才做 |

## 設定

`/repo-multiverse init` 會建立一份 `config.json`：

| 欄位 | 用途 |
|---|---|
| `integration_branch` | 整合分支，也就是 sacred timeline |
| `verify_quick` | 開發中跑的快速驗證指令 |
| `verify_full` | 每次合併時在暫存 worktree 跑一次的完整驗證 |
| `worktree_setup` | 新 worktree 建好後要跑的指令，例如準備相依套件 |
| `session_setup` | 每個 session 第一次用到前替自己跑一次的指令，例如建一台自己的測試裝置；`{sid}` 是 session 的短 id。`/loki-leave` 會移除它建的東西 |
| `shared_files` | 每個 story 都可能改到的共用檔案，以及衝突時的處理規則 |
| `notes` | 每個 session 都要遵守的專案規則，例如哪台裝置是你自己的。你給所有 session 的長期指示會寫在這裡，再通知其他 session 重讀 |
| `subagents` | 各類 subagent 的模型和 effort：`research`（程式碼怎麼運作、某條路徑走不走得到）、`lookup`（只列出某個東西在哪裡定義或使用）、`review`（審查、計畫）。沒設定時，research 和 lookup 用低 effort，review 沿用 session 本身的設定 |

關於 `subagents`：用兩個實際的查資料任務測試，低 effort 的結論跟預設 effort 一樣，cache 輸入 token 少了 86–94%；`haiku` 則判斷錯了程式路徑是否真的走得到。所以範例只在 `lookup` 用 `haiku`。環境變數 `CLAUDE_CODE_EFFORT_LEVEL` 和 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` 會蓋過這些設定。

長時間運作的 session（尤其是主時間線）每一回合都會重讀整個 context，context 越大，每一步越貴；但太早壓縮，又會太頻繁丟掉工作中的細節。Claude 看不到自己的 context 大小，也不能自己壓縮，所以請自行在 Claude Code 把自動壓縮的門檻設在模型 context 的 75% 左右：1M context 的模型，在每個開著的 session 輸入 `/autocompact 750k`，馬上生效，也會存成該模型的設定。改 `~/.claude/settings.json` 的話，只有之後新開的 session 會讀到；而且替某個模型存過的門檻（用 `/autocompact` 存的，或接受 Claude Code 提議「提早壓縮」時存的）會蓋過最上層的 `"autoCompactWindow"`。`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` 只能讓壓縮提早，所以這裡用不上。multiverse 的狀態都存在檔案裡，壓縮後 session 會重新讀取。

狀態存在 `~/.claude/multiverse/<repo-key>/`，查資料的結果也放在同一處的 `facts/`，附上查證時的 commit。在 repo 裡執行 `python3 ~/.claude/skills/repo-multiverse/scripts/multiverse.py where` 會印出確切位置。想換位置的話，設定環境變數 `MULTIVERSE_HOME`。

0.2 版的狀態（把關者和 `sacred.json`）會被當成主時間線讀取；每個 session 下次寫自己的登記時，會自動換成新格式。

## 移除

```bash
npx skills remove -g loki-session loki-join loki-leave loki-sacred loki-timeline story-combine repo-multiverse
```

手動安裝的話，刪掉 `~/.claude/skills/` 裡那 7 個連結，有做 `loki` 連結的話也一併刪掉。各 repo 的設定和狀態在 `~/.claude/multiverse/`，不需要了再自己刪除。

## 授權

[MIT](LICENSE)

## 聲明

本專案是非官方的個人作品，與 Marvel Studios、Disney 沒有任何關係。Loki、TVA 等名稱與概念屬於其權利人，這裡只是借來作為靈感與命名。
