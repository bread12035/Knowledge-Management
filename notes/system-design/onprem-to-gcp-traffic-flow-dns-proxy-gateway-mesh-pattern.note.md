---
raw: raw/system-design/onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern.md
raw_sha256: 192e36b5714f30f823a1385edfa61df31b22e7e317e944d4c5732dbf49fec339
source: system-design
title: On-prem → GCP 流量管理:DNS / Reverse proxy / GKE Gateway / Istio mesh
generated: 2026-11-18
---
# On-prem → GCP 流量管理：DNS / Reverse proxy / GKE Gateway / Istio mesh（note）

## 一句話
企業內部使用者進 GCP 的路徑是 瀏覽器 → reverse proxy（企業單一出口）→ GKE Gateway（GCP 單一入口）→ Istio mesh 內 frontend → backend（FastAPI）→ GCS／Postgres；DNS 只回答位置、不在資料路徑上。

## 主張
證據標記對應：使用者描述的元件與順序（現況描述，非設計決定）→ {討論結論}；原文標為依常見做法**推斷**的細節（hostname、IP 網段、TLS 終止點、專線或 VPN）→ {我的判斷}；沒有標記的元件說明與設計原因 → {討論結論}。

### 流量流向
- 路徑：瀏覽器 → reverse proxy → GKE Gateway → frontend pods → backend pods（FastAPI）→ GCS（發布版 prompt）／Postgres（草稿與資料）{討論結論} (流向圖)
- 路徑上有兩次 DNS 查詢：瀏覽器查企業 DNS 取得 reverse proxy IP；reverse proxy 查 GCP DNS 取得 GKE Gateway IP {討論結論} (流向圖)
- DNS 不在資料路徑上，只回答「對方在哪」，不搬運資料 {討論結論} (流向圖)
- 範例 hostname `prompts.corp.com` 等細節是推斷 {我的判斷} (流程範例)

### 四個元件
- Reverse proxy 代替伺服器接請求再轉給後端，可順便做身份驗證、TLS、請求過濾；本情境是企業往 GCP 的出口 {討論結論} (四個元件)
- GKE Gateway 是 GKE 上設定 load balancer 規則的資源，例如 `/api` 開頭送 backend；只送給健康的 pod {討論結論} (四個元件)
- Istio 在每個 pod 旁放 sidecar proxy，所有進出流量先經過它，負責加密、重試、記錄，不用改應用程式碼 {討論結論} (四個元件)

### 設計原因
- Reverse proxy 是企業往 GCP 的單一出口，方便集中管控與稽核 {討論結論} (設計原因)
- GCP DNS 用名字查詢，讓 GCP 內 IP 變動不影響上游 {討論結論} (設計原因)
- GKE Gateway 是 GCP 的單一入口，負責分流與健康檢查 {討論結論} (設計原因)
- Pod 之間的加密、重試、觀測統一由 mesh 處理，不用每個服務各寫一套 {討論結論} (設計原因)
- Backend 後接 GCS／Postgres 對應 SSOT 設計：Postgres 為編輯來源、GCS 為發布版 {討論結論} (設計原因)

### 對齊清單與下一步
- 待確認：DNS forwarding、Interconnect 或 VPN、TLS 在哪層終止、mesh 從 Gateway 還是 frontend 開始、是否啟用 mTLS、backend 存取 GCS／Postgres 的身份驗證 {我的判斷} (確認清單)
- 下一步學 Istio sidecar 如何攔截 pod 流量 {討論結論} (下一步學習)

## 變更
- （首次產生）

## 候選連結
- system-design：single-source-of-truth-postgres-gcs-release-pattern、earnings-transcript-gcp-to-onprem-handover-pattern（反方向：GCP → on-prem）、trino-gateway-oidc-watermark-pattern（gateway 單一入口與身份）
- wiki：primary-guardrail-gate（單一出入口集中檢查）、progressive-disclosure（弱）
