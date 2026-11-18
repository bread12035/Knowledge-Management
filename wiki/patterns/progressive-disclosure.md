---
id: progressive-disclosure
title: 漸進式揭露與入口地圖（Progressive disclosure）
type: pattern
summary: 給 agent 一個小而穩定的入口，再用指標教它往哪裡找細節，而不是一次塞進所有規則
domains: [ai-new-tech]
sources: [raw/ai-new-tech/structure-of-agent-system.md#2, raw/ai-new-tech/structure-of-agent-system.md#4, raw/ai-new-tech/anthropic-agent-memory-guide.md#5]
evidence: [原文, 使用者決定, 我的判斷]
related: [injected-context, llm-wiki, agent-harness-design]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 漸進式揭露與入口地圖（Progressive disclosure）

> 給 agent 一個小而穩定的入口，再用指標教它往哪裡找細節，而不是一次塞進所有規則

## 重點
- 核心原則：agent 執行時看不到的東西等於不存在，規則、決策、狀態都要寫成檔案 {原文}
- OpenAI 試過超大指令檔，失敗原因：擠掉任務 context、什麼都重要等於什麼都不重要、很快過時、無法用機制檢查 {原文}
- CLAUDE.md 約 100 行，像目錄不像百科；細節放 docs/ {使用者決定}
- Skill 只先露出名稱與描述，需要時才載入全文，這是第二層揭露 {原文}
- 讀取時先讀入口與當前任務記憶，再依指標往下走，不一次讀完所有層 {原文}

## 細節
- 分工：CLAUDE.md 放永遠成立的規則，skill 放做某類事的步驟，output style 放怎麼說話 {我的判斷}
- 使用者的任務 agent 讀取順序固定為 next.md → index.md → L2 → L1 → L0 {使用者決定}
- Claude Code auto memory 只載入 `MEMORY.md` 前 200 行或 25 KB，它本身就是索引 {原文}

## 在設計中怎麼用
- 什麼情況用：agent 要遵守的規則與知識多到放不進每個 session。
- 怎麼用：
  1. 入口檔只放「開始前讀什麼」「永遠成立的規則」「去哪裡找」三段。
  2. 每條細節規則放在專門的文件或 skill，入口只留一行指標。
  3. 用 lint 檢查指標有沒有斷、文件有沒有過期。
- 代價：agent 可能漏讀指標；靠 lint 與指標的清楚程度緩解 {使用者決定}
- 這個 repo：`PRIMER.md` → `wiki/_index.md` → 頁面 → `raw/` 原文。

## 相關
- [[injected-context]]：入口就是常駐層
- [[llm-wiki]]：索引 → 頁面 → 原文的讀取路徑
- [[agent-harness-design]]：使用者的檔案結構
