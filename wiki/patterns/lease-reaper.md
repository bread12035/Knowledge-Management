---
id: lease-reaper
title: Lease 與 reaper（Postgres queue 的工作回收）
type: pattern
summary: 用 FOR UPDATE SKIP LOCKED 領工作並設 lease，到期沒 ack 由 reaper 放回，worker 當機不會卡死
domains: [system-design]
sources: [raw/system-design/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md#可執行範例, raw/system-design/pessimistic-lock-vs-occ-cas-comparison.md#4, raw/system-design/postgres-hub-hybrid-search-peer-spaced-repetition-pattern.md#業界經典範例]
evidence: [討論結論]
related: [reliable-event-processing, transactional-outbox, idempotent-consumer, event-driven-timer, pessimistic-lock, postgres-hub, seat-hold]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# Lease 與 reaper（Postgres queue 的工作回收）

> 用 FOR UPDATE SKIP LOCKED 領工作並設 lease，到期沒 ack 由 reaper 放回，worker 當機不會卡死

## 重點
- `FOR UPDATE SKIP LOCKED` 讓多個 worker 搶工作不重複，不必另養 Redis / RabbitMQ（River、Oban、GoodJob、Graphile Worker）{討論結論}
- 沒有 lease，worker 當機後事件會永遠卡在 `running` {討論結論}
- Lease lock 是悲觀鎖加過期時間：持有者掛掉時鎖自動失效 {討論結論}
- Reaper 用 min-heap 只看最近的 lease deadline，不必每秒掃全表（[[event-driven-timer]]）{討論結論}
- 回收必然造成重複投遞，所以要搭配 [[idempotent-consumer]] {討論結論}

## 細節
領工作：
```sql
UPDATE outbox SET status='running', lease_until=now()+interval '10 s', attempts=attempts+1
WHERE id=(SELECT id FROM outbox WHERE status='new' ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING id, event_id, payload;
```
- Reaper 放回時帶 `AND status='running'`，避免覆蓋已 ack 的事件 {討論結論}
- 等同 AWS SQS Visibility Timeout：領走後一段時間別人看不到，沒 ack 自動回來 {討論結論}

## 在設計中怎麼用
- 什麼情況用：工作量不大、想把 queue 和業務資料放同一個 DB（[[postgres-hub]]）。
- 怎麼用：設 lease 長度大於正常處理時間；`attempts` 上限後進 dead-letter；改 lease 時間或 reaper 邏輯先跑 golden cases。
- 代價：lease 太短會重複處理，太長會延遲回收。

## 相關
- [[reliable-event-processing]]：整體脈絡
- [[transactional-outbox]]：被領取的工作
- [[idempotent-consumer]]：回收後的重複
- [[event-driven-timer]]：reaper 的計時
- [[pessimistic-lock]]：lease lock 的分類
- [[postgres-hub]]：為什麼用 Postgres 當 queue
- [[seat-hold]]：同結構，到期回收的是資源（座位）
