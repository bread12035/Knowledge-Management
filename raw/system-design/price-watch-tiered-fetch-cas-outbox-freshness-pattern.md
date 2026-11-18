---
source_project: system design & code style
source_file: claude/price-watch-tiered-fetch-cas-outbox-freshness-pattern.md
title: 業界經典範例整合：競品價格監控 Price Watch（分層抓取 + CAS 寫入 + Transactional Outbox + Freshness Watchdog）
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：競品價格監控 Price Watch（分層抓取 + CAS 寫入 + Transactional Outbox + Freshness Watchdog）

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。（2026-11-16）

## 這次合併了哪些概念

1. **web-fetch-crawler-api-browser-agent（分層抓取）**：先用官方 API，再用 web fetch，最後才用 headless browser。越後面越貴。
2. **http-api-vs-html-curl-cloudflare-bot-policy（尊重網站政策）**：被 403 或 Cloudflare 挑戰擋下，就停下來交給人。不偽裝、不繞過。
3. **pessimistic-lock-vs-occ-cas（CAS 寫入）**：`UPDATE ... WHERE version = ?`。寫入時才檢查有沒有人先改過。這也是上一篇筆記的「下一步」。
4. **transactional-outbox（Outbox）**：價格更新和「價格變動事件」寫在同一個 transaction。
5. **data-freshness-watchdog（min-heap deadline）**：每個商品有「最晚多久要更新一次」。用 min-heap 找出過期的商品。

## 業界經典範例

這個組合就是 **Price Intelligence（價格情報）系統**：

- **Keepa / CamelCamelCamel**：追蹤 Amazon 商品價格歷史，降價時通知使用者。
- **Prisync、Google Shopping 的比價**：電商定期抓競品價格，觸發自家調價 (repricing)。
- **航空 / 旅宿比價（Skyscanner、Trivago）**：優先用合作方 API (feed)，沒有 feed 才抓網頁。

共同點：資料來源很多，品質和成本不一樣；價格會被多個 worker 同時更新；下游（通知、調價）只在「價格真的變了」時才要動。

## 使用場景

你是一家電商的資料工程師。你要每 150 分鐘更新一次三個競品商品 A、B、C 的價格。價格變動時，要通知定價團隊。

- Step 1（分層抓取）：A 有官方 API → 用 API。B 沒 API，但價格在原始 HTML 裡 → 用 web fetch。C 的網站回 403 → 停下，記錄 `fetch:blocked`。
- Step 2（CAS 寫入）：worker 讀到 `version=1`。寫入時帶 `WHERE version=1`。如果另一個 worker 先寫了，這次寫入被拒，重讀再試。
- Step 3（Outbox）：同一個 transaction 裡，如果新價 ≠ 舊價，寫一筆 `outbox(B, 800, 750)`。另一個 relay 程式之後把它送去 Slack / Kafka。
- Step 4（Freshness）：C 被擋，所以一直沒更新。到 deadline 時，watchdog 把 C 列為「過期」，通知人處理（申請 API、聯絡對方）。

具體輸入與輸出：

| 商品 | 舊價 | 來源 | 新價 | 事件 | 過期？ |
|---|---|---|---|---|---|
| A | 1200 | api | 1200 | 無（沒變） | 否 |
| B | 800 | fetch | 750 | `(B, 800, 750)` | 否 |
| C | 500 | fetch:blocked | — | 無 | 是 |

## 為什麼採用這些技術

- **分層抓取，而不是全部用 headless browser**：browser 一次要幾秒、要 CPU、會被更多偵測。大部分價格在 API 或原始 HTML 就拿得到。從便宜的開始，省錢又穩定。
- **被擋就停，不升級繞過**：網站擋爬蟲常是刻意的。升級到 browser 去「試試看」等於規避。正確做法是讓 freshness watchdog 把它變成「人要處理的事」。
- **CAS（樂觀鎖），而不是悲觀鎖**：同一個商品被兩個 worker 同時抓的機率低。重抓一次很便宜。所以「先做，寫入時才檢查」最划算。它像 Git push 被拒後再 pull。不同點：這裡重做的是整次抓取，不是合併。
- **Transactional Outbox，而不是寫完 DB 再直接發訊息**：如果「DB 寫成功、發訊息失敗」，下游永遠不知道降價了。Outbox 讓兩件事一起成功或一起失敗。
- **Freshness watchdog 用 min-heap**：上千個商品各有 deadline。heap 只看最早的那個。不用每分鐘掃全表。

## 重點要解決的問題

1. **成本與覆蓋率的平衡**：用最便宜但拿得到資料的方法。
2. **合規**：遇到封鎖不繞過，轉成人工流程。
3. **併發寫入不互相覆蓋**：兩個 worker 不會把新價蓋回舊價（lost update）。
4. **事件不遺失、不誤發**：價格變了一定發；沒變不發。
5. **沉默失敗被看見**：抓不到的商品不會「安靜地一直舊著」，會被 watchdog 抓出來。

## 可執行範例（已驗證兩組 golden case + 一組 CAS 衝突測試全部 PASS）

