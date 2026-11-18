---
id: agent-system-memory-layers
title: 使用者 agent system 的五層記憶與升級規則
type: decision
summary: 依壽命分任務記憶、任務結果、長期知識、失敗記憶、證據五層，並用四條規則把下層內容往上升
domains: [ai-new-tech]
sources: [raw/ai-new-tech/structure-of-agent-system.md#3, raw/ai-new-tech/structure-of-agent-system.md#4, raw/ai-new-tech/anthropic-agent-memory-guide.md#14]
evidence: [使用者決定, 原文, 我的判斷]
related: [agent-harness-design, agent-memory, promotion-gate, error-analysis-loop, skill-state, agent-system-memory-layers-x-saga-compensation]
status: active
created: 2026-11-18
last_dreamed: 2026-11-19
review_count: 1
next_review: 2026-11-22
---
# 使用者 agent system 的五層記憶與升級規則

> 依壽命分任務記憶、任務結果、長期知識、失敗記憶、證據五層，並用四條規則把下層內容往上升

## 重點
- 系統不依賴對話記憶；每個 session 從乾淨 context 開始，需要的內容從檔案或資料表讀回 {我的判斷}
- EXEC_PLAN 是單一任務的工作記憶，自成一體、每個停點更新，新 session 只靠它就能接續 {原文}
- 失敗記憶只增不減：修好的問題變成永久的 regression 案例 {使用者決定}
- 四條升級規則（見下表）把會影響未來的內容往上搬 {使用者決定}
- 重要內容放在自己的檔案，Claude Code 內建記憶只當輔助，避免同一份知識存兩處而分叉 {我的判斷}

## 細節
| 層 | 載體 | 保存什麼 | 壽命 |
| --- | --- | --- | --- |
| 任務記憶 | tasks/<ID>/EXEC_PLAN.md、state.json | 進度、發現、決策與理由、當下狀態 | 任務期間 |
| 任務結果 | RESULTS.md、PR | 前後 eval 分數、regression、疑點 | 永久 |
| 長期知識 | docs/、.claude/skills/ | 架構、ADR、操作手冊 | 永久，定期檢查 |
| 失敗記憶 | evals/、docs/failures/ | 出過的錯與測試案例 | 永久，只增不減 |
| 證據 | evidence/、唯讀 DB | trace、來源檔、原始輸出 | 依資料政策，agent 不可改 |

**升級規則：**
1. 會影響未來任務的決策 → docs/decisions/ 的 ADR
2. 任何被修好的失敗 → 至少一個 eval 案例進 regression suite
3. 同一類失敗出現第二次 → docs/failures/ 說明 + CLAUDE.md 一行指標
4. 證據模糊的項目 → 不自動升級，交人判斷

**與 Anthropic 四層的對照：** Transcripts ↔ evidence/、tasks/；Memory notes ↔ EXEC_PLAN 的 Progress；Wiki ↔ knowledge/l2 與 index.md；Injected context ↔ CLAUDE.md；Dreaming ↔ Preprocess {我的判斷}。差別是五層依「壽命與用途」切，四層依「讀取頻率」切。

**EXEC_PLAN 必備章節：** Purpose、Progress（帶時間戳）、Surprises & Discoveries、Decision Log、Acceptance（可執行驗收指令）、Outcomes & Retrospective {原文}

## 在設計中怎麼用
- 設計新 agent 時，先為每一種資訊決定放哪一層、誰寫、何時寫。
- 結案時跑一次升級規則檢查；規則 3 與 4 就是 [[promotion-gate]]。
- EXEC_PLAN 給人與冷啟動 session 讀；state.json 給每一步與 subagent 讀，只放結論（[[skill-state]]）{我的判斷}

## 相關
- [[agent-harness-design]]：這套記憶所在的整體架構
- [[agent-memory]]：Anthropic 的四層模型
- [[promotion-gate]]：升級規則的通用形式
- [[error-analysis-loop]]：失敗記憶的來源
- [[agent-system-memory-layers-x-saga-compensation]]：跨領域：needs-human 停止與 Saga 的 dead-letter 交人
