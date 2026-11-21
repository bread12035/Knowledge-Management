---
source_project: system design & code style
source_file: claude/flash-sale-scheduled-release-pointer-saga-rollback-pattern.md
title: 業界經典範例整合：黑色星期五「準點開賣」= Scanner/Executor 排程 + Release Pointer 發布 + Saga 回滾
first_exported: 2026-11-22
updated: 2026-11-22
---
# 業界經典範例整合：黑色星期五「準點開賣」= Scanner/Executor 排程 + Release Pointer 發布 + Saga 回滾

> 本篇由排程自動整理（2026-11-19）。隨機挑選 3 篇過去文件：
> `scanner-executor-timingwheel-nooa-pattern`、`single-source-of-truth-postgres-gcs-release-pattern`、`saga-outbox-idempotent-escalation-checkout-pattern`。
> SSOT 文件的「下一步」是 Rollback。這次用 Saga 的補償動作來回答它。

## 1. 這次合併了哪些概念

| 來源 | 取用的概念 | 在本範例的角色 |
|---|---|---|
| scanner-executor | Scanner、Executor、min-heap | 決定「什麼時候」發布 |
| SSOT release | Postgres = SSOT、immutable Release、Pointer | 決定「發布什麼」、怎麼原子切換 |
| saga | 補償動作、idempotency key、escalation | 決定「失敗時」怎麼退回 |

一句話：**準時、整組、可退回。**

## 2. 業界經典對照

- **Shopify / Amazon Prime Day 的預約開賣**：價格與活動設定先排好，到點自動生效。
- **LaunchDarkly 的 scheduled flag change**：設定變更可以排程，到點切換，失敗可回到上一版。
- **Netflix / Spinnaker 的 deploy pipeline**：多步驟發布，任何一步失敗就自動 rollback。

## 3. 故事：凌晨 00:00 的開賣

小美是電商平台的工程師。黑色星期五 00:00 要開賣。
行銷團隊在後台改好 3000 個商品的折扣價。

### 第一個問題：誰在 00:00 按下發布？

沒有人想守到半夜按按鈕。
如果用 cronjob 每 10 分鐘檢查一次，最晚會晚 9 分鐘才開賣。
這 9 分鐘，客戶看到的還是原價。

→ 用 **Scanner/Executor**。

- **Scanner**：它定期讀 Postgres，把「哪個活動、幾點開賣」整理成排程表。行銷改了時間，Scanner 會更新它。
- **Executor**：它把排程表放進 **min-heap**（最小堆積，堆頂永遠是最早到期的事件）。它 sleep 到堆頂的時間，再觸發。

它像是鬧鐘：只設定「下一次」要響的時間。
不一樣的是：Executor 醒來前，Scanner 可能已經改了時間，所以 Executor 要重新讀一次排程表。

### 第二個問題：3000 個價格怎麼「同時」生效？

如果一個一個寫進 GCS，service 可能讀到「一半新價、一半舊價」。
客戶加入購物車時是折扣價，結帳時變原價。這會變成客訴。

→ 用 **Release + Pointer**。

- **Release**：一次發布的完整檔案包，例如 `r_0042/`。寫完就不改（**immutable**，不可變）。
- **Pointer**：一個小檔案 `current.json`，記錄「現在生效的是哪個 Release」。

所有價格先上傳到 `r_0042/`。全部完成後，只改 `current.json`。
改一個檔案是原子的，所以 service 不會讀到一半。

### 第三個問題：發布到一半失敗怎麼辦？

發布有三步：upload → switch pointer → purge CDN（清除 CDN 快取，讓客戶拿到新價）。
00:00:03，CDN 的 API 回 503。重試 3 次都失敗。
現在 pointer 已切到新版，但 CDN 還在送舊價。兩邊不一致。

→ 用 **Saga 補償**。

- **Saga**：長流程拆成多步。每一步都有對應的 **補償動作**（compensating action，反向抵銷那一步的效果）。
- `switch` 的補償是 `switch_back`：pointer 改回 `r_0041`。
- `upload` 的補償是 `keep_release`：什麼都不刪。Release 保留下來當歷史紀錄。
- 每一步都帶 **idempotency key**（例如 `bf2026:switch_back`）。重送也只做一次。
- 補償完成後，page 值班人員：「開賣失敗，已回到上一版」。

## 4. 控制權怎麼流動（Step by Step）

