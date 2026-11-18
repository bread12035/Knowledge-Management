---
raw: raw/ai-new-tech/structure-of-agent-system.md
raw_sha256: 6e74d88e158e796c3a0f74b510b921816479e0dd6e5d4f82cbd273d818ba11c9
source: ai-new-tech
title: Structure of agent system
generated: 2026-11-18
---
# Structure of agent system（note）

## 一句話
使用者以檔案為中心的 agent system 骨架：CLAUDE.md 入口地圖、每任務一份 EXEC_PLAN、五層記憶與升級規則、三個省 token 機制、SQLite 到 MCP 的 scale-out，以及沿用 LLM wiki 的 Preprocess（L0 到 L2）。

## 主張
原文證據標記對應：[OpenAI] → {原文}、[報告] → {討論結論}（取自 hakka 研究報告）、[推論] → {我的判斷}、[一般知識] → {討論結論}。整份是使用者的設計，表格中的決策視為 {使用者決定}。

### §1 設計目標與七個決策
- 目標：任務可中斷後接續、記憶分層、token 成本可控、能從單機檔案擴充到資料庫 {使用者決定} (§1)
- 入口檔用 CLAUDE.md，沿用 OpenAI Tax AI 與 harness engineering 的檔案結構，不使用 worktree {使用者決定} (§1)
- 七個決策：入口地圖、EXEC_PLAN、記憶分層、不用 worktree、省 token、SQLite 到 MCP 的 scale-out、Preprocess {使用者決定} (§1)
- 核心原則：agent 執行時看不到的東西等於不存在，規則、決策、狀態都要寫成檔案或資料表 {原文} (§1)

### §2 檔案結構與入口地圖
- CLAUDE.md 約 100 行，像目錄不像百科；細節放 docs/，任務狀態放 tasks/<ID>/ {使用者決定} (§2)
- OpenAI 的超大指令檔失敗原因：擠掉任務 context、什麼都重要等於什麼都不重要、很快過時、無法用機制檢查 {原文} (§2)
- Progressive disclosure：先給小而穩定的入口，再教 agent 往哪裡找；skill 只先露出名稱與描述是第二層 {原文} (§2)
- 分工：CLAUDE.md 放永遠成立的規則，skill 放做某類事的步驟，output style 放怎麼說話 {我的判斷} (§2)
- 每個路徑有明確的寫入者：docs/ 由 agent 起草、人審查；evidence/ 由流程匯出、agent 不可改；knowledge/ 由 Preprocess 產生、不手改 {使用者決定} (§2)
- 不用 worktree：任務隔離靠 tasks/<ID>/、sandbox/<ID>/ 與唯讀 evidence/；改同一份程式碼的任務要排隊 {我的判斷} (§2, §9)

### §3 EXEC_PLAN
- EXEC_PLAN 是單一任務的工作記憶，自成一體、每個停點更新，新 session 只靠它就能接續 {原文} (§3)
- 必備章節：Purpose、Progress（帶時間戳 checkbox）、Surprises & Discoveries、Decision Log、Acceptance（可執行驗收指令）、Outcomes & Retrospective {原文} (§3)
- EXEC_PLAN 給人與冷啟動 session 讀；state.json 給每一步與 subagent 讀，只放決策結論，兩者不重複 {我的判斷} (§3)
- 小改動用一兩行輕量計畫，複雜功能或大型重構才寫完整 ExecPlan {原文} (§3)

### §4 Memory 五層與升級規則
- 五層依壽命與用途分：任務記憶（EXEC_PLAN、state.json）、任務結果（RESULTS.md、PR）、長期知識（docs/、skills）、失敗記憶（evals/、docs/failures/）、證據（evidence/、唯讀 DB）{使用者決定} (§4)
- 系統不依賴對話記憶，每個 session 從乾淨 context 開始，需要的內容從檔案或資料表讀回 {我的判斷} (§4)
- 失敗記憶只增不減：修好的問題變成永久的 regression 案例 {使用者決定} (§4)
- 升級規則 1：會影響未來任務的決策 → 抽成 docs/decisions/ 的 ADR {使用者決定} (§4)
- 升級規則 2：任何被修好的失敗 → 至少一個 eval 案例進 regression suite {使用者決定} (§4)
- 升級規則 3：同一類失敗出現第二次 → 在 docs/failures/ 寫說明，並在 CLAUDE.md 加一行指標 {使用者決定} (§4)
- 升級規則 4：RESULTS 中標示證據模糊的項目 → 不自動升級，交人判斷 {使用者決定} (§4)
- 讀取原則：不一次讀完所有層，先讀 CLAUDE.md 與當前任務記憶，再依指標往下走 {原文} (§4)
- 重要內容放在自己的檔案，Claude Code 內建記憶只當輔助，避免同一份知識存在兩處而分叉 {我的判斷} (§4)

