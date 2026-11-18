# Dreaming Log

每次 dreaming 執行一筆，新的在上。格式見 `prompts/dream.md` §7。

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

