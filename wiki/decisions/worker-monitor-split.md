---
id: worker-monitor-split
title: 使用者的專案分層：common / worker / monitor / helper
type: decision
summary: worker 管訊息傳輸與 ack/nack，monitor 只做業務判斷，common 放共用基礎設施；對應 hexagonal 的 adapter、core、port
domains: [system-design]
sources: [raw/system-design/scanner-executor-timingwheel-nooa-pattern.md#合併概念, raw/system-design/webhook-idempotent-worker-outbox-pattern.md#合併的概念, raw/system-design/structured-rag-golden-eval-hexagonal-pattern.md#業界經典範例, raw/system-design/data-freshness-watchdog-scanner-marker-golden-pattern.md#為什麼採用這些技術]
evidence: [使用者決定, 討論結論]
related: [reliable-event-processing, gateway-authn-service-authz, event-driven-timer, golden-regression-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 使用者的專案分層：common / worker / monitor / helper

> worker 管訊息傳輸與 ack/nack，monitor 只做業務判斷，common 放共用基礎設施；對應 hexagonal 的 adapter、core、port

## 重點
- 慣用結構：common/ 放共用基礎設施，worker 負責 pubsub 事件與 ack/nack（message seam），monitor 負責業務流程判斷，helper/utility 處理細節函式 {使用者決定}
- 分層才能分辨「傳輸問題該重試」與「業務邏輯錯、重試無用」{討論結論}
- 使用者習慣以 module / seam 邊界當 fixed point，每次改動後複查過去結果是否還成立 {使用者決定}
- 對應 Hexagonal Architecture（Ports & Adapters）：worker ≈ adapter、monitor ≈ 核心邏輯、common ≈ port 定義 {討論結論}
- 換掉 pubsub（例如改 Kafka）時核心邏輯不必改 {討論結論}

## 細節
- Web 層驗證格式失敗回 4xx 讓上游重試；背景 job 判斷「不觸發」是成功處理但決定不動作，兩者不應混在同一層 {討論結論}
- Port 的例子：`MarkerStore`、`EntityExtractor`、`Source`；測試換 Fake adapter（字典、假時鐘、FakeSource），核心邏輯不變且測試可重複 {討論結論}
- Monitor 層可再接 generator / evaluator：generator 提建議，evaluator 或真人在執行前核對 {討論結論}

## 在設計中怎麼用
- 新服務照這個分層開目錄；每個外部依賴先定 port 再寫 adapter。
- 除錯時先問：傳輸層沒收到，還是收到了但業務判斷錯？兩者由不同人、用不同方式修。

## 相關
- [[reliable-event-processing]]：事件流程中的位置
- [[gateway-authn-service-authz]]：worker 之前的驗證層
- [[event-driven-timer]]：Executor 觸發後交給 monitor
- [[golden-regression-gate]]：port 讓核心邏輯可用固定案例回歸
