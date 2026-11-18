---
raw: raw/ai-new-tech/hakka-agent-system-reference.md
raw_sha256: 41c6ab110a6c8cc0b41c82f07b982ab0358a640924809a79e0bb0062804aacea
source: ai-new-tech
title: Hakka agent system reference
generated: 2026-11-18
---
# Hakka agent system reference（note）

## 一句話
設計 agent harness 時的省 token 決策依據：預設主對話多輪、大資料用 pass by reference、subagent handoff 用結構化 state，而 caveman 文體與 persistent subagent 都有條件限制。

## 主張
原文證據標記對應：✅ → {原文}（來源直接支持）、⚠️ → {討論結論}（需限定條件）、❓ → {我的判斷}（找不到證據）。

### §1 一頁摘要
- Caveman 降低 output token 有實測，但「降低 request 次數」與「subagent 表現下降」都沒有證據 {我的判斷} (§1)
- 能多輪對話解決就不要用 subagent；例外是大量輸出隔離與獨立可並行 {原文} (§1)
- SKILL.state 只在 single-agent 測過；用在 subagent 是延伸，未驗證 {討論結論} (§1)
- 「persistent subagent」有 resume、memory、fork 三種不同機制 {討論結論} (§1)

### §3.1 Caveman output style
- Caveman 讓 agent 用極簡文體回覆，code、指令、路徑、錯誤訊息保持原樣 {原文} (§3.1)
- 10 個 coding prompt 的 output token 平均 1214 → 294（−65%），範圍 22% 到 87% {原文} (§3.1)
- Skill 規則本身每輪約佔 1 到 1.5k input token；原本就簡短的工作可能反而虧錢 {原文} (§3.1)
- Output style 版不影響 subagent，因為 subagent 用自己的 system prompt（fork 除外）{原文} (§3.1)
- 建議只在主對話敘述使用；subagent 回報用結構化欄位，不靠文體壓縮 {討論結論} (§3.1)

### §3.2 多輪對話 vs subagent
- Claude Code 準則：來回修改、共享大量 context、小而準的修改、延遲敏感 → 主對話 {原文} (§3.2)
- 產生大量之後不再引用的輸出、需要限制工具或權限、自足只回摘要 → subagent {原文} (§3.2)
- Subagent 從新 context 開始，要重新載入 system prompt、CLAUDE.md、git status、skills、任務訊息；回傳結果還會佔主 context {原文} (§3.2)
- 論文（arXiv 2609.09233）：鬆散知識放主 context 較好；只有「有明確輸入輸出契約的程序抽象」subagent 才有優勢 {討論結論} (§3.2)
- 決策流程：需要之前對話 → 主對話或 fork；產出大且不再引用 → subagent；子任務獨立可並行 → 多個 subagent；否則主對話多輪 {原文} (§3.2)

### §3.3 Pass by reference（NVIDIA NOOA）
- 模型只看變數名加有界預覽（型別、長度、頭尾樣本），完整物件留在執行環境，模型寫 code 操作 {原文} (§3.3)
- SWE-bench Verified：NOOA 82.2%、約 28 次呼叫、1.1M token，對比 PI 78.2%、66 次、2.2M token；這是整體 harness 比較，不能單獨歸功 pass by reference {原文} (§3.3)
- Context 排版為 KV-cache 設計：靜態前綴在前、事件歷史只追加、變動區塊放尾端 {原文} (§3.3)
- 判準：資料的完整內容有沒有變成 prompt 字元；用 SQL 取 10 列再貼進 prompt 仍是 pass by value {原文} (§3.3)
- 只給檔案路徑屬弱的 reference；MCP 工具回傳的 JSON 會整包進 context，應回傳 handle 加預覽 {原文} (§3.3)
- 資料不進 context 就沒有對應的 cache write，但論文沒有單獨拆出數字 {我的判斷} (§3.3)

