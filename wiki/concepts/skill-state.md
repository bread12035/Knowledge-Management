---
id: skill-state
title: SKILL.state（結構化狀態取代歷史）
type: concept
summary: 每步只給程序規格、結構化狀態與最新觀察，推理用完即丟，prompt 大小固定
domains: [ai-new-tech]
sources: [raw/ai-new-tech/hakka-agent-system-reference.md#3.4, raw/ai-new-tech/structure-of-agent-system.md#5.3]
evidence: [原文, 我的判斷, 討論結論]
related: [agent-harness-design, pass-by-reference, single-writer, agent-system-memory-layers]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# SKILL.state（結構化狀態取代歷史）

> 每步只給程序規格、結構化狀態與最新觀察，推理用完即丟，prompt 大小固定

## 重點
- 第 t 步只收到不變的程序規格 P、結構化狀態 Σt、最新觀察 Ot；模型輸出推理、state patch、動作，runtime 驗證後合併 {原文}
- Prompt 大小 O(1)、累積 token O(T)；一般歷史累加是 O(T²) {原文}
- 關鍵是「結構化」不是「縮短」：預算匹配下滑動視窗 0.18、摘要 0.52、LLMLingua 0.22、結構化 state 0.94 {原文}
- Schema 每個 domain 寫一次，不是每個任務一次 {原文}
- 只評測 single-agent；用在 subagent 或 multi-agent 是延伸，並行寫入衝突未測 {討論結論}

## 細節
- Warehouse T=100：65,408 token 對 1,062,387 token（16.2 倍）；T=200 準確率 0.94 對摘要式 0.84 {原文}
- InterCode CTF pass@1 54.2%（ReAct 43.2%），總 token −60.4%；100 題共用 5 欄位 schema {原文}
- 小模型失敗 68% 是誤刪既有 key → patch 用合併語意（null 才刪），runtime 驗證失敗就 rollback 重試 {原文}
- 失效情境：事先不知道 schema；早期觀察當時沒被認為重要；任務目標本身是歷史（稽核、追溯）{原文}

## 在設計中怎麼用
- 什麼情況用：多步驟任務、要交接給 subagent、歷史會一直變長的流程。
- 怎麼用：state.json 放目標、已確定決策、資料 handle、未解問題、完成條件；不放推理過程、完整 log、已被取代的假設 {我的判斷}
  ```json
  {"goal": "...", "decided": ["..."], "refs": {"log": "evidence/T-17/run3.txt"}, "open": ["..."], "done_when": "..."}
  ```
- 交接給 subagent：傳 state 路徑與 handle，不貼歷史；回報用結構化欄位（status、patch、refs、open）。
- 多個 subagent 各寫自己的 patch 檔，由主 agent 合併（[[single-writer]]）{我的判斷}
- 代價：schema 設計失誤會遺失資訊；完整敘述另留在 EXEC_PLAN。

## 相關
- [[agent-harness-design]]：三個省 token 機制之一
- [[pass-by-reference]]：refs 欄位放 handle
- [[single-writer]]：多 agent 寫 state 的衝突處理
- [[agent-system-memory-layers]]：EXEC_PLAN 與 state.json 的分工
