---
raw: raw/system-design/structured-rag-golden-eval-hexagonal-pattern.md
raw_sha256: d4c042f7fda8a3423aac6267d6ff8b6f6dfd5874a46507f3b9a5655a2d140c0a
source: system-design
title: 業界經典範例整合：Structured RAG (Text-to-SQL) + Golden-Dataset Eval Harness + Hexagonal Architecture
generated: 2026-11-18
---
# 業界經典範例整合：Structured RAG (Text-to-SQL) + Golden-Dataset Eval Harness + Hexagonal Architecture（note）

## 一句話
內部知識檢索用結構化轉換 + text-to-SQL 取代 naive RAG，以 generator/evaluator + 人工複核驗證生成的 SQL，以 golden dataset 回歸測試當每次迭代的關卡，並用 ports & adapters 分離基礎設施與核心邏輯。

## 主張
原文是排程自動整理的合併文，沒有證據標記：使用者既有的慣例與做法（engineering.md 分層、pass by reference、seam 當 fixed point）→ {使用者決定}；業界案例對照與架構推論 → {討論結論}。

### 合併的概念
- 公司內部知識庫由員工以 HTML 撰寫（文字、圖片、表格），是給人讀不是給 AI 讀；使用者已評估 naive RAG（單純向量相似度）不夠用 {使用者決定} (合併的概念)
- coding-harness-design 採 NOOA 風格 generator/evaluator harness 加 human-in-the-loop 最終確認，核心原則是 pass by reference（大量資料經 pandas/SQLite 傳遞，不塞進 context）{使用者決定} (合併的概念)
- 專案結構慣例：common/ 放共用基礎設施，worker 處理 pubsub 事件與例外，monitor 做業務流程判斷，helper/utility 處理細節函式 {使用者決定} (合併的概念)
- 使用者習慣以 module/seam 邊界當 fixed point，每次改動後人工複查過去結果是否還成立 {使用者決定} (合併的概念)

### 業界經典範例
- Uber QueryGPT、LinkedIn SQL Bot 先把資料整理成有 schema 的表格，再讓 agent 產生 SQL 精準取用欄位與列，與 pass by reference 同原則 {討論結論} (業界經典範例)
- Microsoft GraphRAG、Unstructured.io、Docling 在檢索前做結構化轉換：HTML 表格轉 relational rows、圖片轉 caption/OCR、文件關聯建成 knowledge graph {討論結論} (業界經典範例)
- Golden Master / Approval Testing（Llewellyn Falco）搬進 LLM pipeline 後，成為人工標註的「問題→正確答案」golden dataset，每次調整 prompt/parser/schema 後跑回歸；OpenAI Evals、promptfoo 是這類 eval harness {討論結論} (業界經典範例)
- Hexagonal Architecture / Ports & Adapters（Alistair Cockburn）：核心 domain logic 經 port 介面與外部溝通，外部依賴由 adapter 實作；worker 對應 adapter，monitor 對應核心邏輯，common 對應 port 定義 {討論結論} (業界經典範例)
- 檢索的本質應是精準查詢（query），不是語意相似度的猜測（guess）{討論結論} (業界經典範例)

### 使用場景
- naive RAG 固定長度 chunk 會把表格切散、失去欄位與數值的對應，且抓不到圖片中的文字與圖表數值 {討論結論} (使用場景)
- 結構化 pipeline：parser 把 HTML 表格轉 relational rows 存 SQLite，圖片交 vision model 產生 caption + OCR，章節結構與上下游關聯存成 metadata {討論結論} (使用場景)
- 查詢流程：agent 先判斷要查哪張表、哪個欄位，產生 SQL、執行，再把結果餵回生成答案 {討論結論} (使用場景)
- Generator 產生並執行 SQL；evaluator 檢查結果形狀（列數、欄位、是否有資料），異常打回重來，真正模糊的案例交人工複核 {討論結論} (使用場景)

### Why
- 向量檢索解決「語意相近」，表格需要「精準欄位對應」，兩者是不同問題 {討論結論} (Why)
- Context 有限且昂貴，應以查詢取用，而不是全量傳輸 {討論結論} (Why)
- LLM 生成 SQL 有兩種失敗：語法錯誤執行即失敗、易自動抓；語意錯誤（語法對但邏輯錯，例如本年度與上年度欄位搞混）要看結果是否回答問題，難以完全自動化，所以 human-in-the-loop 不能省 {討論結論} (Why)
- Pipeline 上線後會持續調整 parser、prompt、schema；沒有固定 golden dataset 時每次修改都憑感覺，golden dataset 把「有沒有變差」變成可量化、可在 CI 跑的 gate {討論結論} (Why)
- 「怎麼被觸發、pubsub 失敗怎麼重試」是基礎設施關注點，「結果算不算成功、要不要召回或轉人工」是核心判斷；monitor 不應處理訊息佇列例外，換掉 pubsub（例如改 Kafka）時核心邏輯不必改 {討論結論} (Why)

### 重點要解決的問題
- 四個問題：語意檢索與結構化查詢的取捨、LLM 生成動作難以完全自動驗證、持續迭代下用 golden dataset 當 regression fixed point、基礎設施與核心邏輯分離 {討論結論} (重點要解決的問題)

### 延伸：多模態
- 截圖的 caption + OCR 文字應與表格 rows 存進同一個可查詢的結構化層 {討論結論} (延伸)
- Golden dataset 要包含「答案藏在圖片或表格裡」的案例，確保回歸測試涵蓋多模態檢索路徑 {討論結論} (延伸)

## 變更
- （首次產生）

## 候選連結
- system-design：rag-methods-comparison、postgres-sag-alias-golden-eval-pattern、postgres-hub-hybrid-search-peer-spaced-repetition-pattern、data-freshness-watchdog-scanner-marker-golden-pattern（golden 回歸）、webhook-idempotent-worker-outbox-pattern（worker/monitor 分層）、scanner-executor-timingwheel-nooa-pattern（NOOA harness）
- wiki：golden-dataset、ai-evaluation、promotion-gate、pass-by-reference、agent-harness-design、grader-alignment、error-analysis-loop、ontology-knowledge-graph（GraphRAG、結構化抽取）
