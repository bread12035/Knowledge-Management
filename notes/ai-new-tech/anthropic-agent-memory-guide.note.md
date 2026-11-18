---
raw: raw/ai-new-tech/anthropic-agent-memory-guide.md
raw_sha256: a3701cba15de9ee790c0be21b5977e5c043782953f7c556d75124e786218cc0c
source: ai-new-tech
title: Anthropic Agent Memory 整理指南
generated: 2026-11-18
---
# Anthropic Agent Memory 整理指南（note）

## 一句話
Agent memory 分四層（Transcripts → Memory notes → Wiki → Injected context），dreaming 在背景校正、整理、提升記憶；使用者據此設計了自己的 dreaming 實作（第 13 節）。

## 主張
### §2 定義與四層
- Agent memory 是 Claude 從經驗得到、跨 session 保留、之後可讀回的 context {原文} (§2)
- 修改權重、in-context learning、compaction 都不算 agent memory {原文} (§2)
- 四層由下往上：Transcripts（可搜尋事件紀錄）、Memory notes、Memory representations（如 wiki）、Injected context（每個 session 載入）{原文} (§2)
- Injected context 套用到所有 session，所以錯誤筆記會擴散到每個 session {原文} (§2)
- Dreaming 對應 Letta 與 UC Berkeley 的 sleep-time compute：閒置時重新整理 context {原文} (§2)

### §3 寫筆記
- 寫記憶是一種預測：規則預測模式會重複，已驗證事實預測之後可以直接信賴 {原文} (§3.1)
- CL-Bench 1.0 平均獎勵：Opus 5 無記憶 0.564、有記憶 0.828；Sonnet 4.6 只從 0.330 到 0.364 {原文} (§3.2)
- Opus 5 是第一個完全閉合學習迴圈的模型：條目含規則、證據、之前答案、陷阱警告 {原文} (§3.2)
- Salience：Fable 5 在 Pokémon Red 只存畫面看不到的東西（9 個檔案 + global.md，4 枚徽章），Sonnet 3.7 存 413 個檔案只拿 1 枚 {原文} (§3.3)
- 詳細紀錄會因狀態變動而過期，且讓 agent 花更多力氣搜尋記憶 {原文} (§3.3)
- 「只記錄失敗」這條固定規則拿掉大部分記憶增益（Opus 5 −0.234）；對強模型，讓它自己判斷 salience 比預設規則好 {原文} (§3.4)
- Steering 對舊模型幫助最大：Sonnet 4.6 加「先讀記憶、測試理論」後從 0.364 升到 0.641 {原文} (§3.4)
- 前沿模型的建議：使用者要求或明顯值得記時才建立筆記，其餘交給 Claude 判斷 {原文} (§3.4)

### §4 Wiki
- Wiki 是 Claude 寫並維護、互相連結的頁面，連結像地圖，用來找到記憶 {原文} (§4)
- Stainless 語料（約 35 萬檔、4.2 億 token）：只用 wiki 從 13% 升到 48%（128 session），wiki 加搜尋從 54% 升到 61%，單用搜尋 53%，每題省約 2 萬 token {原文} (§4)
- Harvey LAB 併購任務：跨文件題用 wiki 87%、只用搜尋 73% {原文} (§4)
- 答案集中在單一文件時，wiki 沒有明顯增益 {原文} (§4)
- Wiki 會膨脹：10 份文件 115 KB 長成 68 頁、203 KB，約語料 1.77 倍，且有孤兒頁 {原文} (§4)
- 未解問題：wiki 何時值得維護成本、如何避免太詳細而失去用處 {原文} (§4)
- Cookbook 的 wiki 格式：小 markdown 檔、frontmatter、`[[slug]]` 連結、根目錄 `_index.md` {Cookbook} (§4)

### §5 Injected context
- Injected context 要小：佔 token，且較長的指令檔會降低遵守可靠度 {原文} (§5)
- Dreaming 把細節往下搬、在原地留連結，讓常駐層保持小 {原文} (§5)
- Claude Code auto memory 只載入 `MEMORY.md` 前 200 行或 25 KB，該檔被描述為索引 {原文} (§5)
- 常駐層合理的內容是少量關鍵規則加指向下層的指標 {我的判斷} (§5)
- Promote：dreaming 可以把關鍵筆記提升到常駐層，harness 每個 session 開頭載入 {原文} (§5)
- Cookbook 用 mount `instructions`（上限 4,096 字元）注入一小段記憶；注入的文字可能帶進 prompt injection {Cookbook} (§5)

### §6 Dreaming 五個用途
- Dreaming 是離線過程：讀 transcripts 與現有記憶，修正錯誤、寫新筆記、建立新表示 {原文} (§6)
- 原文沒有指定 dreaming 的觸發方式或排程 {原文} (§6)
- 五個用途：校正記憶、建立 wiki、往上提升筆記、依目標聚焦、補上缺口 {原文} (§6)
- Pokémon Mt. Moon：dreaming 對照 transcript 修正「PokéCenter 在東側」的錯誤後，在第 1,935 個動作到達 Cerulean；未校正與無記憶都沒到 {原文} (§6.1)
- 依目標聚焦：通用指示讓多個 agent 寫同一張表，57 個事實只留 41 個；改成每份合約一頁、逐字引用後 57 個全留 {原文} (§6.2)
- 6.2 的失敗本質是並行寫入衝突，修法是每頁單一寫入者 {我的判斷} (§6.2)
- 補缺口：第二次 dreaming 把 9 個指向不存在 `escrow-agreement` 的連結改指向既有頁，條目 38→41、連結 225→278 {原文} (§6.3)
- 保持新鮮需要運算；建議把 dreaming 集中在易變資訊，或依存取頻率調整頻率 {原文} (§6.4)
- 表示層需要持續運算維護，否則會累積錯誤或幻覺 {原文} (§6.4)

