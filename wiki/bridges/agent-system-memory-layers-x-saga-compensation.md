---
id: agent-system-memory-layers-x-saga-compensation
title: Agent 的 needs-human 停止 ↔ Saga 的 dead-letter 與 escalation
type: bridge
summary: 兩邊都承認自動化會走到盡頭；事先寫好停止條件，停下時留下完整狀態，再交給人
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/structure-of-agent-system.md#2, raw/ai-new-tech/structure-of-agent-system.md#4, raw/ai-new-tech/structure-of-agent-system.md#8, raw/ai-new-tech/structure-of-agent-system.md#9, raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#3, raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#4]
evidence: [使用者決定, 原文, 討論結論, 我的判斷]
related: [agent-system-memory-layers, saga-compensation, promotion-gate, event-driven-timer]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# Agent 的 needs-human 停止 ↔ Saga 的 dead-letter 與 escalation

> 兩邊都承認自動化會走到盡頭；事先寫好停止條件，停下時留下完整狀態，再交給人

## 對照
| | AI new tech：[[agent-system-memory-layers]] | System design：[[saga-compensation]] |
| --- | --- | --- |
| 解決的問題 | 證據不足或不適合自動處理時，agent 繼續做會產生錯的結果或錯的升級 {原文} | 重試與補償都失敗時，流程卡在不一致的中間狀態 {討論結論} |
| 機制 | 標記 needs-human，在 EXEC_PLAN 的 open 項目與 RESULTS 寫明缺什麼證據，然後停止；證據模糊的項目不自動升級 {原文}{使用者決定} | 冪等重試 → 用盡就反向補償 → 補償失敗進 dead-letter，並 page 值班 {討論結論} |
| 代價 / 限制 | 需要人有空回應；停下的任務會累積 {我的判斷} | 值班負擔；未在時限內 ack 要再升級 {討論結論} |

## 共同原理
- 自動化的最後一道防線是人；問題不是「要不要交人」，而是「何時停、停下時留下什麼」{討論結論}{我的判斷}
- 停止條件要事先寫進規則或流程定義（CLAUDE.md 的規則、實作檢查清單；Saga 的每一步重試上限與補償），不在當下臨時判斷 {原文}{討論結論}
- 停下前把狀態持久化：EXEC_PLAN 寫明缺什麼；Saga 狀態存資料庫、事件進 dead-letter。人接手時不必重建脈絡 {原文}{討論結論}
- 停下比硬做安全：錯的升級會擴散到長期知識；錯的補償會擴散到下游服務 {我的判斷}

## 差異
- Agent 停在「判斷不確定」（證據品質）；Saga 停在「動作失敗」（重試與補償用盡）{我的判斷}
- Agent 的交人是非同步的待辦（人之後讀 RESULTS 或 next.md 的反問）；Saga 的交人有時限，未 ack 由 [[event-driven-timer]] 觸發下一層 escalation {討論結論}

## 在設計中怎麼用
設計任何自動流程時，寫下三件事：
- 停止條件：重試幾次、信心或證據低於什麼程度就停。
- 停下時寫到哪裡：哪個檔案或資料表，包含缺什麼、做到哪一步。
- 誰收、多久沒回應要升級。

這個 repo 也照這個做：raw 處理失敗用 `km.py fail` 記錄連續失敗次數，CONFLICT 與 OPTIONAL 列在 log 的「待使用者處理」，不替使用者決定。

## 相關
- [[agent-system-memory-layers]]、[[saga-compensation]]：兩端的細節
- [[promotion-gate]]：證據模糊不升級，是同一個停止規則
- [[event-driven-timer]]：escalation 的計時
