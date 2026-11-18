---
id: knowledge-retrieval-design
title: 知識檢索設計（Knowledge retrieval design）
type: topic
summary: 檢索方法的差別在關係何時建；實務上 SQL 縮範圍、摘要層找與排、原文當證據，精確欄位用結構化查詢不用向量猜
domains: [system-design]
sources: [raw/system-design/rag-methods-comparison.md#怎麼讀, raw/system-design/rag-methods-comparison.md#摘要分層, raw/system-design/rag-methods-comparison.md#查詢流程, raw/system-design/structured-rag-golden-eval-hexagonal-pattern.md#Why, raw/system-design/postgres-sag-alias-golden-eval-pattern.md#為什麼採用這些技術, raw/system-design/pagerduty-escalation-chatops-runbook-pattern.md#業界範例]
evidence: [原文, 討論結論, 第三方, 我的判斷]
related: [hybrid-search-rrf, event-log-current-state, postgres-hub, golden-regression-gate, deterministic-over-llm, llm-wiki-x-knowledge-retrieval-design]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 知識檢索設計（Knowledge retrieval design）

> 檢索方法的差別在關係何時建；實務上 SQL 縮範圍、摘要層找與排、原文當證據，精確欄位用結構化查詢不用向量猜

## 重點
- 關係建立的時機：傳統 RAG 不建、LightRAG 與 LLM wiki 寫入時建、SAG 查詢時建、dreaming 離線批次建 {討論結論}
- 向量檢索解決「語意相近」，表格與 runbook 需要「精準欄位對應」；有標準答案的對應用 query，不用相似度猜 {討論結論}
- 摘要分層：L0 約 100 token 做相似搜尋、L1 約 2k token 做 rerank、答案一律根據 L2 原文；摘要不應比原文長 {第三方}{我的判斷}
- 選擇判準：常需綜合多文件或計算 → 值得建 wiki 或摘要層；多半單一文件查找 → 搜尋加 rerank 就夠 {我的判斷}
- 依更新規則分流：Fact（新值取代舊值，放 structural DB）與 Understanding（新舊印象合併，放 vector store）{討論結論}{我的判斷}

## 細節
**SAG（查詢時建關係）**：每個 chunk 一次 LLM 呼叫產生一個 event 加一組 entity；查詢時向量 + BM25 找 seed，再用 SQL join 串成臨時局部 graph {原文}。SAG 不做 entity 去重，用 alias 表在查詢時雙向展開（台積電 ↔ TSMC）補上；時間用 `event_time` + WHERE {討論結論}

**建議的查詢流程**（同一個 Postgres，未實測）{我的判斷}：
1. SQL 用時間與 tag 篩文件（不耗 token）
2. L0 向量取前 20 個 chunk
3. LLM 讀 20 個 L1 選 5
4. 載入 5 個 L2 回答

**風險**：上層摘要不準會漏掉整棵子樹，保留直接搜所有 chunk 的備援路徑；子層變了上層要由下往上重新產生；漏標 tag 就查不到 {我的判斷}

**Catalog vs DB index**：catalog 是資料本身（index.md、event–entity table），要程式維護；DB index 由引擎維護、只加速 {討論結論}

**結構化轉換**：HTML 表格轉 relational rows、圖片轉 caption + OCR，再讓 agent 產生 SQL（Uber QueryGPT、LinkedIn SQL Bot）；語法錯誤易自動抓，語意錯誤要人工複核 {討論結論}

**Fact 與 Understanding 怎麼分** {我的判斷}：
- 問三件事：只有一個正確答案嗎？可驗證嗎？新資料是取代還是合併？
- 不確定時先放 Understanding，訊號夠強再升級成 Fact。
- Fact 用 [[event-log-current-state]] 存。

## 在設計中怎麼用
- 能用 SQL 篩的先用 SQL（時間、tag、精確名詞），LLM 只判斷意思（[[deterministic-over-llm]]）。
- 關鍵字與向量並用，用 [[hybrid-search-rrf]] 合併。
- 一個來源對應一列或一頁，避免多個程序同時更新同一列。
- 改 alias、排序、parser、prompt 前先跑 [[golden-regression-gate]]。

## 相關
- [[hybrid-search-rrf]]：關鍵字 + 向量
- [[event-log-current-state]]：Fact 的存法
- [[postgres-hub]]：全部放在一個 Postgres
- [[golden-regression-gate]]：檢索規則的回歸
- [[deterministic-over-llm]]：SQL 縮範圍、LLM 判斷意思
- [[llm-wiki-x-knowledge-retrieval-design]]：跨領域：wiki 與摘要分層、SQL catalog 的對照
