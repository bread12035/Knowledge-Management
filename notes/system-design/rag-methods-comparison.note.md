---
raw: raw/system-design/rag-methods-comparison.md
raw_sha256: 01b44636e82b3739db9246fa03553ba015efe2ae33f26c5b49dfd0789a9d1e9a
source: system-design
title: 知識檢索方法比較：傳統 RAG / LLM wiki / LightRAG / SAG（另含 agent memory 各層）
generated: 2026-11-18
---
# 知識檢索方法比較：傳統 RAG / LLM wiki / LightRAG / SAG（另含 agent memory 各層）（note）

## 一句話
各檢索方法的核心差別是「關係在什麼時候建」（不建、寫入時、查詢時、離線批次）；實務建議是在同一個 Postgres 用 SQL 縮小範圍、L0 摘要做相似搜尋、L1 做 rerank、L2 原文當證據，並把 Fact 與 Understanding 依更新規則分流。

## 主張
證據對應：SAG 細節（論文查證）→ {原文}；傳統 RAG / LLM wiki / LightRAG 的「原生」描述（既有知識、未查版本）→ {討論結論}；OpenViking（專案說明＋第三方文章）與 Anthropic 文章（讀近乎完整的轉載版）→ {第三方}；「建議」、整理者想法、未實測 SQL → {我的判斷}；Google Memory Bank（使用者轉述）與使用者觀察 → {討論結論}；無標記 → {討論結論}。

### 怎麼讀 / 一句話描述
- 四種方法的核心差別是關係建立的時機：傳統 RAG 不建，LightRAG 與 LLM wiki 在寫入時建，SAG 在查詢時建，dreaming 是第四種時機「離線批次」 {討論結論} (§怎麼讀)
- 傳統 RAG：切段 → embedding → 找最相似，可混 BM25 做 hybrid {討論結論} (§一句話描述, 表1)
- LLM wiki：LLM 先讀完原文寫成互相連結的 markdown 頁，查詢從 index.md 開始沿 link 翻頁 {討論結論} (§一句話描述, 表1)
- LightRAG：LLM 抽 entity 與 relation 建全域 graph，查詢時把 query 拆成具體關鍵字與主題關鍵字兩層比對 {討論結論} (表1, 表4)
- SAG：每個 chunk 一次 LLM 呼叫產生一個 event（一句摘要）加一組 entity，查詢時用向量＋BM25 找 seed，再用 SQL join 把共用 entity 的 event 串成臨時局部 graph {原文} (§一句話描述, 表1)
- Contextual retrieve 指檢索前在每個 chunk 前補上下文（標題、文件摘要）；rephrase 指把問題改寫成更好查的樣子 {討論結論} (§怎麼讀)

### 表 1–4：agent memory 五層
- Agent memory 分五層：transcript 搜尋（原樣保存）、memory notes（會話中 agent 寫筆記）、linked wiki（離線改寫成互連頁）、injected context（harness 每次會話開頭載入）、dreaming（離線批次維護其他層，不是檢索方式） {第三方} (§一句話描述, 表1)
- Claude Code 的常駐層只載入 MEMORY.md 的前 200 行或 25 KB {第三方} (表1, §測試數字)
- Dreaming 用來修正隨環境變動而過時的記憶 {第三方} (表3)

### 表 2–4：chunking、時間、rerank、rephrase
- SAG 一個 chunk 對應一個 event，論文沒給長度數字；建議按語意邊界切、overlap 少 {我的判斷} (表2)
- 時間建議：RAG metadata 加 `event_time` 查詢時 filter；SAG event 表加 `event_time` 用 WHERE 過濾，因本來就是 SQL 所以最容易 {我的判斷} (表3)
- 傳統 RAG 的 rerank 做法：先取 top 20–50 → cross-encoder 或 LLM 重排 → 留 5–10 {討論結論} (表4)
- 傳統 RAG 的 rephrase 做法：LLM 把問題改成 2–3 種問法各自檢索再合併 {討論結論} (表4)
- SAG 原生 rerank：LLM 對展開後的 event 重排，只留前 K 個，最後合成 10 個 chunk {原文} (表4)
- LLM wiki 與 SAG 都建議在 index 或查詢時加 alias 展開（TSMC = 台積電）讓問題對得上頁名或 entity {我的判斷} (表4)

