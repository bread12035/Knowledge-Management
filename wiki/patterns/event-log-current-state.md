---
id: event-log-current-state
title: Event log 為主、current state 由 view 算出
type: pattern
summary: 事實只追加寫進 event log，現在狀態用 view 或 materialized view 算；明細可算出餘額，餘額不能還原明細
domains: [system-design]
sources: [raw/system-design/rag-methods-comparison.md#Fact 存法, raw/system-design/rag-methods-comparison.md#和 SAG 比較]
evidence: [我的判斷, 討論結論]
related: [knowledge-retrieval-design, single-source-of-truth, skill-state-x-event-log-current-state]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# Event log 為主、current state 由 view 算出

> 事實只追加寫進 event log，現在狀態用 view 或 materialized view 算；明細可算出餘額，餘額不能還原明細

## 重點
- Fact 以 event log（只追加）為主，current state 由它用 view 或 materialized view 算出 {我的判斷}
- 明細可算出餘額，餘額不能還原明細 {我的判斷}
- 查某時間點狀態時，`buy` 與 `give` 兩側都要加 `event_time <= 該時間`，只加一側會算錯 {我的判斷}
- 抽取成欄位一定丟資訊；event log 加 `source` 欄位指回原文 {討論結論}
- 文字型方法存「故事」，每次查詢都要重讀推算最後狀態；structural DB 存「結果」直接讀 {討論結論}

## 細節
- 多表統整由輕到重：view（只存 SQL、不會變快）→ materialized view（查得快，資料變了要 `REFRESH`）→ 自建 catalog table（寫入時一起更新）{討論結論}
- SAG 只追加、不去重，適合事件型摘要，但不適合「現在狀態」（買了又送難處理）{我的判斷}

## 在設計中怎麼用
- 什麼情況用：狀態會被多次修改、需要知道「某時間點是什麼」或「為什麼變成這樣」。
- 怎麼用：寫入只 append 帶 `event_time` 與 `source` 的事件 → 用 view 算 current state → 查歷史時所有相關事件都加時間條件。
- 代價：查詢要計算；量大時用 materialized view 並管理刷新。

## 相關
- [[knowledge-retrieval-design]]：Fact 與 Understanding 分流
- [[single-source-of-truth]]：event log 是 SSOT、current state 是可重建的產物
- [[skill-state-x-event-log-current-state]]：跨領域：保留歷史還是只保留狀態
