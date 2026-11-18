---
id: optimistic-concurrency
title: 樂觀並行控制（Optimistic concurrency）
type: pattern
summary: 寫入時附上讀到的版本 hash，不符就失敗並重讀重試，避免 last-write-wins
domains: [ai-new-tech]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#10, raw/ai-new-tech/anthropic-agent-memory-guide.md#13.2]
evidence: [官方文件, 使用者決定, 示意, 我的判斷]
related: [single-writer, agent-memory, km-dreaming-design, optimistic-concurrency-x-pessimistic-lock]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 樂觀並行控制（Optimistic concurrency）

> 寫入時附上讀到的版本 hash，不符就失敗並重讀重試，避免 last-write-wins

## 重點
- 沒有 precondition 時，同時寫同一記憶檔是後寫者勝（last-write-wins）{官方文件}
- 更新時帶 `content_sha256` precondition：只有儲存的 hash 還是你讀到的那個才套用，否則回 409 `memory_precondition_failed` {官方文件}
- 409 代表這次寫入沒有生效，不需要還原；重讀（已含別人的修改）、重新草擬、再送出 {示意}
- 重試要有上限，超過就記 CONFLICT 或失敗交人；每次重試多一次模型呼叫 {我的判斷}
- 使用者的 dreaming 設計用它做 worker pool 的硬性保護（D3），但檔案工具是否支援 precondition 尚未驗證 {使用者決定}

## 細節
```text
t1  A 讀檔，hash = abc
t2  B 讀檔，hash = abc
t3  B 更新（附 abc）→ 成功，hash 變成 def
t4  A 更新（附 abc）→ 409
t5  A 重新讀檔（hash = def）
t6  A 依新內容重新草擬，再送出（附 def）→ 成功
```
- 軟性認領任務：worker 讀 `queue.md` 記下 hash，把第一個 pending 改成 claimed 並附 hash 送出；409 就重讀挑下一個 {示意}

## 在設計中怎麼用
- 什麼情況用：多個寫入者偶爾會碰到同一份資料，衝突少但不能互相蓋掉。
- 怎麼用：讀時記版本 → 寫時帶版本 → 衝突時重讀重做 → 重試上限 → 交人。
- 代價：衝突頻繁時重試成本高；需要儲存層支援條件寫入。衝突多就改用 [[single-writer]]。
- 同樣的機制：git push 被拒（遠端有你沒有的 commit）→ fetch、rebase、再 push。這個 repo 的排程就用這個方式處理 push 衝突 {我的判斷}

## 未解與衝突
- 待驗證（guide V1）：Managed Agents 的檔案工具（read/write/edit）是否支援 precondition，可能要把 Memory Stores API 包成自訂工具 {我的判斷}

## 相關
- [[single-writer]]：從結構上避免衝突
- [[agent-memory]]：記憶庫的版本與並行寫入
- [[km-dreaming-design]]：D3 worker pool
- [[optimistic-concurrency-x-pessimistic-lock]]：跨領域：樂觀鎖與悲觀鎖怎麼選，重做成本是關鍵
