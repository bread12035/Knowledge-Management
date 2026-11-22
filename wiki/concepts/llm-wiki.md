---
id: llm-wiki
title: LLM wiki（記憶表示層）
type: concept
summary: LLM 把原始資料編譯成互相連結的頁面；跨文件問題幫助最大，但會膨脹、需要維護
domains: [ai-new-tech]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#4, raw/ai-new-tech/structure-of-agent-system.md#7]
evidence: [原文, Cookbook, 討論結論, 使用者決定]
related: [agent-memory, dreaming, ontology-knowledge-graph, progressive-disclosure, km-dreaming-design, llm-wiki-x-knowledge-retrieval-design]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# LLM wiki（記憶表示層）

> LLM 把原始資料編譯成互相連結的頁面；跨文件問題幫助最大，但會膨脹、需要維護

## 重點
- Wiki 是 Claude 寫並維護的頁面，每頁集中一個主題，連結像地圖 {原文}
- Karpathy 的 LLM wiki 模式：raw/ 不可變、wiki/ 由 LLM 編譯、schema 檔規範做法；操作是 ingest、query、lint {討論結論}
- 跨文件問題幫助最大：Harvey LAB 跨文件題 wiki 87%、只用搜尋 73% {原文}
- 答案集中在單一文件時沒有明顯增益 {原文}
- 會膨脹：10 份文件 115 KB 長成 203 KB，約 1.77 倍，還有孤兒頁 {原文}

## 細節
- Stainless 語料（約 35 萬檔）：只用 wiki 從 13% 升到 48%（2 到 128 個 dreaming session），wiki 加搜尋從 54% 升到 61%，單用搜尋 53%；同時用每題省約 2 萬 token {原文}
- 早期 wiki 像新進員工，後期像有知識地圖的資深員工 {原文}
- Cookbook 格式：小 markdown 檔、frontmatter、`[[slug]]` 連結、根目錄 `_index.md` {Cookbook}
- 使用者的 agent system 把它對應到 Preprocess：`knowledge/l0` 是 raw、`l2` 是頁面、加上 `l1` 結構化表 {使用者決定}

## 在設計中怎麼用
- 什麼情況用：問題需要跨很多份紀錄、同一批資料會被反覆查詢。
- 怎麼用：查詢時先讀索引再讀相關頁，沿連結走；搭配搜尋效果最好。
- 代價：維護成本、膨脹、會寫錯與過期。控制方法：單頁大小上限、寧可連結不複製、定期 lint。
- 與 [[ontology-knowledge-graph]] 的差別：wiki 是自由文字加連結，graph 是受 schema 約束的節點與邊 {我的判斷}

## 未解與衝突
- 原文的未解問題：wiki 何時值得維護成本，以及怎麼避免太詳細而失去用處 {原文}

## 相關
- [[agent-memory]]：wiki 是第 3 層
- [[dreaming]]：建立與維護 wiki 的流程
- [[progressive-disclosure]]：索引 → 頁面 → 原文的讀取順序
- [[ontology-knowledge-graph]]：另一種知識表示
- [[km-dreaming-design]]：這個 repo 的 wiki 規則
- [[llm-wiki-x-knowledge-retrieval-design]]：跨領域：wiki 與摘要分層、SQL catalog 的對照
