---
raw: raw/system-design/price-watch-tiered-fetch-cas-outbox-freshness-pattern.md
raw_sha256: cd3005e07ec5095993cfe6c3c3bcdf341b16095500ae672b16dd1fa5b86ebe54
source: system-design
title: 業界經典範例整合：競品價格監控 Price Watch（分層抓取 + CAS 寫入 + Transactional Outbox + Freshness Watchdog）
generated: 2026-11-18
---
# 業界經典範例整合：競品價格監控 Price Watch（分層抓取 + CAS 寫入 + Transactional Outbox + Freshness Watchdog）（note）

## 一句話
價格監控用「便宜來源優先、被擋就停」的分層抓取，CAS 寫入防 lost update，同一 transaction 寫 outbox 確保「變了才發、發了不丟」，再用 min-heap freshness watchdog 讓抓不到的商品浮出來交給人。

## 主張
原文沒有證據標記，且是排程自動合併的整理文（2026-11-16）；一律標 {討論結論}。原文附的程式宣稱「兩組 golden case + 一組 CAS 衝突測試全部 PASS」，仍標 {討論結論}，只在主張中註明有可執行驗證。

### §這次合併了哪些概念
- 本篇合併五個概念：分層抓取、尊重網站 bot 政策、CAS 寫入、Transactional Outbox、data-freshness watchdog（min-heap deadline）{討論結論} (§合併概念)
- 分層抓取順序：官方 API → web fetch → headless browser，越後面越貴 {討論結論} (§合併概念)
- 被 403 或 Cloudflare 挑戰擋下就停、交給人；不偽裝、不繞過 {討論結論} (§合併概念)
- CAS 寫入：`UPDATE ... WHERE version = ?`，寫入時才檢查是否被別人先改 {討論結論} (§合併概念)

### §業界經典範例
- 這個組合即 Price Intelligence 系統，例：Keepa / CamelCamelCamel、Prisync、Google Shopping、Skyscanner、Trivago {討論結論} (§業界範例)
- 共同特徵：來源多且品質成本不同、價格被多個 worker 同時更新、下游只在價格真的變時才動 {討論結論} (§業界範例)
- 比價業者優先用合作方 API（feed），沒有 feed 才抓網頁 {討論結論} (§業界範例)

### §使用場景
- 例：每 150 分鐘更新 A、B、C 三個競品價格，價格變動時通知定價團隊 {討論結論} (§使用場景)
- 被擋的商品記錄來源為 `fetch:blocked`，不寫入新價 {討論結論} (§使用場景)
- CAS 寫入被拒（別的 worker 先寫）時，重讀版本再試 {討論結論} (§使用場景)
- 新價 ≠ 舊價時，同一 transaction 寫 `outbox(sku, old, new)`；另一個 relay 程式之後送到 Slack / Kafka {討論結論} (§使用場景)
- 被擋商品一直沒更新，到 deadline 時 watchdog 列為過期，通知人處理（申請 API、聯絡對方）{討論結論} (§使用場景)

### §為什麼採用
- 不全部用 headless browser：browser 一次要數秒、耗 CPU、更容易被偵測；多數價格在 API 或原始 HTML 就拿得到 {討論結論} (§Why)
- 被擋時升級到 browser「試試看」等於規避；正確做法是讓 freshness watchdog 把它變成人要處理的事 {討論結論} (§Why)
- 選 CAS（樂觀鎖）不選悲觀鎖：同一商品被兩 worker 同時抓的機率低、重抓便宜，所以「先做、寫入時才檢查」最划算 {討論結論} (§Why)
- CAS 重試類似 Git push 被拒後 pull；差別是這裡重做整次抓取，不做合併 {討論結論} (§Why)
- 不用「寫完 DB 再直接發訊息」：DB 成功、發訊息失敗時下游永遠不知道降價；outbox 讓兩件事同生共死 {討論結論} (§Why)
- Freshness watchdog 用 min-heap：上千商品各有 deadline，只看最早的，不必每分鐘掃全表 {討論結論} (§Why)

### §重點要解決的問題
- 五個目標：成本與覆蓋率平衡、合規（封鎖不繞過、轉人工）、併發寫入不 lost update、事件不遺失不誤發（變了一定發、沒變不發）、沉默失敗被看見 {討論結論} (§重點問題)

### §可執行範例與設計重點
- `Source` 是 port，`FakeSource` 是測試 adapter；正式環境換成 `OfficialApiSource`、`WebFetchSource`、`PlaywrightSource`（hexagonal）{討論結論} (§設計重點)
- `fetch_tiered` 依 `cost` 由低到高嘗試，遇 `BLOCKED` 立即回傳 `<source>:blocked`，不往下一層升級 {討論結論} (§可執行範例)
- `fetch_tiered` 回傳價格加來源；記下來源可統計「多少商品靠 browser 才拿到」當成本指標 {討論結論} (§設計重點)
- `save_price` 的 `rowcount == 0` 即 CAS 失敗；`crawl_once` 最多重試 2 次，避免無限迴圈，超過回 `conflict_giveup` {討論結論} (§設計重點)
- Outbox 只在 `old != new_price` 時寫入：狀態變化才發事件，不是每次抓取都發 {討論結論} (§設計重點)
- 範例用 golden dataset（輸入 → 預期來源、事件、過期清單）加 CAS 衝突測試驗證，原文附輸出全部 PASS {討論結論} (§可執行範例)

### §下一步
- 下一個概念：Outbox relay 是 at-least-once 投遞，可能重送同一事件，下游要用 event id 去重（idempotent consumer）{討論結論} (§下一步)

## 變更
- （首次產生）

## 候選連結
- system-design：http-api-vs-html-curl-cloudflare-bot-policy、web-fetch-crawler-api-browser-agent-comparison、pessimistic-lock-vs-occ-cas-comparison、transactional-outbox-lease-reaper-idempotent-consumer-pattern、data-freshness-watchdog-scanner-marker-golden-pattern、webhook-idempotent-worker-outbox-pattern、saga-outbox-idempotent-escalation-checkout-pattern、structured-rag-golden-eval-hexagonal-pattern
- wiki：optimistic-concurrency、golden-dataset、single-writer、primary-guardrail-gate（被擋即停、交給人）
