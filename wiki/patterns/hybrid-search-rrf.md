---
id: hybrid-search-rrf
title: Hybrid search 與 RRF（關鍵字 + 向量）
type: pattern
summary: 關鍵字排名與向量排名各算一次，用 RRF 只看名次合併，同時抓到精確名詞與同義說法
domains: [system-design]
sources: [raw/system-design/postgres-hub-hybrid-search-peer-spaced-repetition-pattern.md#業界經典範例, raw/system-design/postgres-hub-hybrid-search-peer-spaced-repetition-pattern.md#為什麼採用這些技術, raw/system-design/postgres-sag-alias-golden-eval-pattern.md#延伸一步]
evidence: [討論結論, 我的判斷]
related: [knowledge-retrieval-design, postgres-hub]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Hybrid search 與 RRF（關鍵字 + 向量）

> 關鍵字排名與向量排名各算一次，用 RRF 只看名次合併，同時抓到精確名詞與同義說法

## 重點
- 向量找不到精確名詞（如 `SKIP LOCKED`），關鍵字找不到同義說法，所以兩條都跑 {討論結論}
- RRF 把每份排名換成 1/(k + 名次) 再加總，常用 k = 60 {討論結論}
- RRF 只用名次，不必把兩種分數調成同一尺度 {討論結論}
- Supabase Hybrid Search 在同一個 Postgres 用 `tsvector` 排名加 `pgvector` 排名再 RRF {討論結論}
- 完整 SAG 也是先用向量與 BM25 找 seed、再 join 展開，兩條排名用 RRF 合併 {我的判斷}

## 細節
- 範例（SQLite 模擬）：RRF 結果 `['outbox','rrf','minheap','jwt']` {討論結論}
- Embedding 要呼叫 API、寫入慢，先入 SKIP LOCKED queue 由 worker 非同步處理，失敗可重試，不卡住對話 {討論結論}

## 在設計中怎麼用
- 什麼情況用：知識庫同時有專有名詞、指令、程式名稱與自然語言描述。
- 怎麼用：`tsvector` 全文 + `pgvector` 相似度各取前 N → RRF 合併 → 需要時再 rerank。
- 代價：兩條索引都要維護；k 值影響前後名次的權重。

## 相關
- [[knowledge-retrieval-design]]：檢索總覽
- [[postgres-hub]]：兩條索引都放在 Postgres
