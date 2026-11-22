---
id: idempotent-consumer
title: 冪等消費與 idempotency key（Idempotent consumer）
type: pattern
summary: 用已處理事件 ID 或 idempotency key 去重，讓重送、重試、補償都只生效一次
domains: [system-design]
sources: [raw/system-design/webhook-idempotent-worker-outbox-pattern.md#使用場景, raw/system-design/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md#使用場景, raw/system-design/dunning-retry-webhook-idempotent-timingwheel-pattern.md#6, raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#4]
evidence: [討論結論, 我的判斷]
related: [reliable-event-processing, transactional-outbox, lease-reaper, saga-compensation, completion-marker]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# 冪等消費與 idempotency key（Idempotent consumer）

> 用已處理事件 ID 或 idempotency key 去重，讓重送、重試、補償都只生效一次

## 重點
- Webhook 與 relay 通常是 at-least-once；假設「短時間內不會重複」等於把正確性建在不可靠的假設上 {討論結論}
- Consumer 在一個 transaction 寫 `processed(event_id)` 與業務結果，之後才 ack；重複送達撞主鍵就直接 ack {討論結論}
- Lease 回收一定造成重複投遞，所以冪等是必要的，不是可選的 {討論結論}
- 去重在上游做掉後，worker 重試只是重送，不會重複觸發副作用，重試因此永遠安全 {討論結論}
- 呼叫外部 API 也要冪等：扣款帶 idempotency key（例 `alice-2026-11-invoice-attempt-1`），Saga 每步以 `{order}:{step}` 為 key {討論結論}

## 細節
- Stripe：驗簽後先回 200、處理丟背景 worker，用 event 的 idempotency key 判斷是否已處理 {討論結論}
- Consumer 是外部 HTTP 服務時，把 `event_id` 當 Idempotency-Key header 送出 {我的判斷}
- 沒有 idempotency key，Saga 的補償重送可能讓客戶被退款兩次 {討論結論}
- Idempotency key（單筆事件是否已處理）和 [[completion-marker]]（批次是否完整）是同一原則：用明確信號，不猜 {討論結論}

## 在設計中怎麼用
- 什麼情況用：任何可能重送的訊息、可能重跑的步驟、會呼叫外部有副作用 API 的地方。
- 怎麼用：選一個穩定的 key（事件 ID、業務 key + 步驟）→ 去重記錄與業務結果同一 transaction → 重複就回成功。
- 代價：要保存去重記錄（可設保留期）；key 設計錯會誤擋或漏擋。

## 相關
- [[reliable-event-processing]]：整體脈絡
- [[transactional-outbox]]、[[lease-reaper]]：重複投遞的來源
- [[saga-compensation]]：重試與補償都要冪等
- [[completion-marker]]：同一原則的批次版
