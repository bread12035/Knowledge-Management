---
source_project: system design & code style
source_file: claude/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md
title: 業界經典範例整合：Transactional Outbox + Postgres Queue（Lease）+ Idempotent Consumer + Lease Reaper
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Transactional Outbox + Postgres Queue（Lease）+ Idempotent Consumer + Lease Reaper

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。（2026-10-19）

## 這次合併了哪些概念

1. **postgres-hub（Postgres 單一樞紐 + SKIP LOCKED queue）**：用同一個 Postgres 當資料庫和 job queue。
2. **webhook-idempotent-worker-outbox（Idempotent Consumer + Outbox）**：傳輸是 at-least-once，接收端要靠「已處理事件 ID」去重。
3. **scanner-executor-timingwheel（min-heap，只醒在下一個 deadline）**：不輪詢，只關心最近的 deadline。這次拿來做「lease 過期回收」。
4. **structured-rag-golden-eval-hexagonal（Golden dataset 回歸關卡）**：每次改規則，都跑固定案例。

## 業界經典範例

- **Transactional Outbox（Chris Richardson, microservices.io）**：業務資料與要發出的事件，寫在同一個 transaction。
- **River / Oban / GoodJob / Graphile Worker**：Postgres job queue。用 `FOR UPDATE SKIP LOCKED` 領工作，用 lease（租約）加 rescuer 回收死掉的 worker。
- **AWS SQS Visibility Timeout**：領走訊息後，一段時間內別人看不到；worker 沒 ack，時間到訊息自動回來。
- **Stripe idempotency key**：重複請求，只執行一次。

## 使用場景

電商：訂單付款成功後，要通知出貨系統。

- Step 1（Producer）：在一個 transaction 裡，寫 `orders(id=1, paid)` 和 `outbox(evt-1)`。輸入：訂單 1。輸出：兩筆資料同時存在，或同時不存在。
- Step 2（Relay/Claim）：worker 領走 `evt-1`，狀態變 `running`，並設 `lease_until = now+10`。
- Step 3（Consumer）：worker 在一個 transaction 裡，寫 `processed(evt-1)` 和 `shipments(order 1)`。
- Step 4（Ack）：worker 把 outbox 標成 `done`。
- Step 5（Crash 情境）：worker 在 Step 3 後、Step 4 前當機。Reaper 在 lease 過期（t=11）把事件放回 `new`。第二個 worker 再領一次，`processed` 主鍵衝突，直接 ack。結果：出貨只有 1 筆。

## 為什麼採用這些技術

- **Outbox，而非「先寫 DB 再發訊息」**：兩個動作不能同時成功。Outbox 讓它們變成一個動作。
- **Postgres queue，而非另養 Kafka/Redis**：事件量不大。一個 DB，一個備份。事件和業務資料還能共用 transaction。
- **Lease + Reaper，而非永遠鎖住**：worker 會當機。沒有 lease，事件會永遠卡在 `running`。
- **Reaper 用 min-heap**：只看最近的 lease deadline，醒來才處理。不用每秒掃全表。
- **Idempotent Consumer，而非「假設不重複」**：lease 回收一定會造成重複投遞。去重是必要的，不是可選的。
- **Golden cases**：三種失敗路徑固定下來。改 lease 時間或 reaper 邏輯，先跑一次再上線。

## 重點要解決的問題

1. 「資料改了但事件沒發」或「事件發了但資料沒改」。解法：Outbox。
2. Worker 當機，事件卡住。解法：Lease + Reaper。
3. 重試造成重複出貨。解法：Idempotent Consumer（用 event_id 主鍵）。
4. 改規則後不知道有沒有壞掉。解法：Golden cases。

## 可執行範例（SQLite 模擬；三組 golden case 全部 PASS）

```python
import sqlite3, heapq

def init(db):
    db.executescript("""
    CREATE TABLE orders(id INTEGER PRIMARY KEY, status TEXT);
    CREATE TABLE outbox(id INTEGER PRIMARY KEY, event_id TEXT UNIQUE, payload TEXT,
                        status TEXT DEFAULT 'new', lease_until INT, attempts INT DEFAULT 0);
    CREATE TABLE processed(event_id TEXT PRIMARY KEY);
    CREATE TABLE shipments(event_id TEXT, order_id INT);
    """)

def place_order(db, order_id, fail=False):          # 1) Producer: 同一 transaction
    try:
        db.execute("BEGIN")
        db.execute("INSERT INTO orders VALUES (?, 'paid')", (order_id,))
        if fail: raise RuntimeError("crash before commit")
        db.execute("INSERT INTO outbox(event_id,payload) VALUES (?,?)", (f"evt-{order_id}", str(order_id)))
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")

def claim(db, now, lease=10):                        # 2) 領工作 + lease（Postgres: FOR UPDATE SKIP LOCKED）
    db.execute("BEGIN IMMEDIATE")
    row = db.execute("SELECT id,event_id,payload FROM outbox WHERE status='new' ORDER BY id LIMIT 1").fetchone()
    if row:
        db.execute("UPDATE outbox SET status='running', lease_until=?, attempts=attempts+1 WHERE id=?", (now+lease, row[0]))
    db.execute("COMMIT"); return row

def handle(db, event_id, payload):                   # 3) Idempotent consumer
    db.execute("BEGIN")
    try:
        db.execute("INSERT INTO processed VALUES (?)", (event_id,))   # 主鍵衝突 = 重複
        db.execute("INSERT INTO shipments VALUES (?,?)", (event_id, int(payload)))
    except sqlite3.IntegrityError:
        pass
    db.execute("COMMIT")

def ack(db, outbox_id):
    db.execute("UPDATE outbox SET status='done' WHERE id=?", (outbox_id,))

def reap(db, now):                                   # 4) Reaper: min-heap 只看最近的 deadline
    heap = [(l, i) for i, l in db.execute("SELECT id,lease_until FROM outbox WHERE status='running'")]
    heapq.heapify(heap); n = 0
    while heap and heap[0][0] <= now:
        _, i = heapq.heappop(heap)
        db.execute("UPDATE outbox SET status='new' WHERE id=? AND status='running'", (i,)); n += 1
    return n
```

Golden cases（orders, outbox, shipments 的筆數）：

```
PASS case_normal (1, 1, 1)
PASS case_producer_crash (0, 0, 0)               # 付款途中當機：沒有訂單，也沒有事件
PASS case_worker_crash_then_retry (1, 1, 1)      # worker 當機後重投：出貨仍只有 1 筆
```

完整腳本含 golden harness（約 80 行）可重現上述輸出。

正式環境的 Postgres 領工作語句：

```sql
UPDATE outbox SET status='running', lease_until=now()+interval '10 s', attempts=attempts+1
WHERE id = (SELECT id FROM outbox WHERE status='new'
            ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING id, event_id, payload;
```

## 延伸一步

- `attempts` 超過上限（例如 5）時，移到 dead-letter 狀態，交給 PagerDuty 式 escalation 通知人。
- 若 consumer 是外部 HTTP 服務，把 `event_id` 當 Idempotency-Key header 送出。
- 規模變大（高吞吐）時，才考慮改用 Debezium CDC 讀 WAL 取代輪詢 outbox。
