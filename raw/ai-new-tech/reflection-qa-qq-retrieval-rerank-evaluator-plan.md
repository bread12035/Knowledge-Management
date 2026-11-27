---
source_project: AI new tech & studies
source_file: claude/Reflection QA 改善 QQ retrieval、rerank、evaluator 方案.md
title: Reflection QA 改善 Q-Q retrieval、rerank、evaluator 方案
first_exported: 2026-11-28
updated: 2026-11-28
---
# Reflection QA 改善 Q-Q retrieval、rerank、evaluator 方案

更新日期：2026-11-27
狀態：設計方案，尚未實作。標示「（推論）」的是我的設計判斷，不是論文結論。

## 1. 一句話結論

用 reflection QA 當一份資料資產，同時服務三件事：Q-Q retrieval 的索引、rerank 的訓練與評測、evaluator 的測試。
關鍵設計：每一題 QA 都要記下出處（gold chunk）。

## 2. 背景：MeMo 與 reflection QA

- MeMo（Memory as a Model，arXiv 2605.15156）：Generator model 把文件改寫成 reflection QA，小型 Memory model 用這些 QA 做 SFT，Executive model 多輪詢問 Memory model。
- reflection QA 是 Generator 把文件變成「問題與答案」的訓練資料。
- 論文的 baseline（BM25、NV-Embed-V2、HippoRAG2）都是對原始文件檢索。
  我讀到的內容沒有「對 reflection QA 做 RAG」的對照組。
  所以不知道 MeMo 的優勢來自 (A) 把文件改寫成 QA，還是 (B) 把 QA 訓練進權重。
- MeMo 刻意不在 QA 上加文件 ID。我們要做評測與檢索，必須把出處補回去。
- 論文數字（準確度 %，Qwen2.5-32B / Gemini-3-Flash 作 Executive）：
  - NarrativeQA：MeMo 26.85 / 53.58；HippoRAG2 21.39 / 23.21；完美檢索 51.42 / 60.41
  - MuSiQue：MeMo 48.30 / 60.20；HippoRAG2 42.17 / 57.00
  - BrowseComp-Plus：MeMo 54.22 / 66.67；HippoRAG2 56.11 / 66.33
  - 解讀：MeMo 的大優勢在需要整合全文的題目（synthesis）。找特定文件的題目（lookup）差距很小。
- MeMo 的成本：reflection 資料生成約 240 個 H200 GPU 小時，訓練 14B Memory model 約 180 個。
  我們的方案只需要生成那一半，不需要訓練。

## 3. 五個步驟對應的題型

| 步驟 | 產出題型 | 測什麼 |
|---|---|---|
| 1 抽取事實（直接＋推論） | 單一事實查找；推論型事實 | 基本檢索 recall |
| 2 合併 | 同一脈絡下的多事實題 | 一次撈回多個事實 |
| 3 驗證與改寫 | 不產生新題，是品質關卡 | 題目能獨立理解，無代名詞 |
| 4 浮出實體 | 描述屬性、答案是名字 | 只有模糊描述時能否找到 |
| 5 跨文件綜合 | 每題需要多份文件支持 | 多跳檢索、agentic 多輪 |

第 5 步題目的 gold 是一組 chunk，評測看「整組是否都撈到」。

## 4. 單筆資料格式

```json
{
  "qid": "q_0142",
  "question": "核准 Acme 2025 年預算的人，之前在哪家公司工作？",
  "answer": "Beta 公司",
  "type": "cross_doc",
  "gold_chunks": ["doc1#c3", "doc2#c1"],
  "evidence_spans": ["...核准了 2025 年預算", "...2022 年從 Beta 公司加入"],
  "verified": true,
  "split": "test"
}
```

- type：direct / indirect / multi_fact / entity / cross_doc。用來分題型看分數。
- split：index 或 test。用來管理索引集與測試集。

## 5. 三個用途

### A. Q-Q retrieval 索引
- 索引存「問題」，命中後回傳答案與 chunk 指標。
- 有研究支持這個方向：
  - QuOTE：把假設性問題與 chunk 一起 embed，改善檢索。
  - Raina & Gales：把 chunk 拆成原子陳述，再對原子產生問題，recall 高於直接用 chunk。