```python
"""Price Watch: tiered fetch + CAS write + transactional outbox + freshness min-heap + golden eval."""
import heapq, sqlite3

# ---- port: 取價格的來源 (由輕到重) ----
class Source:
    name = "base"; cost = 0
    def get_price(self, sku): raise NotImplementedError   # 回傳 int 或 None (拿不到)

class FakeSource(Source):
    def __init__(self, name, cost, prices, blocked=()):
        self.name, self.cost, self.prices, self.blocked = name, cost, prices, set(blocked)
    def get_price(self, sku):
        if sku in self.blocked: return "BLOCKED"           # 403 / Cloudflare 挑戰
        return self.prices.get(sku)

def fetch_tiered(sources, sku):
    """Step 1: 先便宜的來源; 被擋就停, 不升級去繞過."""
    for s in sorted(sources, key=lambda s: s.cost):
        p = s.get_price(sku)
        if p == "BLOCKED": return None, f"{s.name}:blocked"   # 尊重網站政策 -> 交給人
        if p is not None: return p, s.name
    return None, "not_found"

# ---- CAS 寫入 + outbox 同一個 transaction ----
def save_price(db, sku, new_price, now, read_version):
    with db:  # 一個 transaction
        (old,) = db.execute("SELECT amount FROM price WHERE sku=?", (sku,)).fetchone()
        cur = db.execute(
            "UPDATE price SET amount=?, version=version+1, fetched_at=? "
            "WHERE sku=? AND version=?", (new_price, now, sku, read_version))
        if cur.rowcount == 0: return "conflict"            # 別的 worker 先寫了
        if old != new_price:                               # 價格真的變了才發事件
            db.execute("INSERT INTO outbox(sku, old, new) VALUES (?,?,?)", (sku, old, new_price))
        return "ok"

def crawl_once(db, sources, sku, now, retries=2):
    for _ in range(retries + 1):
        (ver,) = db.execute("SELECT version FROM price WHERE sku=?", (sku,)).fetchone()
        price, via = fetch_tiered(sources, sku)
        if price is None: return via
        if save_price(db, sku, price, now, ver) == "ok": return via
    return "conflict_giveup"

# ---- freshness watchdog: min-heap 只看下一個 deadline ----
def stale_skus(db, now, max_age):
    heap = [(t + max_age, sku) for sku, t in db.execute("SELECT sku, fetched_at FROM price")]
    heapq.heapify(heap)
    out = []
    while heap and heap[0][0] <= now:
        out.append(heapq.heappop(heap)[1])
    return sorted(out)

def new_db():
    db = sqlite3.connect(":memory:")
    db.executescript("""
      CREATE TABLE price(sku TEXT PRIMARY KEY, amount INT, version INT, fetched_at INT);
      CREATE TABLE outbox(id INTEGER PRIMARY KEY, sku TEXT, old INT, new INT);
      INSERT INTO price VALUES ('A',1200,1,0),('B',800,1,0),('C',500,1,0);""")
    return db

# ---- golden dataset ----
def run_case(api, html, browser, now=100):
    db = new_db()
    src = [FakeSource("api", 1, api), FakeSource("fetch", 2, html, blocked={"C"}),
           FakeSource("browser", 9, browser)]
    vias = {s: crawl_once(db, src, s, now) for s in "ABC"}
    events = [r for r in db.execute("SELECT sku, old, new FROM outbox")]
    return vias, events, stale_skus(db, now=200, max_age=150)

GOLDEN = [
  # (api, html, browser) -> (預期來源, 預期事件, 預期過期)
  (({"A": 1200}, {"B": 750}, {}),
   ({"A": "api", "B": "fetch", "C": "fetch:blocked"}, [("B", 800, 750)], ["C"])),
  (({"A": 1100, "B": 800}, {}, {}),
   ({"A": "api", "B": "api", "C": "fetch:blocked"}, [("A", 1200, 1100)], ["C"])),
]

def test_cas_conflict():
    db = new_db()
    assert save_price(db, "A", 999, 50, read_version=1) == "ok"
    assert save_price(db, "A", 888, 51, read_version=1) == "conflict"   # 舊版本 -> 被拒
    print("PASS cas_conflict")

if __name__ == "__main__":
    for (api, html, br), (ev, ee, es) in GOLDEN:
        vias, events, stale = run_case(api, html, br)
        assert (vias, events, stale) == (ev, ee, es), (vias, events, stale)
        print("PASS", vias, events, "stale=", stale)
    test_cas_conflict()
```

輸出：

```
PASS {'A': 'api', 'B': 'fetch', 'C': 'fetch:blocked'} [('B', 800, 750)] stale= ['C']
PASS {'A': 'api', 'B': 'api', 'C': 'fetch:blocked'} [('A', 1200, 1100)] stale= ['C']
PASS cas_conflict
```

## 程式裡對應的設計重點

- `Source` 是 port。`FakeSource` 是測試用 adapter。正式環境換成 `OfficialApiSource`、`WebFetchSource`、`PlaywrightSource`。
- `fetch_tiered` 回傳「價格 + 來源」。來源被記下來，之後能統計「多少商品靠 browser 才拿到」，作為成本指標。
- `save_price` 的 `rowcount == 0` 就是 CAS 失敗。`crawl_once` 最多重試 2 次，避免無限迴圈。
- outbox 只在 `old != new_price` 時寫入。這是「狀態變化才發事件」，不是「每次抓取都發」。

## 下一步

最自然的下一個概念是 **Outbox Relay 的 at-least-once 投遞與消費端去重 (idempotent consumer)**：relay 可能重送同一筆事件，下游要用 event id 去重。
