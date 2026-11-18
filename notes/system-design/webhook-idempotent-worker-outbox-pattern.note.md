---
raw: raw/system-design/webhook-idempotent-worker-outbox-pattern.md
raw_sha256: c717a3983947a4adbf6933c8090c7983ff1232b652d66c4db3848c800315bb36
source: system-design
title: 業界經典範例整合：Idempotent Webhook Gateway + Worker/Monitor 職責分離 + Explicit Completion Signal（Transactional Outbox 模式）
generated: 2026-11-18
---
# 業界經典範例整合：Idempotent Webhook Gateway + Worker/Monitor 職責分離 + Explicit Completion Signal（Transactional Outbox 模式）（note）

## 一句話
接收 webhook 要分三層：Gateway 集中驗簽（Authentication）、worker 用「已處理事件 ID」去重並負責 ack/nack、monitor 只做業務判斷；同步與去重的依據是明確信號，不是時間或次數的猜測。

## 主張
原文是排程自動整理的合併文，沒有證據標記：使用者既有的慣例與設計（engineering.md 分層、log-pipeline completion marker、chat-service auth 分層）→ {使用者決定}；Stripe/GitHub/microservices.io 的描述是轉述，不是一手引用 → {討論結論}；其餘 → {討論結論}。

### 合併的概念
- Worker 負責 pubsub 訊息層的例外與 ack/nack（訊息有沒有處理成功），monitor 負責業務判斷（這件事該不該發生），兩者職責分離 {使用者決定} (合併的概念)
- log-pipeline-architecture 用明確的 completion marker 判斷資料可讀，取代固定時間緩衝；下游以事件而非時間同步 {使用者決定} (合併的概念)
- chat-service-auth-design：Gateway 做 Authentication，後端做 Authorization；issuer 與演算法白名單寫死在 Gateway，不信任呼叫方宣稱的來源 {使用者決定} (合併的概念)
- 接收外部事件有三個缺一不可的層面：來源是否合法（access）、是否已處理過（idempotency）、傳輸失敗與業務判斷如何分開（worker vs monitor）{討論結論} (合併的概念)

### 業界經典範例
- Stripe 每個 event 帶簽章，接收端第一步驗證是否由 webhook secret 簽出，這一步獨立於業務邏輯 {討論結論} (業界經典範例)
- Stripe 建議驗證後先回 200，把處理丟給背景 worker，並用 event 的 idempotency key 判斷是否已處理，避免網路重試造成重複扣款 {討論結論} (業界經典範例)
- GitHub webhook 在 header 帶 `X-Hub-Signature`；Web 層只驗簽、丟進 job queue（Sidekiq / Resque）、立刻回應，業務判斷留給背景 job {討論結論} (業界經典範例)
- Web 層驗證格式失敗回 4xx 讓上游重試；背景 job 判斷「分支不在白名單、不觸發」是成功處理但決定不動作，兩者不應混在同一層 {討論結論} (業界經典範例)
- Transactional Outbox（Chris Richardson, microservices.io）：業務資料變更與要發出的事件寫進同一個資料庫 transaction，避免資料改了事件沒送或反之 {討論結論} (業界經典範例)
- Idempotent Consumer：at-least-once 傳輸下以「已處理事件 ID」記錄判斷重複，不重複執行業務邏輯 {討論結論} (業界經典範例)
- Completion marker（批次是否完整）與 idempotency key（單筆事件是否已處理）是同一原則的兩種場域：同步與去重的依據應是明確信號，不是時間或次數的猜測 {討論結論} (業界經典範例)

### 使用場景
- Gateway 驗證請求簽章是否用雙方約定的 secret 簽出，issuer 與允許演算法寫死在 Gateway，不接受請求自稱的身份；Gateway 不做業務決定，只把已驗證事件轉給 worker {討論結論} (使用場景)
- Worker 先查事件 ID 是否在「已處理事件」記錄中；重複送達就直接 ack、不往下傳 {討論結論} (使用場景)
- 新事件才放進 queue 受 ack/nack 保護；網路層失敗 nack 讓上游重試，與業務邏輯無關 {討論結論} (使用場景)
- Monitor 讀到的是「已驗身份、保證只處理一次」的事件，只判斷狀態是否轉換（例如處理中 → 已完成）、是否觸發出貨 {討論結論} (使用場景)

### Why
- 外部 webhook 是不受信任的輸入；信任 header 宣稱的來源會讓偽造請求有機可乘 {討論結論} (Why)
- 驗證收斂到 Gateway 後，worker 與 monitor 可假設事件身份為真，不必每層重驗 {討論結論} (Why)
- Webhook 傳輸語意通常是 at-least-once，接收端必須能判斷是否已處理；假設「短時間內不會重複」等於把正確性建在不可靠的假設上 {討論結論} (Why)
- 分層讓除錯能先分辨「傳輸層沒收到」還是「收到了但業務判斷錯」，兩者由不同人、用不同方式修 {討論結論} (Why)
- 去重在上游做掉後，worker 層的重試只是重送同一訊息，不會重複觸發業務副作用，重試因此永遠安全 {討論結論} (Why)

### 延伸：接上 generator/evaluator
- 可在 monitor 層接 generator/evaluator：generator 依已驗證、已去重的事件產生建議動作，evaluator 或真人在執行前核對（金額是否對得上、狀態轉換是否符合狀態機路徑）{討論結論} (延伸)
- Access + idempotency 回答「輸入能不能信任」，generator/evaluator 回答「依輸入做出的判斷對不對」，兩層驗證各自獨立 {討論結論} (延伸)

## 變更
- （首次產生）

## 候選連結
- system-design：transactional-outbox-lease-reaper-idempotent-consumer-pattern、saga-outbox-idempotent-escalation-checkout-pattern、dunning-retry-webhook-idempotent-timingwheel-pattern、data-freshness-watchdog-scanner-marker-golden-pattern（completion marker）、price-watch-tiered-fetch-cas-outbox-freshness-pattern、structured-rag-golden-eval-hexagonal-pattern（worker/monitor 分層）、trino-gateway-oidc-watermark-pattern（Gateway 驗證）
- wiki：single-writer、optimistic-concurrency、agent-harness-design、primary-guardrail-gate、skill-state
