---
id: earnings-gcp-onprem-handover
title: Earnings 三條流程與 GCP ↔ on-prem 交接
type: topic
summary: Event Calendar 觸發 GCP 上的 AI 處理，結果先落地 GCS，再經單一 Adapter 交回 on-prem 的 Raw → Stage → Portal；三條流程只差 GCP 側
domains: [system-design]
sources: [raw/system-design/earnings-transcript-gcp-to-onprem-handover-pattern.md#流向圖, raw/system-design/earnings-transcript-gcp-to-onprem-handover-pattern.md#設計原因, raw/system-design/earnings-video2text-gcp-to-onprem-handover-pattern.md#差異, raw/system-design/earnings-pre-earnings-gcp-to-onprem-handover-pattern.md#差異, raw/system-design/onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern.md#流向圖]
evidence: [討論結論, 我的判斷]
related: [gateway-authn-service-authz, single-source-of-truth, web-content-acquisition, idempotent-consumer, event-driven-timer]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Earnings 三條流程與 GCP ↔ on-prem 交接

> Event Calendar 觸發 GCP 上的 AI 處理，結果先落地 GCS，再經單一 Adapter 交回 on-prem 的 Raw → Stage → Portal；三條流程只差 GCP 側

## 重點
- 逐字稿流程：Event Calendar [SCPM] → Pubsub → AI Transcript（FACTSET、BBG-FA、BBG-SEG + Claude API）→ GCS → Adapter → MinIO Raw → DAG → MinIO Stage → DAG → tMIC Portal {討論結論}
- 三條流程在 GCS 之後完全相同，只差 GCP 側 {討論結論}
- Raw 一旦寫入就不改，Stage 出錯時可以從 Raw 重做 {我的判斷}
- 跨邊界前先落地（GCS），交接失敗時檔案還在可以重送；邊界只留一個出入口（Adapter）方便管控與稽核 {我的判斷}
- Event Calendar + Pubsub 用事件觸發，不靠手動也不輪詢 {我的判斷}

## 細節
| 流程 | Calendar | GCP 側處理 |
| --- | --- | --- |
| Transcript | [SCPM] | FACTSET、BBG-FA、BBG-SEG → AI Transcript + Claude API |
| Video2text | [BIAP] | FACTSET + YouTube API → Gemini API 轉文字 → Claude API（加 Web search tool） |
| Pre-earnings | [BIAP] | 沒有固定來源；Claude API 只靠 Web search + Web fetch 上網 {討論結論} |

- Video2text 先把影片轉成文字，以沿用下游文字流程 {討論結論}
- Pre-earnings 沒有固定輸入，要處理網站封鎖、prompt injection、網域白名單與成本上限（[[web-content-acquisition]]）{討論結論}
- 反方向（on-prem 使用者進 GCP）：瀏覽器 → reverse proxy（企業單一出口）→ GKE Gateway（GCP 單一入口）→ Istio mesh 內 frontend → backend → GCS / Postgres；DNS 只回答位置，不在資料路徑上 {討論結論}

## 在設計中怎麼用
- 待確認（原文列出）{討論結論}：
  - 事件改期或取消是否再發 Pubsub
  - Pubsub 重送會不會產生重複結果
  - Adapter 是 pull 還是 push
  - 走專線還是 VPN
  - 端到端延遲與最慢段
- 下一步要補的是冪等性：Pubsub 或 Adapter 重送時同一份資料不被處理兩次（[[idempotent-consumer]]）。
- 事件改期由 Scanner 類角色維持排程表正確（[[event-driven-timer]]）。

## 相關
- [[gateway-authn-service-authz]]：單一出入口
- [[single-source-of-truth]]：GCP 側 prompt 的 SSOT 設計
- [[web-content-acquisition]]：Pre-earnings 上網取資料
- [[idempotent-consumer]]：重送不重複處理
- [[event-driven-timer]]：Event Calendar 與排程
