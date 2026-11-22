# Dreaming Log

每次 dreaming 執行一筆，新的在上。格式見 `prompts/dream.md` §7。

## 2026-11-22 weekly
- raw：預期 2，處理 2，失敗 0，留待下次 0
- notes：新增 seat-hold-cas-timingwheel-outbox-ticketing-pattern、flash-sale-scheduled-release-pointer-saga-rollback-pattern；更新 無
- wiki：新增 seat-hold；更新 single-source-of-truth、saga-compensation、event-driven-timer、pessimistic-lock、reliable-event-processing、optimistic-concurrency-x-pessimistic-lock、golden-regression-gate（實質修改，review_count 歸 0）、lease-reaper（只加連結）；合併/取代 無
- bridges：新增 無（seat-hold 的觀察併入 optimistic-concurrency-x-pessimistic-lock：D3 軟性認領缺到期時間）；候選 4 筆（新增 0；pending 1 不變）
- revisit：agent-system-memory-layers-x-saga-compensation、event-log-current-state、gateway-authn-service-authz、grader-alignment、harness2、hybrid-search-rrf、idempotent-consumer、injected-context、km-dreaming-design、knowledge-retrieval-design、lease-reaper、llm-wiki、memory-salience、ontology-knowledge-graph、ontology-knowledge-graph-x-knowledge-retrieval-design、optimistic-concurrency、paired-test、pass-by-reference、postgres-hub（19 頁核對無誤，review_count +1，next_review 2026-11-29）；golden-regression-gate 改為實質修改
- 留待下次：6 天內到期 43 頁，本次處理 20，剩 23 頁
- PRIMER：更新日期，加 seat-hold 與 single-source-of-truth 兩條原則（1,648 字元）
- 週報：review/2026-W47.md（覆蓋種子版本，涵蓋整週）
- lint：0 errors，0 warnings；wiki/raw 0.31
- 待使用者處理：D3 的鎖選擇與軟性認領缺到期時間；earnings 與 SSOT 的待確認事實（新增：service 怎麼得知 pointer 變更）

## 2026-11-19 daily
- raw：預期 0，處理 0，失敗 0，留待下次 0
- notes：新增 無；更新 無
- wiki：新增 無；更新 agent-memory（「並行寫入保護」一條的證據標記修正：single-writer 是 {我的判斷} 不是 {原文}；補來源 #10）；合併/取代 無
- bridges：新增 無；候選 4 筆（新增 0；pending 1：grader-alignment ↔ watchdog evaluator，SD 側仍缺獨立頁）
- revisit：agent-harness-design、agent-memory、agent-system-memory-layers、ai-evaluation、completion-marker、deterministic-over-llm、earnings-gcp-onprem-handover、error-analysis-loop（7 頁核對無誤 → review_count 1、next_review 2026-11-22；agent-memory 修正後歸 0、next_review 2026-11-20）
- 留待下次：今天到期 41 頁，處理 8，剩 33 頁到期未複習（daily 上限 8）
- lint：0 errors，0 warnings；wiki/raw 0.31
- 待使用者處理：沿用：D3 是否改為單一寫入者（review/2026-W47.md）；earnings 與 SSOT 的待確認事實；複習排程是否改用 SM-2。另：種子執行讓 47 頁同日到期，daily 上限 8 頁需約 5 天才消化，可考慮在 trigger 加 `mode: deep` 跑一次

## 2026-11-18 daily
- raw：預期 0，處理 0，失敗 0，留待下次 0
- notes：新增 無；更新 無
- wiki：新增 ontology-knowledge-graph-x-knowledge-retrieval-design、agent-system-memory-layers-x-saga-compensation；更新 ontology-knowledge-graph、knowledge-retrieval-design、agent-system-memory-layers、saga-compensation（相關加 bridge 連結）、dreaming-x-web-content-acquisition（補來源 web-fetch…#8）；合併/取代 無
- bridges：新增 ontology-knowledge-graph-x-knowledge-retrieval-design、agent-system-memory-layers-x-saga-compensation；候選 4 筆（新增 0；done 2、rejected 1：harness2 ↔ event-driven-timer 共同原理不成立、pending 1：grader-alignment ↔ watchdog evaluator，SD 側缺獨立頁）
- revisit：dreaming-x-web-content-acquisition、golden-dataset-x-golden-regression-gate、llm-wiki-x-knowledge-retrieval-design、optimistic-concurrency-x-pessimistic-lock、skill-state-x-event-log-current-state、cuped、dreaming、golden-dataset（逐條對 raw 核對無誤，review_count → 1，next_review 2026-11-21）
- lint：0 errors，0 warnings；wiki/raw 0.30
- 待使用者處理：沿用上次：D3 是否改為單一寫入者（review/2026-W47.md）；earnings 與 SSOT 的待確認事實；複習排程是否改用 SM-2

## 2026-11-18 deep（種子執行，手動）
- raw：預期 29（ai-new-tech 8、system-design 21），處理 29，失敗 0，留待下次 0
- 上限：這次是初始種子執行，未套用每次 ingest 5 份、新建 15 頁的上限；之後的排程照 `prompts/dream.md` 執行
- notes：新增 29 份（system-design 由 5 個 subagent 平行抽取，只傳路徑）
- wiki：新增 47 頁（6 topic、12 concept、20 pattern、4 decision、5 bridge）
- bridges：新增 optimistic-concurrency-x-pessimistic-lock、skill-state-x-event-log-current-state、llm-wiki-x-knowledge-retrieval-design、golden-dataset-x-golden-regression-gate、dreaming-x-web-content-acquisition；候選 4 筆（新增 4）
- revisit：single-writer、pass-by-reference、promotion-gate、postgres-hub 補上另一個 source 的來源，改為兩個 domain
- lint：0 errors，0 warnings；wiki/raw 0.29
- 工具：`km.py` lint 改為忽略 code 區段內的 `[[...]]`
- 待使用者處理：D3 是否改為單一寫入者（見 review/2026-W47.md）；earnings 與 SSOT 的待確認事實；複習排程是否改用 SM-2

