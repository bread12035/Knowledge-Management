---
id: grader-alignment
title: Grader 代表 User（LLM-as-judge alignment）
type: concept
summary: 讓 LLM judge 的判斷與 User 一致、無偏、穩定：用 kappa、McNemar、mutation test、順序交換檢查，用理由與偏好修正
domains: [ai-new-tech]
sources: [raw/ai-new-tech/model-evals-product-evals.md#6, raw/ai-new-tech/model-evals-product-evals.md#7.1, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#2.5, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#4.11]
evidence: [原文, 討論結論, 第三方, 示意, 我的判斷]
related: [ai-evaluation, promotion-gate, harness2, cuped, error-analysis-loop]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# Grader 代表 User（LLM-as-judge alignment）

> 讓 LLM judge 的判斷與 User 一致、無偏、穩定：用 kappa、McNemar、mutation test、順序交換檢查，用理由與偏好修正

## 重點
- Grader 代表 User 看三件事：一致、無偏、穩定 {我的判斷}
- 只看原始一致率會被騙：範例 92% 一致但 kappa 只有 0.46，人說錯的 10 題 judge 只抓到 4 題 {示意}
- 同一張 judge vs 人的表：kappa 看對角線（一致嗎）、McNemar 看 b 與 c（偏鬆還是偏嚴）{討論結論}
- 強 judge 也有位置偏差，對調答案會改變結論；還有冗長偏差、自我偏好偏差 {原文}
- Grader 就是 reward function；偏好長答案的 grader 當優化目標，系統會學著寫長（reward hacking 縮小版）{我的判斷}

## 細節
**檢查** {討論結論}：
- 分層人工標註：每個子群都要有；和人與人之間的 kappa 比，那是上限
- Mutation test：對好答案注入錯誤（改數字、刪條件、加幻覺），沒抓到的是盲區
- 順序交換：每對兩種順序各評一次，分一致 / 跟著位置 / 不穩定；只有兩次一致才算贏；跟著位置超過約 20% 先修 prompt {我的判斷}
- 預測效度：judge 分數是否預測線上訊號，是「像不像 User」最直接的檢查
- judge prompt 一改就重新校準

**修正** {我的判斷}：
- SFT 式：User 寫「為什麼這樣打分」，寫進 rubric 與 few-shot
- RLHF 式：User 二選一，選答案算 pairwise accuracy，選 grader 輸出挑 prompt 版本
- 流程：兩版 prompt 只改一處 → 盲選、隨機左右 → User 選並寫理由 → 理由 pending，2 到 3 個案例重複才寫進 rubric → held-out 驗收
- GEPA：用軌跡與自然語言反思改寫 prompt，保留 Pareto 候選；論文不是 grader 對齊實驗 {原文}。MLflow 最少要 10 筆標註 trace {原文}
- Dropbox：GEPA 讓 relevance judge NMSE 8.83 → 4.86；風險是複製範例關鍵字過擬合、擅自改評分尺度、整份重寫風險高 {第三方}

**User 時間有限時** {我的判斷}：被動訊號（重問率、轉人工率）先對照人工標註才能信；分層標註只把難題升級專家並審計；Arena 用 Bradley-Terry；PPI 用少量隨機人工標註修正大量 judge。

## 在設計中怎麼用
- 設計 judge 時：能用 Code 的先用 Code；judge 先寫理由再打分；評審模型與被評模型盡量不同。
- Criteria drift：User 的標準會在打分過程中改變（EvalGen），rubric 要有版本並定期拿舊案例重問 {原文}
- Grader 很像 User 不會讓系統沒意義：檢查比做容易、grader 有標準答案、離線可以慢而貴 {我的判斷}

## 相關
- [[ai-evaluation]]：目標 B
- [[promotion-gate]]：rubric 規則的升級
- [[harness2]]：裁判是模型，沒有解決代表 User
- [[cuped]]：PPI 與 CUPED 的相似處
- [[error-analysis-loop]]：rubric 該檢查什麼
