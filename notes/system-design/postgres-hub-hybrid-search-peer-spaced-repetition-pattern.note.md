---
raw: raw/system-design/postgres-hub-hybrid-search-peer-spaced-repetition-pattern.md
raw_sha256: 52ae07947e8a2f3abaa1169b30a3880da353af3aa805cdd2636e4782fd3167e9
source: system-design
title: 業界經典範例整合：Postgres 單一樞紐（Queue + Hybrid Search）+ PEER 複習迴圈（Spaced Repetition）個人知識庫
generated: 2026-11-18
---
# 業界經典範例整合：Postgres 單一樞紐（Queue + Hybrid Search）+ PEER 複習迴圈（note）

## 一句話
個人知識庫全部放在一個 Postgres：SKIP LOCKED queue 非同步做 embedding、`tsvector` 加 `pgvector` 兩條排名用 RRF 合併，複習時 LLM 只評分、間隔由 SM-2 公式決定。

## 主張
證據標記對照：原文沒有標記；原文明寫為使用者原則者（Postgres go-to、用訊號取代猜測時間差）標 {使用者決定}，其餘 {討論結論}；「延伸一步」為未驗證建議，標 {我的判斷}。原文無編號章節，以章節名稱引用。

### §合併的概念
- 預設用一個 PostgreSQL 加 extensions 同時當 relational/jsonb、pgvector、queue、排程，不為每個需求另外申請服務 {使用者決定} (§這次合併了哪些概念、§為什麼採用這些技術)
- PEER 學習迴圈：AI 解釋 → 使用者複述 → AI 評分 → AI 延伸 {討論結論} (§這次合併了哪些概念)
- generator 與 evaluator 分離，每個模組只回答一個問題（窄介面 deep module）{討論結論} (§這次合併了哪些概念)

### §業界經典範例
- GoodJob、Que、River、Graphile Worker 用 `SELECT ... FOR UPDATE SKIP LOCKED` 讓多個 worker 搶工作不重複，不必另養 Redis/RabbitMQ {討論結論} (§業界經典範例)
- Supabase Hybrid Search 在同一個 Postgres 用 `tsvector` 排名加 `pgvector` 排名，再用 RRF 合併 {討論結論} (§業界經典範例)
- RRF 把每份排名換成 1/(k+名次) 再加總；範例 k=60 {討論結論} (§業界經典範例、§可執行範例)
- SM-2（Anki / SuperMemo）依回想品質 0–5 分決定間隔：答好拉長，答錯歸 1 天 {討論結論} (§業界經典範例)

### §使用場景
- Ingest 時寫入 `notes` 並在 `jobs` 插一筆 `new`；worker 用 SKIP LOCKED 領走後呼叫 embedding API 寫回 `notes.embedding` {討論結論} (§使用場景)
- SM-2 範例：連續 5、5、5 分間隔為 1、6、16 天；q < 3 時 reps 歸 0、間隔 1 天；ef 下限 1.3 {討論結論} (§使用場景、§可執行範例)

### §為什麼採用
- 個人知識庫量小（幾千筆），多養 Redis、向量 DB、排程器的維運成本大於收益 {討論結論} (§為什麼採用這些技術)
- Ingestion 是事件（討論結束）不是時間，所以用 queue 而非 cronjob 輪詢 {使用者決定} (§為什麼採用這些技術)
- 向量找不到精確名詞（如 `SKIP LOCKED`），關鍵字找不到同義說法，所以用 hybrid {討論結論} (§為什麼採用這些技術)
- RRF 只用名次，不必把兩種分數調成同一尺度 {討論結論} (§為什麼採用這些技術)
- LLM 只負責「複述有多準」；「何時再問」是確定性公式，不交給 LLM 猜 {討論結論} (§為什麼採用這些技術)

### §重點要解決的問題
- 依回想品質排複習，而非固定每週看一次 {討論結論} (§重點要解決的問題)
- embedding 要呼叫 API、寫入慢，先入 queue 由 worker 非同步處理、失敗可重試，不卡住對話 {討論結論} (§重點要解決的問題)

### §可執行範例
- SQLite 模擬三組 PASS：queue 不重複領取、RRF 結果 `['outbox','rrf','minheap','jwt']`、SM-2 `[1,6,16]` 且失敗歸 1；Postgres SQL 版本未執行，僅為對照 {討論結論} (§可執行範例)

### §延伸一步
- Evaluator 換成 LLM 評分時，建「複述 → 預期分數」的 golden dataset，改 prompt 前先跑，分數漂移就擋下 {我的判斷} (§延伸一步)
- 用 `pg_cron` 每天產生今日到期複習清單 {我的判斷} (§延伸一步)
- 規模到百萬筆、多人時才考慮拆出專用向量 DB 或獨立 queue；在那之前不拆 {我的判斷} (§延伸一步)

## 變更
- （首次產生）

## 候選連結
- system-design：transactional-outbox-lease-reaper-idempotent-consumer-pattern、postgres-sag-alias-golden-eval-pattern、rag-methods-comparison、single-source-of-truth-postgres-gcs-release-pattern、structured-rag-golden-eval-hexagonal-pattern
- wiki：llm-wiki、dreaming（複習欄位 / 間隔重複）、km-dreaming-design、agent-harness-design、grader-alignment、golden-dataset、agent-memory
