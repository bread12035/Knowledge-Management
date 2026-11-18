---
id: golden-dataset
title: Golden dataset 與題庫代表性（Golden dataset）
type: concept
summary: 固定題庫要代表 User 的需求：分 dev 與 held-out、對照題目分布、補尾部風險、持續回填失敗
domains: [ai-new-tech]
sources: [raw/ai-new-tech/model-evals-product-evals.md#0.1, raw/ai-new-tech/model-evals-product-evals.md#5, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#2.6, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#4.10]
evidence: [討論結論, 我的判斷, 示意, 第三方]
related: [ai-evaluation, paired-test, error-analysis-loop, primary-guardrail-gate, golden-dataset-x-golden-regression-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Golden dataset 與題庫代表性（Golden dataset）

> 固定題庫要代表 User 的需求：分 dev 與 held-out、對照題目分布、補尾部風險、持續回填失敗

## 重點
- 題庫分 dev 集（調 prompt 用）與 held-out 集（只在決定是否採用時用）；同一批題既調又驗會 overfitting to the test set {討論結論}
- 代表 User 看四件事：比例、內容、難度、邊界 {我的判斷}
- 從真實紀錄挑題並去識別化，涵蓋常見、困難、不該回答；起步 50 到 200 題，品質比數量重要 {討論結論}
- 代表性只能檢查不能證明：冷啟動只有舊系統處理過的問題（survivorship bias）{討論結論}
- 固定版本，不隨便改舊題；新的失敗案例加一題 {討論結論}

## 細節
**題目分布對照** {討論結論}：定分層欄位（領域 × 任務 × 難度）→ 算流量比例與題庫比例 → TVD = 0.5 × Σ|p − q| → 補題或加權（權重 = 流量比例 ÷ 題庫比例）→ 報每層與加權總分。

範例：題庫平均新版 86.5% 看似進步，依流量加權卻從 79.5% 退步到 77.7%（TVD = 0.20）{示意}。小層（20 題，Wilson CI 34% 到 74%）加權會放大雜訊，只靠加權不夠要補題 {我的判斷}

**難度** {我的判斷}：用舊版跑 k 次的通過率分帶；全是易題會飽和；分開報易中難。

**Red Team** {我的判斷}：另成一套必須全過的集合，不和平均分混；跨領域資安用「角色 × 資料領域」矩陣與 canary 字串，洩漏率要求為零；權限在系統層強制。

**模擬使用者**：只能補缺口，必須用真實紀錄驗證分布 {我的判斷}

## 在設計中怎麼用
- 建題庫時就切 dev / held-out，並記下每層在真實流量的比例。
- 每季把題目分布和真實流量重新對照一次 {我的判斷}
- 新失敗由 [[error-analysis-loop]] 回填；已修好的進回歸題（護欄之一）。

## 相關
- [[ai-evaluation]]：目標 A
- [[paired-test]]：題庫上的比較方法
- [[error-analysis-loop]]：題庫缺什麼的來源
- [[primary-guardrail-gate]]：Red Team 與回歸題是護欄
- [[golden-dataset-x-golden-regression-gate]]：跨領域：統計比較與斷言回歸是同一工具的兩種用法
