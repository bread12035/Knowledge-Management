# Bridge 候選

只有一邊有 wiki 頁、等另一個 source 的原文進來才能建立的跨領域連結。由 dreaming 維護（`prompts/dream.md` §3）。

| 狀態 | AI new tech | System design | 可能的共同原理 | 來源 | 加入日期 |
| --- | --- | --- | --- | --- | --- |
| pending | [[ontology-knowledge-graph]]（entity resolution、新類型待人審） | [[knowledge-retrieval-design]]（SAG 不去重、alias 表由 LLM 提議人確認） | 同名不同寫法：寫入時合併 vs 查詢時展開 | raw/ai-new-tech/ontology-knowledge-graph-guide.md#4；raw/system-design/postgres-sag-alias-golden-eval-pattern.md | 2026-11-18 |
| pending | [[grader-alignment]]（judge 偏鬆偏嚴、預測效度） | [[completion-marker]]（freshness watchdog 的 evaluator 擋不值得吵人的 alert） | generator 與 evaluator 分離；evaluator 本身也要校準 | raw/ai-new-tech/model-evals-product-evals.md#6；raw/system-design/data-freshness-watchdog-scanner-marker-golden-pattern.md | 2026-11-18 |
| pending | [[agent-system-memory-layers]]（證據不足標 needs-human 並停止） | [[saga-compensation]]（補償失敗 → dead-letter + escalation） | 自動化的最後一道防線是人；停下來的條件要事先寫好 | raw/ai-new-tech/structure-of-agent-system.md#8；raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#4 | 2026-11-18 |
| pending | [[harness2]]（Propose-Probe-Compose、確認執行防 winner's curse） | [[event-driven-timer]]（Scanner reconcile 排程表、Executor 精準觸發） | reconciliation loop：定期把「計畫」對齊「現實」 | raw/ai-new-tech/agent-evaluation-harness-2-ab-test-guide.md#2.4；raw/system-design/scanner-executor-timingwheel-nooa-pattern.md | 2026-11-18 |
