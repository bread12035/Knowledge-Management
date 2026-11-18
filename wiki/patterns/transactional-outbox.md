---
id: transactional-outbox
title: Transactional outbox（業務資料與事件同交易）
type: pattern
summary: 業務變更與要發出的事件寫進同一個 DB transaction，再由 relay 送出，避免資料改了事件沒發
domains: [system-design]
sources: [raw/system-design/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md#使用場景, raw/system-design/price-watch-tiered-fetch-cas-outbox-freshness-pattern.md#Why, raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#4, raw/system-design/dunning-retry-webhook-idempotent-timingwheel-pattern.md#4]
evidence: [討論結論, 我的判斷]
related: [reliable-event-processing, idempotent-consumer, lease-reaper, saga-compensation]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Transactional outbox（業務資料與事件同交易）

> 業務變更與要發出的事件寫進同一個 DB transaction，再由 relay 送出，避免資料改了事件沒發

## 重點
- 「先寫 DB 再發訊息」兩個動作不能同時成功；outbox 讓它們變成一個動作，同生共死 {討論結論}
- Producer 在一個 transaction 寫 `orders` 與 `outbox`，兩筆同時存在或同時不存在 {討論結論}
- Relay 是 at-least-once，所以 consumer 必須是 [[idempotent-consumer]] {討論結論}
- 在 Saga 中，「狀態更新」和「發下一步事件」要同一個交易，否則流程會中途斷掉 {討論結論}
- 價格監控：新價 ≠ 舊價才在同一 transaction 寫 `outbox(sku, old, new)`，變了一定發、沒變不發 {討論結論}

## 細節
- 出處：Chris Richardson（microservices.io）{討論結論}
- Worker 領 outbox 用 `FOR UPDATE SKIP LOCKED` 加 lease，當機由 [[lease-reaper]] 回收 {討論結論}
- 高吞吐時才考慮 Debezium CDC 讀 WAL 取代輪詢 outbox {我的判斷}
- 範例 golden cases：normal (1,1,1)、producer_crash (0,0,0)、worker_crash_then_retry (1,1,1)（orders, outbox, shipments 筆數）{討論結論}

## 在設計中怎麼用
- 什麼情況用：資料變更後必須通知下游（出貨、通知、下一步 Saga）。
- 怎麼用：outbox 表欄位至少 `event_id`、`payload`、`status`、`lease_until`、`attempts`；relay 領取、送出、ack；`attempts` 超過上限進 dead-letter。
- 代價：多一張表與一個 relay；事件有延遲。

## 相關
- [[reliable-event-processing]]：整體脈絡
- [[idempotent-consumer]]：outbox 的必要搭檔
- [[lease-reaper]]：relay 當機的回收
- [[saga-compensation]]：每一步都用 outbox
