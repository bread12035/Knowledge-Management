---
id: deterministic-over-llm
title: 能用程式決定的不交給 LLM（Deterministic over LLM）
type: pattern
summary: SQL、公式、程式、Code 評分能確定的部分不讓 LLM 猜；LLM 只做判斷意思、摘要與模糊決策
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/structure-of-agent-system.md#7.4, raw/ai-new-tech/model-evals-product-evals.md#4, raw/system-design/postgres-hub-hybrid-search-peer-spaced-repetition-pattern.md#為什麼採用這些技術, raw/system-design/postgres-sag-alias-golden-eval-pattern.md#為什麼採用這些技術, raw/system-design/web-fetch-crawler-api-browser-agent-comparison.md#5.4, raw/system-design/rag-methods-comparison.md#比較]
evidence: [使用者決定, 討論結論, 我的判斷]
related: [knowledge-retrieval-design, web-content-acquisition, pass-by-reference, ai-evaluation, km-dreaming-design, golden-regression-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 能用程式決定的不交給 LLM（Deterministic over LLM）

> SQL、公式、程式、Code 評分能確定的部分不讓 LLM 猜；LLM 只做判斷意思、摘要與模糊決策

## 重點
- Preprocess 規則：能用程式做的不用 LLM；ETL 用腳本，LLM 只做摘要、缺口分析與反問 {使用者決定}
- 評估：能用 Code 評分就用 Code，LLM judge 只用在 Code 做不到的地方 {討論結論}
- 複習排程：LLM 只評「複述有多準」，「何時再問」由 SM-2 公式決定 {討論結論}
- 檢索：同名不同寫法用一張可讀、可改、可測的 alias 表補，時間條件用 WHERE；SQL 縮小範圍，LLM 判斷意思 {討論結論}
- Browser agent：重複固定的動作寫成複合工具（`scroll_to_bottom()`），模型只做判斷，更快、更省 token、更穩 {討論結論}

## 細節
- 同一個原則在兩個 project 反覆出現：
  - AI new tech：[[pass-by-reference]]（模型寫程式取聚合，不讀全文）、Code grader 優先、Preprocess 的 ETL。
  - System design：alias 表、SM-2、SQL catalog、Scanner/Executor 的確定性排程、web 抓取的複合工具。
- 這個 repo 本身也照做：`scripts/km.py` 負責變更偵測、目錄重建、lint 與到期計算；LLM 只寫 note 與 wiki 內容（[[km-dreaming-design]]）{我的判斷}
- 確定性的部分可以用 golden cases 穩定回歸；LLM 的部分要加模糊案例與人工複核（[[golden-regression-gate]]）{我的判斷}

## 在設計中怎麼用
- 拆解任務時逐步問：這一步有唯一正確答案、能用規則或查詢算出來嗎？是 → 寫程式；否 → 交給 LLM，並設 evaluator 或人工檢查。
- 讓 LLM 提議、人或程式確認：alias 由 LLM 提議、人確認後寫入；ontology 新類型先標記待審 {我的判斷}
- 代價：程式邏輯要維護；規則覆蓋不到的長尾仍需要 LLM。

## 相關
- [[knowledge-retrieval-design]]：SQL 縮範圍、LLM 判斷意思
- [[web-content-acquisition]]：複合工具
- [[pass-by-reference]]：模型寫程式取資料
- [[ai-evaluation]]：Code 評分優先
- [[km-dreaming-design]]：km.py 的分工
- [[golden-regression-gate]]：確定性部分的回歸
