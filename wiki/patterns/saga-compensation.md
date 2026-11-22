---
id: saga-compensation
title: Saga 與補償（Saga + compensation）
type: pattern
summary: 跨服務流程拆成多個本地交易，失敗先冪等重試，用盡就反向補償，補償失敗進 dead-letter 交人
domains: [system-design]
sources: [raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#3, raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#4, raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#7, raw/system-design/pagerduty-escalation-chatops-runbook-pattern.md#業界範例, raw/system-design/flash-sale-scheduled-release-pointer-saga-rollback-pattern.md#3, raw/system-design/flash-sale-scheduled-release-pointer-saga-rollback-pattern.md#6]
evidence: [討論結論]
related: [reliable-event-processing, transactional-outbox, idempotent-consumer, event-driven-timer, agent-system-memory-layers-x-saga-compensation, single-source-of-truth]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 0
next_review: 2026-11-29
---
# Saga 與補償（Saga + compensation）

> 跨服務流程拆成多個本地交易，失敗先冪等重試，用盡就反向補償，補償失敗進 dead-letter 交人

## 重點
- 三個服務不共用資料庫時用 Saga 取代 2PC：2PC 會鎖資源，協調者當機就卡住 {討論結論}
- 補償是新的業務動作，不是 rollback：已扣款不能撤銷只能退款 {討論結論}
- 四個問題四個解法：跨服務一致性 → Saga + 補償；重複動作 → idempotency key；流程中途斷 → outbox + lease reaper；補償失敗 → dead-letter + escalation {討論結論}
- 自動補償不是萬能，最後一道防線是人 {討論結論}
- Saga 狀態要存資料庫，記憶體狀態重啟就丟 {討論結論}

## 細節
- 範例：reserve → charge → ship；ship 用 key `o2:ship` 重試 3 次仍失敗 → refund → release，訂單標失敗；補償本身失敗 → dead-letter 並 page 值班 {討論結論}
- 出處：Garcia-Molina 1987；Temporal / Cadence、AWS Step Functions 把 Saga 狀態持久化 {討論結論}
- Orchestration 易除錯、choreography 耦合低但難追蹤；先用 orchestration {討論結論}
- 補償也適用於不支援 transaction 的資源：GCS 與 CDN 無法一起撤銷，所以準點開賣的 `switch` 補償是 `switch_back`（pointer 指回舊版）、`upload` 補償是 `keep_release`（不刪）；每步帶 key（`bf2026:switch_back`）防止 Executor 重啟後重送 {討論結論}
- Escalation policy（PagerDuty / Opsgenie）：未在時限內 ack 就自動升級下一層，計時器用 [[event-driven-timer]] {討論結論}

## 在設計中怎麼用
- 什麼情況用：跨多個服務、各自有資料庫的多步驟流程（結帳、開通、退款）。
- 怎麼用：每步定義正向動作與補償動作；補償必須可重複執行；每步用 [[transactional-outbox]] 發下一步；每步帶 idempotency key（[[idempotent-consumer]]）。
- 改流程前先跑三條 golden cases：全成功、中途失敗、補償失敗。
- 代價：流程中間狀態對外可見；補償邏輯要另外設計與測試。

## 相關
- [[reliable-event-processing]]：整體脈絡
- [[transactional-outbox]]、[[idempotent-consumer]]：每一步的基礎
- [[event-driven-timer]]：escalation 的計時
- [[single-source-of-truth]]：發布流程的補償就是 pointer 指回舊版
- [[agent-system-memory-layers-x-saga-compensation]]：跨領域：agent 的 needs-human 停止條件
