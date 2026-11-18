---
source_project: system design & code style
source_file: claude/structured-rag-golden-eval-hexagonal-pattern.md
title: 業界經典範例整合：Structured RAG (Text-to-SQL) + Golden-Dataset Eval Harness + Hexagonal Architecture
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Structured RAG (Text-to-SQL) + Golden-Dataset Eval Harness + Hexagonal Architecture

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。

## 這次合併了哪些概念

這次從記憶庫裡挑了三個表面上分屬不同專案、但骨子裡是同一種「如何讓 agent 可靠地存取大量結構化知識」問題的討論，合併成一個完整的實作範例：

1. **ai-searchable-knowledge-base**：你的公司內部知識管理系統，員工用 HTML 寫記錄（含文字、圖片、表格），是為了人類閱讀而寫，不是為了 AI 讀取而寫；你評估過 naive RAG（單純向量相似度檢索）對這個場景是不夠的。
2. **coding-harness-design**：NOOA 風格的 generator/evaluator harness——generator 負責動手做，evaluator 負責檢查合理性，再加上 human-in-the-loop 的最終確認；核心原則是 pass by reference（大量資料透過 pandas/SQLite 傳遞，而不是整包塞進 LLM 的 context）。
3. **engineering.md**：你慣用的專案結構——common/ 放共用基礎設施，worker 負責 pubsub 事件邏輯與例外處理，monitor 負責業務流程判斷，helper/utility 處理細節函式；以及你「用 module/seam 邊界當作 fixed point，每次改動後人工複查過去結果是否還成立」的習慣。

把這三個放在一起看，會發現它們共同指向同一個業界經典模式——**Structured Retrieval（結構化檢索）取代 naive RAG，搭配 Regression Gate（回歸測試關卡）驗證每次迭代，再用 Ports & Adapters 把基礎設施跟核心邏輯分開**，這是企業內部知識檢索系統與 LLM pipeline 工程化過程中反覆出現的標準架構。

## 業界經典範例

這個模式在業界有具體的先例可以對照：

- **Uber 的 QueryGPT / LinkedIn 的 SQL Bot（Text-to-SQL Agentic Retrieval）**：與其讓 LLM 直接在一大堆向量化的文字片段裡「猜」哪段最相關，這類系統先把資料整理成有明確 schema 的表格，再讓 agent 產生 SQL 查詢去精準取用需要的欄位與列——這跟你在 coding-harness-design 裡「pass by reference，用 SQLite/pandas 查詢而非整包塞 context」是同一個原則，只是把它用在「內部知識檢索」這個場景。
- **Microsoft GraphRAG 與 Unstructured.io / Docling 這類文件結構化 pipeline**：這些工具的共同思路是「naive RAG 把長文機械式切塊、做向量相似度比對，會拆散表格的欄位對應關係、也會讓跨段落的上下文斷裂」，所以在檢索之前先做一層結構化轉換——把 HTML 表格轉成真正的 relational rows、把圖片轉成 caption/OCR 文字、把文件之間的關聯建成 knowledge graph——這正是你評估「naive RAG 不夠用」之後，該往的方向。
- **Golden Master / Approval Testing（Llewellyn Falco 提出的經典測試手法）與 OpenAI Evals、promptfoo 這類 LLM eval harness**：軟體工程裡「先跑一次現有邏輯，把輸出存成 golden file，之後每次改動都拿新輸出跟 golden file 比對」的做法，被搬進 LLM pipeline 之後變成「準備一組人工標註過的『問題→正確答案』golden dataset，每次調整 prompt/parser/schema 之後跑一次回歸測試」——這正是把你在 engineering.md 裡「用 seam 當 fixed point，人工複查過去結果是否還成立」的習慣，系統化成自動化的驗證關卡。
- **Hexagonal Architecture / Ports & Adapters（Alistair Cockburn 提出的經典架構模式）**：核心 domain logic 不該直接依賴外部世界的細節（訊息佇列、資料庫 SDK、HTTP client），而是透過「port」定義好的介面跟外部溝通，實際的外部依賴用「adapter」去實作——你的 common/worker/monitor/helper 分層，其實就是這個模式的具體實踐：worker 是處理外部訊息的 adapter，monitor 是不該被基礎設施細節污染的核心邏輯，common 是共用的 port 定義。

你在 ai-searchable-knowledge-base 裡「naive RAG 不夠用」的判斷，其實就是在重新發現 QueryGPT / GraphRAG 這類系統想解決的同一個問題：**檢索的本質應該是精準查詢（query），而不是語意相似度的猜測（guess）**。

## 使用場景（Use Case）

想像你要把公司內部那套 HTML 格式的知識庫，改造成一個 agent 可以快速查詢的系統。這些記錄裡有段落文字，也有大量表格（例如某個產品各版本的參數對照表）跟截圖（例如系統架構圖、操作流程截圖）。如果直接套用 naive RAG——把整份文件切成固定長度的 chunk，做 embedding，存進向量資料庫——會發生兩個問題：表格被切成好幾個 chunk 之後，欄位跟數值的對應關係就消失了；圖片裡的資訊（例如截圖上的文字、圖表數值）向量相似度也完全抓不到。

