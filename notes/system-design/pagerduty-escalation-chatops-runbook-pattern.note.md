---
raw: raw/system-design/pagerduty-escalation-chatops-runbook-pattern.md
raw_sha256: dddb8ff7f358ac47bd796e48019fbd9122e062017b14126bedd9d18e842d952b
source: system-design
title: 業界經典範例整合：Timing-Wheel Escalation Engine + Authenticated ChatOps Gateway + Structured Runbook Retrieval
generated: 2026-11-18
---
# 業界經典範例整合：Timing-Wheel Escalation Engine + Authenticated ChatOps Gateway + Structured Runbook Retrieval（note）

## 一句話
On-call 事故應變系統要同時處理三層：用 min-heap／timing wheel 精準觸發升級（timing）、Authentication 集中在 API Gateway（access）、runbook 用結構化查詢取代 naive RAG（knowledge）。

## 主張
原文沒有證據標記，且是排程自動合併的整理文；一律標 {討論結論}。引用過去討論中使用者已做出的設計選擇時標 {使用者決定}。業界例子（PagerDuty、Slack、Rundeck 等）沒有附來源連結，也標 {討論結論}，不升級為 {第三方}。

### §這次合併了哪些概念
- 本篇合併三個過去討論：earnings-pipeline（Scanner/Executor + min-heap）、chat-service-auth-design（Authentication／Authorization 分層）、ai-searchable-knowledge-base（Structured Retrieval 取代 naive RAG）{討論結論} (§合併概念)
- Earnings-pipeline 的設計：Scanner 讓排程表保持新鮮，Executor 用 min-heap 只看「下一個」事件、event-driven 觸發 {使用者決定} (§合併概念)
- Chat-service 的設計：Client 從 Keycloak 拿 JWT，API Gateway 集中做 Authentication（驗簽章、驗 issuer），後端 Service 只做 Authorization {使用者決定} (§合併概念)
- Realm URL 與演算法白名單寫死在 Gateway 端，不信任 Client 宣稱的來源 {使用者決定} (§合併概念)
- 為人類閱讀寫的 HTML 知識庫（含表格、截圖）用 naive RAG 向量檢索會拆散表格欄位對應；應先轉成有 schema 的結構化資料，用 query 取代語意猜測 {討論結論} (§合併概念)
- 三者對應 on-call 系統三層：什麼時候通知誰（timing）、管道與身份驗證（access）、查到正確處理步驟（knowledge）{討論結論} (§合併概念)

### §業界經典範例
- PagerDuty / Opsgenie 的 Escalation Policy：第一線未在時限內 acknowledge，就自動升級通知下一層（team lead、on-call manager）{討論結論} (§業界範例)
- 成百上千個升級計時器不該逐一固定間隔輪詢；用 min-heap peek 堆頂即知下一個到期事件，規模更大時用 hierarchical timing wheel（如 Kafka Purgatory）{討論結論} (§業界範例)
- Slack、PagerDuty webhook、內部 App 三種來源的請求應走同一套集中式身份驗證，由 Gateway 確認請求真的來自合法來源，下游不各自驗簽章 {討論結論} (§業界範例)
- Runbook 寫成 wiki 頁面時，事故中全文搜尋常找到過時或部分相關頁面；成熟做法是拆成「服務名稱、症狀、處理步驟、負責團隊」欄位表，用過濾查詢取代向量比對 {討論結論} (§業界範例)
- Chunk 切斷段落會遺失「症狀對應哪個處理步驟」的精確關係 {討論結論} (§業界範例)

### §使用場景
- 例：incident 觸發後排「5 分鐘內沒人 ack 就升級」的計時器；不用每分鐘掃描所有 pending incident {討論結論} (§使用場景)
- ChatOps 請求流程：Gateway 先驗證訊息來自合法 Slack workspace（Authentication），後端再判斷該工程師能否看該服務事故記錄（Authorization），再用結構化查詢撈處理步驟與歷史事故 {討論結論} (§使用場景)

### §為什麼採用
- 固定間隔輪詢必須在精準度與資源消耗之間取捨：間隔短浪費空轉檢查，間隔長有系統性延遲 {討論結論} (§Why)
- 事故升級對延遲特別敏感，所以用 event-driven 的 min-heap 只關心下一個事件 {討論結論} (§Why)
- Authentication（請求來源、簽章）與 Authorization（業務上是否允許）是不同層次的關注點，應分開 {討論結論} (§Why)
- 每個下游服務各自驗證，除了重複，還容易出現「相信呼叫方宣稱的來源、不用 Gateway 端寫死白名單」的漏洞 {討論結論} (§Why)
- 「服務對應哪個處理步驟」是精準欄位對應、有標準答案，不適合用向量相似度猜 {討論結論} (§Why)

### §重點要解決的問題
- 三個要解決的問題：通知與升級的時效性、多來源身份統一且可稽核的驗證、事故當下知識檢索要精準 {討論結論} (§重點問題)

### §延伸一步
- 可接 generator/evaluator：generator 依結構化查詢到的歷史與症狀生成「可能原因＋建議步驟」摘要，evaluator 或真人在行動前核對（如引用不存在的服務、與歷史模式矛盾）{討論結論} (§延伸)
- Timing 解決「什麼時候做」，generator/evaluator + human-in-the-loop 解決「建議對不對」，兩層驗證互相獨立 {討論結論} (§延伸)

## 變更
- （首次產生）

## 候選連結
- system-design：scanner-executor-timingwheel-nooa-pattern、dunning-retry-webhook-idempotent-timingwheel-pattern、data-freshness-watchdog-scanner-marker-golden-pattern、structured-rag-golden-eval-hexagonal-pattern、rag-methods-comparison、saga-outbox-idempotent-escalation-checkout-pattern、trino-gateway-oidc-watermark-pattern
- wiki：agent-harness-design（generator/evaluator）、ontology-knowledge-graph（結構化取代 naive RAG）、primary-guardrail-gate、promotion-gate
