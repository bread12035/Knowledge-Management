---
source_project: system design & code style
source_file: claude/postgres-hub-hybrid-search-peer-spaced-repetition-pattern.md
title: 業界經典範例整合：Postgres 單一樞紐（Queue + Hybrid Search）+ PEER 複習迴圈（Spaced Repetition）個人知識庫
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Postgres 單一樞紐（Queue + Hybrid Search）+ PEER 複習迴圈（Spaced Repetition）個人知識庫

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。（2026-10-12）

## 這次合併了哪些概念

1. **engineering（Postgres 為預設樞紐）**：用一個 PostgreSQL 加 extensions，同時當 relational/jsonb、pgvector、queue、排程，不為每個需求另外申請服務。
2. **personal-knowledge-wiki（ingestion / retrieval 兩個 skill）**：討論完要更新知識庫（手動或 cronjob），需要時要能查回來。
3. **peer-learn-skill（PEER：AI 解釋 → 你複述 → AI 評分 → AI 延伸）**：學習時，你自己用一段話說出理解，AI 當 evaluator。
4. **coding-harness-design（generator/evaluator + 窄介面 deep module）**：生成與評分分離，每個模組只回答一個問題。

## 業界經典範例

- **Postgres 當 job queue**：GoodJob、Que、River、Graphile Worker 都用 `SELECT ... FOR UPDATE SKIP LOCKED`。多個 worker 同時搶工作，不會搶到同一筆，也不用多養一套 Redis/RabbitMQ。
- **Supabase 的 Hybrid Search**：同一個 Postgres 裡，`tsvector`（關鍵字）排名加 `pgvector`（語意）排名，再用 **Reciprocal Rank Fusion (RRF)**（倒數排名融合：把兩份排名各自換成 1/(k+名次) 再加總）合併。
- **Anki / SuperMemo 的 SM-2**：依你回想的品質（0–5 分）決定下次複習間隔。答得好，間隔拉長；答錯，間隔歸 1 天。

## 使用場景

你和 Claude 討論完「Outbox pattern」。這次討論要變成知識庫的一筆筆記，之後還要能被查到、被複習。

- Step 1（Ingest）：討論結束，寫入 `notes` 一筆，同時在 `jobs` 插入一筆 `new`。輸入：筆記全文。輸出：job id 1。
- Step 2（Worker）：worker 用 `SKIP LOCKED` 領走 job，呼叫 embedding API，把向量寫回 `notes.embedding`。兩個 worker 同時跑，也不會領到同一筆。
- Step 3（Retrieve）：你問「重複送達怎麼處理」。關鍵字排名：`outbox, minheap, rrf`。向量排名：`rrf, outbox, jwt`。RRF 合併後，`outbox` 第一。
- Step 4（PEER）：Claude 解釋 → 你用一段話複述 → evaluator 給 0–5 分。你連續答 5、5、5，下次複習間隔是 1、6、16 天。你答 2 分，間隔歸 1 天。

## 為什麼採用這些技術

- **Postgres 單一樞紐**：個人知識庫的量很小（幾千筆）。多養 Redis、向量 DB、排程器，維運成本大於收益。一個資料庫，一個備份。（對應你的 Postgres go-to 原則。）
- **SKIP LOCKED queue，而非 cronjob 輪詢**：ingestion 是事件（討論結束），不是時間。job 進表就被領走。對應你「用訊號取代猜測時間差」的原則。
- **Hybrid 而非純向量**：向量找得到「意思像」的筆記，但找不到精確名詞（如 `SKIP LOCKED`）。關鍵字找得到名詞，找不到同義說法。RRF 不需要把兩種分數調成同一尺度，只用名次，簡單可靠。這是「query 優於 guess」的延伸：能精確查的用關鍵字，其餘才用語意。
- **PEER 的評分交給 evaluator，排程交給 SM-2**：LLM 只負責「這段複述有多準」。「何時再問你」是確定性的公式，不交給 LLM 猜。generator/evaluator 分離，加上 human 自己就是回答者。

## 重點要解決的問題

1. 學過的東西會忘。解法：依回想品質排複習，而非固定每週看一次。
2. 筆記存進去了，卻找不到。解法：關鍵字加語意兩條路，用 RRF 合併。
3. 寫入慢（embedding 要呼叫 API），不能卡住對話。解法：先入 queue，worker 非同步處理，失敗可重試。
4. 系統零件太多，一人無法維運。解法：全部放進同一個 Postgres。

## 可執行範例（邏輯已驗證，三組 PASS）

下面的 Python 用 SQLite 模擬 queue 領取（正式環境改用 Postgres 的 SKIP LOCKED），RRF 與 SM-2 為純函式。

```python
import sqlite3
from dataclasses import dataclass

def claim(db):                      # 領一筆 job，不重複
    db.execute("BEGIN IMMEDIATE")
    row = db.execute("SELECT id,note_id FROM jobs WHERE status='new' ORDER BY id LIMIT 1").fetchone()
    if row: db.execute("UPDATE jobs SET status='running' WHERE id=?", (row[0],))
    db.execute("COMMIT"); return row

def rrf(*rankings, k=60):           # Reciprocal Rank Fusion
    score = {}
    for r in rankings:
        for pos, doc in enumerate(r, 1):
            score[doc] = score.get(doc, 0) + 1/(k+pos)
    return sorted(score, key=score.get, reverse=True)

@dataclass
class Card: ef: float = 2.5; reps: int = 0; interval: int = 0
def review(c, q):                   # SM-2: q = evaluator 給的 0-5 分
    if q < 3: c.reps, c.interval = 0, 1
    else:
        c.interval = 1 if c.reps == 0 else 6 if c.reps == 1 else round(c.interval*c.ef)
        c.reps += 1
    c.ef = max(1.3, c.ef + 0.1 - (5-q)*(0.08+(5-q)*0.02))
    return c
```

輸出：

```
PASS queue: no double claim
PASS rrf: ['outbox', 'rrf', 'minheap', 'jwt']
PASS sm2: [1, 6, 16] -> fail resets to 1
```

正式環境的 Postgres 版本（未在本次執行，僅為對照）：

```sql
-- 領工作：多個 worker 不會搶到同一筆
UPDATE jobs SET status='running'
WHERE id = (SELECT id FROM jobs WHERE status='new'
            ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING id, note_id;

-- Hybrid：兩條排名，應用層用 rrf() 合併
SELECT id FROM notes WHERE tsv @@ plainto_tsquery($1) ORDER BY ts_rank(tsv, plainto_tsquery($1)) DESC LIMIT 20;
SELECT id FROM notes ORDER BY embedding <=> $2 LIMIT 20;
```

## 延伸一步

- 把 evaluator 換成 LLM 評分時，要建一組 golden dataset：「複述 → 預期分數」。改 prompt 前先跑，分數漂移就擋下。
- 用 `pg_cron` 每天產生「今日到期複習清單」，與 ingestion 共用同一個 Postgres。
- 規模變大（百萬筆、多人）時，才考慮拆出專用向量 DB 或獨立 queue。在那之前，不拆。
