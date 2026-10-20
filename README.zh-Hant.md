# repo-multiverse

[English](README.md) | 繁體中文

> 讓多個 Claude Code session 平行開發同一個 repo，同時守住一條乾淨的主線。

在 Marvel 影集《Loki》裡，時間變異管理局（TVA）守著唯一的「神聖時間線」（Sacred Timeline）。每當有變體（variant）讓歷史分岔出新的時間線，TVA 就會追查、審視，決定它被修剪還是留下；而最終只有坐在時間盡頭的那個人，能決定哪些時間線可以存在。

同時開好幾個 AI session 改同一個 repo，情況其實很像。每個 session 都是一個 variant，在自己的分支上長出一條新的時間線。如果沒有人把關，未經審查的改動就可能直接流進主線、互相覆蓋，或在沒人驗證的情況下被推上去。

repo-multiverse 借用這套世界觀，為 Claude Code 提供一套多 session 的開發把關流程：每個 session 在自己的 worktree 和分支上工作；同一時間只有一個 session 坐在神聖時間線上，只有它能把成果合進整合分支；每次合併都先驗證，而且一定要經過你批准。這也是它的指令都以 `loki-` 開頭的原因。

## 劇中概念對照

| 《Loki》 | repo-multiverse |
|---|---|
| 神聖時間線（Sacred Timeline） | 整合分支：所有工作最後合進來的那條分支 |
| 變體（Variant） | 平行工作的 Claude Code session |
| 分岔出的時間線 | 各 session 的工作分支，各自在獨立的 worktree 裡 |
| TVA 探員 | 把關者（gatekeeper）：負責一個 story，審查底下分支的改動範圍 |
| 時間盡頭的王座 | sacred timeline 持有者：唯一能合併的 session（`/loki-sacred`） |
| Nexus 事件 | 合併前的檢查：改到範圍外的檔案、和其他分支重疊、碰到別人沒提交的檔案 |
| 修剪（Pruning） | 清理已合併的 worktree 和過期的登記（`/loki-prune`） |

## 核心概念

### 角色

```
你（指定持有者、批准每次合併與推送）
└─ sacred timeline：整合分支 ← 持有者 session（唯一能合併）
   ├─ 把關者 A（story A）
   │   ├─ 工作分支（把關者自己做）
   │   └─ 工作分支（worker session 做）
   └─ 把關者 B（story B）
       └─ 工作分支
```

| 角色 | 做什麼 |
|---|---|
| 你（使用者） | 決定由哪個 session 持有 sacred timeline，批准每一次合併與推送 |
| sacred timeline 持有者 | 同一時間只有一個；唯一能執行 `/story-combine`、移動整合分支的 session，也可以同時當把關者 |
| 把關者（gatekeeper） | 負責一個 story（一塊功能範圍）和底下的工作分支，確認改動沒有越界，再交給持有者合併 |
| worker | 在某個把關者底下做一條工作分支，完成後回報 ready |

### 一次合併怎麼走

1. worker 或把關者在自己的 worktree 開工作分支，從整合分支最新的 commit 長出來。
2. 做完後標記 ready。把關者確認改動範圍，再轉給持有者。
3. 持有者向你確認這次要合哪些分支。
4. 每條分支先在暫存 worktree 裡合併、跑完整驗證，通過之後整合分支才 fast-forward 過去。
5. 持有者回報結果並通知其他 session。要不要 push，由你決定。

### 它保證什麼

- **只有一個 session 能合併**：持有者記錄在狀態檔裡，其他 session 嘗試合併會直接被腳本拒絕，不靠 AI 自律。
- **一次只合一條**：合併時持有鎖，同一時間不會有兩個合併在進行。
- **先驗證再前進**：合併和驗證都在暫存 worktree 進行，主資料夾只做 fast-forward，別人沒提交的檔案不會被動到。
- **改動不越界**：把關者登記時寫明 story 可以改哪些路徑，合併前會列出超出範圍的檔案，先問過你。
- **你說了才算**：其他 session 的訊息、subagent 的回報都不算批准；沒有你同意，不合併、不推送。
- **不寫進你的專案**：設定和狀態都存在 `~/.claude/multiverse/<repo-key>/`，不會在 repo、`.git` 或 `.claude` 裡留下任何檔案。