### Anthropic 測試數字
- 公司文件測試（約 35 萬檔案、25 題）只用搜尋得分約 53%；數字為 Anthropic 用 Claude 與自家資料測得，不一定適用其他資料 {第三方} (§測試數字)
- 單用 wiki 時 dreaming 從 2 個 session 增到 128 個，得分從 13% 升到 48% {第三方} (§測試數字)
- wiki 加搜尋得分從 54% 升到 61%，每題約省 2 萬 token {第三方} (§測試數字)

### 補充：SAG 不做 entity 去重
- SAG 不去重的好處是每個 chunk 可獨立處理、新資料直接追加，不必與舊資料比對 {原文} (§SAG 去重)
- 代價是同一東西的不同寫法（TSMC / 台積電）不會被 SQL join 接起來；向量路徑可部分緩解 {原文} (§SAG 去重)
- 建議另加 alias 對照表，在查詢時展開 {我的判斷} (§SAG 去重)

### 補充：catalog 與 DB index
- Catalog 是指向內容的清單，屬於資料本身，內容變了要靠程式一起更新（index.md、SAG 的 event–entity table 都是）{討論結論} (§catalog)
- DB index 附在 table 上由資料庫引擎自動維護，不改變資料，只加快 `WHERE` 與 `JOIN` {討論結論} (§catalog)
- index.md 由 LLM 掃整份判斷、可寫自由語意描述，但變大會塞爆 context 且難統計；SQL catalog 用精準條件查、可放大量資料、一行 `COUNT`，但欄位固定 {討論結論} (§catalog)
- B-tree 每層排除大部分資料，幾百萬筆通常走三、四層；也能加速範圍查詢與 `ORDER BY` {討論結論} (§catalog 例子3)
- B-tree 只處理相等與大小比較；embedding 相似度搜尋要用 pgvector 的 HNSW 或 IVFFlat {討論結論} (§catalog 例子3)
- 多表統整由輕到重：view（只存 SQL、不會變快）→ materialized view（查得快，資料變了要手動 `REFRESH`）→ 自建 catalog table（寫入時一起更新） {討論結論} (§catalog)
- 索引只有查詢真的用到該欄位才有用；索引越多寫入越慢 {討論結論} (§catalog)

### 補充：摘要分層 L0/L1/L2
- 原則：寫入時先做好摘要，查詢時先看摘要，需要時才讀原文 {討論結論} (§摘要分層)
- OpenViking 定義 L0 abstract 約 100 token（篩選與向量搜尋）、L1 overview 約 2k token（導覽與 rerank）、L2 detail 為完整原文（按需載入） {第三方} (§摘要分層)
- 做法 A（整理者想法）把 L0/L1 搬到 chunk 層級：L0 做 embedding 與全文索引，L1 給 LLM rerank，答案一律根據 L2 {我的判斷} (§做法A)
- 做法 A 流程：contextualize chunk → LLM 產 L0/L1 → query 搜 L0 取前 50 → LLM 讀 50 個 L1 選前 5 → 載入 5 個 L2 回答 {我的判斷} (§做法A)
- SAG 的 event 等同 L0、原始 chunk 等同 L2，做法 A 補上 L1；L0 與 L1 可放在 SAG 原本那次 LLM 呼叫裡產生（需實測） {我的判斷} (§做法A)
- 摘要風險與對策：可能漏精確數字與名詞 → 原文也留 BM25 索引；摘要可能錯 → L0/L1 只用來找與排序；寫入成本增加 → 合併進同一次 LLM 呼叫 {我的判斷} (§做法A)
- OpenViking 是 ByteDance 開源的 context database，用 `viking://` 虛擬檔案系統，每個目錄由 LLM 產生 `.abstract.md`（L0）與 `.overview.md`（L1），最上層最後產生，文件註明不要手動編輯 {第三方} (§做法B)
- OpenViking 的 directory recursive retrieval 先用全域向量找分數最高的目錄，再進目錄遞迴往下鑽，合併排序並保留檢索路徑 {第三方} (§做法B)
- 第三方稱往下鑽時節點分數是自身相似度與父層分數各占一半（二手資料，待核對） {第三方} (§做法B)
- OpenViking 階層檢索「更準」沒有公開比較證據；省 token 與可追蹤有道理 {第三方} (§做法B)
- OpenViking 與 index.md 的最大差別是把一份長清單拆成分散在各層的小份，只讀走到的層，所以省 token；底層仍有向量索引 {討論結論} (§比較)
- 分工：SQL 負責縮小範圍，LLM 負責判斷意思；兩邊在寫入時產生目錄內容都要靠 LLM {討論結論} (§比較)

