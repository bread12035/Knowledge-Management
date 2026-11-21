---
source_project: system design & code style
source_file: claude/seat-hold-cas-timingwheel-outbox-ticketing-pattern.md
title: 業界經典範例整合：演唱會選位 Seat Hold — CAS 搶位 + Timing Wheel 到期釋放 + Outbox 出票
first_exported: 2026-11-22
updated: 2026-11-22
---
# 業界經典範例整合：演唱會選位 Seat Hold — CAS 搶位 + Timing Wheel 到期釋放 + Outbox 出票

> 本篇由排程自動整理（2026-11-20）。隨機挑選專案文件中的三個概念，合併成一個實作。

## 這次合併了哪些概念

1. **pessimistic-lock-vs-occ-cas-comparison**：CAS（Compare-And-Swap）。「如果現在還是我讀到的版本，才寫入。」本篇用它搶座位。
2. **scanner-executor-timingwheel-nooa-pattern**：min-heap / Timing Wheel。只在下一個 deadline 醒來。本篇用它釋放過期的保留座位。
3. **transactional-outbox-lease-reaper-idempotent-consumer-pattern**：Outbox。業務資料和事件寫在同一個 transaction。本篇用它在付款成功後發出「出票」事件。

## 業界經典範例

- **Ticketmaster / KKTIX / 拓元**：選位後，座位保留 10 分鐘。時間到沒付款，座位回到市場。
- **Booking.com / Airbnb**：訂房時先「暫扣」房間，付款後才確認。
- **航空公司 PNR hold**：訂位保留到某個時間點，過期自動取消。

這類設計叫 **Seat Hold（座位保留）**。白話：座位不是一次賣掉，而是分兩步：先「暫時占住」，再「付款買下」。
它像是餐廳訂位保留 15 分鐘。不一樣的地方：餐廳靠店員看時鐘；系統要自己算時間，而且要處理上千人同時搶同一個位子。

## 故事：週五晚上 8 點開賣

某天團演唱會，週五 20:00 開賣。A 區第 1 排 1 號（A1）是最好的位子。

20:00:00.120，小明和小華同時點了 A1。兩人的瀏覽器都看到 A1 是「空位」，版本號 version = 0。

- Step 1（搶位）：兩人都送出「如果 A1 還是 version 0，就保留給我」。資料庫一次只執行一個 UPDATE。小明先到，A1 變成 `held`，version 變 1。小華的條件 `version = 0` 不成立，更新 0 列。系統回小華：「這個位子剛被選走」。
- Step 2（倒數）：小明有 600 秒付款。座位上記錄 `hold_id = h-明`、`hold_until = 600`。
- Step 3（放棄）：小明卡在信用卡驗證，600 秒到了還沒付。Reaper（回收器）在 t=600 醒來，把 A1 放回 `free`。
- Step 4（第二輪）：小華重新整理，看到 A1 又是空位（version 2）。她在 t=601 搶到，t=700 付款成功。同一個 transaction 裡，A1 變 `sold`，outbox 多一筆 `ticket-h-華`。出票服務之後再讀 outbox 寄電子票。
- Step 5（晚到的付款）：小明的銀行在 t=650 才回「付款成功」。系統用 `hold_id = h-明` 去改 A1，條件不成立。結果：拒絕，觸發退款。A1 不會被賣兩次。

## 為什麼採用這些技術

**為什麼搶位用 CAS，不用悲觀鎖？**
開賣瞬間有上萬人點不同座位。大部分人點的位子不一樣，衝突其實很少。CAS 不需要排隊等鎖。搶輸的人只是重選一個位子，代價很低。這正好符合「衝突少、重做便宜 → 樂觀鎖」的選擇規則。
如果用悲觀鎖，每個人都要先 `SELECT ... FOR UPDATE`，連線被佔住，開賣尖峰時資料庫連線池會先爆。

**為什麼釋放用 min-heap / Timing Wheel，不用每秒掃全表？**
同時有幾萬個保留中的座位。每秒掃一次全表，大部分時間都在看「還沒到期」的資料。min-heap 只看堆頂：最早到期的那一個。沒到期就繼續睡。規模更大時（百萬級 hold），換成 Kafka 那種 Hierarchical Timing Wheel，插入和到期都接近 O(1)。

**為什麼釋放也要用 CAS？**
Reaper 和付款可能同時發生。Reaper 的 UPDATE 帶 `WHERE hold_id = ? AND status = 'held'`。如果付款先成功，status 已經是 `sold`，Reaper 更新 0 列，什麼都不做。反過來，付款的 UPDATE 帶 `hold_until > now`。就算 Reaper 還沒跑，過期的付款也會被拒絕。兩邊都用條件寫入，所以誰先到都不會出錯。

**為什麼出票用 Outbox，不直接呼叫出票 API？**
「座位變 sold」和「要出票」必須同時成立。如果先改 DB 再呼叫 API，API 失敗時會出現「賣了但沒票」。Outbox 讓兩件事變成一個 transaction。出票服務用 `event_id` 去重，重送也只出一張票。

## 重點要解決的問題