### §3.4 SKILL.state（Google，arXiv 2608.26263）
- 每步只給模型程序規格 P、結構化狀態 Σt、最新觀察 Ot；推理用完即丟，prompt 大小 O(1)、累積 token O(T)，歷史累加是 O(T²) {原文} (§3.4)
- 模型輸出 state patch（key 設 null 代表刪除），runtime 驗證後合併 {原文} (§3.4)
- Warehouse T=200：SKILL.state 準確率 0.94、約 122k token；摘要式 memory 0.84、約 6.2M token {原文} (§3.4)
- 預算匹配對照：滑動視窗 0.18、摘要 0.52、LLMLingua 0.22、結構化 state 0.94；關鍵是結構化，不是縮短 {原文} (§3.4)
- Schema 每個 domain 寫一次，CTF 100 題共用 5 欄位 schema {原文} (§3.4)
- 失效情境：事先不知道 schema、早期觀察當時沒被認為重要、任務目標本身是歷史（稽核、追溯）{原文} (§3.4)
- 小模型的失敗 68% 是誤刪既有 key，patch 要用合併語意並由 runtime 驗證、失敗 rollback {原文} (§3.4)
- Subagent handoff state 放：目標、已確定決策、資料 handle、未解問題、完成條件；不放推理過程、完整 log、已取代的假設 {我的判斷} (§3.4)

### §3.5 Persistent subagent
- Resume 保留同一 instance 的完整歷史，可讀回暖好的 cache，但歷史變長又回到 O(T²) {原文} (§3.5)
- `memory` 欄位是知識持久，不是 process 持久；載入 `MEMORY.md` 前 200 行或 25KB {原文} (§3.5)
- Fork 首次 request 重用主 session cache，比新開 subagent 便宜，但繼承全部 context {原文} (§3.5)
- `omitClaudeMd: true` 讓自訂 subagent 不載入 CLAUDE.md；Explore 與 Plan 內建跳過 CLAUDE.md 與 git status {原文} (§3.5)
- Cache 過 TTL 後再 resume，推論上要重新付 cache write {我的判斷} (§3.5)

### §4 Hakka vibe 專案
- Hakka vibe 是可重用的 Python agent harness，加上量測各種 harness 設計省多少 token 成本的實驗 {原文} (§4)
- Agent = Python class，method 是 capability，field 是 typed state；DataRef 是指向 process 內大量資料的薄引用 {原文} (§4)
- 實驗結構：Experiment（每個只動一個變因）→ Arm → Run（每 arm 3 次）；baseline 少於 8 輪視為太簡單（calibration gate）{原文} (§4)
- 成本一律換算美元；cache write 分 1h 與 5m 兩種單價；thinking token 計為 output {原文} (§4)
- 開發四階段：釐清需求 → 需求轉任務 → implement + tdd → 定期審核架構；`/code-review` 以 Standards 與 Spec 兩軸並行 {原文} (§4)

### §6 給 agent 的操作規則
- 預設主對話多輪；只有大量輸出隔離、需限制工具、自足且有 I/O 契約、獨立可並行才派 subagent {討論結論} (§6)
- 大資料落地 sandbox，context 只放 handle、預覽與聚合結果 {討論結論} (§6)
- 派 subagent 用 state JSON 傳 handoff，不貼對話歷史；回報也用結構化欄位 {討論結論} (§6)
- 是否採用省 token 手法以美元 cost model 實測為準，不憑 token 數字 {討論結論} (§6)

## 變更
- （首次產生）

## 候選連結
- 本 source：anthropic-agent-memory-guide（Cookbook pass by reference、MEMORY.md 200 行、subagent 當 analyzer）、agent-evaluation-harness-2-ab-test-guide（一次只動一個變因、cost model）
- system-design：handle / reference vs copy、cache 設計（前綴穩定、append-only）、state machine 與 patch 合併語意、event sourcing（任務目標是歷史時）