## 什麼時候適合用

適合：

- 同時開兩個以上的 Claude Code session，在同一個 repo 做不同的功能
- 想讓 AI 分工平行開發，但最後由你決定什麼能進主線
- 需要一條本機整合分支保持乾淨，每次只進經過驗證和批准的改動

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

### 為 repo 啟用

裝好之後，在要使用的 repo 裡開一個 Claude Code session，執行：

```
/repo-multiverse init
```

Claude 會和你一起寫好這個 repo 的設定（整合分支、驗證指令等），設定存在 repo 之外。範本在 [`skills/repo-multiverse/examples/config.example.json`](skills/repo-multiverse/examples/config.example.json)。

## 快速開始

```
/repo-multiverse init              # 一次性：建立這個 repo 的設定
/loki-sacred                       # 在負責合併的 session：坐上 sacred timeline
/loki-join gatekeeper <story>      # 在負責功能的 session：登記為把關者
/loki-join worker <把關者> <story>  # 或登記為某個把關者底下的 worker
/loki-join branch <分支> ready      # 分支做完：標記 ready
/loki-timeline                     # 看所有 session 和分支的全貌
/story-combine 1 2                 # 在持有者 session：依序合併 timeline 上的 1、2 號分支
/loki-prune                        # 收尾：清理已合併的 worktree 和過期登記
```

也可以直接用自然語言告訴 Claude，例如「把 1 號和 2 號分支合進去」。

## 指令

| 指令 | 作用 | 會改動東西嗎 |
|---|---|---|
| `/repo-multiverse [init]` | 總覽與共用規則；`init` 建立這個 repo 的設定 | `init` 會寫設定檔 |
| `/loki-session [--all]` | 列出活躍中的 session：名字、狀態、閒置時間、角色、分支 | 否 |
| `/loki-join …` | 登記為把關者或 worker、登記工作分支、標記 ready、離開 | 只寫自己的登記 |
| `/loki-sacred [status \| takeover \| release]` | 讓目前的 session 坐上 sacred timeline；`takeover` 從還在線的持有者手上接手（需要你批准），`release` 讓出 | 寫持有者紀錄 |
| `/loki-timeline` | 樹狀圖：整合分支 → 把關者 → 工作分支，含編號、領先／落後、是否已合併 | 否 |
| `/story-combine <編號或分支…>` | 持有者依序把批准的分支合進整合分支 | 是，需要你批准 |
| `/loki-prune [--scratch]` | 列出可以清理的 worktree、過期登記和暫存資料夾，你同意後才刪 | 是，逐組確認 |

## 設定

`/repo-multiverse init` 會建立一份 `config.json`：

| 欄位 | 用途 |
|---|---|
| `integration_branch` | 整合分支，也就是 sacred timeline |
| `verify_quick` | 開發中跑的快速驗證指令 |
| `verify_full` | 每次合併時在暫存 worktree 跑一次的完整驗證 |
| `worktree_setup` | 新 worktree 建好後要跑的指令，例如準備相依套件 |
| `extra_locks` | 合併前必須沒被佔用的鎖檔 |
| `protected_devices` | 保留給你自己、session 不能使用的模擬器或裝置 |
| `shared_files` | 每個 story 都可能改到的共用檔案，以及衝突時的處理規則 |
| `notes` | 給把關者看的專案注意事項 |

狀態存在 `~/.claude/multiverse/<repo-key>/`。在 repo 裡執行 `python3 ~/.claude/skills/repo-multiverse/scripts/multiverse.py where` 會印出確切位置。想換位置的話，設定環境變數 `MULTIVERSE_HOME`。

## 移除

```bash
npx skills remove -g loki-session loki-join loki-sacred loki-timeline story-combine loki-prune repo-multiverse
```

手動安裝的話，刪掉 `~/.claude/skills/` 裡那 7 個連結即可。各 repo 的設定和狀態在 `~/.claude/multiverse/`，不需要了再自己刪除。

## 聲明

本專案是非官方的個人作品，與 Marvel Studios、Disney 沒有任何關係。Loki、TVA 等名稱與概念屬於其權利人，這裡只是借來作為靈感與命名。
