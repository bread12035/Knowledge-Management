---
raw: raw/system-design/earnings-transcript-gcp-to-onprem-handover-pattern.md
raw_sha256: cc41a744965c1e760b71022129fa103c53428334c414dbf8d3eec2a9b5cbdbf7
source: system-design
title: 財報逐字稿流程:GCP(tMIC)→ On-prem 交接
generated: 2026-11-18
---
# 財報逐字稿流程：GCP（tMIC）→ On-prem 交接（note）

## 一句話
財報逐字稿（AI Transcript）流程：Event Calendar [SCPM] → Pubsub → AI Transcript（FACTSET、BBG-FA、BBG-SEG + Claude API）→ GCS → Adapter 跨邊界 → on-prem BDP（MinIO Raw → DAG → Stage）→ DAG → tMIC Portal；這是三份 earnings 交接文件的基準頁，GCS 之後第 5~10 步與 BDP 的說明只在這份完整寫出。

## 主張
證據標記對應：使用者描述的元件與順序（現況描述，非設計決定）→ {討論結論}；原文標為依常見做法**推斷**的元件角色、流程範例、設計原因 → {我的判斷}。

### 流向圖
- 元件順序：1 Event Calendar [SCPM] → 2 Pubsub → 3 AI Transcript → 4 GCS → 5 Adapter → 6 MinIO Raw Layer → 7 DAG → 8 MinIO Stage Layer → 9 DAG → 10 tMIC Portal {討論結論} (流向圖)
- FACTSET Transcript、BBG-FA、BBG-SEG 是流入 AI Transcript 的資料來源；AI Transcript 與 Claude API service 雙向呼叫 {討論結論} (流向圖)
- On-prem 的 Raw Layer、第一個 DAG、Stage Layer 用 BDP 方框圈起；第二個 DAG 與 Portal 畫在 BDP 外 {討論結論} (流向圖, 元件說明)
- 本文是資料從 GCP 交接回 on-prem 的方向；使用者請求從 on-prem 進 GCP 的方向在另一份文件 {討論結論} (前言)

### 流程範例（推斷）
- AI Transcript 收到 Pubsub 訊息後，從 FACTSET 取逐字稿、從 BBG-FA／BBG-SEG 取資料、呼叫 Claude API 處理，結果寫成檔案存到 GCS {我的判斷} (流程範例)
- Adapter 取走 GCS 檔案送進企業內部；第一個 DAG 檢查整理 Raw → Stage，第二個 DAG 把 Stage 送到 Portal {我的判斷} (流程範例)

### 元件說明
- Pubsub 讓發送者與接收者不需直接連線，且訊息會暫存，接收者晚上線也收得到 {我的判斷} (元件說明)
- DAG 由排程系統自動執行，失敗時可重試 {我的判斷} (元件說明)
- Adapter 是跨越邊界的一步，出入口權限、網路與失敗重送都要管 {我的判斷} (元件說明)
- Raw 一旦寫入就不改，所以 Stage 出錯時可以從 Raw 重做 {我的判斷} (元件說明)

### 設計原因（推斷）
- Event Calendar + Pubsub 用事件觸發，不用人手動啟動也不用輪詢 {我的判斷} (設計原因)
- 資料來源接在 AI Transcript 上游彙整，後面只傳處理結果 {我的判斷} (設計原因)
- GCS 在 Adapter 之前讓產出先落地；交接失敗時檔案還在，可以重送 {我的判斷} (設計原因)
- 邊界只留一個出入口（Adapter），方便管控與稽核 {我的判斷} (設計原因)
- 兩段 DAG 各只做一件事，失敗時知道是哪一段 {我的判斷} (設計原因)

### 確認清單與下一步
- 待確認：事件改期／取消是否再發 Pubsub、AI Transcript 失敗時 Pubsub 重送會不會產生重複結果、Adapter 是 pull 或 push、走專線或 VPN、BDP 全名與範圍、端到端延遲與最慢段 {討論結論} (確認清單)
- 下一步學冪等性：Pubsub 重送訊息、Adapter 重送檔案時，同一份資料不被處理兩次 {討論結論} (下一步學習)

## 變更
- （首次產生）

## 候選連結
- system-design：earnings-video2text-gcp-to-onprem-handover-pattern、earnings-pre-earnings-gcp-to-onprem-handover-pattern、onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern、webhook-idempotent-worker-outbox-pattern（重送與冪等）、data-freshness-watchdog-scanner-marker-golden-pattern
- wiki：single-writer、agent-harness-design（Claude API 嵌入批次流程）