### §5 三個省 token 機制
- 三個機制各管一種成本、可以疊加：pass by reference 管資料進 context、caveman 管輸出文字、SKILL.state 管跨步驟與跨 agent 的狀態傳遞 {使用者決定} (§5)
- 三個機制各有設定檔：`.claude/skills/pass-by-reference/SKILL.md`、`.claude/skills/skill-state/SKILL.md`、`.claude/output-styles/caveman.md` {使用者決定} (§5, 附錄 A)
- EXEC_PLAN、RESULTS、docs/ 是給人與冷啟動 session 讀的，保持完整句子，不套 caveman {我的判斷} (§5.2)
- 多個 subagent 不並行寫同一份 state.json，各寫自己的 patch 檔，由主 agent 合併 {我的判斷} (附錄 A.2)
- Output style 預設會拿掉 Claude Code 內建的軟體工程指令，設 `keep-coding-instructions: true` 才保留 {討論結論} (附錄 A.3)

### §6 Scale-out
- 儲存階層：S1 sandbox 內 SQLite 單檔 → S2 共用 .db 經 MCP 唯讀查詢 → S3 外部資料庫經 MCP {使用者決定} (§6)
- 換層只改取資料的後端，不改 agent 流程；文字記憶一直留在檔案，資料庫只放高量結構化資料 {使用者決定} (§6)
- SQLite 同一時間只能有一個寫入者（WAL 模式下讀者不被擋）；並行寫入變多是往 S2、S3 移動的主要訊號 {討論結論} (§6)
- MCP 工具規則：回傳 handle、欄位、列數與預覽不回全文；只提供唯讀查詢並強制 limit 與逾時；`fetch_to_sandbox(handle)` 落地細算；寫入走獨立工具並帶 task ID {我的判斷} (§6)

### §7 Preprocess
- Preprocess 是任務之外的整理階段：比對已完成與目標產出 next.md 與反問問題；把大資料整理成 L0、L1、L2 {使用者決定} (§7)
- 概念來源是 Karpathy 的 LLM wiki：raw/ 不可變、wiki/ 由 LLM 編譯維護、schema 檔規範做法；操作有 ingest、query、lint {討論結論} (§7)
- L0 原始層不可變、是事實來源；L1 整理層可由 L0 重跑；L2 摘要層可由 L1 重算，頁面小而有界才能進 context {使用者決定} (§7.2)
- L0 的 hash 改變時，對應的 L1、L2 失效並重跑；L2 頁面帶來源引用與產生時間，讓 agent 判斷是否過期 {我的判斷} (§7.2)
- 反問 User 時，每題附建議答案，並依對下一步的影響排序（沿用 hakka-vibe 的 grill-me）{使用者決定} (§7.1)
- 執行時機：任務結案後、新資料來源到達、開始新任務前（next.md 過期時）、定期 lint {我的判斷} (§7.3)
- 規則：Preprocess 只寫 knowledge/ 與 next.md，不改程式碼、evals、docs；能用程式做的不用 LLM；LLM 只讀聚合結果與有界樣本；任務 agent 讀取順序固定為 next.md、index.md、L2、L1、L0 {使用者決定} (§7.4)

### §8 端到端流程
- 任務是一條固定路徑：每一步把狀態寫回檔案，通過驗收才升級記憶，證據不足就標 needs-human 並停止 {使用者決定} (§8)
- 「通過」是 targeted eval 通過且 regression suite 沒有退步 {使用者決定} (§8)

### §9 取捨與待決問題
- 允許 agent 改 grader 能排除誤判雜訊，但可能為了通過而放寬標準；grader 變更在 RESULTS.md 單獨標註並由人審查 {使用者決定} (§9)
- CLAUDE.md 保持短的代價是 agent 可能漏讀指標，用 lint 檢查連結與新鮮度緩解 {我的判斷} (§9)
- 待決：多個 agent 並行寫同一份 state 如何處理衝突（SKILL.state 論文未測）{討論結論} (§9)
- 待決：Preprocess 自動產生的 next.md 品質怎麼驗證，建議前幾次由人審查 {我的判斷} (§9)
- 待決：L0 hash 改變就重跑 L1、L2，資料量大時重算成本多高 {我的判斷} (§9)

## 變更
- （首次產生）

## 候選連結
- 本 source：anthropic-agent-memory-guide（§14 對照表的另一端：五層記憶 ↔ 四層記憶、Preprocess ↔ Dreaming、L0 hash ↔ raw sha256）、hakka-agent-system-reference（§5 的證據來源）、agent-evaluation-harness-2-ab-test-guide（教訓升級閘門 ↔ 升級規則 3、4）、paired-test-guide（evals/ 的驗收方法）
- system-design：ADR、檔案權限與唯讀角色、SQLite WAL 與單一寫入者、MCP 工具設計、不用 worktree 時的並行策略
