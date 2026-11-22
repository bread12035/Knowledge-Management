---
id: single-source-of-truth
title: Single source of truth 與不可變 release（SSOT + immutable release）
type: pattern
summary: 只有一個地方可以編輯，其他都是單向產生、可重建的複本；發布時整組寫入不可變 release，最後原子切換 pointer
domains: [system-design]
sources: [raw/system-design/single-source-of-truth-postgres-gcs-release-pattern.md#Part 1, raw/system-design/single-source-of-truth-postgres-gcs-release-pattern.md#Part 2, raw/system-design/onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern.md#設計原因, raw/system-design/flash-sale-scheduled-release-pointer-saga-rollback-pattern.md#3, raw/system-design/flash-sale-scheduled-release-pointer-saga-rollback-pattern.md#8]
evidence: [討論結論, 我的判斷]
related: [postgres-hub, earnings-gcp-onprem-handover, saga-compensation, event-driven-timer]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 0
next_review: 2026-11-29
---
# Single source of truth 與不可變 release（SSOT + immutable release）

> 只有一個地方可以編輯，其他都是單向產生、可重建的複本；發布時整組寫入不可變 release，最後原子切換 pointer

## 重點
- SSOT：同一份資料只有一個地方可以改，其他都是它產生的複本；不一致時以 SSOT 為準，複本錯了就重新產生 {討論結論}
- Prompt 管理提案：Postgres 是 SSOT（只能經 FastAPI 編輯），GCS 只由 `config_gen` 寫入，service 只讀 GCS {討論結論}
- 資料單向流動、複本不回寫，所以複本像編譯產物，可隨時重建 {討論結論}
- 寫單一檔案是原子的、寫一組檔案不是：先把整組寫進新 release 資料夾，最後改單一 pointer 檔，service 不會讀到半新半舊 {我的判斷}
- 每次發布寫新資料夾不覆蓋、編號遞增，出問題能指出是哪一版，rollback 只改 pointer {我的判斷}

## 細節
- 結構：`current.json`（`{"release": "r_0042"}`）＋ `releases/r_xxxx/`（`manifest.json` 與 prompts）；manifest 記檔案清單、checksum、來源版本、發布者與時間 {我的判斷}
- 發布步驟：鎖草稿 → 整組驗證（失敗回 409，什麼都不寫）→ 渲染 → 上傳並讀回比對 checksum → 切換 pointer → 在 Postgres 記錄 `published` {我的判斷}
- 好處：解耦編輯與消費環境、可控的發布節奏、可回溯 {討論結論}
- **Rollback 的答案**（準點開賣範例）：release 永遠不刪；回滾不是「刪掉新的」，而是把 pointer 指回上一版，只改一個檔案，是最便宜的 rollback。多步發布（upload → switch → purge CDN）中途失敗時，用 Saga 補償做 `switch_back`（[[saga-compensation]]）{討論結論}
- **準點發布**：行銷只寫 Postgres，Scanner 排程、Executor 睡到開賣時間才觸發；觸發前再讀一次 Postgres 確認活動沒被取消（[[event-driven-timer]]）{討論結論}
- 待補：service 怎麼得知 pointer 已變更（polling `current.json` 或推播），決定客戶多快看到新版 {討論結論}
- Part 2 是依慣例推斷的設計，待與 infra 對齊 release 編號、pointer 形式、驗證規則、Object Versioning {討論結論}

## 在設計中怎麼用
- 什麼情況用：設定、prompt、知識內容要從編輯環境發布到執行環境。
- 怎麼用：明確寫出哪裡是 SSOT、誰能寫；複本只由產生器寫；多檔發布用 release + pointer。
- 代價：每個 release 各存一份完整檔案，較耗空間，但最簡單、最不易出錯 {我的判斷}

## 相關
- [[postgres-hub]]：SSOT 放在 Postgres
- [[earnings-gcp-onprem-handover]]：同一個 GCP 環境的資料流
- [[saga-compensation]]：多步發布失敗時把 pointer 指回舊版
- [[event-driven-timer]]：準點觸發發布
