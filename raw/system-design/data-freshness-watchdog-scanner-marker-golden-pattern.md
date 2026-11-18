---
source_project: system design & code style
source_file: claude/data-freshness-watchdog-scanner-marker-golden-pattern.md
title: 業界經典範例整合：Data Freshness Watchdog（Scanner/Executor + Completion Marker + Golden-Dataset Eval）
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Data Freshness Watchdog（Scanner/Executor + Completion Marker + Golden-Dataset Eval）

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。（2026-10-05）

## 這次合併了哪些概念

1. **scanner-executor-timingwheel（Scanner/Executor + min-heap）**：Scanner 讓排程表保持新鮮；Executor 用 min-heap 只關心「下一個」deadline，睡到那一刻才醒來。
2. **trino-gateway-oidc-watermark（Completion Marker / Watermark）**：用明確的完成標記判斷資料是否可讀，不用猜固定時間緩衝。
3. **structured-rag-golden-eval-hexagonal（Golden Dataset + Ports & Adapters）**：用一組已知答案的 golden dataset 當 regression gate；用 port 隔離基礎設施。

## 業界經典範例

這個組合就是 **Data Observability / Freshness SLA 監控**：

- **Airflow SLA Miss + Sensor**：Scheduler 記錄每個 task 的 SLA deadline，deadline 到了還沒看到成功訊號，就發出 SLA miss callback。
- **Monte Carlo / Great Expectations 的 Freshness Check**：檢查「某張表在預期時間內有沒有新資料」，不是看時鐘猜。
- **Iceberg/Hudi commit metadata**：commit 是否存在，就是 completion marker。

## 使用場景

on-prem 每 3 小時送一批 log 到雲端，每批有一個 `_SUCCESS` marker。PowerBI、App、Claude Cowork 都依賴這份資料。
你想要：「某批資料超過 deadline 還沒有 marker，才通知我」。

- Step 1（Scanner）：每天產生「預期批次表」。例：`logs_a / batch 09 / deadline 100`。
- Step 2（Executor）：把所有 deadline 放進 min-heap。堆頂 = 最近的 deadline。睡到那一刻。
- Step 3（Marker check）：醒來後只問一件事：marker 在不在？不在 → raw alert。
- Step 4（Evaluator）：檢查 raw alert 合不合理。例：`logs_b` 在維護窗口 → 擋掉。
- Step 5（Golden eval）：每次改規則，都跑 golden dataset。結果變了就擋下改動。

## 為什麼採用這些技術

- **min-heap 而非每分鐘輪詢**：輪詢要在「精準度」和「CPU 消耗」之間取捨；min-heap 讓你只在 deadline 到的那一刻醒來。
- **Completion marker 而非固定緩衝**：批次耗時不穩定。marker 是事件，時間差是猜測。
- **Evaluator 分離**：generator（Executor）只負責「發現遲到」，不負責判斷「該不該吵人」。避免誤報疲勞（alert fatigue）。
- **Golden dataset**：規則（維護窗口、deadline 容忍度）會一直改。沒有固定測資，每次改都是憑感覺。
- **Port/Adapter（`MarkerStore`）**：核心邏輯不知道 marker 在 S3、Iceberg 還是本地檔案；測試時換 Fake adapter 即可。

## 重點要解決的問題

1. 準時偵測「資料遲到」，但不空轉浪費資源。
2. 用事件（marker）判斷完整性，不靠時間猜測。
3. 區分「發現異常」與「值得通知」，降低誤報。
4. 規則持續演進時，用 golden dataset 保證不退步。

## 可執行範例（已驗證三組 golden case 全部 PASS）

```python
"""Data Freshness Watchdog: Scanner/Executor + min-heap + completion marker + golden eval."""
import heapq, sqlite3
from dataclasses import dataclass

# ---- common/: port (介面) ----
class MarkerStore:                       # port: 查 completion marker
    def has_marker(self, dataset, batch): raise NotImplementedError

class FakeMarkerStore(MarkerStore):      # adapter: 測試用; 正式環境換成 S3/Iceberg
    def __init__(self, done): self.done = set(done)
    def has_marker(self, dataset, batch): return (dataset, batch) in self.done

# ---- scanner: 讓「排程表」保持新鮮 ----
def scan(db, expected_batches):
    for ds, batch, deadline in expected_batches:
        db.execute("INSERT OR REPLACE INTO schedule VALUES (?,?,?)", (ds, batch, deadline))

# ---- executor: min-heap 只關心「下一個」deadline ----
@dataclass(order=True)
class Check: deadline: int; dataset: str; batch: str

def run_executor(db, store, now_fn, sleep_fn):
    heap = [Check(d, ds, b) for ds, b, d in db.execute("SELECT * FROM schedule")]
    heapq.heapify(heap)
    alerts = []
    while heap:
        nxt = heap[0]
        wait = nxt.deadline - now_fn()
        if wait > 0: sleep_fn(wait); continue       # event-driven: 睡到下一個 deadline
        c = heapq.heappop(heap)
        if not store.has_marker(c.dataset, c.batch):  # marker 沒出現 = late
            alerts.append({"dataset": c.dataset, "batch": c.batch, "late_by": now_fn() - c.deadline})
    return alerts

# ---- evaluator: 先判斷 alert 合不合理 (generator 只產 raw alert) ----
def evaluate(alerts, maintenance=("logs_b",)):
    return [a for a in alerts if a["dataset"] not in maintenance]

# ---- golden dataset: 回歸關卡 ----
GOLDEN = [  # (已完成的 batch, 預期 alert 的 dataset)
    ({("logs_a", "09"), ("logs_b", "09")}, []),                  # 全到齊 -> 無 alert
    ({("logs_b", "09")}, ["logs_a"]),                            # a 遲到
    (set(), ["logs_a"]),                                         # b 在維護窗口 -> 被 evaluator 擋掉
]

if __name__ == "__main__":
    for done, expected in GOLDEN:
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE schedule(ds TEXT, batch TEXT, deadline INT, PRIMARY KEY(ds,batch))")
        scan(db, [("logs_a", "09", 100), ("logs_b", "09", 110)])
        t = [0]
        def sleep(s): t[0] += s
        alerts = evaluate(run_executor(db, FakeMarkerStore(done), lambda: t[0], sleep))
        got = sorted(a["dataset"] for a in alerts)
        assert got == expected, (got, expected)
        print("PASS", got)

```

輸出：

```
PASS []
PASS ['logs_a']
PASS ['logs_a']
```

## 延伸一步

把 `evaluate()` 換成 LLM evaluator（例如判斷 late_by 的嚴重度、是否該 page 人），golden dataset 就要加入「模糊案例」，並保留 human-in-the-loop 做最後確認。
