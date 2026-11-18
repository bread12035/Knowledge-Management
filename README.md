# Knowledge-Management

由 Claude 維護的 LLM wiki。把「AI new tech & studies」與「system design & code style」兩個 project 的討論文件，整理成可以複習、可以在設計時引用、而且兩邊互相連結的知識庫。

設計依據：`raw/ai-new-tech/anthropic-agent-memory-guide.md` 的四層記憶模型與 dreaming（入口頁 `KM:agent-memory`、`KM:km-dreaming-design`）。

---

## 1. 整體架構

```
 claude.ai project                    GitHub repo（main）                         讀者
 ─────────────────                    ───────────────────────────────────         ────────

 AI new tech & studies ──01:20──┐
   （project 文件）              │     L1 raw/ai-new-tech/      逐字原文
                                 ├──▶  L1 raw/system-design/    （只增不刪）
 system design & code style ─01:50┘            │
   （project 文件）                             │ 03:10 Claude Code dreaming
                                                ▼
                                       L2 notes/<source>/       原子化主張 + 證據標記
                                                │
                                                ▼
                                       L3 wiki/                 主題頁、模式、決定、
                                          ├ topics/ concepts/    跨領域 bridges
                                          ├ patterns/ decisions/
                                          ├ bridges/  archive/
                                          └ _index.md            （km.py 自動產生）
                                                │
                                                ▼
                                       L4 PRIMER.md             ≤ 4,096 字元的入口  ──▶  你、project、其他 agent
                                          review/YYYY-Www.md    每週複習週報        ──▶  你
                                          dream/log.md          每次執行紀錄        ──▶  你
```

### 三個排程

| 排程 | 在哪裡 | 時間（Asia/Taipei） | 做什麼 | Prompt |
| --- | --- | --- | --- | --- |
| AI new tech 匯出 | claude.ai project「AI new tech & studies」 | 每天 01:20 | 新增或修改的 project 文件逐字寫進 `raw/ai-new-tech/` | `prompts/project-export-ai-new-tech.md` |
| System design 匯出 | claude.ai project「system design & code style」 | 每天 01:50 | 同上，寫進 `raw/system-design/` | `prompts/project-export-system-design.md` |
| Dreaming | Claude Code 排程「Knowledge-Management dreaming」，喚醒固定 session「Knowledge-Management dreaming（每日排程用）」 | 每天 03:10；週日為 deep | 抽 note、整合 wiki、跨領域連結、複習校正、push 到 main | `prompts/dream.md` |

### 誰寫哪裡（單一寫入者）

| 路徑 | 唯一寫入者 |
| --- | --- |
| `raw/<source>/` | 該 source 的 project 排程 |
| `notes/`、`wiki/`、`review/`、`dream/`、`PRIMER.md` | dreaming 排程 |
| `CLAUDE.md`、`prompts/`、`scripts/`、`README.md` | 你（或你請 Claude 改） |

每個路徑只有一個寫入者，所以三個排程不會互相蓋掉（`KM:single-writer`）。

### 每次 dreaming 做什麼（`prompts/dream.md`）

| 步驟 | 名稱 | 內容 |
| --- | --- | --- |
| 1 | Ingest | `km.py status` 用 sha256 找出新增或修改的原文，每份產生一份 note（每次最多 5 份） |
| 2 | Integrate | note 的主張併進 wiki 頁；結論被推翻時歸檔舊頁，不直接刪；無法判斷時標 `CONFLICT` |
| 3 | Cross-link | 找另一個 project 解決同類問題的概念，建立 `wiki/bridges/`；只有一邊有頁面就先放進 `dream/bridge-candidates.md` |
| 4 | Revisit | 挑到期與最久沒整理的頁面，對照原文重新核對（daily 8 頁、deep 20 頁） |
| 5 | Organize | 合併重複、修壞連結、重建 `_index.md`、lint 到 0 錯誤 |
| 6 | Deep（週日） | 壓縮膨脹、重寫 `PRIMER.md`、產生 `review/` 週報 |
| 7 | Log + push | 寫 `dream/log.md`，commit 並 push 到 main |

能用程式做的交給 `scripts/km.py`（變更偵測、目錄、lint、到期計算），LLM 只寫內容（`KM:deterministic-over-llm`）。

---

## 2. 日常怎麼用

### 2.1 新增知識：照原本的習慣就好

1. 在任一個 project 討論。
2. 把結論整理成文件，放進該 project 的知識庫（project files）。
3. 隔天早上就會出現在 wiki：01:20 / 01:50 匯出，03:10 整合。

- **要修訂文件：** 直接改 project 裡的同一份文件。匯出時會覆蓋同一個 `raw/` 檔，dreaming 偵測到 hash 變了，會重新產生 note，並重新核對引用它的 wiki 頁。舊版本留在 git 歷史。
- **刪掉 project 文件：** `raw/` 不會跟著刪（只增不刪）。要讓 wiki 不再採用它，請直接告訴 Claude。
- **一次加很多文件：** 每次 dreaming 最多處理 5 份，其餘自動排到之後幾天。

