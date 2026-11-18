---
id: golden-regression-gate
title: Golden cases 當回歸關卡（Golden regression gate）
type: pattern
summary: 把正常與失敗路徑固定成可執行的 golden cases，改規則、prompt、schema 前先跑，結果變了就擋下
domains: [system-design]
sources: [raw/system-design/structured-rag-golden-eval-hexagonal-pattern.md#Why, raw/system-design/transactional-outbox-lease-reaper-idempotent-consumer-pattern.md#為什麼採用這些技術, raw/system-design/data-freshness-watchdog-scanner-marker-golden-pattern.md#可執行範例, raw/system-design/postgres-sag-alias-golden-eval-pattern.md#為什麼採用這些技術, raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md#7]
evidence: [討論結論, 我的判斷]
related: [reliable-event-processing, knowledge-retrieval-design, worker-monitor-split, completion-marker, golden-dataset-x-golden-regression-gate]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Golden cases 當回歸關卡（Golden regression gate）

> 把正常與失敗路徑固定成可執行的 golden cases，改規則、prompt、schema 前先跑，結果變了就擋下

## 重點
- Pipeline 上線後會持續調整；沒有固定 golden dataset，每次修改都憑感覺；golden dataset 把「有沒有變差」變成可在 CI 跑的 gate {討論結論}
- 每份系統設計討論都附了 golden cases：outbox 三條（normal、producer crash、worker crash 重試）、Saga 三條（全成功、中途失敗、補償失敗）、freshness watchdog 三條、SAG alias 四條 {討論結論}
- 把「已知會出錯的情況」固定下來（例如沒有 alias 會漏資料），改規則才不會悄悄退步 {討論結論}
- 出處是 Golden Master / Approval Testing；搬進 LLM pipeline 後就是「問題 → 正確答案」的 eval harness（OpenAI Evals、promptfoo）{討論結論}
- 核心邏輯經 port 注入依賴（假時鐘、FakeSource、字典），golden cases 才能穩定重現 {討論結論}

## 細節
- 把判斷交給 LLM 時（evaluator、entity extractor、SM-2 評分），golden dataset 要加入模糊案例，並保留 human-in-the-loop 最後確認 {我的判斷}
- LLM 生成 SQL 的語法錯誤易自動抓；語意錯誤（欄位搞混）要看結果是否回答問題，所以人工複核不能省 {討論結論}

## 在設計中怎麼用
- 什麼情況用：任何會持續調整規則的模組，尤其是失敗路徑。
- 怎麼用：每條失敗路徑寫一個可執行案例，斷言最終狀態（例如筆數 (1,1,1)）→ 放進 CI → 改動前後都跑。
- 代價：案例要維護；只能抓到已知失敗，新失敗要靠 error analysis 補。

## 相關
- [[reliable-event-processing]]：失敗路徑的 golden cases
- [[knowledge-retrieval-design]]：檢索規則的 golden cases
- [[worker-monitor-split]]：port 讓案例可重現
- [[completion-marker]]：watchdog 規則的回歸
- [[golden-dataset-x-golden-regression-gate]]：跨領域：統計比較與斷言回歸是同一工具的兩種用法
