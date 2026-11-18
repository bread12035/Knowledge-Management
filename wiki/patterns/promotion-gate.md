---
id: promotion-gate
title: 升級閘門：先 pending，重複出現才升級（Promotion gate）
type: pattern
summary: 新教訓、規則、決策先放待定區，在多個案例重複出現且有證據才升到長期或常駐層
domains: [ai-new-tech]
sources: [raw/ai-new-tech/structure-of-agent-system.md#4, raw/ai-new-tech/agent-evaluation-harness-2-ab-test-guide.md#7.7, raw/ai-new-tech/model-evals-product-evals.md#6.5, raw/ai-new-tech/anthropic-agent-memory-guide.md#5]
evidence: [使用者決定, 我的判斷, 原文, 第三方]
related: [agent-system-memory-layers, harness2, grader-alignment, injected-context, error-analysis-loop]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 升級閘門：先 pending，重複出現才升級（Promotion gate）

> 新教訓、規則、決策先放待定區，在多個案例重複出現且有證據才升到長期或常駐層

## 重點
- 使用者 agent system 的升級規則：同一類失敗出現第二次，才在 docs/failures/ 寫說明並在 CLAUDE.md 加指標；證據模糊不自動升級，交人判斷 {使用者決定}
- Harness² 的教訓只來自一個任務，「被執行對比支持」不等於統計驗證；一次運氣好的結果被存成經驗，會影響所有任務 {我的判斷}
- 因此教訓先 pending，在 2 到 3 個不同任務重複出現才升級，升級前用 paired test 加護欄驗收 {我的判斷}
- 修 grader 時，User 的理由也先 pending，2 到 3 個案例重複出現才寫進 rubric {我的判斷}
- 越上層影響越廣：常駐層的錯誤會擴散到所有 session，所以越往上門檻越高 {原文}

## 細節
| 場景 | 待定區 | 升級條件 | 升級去處 |
| --- | --- | --- | --- |
| Agent system 失敗 | EXEC_PLAN / RESULTS | 同類第二次 | docs/failures/ + CLAUDE.md 指標 |
| Harness² 教訓 | pending | 2 到 3 個任務重複 + paired test 驗收 | library |
| Grader 規則 | pending 理由 | 2 到 3 個案例重複 | rubric |
| 這個 repo | note、wiki | 關鍵且穩定 | PRIMER.md（deep 模式才更新） |

## 在設計中怎麼用
- 什麼情況用：系統會從單次經驗自動產生規則或記憶，且這些規則會影響之後所有執行。
- 怎麼用：定義待定區、升級條件（重複次數 + 證據）、升級去處、與交人的條件。
- 寫成通用說法再升級，不抄案例中的專有名詞，避免過擬合（Dropbox 的 GEPA 經驗）{第三方}
- 模型換版後，已升級的內容要定期 lint，舊教訓可能過期 {我的判斷}
- 代價：升級變慢；只出現一次但很重要的教訓可能被延後。

## 相關
- [[agent-system-memory-layers]]：升級規則 1 到 4
- [[harness2]]：library 的教訓升級
- [[grader-alignment]]：rubric 規則的升級
- [[injected-context]]：最上層、門檻最高
- [[error-analysis-loop]]：失敗分類後決定升級什麼