1. **超賣（double booking）**：兩人同時搶一個位子。解法：CAS 條件更新，只有一人成功。
2. **座位被占著不付錢**：保留的人離開。解法：`hold_until` + min-heap Reaper 到期釋放。
3. **付款和到期的競態（race condition）**：付款在第 599.9 秒，Reaper 在第 600 秒。解法：兩邊都是 CAS，資料庫決定唯一的贏家。
4. **賣了但沒出票**：解法：Outbox，座位狀態和出票事件一起 commit。

## 可執行範例（SQLite 模擬；四組 golden case 全部 PASS）

```python
import sqlite3, heapq

def init():
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.executescript("""
    CREATE TABLE seats(id TEXT PRIMARY KEY, status TEXT DEFAULT 'free',
                       hold_id TEXT, hold_until INT, version INT DEFAULT 0);
    CREATE TABLE outbox(event_id TEXT PRIMARY KEY, seat_id TEXT, hold_id TEXT, status TEXT DEFAULT 'new');
    INSERT INTO seats(id) VALUES ('A1');
    """)
    return db

def read(db, seat):
    return db.execute("SELECT status, version FROM seats WHERE id=?", (seat,)).fetchone()

def hold(db, seat, hold_id, version, now, ttl=600):          # CAS: 只有 version 沒變才成功
    cur = db.execute("""UPDATE seats SET status='held', hold_id=?, hold_until=?, version=version+1
                        WHERE id=? AND status='free' AND version=?""",
                     (hold_id, now+ttl, seat, version))
    return cur.rowcount == 1

def pay(db, seat, hold_id, now):                              # CAS + Outbox 同一個 transaction
    db.execute("BEGIN")
    cur = db.execute("""UPDATE seats SET status='sold', version=version+1
                        WHERE id=? AND hold_id=? AND status='held' AND hold_until>?""",
                     (seat, hold_id, now))
    if cur.rowcount == 1:
        db.execute("INSERT INTO outbox(event_id,seat_id,hold_id) VALUES (?,?,?)",
                   (f"ticket-{hold_id}", seat, hold_id))
        db.execute("COMMIT"); return True
    db.execute("ROLLBACK"); return False                      # 呼叫端退款

def reap(db, now):                                            # min-heap: 只處理到期的 hold
    heap = [(u, s, h) for s, h, u in db.execute(
        "SELECT id, hold_id, hold_until FROM seats WHERE status='held'")]
    heapq.heapify(heap); n = 0
    while heap and heap[0][0] <= now:
        _, s, h = heapq.heappop(heap)
        cur = db.execute("""UPDATE seats SET status='free', hold_id=NULL, hold_until=NULL,
                            version=version+1 WHERE id=? AND hold_id=? AND status='held'""", (s, h))
        n += cur.rowcount
    return n

def snap(db):
    st = db.execute("SELECT status FROM seats WHERE id='A1'").fetchone()[0]
    ob = db.execute("SELECT count(*) FROM outbox").fetchone()[0]
    return st, ob

def case_two_users_same_seat():
    db = init(); _, v = read(db, "A1")                       # A、B 都讀到 version 0
    a = hold(db, "A1", "h-A", v, now=0); b = hold(db, "A1", "h-B", v, now=0)
    return (a, b, *snap(db)) == (True, False, "held", 0)

def case_hold_expires_then_other_buys():
    db = init(); _, v = read(db, "A1"); hold(db, "A1", "h-A", v, now=0)
    released = reap(db, now=600)
    _, v = read(db, "A1"); ok = hold(db, "A1", "h-B", v, now=601) and pay(db, "A1", "h-B", now=700)
    return (released, ok, *snap(db)) == (1, True, "sold", 1)

def case_late_payment_rejected():
    db = init(); _, v = read(db, "A1"); hold(db, "A1", "h-A", v, now=0)
    ok = pay(db, "A1", "h-A", now=650)                        # 超過 600，reaper 還沒跑也要拒絕
    return (ok, *snap(db)) == (False, "held", 0)

def case_pay_wins_race_with_reaper():
    db = init(); _, v = read(db, "A1"); hold(db, "A1", "h-A", v, now=0)
    ok = pay(db, "A1", "h-A", now=599)                        # 付款先到
    released = reap(db, now=600)                              # reaper 晚到：CAS 不成立
    return (ok, released, *snap(db)) == (True, 0, "sold", 1)

for c in [case_two_users_same_seat, case_hold_expires_then_other_buys,
          case_late_payment_rejected, case_pay_wins_race_with_reaper]:
    print("PASS" if c() else "FAIL", c.__name__)
```

輸出：

```
PASS case_two_users_same_seat
PASS case_hold_expires_then_other_buys
PASS case_late_payment_rejected
PASS case_pay_wins_race_with_reaper
```

正式環境（Postgres）的搶位語句：

```sql
UPDATE seats
SET status = 'held', hold_id = $1, hold_until = now() + interval '10 min', version = version + 1
WHERE id = $2 AND status = 'free' AND version = $3;
-- rowcount = 0 → 回前端「位子剛被選走」
```

## 下一步

最自然的下一個概念：**Virtual Waiting Room（虛擬排隊室）**。它在流量進到 CAS 之前先排隊限流，避免開賣瞬間把資料庫打爆。
