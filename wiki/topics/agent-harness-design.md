---
id: agent-harness-design
title: Agent harness 設計：檔案結構與省 token（Agent harness design）
type: topic
summary: 使用者以檔案為中心的 agent system：入口地圖、EXEC_PLAN、五層記憶、三個省 token 機制、scale-out 與 Preprocess
domains: [ai-new-tech]
sources: [raw/ai-new-tech/structure-of-agent-system.md#1, raw/ai-new-tech/hakka-agent-system-reference.md#3.2, raw/ai-new-tech/hakka-agent-system-reference.md#6]
evidence: [使用者決定, 原文, 討論結論, 我的判斷]
related: [progressive-disclosure, agent-system-memory-layers, pass-by-reference, skill-state, single-writer, llm-wiki, harness2]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Agent harness 設計：檔案結構與省 token（Agent harness design）

> 使用者以檔案為中心的 agent system：入口地圖、EXEC_PLAN、五層記憶、三個省 token 機制、scale-out 與 Preprocess

## 重點
- Harness 是包在模型外的程式層：組 prompt、跑迴圈、執行動作、管理狀態；同一模型換 harness，成績與成本可差很多 {討論結論}
- 七個決策：入口地圖、EXEC_PLAN、記憶分層、不用 worktree、省 token、SQLite 到 MCP、Preprocess {使用者決定}
- 三個省 token 機制各管一種成本、可疊加：[[pass-by-reference]]（資料）、caveman（輸出文字）、[[skill-state]]（狀態傳遞）{使用者決定}
- 預設在主對話多輪完成；只有大量輸出隔離、需限制工具、自足且有 I/O 契約、獨立可並行才派 subagent {討論結論}
- 是否採用省 token 手法，以美元 cost model 實測為準，不憑 token 數字 {討論結論}

## 細節
**subagent 決策流程** {原文}：需要之前對話 → 主對話或 fork；產出大且不再引用 → subagent；子任務獨立可並行 → 多個 subagent；否則主對話多輪。subagent 要重新載入 system prompt、CLAUDE.md、git status、skills，回傳還佔主 context。

**Caveman**：output token 平均 −65%（範圍 22% 到 87%），但規則每輪佔 1 到 1.5k input token，短任務可能虧；output style 版不影響 subagent。只用在主對話敘述，EXEC_PLAN、RESULTS、docs 寫完整句子 {原文}{我的判斷}

**Persistent subagent 三種**：resume（保留完整歷史，可讀回暖 cache，但又回到 O(T²)）、`memory` 欄位（知識持久，不是 process 持久）、fork（重用主 session cache，繼承全部 context）{原文}

**Scale-out**：S1 sandbox SQLite → S2 共用 .db 經 MCP 唯讀 → S3 外部 DB；換層只改後端不改流程；文字記憶永遠留在檔案 {使用者決定}

**不用 worktree**：任務隔離靠 tasks/<ID>/、sandbox/<ID>/、唯讀 evidence/；改同一份程式碼的任務要排隊 {使用者決定}

**Preprocess**：任務之外的整理階段，對應 [[llm-wiki]]；L0 不可變、L1 可由 L0 重跑、L2 可由 L1 重算；L0 hash 變就重跑；只寫 knowledge/ 與 next.md {使用者決定}

**Hakka vibe**：實驗每個只動一個變因，每 arm 跑 3 次；baseline 少於 8 輪視為太簡單；成本換算美元，cache write 分 1h 與 5m 單價 {原文}

## 在設計中怎麼用
- 新專案的骨架：先建入口地圖（[[progressive-disclosure]]）、任務目錄與 EXEC_PLAN、五層記憶（[[agent-system-memory-layers]]）。
- 每個路徑寫明誰寫（[[single-writer]]）。
- 待決問題：多 agent 並行寫同一份 state、caveman 對 subagent 的實際影響、cache 過期後 resume 的成本、SQLite 換外部 DB 的門檻、Preprocess 產出的 next.md 品質 {使用者決定}

## 相關
- [[progressive-disclosure]]：CLAUDE.md 入口地圖
- [[agent-system-memory-layers]]：五層記憶與升級規則
- [[pass-by-reference]]、[[skill-state]]：省 token 機制
- [[single-writer]]：路徑擁有者
- [[llm-wiki]]：Preprocess 的概念來源
- [[harness2]]：自動改善 harness 的方法
