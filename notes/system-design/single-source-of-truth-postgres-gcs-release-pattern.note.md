---
raw: raw/system-design/single-source-of-truth-postgres-gcs-release-pattern.md
raw_sha256: df866b9aa02d135fc1fffb70df76428df4964f064885acdafc561b479116c9d6
source: system-design
title: Single Source of Truth:Postgres 編輯 + GCS 發布(Release / Pointer 模式)
generated: 2026-11-18
---
# Single Source of Truth：Postgres 編輯 + GCS 發布（Release / Pointer 模式）（note）

## 一句話
Postgres 是唯一可編輯的真實來源（SSOT），GCS 是單向渲染出來、可重建的發布複本；發布時先把整組檔案寫進不可變的 Release 資料夾，最後才原子地切換 pointer。

## 主張
證據標記對應：Part 1 沒有標記 → {討論結論}；Part 2「Publish Flow」與 Snapshot 原文明標為依慣例**推斷**、非 infra 實際規格 → {我的判斷}。

### 背景
- 現況用 CD pipeline 把 prompt 從企業內部部署到 GCP；infra team 提議改成資料先進 Postgres、再發布到 GCS，GCP 上的 service 從 GCS 讀 prompt {討論結論} (背景)

### Part 1 Single Source of Truth
- SSOT：同一份資料只有一個地方可以改，其他地方都是從它產生的複本 {討論結論} (Part 1)
- Postgres 是 SSOT，人只能經 FastAPI 在這裡編輯；GCS 只由 `config_gen` 寫入，人不能直接改 {討論結論} (Part 1)
- 兩邊不一致時以 Postgres 為準，GCS 錯了就重新產生 {討論結論} (Part 1)
- 資料只單向流動（Postgres → GCS），GCS 不回寫，所以 GCS 是可隨時重建的產物，類似原始碼與編譯產物 {討論結論} (Part 1)
- Service 只讀 GCS，不連 Postgres {討論結論} (Part 1)
- GCS 的 snapshot 保留舊版本，所以它同時是歷史紀錄 {討論結論} (Part 1)
- SSOT 帶來三個好處：解耦編輯與消費環境、可控的發布節奏（按下發布才生效）、可回溯 {討論結論} (Part 1)

### Part 2 Publish Flow（推斷設計）
- 發布 = 把草稿凍結成不可改的 Release（例 `r_0042`），再切換 pointer 指向它 {我的判斷} (Part 2)
- GCS 寫單一檔案是原子的、寫一組檔案不是；先把整組寫進新資料夾，最後改單一 pointer 檔，service 就不會讀到半新半舊 {我的判斷} (Part 2)
- 目錄結構：`current.json`（`{"release": "r_0042"}`）＋ `releases/r_xxxx/`（`manifest.json` 與 prompts）{我的判斷} (Part 2)
- `manifest.json` 記錄檔案清單、每個檔案的 checksum、來源 Postgres 版本、發布者與時間 {我的判斷} (Part 2)
- 發布步驟：開 transaction 鎖草稿 → 整組驗證（失敗回 `409`，什麼都不寫）→ `config_gen` 渲染 → 上傳並讀回比對 checksum → 切換 `current.json` → 在 Postgres 的 `release` 表記錄狀態 `published` {我的判斷} (Part 2)
- 每次發布寫新資料夾不覆蓋、編號遞增不用 latest，出問題時能明確指出是哪一版並回溯 {我的判斷} (Part 2)
- Release 紀錄存在 Postgres，「誰、何時、發布了什麼」仍只有一個答案 {我的判斷} (Part 2)
- 常見做法會加 GCS Object Versioning 當第二層保護避免誤刪 {我的判斷} (Part 2 Snapshot)
- 每個 Release 各自完整一份、不依賴前一版：較耗空間，但最簡單、最不易出錯 {我的判斷} (Part 2 Snapshot)

### 對齊清單與下一步
- 待與 infra 確認：Release 編號規則、pointer 形式、整組驗證規則、是否啟用 Object Versioning 與保留期、`409` 是否也用於版本號不符的編輯衝突 {討論結論} (確認清單)
- 下一步學 rollback（只改 pointer 回上一版）與 service 如何得知 pointer 已變更 {討論結論} (下一步學習)

## 變更
- （首次產生）

## 候選連結
- system-design：onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern（backend 接 GCS／Postgres）、pessimistic-lock-vs-occ-cas-comparison（409 版本衝突）、transactional-outbox-lease-reaper-idempotent-consumer-pattern
- wiki：single-writer（GCS 唯一寫入者 `config_gen`）、optimistic-concurrency、promotion-gate（驗證通過才發布）、llm-wiki（raw → wiki 單向產生）、km-dreaming-design
