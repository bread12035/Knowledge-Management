---
id: skill-state-x-event-log-current-state
title: SKILL.state 的結構化狀態 ↔ Event log 與 current state
type: bridge
summary: 兩者都在決定「保留歷史還是只保留狀態」；SKILL.state 丟掉歷史只留狀態，event log 保留歷史再算出狀態
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/hakka-agent-system-reference.md#3.4, raw/ai-new-tech/structure-of-agent-system.md#3, raw/system-design/rag-methods-comparison.md#Fact 存法]
evidence: [原文, 我的判斷, 討論結論]
related: [skill-state, event-log-current-state, agent-system-memory-layers]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 1
next_review: 2026-11-21
---
# SKILL.state 的結構化狀態 ↔ Event log 與 current state

> 兩者都在決定「保留歷史還是只保留狀態」；SKILL.state 丟掉歷史只留狀態，event log 保留歷史再算出狀態

## 對照
| | AI new tech：[[skill-state]] | System design：[[event-log-current-state]] |
| --- | --- | --- |
| 解決的問題 | agent 每步 prompt 隨歷史變長（O(T²)）{原文} | 文字型記憶每次查詢都要重讀故事推算最後狀態 {討論結論} |
| 機制 | 每步只給規格 + 結構化狀態 + 最新觀察；patch 合併，推理丟棄 {原文} | 事件只追加，current state 由 view 算出 {我的判斷} |
| 代價 / 限制 | 早期沒寫進 state 的觀察就消失；目標本身是歷史（稽核）時不適用 {原文} | 查詢要計算；量大要 materialized view {討論結論} |

## 共同原理
- 都把「現在要用的東西」做成結構化欄位，讓讀取者不必重讀全部歷史。
- 都要求狀態更新有明確語意：SKILL.state 的 patch 合併（null 才刪）、event log 的只追加。

## 差異
- SKILL.state 的失效情境「任務目標本身就是歷史（稽核、追溯）」，正好是 event log 的強項：明細可算出餘額，餘額不能還原明細 {原文}{我的判斷}
- 使用者 agent system 已經把兩者並用：state.json 給每一步（只放結論），EXEC_PLAN 的 Decision Log 與 Progress 保留帶時間戳的歷史給人與冷啟動 session（[[agent-system-memory-layers]]）{我的判斷}

## 在設計中怎麼用
- 判斷要不要保留歷史：之後會不會被問「某時間點是什麼」或「為什麼變成這樣」？會 → event log；只關心下一步 → structured state。
- 兩者可疊加：event log 當 source of truth，structured state 是給 agent 看的 view。

## 相關
- [[skill-state]]、[[event-log-current-state]]：兩端的細節
- [[agent-system-memory-layers]]：EXEC_PLAN 與 state.json 的分工
