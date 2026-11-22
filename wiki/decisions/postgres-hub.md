---
id: postgres-hub
title: 預設一個 Postgres（Postgres as the default hub）
type: decision
summary: 規模小時一個 PostgreSQL 加 extensions 同時當 relational、向量、queue、排程，不為每個需求另養服務
domains: [system-design, ai-new-tech]
sources: [raw/system-design/postgres-hub-hybrid-search-peer-spaced-repetition-pattern.md#為什麼採用這些技術, raw/system-design/postgres-sag-alias-golden-eval-pattern.md#為什麼採用這些技術, raw/system-design/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md#為什麼採用這些技術, raw/system-design/rag-methods-comparison.md#和 SAG 比較, raw/ai-new-tech/structure-of-agent-system.md#6]
evidence: [使用者決定, 討論結論, 我的判斷]
related: [lease-reaper, hybrid-search-rrf, knowledge-retrieval-design, single-source-of-truth, transactional-outbox]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# 預設一個 Postgres（Postgres as the default hub）

> 規模小時一個 PostgreSQL 加 extensions 同時當 relational、向量、queue、排程，不為每個需求另養服務

## 重點
- 預設用一個 PostgreSQL 加 extensions 同時當 relational / jsonb、pgvector、queue、排程，不為每個需求另外申請服務 {使用者決定}
- 個人知識庫量小（幾千筆），多養 Redis、向量 DB、排程器的維運成本大於收益 {討論結論}
- 事件量不大時用 Postgres queue 不另養 Kafka / Redis：一個 DB、一個備份，事件與業務資料可共用 transaction（[[transactional-outbox]]）{討論結論}
- SAG 檢索的 event、entity、alias、向量、全文都放同一個 Postgres，資料量幾萬筆不另養 graph DB {討論結論}
- 規模到百萬筆、多人時才考慮拆出專用向量 DB 或獨立 queue {我的判斷}

## 細節
- 對應工具：queue 用 `FOR UPDATE SKIP LOCKED`（[[lease-reaper]]）、全文用 `tsvector`、向量用 `pgvector`（HNSW / IVFFlat）、排程用 `pg_cron` {討論結論}{我的判斷}
- B-tree 只處理相等與大小比較；embedding 相似度要 pgvector 的索引 {討論結論}

## 在設計中怎麼用
- 新服務先問「Postgres 做得到嗎」；需要拆出去時，寫下觸發條件（資料量、併發寫入、多機存取）。
- 與使用者 agent system 的 scale-out 一致：先 SQLite、再共用 DB、最後外部 DB，並行寫入變多是升級訊號。

## 相關
- [[lease-reaper]]、[[transactional-outbox]]：Postgres 當 queue
- [[hybrid-search-rrf]]、[[knowledge-retrieval-design]]：Postgres 當檢索
- [[single-source-of-truth]]：Postgres 當 SSOT
