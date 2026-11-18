---
raw: raw/system-design/trino-gateway-oidc-watermark-pattern.md
raw_sha256: d927b0d36f33126bcad5334d78d15835d3eb37ec51fee4d1ddc536db3f5cca2d
source: system-design
title: 業界經典範例整合：Stateless Query Gateway + OIDC Authentication + Watermark-gated Ingestion
generated: 2026-11-18
---
# 業界經典範例整合：Stateless Query Gateway + OIDC Authentication + Watermark-gated Ingestion（note）

## 一句話
所有消費者（PowerBI、自建 App、Claude Cowork via MCP）經同一個 stateless Gateway 查 Trino；Gateway 集中做 JWT Authentication、後端只做 Authorization，資料可讀與否由 completion marker 判斷而不是猜時間緩衝。

## 主張
證據標記對照：原文沒有標記；原文明寫為使用者在 log-pipeline / chat-service 設計中的決定者標 {使用者決定}，其餘 {討論結論}；「延伸一步」為未驗證建議，標 {我的判斷}。原文無編號章節，以章節名稱引用。

### §合併的概念
- 雲端 log 系統讓 PowerBI、自建 App、Claude Cowork（MCP）三種消費者都經由一個 stateless Gateway 查詢 Trino {使用者決定} (§這次合併了哪些概念)
- on-prem ingestion 用 completion marker 判斷資料是否可讀，而非固定時間緩衝 {使用者決定} (§這次合併了哪些概念、§業界經典範例)
- Client 從 Keycloak 拿 JWT，API Gateway（FastAPI）負責 Authentication（驗簽），後端 Service 只負責 Authorization {使用者決定} (§這次合併了哪些概念)
- 這三者合起來是 Data Lakehouse Serving Layer 的常見做法 {討論結論} (§這次合併了哪些概念)

### §業界經典範例
- Lyft 開源的 trino-gateway 在多個 Trino cluster 前放 stateless gateway，負責路由、限流與集中身份驗證，不保存查詢狀態 {討論結論} (§業界經典範例)
- Iceberg 的 snapshot / commit 機制提供「這批資料是否已完整寫入」的訊號，下游只讀已提交的 snapshot {討論結論} (§業界經典範例)
- Hudi 用 completion marker（`_SUCCESS` 檔或 commit metadata）標示批次完成，下游檢查標記才往下跑 {討論結論} (§業界經典範例)

### §為什麼採用
- 併發使用者 < 3、資料每 3 小時更新一次，Gateway 不需要 MongoDB 這類狀態層或快取層，有狀態中間層是過度設計 {使用者決定} (§為什麼採用這些技術)
- Gateway 是 deep module：介面窄、只負責轉發查詢，不同時扛快取等額外職責 {討論結論} (§為什麼採用這些技術)
- realm URL 與演算法白名單寫死在 FastAPI 層，不信任 Client 傳來的值，以防 JWT algorithm confusion / issuer 偽造（指向假 Keycloak 簽出看似合法的 JWT）{討論結論} (§為什麼採用這些技術)
- 固定時間緩衝在批次耗時不穩定時會失準：太慢讀到舊資料或報錯，太快則浪費等待 {討論結論} (§為什麼採用這些技術)
- 原則：用明確信號（事件）取代猜測的時間差；與 message-seam 的 ack/nack 同源 {討論結論} (§為什麼採用這些技術)

### §重點要解決的問題
- PowerBI 不可直接對 Trino 下 SQL，一律走 API，以便統一記錄、限流、稽核 {使用者決定} (§重點要解決的問題)
- Authentication（是誰）與 Authorization（能不能做）分層，混在一起難維護、難稽核、易出漏洞 {討論結論} (§重點要解決的問題)
- 低頻、低併發場景下資料完整性優先於即時性：寧可稍等拿完整資料，不猜時間窗讀到半批 {討論結論} (§重點要解決的問題)
- 異質消費者（排程 poll、on-demand、MCP）共用同一套 Gateway、認證與新鮮度契約，否則每加一種消費者就要重設計 {討論結論} (§重點要解決的問題)

### §延伸一步
- 可把 pipeline 健康監控做成小型 agent：generator 檢查 marker 是否準時、資料量是否在歷史區間，evaluator 或真人決定是否通知或 retry {我的判斷} (§延伸一步)

## 變更
- （首次產生）

## 候選連結
- system-design：data-freshness-watchdog-scanner-marker-golden-pattern、onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern、scanner-executor-timingwheel-nooa-pattern、price-watch-tiered-fetch-cas-outbox-freshness-pattern
- wiki：agent-harness-design（generator/evaluator、deep module）、harness2、primary-guardrail-gate、single-writer
