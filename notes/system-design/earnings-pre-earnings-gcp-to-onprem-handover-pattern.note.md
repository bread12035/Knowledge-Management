---
raw: raw/system-design/earnings-pre-earnings-gcp-to-onprem-handover-pattern.md
raw_sha256: b6b0749f8752a4f07620c3cd91fc25477c1fb12582d1a953075d36585eb12322
source: system-design
title: Pre-earnings 流程:GCP(tMIC)→ On-prem 交接
generated: 2026-11-18
---
# Pre-earnings 流程：GCP（tMIC）→ On-prem 交接（note）

## 一句話
Pre-earnings 流程沿用 Video2text 頁但移除所有固定資料來源與 Gemini API，Claude API 只靠 Web search + Web fetch 兩個工具上網取資料；與前兩頁的差別是沒有固定輸入，因此多出防機器人封鎖、prompt injection、網域白名單與成本上限的風險。

## 主張
證據標記對應：使用者描述的元件與順序（現況描述，非設計決定）→ {討論結論}；原文標為**推斷**的 Pre-earnings 實際內容、Claude 如何使用兩個工具、流程範例、設計原因 → {我的判斷}。

### 與第三頁（Video2text）的差異
- Event Calendar 維持 [BIAP] {討論結論} (差異)
- 第 3 步改為 Pre-earnings {討論結論} (差異)
- 資料來源（FACTSET Transcript、YouTube API）全部移除，Gemini API 也移除 {討論結論} (差異)
- Claude API service 保留，工具為 Web search tool + 新增的 Web fetch tool，皆雙向呼叫 {討論結論} (差異, 流向圖)
- GCP 側沒有固定資料來源，Pre-earnings 取得資料的唯一途徑是 Claude 透過兩個工具上網 {討論結論} (差異)
- GCS → Adapter → on-prem（BDP）與第二、三頁完全相同 {討論結論} (前言)

### 流程範例與元件（推斷）
- Pre-earnings 推斷為財報前彙整與準備資訊；名稱來自使用者，具體內容是推斷 {我的判斷} (元件說明)
- Claude 先用 Web search 找相關網頁，再用 Web fetch 讀取需要的網頁內文 {我的判斷} (流程範例)
- Web fetch 直接連到網站，可能被防機器人機制擋下；Web search 查搜尋引擎結果，比較不會被擋 {我的判斷} (元件說明)

### 設計原因（推斷）
- 財報前還沒有逐字稿與影片，能用的只有網路上已公開資訊，所以移除固定資料來源 {我的判斷} (設計原因)
- 只搜尋只會拿到摘要，所以 search 後接 fetch 讀內文 {我的判斷} (設計原因)
- 由 Claude 判斷要查什麼、讀哪一頁，不事先寫死資料來源 {我的判斷} (設計原因)

### 確認清單與下一步
- 待確認：Web fetch 被擋（防機器人、需登入、JavaScript 載入）時的備援 {討論結論} (確認清單)
- 待確認：Web search／fetch 可存取網域是否限制白名單 {討論結論} (確認清單)
- 待確認：抓回的網頁內容可能夾帶 prompt injection，要怎麼處理 {討論結論} (確認清單)
- 待確認：單次 Pre-earnings 的搜尋／抓取次數與成本上限、輸出來源標註與能否點回原網頁、財報前多久觸發 {討論結論} (確認清單)
- 下一步學 tool use：Claude 何時呼叫 Web search 或 Web fetch {討論結論} (下一步學習)

## 變更
- （首次產生）

## 候選連結
- system-design：earnings-video2text-gcp-to-onprem-handover-pattern（來源頁）、earnings-transcript-gcp-to-onprem-handover-pattern（第 5~10 步）、web-fetch-crawler-api-browser-agent-comparison、http-api-vs-html-curl-cloudflare-bot-policy、price-watch-tiered-fetch-cas-outbox-freshness-pattern
- wiki：agent-harness-design（tool use、預算上限）、primary-guardrail-gate（不可信網頁內容）
