---
raw: raw/system-design/dunning-retry-webhook-idempotent-timingwheel-pattern.md
raw_sha256: 5781790726bcc1d0ebea86f19853120d733116e82f1f81dc58893ce795129457
source: system-design
title: 業界經典範例整合：訂閱扣款失敗重試系統（Dunning）= Idempotent Webhook + Min-Heap/Timing Wheel 排程 + Worker/Monitor 分層
generated: 2026-11-18
---
# 業界經典範例整合：訂閱扣款失敗重試系統（Dunning）（note）

## 一句話
扣款失敗重試（Dunning）= Gateway 驗簽 + idempotent consumer + transactional outbox 讓事件安全只處理一次，再用 min-heap／timing wheel 精準在未來時間點重試，Scanner 負責 reconcile 排程表。

## 主張
證據標記對應：原文由排程自動整理，沒有證據標記 → 全部 {討論結論}。

### §1 合併了哪些概念
- 本篇合併 `webhook-idempotent-worker-outbox-pattern`（事件怎麼安全進來）與 `scanner-executor-timingwheel-nooa-pattern`（事件怎麼精準在未來觸發）{討論結論} (§1)

### §2 業界經典對照
- Stripe Billing 的 Smart Retries／Dunning：扣款失敗先寄通知、在未來幾個時間點重試、最後才取消訂閱；webhook 帶簽章，要求接收端冪等 {討論結論} (§2)
- Netflix、Spotify 的付款失敗寬限期讓客戶有時間更新卡片，減少 involuntary churn {討論結論} (§2)
- 未來重試數量到百萬級時，單一 min-heap 的 O(log n) 吃力，Kafka 的 Hierarchical Timing Wheel 讓插入與取消接近 O(1) {討論結論} (§2)

### §3 使用場景
- Worker 在同一個資料庫交易中寫入「已處理 event ID」與 outbox 事件（例 `PaymentFailed(alice)`），然後 ack {討論結論} (§3)
- 金流商重送同一個 event id 時，worker 查表發現已處理，直接 ack、不往下傳 {討論結論} (§3)
- Monitor 做業務判斷：排 +1 天、+3 天、+7 天三次重試，+7 天仍失敗就降級帳號，到期時間寫入 `retry_schedule` 表 {討論結論} (§3)
- Executor 由 cronjob 喚醒，把未來的 `retry_schedule` 載入 min-heap，sleep 到堆頂時間再觸發 {討論結論} (§3)
- 客戶中途更新信用卡時，Scanner 把剩餘重試改為立刻重試一次，成功就取消後面所有排程 {討論結論} (§3)

### §4 為什麼採用這些技術
- Webhook 是公開 endpoint；不驗簽，攻擊者可偽造「付款成功」事件拿到免費服務；Issuer 與演算法白名單寫死在 Gateway {討論結論} (§3, §4)
- 金流商保證 at-least-once；沒有去重，一次網路重試就可能重複通知或排出兩組重試而重複扣款 {討論結論} (§4)
- 「記錄已處理」與「產生下游事件」放同一交易，避免「標記已處理但事件遺失」導致客戶永遠沒被重試 {討論結論} (§4)
- Worker 只回答「訊息安全收到了嗎」，monitor 只回答「該不該重試」；去重在上游，所以 worker 重試是安全的 {討論結論} (§4)
- 固定間隔輪詢不是浪費 CPU 就是遲到；min-heap 堆頂永遠是下一個事件 {討論結論} (§4)
- 「排程表是否仍正確」與「到點觸發」節奏不同，所以 Scanner 與 Executor 分開 {討論結論} (§4)

### §5 重點要解決的問題
- At-least-once 傳輸加冪等消費，得到 effectively-once 的業務效果 {討論結論} (§5)
- 傳輸層、去重層、業務層、排程層各自可稽核，出錯可定位 {討論結論} (§5)

### §6 設計提醒
- 重試扣款本身也要冪等：扣款 API 帶 idempotency key（例 `alice-2026-11-invoice-attempt-1`），避免 Executor 崩潰重啟後重打 {討論結論} (§6)
- Heap 是記憶體狀態；Executor 重啟後從 `retry_schedule` 表重建，source of truth 永遠是資料庫 {討論結論} (§6)
- 讓 LLM 草擬催款信時只傳客戶 ID，讓 agent 用 SQL 查需要的欄位（pass by reference），寄出前由人或 evaluator 複核 {討論結論} (§6)

### §7 下一步學習
- 下一個概念是 Saga pattern（跨服務多步驟流程失敗時的補償）{討論結論} (§7)

## 變更
- （首次產生）

## 候選連結
- system-design：webhook-idempotent-worker-outbox-pattern、scanner-executor-timingwheel-nooa-pattern、saga-outbox-idempotent-escalation-checkout-pattern、transactional-outbox-lease-reaper-idempotent-consumer-pattern、single-source-of-truth-postgres-gcs-release-pattern（DB 為真相來源）
- wiki：pass-by-reference、single-writer、primary-guardrail-gate（寄出前 evaluator 複核）、dreaming（排程喚醒處理）