| Step | 誰 | 做什麼 |
|---|---|---|
| 1 | 行銷 | 在後台改價格。資料只寫進 Postgres（SSOT）。 |
| 2 | Scanner | 讀 Postgres，寫入排程：`(00:00, bf2026, r_0042)`。 |
| 3 | Executor | 把排程放進 min-heap，sleep 到 00:00。 |
| 4 | Executor | 觸發 Saga：upload → switch → purge_cdn。 |
| 5a | 成功 | Pointer = `r_0042`。開賣。 |
| 5b | 失敗 | 反向補償：switch_back → keep_release。Pointer = `r_0041`。Page 值班。 |

## 5. 可執行範例（已驗證輸出）

```python
import heapq

class Store:                        # GCS pointer + idempotent step log
    def __init__(s):
        s.pointer = "r_0041"; s.releases = {"r_0041"}; s.done = set(); s.log = []
    def step(s, key, name, fn):
        if key in s.done: return     # idempotent: re-send does nothing
        fn(); s.done.add(key); s.log.append(name)

def launch(S, sale, rel, fail_at=None, tries=3):
    old = S.pointer
    steps = [("upload",    lambda: S.releases.add(rel),        "keep_release"),
             ("switch",    lambda: setattr(S, "pointer", rel), "switch_back"),
             ("purge_cdn", lambda: None,                       "purge_cdn_again")]
    comps = {"keep_release": lambda: None,
             "switch_back": lambda: setattr(S, "pointer", old),
             "purge_cdn_again": lambda: None}
    applied = []
    for name, fn, comp in steps:
        ok = False
        for _ in range(tries):
            if name == fail_at: continue
            S.step(f"{sale}:{name}", name, fn); ok = True; break
        if not ok:
            for c in reversed(applied):
                S.step(f"{sale}:{c}", c, comps[c])
            return "ROLLED_BACK -> page on-call"
        applied.append(comp)
    return "LIVE"

def executor(schedule, now_end, fail=None):     # min-heap of (fire_time, sale, release)
    S = Store(); heap = list(schedule); heapq.heapify(heap); out = []
    while heap and heap[0][0] <= now_end:
        t, sale, rel = heapq.heappop(heap)        # sleep until t, then fire
        out.append((t, sale, launch(S, sale, rel, fail), S.pointer))
    return out, S.log
```

輸入與輸出：

```
executor([("00:00","bf2026","r_0042")], "00:10")
-> [('00:00','bf2026','LIVE','r_0042')]
   log: ['upload','switch','purge_cdn']

executor([("00:00","bf2026","r_0042")], "00:10", fail="purge_cdn")
-> [('00:00','bf2026','ROLLED_BACK -> page on-call','r_0041')]
   log: ['upload','switch','switch_back','keep_release']
```

## 6. 為什麼採用這些技術

| 技術 | 不用它會怎樣 |
|---|---|
| Scanner/Executor 分開 | 「排程表新不新」與「準不準時」互相拖累。 |
| min-heap，而非固定輪詢 | 輪詢間隔短則浪費 CPU；間隔長則晚開賣。 |
| Postgres = SSOT | 價格同時存在兩處，不知道哪一份是對的。 |
| Immutable Release + Pointer | 客戶讀到半新半舊的價格。 |
| Saga 補償，而非 rollback transaction | GCS 與 CDN 不在同一個 transaction 裡，無法一起撤銷。 |
| Idempotency key | Executor 重啟後重送，pointer 被切換兩次。 |
| Escalation | 補償也失敗時，最後要有人接手。 |

## 7. 重點要解決的問題

1. **準時**：沒有人值夜班，也要在 00:00 開賣。解法：Scanner + Executor + min-heap。
2. **整組生效**：3000 個價格不能一半新一半舊。解法：Immutable Release + 原子切換 Pointer。
3. **可退回**：發布中途失敗，要回到一致的狀態。解法：Saga 補償 + idempotency key + escalation。

## 8. 設計提醒

- Pointer 切換本身就是最便宜的 rollback：只改一個檔案。所以補償動作很簡單。
- Release 永遠不刪。回滾不是「刪掉新的」，而是「指回舊的」。
- Executor 觸發前，要再讀一次 Postgres 確認活動沒有被取消（Scanner 可能剛更新）。
- Saga 狀態要寫進 Postgres。Executor 重啟後，才知道做到哪一步。
- Golden cases：全成功、purge_cdn 失敗、switch_back 也失敗，三條路徑都要測。

## 9. 下一步學習

最自然的下一個概念：**Service 如何得知 Pointer 已變更**（polling `current.json` vs 推播通知），這決定開賣時客戶多快看到新價。
