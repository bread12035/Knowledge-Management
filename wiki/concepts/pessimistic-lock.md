---
id: pessimistic-lock
title: 悲觀鎖與其他並行寫入選擇（Pessimistic lock）
type: concept
summary: 先鎖再做讓後到者等待；和樂觀鎖的差別只在衝突何時處理，重做昂貴時選悲觀鎖或 single writer queue
domains: [system-design]
sources: [raw/system-design/pessimistic-lock-vs-occ-cas-comparison.md#1, raw/system-design/pessimistic-lock-vs-occ-cas-comparison.md#4, raw/system-design/pessimistic-lock-vs-occ-cas-comparison.md#5, raw/system-design/price-watch-tiered-fetch-cas-outbox-freshness-pattern.md#Why, raw/system-design/seat-hold-cas-timingwheel-outbox-ticketing-pattern.md#為什麼採用這些技術]
evidence: [討論結論]
related: [lease-reaper, reliable-event-processing, optimistic-concurrency-x-pessimistic-lock, seat-hold]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 0
next_review: 2026-11-29
---
# 悲觀鎖與其他並行寫入選擇（Pessimistic lock）

> 先鎖再做讓後到者等待；和樂觀鎖的差別只在衝突何時處理，重做昂貴時選悲觀鎖或 single writer queue

## 重點
- 悲觀鎖假設一定衝突，先鎖再做（B 等待）；樂觀鎖假設衝突少，寫入時用 CAS 比對版本（B 重做）{討論結論}
- 悲觀鎖的代價是等待，但拿到鎖後用的是最新資料；樂觀鎖的代價是白做一次 {討論結論}
- 重做很貴（例如一次 LLM 呼叫要花錢）→ 悲觀鎖或 single writer queue {討論結論}
- 持有鎖者可能掛掉 → 悲觀鎖要加 lease（[[lease-reaper]]）{討論結論}
- 價格監控選 CAS：同商品被兩個 worker 同時抓的機率低、重抓便宜 {討論結論}
- 演唱會搶位也選 CAS：開賣時多數人點不同座位、搶輸只要重選；悲觀鎖讓每人先 `SELECT ... FOR UPDATE` 佔住連線，尖峰時連線池會先爆（[[seat-hold]]）{討論結論}

## 細節
| 情況 | 選擇 |
| --- | --- |
| 衝突少、重做便宜 | 樂觀鎖（CAS：`UPDATE ... WHERE version = ?`） |
| 衝突多 | 悲觀鎖或 single writer queue |
| 重做很貴 | 悲觀鎖或 single writer queue |
| 持有者可能掛掉 | 悲觀鎖 + lease |
| 讀多寫少 | read-write lock 或樂觀鎖 |

- Single writer queue：所有寫入排一條隊由一個 worker 處理，沒有衝突也不用鎖 {討論結論}
- Merge：發現過期時合併雙方改動，不整個重做（像 Git three-way merge）{討論結論}
- 樂觀鎖像 Git push 被拒後 pull 再 push；差別是 Git 重做的是合併，樂觀鎖預設重做整個流程 {討論結論}

## 在設計中怎麼用
- 選鎖時問兩件事：衝突多常見？重做一次多貴？
- 這份討論本身就是在對照 DataFrame cache 的 key 鎖設計，與 dreaming 的 SHA256 憑證設計 {討論結論}

## 相關
- [[lease-reaper]]：悲觀鎖加過期時間的實作
- [[seat-hold]]：高併發下選 CAS 的實例
- [[reliable-event-processing]]：並行寫入在事件處理中的位置
- [[optimistic-concurrency-x-pessimistic-lock]]：跨領域：樂觀鎖與悲觀鎖怎麼選，重做成本是關鍵