- 風險：Doc2Query 類方法可能產生無關擴充、索引膨脹。第 3 步驗證就是過濾關卡。

### B. Rerank
- 正樣本：gold chunk。
- 困難負樣本：同一實體或同一群組的其他 QA（主題相近、答案不同）。（推論）
- 評測：用 gold 標籤算 MRR、nDCG。

### C. Evaluator（agentic loop 裡判斷「證據夠不夠」）
- 該通過：給完整證據，應判定「夠」。
- 該擋下：用跨文件題，拿掉其中一份證據，應判定「不夠」。（推論）
- 也可用 gold 答案量 evaluator 本身的準確率。

## 6. Agentic RAG 分段量測

| 階段 | 指標 |
|---|---|
| 檢索 | recall@k（跨文件題看整組是否全撈到） |
| rerank | MRR、nDCG |
| evaluator | 證據是否足夠的判斷準確率 |
| 端到端 | 答案正確率 |

分段量測的用處：哪一段掉分，就知道該改哪一段。

## 7. 風險與對策

1. 洩漏：同一批 QA 既是索引又是測試集，Q-Q 會幾乎必中，分數是假的。
   對策：索引 QA 與測試 QA 分開生成（換 prompt、換模型），或留一批文件不進索引。
2. 合成題不等於真實問題：研究發現合成基準在比較不同 generator 架構時，排名不一致，可能有風格偏好；RAGalyst 的實驗則幾乎沒看到來源偏差，證據不一致。
   對策：合成題擴大覆蓋，再用幾十題真實問題校準。
3. 企業文件重複內容多：只標一個 gold chunk 會漏標，別的 chunk 也能答卻被算錯。
   對策：參考 RARE，把文件拆成原子事實追蹤冗餘。
4. 第 3 步只檢查「題目能否獨立理解」，不檢查答案真偽。
   對策：另加一步，用原 chunk 檢查答案有根據；再抽樣人工看。（推論）
5. 成本：第 5 步成本隨群組大小快速增加，論文給的複雜度是 O(k·C²·Q²)。
   對策：群組不要切太大。
6. 生成的題目太乾淨，真實使用者會問得含糊。
   對策：生成時加入不同的提問風格或角色。（推論）

## 8. 驗證實驗

比較三組，看「QA 本身」與「訓練進權重」各貢獻多少：

- A：對原文 chunk 做 RAG。
- B：對 reflection QA 做 RAG（本方案）。
- C：MeMo。

判讀：B 贏 A 但輸 C，表示訓練進權重有價值。B 已接近 C，就不值得付訓練成本。

## 9. 待辦

- [ ] 定義索引 QA 與測試 QA 的切分規則（避免自己考自己）
- [ ] 學習 MeMo 的三階段推論協議（Executive 怎麼逐步追問）
- [ ] 設計第 3 步之後的「答案真偽」檢查
- [ ] 準備幾十題真實問題作校準集

## 10. 來源

- MeMo 論文：https://arxiv.org/abs/2605.15156
- MeMo 作者 blog：https://arunv3rma.github.io/blogs/memo/
- VentureBeat 報導：https://venturebeat.com/orchestration/memo-memory-model-teams-upgrade-llm-without-retraining
- QuOTE：https://arxiv.org/html/2502.10976v1
- Question-Based Retrieval using Atomic Units：https://arxiv.org/html/2405.12363v2
- Doc2Query 的限制與過濾（Hypothetical Prompt Embeddings 論文的相關工作段）：https://arxiv.org/pdf/2607.29402
- 合成基準的可靠性：https://arxiv.org/abs/2508.11758v1
- RAGalyst（generator 偏差檢查）：https://arxiv.org/pdf/2511.04502
- RARE（冗餘感知的檢索評測）：https://arxiv.org/html/2604.19047v1
- DataMorgana（合成基準的多樣性）：https://preview.aclanthology.org/landing_page/2025.acl-industry.33.pdf
