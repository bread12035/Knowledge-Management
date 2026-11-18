---
id: golden-dataset-x-golden-regression-gate
title: AI 評估的 golden dataset ↔ 系統設計的 golden cases
type: bridge
summary: 同一個工具的兩種用法：AI 評估用統計比較兩版，系統設計用斷言擋住退步；都要求事先固定、只改一處、失敗回填
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/model-evals-product-evals.md#0.1, raw/ai-new-tech/paired-test-guide.md#3, raw/system-design/structured-rag-golden-eval-hexagonal-pattern.md#Why, raw/system-design/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md#可執行範例]
evidence: [討論結論, 我的判斷]
related: [golden-dataset, golden-regression-gate, paired-test, error-analysis-loop, primary-guardrail-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# AI 評估的 golden dataset ↔ 系統設計的 golden cases

> 同一個工具的兩種用法：AI 評估用統計比較兩版，系統設計用斷言擋住退步；都要求事先固定、只改一處、失敗回填

## 對照
| | AI new tech：[[golden-dataset]] | System design：[[golden-regression-gate]] |
| --- | --- | --- |
| 解決的問題 | 改 prompt 或模型後，B 是否真的比 A 好 {討論結論} | 改規則、parser、lease 時間後有沒有悄悄退步 {討論結論} |
| 機制 | 幾十到幾百題，A、B 各答，用 [[paired-test]] 檢定 {討論結論} | 少數幾條固定路徑，斷言最終狀態（如 (1,1,1)）{討論結論} |
| 判定 | 統計顯著 + 護欄 {討論結論} | 全部 PASS 才能合併 {討論結論} |
| 代價 / 限制 | 題庫要代表 User；小題庫只能測大差異 {討論結論} | 只抓已知失敗 {我的判斷} |

## 共同原理
- 事先固定，結果出來後才改就是替自己找理由。
- 一次只改一個變因，失敗才能歸因。
- 新的失敗一律回填（[[error-analysis-loop]]）：AI 那邊回填題庫，系統設計這邊加一條 golden case。
- 「回歸題不可再失敗」在 AI 評估裡是護欄之一（[[primary-guardrail-gate]]），在系統設計裡就是 CI gate。

## 差異
- 系統設計的路徑是確定性的，一條案例就夠；LLM 的輸出有隨機性，要很多題、多次執行並彙整、再做統計 {討論結論}
- 系統設計中把判斷換成 LLM（evaluator、entity extractor、SM-2 評分）時，golden cases 要從「斷言」升級成「題庫 + 統計」，並加模糊案例與人工複核 {我的判斷}
- AI 評估要切 dev 與 held-out 防止 overfitting to the test set；確定性的 golden cases 沒有這個問題 {討論結論}{我的判斷}

## 在設計中怎麼用
- 模組裡確定性的部分 → golden cases 斷言。
- LLM 判斷的部分 → golden dataset + paired test + 護欄。
- 兩者放進同一個 CI，改動前後都跑。

## 相關
- [[golden-dataset]]、[[golden-regression-gate]]：兩端的細節
- [[paired-test]]：LLM 部分的比較方法
- [[error-analysis-loop]]：失敗回填
- [[primary-guardrail-gate]]：回歸題是護欄