於是改用一條結構化轉換的 pipeline：先跑一個 parser，把 HTML 裡的表格轉成真正的 relational rows 存進 SQLite，把圖片丟給 vision model 產生 caption 加 OCR 文字，把整份文件的章節結構、上下游關聯記錄成 metadata。這一步做完之後，agent 不再是「向量相似度找最像的段落」，而是「先理解使用者問題要查哪張表、哪個欄位，產生一段 SQL，執行後把結果餵回去生成答案」——這就是 pass by reference 在知識檢索場景裡的具體落地。而這個「LLM 生成 SQL」的動作本身有風險：語法可能寫錯、也可能語法對但查錯邏輯（例如把「本年度」跟「上年度」的欄位搞混）；所以用 generator/evaluator 分工，generator 產生並執行 SQL，evaluator 檢查回傳結果的形狀是否合理（列數、欄位、有沒有查到資料），異常的話打回重來，真正模糊的案例則交給人工複核。而整套轉換 pipeline 上線之後，你一定會持續調整 parser 的規則、prompt 的寫法、schema 的設計——這時候如果沒有一組固定的「已知問題→正確答案」golden dataset 可以跑回歸測試，每一次修改都是憑感覺，跟你在 engineering.md 提到的「每次改動後人工複查過去結果是否還成立」的習慣完全對應，只是把它自動化成一個可以量化、可以跑在 CI 裡的 gate。

## 為什麼採用這些技術（Why）

放棄 naive RAG、改用結構化儲存加上 text-to-SQL 查詢，是因為向量相似度檢索的本質是「語意相近」，但表格資料需要的是「精準的欄位對應關係」，兩者是完全不同的問題——把表格硬塞進向量相似度的框架裡，等於用錯的工具解決問題。轉成 typed schema 之後，agent 能用查詢的方式精準取用它真正需要的那一小部分資料，這跟 coding-harness-design 裡「pass by reference，用 SQL/pandas 查詢而非整包塞進 context」是同一個核心原則的延伸：**context 是有限且昂貴的資源，該用查詢取用，而不是全量傳輸**。

generator/evaluator 加上 human-in-the-loop 用在 SQL 生成上，是因為 LLM 產生的查詢有兩種失敗模式，難度完全不同：語法錯誤執行就會失敗，容易自動抓到；但語意錯誤（語法正確、但查詢邏輯本身有問題）通常要看執行結果是否真的回答了使用者的問題才看得出來，這種判斷很難完全自動化，所以 human-in-the-loop 這道關卡不能省略——evaluator 負責篩掉明顯異常的結果，把真正模糊的案例留給人工做最後判斷，分工讓驗證的成本跟精準度可以取得平衡。

採用 golden dataset 回歸測試，是因為結構化檢索 pipeline 一旦上線一定會持續迭代——調整 parser 的表格解析規則、調整 SQL 生成的 prompt、調整 schema 設計——如果每次修改都要靠人工把所有案例重新看一遍，既沒效率也容易漏掉迴歸的問題。固定一組已知答案的 golden dataset，讓「這次修改有沒有讓結果變差」變成可以量化、可以自動跑的事，這正是把你在 engineering.md 裡「用 module/seam 邊界當 fixed point」的習慣往前推一步：從「人工複查」進化成「自動化回歸關卡」，但背後的精神——**先確認過去建立的結果還站得住，才放心往下建**——完全一致。

common/worker/monitor/helper 分層對應 Hexagonal Architecture 的 ports & adapters，是因為「這個轉換任務怎麼被觸發、pubsub 訊息處理失敗要怎麼重試」跟「這次查詢結果算不算成功、要不要進一步召回或轉交人工」是兩種完全不同層次的關注點：前者是基礎設施細節，後者是核心業務判斷。如果讓 monitor 直接處理訊息佇列的例外，核心邏輯會被基礎設施污染，將來想把訊息佇列從 pubsub 換成 Kafka，核心的判斷邏輯也不該被迫跟著改——這正是 ports & adapters 想達成的效果：**核心邏輯透過穩定的介面跟外部世界溝通，外部依賴的實作細節可以替換而不影響核心**。

## 重點要解決的問題

把這三個概念合在一起看，這個架構真正要解決的問題可以歸納成四點：第一，**語意檢索與結構化查詢的取捨**——naive RAG 把為人類閱讀設計的內容（表格、圖片、跨段落結構）硬套進向量相似度框架，會遺失結構化的對應關係；轉成 typed schema 加上 text-to-SQL 查詢，才能精準取用真正需要的資料，這也呼應了 pass by reference 的核心精神。第二，**LLM 生成動作的正確性難以完全自動驗證**——語法錯誤容易抓，語意錯誤很難，所以需要 generator/evaluator 分工加上人工在關鍵節點複核，才能兼顧效率與可信度。第三，**pipeline 持續迭代下如何維持信心**——需要 golden dataset 當作 regression 的 fixed point，把「這次修改有沒有讓結果變差」變成可測量、可自動化的事，而不是每次都靠人工肉眼複查。第四，**基礎設施關注點與核心邏輯要分離**——common/worker/monitor/helper 分層（也就是 ports & adapters 的具體實踐）讓「怎麼被觸發、怎麼處理失敗重試」跟「這次結果算不算對」互不干擾，將來替換基礎設施元件時，核心邏輯不必跟著改動。

## 延伸一步：如果把多模態內容也涵蓋進來

如果要更完整地涵蓋 ai-searchable-knowledge-base 提到的「圖片、表格都是知識庫的一部分」，可以把這套系統再往前一步：用 vision model 把截圖轉成 caption 加 OCR 文字，跟表格轉出來的 relational rows 一樣存進同一個可查詢的結構化層，讓 text-to-SQL 的 agent 真正能涵蓋所有格式的知識，而不只是純文字段落。這樣一來，golden dataset 裡也該包含「答案藏在圖片或表格裡」的案例，確保回歸測試真的涵蓋到多模態的檢索路徑，而不是只驗證了純文字的部分。
