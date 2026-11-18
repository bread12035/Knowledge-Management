---
id: reliable-event-processing
title: 可靠的事件處理（Reliable event processing）
type: topic
summary: at-least-once 傳輸下讓業務效果只發生一次：outbox、冪等消費、lease 回收、Saga 補償、精準計時、明確完成信號
domains: [system-design]
sources: [raw/system-design/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md#為什麼採用這些技術, raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#5, raw/system-design/dunning-retry-webhook-idempotent-timingwheel-pattern.md#5, raw/system-design/webhook-idempotent-worker-outbox-pattern.md#Why]
evidence: [討論結論, 使用者決定]
related: [transactional-outbox, idempotent-consumer, lease-reaper, saga-compensation, event-driven-timer, completion-marker, gateway-authn-service-authz, worker-monitor-split, golden-regression-gate, pessimistic-lock]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 可靠的事件處理（Reliable event processing）

> at-least-once 傳輸下讓業務效果只發生一次：outbox、冪等消費、lease 回收、Saga 補償、精準計時、明確完成信號

## 重點
- At-least-once 傳輸加冪等消費，得到 effectively-once 的業務效果 {討論結論}
- 每個失敗模式對應一個解法：資料改了事件沒發 → [[transactional-outbox]]；重複投遞 → [[idempotent-consumer]]；worker 當機卡住 → [[lease-reaper]]；跨服務一致性 → [[saga-compensation]]；補償失敗 → dead-letter + escalation {討論結論}
- 同步與去重的依據是明確信號，不是時間或次數的猜測（[[completion-marker]]、idempotency key）{討論結論}
- 何時做用 [[event-driven-timer]]；做的內容對不對用 generator/evaluator + 人，兩層獨立 {討論結論}
- 傳輸層、去重層、業務層、排程層各自可稽核，出錯可定位（[[worker-monitor-split]]）{討論結論}

## 細節
**一條典型路徑（webhook / dunning）** {討論結論}：
1. Gateway 驗簽（[[gateway-authn-service-authz]]）
2. Worker 查已處理事件 ID，重複就 ack；新事件在同一 transaction 寫「已處理」與 outbox，然後 ack
3. Relay 送出 outbox 事件；consumer 以 `event_id` 去重
4. Monitor 做業務判斷，必要時排未來重試到排程表
5. Executor 用 min-heap 睡到下一個時間點觸發；Scanner 維持排程表正確

**多份討論共同的設計提醒** {討論結論}：
- 記憶體狀態（heap、Saga 進度）重啟就丟，source of truth 永遠是資料庫
- 重試本身也要冪等：外部 API 帶 idempotency key
- 事件量不大時用 Postgres 當 queue，不另養 Kafka / Redis（見 [[postgres-hub]]）
- 把失敗路徑固定成 golden cases，改規則先跑（[[golden-regression-gate]]）
- 並行寫同一筆資料時，依重做成本選樂觀鎖或 [[pessimistic-lock]]

## 在設計中怎麼用
設計任何「收到事件 → 改資料 → 通知下游」的流程時，逐項檢查：
- 來源可信嗎？
- 重複會怎樣？
- 改資料和發事件會不會只成功一半？
- 處理者當機會卡住嗎？
- 跨服務失敗怎麼補償？
- 補償失敗由誰接手？

## 相關
- [[transactional-outbox]]、[[idempotent-consumer]]、[[lease-reaper]]、[[saga-compensation]]：四個核心模式
- [[event-driven-timer]]、[[completion-marker]]：時間與信號
- [[gateway-authn-service-authz]]、[[worker-monitor-split]]：分層
- [[golden-regression-gate]]：改規則前的回歸
- [[pessimistic-lock]]：並行寫入的選擇