### 補充：同一張 table 放原文、L0、L1
- 建議單表 `nodes`：每列一個節點，欄位含 `parent_id`、`root_id`、`node_type`（doc/section/chunk）、`event_time`、`l0`、`l0_embedding VECTOR(1024)`、`l1`、`l2`（大時改 `l2_path`），並對 `l0_embedding` 建 hnsw 索引 {我的判斷} (§單表設計)
- 分層兩種做法：同表 self-reference（一套 index、層數不固定，但空欄位多、原文會讓表變重）或各層一張表用外鍵連（欄位乾淨但 join 多）；依規模決定 {我的判斷} (§分層)
- 用 materialized view `catalog_top` 把 doc 與 section 整理成目錄，可給 SQL 條件查，也可轉成文字給 LLM 讀 {我的判斷} (§SQL catalog)
- 查詢流程：SQL 用時間與 tag 篩文件（不耗 token）→ L0 向量取前 20 個 chunk → LLM 讀 20 個 L1 選 5 → 載入 5 個 L2 回答 {我的判斷} (§查詢流程)
- 上層摘要不準會漏掉整棵子樹；對策是保留直接搜所有 chunk L0 的備援路徑 {我的判斷} (§風險)
- 子層內容變了，上層 L0/L1 要由下往上重新產生 {我的判斷} (§風險)
- SQL 篩選品質取決於寫入時填的欄位，漏標 tag 就查不到；對策是 alias 表並保留 embedding 與全文搜尋 {我的判斷} (§風險)
- 放進 table 得到查詢能力，失去像 index.md 一樣直接打開編輯的方便 {我的判斷} (§風險)

### 補充：Google Memory Bank 的 Fact / Understanding 分流
- Google Memory Bank 依更新規則把記憶分成 Fact（structural DB，synchronize）與 Understanding（vector store，post-extraction，訊號夠強才寫入），兩者都在 session 開始前讀 {討論結論} (§Google 設計)
- 新資訊會和既有記憶整併而不是只堆疊（二手文章提到） {第三方} (§查證狀態)
- 分流理由：Fact 新值取代舊值，Understanding 新舊印象合併；全放 vector store 會同時撈到新舊值、LLM 可能選舊的；全放 SQL 則偏好沒固定欄位也不能語意搜尋 {我的判斷} (§為什麼分開)
- 分辨三問：只有一個正確答案嗎、可驗證嗎、新資料是取代還是合併；取代且可驗證 → Fact {我的判斷} (§怎麼分辨)
- 不確定時先放 Understanding 並保留原文，訊號夠強再升級成 Fact，分錯代價較低 {我的判斷} (§怎麼分辨)
- Fact 以 event log（只追加）為主，current state 由它用 view 或 materialized view 算出；明細可算出餘額，餘額不能還原明細 {我的判斷} (§Fact 存法)
- 查某時間點狀態時，`buy` 與 `give` 兩側都要加 `event_time <= 該時間`，只加一側會算錯 {我的判斷} (§Fact 存法)
- 文字型方法存「故事」，每次查詢都要重讀推算最後狀態；structural DB 存「結果」直接讀 {討論結論} (§Fact 放 structural DB)
- 抽取成欄位一定丟資訊；對策是 event log 加 `source` 欄位指回原文 {討論結論} (§Fact 放 structural DB)
- Understanding 依資料性質選載體：短句偏好用 RAG＋vector、少量高密度長期印象用 LLM wiki、有時間與 entity 的事件型印象用 SAG、複雜關係用 GraphRAG/LightRAG {我的判斷} (§Understanding)
- SAG 只追加、不去重，適合 Understanding 的事件摘要，但不適合 Fact 的「現在狀態」（買了又送難處理） {我的判斷} (§和 SAG 比較)
- 建議同一個 Postgres：Fact 用 `fact_events`＋current state view，Understanding 用 SAG 式 `u_events`、`u_event_entity`、`alias` 表加 pgvector；SQL 為未執行過的草稿 {我的判斷} (§和 SAG 比較)
- 讀取時 Fact 與 Understanding 用標題分開放進 prompt，因 agent 只看得到文字；衝突時 Fact 優先（未查證） {我的判斷} (§讀取流程)
- 多模態內容另存，並產生 caption 或 OCR 文字讓文字側能指回它 {我的判斷} (§風險與對策)

