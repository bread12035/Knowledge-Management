---
raw: raw/system-design/earnings-video2text-gcp-to-onprem-handover-pattern.md
raw_sha256: 058927157120aab022bfe50793cdd974967fe930f84b775173c04b849980c482
source: system-design
title: 財報影音轉文字流程:GCP(tMIC)→ On-prem 交接
generated: 2026-11-18
---
# 財報影音轉文字流程：GCP（tMIC）→ On-prem 交接（note）

## 一句話
影音轉文字（Video2text）流程只改 GCP 側：Event Calendar 改 [BIAP]、資料來源改為 FACTSET + YouTube API、新增 Gemini API 做影片轉文字、Claude API 多接 Web search tool；GCS 之後的交接與 on-prem BDP 與逐字稿流程完全相同。

## 主張
證據標記對應：使用者描述的元件與順序（現況描述，非設計決定）→ {討論結論}；原文標為依常見做法**推斷**的元件角色（Gemini 轉文字、Claude 處理、web search 補查）、流程範例、設計原因 → {我的判斷}。

### 與第二頁（逐字稿流程）的差異
- Event Calendar 由 [SCPM] 改為 [BIAP] {討論結論} (差異)
- 第 3 步由 AI Transcript 改為 Video2text {討論結論} (差異)
- 資料來源只留 FACTSET Transcript，移除 BBG-FA、BBG-SEG，新增 YouTube API (Earnings Source) {討論結論} (差異)
- 外部服務：Claude API service 多接 Web search tool（雙向），新增 Gemini API (Video2text)（雙向）{討論結論} (差異, 流向圖)
- GCS → Adapter → on-prem（BDP：Raw、DAG、Stage；再接第二個 DAG 與 tMIC Portal）與逐字稿流程完全相同 {討論結論} (前言)

### 流程範例（推斷）
- Video2text 透過 YouTube API 取得記者會影片、呼叫 Gemini API 轉成文字、參考 FACTSET Transcript，再呼叫 Claude API 處理；Claude 需要時用 Web search tool 查外部資料 {我的判斷} (流程範例)

### 元件說明（推斷）
- Video2text 不自己轉文字，而是呼叫 Gemini API，自己負責串接與彙整 {我的判斷} (元件說明)
- YouTube API 提供影片存取方式，不負責轉文字 {我的判斷} (元件說明)
- Web search tool 由 Claude 自行決定要不要呼叫，不是每次都用 {我的判斷} (元件說明)

### 設計原因（推斷）
- 先把影片轉成文字，後面的處理就能沿用文字流程 {我的判斷} (設計原因)
- 保留 FACTSET 官方逐字稿當對照，也可能在影片轉文字失敗時當備援 {我的判斷} (設計原因)
- 輸出都是一份檔案，所以第 5~10 步的交接與落地方式可以共用 {我的判斷} (設計原因)

### 確認清單與下一步
- 待確認：[BIAP] 與 [SCPM] 差異、FACTSET 與 Gemini 文字不一致時以哪份為準、YouTube 影片不可用（未上架、直播中、被下架）的處理與重試、Gemini 對影片長度／大小的限制與切段、Web search 可搜網域與成本上限與來源標註、第 5~10 步是否真的共用同一組 DAG 與資料表 {討論結論} (確認清單)
- 下一步學 tool use：Claude 何時呼叫 Web search tool、結果怎麼回到對話 {討論結論} (下一步學習)

## 變更
- （首次產生）

## 候選連結
- system-design：earnings-transcript-gcp-to-onprem-handover-pattern（基準頁）、earnings-pre-earnings-gcp-to-onprem-handover-pattern、web-fetch-crawler-api-browser-agent-comparison
- wiki：agent-harness-design（tool use）、golden-dataset（雙來源對照）
