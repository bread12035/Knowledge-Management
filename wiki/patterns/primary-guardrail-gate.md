---
id: primary-guardrail-gate
title: 主指標加護欄的決策閘門（Primary metric + guardrails）
type: pattern
summary: 一個主指標下結論，加幾個事先定好門檻的「不能變差」指標；任何一個沒過就不採用
domains: [ai-new-tech]
sources: [raw/ai-new-tech/model-evals-product-evals.md#8, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#2.7, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#4.3, raw/ai-new-tech/paired-test-guide.md#3]
evidence: [討論結論, 我的判斷, 示意]
related: [ai-evaluation, paired-test, golden-dataset, error-analysis-loop]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 主指標加護欄的決策閘門（Primary metric + guardrails）

> 一個主指標下結論，加幾個事先定好門檻的「不能變差」指標；任何一個沒過就不採用

## 重點
- 主指標只選一個；看 20 個指標平均有 1 個會因運氣顯著 {討論結論}
- 只看主指標會被騙：AI 常用「變長、變貴、變慢」換取品質 {討論結論}
- 護欄用「不能超過的門檻」，因為樣本少時小的變差測不出顯著；門檻要事先定 {討論結論}
- 「沒有變差」正式的檢查是 non-inferiority：差異 CI 下界 > −margin 才通過 {討論結論}
- 決策規則事先寫好、測試中不改：主指標 CI 下界 > 0（或 > MDE）且所有護欄通過才採用 {我的判斷}

## 細節
| 護欄類型 | 規則 |
| --- | --- |
| 子群底線 | 每個子群不可比舊版差超過 margin |
| 成本與延遲 | 不超過預算（token 成本、P95 延遲） |
| 安全 | 次數必須為 0（跨領域洩漏、Red Team 全過） |
| 過度拒答 | 正常問題的拒答率不可大幅上升 |
| 回歸題 | 已修好的失敗不可再出現 |

- 子群非劣性很難證明：ψ = 15%、margin 3 點約需 1030 題，5 點約 371 題 {討論結論}。範例 40 題子群差 −7.5%、CI −22% 到 +7%，不能證明沒變差 {示意}
- Rule of three：n 次 0 失敗，95% 失敗率上界約 3/n；300 題 0 洩漏上界約 1%。零容忍的安全要靠系統層權限強制 {討論結論}
- 線上 A/B 的護欄可以設嚴重惡化的停損線，但停損只止血，不宣布勝利 {討論結論}
- 護欄太多會增加誤報，只放最重要的幾個，必要時 Bonferroni {討論結論}

## 在設計中怎麼用
- 什麼情況用：任何「要不要採用新版本」的決策（prompt、模型、workflow、架構）。
- 怎麼用：事先寫 1 個主指標 + 3 到 5 個護欄與門檻 → 跑 → 主指標過才看護欄 → 任一護欄沒過就不採用，對該子群做 [[error-analysis-loop]]。
- 代價：小子群難證明沒變差；可放寬 margin、合併相近子群、或用點估計規則加人工檢查 {我的判斷}
- 同樣的結構適用於軟體發布：功能指標 + 錯誤率、延遲、成本的門檻 {我的判斷}

## 相關
- [[ai-evaluation]]：決策在整體流程的位置
- [[paired-test]]：主指標的檢定
- [[golden-dataset]]：Red Team 與回歸題
- [[error-analysis-loop]]：護欄沒過之後
