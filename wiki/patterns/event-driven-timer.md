---
id: event-driven-timer
title: Scanner + Executor 與事件驅動計時（Reconciliation loop + precise timer）
type: pattern
summary: Scanner 讓排程表貼近現實，Executor 用 min-heap 或 timing wheel 睡到下一個事件才醒，取代固定間隔輪詢
domains: [system-design]
sources: [raw/system-design/scanner-executor-timingwheel-nooa-pattern.md#Why, raw/system-design/dunning-retry-webhook-idempotent-timingwheel-pattern.md#3, raw/system-design/data-freshness-watchdog-scanner-marker-golden-pattern.md#使用場景, raw/system-design/pagerduty-escalation-chatops-runbook-pattern.md#Why]
evidence: [使用者決定, 討論結論]
related: [reliable-event-processing, completion-marker, lease-reaper, saga-compensation, worker-monitor-split]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Scanner + Executor 與事件驅動計時（Reconciliation loop + precise timer）

> Scanner 讓排程表貼近現實，Executor 用 min-heap 或 timing wheel 睡到下一個事件才醒，取代固定間隔輪詢

## 重點
- Earnings-pipeline 用兩個 cronjob 分工：Scanner 定期更新事件時間，Executor 被喚醒後在 pod 內用 min-heap 事件驅動觸發 {使用者決定}
- 分開的理由：排程表更新可容忍延遲，事件觸發錯過窗口就無意義；混在一起會互相拖累 {討論結論}
- 固定間隔輪詢天生在精準度與資源間取捨；min-heap 堆頂永遠是下一個事件 {討論結論}
- 規模選型：小規模 min-heap（插入 O(log n)、取最近 O(1)）；百萬級用 hierarchical timing wheel（Kafka Purgatory，接近 O(1)）{討論結論}
- Heap 是記憶體狀態；重啟後從資料庫的排程表重建，source of truth 是資料庫 {討論結論}

## 細節
- Executor 每 10 分鐘被喚醒，載入未來事件到 min-heap 後 sleep-until-next-event，避免晚到最多 9 分鐘 {討論結論}
- 同一個結構出現在：dunning 重試（+1、+3、+7 天）、事故升級（5 分鐘沒 ack 就升級）、lease reaper、data freshness watchdog（睡到 deadline 才查 marker）{討論結論}
- 業界對照：Airflow Scheduler / Executor、Quartz 的 trigger 佇列與 misfire 偵測 {討論結論}
- 以注入的 `now_fn` / `sleep_fn` 驅動，測試時用假時鐘即可重現 {討論結論}

## 在設計中怎麼用
- 什麼情況用：大量「在未來某時間點做某事」的計時（重試、升級、到期檢查）。
- 怎麼用：資料庫存排程表 → Scanner 依現實更新（改期、取消、提前）→ Executor 載入 heap、睡到堆頂 → 觸發後由 monitor 做業務判斷。
- 代價：多一個常駐行程；重啟要重建；時間精準只回答「何時做」，「做得對不對」要另外驗證。

## 相關
- [[reliable-event-processing]]：整體脈絡
- [[completion-marker]]：醒來之後問的是信號，不是時間
- [[lease-reaper]]、[[saga-compensation]]：計時的應用
- [[worker-monitor-split]]：觸發後的分層
