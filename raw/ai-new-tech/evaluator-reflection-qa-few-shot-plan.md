---
source_project: AI new tech & studies
source_file: claude/Evaluator 用 reflection QA 加真實問題做 few-shot 方案.md
title: Evaluator 用 reflection QA 加真實問題做 few-shot 方案
first_exported: 2026-11-28
updated: 2026-11-28
---
# Evaluator 用 reflection QA 加真實問題做 few-shot 方案

更新日期：2026-11-27
狀態：設計方案，尚未實作。標示「（推論）」的是我的設計判斷，不是論文結論。
相關文件：「Reflection QA 改善 QQ retrieval、rerank、evaluator 方案」

## 1. 一句話結論

把「真實常見問題」比對到 reflection QA，取得答案與證據，組成 evaluator 的案例，再動態挑選相似案例放進 evaluator 的 prompt。
目的：讓 evaluator 更貼近使用者實際的提問方式。

已有類似做法：把人工修正案例放進 evaluator prompt，並追蹤與人工判斷的一致性（LangChain）。
本方案多出的優點：reflection QA 能替真實問題補上答案與證據。

## 2. 流程

- Step 1：收集真實常見問題（紀錄、FAQ 或人工寫的）。
- Step 2：用 Q-Q 比對，把每個真實問題對到最接近的 reflection QA。
- Step 3：驗證比對結果，分成三類：完全對應、部分對應、沒有對應。
- Step 4：把對應到的 QA 組成 evaluator 案例。
  - 給完整證據，標為「夠」。
  - 拿掉一份證據，標為「不夠」。
- Step 5：人工抽驗，再分進 few-shot 池或評測池。
- Step 6：執行時，依當前問題挑 3 到 5 個最相似的案例放進 evaluator 的 prompt。

## 3. 為什麼有幫助

- 使用者的說法：evaluator 看到使用者實際的提問方式與細緻程度，而不只是 LLM 生成的乾淨問句。
- 判斷依據：檢索充分性判斷需要預期事實或預期回答作為標準答案（Databricks/MLflow RetrievalSufficiency）。reflection QA 的答案正好能當預期事實。

## 4. 設計重點

1. 比對到不等於同一題。同一實體、不同屬性或時間的 QA 容易誤配。Step 3 要驗證「這個 QA 的答案是否完整回答真實問題」。
   - 完全對應：直接用。
   - 部分對應：可當「不夠」的範例。證據回答的是鄰近問題，不是這一題。（推論）
   - 沒有對應：最有價值。代表 reflection QA 沒涵蓋到，交給人工標註或補生成 QA。
2. 用答案判斷「夠不夠」，不要用 gold chunk。
   研究發現，用「有沒有 gold 文件」推斷「夠不夠」會讓標準答案出錯，可回答性的 AUROC 最多偏低 0.19。標籤應該是「context 是否涵蓋預期事實」。企業文件重複多，gold chunk 標註本來就不完整。
3. 範例要人工驗過。InstaJudge 的做法是 few-shot 範例只用人工撰寫的資料。我們的案例是 LLM 比對出來的，進 few-shot 池前必須人工抽驗。
4. 範例組成要平衡：同時有「夠」「不夠」與困難的近似案例。只放「夠」會讓 evaluator 偏向放行。（推論）
5. 兩種錯都要量。S2G-RAG 的 sufficiency judge 在 HotpotQA 上：誤判為「夠」的比例 6.44%，把其實夠的判成「不夠」的比例 31.60%。
   推論：在 agentic 流程裡，前者讓錯誤答案流出，後者多出不必要的檢索輪次。
6. 範例不能完全消除偏差。某藥物探索評測系統用 DSPy 的 few-shot 最佳化，一致性從 0.80 提升到 0.86，完整度偏差從 −0.12 降到 −0.08，沒有消除。

## 5. 單筆案例格式

```json
{
  "real_question": "Alice 之前在哪裡上班？",
  "matched_qid": "q_0142",
  "match_status": "partial",
  "expected_facts": ["Alice Chen 2022 年從 Beta 公司加入"],
  "context_case": "missing_hop",
  "label": "insufficient",
  "explanation": "證據只說她核准預算，沒說她之前的公司。",
  "pool": "fewshot"
}
```

## 6. 三份資料不能重疊

| 資料 | 用途 |
|---|---|
| 索引 QA | 給 Q-Q retrieval 當索引 |
| few-shot 範例池 | 放進 evaluator 的 prompt |
| evaluator 評測集 | 衡量 evaluator 的準確率 |

範例若同時出現在 prompt 和評測集，量到的是「背答案」，不是 evaluator 的能力。

## 7. 驗證實驗

比較三種 evaluator：
- A：零樣本。
- B：固定的 few-shot 範例。
- C：依相似度挑選的動態 few-shot（本方案）。

在評測集上看：與人工判斷的一致性、誤放率、誤擋率。
C 明顯勝過 B，才值得維護比對流程。

## 8. 待辦

- [ ] 定義三份資料的切分規則
- [ ] 決定真實問題的收集來源與數量
- [ ] 設計 Step 3 的比對驗證 prompt 與人工抽驗比例
- [ ] 決定 few-shot 的數量與挑選方式（相似度加多樣性）
- [ ] 定期用新紀錄更新範例池（避免分布漂移）（推論）

## 9. 來源

- Databricks/MLflow RetrievalSufficiency judge：https://docs.databricks.com/aws/mlflow3/genai/eval-monitor/concepts/judges/is_context_sufficient
- Better Retrievers, Worse Labels（不完整相關性標註對可回答性評測的影響）：https://arxiv.org/pdf/2610.40966
- InstaJudge（few-shot 範例只用人工資料）：https://aclanthology.org/2025.emnlp-industry.82
- LangChain 校準 LLM-as-a-judge：https://www.langchain.com/articles/llm-as-a-judge
- LangSmith few-shot evaluators：https://docs.langchain.com/langsmith/create-few-shot-evaluators
- S2G-RAG（sufficiency judge 的誤判率）：https://arxiv.org/pdf/2604.23783
- 藥物探索評測系統的人工對齊（DSPy few-shot 最佳化）：https://arxiv.org/pdf/2608.21057