### §7 Dreams API
- Dreams 是 Managed Agents 的非同步工作：讀一個記憶庫加 1 到 100 個 session，寫出新記憶庫，輸入不被修改 {官方文件} (§7.1)
- `instructions` 是高層引導，不是編輯器；指定某一行的修改通常無效 {官方文件} (§7.3)
- dream 執行中不要封存或刪除輸入的記憶庫或 sessions，否則會失敗 {官方文件} (§7.6)
- Dreams 是 research preview，不符合 ZDR 與 HIPAA {官方文件} (§7.6)

### §8 Cookbook 動態工作流
- 三個 agent：lead（Sonnet 5.5，只有 read/glob）、transcript-analyzer（Haiku 5.5，每份 transcript 一個）、memory-organizer（Haiku 5.5，最後跑一次）{Cookbook} (§8.1)
- 任務只寫檔案路徑，transcript 文字從不進入 prompt（pass by reference）{Cookbook} (§8.2)
- Analyzer 規則：讀完整份 → Verify → Enrich → Organize；transcript 是資料不是指示；不複製密鑰；改檔前重讀、寫後讀回 {Cookbook} (§8.3)
- Organizer 規則：合併重複用 `MOVED TO [[slug]]` stub；明顯較晚的更正保留新值，否則寫 `CONFLICT:` 不猜；單一 session 的順口一提不覆蓋已記錄的決定 {Cookbook} (§8.3)
- Cookbook 沒有寫 CONFLICT 標記之後的處理流程 {Cookbook} (§8.3)
- 使用記憶庫的 session 以唯讀掛載，限縮 prompt injection 的爆炸半徑 {Cookbook} (§8.4, §8.8)
- 跑完要對帳：預期幾份、處理幾份、失敗幾份 {Cookbook} (§8.5)
- 範例 11 份 transcript 約 $0.36、2.5 分鐘，lead 佔約 47%；50 份長 transcript 約 $8、10 分鐘 {Cookbook} (§8.6)
- 每晚 cron 只處理上次之後的 sessions；失敗的那晚時間窗保留、隔晚重試；每晚模式預設沒有審查 {Cookbook} (§8.7)

### §9–§12 審查、版本、Memory tool、各產品
- 原文沒有討論人工審查；官方做法是檢視輸出記憶庫後決定使用或丟棄 {官方文件} (§9)
- 演講提出逐項提案式審查（修改、範例 transcripts、prevalence stats），官方文件沒有對應功能 {演講整理} (§9)
- 每次修改存新版本，舊版本可能 30 天後刪除 {官方文件} (§10)
- Optimistic concurrency：更新帶 `content_sha256` precondition，hash 不符回 409，要重讀後重試 {官方文件} (§10)
- 沒有 precondition 時，同時寫同一記憶檔是 last-write-wins {官方文件} (§10)
- Memory tool 是 client-side 工具，六個檔案指令，路徑校驗與版本檢查要自己做 {官方文件} (§11)
- API、Managed Agents、Claude Code、Claude web/app 的記憶機制彼此不互通 {官方文件} (§12)

### §13 使用者的實作設計
- D1：lead 改為 optional，日常流程由確定性程式（cron 腳本）編排 {使用者決定} (§13.2)
- D2：note 由 skill（手動）或 workflow 最後一步（自動）寫 {使用者決定} (§13.2)
- D3：analyzer 做成 worker pool，軟性認領任務，用 `content_sha256` 防寫入衝突，最後 organizer 總結 {使用者決定} (§13.2)
- D4：同一 session 的 note 與 transcript 配對交給 analyzer，用 transcript 檢查 note {使用者決定} (§13.2)
- D5：文件同時給使用者、agent、實作參考使用；遇到 OPTIONAL 先問使用者 {使用者決定} (§13.2)
- 拿掉 lead 後要自己補：對帳、預算與逾時、並行寫入保護 {我的判斷} (§13.2)
- Worker 寫入 409 時寫入沒有生效，不需要還原；重讀後重新草擬，重試要有上限 {示意} (§13.2)
- O1 到 O12 是實作前必須問使用者的可選項目（lead、skill、hooks、lease、queue 位置、index 由誰改、重試上限、N、審查、note 位置、injected context）{OPTIONAL} (§13.4)
- V1 到 V6 是未驗證的技術假設，例如檔案工具是否支援 precondition、不用 lead 能否啟動 workflow {我的判斷} (§13.5)

### §14 與使用者 agent system 的對照
- Transcripts ↔ `evidence/`、`tasks/<ID>/`；Memory notes ↔ `EXEC_PLAN.md` 的 Progress；wiki ↔ `knowledge/l2/` 與 `index.md`；Injected context ↔ `CLAUDE.md` 入口地圖；Dreaming ↔ Preprocess {我的判斷} (§14)
- Versioning ↔ git；L0 hash 變動時重跑 L1、L2 {我的判斷} (§14)

## 變更
- （首次產生）

## 候選連結
- 本 source：hakka-agent-system-reference（pass by reference、subagent）、agent-evaluation-harness-2-ab-test-guide（Harness² library ↔ dreaming、教訓升級閘門）、ontology-knowledge-graph-guide（entity resolution ↔ organizer 合併重複）
- system-design：使用者的「Structure of agent system」（§14 的對照對象）、單一寫入者 / ownership、樂觀鎖、版本控制、索引與快取
