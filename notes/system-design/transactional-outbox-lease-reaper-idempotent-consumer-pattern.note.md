---
raw: raw/system-design/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md
raw_sha256: b8d1c3926b92b268ecf4fa5409fd4a8535abbeb6ca40d28033f08afab76dae39
source: system-design
title: 業界經典範例整合：Transactional Outbox + Postgres Queue（Lease）+ Idempotent Consumer + Lease Reaper
generated: 2026-11-18
---
# 業界經典範例整合：Transactional Outbox + Postgres Queue（Lease）+ Idempotent Consumer + Lease Reaper（note）

## 一句話
業務資料與事件同一個 transaction 寫入 outbox，worker 用 `FOR UPDATE SKIP LOCKED` 加 lease 領取，reaper 回收過期 lease，consumer 以 `event_id` 主鍵去重，讓 at-least-once 投遞變成只出貨一次。

## 主張
證據標記對照：原文沒有標記，一律 {討論結論}；「延伸一步」為未驗證建議，標 {我的判斷}。原文無編號章節，以章節名稱引用。

### §業界經典範例
- Transactional Outbox（Chris Richardson, microservices.io）：業務資料與要發出的事件寫在同一個 transaction {討論結論} (§業界經典範例)
- River / Oban / GoodJob / Graphile Worker 是 Postgres job queue：用 `FOR UPDATE SKIP LOCKED` 領工作，用 lease 加 rescuer 回收死掉的 worker {討論結論} (§業界經典範例)
- AWS SQS Visibility Timeout：領走後一段時間別人看不到，沒 ack 時間到自動回來 {討論結論} (§業界經典範例)
- Stripe idempotency key：重複請求只執行一次 {討論結論} (§業界經典範例)

### §使用場景
- Producer 在一個 transaction 寫 `orders` 與 `outbox`，兩筆同時存在或同時不存在 {討論結論} (§使用場景)
- Claim 時狀態改為 `running` 並設 `lease_until = now+10`，`attempts += 1` {討論結論} (§使用場景、§可執行範例)
- Consumer 在一個 transaction 寫 `processed(event_id)` 與業務結果（`shipments`），之後才 ack 成 `done` {討論結論} (§使用場景)
- Worker 在處理後、ack 前當機時，reaper 在 lease 過期後把事件放回 `new`；第二次處理撞 `processed` 主鍵衝突直接 ack，出貨只有 1 筆 {討論結論} (§使用場景)

### §為什麼採用
- 「先寫 DB 再發訊息」兩個動作不能同時成功；outbox 讓它們變成一個動作 {討論結論} (§為什麼採用這些技術)
- 事件量不大時用 Postgres queue 而不另養 Kafka/Redis：一個 DB、一個備份，事件與業務資料共用 transaction {討論結論} (§為什麼採用這些技術)
- 沒有 lease，worker 當機後事件會永遠卡在 `running` {討論結論} (§為什麼採用這些技術)
- Reaper 用 min-heap 只看最近的 lease deadline，不必每秒掃全表 {討論結論} (§為什麼採用這些技術)
- Lease 回收一定造成重複投遞，所以 idempotent consumer 是必要的，不是可選的 {討論結論} (§為什麼採用這些技術)
- 三種失敗路徑固定成 golden cases；改 lease 時間或 reaper 邏輯先跑一次再上線 {討論結論} (§為什麼採用這些技術)

### §可執行範例
- 正式環境領工作語句：`UPDATE outbox SET status='running', lease_until=now()+interval '10 s', attempts=attempts+1 WHERE id=(SELECT id FROM outbox WHERE status='new' ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING id, event_id, payload` {討論結論} (§可執行範例)
- Reaper 放回時帶 `AND status='running'` 條件，避免覆蓋已 ack 的事件 {討論結論} (§可執行範例)
- SQLite 模擬三組 golden case PASS：normal (1,1,1)、producer_crash (0,0,0)、worker_crash_then_retry (1,1,1)（orders, outbox, shipments 筆數）{討論結論} (§可執行範例)

### §延伸一步
- `attempts` 超過上限（例如 5）移到 dead-letter，交給 PagerDuty 式 escalation {我的判斷} (§延伸一步)
- consumer 是外部 HTTP 服務時，把 `event_id` 當 Idempotency-Key header 送出 {我的判斷} (§延伸一步)
- 高吞吐時才考慮用 Debezium CDC 讀 WAL 取代輪詢 outbox {我的判斷} (§延伸一步)

## 變更
- （首次產生）

## 候選連結
- system-design：webhook-idempotent-worker-outbox-pattern、saga-outbox-idempotent-escalation-checkout-pattern、price-watch-tiered-fetch-cas-outbox-freshness-pattern、scanner-executor-timingwheel-nooa-pattern、dunning-retry-webhook-idempotent-timingwheel-pattern、pagerduty-escalation-chatops-runbook-pattern、postgres-hub-hybrid-search-peer-spaced-repetition-pattern
- wiki：single-writer、optimistic-concurrency、golden-dataset、promotion-gate
