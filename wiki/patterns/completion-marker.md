---
id: completion-marker
title: 用明確信號取代猜測的時間差（Completion marker）
type: pattern
summary: 用 completion marker、commit、idempotency key 這類明確信號判斷資料是否可讀或事件是否已處理，不用固定時間緩衝
domains: [system-design]
sources: [raw/system-design/trino-gateway-oidc-watermark-pattern.md#為什麼採用這些技術, raw/system-design/data-freshness-watchdog-scanner-marker-golden-pattern.md#為什麼採用這些技術, raw/system-design/webhook-idempotent-worker-outbox-pattern.md#業界經典範例]
evidence: [使用者決定, 討論結論]
related: [reliable-event-processing, event-driven-timer, idempotent-consumer, golden-regression-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 用明確信號取代猜測的時間差（Completion marker）

> 用 completion marker、commit、idempotency key 這類明確信號判斷資料是否可讀或事件是否已處理，不用固定時間緩衝

## 重點
- Log pipeline 用 completion marker 判斷資料是否可讀，取代固定時間緩衝；下游以事件同步 {使用者決定}
- 批次耗時不穩定：marker 是事件，時間差是猜測；太慢讀到舊資料，太快讀到半批 {討論結論}
- 低頻、低併發時資料完整性優先於即時性：寧可稍等拿完整資料 {討論結論}
- Completion marker（批次是否完整）與 idempotency key（單筆是否已處理）是同一原則的兩種場域 {討論結論}
- 「用訊號取代猜測的時間差」是使用者跨專案的原則，也和 message seam 的 ack/nack 同源 {使用者決定}

## 細節
- 實作：Hudi 的 `_SUCCESS` 檔或 commit metadata；Iceberg 的 snapshot / commit；下游只讀已提交的 snapshot {討論結論}
- Freshness watchdog：Scanner 產生預期批次表 → Executor 睡到 deadline → 只問 marker 在不在 → 不在才產生 raw alert → evaluator 擋掉維護窗口等不值得吵人的 alert {討論結論}
- 這就是 Data Observability / Freshness SLA（Airflow SLA miss、Monte Carlo freshness check）{討論結論}
- `MarkerStore` 是 port：核心邏輯不知道 marker 在 S3、Iceberg 或本地檔 {討論結論}

## 在設計中怎麼用
- 什麼情況用：下游要等上游「完成」才能讀；需要判斷「這件事做過了沒」。
- 怎麼用：上游完成時寫一個不可分割的標記；下游只看標記；遲到用 [[event-driven-timer]] 到 deadline 才檢查；規則改動用 [[golden-regression-gate]]。
- 代價：上游要負責寫標記；標記遺失會讓下游永遠等，要有 watchdog。

## 相關
- [[reliable-event-processing]]：整體脈絡
- [[event-driven-timer]]：deadline 到才檢查
- [[idempotent-consumer]]：同一原則的單筆版
- [[golden-regression-gate]]：watchdog 規則的回歸
