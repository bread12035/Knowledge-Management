---
id: cuped
title: CUPED 與變異降低（CUPED）
type: concept
summary: 用實驗前就有、且不受新版影響的資料扣掉本來的差異，變異約縮小為 (1 − ρ²) 倍
domains: [ai-new-tech]
sources: [raw/ai-new-tech/ab-test-ai-evaluation-guide.md#2.8, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#4.14, raw/ai-new-tech/model-evals-product-evals.md#7.2]
evidence: [討論結論, 第三方, 示意, 我的判斷]
related: [paired-test, ai-evaluation, grader-alignment]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 1
next_review: 2026-11-21
---
# CUPED 與變異降低（CUPED）

> 用實驗前就有、且不受新版影響的資料扣掉本來的差異，變異約縮小為 (1 − ρ²) 倍

## 重點
- Y_adj = Y − θ(X − X̄)，θ = cov(X, Y) / var(X)，用兩組合併資料算一次；平均差不變、變異變小 {討論結論}
- 變異約縮小為 (1 − ρ²) 倍：ρ = 0.5 樣本約少 25%，ρ = 0.7 約少 49% {討論結論}
- X 必須是實驗前量到、不受新版影響的資料，否則會把真正的效果一起扣掉 {討論結論}
- 是否使用、用哪個共變量要事先決定；看完結果再選是 p-hacking {討論結論}
- Paired 設計是 θ = 1 的特例；離線同題評估不需要另外用 CUPED {討論結論}

## 細節
- 2013 年 Microsoft 的 Deng、Xu、Kohavi、Walker 提出 {第三方}
- 範例（模擬）：ρ ≈ 0.81，B − A 原始 +0.28（CI +0.01 到 +0.55），CUPED +0.30（CI +0.14 到 +0.45），變異降為 0.32 倍，約只需三分之一題數 {示意}
- 新使用者沒有歷史資料：缺值設 0 並加指示變數（Datadog 做法）{第三方}
- 判斷用的 judge 改版後，舊的 X 要用同一個 judge 重算才可比 {討論結論}
- PPI 的概念相近：PPI 用 judge 分數、CUPED 用實驗前資料，都是用便宜且相關的數字降雜訊 {討論結論}

## 在設計中怎麼用
- 什麼情況用：線上 A/B、不同使用者或不同題目、有歷史資料、指標是每位使用者的連續值或比例（特別是成本）{我的判斷}
- 不適合：離線同題評估（用 [[paired-test]]）、全新產品沒有歷史、ρ 很低。
- 先用歷史資料估 ρ，ρ 太低就不要增加複雜度。

## 相關
- [[paired-test]]：θ = 1 的特例
- [[ai-evaluation]]：在整體流程的位置
- [[grader-alignment]]：PPI 是 grader 端的類似做法
