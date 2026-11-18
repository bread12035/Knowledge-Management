---
id: llm-wiki-x-knowledge-retrieval-design
title: LLM wiki 與記憶分層 ↔ 檢索的摘要分層與 SQL catalog
type: bridge
summary: 兩邊都在寫入時先整理、查詢時先看小的再往下鑽；差別是 wiki 用 LLM 寫的連結頁，檢索設計用 SQL 篩選加 L0/L1/L2 摘要
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#4, raw/ai-new-tech/structure-of-agent-system.md#7, raw/system-design/rag-methods-comparison.md#摘要分層, raw/system-design/rag-methods-comparison.md#catalog, raw/system-design/rag-methods-comparison.md#怎麼讀]
evidence: [原文, 使用者決定, 第三方, 討論結論, 我的判斷]
related: [llm-wiki, knowledge-retrieval-design, progressive-disclosure, dreaming, promotion-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 1
next_review: 2026-11-21
---
# LLM wiki 與記憶分層 ↔ 檢索的摘要分層與 SQL catalog

> 兩邊都在寫入時先整理、查詢時先看小的再往下鑽；差別是 wiki 用 LLM 寫的連結頁，檢索設計用 SQL 篩選加 L0/L1/L2 摘要

## 對照
| | AI new tech：[[llm-wiki]] | System design：[[knowledge-retrieval-design]] |
| --- | --- | --- |
| 解決的問題 | 跨文件問題搜尋要找很多次 {原文} | 向量相似度不夠準、context 塞不下 {討論結論} |
| 機制 | LLM 寫互相連結的頁面，從 index.md 沿 link 讀 {原文} | SQL 縮範圍 → L0 找 → L1 排 → L2 回答 {我的判斷} |
| 何時建關係 | 寫入時（dreaming 是離線批次）{討論結論} | SAG 在查詢時；摘要層在寫入時 {原文}{討論結論} |
| 代價 / 限制 | 膨脹到語料 1.77 倍、會寫錯過期 {原文} | 上層摘要錯會漏掉整棵子樹；漏標 tag 查不到 {我的判斷} |

## 共同原理
- 寫入時先做好摘要與目錄，查詢時先看摘要，需要時才讀原文（[[progressive-disclosure]] 的資料版）。
- 摘要只用來找與排序，答案一律回到原文；不要只壓縮不校對，要定期用原文重驗（[[dreaming]] 的校正用途）{我的判斷}
- 摘要不應比原文長，要有上限並定期比較總量 {我的判斷}

## 差異
- index.md 由 LLM 判斷、可寫自由語意描述，但變大會塞爆 context 且難統計；SQL catalog 精準、可放大量、一行 `COUNT`，但欄位固定 {討論結論}
- 使用者的 Preprocess 兩者都用：L1 是 SQLite 結構化表、L2 是 md 摘要頁 {使用者決定}
- Fact / Understanding 分流的「不確定先放 Understanding、訊號夠強再升級成 Fact」，就是 [[promotion-gate]] 用在資料上 {我的判斷}

## 在設計中怎麼用
- 量小、以文字理解為主 → LLM wiki（這個 repo 的做法）。
- 量大、需要計數、時間或精確條件 → SQL catalog + 摘要層。
- 兩者都要：原文不可變、摘要可重建、帶來源引用、定期 lint。
- 這個 repo 如果要支援「查某段時間學了什麼」或「哪些頁面很久沒複習」，可以把 frontmatter 匯進 SQLite 當 catalog，wiki 頁仍是 md {我的判斷}

## 相關
- [[llm-wiki]]、[[knowledge-retrieval-design]]：兩端的細節
- [[progressive-disclosure]]：先小後大的讀取順序
- [[dreaming]]：離線批次校正摘要
- [[promotion-gate]]：Understanding 升級成 Fact
