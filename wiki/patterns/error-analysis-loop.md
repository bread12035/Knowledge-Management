---
id: error-analysis-loop
title: Error analysis 回饋迴圈（Error analysis loop）
type: pattern
summary: 讀真實失敗、分類計數，再把失敗類型寫成測試並回填題庫、回歸集與 judge rubric
domains: [ai-new-tech]
sources: [raw/ai-new-tech/model-evals-product-evals.md#10, raw/ai-new-tech/structure-of-agent-system.md#4, raw/ai-new-tech/paired-test-guide.md#3]
evidence: [討論結論, 使用者決定, 我的判斷]
related: [ai-evaluation, golden-dataset, grader-alignment, primary-guardrail-gate, promotion-gate, agent-system-memory-layers]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Error analysis 回饋迴圈（Error analysis loop）

> 讀真實失敗、分類計數，再把失敗類型寫成測試並回填題庫、回歸集與 judge rubric

## 重點
- Error analysis 是「讀真實失敗，再決定要測什麼」，是方法論不是統計檢定 {討論結論}
- 流程：約 100 筆 trace → open coding（每筆一句自由筆記，不先設檢查表）→ axial coding 成 failure taxonomy → 計數排序 → 重複到 saturation → 寫成 evals {討論結論}
- 能用 Code 判斷的失敗寫成 Code 測試，主觀的寫成 LLM judge {討論結論}
- 輸出餵給題庫、回歸測試集、judge rubric；護欄沒過時對該子群做一次 {我的判斷}
- 與使用者 agent system 一致：修好的失敗至少一個 eval 進回歸集；同類失敗第二次寫進 docs；證據模糊交人 {使用者決定}

## 在設計中怎麼用
- 什麼情況用：上線前第一次建評估、護欄沒過、線上指標退步、paired test 的 b 格（A 對 B 錯）有案例。
- 怎麼用：
  1. 抽有代表性的 trace，不是只看最糟的。
  2. 先自由描述，再歸類；類別從資料長出來。
  3. 依頻率 × 嚴重度排序修。
  4. 每個類別至少一個測試案例；修好的進回歸集，永久保留。
- 代價：要人讀；約 100 筆起。

## 相關
- [[ai-evaluation]]：貫穿整個評估流程
- [[golden-dataset]]：回填題庫
- [[grader-alignment]]：回填 rubric
- [[primary-guardrail-gate]]：回歸題是護欄
- [[promotion-gate]]：同類第二次才升級
- [[agent-system-memory-layers]]：失敗記憶層
