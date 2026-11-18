---
id: pass-by-reference
title: Pass by reference（資料留在環境，prompt 只放引用）
type: pattern
summary: 大資料留在執行環境，context 只放 handle 與有界預覽，模型寫程式取聚合結果
domains: [ai-new-tech]
sources: [raw/ai-new-tech/hakka-agent-system-reference.md#3.3, raw/ai-new-tech/structure-of-agent-system.md#5.1, raw/ai-new-tech/structure-of-agent-system.md#6, raw/ai-new-tech/anthropic-agent-memory-guide.md#8.2]
evidence: [原文, 討論結論, 我的判斷, Cookbook, 使用者決定]
related: [agent-harness-design, skill-state, dreaming]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Pass by reference（資料留在環境，prompt 只放引用）

> 大資料留在執行環境，context 只放 handle 與有界預覽，模型寫程式取聚合結果

## 重點
- 模型只看變數名加有界預覽（型別、真實長度、頭尾樣本），完整物件留在環境，只有模型選擇印出的小結果進 context（NVIDIA NOOA）{原文}
- 判準：資料的完整內容有沒有變成 prompt 字元；用 SQL 只取 10 列再貼進 prompt 仍是 pass by value {原文}
- 只給檔案路徑是弱的 reference：沒有型別，要自己從文字重建 {原文}
- MCP 工具的回傳會整包進 context，所以工具要回傳 handle 加預覽，不回全文 {原文}
- Cookbook 的 dreaming 也是這樣：任務只寫 transcript 路徑，文字從不進 lead 的 prompt {Cookbook}

## 細節
- SWE-bench Verified：NOOA 82.2%、約 1.1M token；PI 78.2%、約 2.2M token。這是整體 harness 比較，不能單獨歸功 {原文}
- 資料不進 context 就沒有對應的 cache write，但論文沒有單獨拆出數字 {我的判斷}
- 小模型較不守 code-as-action 紀律：批次 bookkeeping 壓力測試通過率 70.8%，大模型 93.9% {原文}
- 範例：50 萬列 CSV 落地到 `sandbox/<ID>/data.db`，context 只放 `df = DataFrame(rows=500000, cols=12, head/tail 各 5 列)`，模型寫 `groupby` 只印聚合結果 {討論結論}

## 在設計中怎麼用
- 什麼情況用：檔案、查詢結果、trace、log 大到不該整份讀進 context。
- 怎麼用：
  1. 資料落地到 sandbox（SQLite 或 DataFrame）。
  2. context 只放 handle、欄位、列數與預覽。
  3. 用程式取聚合或有界樣本；結果也落地，不貼回 prompt。
  4. handle 寫進 state 的 `refs`，交接時傳 handle。
- MCP 工具規則：只回 handle 與預覽、唯讀、強制 limit 與逾時、另提供 `fetch_to_sandbox(handle)` {我的判斷}
- 代價：agent 要會寫程式；小模型紀律差，要提供預寫的查詢工具與範例。

## 相關
- [[agent-harness-design]]：三個省 token 機制之一
- [[skill-state]]：state 的 `refs` 放 handle
- [[dreaming]]：Cookbook 用路徑派工給 analyzer
