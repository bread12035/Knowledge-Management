---
id: ontology-knowledge-graph
title: Ontology 與 Knowledge Graph
type: concept
summary: Ontology 規定允許哪些類型與關係，Graph 存真實的節點與邊；用 ontology 當 LLM 抽取與檢查的標準
domains: [ai-new-tech]
sources: [raw/ai-new-tech/ontology-knowledge-graph-guide.md#1, raw/ai-new-tech/ontology-knowledge-graph-guide.md#3, raw/ai-new-tech/ontology-knowledge-graph-guide.md#4, raw/ai-new-tech/ontology-knowledge-graph-guide.md#7]
evidence: [討論結論, 我的判斷]
related: [llm-wiki, promotion-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Ontology 與 Knowledge Graph

> Ontology 規定允許哪些類型與關係，Graph 存真實的節點與邊；用 ontology 當 LLM 抽取與檢查的標準

## 重點
- Ontology 是規格（像 schema / class），Graph 是資料（像 rows / objects）；ontology 還帶語意，可推出沒寫出的事 {討論結論}
- 沒有 ontology，LLM 每次抽取用不同名字與關係名，Graph 變亂、查不到 {討論結論}
- 抽取循環：ontology 放進 prompt → 抽取 → 用 ontology 檢查、不合法退回 → entity resolution → 寫入 Graph {討論結論}
- 主流建法：LLM 提案（bottom-up）、人審核定案；定案後 LLM 發現的新類型只標記等人審，不自動加入 {討論結論}
- 通常不是 Graph 或 RAG 二選一：關係與數量交給 Graph、細節與原文交給 RAG，合用即 GraphRAG {討論結論}

## 細節
- **Entity resolution**：按類型分組只比同類 → 相似度或 embedding 篩選 → 沒把握的交 LLM 看上下文 → 選 canonical name、其他存 alias、舊邊改指新節點。錯合併（兩個同名的人）事後很難發現 {討論結論}
- **格式**：寫成 Pydantic 或 JSON Schema，搭配 structured output；同一份 schema 是抽取標準也是檢查表。`Literal` 擋不住方向錯的關係，要另寫 validator {討論結論}
- **Graph 的壞處**：建置成本高、不符合類型的細節會流失、抽取或合併錯誤變成看起來很確定的錯誤事實 {討論結論}
- 條件規則（「滿 3 年才能請特休」）不會自動變成 Graph 的一部分 {討論結論}

## 在設計中怎麼用
- 什麼情況用：多跳關係問題、需要精確計數、需要每條事實可追溯來源。
- 怎麼用：先定 ontology v1（人審核）→ structured output 抽取 → validator 檢查 → entity resolution → 寫入；新類型走待審流程（[[promotion-gate]] 的形式）。
- 代價：建置與維護成本；資訊流失；錯誤難發現。
- 和 [[llm-wiki]] 比較：wiki 是自由文字加連結、彈性高；graph 有 schema 約束、可計算。wiki 的 organizer 合併重複頁，和 entity resolution 是同一類問題 {我的判斷}

## 未解與衝突
- 學習狀態：下一步要學 GraphRAG（問題進來時怎麼決定走 Graph 或 RAG，並合併結果）{討論結論}

## 相關
- [[llm-wiki]]：另一種知識表示
- [[promotion-gate]]：新類型先標記、人審後才加入
