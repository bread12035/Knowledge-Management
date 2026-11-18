---
raw: raw/system-design/data-freshness-watchdog-scanner-marker-golden-pattern.md
raw_sha256: 52cfab76784000119c09b93491c367433f692f921c28f46579749f028c2597df
source: system-design
title: 業界經典範例整合：Data Freshness Watchdog（Scanner/Executor + Completion Marker + Golden-Dataset Eval）
generated: 2026-11-18
---
# 業界經典範例整合：Data Freshness Watchdog（note）

## 一句話
Scanner 產生預期批次表，Executor 用 min-heap 睡到下一個 deadline 才檢查 completion marker，evaluator 過濾不值得通知的 alert，規則變更用 golden dataset 當回歸關卡。

## 主張
證據標記對照：原文沒有標記，一律 {討論結論}；「延伸一步」為未驗證建議，標 {我的判斷}。原文無編號章節，以章節名稱引用。

### §合併的概念
- Scanner 讓排程表保持新鮮；Executor 用 min-heap 只關心下一個 deadline，睡到那一刻才醒 {討論結論} (§這次合併了哪些概念)
- 用明確的完成標記判斷資料是否可讀，不猜固定時間緩衝 {討論結論} (§這次合併了哪些概念)

### §業界經典範例
- 這個組合就是 Data Observability / Freshness SLA 監控 {討論結論} (§業界經典範例)
- Airflow SLA Miss + Sensor：deadline 到了還沒看到成功訊號就發 SLA miss callback {討論結論} (§業界經典範例)
- Monte Carlo / Great Expectations 的 freshness check 檢查表在預期時間內有沒有新資料 {討論結論} (§業界經典範例)
- Iceberg / Hudi 的 commit 是否存在就是 completion marker {討論結論} (§業界經典範例)

### §使用場景
- 場景：on-prem 每 3 小時送一批 log 到雲端，每批有 `_SUCCESS` marker；只在某批超過 deadline 還沒 marker 時通知 {討論結論} (§使用場景)
- 流程：Scanner 產生預期批次表 → Executor 放進 min-heap 睡到最近 deadline → 醒來只問 marker 在不在，不在就產生 raw alert → Evaluator 擋掉不合理的 alert（例如維護窗口）→ 改規則先跑 golden dataset {討論結論} (§使用場景)

### §為什麼採用
- 輪詢要在精準度與 CPU 消耗間取捨；min-heap 只在 deadline 到時醒來 {討論結論} (§為什麼採用這些技術)
- 批次耗時不穩定：marker 是事件，時間差是猜測 {討論結論} (§為什麼採用這些技術)
- Generator（Executor）只負責發現遲到，不判斷該不該吵人；分離 evaluator 以避免 alert fatigue {討論結論} (§為什麼採用這些技術)
- 維護窗口、deadline 容忍度等規則會一直改，沒有固定測資每次改都是憑感覺 {討論結論} (§為什麼採用這些技術)
- `MarkerStore` 是 port：核心邏輯不知道 marker 在 S3、Iceberg 或本地檔；測試換 Fake adapter {討論結論} (§為什麼採用這些技術)

### §可執行範例
- 三組 golden case PASS：全到齊無 alert；logs_a 遲到產生 alert；兩者都缺時 logs_b 因維護窗口被 evaluator 擋掉，只剩 logs_a {討論結論} (§可執行範例)
- Executor 以注入的 `now_fn` / `sleep_fn` 驅動，測試時用假時鐘即可重現 {討論結論} (§可執行範例)

### §延伸一步
- `evaluate()` 換成 LLM evaluator（判斷 late_by 嚴重度、是否 page 人）時，golden dataset 要加模糊案例並保留 human-in-the-loop 最後確認 {我的判斷} (§延伸一步)

## 變更
- （首次產生）

## 候選連結
- system-design：trino-gateway-oidc-watermark-pattern、scanner-executor-timingwheel-nooa-pattern、structured-rag-golden-eval-hexagonal-pattern、pagerduty-escalation-chatops-runbook-pattern、price-watch-tiered-fetch-cas-outbox-freshness-pattern
- wiki：golden-dataset、promotion-gate、agent-harness-design（generator/evaluator 分離）、primary-guardrail-gate、error-analysis-loop、ai-evaluation