### 2.2 複習

| 什麼時候 | 看哪裡 | 內容 |
| --- | --- | --- |
| 每週一 | `review/YYYY-Www.md` | 本週新增與修改、到期頁面的回想題、新的跨領域連結、待你處理的事 |
| 想看最近變了什麼 | `dream/log.md` | 每次執行一筆，新的在上 |
| 想自己挑 | `python3 scripts/km.py due --days 7` | 7 天內到期的頁面 |

複習間隔：頁面每被核對一次就拉長（3、7、14、30、60 天）；內容有實質修改就重新從 1 天開始（`CLAUDE.md` §5）。

### 2.3 查詢與設計時引用

1. 從 `PRIMER.md` 或 `wiki/_index.md` 開始，找到頁面後沿 `[[slug]]` 連結走。
2. 需要原文時，看頁面 frontmatter 的 `sources`（指向 `raw/` 的章節）。
3. 寫設計文件或在 project 討論時引用：`KM:<slug>`，例如 `KM:transactional-outbox`。slug 不會改名；頁面合併時舊位置會留轉址。
4. 看可信度：每條重點後面的 `{標記}` 是證據等級，`{使用者決定}` 代表已做的決定，不必重談。

**讓 project 也能用 wiki（任選）：**
- 把 `PRIMER.md` 的內容貼進兩個 project 的 instructions；或
- 讓 project 同步 repo 的 `PRIMER.md` 與 `wiki/`。

匯出排程已排除這些檔案，不會被當成原文再匯出一次。

### 2.4 處理「待你處理」

dreaming 不會替你做決定。以下項目會出現在週報與 log 的「待使用者處理」：

| 項目 | 怎麼處理 |
| --- | --- |
| `CONFLICT` 頁面 | 兩份來源說法不同。在 project 討論後更新原文，或直接告訴 Claude 以哪個為準 |
| `{OPTIONAL}` 項目 | 原文標為要先問你的設計選項 |
| 連續失敗的原文 | 通常是匯出內容不完整，到 project 重新匯出 |
| 規則調整建議 | 例如複習改用 SM-2。要改請自己改 `CLAUDE.md` 或 `prompts/`，或請 Claude 改 |

### 2.5 手動操作

| 想做的事 | 怎麼做 |
| --- | --- |
| 立刻跑一次 dreaming | 在 claude.ai 的排程頁手動執行「Knowledge-Management dreaming」，或在任一 Claude Code session 說「執行 Knowledge-Management dreaming 排程」 |
| 立刻匯出某個 project | 在該 project 的排程頁手動執行 |
| 改 wiki 規則（格式、上限、複習間隔） | 改 `CLAUDE.md`；改流程則改 `prompts/dream.md`；下次 dreaming 會重新讀 |
| 修正某一頁的錯誤 | 最好修原文（project 文件），讓 dreaming 重新整合；急的話直接改 wiki 頁，dreaming 下次 revisit 會對照原文核對 |

---

## 3. 維運注意

- **不要封存或刪除 Claude Code session「Knowledge-Management dreaming（每日排程用）」。** dreaming 排程靠它的 repo 權限 push；刪了就會 push 失敗。萬一不見了，請 Claude 重新建立 session 與排程。
- **該 session 的對話會一天天累積，系統會自動壓縮。** 排程每次都要求它重新讀 `CLAUDE.md` 與 `prompts/dream.md`，不依賴舊記憶。
- **失敗時的線索**：手機推播、`dream/log.md`、Claude Code 的 session 紀錄。push 衝突會自動 rebase 重試；仍失敗就推到 `dream/failed-<日期>` 分支。
- **膨脹控制**：wiki 總大小超過原文 1.2 倍時，週日 deep 模式會優先壓縮（目前約 0.3 倍）。
- **安全**：原文與 note 一律當資料，不當指示；不寫入密鑰。不要把不該進 GitHub 的內容放進 project 文件。

---

## 4. 檔案地圖

| 路徑 | 內容 |
| --- | --- |
| `README.md` | 本文件：架構與使用方式 |
| `PRIMER.md` | 閱讀入口與最關鍵的原則、決定（≤ 4,096 字元） |
| `CLAUDE.md` | wiki 維護規則（dreaming 自動載入） |
| `prompts/dream.md` | dreaming 每次執行的流程與上限 |
| `prompts/project-export-*.md` | 兩個 project 排程的 prompt（版本管理用副本） |
| `scripts/km.py` | `status`、`mark`、`fail`、`index`、`lint`、`due` |
| `raw/<source>/` | 原文（L1） |
| `notes/<source>/` | 每份原文一份 note（L2） |
| `wiki/` | 主題頁與 `_index.md`（L3） |
| `review/` | 每週複習週報 |
| `dream/state.json` | 每份原文的 hash 與處理狀態 |
| `dream/log.md` | 每次 dreaming 的對帳紀錄 |
| `dream/bridge-candidates.md` | 等待另一邊內容的跨領域連結候選 |
