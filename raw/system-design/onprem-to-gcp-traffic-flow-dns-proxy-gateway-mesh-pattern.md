---
source_project: system design & code style
source_file: claude/onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern.md
title: On-prem → GCP 流量管理:DNS / Reverse proxy / GKE Gateway / Istio mesh
first_exported: 2026-11-18
updated: 2026-11-18
---
# On-prem → GCP 流量管理:DNS / Reverse proxy / GKE Gateway / Istio mesh

> 背景:infra team 在 GCP 上部署 frontend 與 backend。使用者從企業內部出發,輸入網址後執行動作。
>
> 註記:本文的元件順序來自使用者描述;各元件的細節(hostname、IP 網段、TLS 在哪一層終止、專線或 VPN)是依常見做法**推斷**的,不是 infra team 的實際規格。與 infra 對齊時以他們的版本為準。

---

## 流量流向圖

```
【企業內部 On-prem】
  1. 瀏覽器 ┄┄(查詢)┄┄► 企業 DNS(回傳 reverse proxy 的 IP)
      │
      ▼
  2. Reverse proxy ┄┄(查詢)┄┄► GCP DNS(回傳 GKE Gateway 的 IP)
      │
══════│═══════════════════════════ 進入 GCP ═══════
      ▼
【GCP】
  3. GKE Gateway(Load balancer 入口)
      │
      ▼
  ┌─ Service mesh (Istio) ─────────────┐
  │ 4. Frontend pods                    │
  │      │                              │
  │      ▼                              │
  │ 5. Backend pods(FastAPI)           │
  └──────┬───────────────┬──────────────┘
         ▼               ▼
     6a. GCS         6b. Postgres
   (發布版 prompt)    (草稿與資料)

  實線 = 流量方向;虛線(┄)= DNS 查詢
```

重點:**DNS 不在資料路徑上。** DNS 只回答「對方在哪」,不搬運資料。這條路徑上有兩次 DNS 查詢:
- 瀏覽器查企業 DNS,取得 reverse proxy 的位置。
- Reverse proxy 查 GCP DNS,取得 GKE Gateway 的位置。

---

## 流程範例

輸入:瀏覽器開啟 `https://prompts.corp.com/summarize_v3`。

| Step | 動作 |
|---|---|
| 1 | 瀏覽器問企業 DNS:「`prompts.corp.com` 在哪?」企業 DNS 回傳 reverse proxy 的 IP |
| 2 | 瀏覽器把請求送到 reverse proxy |
| 3 | Reverse proxy 問 GCP DNS:「後端在哪?」GCP DNS 回傳 GKE Gateway 的 IP。Reverse proxy 把請求轉過去 |
| 4 | GKE Gateway 選一個健康的 frontend pod,送過去 |
| 5 | Frontend 呼叫 backend。這一段由 mesh 管理 |
| 6 | Backend 讀 GCS 或 Postgres,結果沿原路送回瀏覽器 |

輸出:`summarize_v3` 的內容。

---

## 四個元件

### DNS(Domain Name System,網域名稱系統)
- 作用:把名字換成 IP。
- 類比:電話簿。你查名字,它給號碼。
- 不同點:DNS 只給號碼,不幫你打電話(不搬運資料)。
- 本情境有兩本電話簿:企業 DNS 管企業內部的名字;GCP DNS 管 GCP 內部的名字。

### Reverse proxy(反向代理)
- 作用:站在伺服器前面,代替伺服器接請求,再轉給後端。
- 類比:公司櫃檯。訪客先找櫃檯,櫃檯再通知內部的人。
- 不同點:櫃檯可以順便做檢查,例如驗證身份、處理 TLS 加密、過濾請求。
- 本情境:它是企業出口,把請求轉送到 GCP。

### Load balancer(負載平衡器)與 GKE Gateway
- 作用:把請求分給多個相同的 pod,並且只送給健康的 pod。
- 類比:餐廳的帶位員。
- GKE Gateway 是 GKE 上用來設定這些規則的資源,例如「`/api` 開頭的請求送到 backend」。

### Service mesh(服務網格)與 Istio
- 作用:管理 pod 與 pod 之間的流量。Istio 是最常見的 mesh 軟體。
- 做法:在每個 pod 旁邊放一個 sidecar proxy(隨身代理)。所有進出該 pod 的流量,都先經過它。
- 類比:給每個 pod 配一位祕書,由祕書負責加密、重試、記錄。
- 不同點:祕書是軟體自動執行,不用改應用程式的程式碼。

---

## 設計原因(依元件分工)

| 元件 | 為什麼放在這個位置 |
|---|---|
| 企業 DNS | 讓使用者用好記的網址,不必記 IP |
| Reverse proxy | 企業對外(往 GCP)的單一出口,方便集中管控與稽核 |
| GCP DNS | GCP 內的位置可能改變,用名字查詢,讓 IP 變動不影響上游 |
| GKE Gateway | GCP 的單一入口,負責分流與健康檢查 |
| Istio mesh | pod 之間的加密、重試、觀測,統一由 mesh 處理,不用每個服務各寫一套 |
| Backend 後面接 GCS / Postgres | 與 SSOT 設計對應:Postgres 為編輯來源,GCS 為發布版(見 `claude/single-source-of-truth-postgres-gcs-release-pattern.md`) |

---

## 與 infra team 對齊時的確認清單

- 企業 DNS 與 GCP DNS 之間,是否有轉發規則(DNS forwarding)?
- 企業到 GCP 走專線(Interconnect)還是 VPN?
- TLS 在哪一層終止?(reverse proxy、Gateway,或 pod 內)
- Gateway 與 frontend 之間是否已在 Istio mesh 內?還是 mesh 從 frontend 開始?
- Mesh 內是否啟用 mTLS(雙向加密)?
- Backend 存取 GCS 與 Postgres 的身份驗證方式?

## 下一步學習

Istio sidecar 如何攔截 pod 的流量:mesh 怎麼做到「不改程式也能加密與重試」。
