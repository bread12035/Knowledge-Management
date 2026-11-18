---
raw: raw/system-design/postgres-sag-alias-golden-eval-pattern.md
raw_sha256: 9e6d70c0c83be609d6fb2b9ee64c495548c4eb44ae06a7f3d8fee30ec6cb883a
source: system-design
title: 業界經典範例整合：Postgres-only 的 SAG 式知識檢索（Query-time Join + Alias 展開 + 時間過濾 + Golden Eval）
generated: 2026-11-18
---
# 業界經典範例整合：Postgres-only 的 SAG 式知識檢索（note）

## 一句話
SAG 式檢索在寫入時只追加 event 與 entity、查詢時才用 SQL join 建關係；用 alias 表補上不做去重的缺口、用 `event_time` + WHERE 處理時間條件，全部放在一個 Postgres，並用 golden cases 擋住規則退步。

## 主張
證據標記對照：原文沒有標記，一律 {討論結論}；「延伸一步」是未驗證的建議，標 {我的判斷}。原文無編號章節，以章節名稱引用。

### §合併的概念
- SAG 把每段文字變成一個 event 加一組 entity；關係不在寫入時建，查詢時才用 SQL join 串起來 {討論結論} (§這次合併了哪些概念)
- SAG 不做 entity 去重，因此要自己加 alias 對照表；時間用 WHERE 過濾 {討論結論} (§這次合併了哪些概念)
- event、entity、alias、向量、全文都放在同一個 Postgres {討論結論} (§這次合併了哪些概念)

### §業界經典範例
- 企業搜尋（Glean、Notion AI Search）不先建全域 graph，而是查詢時結合關鍵字、語意、權限、時間找資料 {討論結論} (§業界經典範例)
- Elasticsearch / OpenSearch 的 synonym filter 在查詢時展開同義詞（TSMC = 台積電）{討論結論} (§業界經典範例)
- Wikidata 用 alias 欄位處理同一個 entity 的不同寫法 {討論結論} (§業界經典範例)

### §使用場景
- Ingest：每則新聞一次抽取，寫入 `events`（摘要 + `event_time`）與 `event_entity`；新資料直接追加，不和舊資料比對 {討論結論} (§使用場景)
- Query 前處理：從問題抽 entity，用 `alias` 表雙向展開（台積電 → 台積電, TSMC）{討論結論} (§使用場景)
- Query-time join：`JOIN event_entity` 找共用 entity 的 event，依命中 entity 數排序、再依 `event_time` 由新到舊 {討論結論} (§使用場景、§可執行範例)
- 時間條件寫成 `WHERE event_time >= '2026-09-01'` {討論結論} (§使用場景)

### §為什麼採用
- 寫入時每段獨立處理，成本低，不必和全部舊資料對齊；關係只在被問到時才算 {討論結論} (§為什麼採用這些技術)
- 不去重是 SAG 的設計選擇不是 bug；同名不同寫法由一張可讀、可改、可測的小表補上，確定性的事不交給 LLM 猜 {討論結論} (§為什麼採用這些技術)
- 時間是精確條件：能用 SQL 查的不用語意猜 {討論結論} (§為什麼採用這些技術)
- 資料量是幾萬筆等級，一個 DB、一個備份，不另養 graph DB {討論結論} (§為什麼採用這些技術)
- `EntityExtractor` 是 port：正式環境用 LLM 抽 entity，測試用字典，核心邏輯不變且測試可重複 {討論結論} (§為什麼採用這些技術)
- 「沒有 alias 會漏資料」這個失敗要固定成 golden case，改規則才不會悄悄退步 {討論結論} (§為什麼採用這些技術)

### §重點要解決的問題
- 問題中沒有已知 entity 時回空結果，不亂回，再交給向量或全文路徑補 {討論結論} (§重點要解決的問題)
- 向量搜尋不擅長「最近」「9 月後」這類條件，改用 `event_time` + WHERE {討論結論} (§重點要解決的問題)

### §可執行範例
- SQLite 模擬四組 golden case 全部 PASS：無 alias 只找到 1 筆、有 alias 找到 TSMC 與台積電 2 筆、加 since 只剩 1 筆、無 entity 回空 {討論結論} (§可執行範例)
- 改 alias 或排序規則前先跑固定案例，結果變了就擋下改動 {討論結論} (§使用場景 Step 5)

### §延伸一步
- 完整 SAG 流程是先用向量與 BM25 找 seed event 再用 join 展開，兩條排名用 RRF 合併 {我的判斷} (§延伸一步)
- `EntityExtractor` 換成 LLM 時，golden dataset 要加入模糊案例 {我的判斷} (§延伸一步)
- Alias 表可由 LLM 提議、人確認後才寫入（human-in-the-loop）{我的判斷} (§延伸一步)

## 變更
- （首次產生）

## 候選連結
- system-design：rag-methods-comparison、structured-rag-golden-eval-hexagonal-pattern、postgres-hub-hybrid-search-peer-spaced-repetition-pattern、single-source-of-truth-postgres-gcs-release-pattern
- wiki：golden-dataset、ontology-knowledge-graph（entity resolution / alias ↔ SAG 不去重）、promotion-gate（golden cases 當關卡）、ai-evaluation、llm-wiki
