---
raw: raw/system-design/scanner-executor-timingwheel-nooa-pattern.md
raw_sha256: b1b7ce2df4f64cb2040fdc659a998f0d52b1a656d5f435bb2e14744200398b89
source: system-design
title: 業界經典範例整合：Scanner/Executor Reconciliation + Timing Wheel 排程 + NOOA Pass-by-Reference
generated: 2026-11-18
---
# 業界經典範例整合：Scanner/Executor Reconciliation + Timing Wheel 排程 + NOOA Pass-by-Reference（note）

## 一句話
Scanner 讓排程表貼近現實、Executor 用 min-heap／timing wheel 精準觸發（Reconciliation Loop + Precise Timer），觸發後的大量資料用 pass-by-reference 給 LLM 查詢，傳輸層錯誤與業務判斷分層處理。

## 主張
原文沒有證據標記，且是排程自動合併的整理文；一律標 {討論結論}。原文明說是使用者在 earnings-pipeline、coding-harness-design、engineering.md 裡做出的設計選擇時標 {使用者決定}。業界例子（Airflow、Quartz、Kafka）沒有附來源連結，也標 {討論結論}。

### §這次合併了哪些概念
- Earnings-pipeline 用兩個 cronjob 分工：Scanner 定期更新事件日期時間，Executor 偵測並觸發即將到來的事件 {使用者決定} (§合併概念)
- Executor 被 cronjob 喚醒後，在 pod 內改用 min-heap 做事件驅動排程，不用固定間隔輪詢 {使用者決定} (§合併概念)
- Coding-harness-design：NOOA 風格 typed state；大量資料用 pandas/SQLite pass by reference，不整包塞進 LLM context；generator/evaluator 搭配 human-in-the-loop {使用者決定} (§合併概念)
- 慣用專案結構：common/ 放共用基礎設施，worker 負責 pubsub 事件邏輯與 ack/nack（message seam），monitor 負責業務流程判斷，helper/utility 處理細節函式 {使用者決定} (§合併概念)
- 「naive RAG 不夠」與「大資料集不塞 context、用結構化查詢」是同一原則的兩種應用 {討論結論} (§合併概念)
- 四者共同指向 Reconciliation Loop + Precise Timer 模式 {討論結論} (§合併概念)

### §業界經典範例
- Airflow：Scheduler 掃 DAG 與 metadata DB 判斷該跑什麼（對應 Scanner），Executor（Celery/Kubernetes）負責執行 {討論結論} (§業界範例)
- Quartz 用優先權佇列（min-heap）管理 trigger：插入 O(log n)、取最近事件 O(1)；另有 misfire 偵測定期核對排程與現實是否脫節，角色近似 Scanner {討論結論} (§業界範例)
- Kafka Purgatory 管理百萬級延遲請求，用 hierarchical timing wheel 取代單一 min-heap，插入／刪除接近 O(1) {討論結論} (§業界範例)
- 規模選型：小規模用 min-heap 就夠，巨量並發才需要 timing wheel {討論結論} (§業界範例)

### §使用場景
- 例：Scanner 08:00 發現財報時間由 16:00 延到隔天早上，把變動寫回 DB {討論結論} (§使用場景)
- Executor 每 10 分鐘被 cronjob 喚醒，把未來事件載入 min-heap，用 sleep-until-next-event 迴圈精準觸發，避免晚到最多 9 分鐘 {討論結論} (§使用場景)
- 觸發 LLM 摘要時，幾百列歷史財務數字放進暫存 SQLite，讓 agent 用 SQL 查需要的欄位，不塞進 prompt {討論結論} (§使用場景)

### §為什麼採用
- Scanner 與 Executor 分開，因為「排程表更新」可容忍延遲，「事件觸發」錯過窗口就無意義；混在一起會互相拖累節奏 {討論結論} (§Why)
- 分開也是 deep-module 原則的延伸：介面窄、職責單一，一個模組只回答一個問題 {討論結論} (§Why)
- 固定間隔輪詢天生在精準度與資源消耗間取捨；min-heap 以 event-driven 取代 time-driven {討論結論} (§Why)
- 此原則與 log-pipeline-architecture 用 completion marker 取代固定時間緩衝相同：用訊號取代猜測的時間差 {討論結論} (§Why)
- Context 有限且昂貴：塞越多成本越高，模型也越容易在長 context 中漏掉細節；改讓 agent 用 SQL/pandas 查所需部分（typed state + code as action）{討論結論} (§Why)
- Worker 層 ack/nack 與 monitor 層業務判斷分層，才能分辨「傳輸問題該重試」與「業務邏輯錯、重試無用」{討論結論} (§Why)

### §重點要解決的問題
- 四個要解決的問題：精準度與資源取捨、排程表新鮮度與觸發精準度分開、不把大量資料塞進 context、分辨傳輸層與業務邏輯錯誤 {討論結論} (§重點問題)

### §延伸一步
- 觸發的動作會影響決策（交易員摘要、下單前置判斷）時，接 generator/evaluator：通過 evaluator 或真人核對才放行 {討論結論} (§延伸)
- 時間精準解決「什麼時候做」，human-in-the-loop 解決「做的內容對不對」，是兩個獨立互補的驗證層 {討論結論} (§延伸)

## 變更
- （首次產生）

## 候選連結
- system-design：pagerduty-escalation-chatops-runbook-pattern、dunning-retry-webhook-idempotent-timingwheel-pattern、data-freshness-watchdog-scanner-marker-golden-pattern、earnings-pre-earnings-gcp-to-onprem-handover-pattern、earnings-transcript-gcp-to-onprem-handover-pattern、webhook-idempotent-worker-outbox-pattern、structured-rag-golden-eval-hexagonal-pattern
- wiki：pass-by-reference、agent-harness-design、harness2、dreaming（排程維護）、progressive-disclosure（不整包塞 context）
