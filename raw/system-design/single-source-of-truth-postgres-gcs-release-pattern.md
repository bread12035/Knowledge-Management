---
source_project: system design & code style
source_file: claude/single-source-of-truth-postgres-gcs-release-pattern.md
title: Single Source of Truth:Postgres 編輯 + GCS 發布(Release / Pointer 模式)
first_exported: 2026-11-18
updated: 2026-11-18
---
# Single Source of Truth:Postgres 編輯 + GCS 發布(Release / Pointer 模式)

> 背景:與 infra team 協作。現況是用 CD pipeline 把 prompt 從企業內部部署到 GCP。infra 提議改成:資料先進 Postgres,再發布到 GCS,GCP 上的 service 從 GCS 讀 prompt。
>
> 註記:「Publish Flow」章節中的細節(目錄結構、步驟順序、`manifest`、`current.json`)是依常見設計慣例**推斷**的,不是 infra team 的實際規格。與 infra 對齊時以他們的版本為準。

---

## Part 1:Single Source of Truth(SSOT,唯一真實來源)

### 核心概念

同一份資料,只有一個地方可以改。其他地方都是從這裡產生出來的複本。

- Postgres = SSOT。人只能在這裡編輯。
- GCS = 產出的複本。人不能直接改它。

### 為什麼需要

沒有 SSOT 時,prompt 可能同時存在兩處(Postgres 與 GCS)。有人改了一份,另一份沒改,就無法確定 service 讀到哪一版。

SSOT 先定一條規則:**兩邊不一致時,以 Postgres 為準。** GCS 錯了,就重新產生。

### 整體架構

```
編輯者 → FastAPI → Postgres (草稿區 + 驗證 + 409)   ← SSOT
                       │
                   config_gen(渲染,單向)
                       ▼
                      GCS (Release + snapshot)       ← 消費格式
                       ▲
                   Service(只讀 GCS,不連 Postgres)
```

### 為什麼 Postgres 與 GCS 要分開

| | Postgres | GCS |
|---|---|---|
| 角色 | 編輯、驗證 | 發布、被讀取 |
| 誰寫入 | 人(經 FastAPI) | 只有 `config_gen` |
| 內容 | 草稿 + 已驗證資料 | 只有已驗證、已發布的版本 |

關鍵:**資料只往一個方向流**(Postgres → GCS),GCS 不回寫 Postgres。所以 GCS 是可隨時重建的產物。

類比:像「原始碼」與「編譯後的程式」。改原始碼,再編譯;不改編譯產物。
不同點:GCS 的 snapshot 會保留舊版本,所以它也是歷史紀錄。

### 三個好處(都是 SSOT 的結果)

1. **解耦編輯環境與消費環境**:編輯時的草稿與錯誤,不會影響正在運行的 service。
2. **可控的發布節奏**:改完不等於生效,按下發布才生效。
3. **可回溯性**:每次發布都是一個固定版本,出問題可以回到上一版。

---

## Part 2:Publish Flow(發布流程,推斷設計)

### 核心概念

發布 = 把草稿凍結成一個不可改的版本包,再切換指標指向它。

- **Release**:一次發布產生的完整檔案集合,有編號(例:`r_0042`)。
- **Immutable**:Release 寫入 GCS 後不再修改。
- **Pointer**:一個小檔案,記錄「目前生效的是哪個 Release」。

### 為什麼需要

Service 要讀一組檔案。GCS 寫單一檔案是原子的(atomic),寫一組檔案不是。寫到一半被讀取,會讀到「一半新、一半舊」。

解法:先把整組寫進新資料夾,全部完成後,再改指標。指標只有一個檔案,切換是原子的。

### GCS 目錄結構

```
gs://prompt-bucket/
├── current.json                 ← Pointer: {"release": "r_0042"}
└── releases/
    ├── r_0041/
    │   ├── manifest.json
    │   └── prompts/summarize_v3.json
    └── r_0042/
        ├── manifest.json        ← 檔案清單 + checksum + 來源資訊
        └── prompts/summarize_v3.json
```

`manifest.json` 記錄:
- 有哪些檔案
- 每個檔案的 checksum(內容指紋)
- 來源的 Postgres 版本、發布者、發布時間

### 流程範例

情境:把 `summarize_v3` 從「請摘要」改成「請用三點摘要」,然後發布。

| Step | 動作 | 說明 |
|---|---|---|
| 1 | 凍結輸入 | FastAPI 對 Postgres 開 transaction,鎖住要發布的草稿 |
| 2 | 整組驗證 | 檢查整組資料(例如所有被引用的 template 都存在)。失敗回 `409`,什麼都不寫 |
| 3 | 渲染 | `config_gen` 讀已驗證資料,產生 `r_0042/` 的所有檔案與 `manifest.json` |
| 4 | 上傳並驗證 | 上傳到 `releases/r_0042/`,讀回比對 checksum |
| 5 | 切換指標 | 把 `current.json` 改成 `{"release": "r_0042"}`,新版生效 |
| 6 | 記錄 | 在 Postgres 的 `release` 表寫入 `r_0042`、時間、發布者、狀態 `published` |

輸入:一批草稿。
輸出:GCS 多了 `r_0042/`,且 `current.json` 指向它。

### 設計原因

| 設計 | 原因 |
|---|---|
| 每次發布寫新資料夾,不覆蓋 | 舊版本保留,可回溯 |
| 先寫完整組,最後才改指標 | Service 不會讀到半新半舊 |
| Step 2 失敗就整個中止 | 壞資料不進 GCS |
| `manifest` 帶 checksum | 能發現檔案損壞或被人手動改過 |
| Release 記錄在 Postgres | 「誰、何時、發布了什麼」只有一個答案(仍是 SSOT) |
| 編號遞增,不用 latest 覆蓋 | 出問題時能明確指出是哪一版 |

### Snapshot 的意思(推斷)

Snapshot 即 `releases/r_xxxx/` 資料夾。常見做法會再加 GCS Object Versioning 當第二層保護,避免誤刪。

類比 git tag:每個版本有固定名稱,指向固定內容。
不同點:git 歷史由 commit 串成;這裡每個 Release 各自完整一份,不依賴前一版。較耗空間,但最簡單、最不易出錯。

---

## 與 infra team 對齊時的確認清單

- Release 編號規則是什麼?(遞增數字、時間戳、hash)
- Pointer 的形式?(`current.json`、GCS 物件 metadata、或 Postgres 查詢)
- Step 2 的整組驗證包含哪些規則?
- 是否啟用 GCS Object Versioning?舊 Release 保留多久?
- `409` 除了關聯完整性,是否也用於編輯衝突(版本號不符)?

## 下一步學習

Rollback(回滾)與 Service 如何讀取 Pointer:出問題時只改一個檔案回到上一版,以及 Service 如何得知指標已變更。
