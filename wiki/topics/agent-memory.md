---
id: agent-memory
title: Agent memory 四層模型（Agent memory）
type: topic
summary: Transcripts → Notes → Wiki → Injected context，dreaming 在背景校正與整理各層
domains: [ai-new-tech]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#2, raw/ai-new-tech/anthropic-agent-memory-guide.md#6, raw/ai-new-tech/structure-of-agent-system.md#4]
evidence: [原文, 使用者決定, 我的判斷]
related: [dreaming, llm-wiki, injected-context, memory-salience, optimistic-concurrency, single-writer, km-dreaming-design, agent-system-memory-layers]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Agent memory 四層模型（Agent memory）

> Transcripts → Notes → Wiki → Injected context，dreaming 在背景校正與整理各層

## 重點
- Agent memory 是 Claude 從經驗得到、跨 session 保留、之後讀回的 context；權重、in-context learning、compaction 都不算 {原文}
- 四層由下往上：Transcripts（可搜尋事件紀錄）、Memory notes、Memory representations（如 [[llm-wiki]]）、[[injected-context]] {原文}
- 越上層越常被讀、要越小；最上層每個 session 都載入，錯誤會擴散到所有 session {原文}
- 寫筆記是一種預測，前沿模型能自己判斷什麼值得記，見 [[memory-salience]] {原文}
- [[dreaming]] 是離線過程：對照 transcripts 修正、整理成 wiki、把關鍵內容往上提升 {原文}
- 並行寫同一份記憶要有保護：[[optimistic-concurrency]] 或 [[single-writer]] {原文}

## 細節
| 層 | 讀取時機 | 這個 repo 的對應 |
| --- | --- | --- |
| Transcripts | 需要時搜尋 | `raw/` |
| Memory notes | 需要時讀 | `notes/` |
| Wiki | 需要時讀 | `wiki/` |
| Injected context | 每次載入 | `PRIMER.md` |

使用者的 agent system 另有一套依壽命分的五層記憶，見 [[agent-system-memory-layers]]；兩者是不同切法，對照見該頁 {我的判斷}

## 在設計中怎麼用
- 設計 agent 記憶時，先決定每一層放什麼、誰寫、多久整理一次。
- 這個知識庫本身就是四層模型的實作，設計決定見 [[km-dreaming-design]]。

## 未解與衝突
- 原文的未解問題：什麼該進常駐層、wiki 何時值得維護成本、何時建立記憶 {原文}

## 相關
- [[dreaming]]：整理各層的背景流程
- [[llm-wiki]]：第 3 層
- [[injected-context]]：第 4 層
- [[memory-salience]]：第 2 層怎麼寫
- [[optimistic-concurrency]]、[[single-writer]]：並行寫入的保護
- [[agent-system-memory-layers]]：使用者自己的五層記憶
- [[km-dreaming-design]]：這個 repo 的實作
