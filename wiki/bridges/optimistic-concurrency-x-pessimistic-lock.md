---
id: optimistic-concurrency-x-pessimistic-lock
title: 記憶庫的 content_sha256 ↔ 資料庫的悲觀鎖與 CAS
type: bridge
summary: 兩者都在處理「兩個寫入者改同一份資料」；差別只在衝突何時處理，而重做成本決定該選哪一個
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#10, raw/ai-new-tech/anthropic-agent-memory-guide.md#13.2, raw/system-design/pessimistic-lock-vs-occ-cas-comparison.md#5, raw/system-design/price-watch-tiered-fetch-cas-outbox-freshness-pattern.md#Why, raw/system-design/seat-hold-cas-timingwheel-outbox-ticketing-pattern.md#為什麼採用這些技術]
evidence: [官方文件, 使用者決定, 討論結論, 我的判斷]
related: [optimistic-concurrency, pessimistic-lock, single-writer, lease-reaper, km-dreaming-design, seat-hold]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 0
next_review: 2026-11-29
---
# 記憶庫的 content_sha256 ↔ 資料庫的悲觀鎖與 CAS

> 兩者都在處理「兩個寫入者改同一份資料」；差別只在衝突何時處理，而重做成本決定該選哪一個

## 對照
| | AI new tech：[[optimistic-concurrency]] | System design：[[pessimistic-lock]] |
| --- | --- | --- |
| 解決的問題 | 多個 dreaming worker 寫同一個記憶檔或 `queue.md` | 多個 worker 更新同一筆價格、同一個 cache key |
| 機制 | 更新帶 `content_sha256`，不符回 409，重讀重做 {官方文件} | 先鎖再做（等待），或 CAS `WHERE version = ?`（重做）{討論結論} |
| 代價 / 限制 | 每次重試多一次 LLM 呼叫 {我的判斷} | 悲觀鎖要等待、持有者掛掉要 lease；樂觀鎖白做一次 {討論結論} |

## 共同原理
- 衝突一定要處理，只是時間點不同：悲觀鎖在開始前（等待），樂觀鎖在寫入時（重做）。
- 版本憑證（hash 或 version）就是 CAS 的比較值；git push 被拒後 pull 再 push 是同一個機制。

## 差異
- 系統設計的判準是「衝突多不多、重做貴不貴」；重做很貴（一次 LLM 呼叫要花錢）時選悲觀鎖或 single writer queue {討論結論}
- 使用者的 dreaming 設計 D3 選了 `content_sha256`（樂觀），但 worker 的重做正是 LLM 呼叫 {使用者決定}。依系統設計的判準，D3 在衝突多時應改成每頁單一寫入者（[[single-writer]]）或加 lease 的悲觀鎖（[[lease-reaper]]）{我的判斷}
- 系統設計端有一個反例：演唱會搶位衝突少、搶輸只要重選，所以選 CAS；而且 hold 帶 `hold_until`，到期由 reaper 釋放（[[seat-hold]]）。D3 的軟性認領（`queue.md` 的 claimed）沒有到期時間，worker 當機時任務會一直卡在 claimed {討論結論}{我的判斷}
- 這個 repo 採用的是單一寫入者加 git rebase 重試；rebase 不重做 LLM 工作，只重新套用 commit，所以成本低（[[km-dreaming-design]]）{我的判斷}

## 在設計中怎麼用
- 多個 agent 寫共享狀態時，先估「同一頁同時被改的機率」與「重做一次的成本」：
  - 機率低、重做便宜 → 樂觀鎖
  - 機率高或重做是 LLM 呼叫 → 單一寫入者，或悲觀鎖加 lease
- 樂觀鎖的重試要設上限，超過就交人或記 CONFLICT。
- 用 CAS 認領工作或資源時，同時寫到期時間，並讓「完成」與「回收」兩邊都是條件寫入（[[seat-hold]]、[[lease-reaper]]）。

## 相關
- [[optimistic-concurrency]]、[[pessimistic-lock]]：兩端的細節
- [[single-writer]]：從結構上避免衝突
- [[lease-reaper]]：悲觀鎖加過期時間
- [[km-dreaming-design]]：D3 與本 repo 的選擇
- [[seat-hold]]：衝突少時選 CAS，並加到期釋放
