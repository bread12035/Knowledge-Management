---
id: harness2
title: Harness²（遞迴改善 agent harness）
type: concept
summary: 不改模型、不需標準答案，針對單一任務 Propose-Probe-Compose 改善 harness，並把有效的原因存進 library
domains: [ai-new-tech]
sources: [raw/ai-new-tech/agent-evaluation-harness-2-ab-test-guide.md#2, raw/ai-new-tech/agent-evaluation-harness-2-ab-test-guide.md#4, raw/ai-new-tech/agent-evaluation-harness-2-ab-test-guide.md#6, raw/ai-new-tech/agent-evaluation-harness-2-ab-test-guide.md#7]
evidence: [原文, 第三方, 我的判斷]
related: [ai-evaluation, paired-test, promotion-gate, dreaming, agent-harness-design, grader-alignment]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Harness²（遞迴改善 agent harness）

> 不改模型、不需標準答案，針對單一任務 Propose-Probe-Compose 改善 harness，並把有效的原因存進 library

## 重點
- 第一層（任務層）：用原 harness 跑參考執行 → Propose 一個通用、一個領域候選 → Probe 在同一任務比對行為 → Compose 只合併有行為證據的修改 {原文}
- 第二層（跨任務）：library 只存「為什麼有效」並選擇性重用；每個任務仍從基礎 harness 出發，避免客製 harness 帶入雜訊 {原文}
- 可改八個元件：system prompt、guardrails、memory、tool guidance、subagents、skills、scripts、plugins {原文}
- 它找出「這個任務該怎麼改」；paired test 證明「改動平均有沒有效」，兩者串接 {我的判斷}
- 裁判是模型，不是 User；比較能引導決定，但不能證明輸出是對的 {第三方}{我的判斷}

## 細節
- arXiv:2610.14224（Northwestern + Google Cloud AI Research），作者自報最多 +11.5（WorkBuddy-Bench）、+4.5（JobBench）、+11.8 個百分點（LAB）{原文}
- 實驗 editor 是 Claude Opus 4.8，弱模型的進步可能部分來自強 editor {第三方}
- 一個任務 k = 1 就要 4 次 executor 與 3 次 improver；真實 HR 任務約 22 美元；程式沒有花費上限 {第三方}
- executor 網路不受限、Codex sandbox 關閉，評估前要限制網路 {原文}
- Harness 內的 guardrails 是規則；評估的 guardrail metrics 是指標，同名不同義 {討論結論}

## 在設計中怎麼用
| 情境 | 建議 |
| --- | --- |
| 任務固定重複、能建題庫 | 用 [[paired-test]] |
| 任務每次不同、沒有答案 | 用 Harness² 產生候選 |
| 要做上線決策 | Harness² 產生候選 → 驗收題庫 paired test 加護欄 |
| 有副作用（寫 DB、寄信、下單） | 避免，Probe 會重跑 |
| 高風險（法律、財務） | 結果一定要經 paired test 驗收 |

- 加入 A/B 概念 {我的判斷}：便宜的程式檢查當行為證據（引用必須出現在原文）；參考版本重跑量雜訊；比較候選減參考；合成後用新 seed 確認以防 winner's curse。
- Library 的教訓要過 [[promotion-gate]]：2 到 3 個任務重複才升級。

## 相關
- [[ai-evaluation]]：評估方法總覽
- [[paired-test]]：驗收用的統計方法
- [[promotion-gate]]：library 教訓的升級閘門
- [[dreaming]]：同樣是事後回顧並存下有效的東西
- [[grader-alignment]]：Harness² 沒有解決代表 User 的問題
- [[agent-harness-design]]：被改善的對象
