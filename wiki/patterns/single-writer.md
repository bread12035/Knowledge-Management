---
id: single-writer
title: 單一寫入者（Single writer）
type: pattern
summary: 每份資料只讓一個寫入者負責，從結構上消除並行寫入衝突
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#6.2, raw/ai-new-tech/structure-of-agent-system.md#2, raw/ai-new-tech/structure-of-agent-system.md#6, raw/ai-new-tech/structure-of-agent-system.md#9, raw/system-design/pessimistic-lock-vs-occ-cas-comparison.md#4, raw/system-design/rag-methods-comparison.md#5]
evidence: [原文, 我的判斷, 使用者決定, 討論結論]
related: [optimistic-concurrency, dreaming, skill-state, km-dreaming-design, agent-harness-design, pessimistic-lock]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 單一寫入者（Single writer）

> 每份資料只讓一個寫入者負責，從結構上消除並行寫入衝突

## 重點
- LAB 併購任務：多個 agent 寫同一張共享表，57 個事實只留 41 個（72%）；改成每份合約一頁後 57 個全留 {原文}
- 這個失敗本質是並行寫入衝突，修法是每頁只由一個 agent 寫 {我的判斷}
- 使用者的 agent system 每個路徑都標明誰寫：evidence/ 由流程匯出、agent 不可改；knowledge/ 只由 Preprocess 寫 {使用者決定}
- SQLite 同一時間只能有一個寫入者；並行寫入變多是往共用 DB 與外部 DB 升級的訊號 {討論結論}
- 多個 subagent 不並行寫同一份 state.json，各寫自己的 patch 檔，由主 agent 合併 {我的判斷}

## 細節
- 系統設計的對應：single writer queue（所有寫入排一條隊由一個 worker 處理，不用鎖）；table 設計時一個來源對應一列或一頁 {討論結論}{我的判斷}

## 在設計中怎麼用
- 什麼情況用：多個 agent、排程或 worker 會寫同一個儲存空間。
- 怎麼用：
  1. 依路徑、頁面或 key 範圍劃分擁有者，寫成文件（誰寫哪裡）。
  2. 需要合併時，讓各寫入者寫自己的檔，再由唯一的合併者整合。
  3. 共享的索引（例如 `_index.md`）只在最後由一個角色重建。
- 代價：合併者是瓶頸；擁有者劃分錯了，需要重新分工。
- 無法劃分擁有者時，退而求其次用 [[optimistic-concurrency]]。
- 這個 repo：producer 只寫 `raw/<source>/`，consumer 只寫 notes、wiki 等路徑；`_index.md` 由 `km.py index` 統一重建 {使用者決定}

## 相關
- [[optimistic-concurrency]]：無法單一寫入時的保護
- [[skill-state]]：多 agent 共享 state 的衝突問題
- [[dreaming]]：LAB 案例出處
- [[km-dreaming-design]]：這個 repo 的寫入者分工
- [[agent-harness-design]]：使用者 agent system 的路徑擁有者表
- [[pessimistic-lock]]：single writer queue 是並行寫入選項之一
