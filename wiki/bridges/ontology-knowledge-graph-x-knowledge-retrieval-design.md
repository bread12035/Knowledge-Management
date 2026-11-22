---
id: ontology-knowledge-graph-x-knowledge-retrieval-design
title: Entity resolution ↔ 查詢時 alias 展開
type: bridge
summary: 兩邊都在處理「同一個東西有不同寫法」；Graph 在寫入時合併成一個節點，SAG 不合併、在查詢時用 alias 表展開
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/ontology-knowledge-graph-guide.md#4, raw/ai-new-tech/ontology-knowledge-graph-guide.md#5, raw/system-design/postgres-sag-alias-golden-eval-pattern.md#為什麼採用這些技術, raw/system-design/postgres-sag-alias-golden-eval-pattern.md#延伸一步, raw/system-design/rag-methods-comparison.md#補充：SAG 不做 entity 去重]
evidence: [討論結論, 我的判斷]
related: [ontology-knowledge-graph, knowledge-retrieval-design, promotion-gate, deterministic-over-llm, golden-regression-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# Entity resolution ↔ 查詢時 alias 展開

> 兩邊都在處理「同一個東西有不同寫法」；Graph 在寫入時合併成一個節點，SAG 不合併、在查詢時用 alias 表展開

## 對照
| | AI new tech：[[ontology-knowledge-graph]] | System design：[[knowledge-retrieval-design]] |
| --- | --- | --- |
| 解決的問題 | 文件沒有統一 ID，`台積電`、`TSMC` 變成多個節點 {討論結論} | SAG 不去重，`台積電` 與 `TSMC` 的 event 用 SQL join 接不起來 {討論結論} |
| 機制 | 寫入時：同類型分組 → 相似度篩選 → 沒把握交 LLM → 選 canonical name、其他存 alias、邊改指新節點 {討論結論} | 查詢時：從問題抽 entity，查 `alias(alias, canonical)` 表雙向展開，再 join {討論結論} |
| 代價 / 限制 | 錯合併（兩個同名的人）事後很難發現；新資料要和舊資料比對 {討論結論} | 每次查詢多一步；alias 表沒收錄就漏資料 {討論結論} |

## 共同原理
- 名字不是身分。系統要有一份「哪些寫法是同一個東西」的對照（canonical + alias），兩邊都用這個結構 {我的判斷}
- 對照表的新增要有人把關：ontology 定案後新類型只標記等人審；alias 表由 LLM 提議、人確認後才寫入（[[promotion-gate]]）{討論結論}
- 一旦確定，就用確定性的方式套用：Graph 改邊、SAG 用 SQL 查表，不在每次查詢時讓 LLM 猜（[[deterministic-over-llm]]）{討論結論}

## 差異
- **時機：** Graph 在寫入時合併（破壞性，改掉原本的邊）；SAG 在查詢時展開（非破壞性，原資料不動）{我的判斷}
- **錯誤的成本：** 寫入時錯合併會污染之後所有查詢，且難回復；查詢時展開錯了，改一行 alias 就好 {我的判斷}
- **代價的位置：** 寫入時合併讓查詢簡單、但新資料要比對舊資料；查詢時展開讓寫入可平行、只追加 {討論結論}

## 在設計中怎麼用
- 誤合併代價高、或來源持續追加 → 原資料不合併，維護 alias 表在查詢時展開。
- 需要多跳關係或精確計數，且同一實體被大量引用 → 寫入時合併，但保留 alias 與原始名稱以便拆回 {我的判斷}
- 不論哪種，把「沒有 alias 會漏資料」固定成 golden case（[[golden-regression-gate]]），改 alias 規則前先跑。

## 相關
- [[ontology-knowledge-graph]]、[[knowledge-retrieval-design]]：兩端的細節
- [[promotion-gate]]：新類型與新 alias 先待審
- [[deterministic-over-llm]]：確定後用查表，不讓 LLM 猜
- [[golden-regression-gate]]：alias 改動的回歸關卡
