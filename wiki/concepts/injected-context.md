---
id: injected-context
title: Injected context（常駐記憶層）
type: concept
summary: 每個 session 都載入的一小層；放關鍵規則加指向下層的指標，錯誤會擴散到所有 session
domains: [ai-new-tech]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#5, raw/ai-new-tech/structure-of-agent-system.md#2]
evidence: [原文, Cookbook, 我的判斷]
related: [agent-memory, progressive-disclosure, dreaming, promotion-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Injected context（常駐記憶層）

> 每個 session 都載入的一小層；放關鍵規則加指向下層的指標，錯誤會擴散到所有 session

## 重點
- 每個 session 開頭載入，其他層則是需要時才讀 {原文}
- 要小：佔 token，而且較長的指令檔會降低遵守可靠度 {原文}
- 錯誤的筆記會被帶進每個 session {原文}
- [[dreaming]] 把細節往下搬、在原地留連結，讓這層保持小；也可以把關鍵筆記 promote 上來 {原文}
- 合理的內容是少量關鍵規則加指向下層的指標 {我的判斷}

## 細節
- Claude Code auto memory 只載入 `MEMORY.md` 前 200 行或 25 KB，原文把它描述成索引 {原文}
- Cookbook 用 mount `instructions`（上限 4,096 字元）注入；注入的文字可能帶進 prompt injection {Cookbook}
- 使用者的 agent system 用約 100 行的 CLAUDE.md 當入口地圖，同樣的想法，見 [[progressive-disclosure]] {使用者決定}

## 在設計中怎麼用
- 什麼情況用：有少數規則每次都必須遵守、或 agent 需要知道去哪裡找。
- 怎麼用：一條一行；規則本身之外，其他都寫成指標；設硬上限並用 lint 檢查。
- 代價：越短越可能漏掉細節，要靠指標與定期檢查補。
- 往上提升要有門檻，避免一次性的結論污染所有 session，見 [[promotion-gate]]。
- 這個 repo 的對應是 `PRIMER.md`（上限 4,096 字元）。

## 未解與衝突
- 原文的未解問題：什麼該放進常駐層，什麼該留在可搜尋的層 {原文}

## 相關
- [[agent-memory]]：第 4 層
- [[progressive-disclosure]]：入口小、細節往下找
- [[promotion-gate]]：什麼能升到常駐層
