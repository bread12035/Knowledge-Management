---
source_project: AI new tech & studies
source_file: claude/Contextualize 加常問問題的索引方案.md
title: Contextualize 加常問問題的索引方案
first_exported: 2026-11-28
updated: 2026-11-28
---
# Contextualize 加常問問題的索引方案

更新日期：2026-11-27
狀態：設計方案，尚未實作。標示「（推論）」的是我的設計判斷，不是論文結論。
相關文件：「Reflection QA 改善 QQ retrieval、rerank、evaluator 方案」

## 1. 一句話結論

每個 chunk 同時附上兩樣東西：
- context（這段出自哪、在講什麼），解決文件側的問題。
- 常問問題 Q，解決查詢側的問題。

A 是原本的 chunk。兩者作用的位置不同，所以可以疊加。

## 2. 各自解決什麼

| 做法 | 解決的問題 | 作用側 |
|---|---|---|
| Contextualize（補上文脈） | chunk 被切出來後失去上下文，例如「它」指誰、屬於哪份文件哪個章節 | 文件側 |
| 附上常問問題 Q | 使用者問的是「問句」，chunk 是「陳述句」，形式對不上 | 查詢側 |

第二點的依據：陳述句形式的內容，和「詢問缺少資訊」的問句，不一定最適合互相比對（Raina & Gales, 2024）。

## 3. 證據

- Contextualize：Anthropic 的 contextual retrieval 號稱可把錯誤的 chunk 檢索率最多降低 67%。這是 Anthropic 自己的說法，QuOTE 論文轉述，未獨立驗證。
- 加問題：arXiv 2508.09755 的消融實驗，比較「只用文件」「只用生成問題（AQG）」「兩者並用」。
  GPT-4o 在 2Wiki 上的答題 F1 分別是 38.95、67.29、69.19。
  並用在每一列都最高，但比只用問題通常只高不到 2 分。
  作者認為生成的問題已涵蓋檢索需要的大部分內容。
- 限制：該實驗用多跳問答資料集與他們自己的流程，不一定適用於我們的文件，必須自己量。

## 4. 資料結構與順序

```json
{
  "chunk_id": "doc1#c3",
  "doc_id": "doc1",
  "context": "這段出自 Acme 2025 年度預算會議紀錄，討論財務部門的核准流程。",
  "chunk_text": "Alice Chen 是 Acme 的財務長，她核准了 2025 年預算。",
  "questions": [
    "誰核准了 Acme 的 2025 年預算？",
    "Acme 的財務長是誰？"
  ]
}
```

順序：
- Step 1：切 chunk。
- Step 2：用整份文件為 chunk 補上 context。
- Step 3：根據「context + chunk」產生問題。
- Step 4：驗證問題，丟掉代名詞不清或沒有根據的。
- Step 5：建索引。

先補 context 再產生問題，是我的設計判斷（推論）：context 能幫 Generator 解開代名詞，問題才能獨立理解，也就符合 reflection QA 的第 3 步。

## 5. 三種索引方式

| 方式 | 做法 | 優點 | 缺點 |
|---|---|---|---|
| 1 單一文字 | context + chunk + 問題串成一段，一個向量 | 最簡單 | 問題的訊號被稀釋 |
| 2 多向量 | 每個問題、以及「context + chunk」各一個向量，都指向同一個 chunk_id，取最高分並去重 | Q-Q 比對最精準，可分開量測 | 索引變大，要處理去重 |
| 3 分開索引 | chunk 索引與問題索引各一個，用 BM25 或 RRF 融合 | 容易做消融與調權重 | 流程較複雜 |

建議從方式 2 或 3 起步，因為可以分別量測各欄位的貢獻。（推論）

## 6. 風險與對策

- 索引膨脹：arXiv 2508.09755 每個 chunk 平均約 11.5 到 12.2 個問題，索引會比只存 chunk 大很多。該論文沒有量化儲存成本。
- 雜訊：生成問題的品質取決於底層 LLM，可能引入雜訊。Doc2Query 後續研究也指出生成可能產生無關擴充。對策：第 4 步驗證。
- 有些 chunk 產不出問題：通常是數字或公式型內容。要保留 chunk 本身的向量當後備。表格多的文件要特別注意。
- 維護成本（推論）：context 依賴整份文件。文件改了，同一份文件所有 chunk 的 context 和問題都要重產。
- 洩漏：附在索引上的問題，不能再拿來當測試題。測試題要另外生成。

## 7. 消融實驗

比較四組：
- 只有 chunk
- chunk + context
- chunk + 問題
- chunk + context + 問題

最後這組再和拼接方式（方式 1、2、3）交叉比較。指標：recall@k、MRR；端到端看答案正確率。

## 8. 待辦

- [ ] 決定每個 chunk 產生幾個問題（參考約 10 個）
- [ ] 設計問題的驗證與過濾規則
- [ ] 設計消融實驗的指標與測試題
- [ ] 決定表格或數字型 chunk 的後備策略

## 9. 來源

- QuOTE：https://arxiv.org/html/2502.10976v1
- Question-Based Retrieval using Atomic Units for Enterprise RAG：https://arxiv.org/html/2405.12363v2
- Transforming Questions and Documents for Semantically Aligned RAG（消融實驗）：https://arxiv.org/pdf/2508.09755
- Doc2Query 的限制與過濾（Hypothetical Prompt Embeddings 論文的相關工作段）：https://arxiv.org/pdf/2607.29402