### 補充：從 Anthropic agent memory 文章可融入的想法
- 時間軸多一格「離線批次」：L0/L1 可寫入時先做簡版，再用離線批次補強校對；代價是運算成本與輸出非即時 {我的判斷} (§1)
- Dreaming 以 transcript 為標準答案改正筆記；遊戲例子中錯的地標筆記讓 agent 一直失敗，改正後才走對 {第三方} (§2)
- 應定期把 L0/L1 對照 L2 重驗；原則是不要只壓縮不校對 {我的判斷} (§2)
- 需綜合多份文件的題目 wiki 得 87%、只用搜尋 73%；答案在單一文件時 wiki 沒有明顯好處 {第三方} (§3)
- 選擇判準：常需綜合多文件、判斷或算術 → 值得建 wiki 或摘要層；多半單一文件查找 → 搜尋加 rerank 就夠 {我的判斷} (§3)
- 10 份文件共 115 KB 產生 203 KB 的 wiki，是原文 1.77 倍，部分頁面沒有 link {第三方} (§4)
- 摘要不應比原文長：L1 不超過 L2，L0 約 100 token、L1 約 2k token 要有上限，並定期比較摘要總量與原文總量 {我的判斷} (§4)
- 四個 agent 同時寫同一張共用表互相覆蓋，57 項事實只保住 41 項；改成每份合約一頁、一個 agent 負責後 57 項全保住 {第三方} (§5)
- Table 設計時一個來源對應一列或一頁，避免多個程序同時更新同一列 {我的判斷} (§5)
- 常駐層每次會話都耗 token，錯誤筆記會擴散到之後每次會話，所以只放索引、細節往下放並留連結；若把摘要放進 prompt 要設硬上限 {第三方} (§6)
- OpenViking 的 L0 是按需讀取，常駐層是每次都載入，兩者用途不同 {我的判斷} (§6)
- 只告訴模型「有一個記憶資料夾」較強模型就能用好；規定「只記失敗」時較強模型收益損失最多 0.234，較舊的 Sonnet 4.6 只損失 0.020 {第三方} (§7)
- 產 L0/L1 的 prompt 應寫明用途（L0 給 similar search、L1 給 rerank）而不死規定格式；換較弱模型時可能需要更明確步驟 {我的判斷} (§7)

## 變更
- （首次產生）

## 候選連結
- system-design：postgres-hub-hybrid-search-peer-spaced-repetition-pattern（Postgres hybrid search）、postgres-sag-alias-golden-eval-pattern（SAG＋alias 表）、structured-rag-golden-eval-hexagonal-pattern（結構化 RAG）、single-source-of-truth-postgres-gcs-release-pattern（單一 Postgres、l2_path 指向檔案）、pessimistic-lock-vs-occ-cas-comparison（多寫入者覆蓋同一列）、transactional-outbox-lease-reaper-idempotent-consumer-pattern（event log 只追加）
- wiki：agent-memory、agent-system-memory-layers、llm-wiki、dreaming、injected-context、memory-salience、progressive-disclosure（L0/L1/L2 按需載入）、single-writer（一來源一列 / 一頁）、ontology-knowledge-graph（LightRAG / GraphRAG、entity 去重 ↔ alias 表）、golden-dataset、km-dreaming-design（膨脹比例檢查）
