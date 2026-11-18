---
source_project: system design & code style
source_file: claude/trino-gateway-oidc-watermark-pattern.md
title: 業界經典範例整合：Stateless Query Gateway + OIDC Authentication + Watermark-gated Ingestion
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Stateless Query Gateway + OIDC Authentication + Watermark-gated Ingestion

> 本篇由排程自動整理，隨機挑選過去三次討論中的概念合併而成，作為「system design & coding style」專案的知識累積。

## 這次合併了哪些概念

這次從記憶庫裡挑了三個看似不相關、但其實屬於同一個技術家族的討論，合併成一個完整的實作範例：

1. **log-pipeline-architecture**：你在設計的雲端 log 系統，讓 PowerBI、自建 App、Claude Cowork（透過 MCP）三種消費者，都經由一個 stateless Gateway 去查詢 Trino；資料是否可讀，是用 completion marker（完成標記）判斷，而不是猜一個固定的時間緩衝。
2. **chat-service-auth-design**：Client 從 Keycloak 拿到 JWT，由 API Gateway（FastAPI）負責 Authentication（驗證簽章），後端 Service 只負責 Authorization（業務邏輯的授權判斷）——認證與授權職責分離。
3. **coding-harness-design**：NOOA 風格的 generator/evaluator harness，強調 typed state、明確的職責邊界，以及 human-in-the-loop 的驗證關卡。

把這三個放在一起看，會發現它們其實是同一個業界經典架構的三個切面——這正是很多公司在做 **Data Lakehouse Serving Layer** 時採用的標準做法。

## 業界經典範例：Query Gateway 模式

這個模式在業界有具體的先例可以對照：

- **Lyft 開源的 trino-gateway**：在多個 Trino cluster 前面放一層 stateless gateway，負責路由、限流、以及集中式的身份驗證，本身不保存查詢狀態。
- **Netflix 的 Iceberg + Trino 平台**：資料以 Iceberg table format 落地，靠 snapshot / commit 機制天然提供「這批資料是否已完整寫入」的訊號，下游消費者只讀已提交的 snapshot，不會讀到寫一半的資料。
- **Uber 的 Hudi 增量處理**：用 completion marker（或稱 \_SUCCESS 檔案 / commit metadata）標示一個批次是否處理完畢，下游 job 靠檢查這個標記來決定要不要往下跑，而不是猜一個固定延遲時間。

你在 log-pipeline-architecture 裡「on-prem ingestion 用 completion marker 而非固定時間緩衝」的決定，其實就是在重新發明 Hudi/Iceberg 這類 lakehouse 系統解決的同一個問題：**如何在資料是分批寫入（batch write）的情況下，讓下游消費者不會讀到不完整的資料**。

## 使用場景（Use Case）

想像一個具體的一天：

早上 9 點，財務主管打開 PowerBI 報表，PowerBI 依照自己的排程（例如每小時）去打 Gateway 的 API；中午，客服人員打開自建的靜態網頁 App，這個 App 只讀不寫，使用者一進頁面就即時發一次查詢請求；晚上 11 點，你自己透過 Claude Cowork（走 MCP）臨時問一句「昨天有哪些公司的 log 量異常」，這是一個 on-demand 的查詢。三種消費者、三種呼叫頻率，但全部經過同一個 Gateway、同一套 Authentication 機制、同一套「資料是否新鮮」的判斷邏輯。這正是 Query Gateway 模式要解決的典型場景：**消費者形態很不一樣，但底層資料存取與安全政策必須統一**。

## 為什麼採用這些技術（Why）

Gateway 做成 stateless、只負責 proxy 查詢到 Trino，是因為你的併發使用者數很低（< 3），資料每 3 小時才更新一次——這種低頻場景完全不需要 MongoDB 這類額外的狀態層或快取層，維護一個有狀態的中間層反而是過度設計（over-engineering）。這呼應了你在 coding-harness-design 裡強調的 deep-module 概念：介面（interface）要窄、職責要單一，Gateway 的介面就是「轉發查詢」，不該同時扛「快取」「認證細節」等等額外職責。

採用 JWT + Keycloak 做 Authentication，是因為身份驗證的邏輯（誰是誰、簽章對不對）應該集中在一個地方管理，不該讓每個後端服務各自實作一套。把 realm URL 和演算法白名單寫死在 FastAPI 這一層（而不是讓 Client 傳過來），是為了避免一個經典的安全漏洞——**JWT algorithm confusion / issuer 偽造攻擊**：如果信任 Client 宣稱的 realm URL，惡意呼叫者理論上可以指向自己控制的假 Keycloak 伺服器，偽造一個「看起來合法」的 JWT。

用 completion marker 而不是固定時間緩衝去判斷資料新鮮度，是因為固定緩衝（例如「假設 3 小時內一定跑完，所以延遲 30 分鐘讀取」）在批次處理時間不穩定時會失準：跑太慢會讀到舊資料或報錯，跑太快則是浪費等待時間。Completion marker 讓下游用「事件」而非「時間」來同步，這也是 event-driven 架構（跟你 coding-harness-design 裡 message-seam 的 ack/nack 概念）背後同一個核心原則：**用明確的信號取代猜測的時間差**。

## 重點要解決的問題

把三個概念合在一起看，這個架構真正要解決的問題可以歸納成四點：第一，**避免 BI 工具直接碰資料庫**——PowerBI 沒有權限直接對 Trino 下 SQL，一律要走 API，這是治理（governance）與稽核的需要，所有查詢都有一個統一的出入口可以記錄、限流、審計。第二，**認證與授權要分層**——身份是誰（Authentication）跟這個人能不能做這件事（Authorization）是兩件事，混在一起會讓系統難以維護、難以稽核，也更容易出安全漏洞。第三，**資料完整性優先於資料即時性**——低頻更新、低併發的場景下,寧可讓消費者稍等一下拿到完整資料，也不要為了「快」去猜一個時間窗、冒著讀到半批資料的風險。第四，**異質消費者共用同一套契約**——PowerBI 用排程 poll、App 用 on-demand 查詢、Claude Cowork 用 MCP 呼叫，三者需求頻率完全不同，但底層的 Gateway、認證機制、資料新鮮度保證必須是同一套，不然每加一種消費者就要重新設計一次安全與一致性邏輯。

## 延伸一步：如果把 coding-harness-design 也用上

如果要更進一步結合 generator/evaluator harness 的概念，可以把這個 pipeline 的健康監控本身也做成一個小型 agent：generator 負責定期檢查 completion marker 是否準時出現、資料量是否符合歷史區間，evaluator（或是真人）負責在偵測到異常時（例如某天的 marker 遲遲沒出現，或某家公司的 log 量暴增暴減）決定要不要通知你、要不要自動 retry，這就是 human-in-the-loop 驗證關卡在資料維運場景裡的具體應用，而不只是用在 coding agent 上。
