---
source_project: system design & code style
source_file: claude/rag-methods-comparison.md
title: 知識檢索方法比較：傳統 RAG / LLM wiki / LightRAG / SAG（另含 agent memory 各層）
first_exported: 2026-11-18
updated: 2026-11-18
---
# 知識檢索方法比較：傳統 RAG / LLM wiki / LightRAG / SAG（另含 agent memory 各層）

整理日期：2026-10-25
更新日期：
- 2026-10-26：新增「catalog 與 DB index」一節
- 2026-10-28：新增「摘要分層 L0/L1/L2：chunk 層級與 OpenViking 目錄層級」一節
- 2026-10-28：新增「同一張 table 放原文、L0、L1，並分層與 SQL catalog」一節
- 2026-10-29：新增「Google Memory Bank 的 Fact / Understanding 分流，以及四種方法的對應」一節
- 2026-11-09：在表 1–4 新增 Anthropic「The components of agent memory」的五列（transcript 搜尋、memory notes、linked wiki、injected context、dreaming）
- 2026-11-09：新增「從 Anthropic agent memory 文章可融入的想法」一節

## 怎麼讀這份表

- 四個方法的核心差別：**關係在什麼時候建。** 傳統 RAG 不建。LightRAG 和 LLM wiki 在寫入時建。SAG 在查詢時才建。agent memory 的 dreaming 則是第三種時機：離線批次（見「從 Anthropic agent memory 文章可融入的想法」）。
- **原生**：方法本身就有的設計。
- **建議**：整理者的設計建議，不是方法本身的規定。
- 查證狀態：只有 SAG 的細節用論文查證過。傳統 RAG、LLM wiki、LightRAG 來自既有知識，版本細節請再核對。OpenViking 的內容來自專案說明和第三方文章，沒有讀原始碼。
- 標「（agent memory）」的五列，來自 Anthropic 2026-11-06 的文章。我無法直接打開原始頁面，是讀一份幾乎完整的轉載。文章沒討論的欄位，寫「文章未討論」。數字是 Anthropic 用 Claude 和自己的資料測的，不一定適用於其他資料。
- Contextual retrieve：檢索前，先在每個 chunk 前補上它的上下文，例如標題或文件摘要。
- Rephrase：把使用者的問題改寫成更好查的樣子。

## 一句話描述

- 傳統 RAG：切段、轉向量、找最像的。
- LLM wiki：LLM 先把原文讀完，寫成互相連結的 markdown 頁面，查詢時從索引頁開始翻。
- LightRAG：LLM 抽出 entity 和 relation，建成全域 graph，再用兩層關鍵字查。
- SAG：每段變成一個 event 加一組 entity，查詢時才用 SQL join，把共用 entity 的 event 串成臨時的局部 graph。
- Transcript 搜尋（agent memory）：原始紀錄不處理，直接搜尋。
- Memory notes（agent memory）：agent 在工作中，把它判斷重要的觀察寫成筆記檔。
- Linked wiki（agent memory）：離線整理時，把 transcript 和筆記改寫成互相連結的頁面。
- Injected context（agent memory）：每次會話開頭，由 harness 載入的少量內容。
- Dreaming（agent memory）：離線批次。讀既有記憶和 transcript，改錯、合併、補 link，並挑出要晉升到常駐層的內容。

## 表 1：進入點與 ingestion

| 方法 | 進入點 | Ingestion 動作 | 抽取的指標 |
|---|---|---|---|
| 傳統 RAG | embedding + 相似度搜尋。可混 BM25（hybrid）。 | 切 chunk → embedding → 存入。 | 向量、metadata |
| LLM wiki | 先讀 index.md，再沿 link 開頁。 | 新資料進來 → LLM 讀 → 新增或更新頁面 → 補 link → 更新 index。 | 概念（一頁一個）、頁間關聯、統整摘要 |
| LightRAG | 從 query 抽關鍵字 → 比對 entity 向量和 relation 向量。 | 切 chunk → LLM 抽 entity 和 relation → 合併同名 → 建 graph。 | entity、relation、各自的描述 |
| SAG | 向量 + 全文（BM25）找 seed，再用 SQL join 展開。 | 切 chunk → 每段一次 LLM 呼叫 → 寫入 SQL、向量、全文。 | event（一句摘要）、entity（索引鍵） |
| Transcript 搜尋（agent memory） | 對原始紀錄做搜尋。文章只說可搜尋，沒指定關鍵字或向量。 | 不處理，原樣保存事件紀錄。 | 無，保留原始事件 |
| Memory notes（agent memory） | agent 讀資料夾裡的筆記檔。 | 會話中，agent 判斷重要的，就寫成筆記。 | 觀察、規則、失敗診斷、下一步 |
| Linked wiki（agent memory） | 沿 link 讀頁。可搭配搜尋。 | dreaming 讀 transcript 和筆記 → 寫頁、改頁、合併重複、對照來源查證。 | 頁面、頁間 link、主題整理 |
| Injected context（agent memory） | 不用找。harness 每次會話開頭直接載入。 | dreaming 挑少數筆記晉升到頂層，細節往下放並留 link。 | 小型索引。Claude Code 是 MEMORY.md 的前 200 行或 25 KB。 |
| Dreaming（agent memory） | 不是檢索方式。它維護其他幾層。 | 離線批次：讀既有記憶和 transcript → 改錯、合併、補 link、挑晉升。 | 修正後的筆記、wiki 頁、常駐索引 |

## 表 2：Chunking、資料型態、載體

| 方法 | Chunking | 資料型態 | 載體 |
|---|---|---|---|
| 傳統 RAG | 固定長度或語意切。常加 overlap。 | text based + 向量 | vector DB，或 Postgres + pgvector |
| LLM wiki | 不切 chunk，以「頁」為單位。 | text based，有 link 像輕量 graph | markdown 檔（Obsidian）。索引可放 DB table。 |
| LightRAG | 固定 token 長度加 overlap（數字請查文件）。 | graph like + 向量 | graph store + vector store，也可全放 Postgres |
| SAG | 一個 chunk 對應一個 event。論文沒給數字。**建議**按語意邊界切，overlap 要少。 | table like + 向量 + 全文 | SQL DB（Postgres） |
| Transcript 搜尋（agent memory） | 文章未討論。 | text based，事件紀錄 | 事件紀錄（形式文章未指定） |
| Memory notes（agent memory） | 以「筆記檔」為單位，不切 chunk。 | text based | 資料夾裡的檔案 |
| Linked wiki（agent memory） | 以「頁」為單位，不切 chunk。 | text based，有 link 像輕量 graph | 檔案（wiki 頁的集合） |
| Injected context（agent memory） | 整份載入，有大小上限。 | text based | 檔案（例如 MEMORY.md） |
| Dreaming（agent memory） | 不適用 | 不適用，它作用在上面幾層 | 不適用 |

## 表 3：時間與 contextual retrieve

| 方法 | 加入時間 | Contextual retrieve |
|---|---|---|
| 傳統 RAG | **建議**：metadata 加 `event_time`，查詢時用 filter。 | **可做**：寫入時用 LLM 為每個 chunk 寫一句上下文，接在前面再 embedding。 |
| LLM wiki | **建議**：頁面開頭加日期，並維護一份按時間排序的紀錄頁。 | **原生接近**：頁面本身就是整理過、帶 link 的上下文。 |
| LightRAG | 沒看到原生支援。**建議**：在 chunk metadata 或 entity 描述裡加時間。 | 非原生。**建議**：抽取前先在 chunk 前補上標題。 |
| SAG | 非原生。**建議**：event 表加 `event_time` 欄位，SQL 用 WHERE 過濾。 | **原生接近**：event 就是帶完整語意的摘要。也可在 chunk 前加標題。 |
| Transcript 搜尋（agent memory） | 事件紀錄本身有先後順序。文章未特別討論時間過濾。 | 無。原始紀錄沒有補上下文。 |
| Memory notes（agent memory） | 文章未討論。**建議**筆記標日期。 | **原生接近**：筆記本身就是整理過的短上下文。 |
| Linked wiki（agent memory） | 文章未討論。**建議**頁面標日期（同 LLM wiki）。 | **原生接近**：link 把相關頁連起來，提供上下文。 |
| Injected context（agent memory） | 文章未討論。 | 它本身就是每次會話都在的上下文。 |
| Dreaming（agent memory） | 文章指出記憶可能隨環境變動而過時，dreaming 用來修正。 | 不適用。輸出是整理好的上下文。 |

SAG 加時間最容易，因為它本來就是 SQL。

## 表 4：Rerank 與 rephrase

| 方法 | Rerank | Rephrase |
|---|---|---|
| 傳統 RAG | **可做**：先取 top 20–50 → cross-encoder 或 LLM 重排 → 留 5–10。 | **可做**：LLM 把問題改成 2–3 種問法，各自檢索，再合併。 |
| LLM wiki | 較少需要。LLM 讀 index 後自己挑頁。頁數很多時，可先用 BM25 取候選。 | **建議**：在 index 放同義詞（alias），讓問題對得上頁名。 |
| LightRAG | 新版支援 reranker（請查所用版本）。也可在合併結果後自己加一層。 | **原生**：LLM 先把 query 拆成具體關鍵字和主題關鍵字。 |
| SAG | **原生**：LLM 對展開後的 event 重排，只留前 K 個，最後合成 10 個 chunk。 | **部分原生**：LLM 辨識 query 裡的 entity。**建議**再加 alias 展開（TSMC = 台積電）。 |
| Transcript 搜尋（agent memory） | 文章未討論。**建議**用 LLM 重排搜尋結果。 | 文章未討論。**建議**用 query 改寫。 |
| Memory notes（agent memory） | 少需要。agent 自己讀檔挑選。 | 文章未討論。 |
| Linked wiki（agent memory） | 文章未討論。agent 讀頁後自己判斷。 | 文章未討論。**建議**在頁面放 alias。 |
| Injected context（agent memory） | 不適用 | 不適用 |
| Dreaming（agent memory） | 不適用 | 不適用 |

### agent memory 五列的測試數字（Anthropic 的測試，供參考）

- 在公司文件的測試中（約 35 萬個檔案、25 個問題），只用搜尋的得分約 53%。
- 單用 wiki：dreaming 從 2 個 session 增加到 128 個，得分從 13% 升到 48%。
- wiki 加搜尋：從 54% 升到 61%，每題約省 2 萬 token。
- 常駐層要小：Claude Code 只載入 MEMORY.md 的前 200 行或 25 KB。

## 補充：SAG 不做 entity 去重

- 好處：每個 chunk 可以獨立處理，新資料直接追加，不用和舊資料全部比對。
- 代價：同一個東西的不同寫法（例如 TSMC 和台積電）不會被 SQL join 接起來。
- 緩解：SAG 同時有向量路徑，語意相近的 chunk 仍可能被撈回。
- **建議**：另加一張 alias 對照表，在查詢時展開。

## 補充：catalog 與 DB index（index.md 和 B-tree）

「index」有兩種意思，容易混淆。

### 兩種 index 的差別

- **Catalog（目錄）**：一份指向內容的清單，列出每筆內容是什麼、在哪裡。它是資料的一部分。內容變了，要靠程式一起更新。`index.md` 是這種。SAG 的 event–entity table 也是這種。它像書前面的目錄。
- **DB index（資料庫索引）**：附在一張 table 上，由資料庫引擎自動維護。它不改變資料，只加快 `WHERE` 和 `JOIN`。它像書後面的詞條索引。

### index.md 和 SQL catalog 的比較

| 面向 | index.md | SQL catalog（table） |
|---|---|---|
| 誰在讀 | LLM 讀文字 | 資料庫引擎執行條件查詢 |
| 找東西的方式 | LLM 掃整份後判斷 | 精準條件，例如 `tag = '資料庫'` |
| 規模 | 變大會塞爆 context | 可放很多筆 |
| 統計 | 很難數「有幾篇」 | 一行 `COUNT` |
| 彈性 | 可寫自由的語意描述 | 欄位固定 |

### 例子 1：index.md

```
# index.md
- [[outbox-pattern]] — 事件可靠送出；tag: 微服務；2026-10-12
- [[pgvector]] — Postgres 向量擴充；tag: 資料庫；2026-10-20
```

- 輸入：問「Postgres 的向量怎麼做？」
- 流程：LLM 讀 index.md → 判斷 `pgvector` 這行最相關 → 開啟該頁。
- 輸出：根據 pgvector 頁的內容回答。

### 例子 2：同一份目錄放進 SQL table

```sql
CREATE TABLE catalog (
  id INT PRIMARY KEY, title TEXT, tag TEXT, created_at DATE
);
SELECT title FROM catalog WHERE tag = '資料庫';
```

- 輸出：`pgvector`。
- 和 index.md 的差別：不用 LLM 讀，條件寫得出來就能精準查。

### DB index 是什麼

- 它是一份排好序的清單。每一行是「值 → 這筆資料放在哪裡」。
- 它只複製那一個欄位的值。欄位本身存資料，順序是寫入的順序。
- index 不取代欄位，是欄位旁邊的捷徑。

### 例子 3：B-tree 怎麼加速

假設 `entities` 表有 100 萬筆，查 `WHERE name = 'TSMC'`。

沒有 index：
- Step 1：從第一筆開始，一筆一筆看。
- Step 2：看完 100 萬筆才確定找完。

有 B-tree index：
- Step 1：根節點是一張小表，寫著「Google 以前往左、Samsung 以後往右」。
- Step 2：`TSMC` 排在 Samsung 之後，往右，進下一層。
- Step 3：再走一、兩層，到最底層，找到 `TSMC → 某筆資料的位置`。
- Step 4：照這個位置直接讀那一筆。

每一層都能排除大部分資料。每個節點放很多個值，所以幾百萬筆通常只要走三、四層。

因為值是排好序的，B-tree 也能加速範圍查詢（`event_time > '2026-10-01'`）和 `ORDER BY`。

注意：B-tree 只管「值相等或大小比較」。embedding 的相似度搜尋要用另一種 index（pgvector 的 HNSW 或 IVFFlat）。

### 在多張 table 上做統整

由輕到重有三種做法：

- **View**：只存一段 SQL，不存資料。方便，但不會變快。
- **Materialized view**：把查詢結果存起來，查得快。資料變了要手動 `REFRESH`。
- **自建 catalog table**：自己建一張表，寫入時一起更新。

```sql
-- DB index：讓「找某個 entity 的所有 event」變快
CREATE INDEX idx_ee_entity ON event_entity (entity_id);

-- 統整：把多張表的重點放在一起
CREATE MATERIALIZED VIEW catalog_all AS
SELECT 'event' AS src, id, summary AS title, event_time FROM events
UNION ALL
SELECT 'note', id, title, created_at FROM notes;

-- 資料變了，再執行：
REFRESH MATERIALIZED VIEW catalog_all;
```

兩個注意：
- 索引只有在查詢真的用到那個欄位時才有用。
- 索引越多，寫入越慢。

## 補充：摘要分層 L0/L1/L2（chunk 層級與 OpenViking 目錄層級）

一句話：**寫入時，先把摘要做好。查詢時，先看摘要，需要時才讀原文。**

### 三層的定義（來自 OpenViking）

- **L0（abstract）**：約 100 token 的一句話。用來快速篩選和向量搜尋。
- **L1（overview）**：約 2k token 的重點。用來導覽和 rerank。
- **L2（detail）**：完整的原始內容。需要時才載入。

### 做法 A：chunk 層級（整理者的想法，不是 OpenViking 原本的做法）

OpenViking 的 L0 和 L1 是掛在目錄上。這裡是把同樣的概念，搬到每個 chunk 上。

- **L0 幫助 similar search**：L0 短而集中，拿它做 embedding 和全文索引，比對起來更準。
- **L1 幫助 rerank**：LLM 只讀候選的 L1，不用讀原文，就能判斷哪幾個最相關。
- **L2 是最後的證據**：答案一律根據 L2。

流程：
- Step 1（寫入）：chunk 前面先加上下文（文件標題、章節、日期），這就是 contextualization。
- Step 2：請 LLM 產出 L0 和 L1。
- Step 3（存放）：L0 做 embedding 和全文索引。L1 存成文字欄位。L2 存原文。
- Step 4（查詢）：query 搜 L0，取前 50 個候選。
- Step 5（Rerank）：LLM 讀這 50 個的 L1，選出前 5 個。
- Step 6（回答）：載入這 5 個的 L2，交給 LLM 回答。

小例子：
- 原文：一大段法說會記錄。
- L0：「台積電 2026 Q3 法說會：CoWoS 產能仍吃緊。」
- L1：重點、出現的 entity、時間、適合回答什麼問題。
- L2：原始 chunk。

和 SAG 的關係：SAG 的 event 很像 L0。它在簡短的 event 文字上檢索，找到後才回傳對應的原始 chunk 當證據。所以 SAG 已經有 L0 和 L2。做法 A 是補上 L1，並加上 contextualization。如果用 SAG，寫入時已經有一次 LLM 呼叫，L0 和 L1 可以放在同一次呼叫裡產生（**建議**，需實測）。

可選項（依情況決定，沒有固定答案）：
- L0 做 embedding 時，只用 L0，或 L0 和原文各做一份向量。
- 是否在四張表裡另加「摘要層」欄位，或維持獨立一節。

風險與對策：
- 摘要可能漏掉精確的數字和名詞。對策：原文也留一份 BM25 索引。
- 摘要可能有錯。對策：L0 和 L1 只用來找和排序，答案根據 L2。
- 寫入成本增加。對策：合併進同一次 LLM 呼叫。

### 做法 B：OpenViking 目錄層級

OpenViking 是 ByteDance 開源的 context database（給 AI agent 用的上下文資料庫）。它用虛擬檔案系統（`viking://` 路徑）組織資料。

流程：
- Step 1：資料依結構放進不同的資料夾和檔案。
- Step 2：LLM 為每個目錄產生 L0 和 L1。最上層最後產生，提供整個專案的概覽。
- Step 3：存成 catalog 設計：`.abstract.md`（L0）和 `.overview.md`（L1）。文件註明不要手動編輯。
- Step 4：為 abstract、overview、detail 各層級建向量索引。
- Step 5（後續動作）：L0 用於快速篩選和向量搜尋。L1 用於導覽和 rerank。L2 按需載入。

目錄範例：

```
my_project/
├── .abstract.md   ← 整個專案的一句話（L0）
├── .overview.md   ← 整個專案的重點（L1）
└── docs/
    ├── .abstract.md   ← docs 的一句話
    ├── .overview.md   ← docs 的重點
    └── auth.md        ← 原文（L2）
```

**未查證：** 資料夾結構是由系統自動切分和分類，還是沿用原本資料的結構，我沒有查到明確說明。

### OpenViking 的檢索：directory recursive retrieval

它像 path 檢索，但不是用路徑名稱做精準比對，而是用向量分數引導它沿著路徑往下走。

- Step 1：分析 query 的意圖。
- Step 2：用全域向量搜尋，找出分數最高的起始目錄。找的是資料夾，不是段落。
- Step 3：進到那個目錄再搜一次，並遞迴往子目錄鑽。
- Step 4：把結果合併排序，並保留走過的路徑。

小例子：
- 輸入：「OAuth token refresh」。
- 流程：`docs/` 的 L0 分數低，略過 → `docs/auth/` 分數高，進入 → 找到 `oauth.md`。
- 輸出：回傳 `oauth.md`，並保留這條路徑，可以回頭看。

第三方文章提到，往下鑽時節點分數是自身相似度和父層分數各占一半（二手資料，請核對）。

提醒：有第三方分析指出，OpenViking 的 repo 有評估工具，但沒有公開比較資料，證明階層檢索一定比一般向量搜尋準。它的好處（省 token、可追蹤）有道理，「更準」還沒有公開證據。

### 比較：RAG chunk 和 OpenViking 檔案層

| 面向 | RAG chunk | OpenViking 檔案層 |
|---|---|---|
| 基本單位 | 切好的小段文字 | 檔案和目錄，保留原本的結構 |
| 結構 | 扁平，chunk 之間沒有上下層 | 樹狀，用 `viking://` 路徑表示 |
| 摘要 | 預設沒有 | 每個目錄自動產生 L0 和 L1 |
| 進入點 | query 向量去比對所有 chunk | 先找最相關的目錄，再往下鑽 |
| 結果 | 零散的片段 | 帶著上下文的檔案或目錄 |
| 除錯 | 像黑盒 | 保留檢索路徑，可以回頭看 |

### 比較：index.md、SQL catalog table、OpenViking

三者都是 catalog（目錄），差別在形式和用法。

| 面向 | index.md | SQL catalog table | OpenViking |
|---|---|---|---|
| 形式 | 一個檔案 | 一張 table | 每個目錄各有 `.abstract.md` 和 `.overview.md` |
| 層數 | 一層，扁平 | 一層，扁平 | 多層，樹狀 |
| 誰來用 | LLM 讀整份 | SQL 用精準條件查 | 向量分數引導，由上往下 |
| 更新 | LLM 或程式寫入時更新 | 程式寫入時更新 | 系統自動產生 |
| 規模 | 變大會塞爆 context | 可放很多筆 | 分散在各層，只讀走到的那幾層 |

OpenViking 和 index.md 的最大差別：index.md 是一份很長的清單，LLM 要整份讀。OpenViking 把清單拆成很多小份，分散在每一層，所以省 token。

另外，OpenViking 底下仍有向量索引。目錄（catalog）負責結構和摘要，向量索引負責快速找。這和「catalog 與 DB index 是兩種 index」的說法一致。

### 比較：index.md + L0/L1 和 SQL table + catalog

| 面向 | index.md + L0/L1 | SQL table + catalog |
|---|---|---|
| 誰來找 | LLM 讀文字 | 資料庫引擎執行 |
| 擅長 | 語意判斷 | 精準條件：時間、tag、數量 |
| 規模 | 變大會塞爆 context | 有 DB index 時，大量資料也能查 |
| 成本 | 每次讀都耗 token | 查詢不耗 token，速度快 |
| 統計與排序 | 難 | 一行 SQL |
| 模糊問題 | 好 | 差，除非另外加 embedding |
| 彈性 | 自由文字，隨時可改 | 欄位固定，改結構要 migration |
| 可讀性 | 人和 LLM 都能直接讀 | 要靠查詢或工具 |

SQL 能分擔的是「查詢時的搜尋」，不能分擔「判斷意思」。兩邊在「寫入時產生目錄內容」都要靠 LLM。分工是：**SQL 負責縮小範圍，LLM 負責判斷意思。**

SAG 的進入點本來就包含 embedding（對 entity 和 event 向量做相似度搜尋）。它的 event 文字已經扮演 L0。它的結構路徑，LLM 重排的是 event（摘要），不是原文。

## 補充：同一張 table 放原文、L0、L1，並分層與 SQL catalog

以下是整理者的設計建議（不是某個系統的規定），用 Postgres 為例。

### 概念

把三種內容放在同一張 table 的同一列：
- **原文（L2）**：最後的證據。
- **摘要（L0）**：給 similar search（embedding 和全文索引）。
- **概覽（L1）**：給 rerank。

並且 table 可以分層：上層（parent）的列，放文件或章節的摘要；下層（child）的列，放 chunk。再用 SQL catalog 把各層整理起來，方便查和讀。

### 單表設計：每一列是一個節點

```sql
CREATE TABLE nodes (
  id            BIGINT PRIMARY KEY,
  parent_id     BIGINT REFERENCES nodes(id),  -- 上一層；最上層為 NULL
  root_id       BIGINT,                        -- 所屬文件，省去遞迴查詢
  node_type     TEXT,                          -- 'doc' / 'section' / 'chunk'
  title         TEXT,
  tag           TEXT,
  event_time    DATE,
  l0            TEXT,             -- 摘要，給 similar search
  l0_embedding  VECTOR(1024),     -- l0 的向量（pgvector）
  l1            TEXT,             -- 概覽，給 rerank
  l2            TEXT              -- 原文；很大時改放 l2_path 指向檔案
);

-- DB index：加速條件篩選和向量搜尋
CREATE INDEX idx_nodes_parent ON nodes (parent_id);
CREATE INDEX idx_nodes_root   ON nodes (root_id);
CREATE INDEX idx_nodes_time   ON nodes (event_time);
CREATE INDEX idx_nodes_vec    ON nodes USING hnsw (l0_embedding vector_cosine_ops);
```

### 分層：parent 和 child

兩種做法：

- **做法 1：同一張 table，用 `parent_id` 指向上一層（self-reference）。**
  - 優點：只有一套 index，層數不固定也能放。
  - 缺點：各層用不到的欄位會是空的。原文很大時會讓表變重，可把原文改放另一張 table 或檔案，用 `l2_path` 指過去。
- **做法 2：多張 table，各層一張（documents → sections → chunks），用外鍵連結。**
  - 優點：各層欄位乾淨。
  - 缺點：查詢要 join 比較多張表。

兩種都可以。依資料規模和層數決定，沒有固定答案。

這個 parent 結構，對應到 OpenViking 的目錄樹：上層節點的 L0 和 L1，就像目錄的 `.abstract.md` 和 `.overview.md`。

### 用 SQL catalog 整理

Catalog 可以是 view、materialized view，或自建 table。例如：把上層節點（doc 和 section）整理成一份目錄。

```sql
CREATE MATERIALIZED VIEW catalog_top AS
SELECT id, parent_id, node_type, title, tag, event_time, l0
FROM nodes
WHERE node_type IN ('doc', 'section');

-- 資料變了，再執行：
REFRESH MATERIALIZED VIEW catalog_top;
```

這份目錄有兩種用法：
- SQL 用條件直接查（時間、tag）。
- 需要時，整理成文字，交給 LLM 讀（像 index.md）。

記得區分：catalog 是「目錄」，DB index 是「加速用的附屬品」。上面的 `CREATE INDEX` 是 DB index，`catalog_top` 是 catalog。

### 查詢流程

- Step 1（SQL）：先在上層縮小範圍，例如用時間和 tag 篩出幾份文件。
- Step 2（embedding）：用 query 向量比對這些文件底下 chunk 的 L0，取前 20 筆。
- Step 3（Rerank）：LLM 只讀這 20 筆的 L1，選出前 5 筆。
- Step 4（回答）：載入這 5 筆的 L2，交給 LLM 回答。

```sql
-- Step 1：篩出文件
SELECT id FROM nodes
WHERE node_type = 'doc' AND event_time >= '2026-09-28' AND tag = '資料庫';

-- Step 2：在這些文件底下，用 L0 向量找最近的 20 筆 chunk
SELECT id, l1 FROM nodes
WHERE node_type = 'chunk' AND root_id IN (/* Step 1 的 id */)
ORDER BY l0_embedding <=> $1   -- $1 是 query 的向量；<=> 是 pgvector 的距離運算
LIMIT 20;
```

小例子：
- 輸入：「上個月有哪些資料庫筆記，和向量搜尋有關？」
- Step 1：SQL 篩出 12 份文件。不耗 token。
- Step 2：這 12 份底下共幾百個 chunk，用 L0 向量取前 20。
- Step 3：LLM 讀 20 份 L1，選出 5 份。
- 輸出：根據這 5 份的原文回答。

### 風險與對策

- 上層摘要不準，整棵子樹會被漏掉。對策：保留備援路徑，也可以直接搜所有 chunk 的 L0，不經過上層。
- 子層內容變了，上層的 L0 和 L1 要重新產生。OpenViking 是最上層最後產生。這裡也建議由下往上產生。
- SQL 篩選的品質，取決於寫入時填的欄位。漏標 tag 就查不到。對策：加 alias 對照表，並保留 embedding 和全文搜尋。
- 放進 table 後，不能像 index.md 那樣直接打開編輯。得到查詢能力，失去直接編輯的方便。

## 補充：Google Memory Bank 的 Fact / Understanding 分流，以及四種方法的對應

一句話：**寫入時先分類。資料依「更新規則」分成 Fact 和 Understanding，各放進適合的載體。**

### 查證狀態

- Google Memory Bank 的設計，來自使用者讀到的描述，沒有附原始連結。我沒有讀 Google 的原始文件。
- 「新資訊會和既有記憶整併，而不是只堆疊」這一點，有二手文章提到（見 Sources）。
- 其他內容（分辨方法、event log、prompt 標示、衝突排序、和四種方法的對應）是整理者的**建議**，不是 Google 的規定。
- GraphRAG 的細節沒有查證。本文第一部分比較的是 LightRAG，所以 graph 這一類以它為代表。

### Google 的設計（依使用者的描述）

名詞：
- **Fact（事實）**：只有一個正確答案、可以驗證的資料。例如「雇主是台積電」。
- **Understanding（理解）**：對使用者的印象或偏好。例如「偏好簡單、分步驟的學習方式」。
- **Synchronize（同步）**：資料一變，馬上更新。
- **Post-extraction（事後抽取）**：對話結束後，才用 LLM 從對話裡抽取。

| 面向 | Facts | Understanding | Multi-modal |
|---|---|---|---|
| 載體 | structural DB | vector store | 另外儲存 |
| 讀取時機 | session 開始前 | session 開始前 | 未提到 |
| 更新方式 | synchronize | post-extraction | post-extraction |
| 寫入條件 | 持續更新，可加時間 | 訊號夠強才寫入 | 未提到 |

### 為什麼分開（建議）

原因：兩種資料的更新規則不同。
- Fact：新值**取代**舊值。
- Understanding：新印象和舊印象**合併**。

混放的問題，小例子：
- 第 1 個月，使用者說：「我在 A 公司工作。」
- 第 6 個月，使用者說：「我換到 B 公司了。」

| 全部放哪裡 | 會發生什麼 |
|---|---|
| 全放 vector store | A 和 B 兩筆都被找到。向量庫只比「意思相近」，不知道哪筆最新。LLM 可能選到舊的。 |
| 全放 SQL | Fact 沒問題：`UPDATE` 後只剩一個答案。但偏好沒有固定欄位，說法又很多，也不能用意思搜尋。 |

### 怎麼分辨 Fact 和 Understanding（建議）

對每一筆資料，問三個問題：

1. 這個問題只有一個正確答案嗎？是 → Fact。不是 → Understanding。
2. 它可以驗證對錯嗎？可以 → Fact。只是印象或判斷 → Understanding。
3. 新資料進來時，是取代還是合併？取代 → Fact。合併 → Understanding。

| 句子 | 判斷 | 理由 |
|---|---|---|
| 「我在台積電工作。」 | Fact | 一個答案，可驗證，新值取代舊值 |
| 「我昨天買了一件襯衫。」 | Fact（事件） | 可驗證，有時間 |
| 「這個說明太長了，我看不完。」 | Understanding | 是印象，不能驗證對錯 |

灰色地帶：「我喜歡簡單的解釋。」使用者明確說出來，像 Fact。系統從行為推測出來，是 Understanding。

**建議**：不確定時，先放 Understanding，並保留原文。訊號夠強，再升級成 Fact。這樣分錯的代價較低。

### Fact 的存法：event log 和 current state（建議）

- **Event log（事件紀錄）**：每發生一件事，就追加一列。不修改舊的列。
- **Current state（當前狀態）**：每個東西只有一列，存最新的值。有新資料就覆蓋。

它像銀行的交易明細（event log）和帳戶餘額（current state）。餘額可以從明細算出來。明細不能從餘額還原。

小例子（衣服）：
- Step 1：追加事件。`2026-01 buy 衣服A`、`2026-03 give 衣服A`、`2026-05 buy 衣服B`。
- Step 2：用查詢算出「現在擁有什麼」。
- Step 3：輸出 `衣服B`。

```sql
-- Fact：event log（只追加）
CREATE TABLE fact_events (
  id          BIGSERIAL PRIMARY KEY,
  user_id     TEXT,
  action      TEXT,          -- 'buy' / 'give' ...
  item        TEXT,
  event_time  TIMESTAMPTZ,
  source      TEXT           -- 指回原文，補回抽取時丟掉的資訊
);

-- Fact：current state，由 event log 算出
CREATE VIEW owned_items AS
SELECT b.user_id, b.item
FROM fact_events b
WHERE b.action = 'buy'
  AND NOT EXISTS (
    SELECT 1 FROM fact_events g
    WHERE g.user_id = b.user_id AND g.item = b.item
      AND g.action = 'give' AND g.event_time > b.event_time
  );
```

查「某個時間點」的狀態：`b` 和 `g` 兩處都要加上 `event_time <= 該時間`。只加 `b` 會算錯。例如查 2 月：衣服A 的 `give` 在 3 月，如果 `g` 沒有限制時間，衣服A 會被誤判成已送出。

| 需求 | 選擇 |
|---|---|
| 要查歷史、要追蹤「為什麼變成這樣」 | Event log |
| 只要最新值，而且常讀 | Current state |
| 兩者都要 | Event log 為主，current state 由它算出（view 或 materialized view） |

### Fact 為什麼放 structural DB（使用者的觀察，我同意）

小例子：買了一件衣服，送給朋友，又買了另一件。

- 文字型方法（傳統 RAG、LLM wiki、graph）存的是「故事」。這三件事可能散落在不同 chunk 或頁面。每次查詢，都要重新讀完再推算最後的狀態。
- Structural DB 存的是「結果」。查詢時直接讀。

代價：抽取成欄位時，一定會丟資訊（不在欄位裡的內容）。對策：`source` 欄位加 event log，需要時回頭讀原文。

### Understanding 這一側：四種方法都能用（使用者的想法 + 整理者的對應）

Fact 固定放 structural DB。Understanding 沒有固定答案，依資料性質選。也可以混用，在同一個 Postgres 內做 SQL + pgvector。

| 方法 + 載體 | 強項 | 適合放的 Understanding | 弱點 |
|---|---|---|---|
| 傳統 RAG + vector store | 寫入便宜。模糊的語意找得到。 | 短句的偏好和印象，例如「偏好分步驟學習」 | 找不到精確名詞。不知道新舊（**建議**加 `event_time`）。舊印象會堆積。 |
| LLM wiki + text-based | 內容整理過，人可以讀、可以改。有 link。 | 少量、高密度的長期印象，例如一頁「使用者的學習風格」 | 頁數多了，index 會塞爆 context。不能精準統計。 |
| SAG + DB | 時間過濾、entity join、alias 展開。查詢時才建關係。 | 有時間、有 entity 的事件型印象，例如「最近常討論 pgvector」 | 不做 entity 去重，需要 alias 表。沒有 entity 的偏好句，join 接不起來。 |
| GraphRAG（或 LightRAG）+ graph | 多跳關係。人、專案、工具之間的關係。 | 關係複雜的 Understanding | 寫入和維護成本高。（細節未查證） |

### 和 SAG 的比較

SAG 把 event、entity、向量、全文都放在同一個 SQL DB。Fact 和 Understanding 不分類，都是 event。

| 面向 | Google 分流 | SAG |
|---|---|---|
| 載體 | SQL + vector store + 多模態另存 | 一個 SQL DB（含向量、全文） |
| 何時決定結構 | 寫入時分類 | 不分類。關係在查詢時用 JOIN 建 |
| 更新方式 | Fact 覆蓋（或 event log）。Understanding 整併。 | 只追加。不去重。 |
| 時間 | Fact 可加時間 | **建議**加 `event_time` |
| 主要對象 | 使用者的 memory | 文件知識 |
| 讀取時機 | session 開始前先讀 | 查詢時才建 |
| 風險 | 寫入時分錯類 | Fact 變動（買了又送）難處理。同名東西會混在一起。 |

不是二選一。**建議**（需實測）：同一個 Postgres。
- Fact：用 `fact_events` 加 current state view。
- Understanding：用 SAG 式的 event 表和 entity 表，加 pgvector 和 alias 表。

理由：SAG 的「只追加」適合 Understanding（事件摘要）。但它不適合 Fact 的「現在狀態」。

```sql
-- Understanding：SAG 式
CREATE TABLE u_events (
  id          BIGSERIAL PRIMARY KEY,
  user_id     TEXT,
  summary     TEXT,           -- 一句摘要，像 L0
  event_time  TIMESTAMPTZ,
  embedding   VECTOR(1024),
  source      TEXT
);
CREATE TABLE u_event_entity (event_id BIGINT, entity TEXT);
CREATE TABLE alias (alias TEXT PRIMARY KEY, canonical TEXT);
```

以上 SQL 是草稿，沒有執行過。「訊號夠強才寫入」的規則怎麼設計，本節沒有展開。

### 讀取流程：session 開始前

- Step 1：用 SQL 讀 Fact（current state）。
- Step 2：用目前的話題向量，搜尋 Understanding。
- Step 3：兩份結果用標題分開，放進 prompt。
- Step 4：衝突時，Fact 優先。（**建議**，未查證）

為什麼要標示：agent 只看得到 prompt 裡的文字。沒有標題，它分不出資料從哪一側來。

輸出範例：

```
Facts:
- employer: B（自 2026-06）
Understanding:
- 偏好簡單、分步驟的學習方式
- 近期常討論 pgvector
```

### 風險與對策

- 寫入時分錯類。對策：不確定先放 Understanding，留原文，訊號夠強再升級。
- Fact 抽取丟資訊。對策：`source` 欄位加 event log。
- Fact 和 Understanding 衝突。對策：prompt 標示來源，Fact 優先。
- 舊的 Understanding 過期。對策：事後整併（memory consolidation）。本節沒有展開。
- Multi-modal 另存。**建議**：圖片等內容另存，並產生 caption 或 OCR 文字，讓上面兩側能用文字指回它。

## 補充：從 Anthropic agent memory 文章可融入的想法

來源：Anthropic「The components of agent memory」（2026-11-06）。文章的證據是 Anthropic 用 Claude 和自己的資料測的。下面每一項的「可用在哪裡」是整理者的**建議**，沒有實測過。

### 1. 時間軸多一格：離線批次

- 文章的依據：dreaming 在工作之外的時間，重新讀紀錄，改錯、整理。它的輸出不一定馬上可用。
- 目前表上只有「寫入時」和「查詢時」（SAG）。dreaming 是第三種：**離線批次**。
- 可用在哪裡：L0 和 L1 不一定要在寫入時一次做完。可以寫入時先做簡版，再用離線批次補強和校對。
- 取捨：離線整理要花運算，輸出也不是立刻可用。

### 2. 用原文校對摘要

- 文章的依據：筆記是會話中憑當下判斷寫的，可能一開始就錯。dreaming 拿 transcript 當標準答案，檢查並改正筆記。有一個遊戲的例子：錯的地標筆記讓 agent 一直失敗，改正後才走對路。
- 可用在哪裡：對應「摘要可能有錯」的風險。可以定期把 L0 和 L1 對照 L2 重驗，發現不一致就改寫。
- 原則：不要只壓縮，不校對。

### 3. 什麼時候 wiki 才有用

- 文章的依據：在合併文件的測試中，需要綜合多份文件的題目，用 wiki 得 87%，只用搜尋得 73%。如果答案在單一文件裡就查得到，wiki 沒有明顯好處。
- 可用在哪裡：這可以當作「怎麼選」的判準。
  - 問題常需要綜合多份文件、做判斷或算術：值得建 wiki 或摘要層。
  - 問題多半是單一文件查找：搜尋加 rerank 就夠。
- wiki 加搜尋並用，效果比單用 wiki 好。

### 4. 摘要不要比原文還長

- 文章的依據：有一個例子，10 份文件共 115 KB，產生的 wiki 有 203 KB，是原文的 1.77 倍，有些頁面沒有 link。
- 可用在哪裡：L1 不應該比 L2 長。L0 約 100 token，L1 約 2k token，要有上限。
- 檢查方法：定期比較摘要總量和原文總量。

### 5. 多個寫入者不要寫同一列

- 文章的依據：四個 agent 同時寫同一張共用表，互相覆蓋，57 項事實只保住 41 項。改成每份合約一頁、由一個 agent 負責，57 項全部保住。
- 可用在哪裡：table 設計時，一個來源對應一列（或一頁）。避免多個程序同時更新同一列。
- 對應「同一張 table」那一節：一份文件、一個 chunk，各自是一個節點。

### 6. 常駐層要小，細節往下放

- 文章的依據：常駐層每次會話都耗 token，錯誤的筆記還會進入之後每一次會話。所以常駐層放索引，細節放在下層並留連結。Claude Code 只載入 MEMORY.md 的前 200 行或 25 KB。
- 可用在哪裡：對應 L0 和 `catalog_top`。如果要把摘要放進 prompt，設定硬上限，只放索引，不放細節。
- 注意：OpenViking 的 L0 是按需讀取，這裡的常駐層是每次都載入，兩者用途不同。

### 7. 告訴模型用途，少規定寫法

- 文章的依據：只告訴模型「有一個記憶資料夾」，較強的模型就能用得好。如果規定「只記失敗」，較強的模型的收益損失較大（最多 0.234），較舊的 Sonnet 4.6 只損失 0.020。較舊的模型則需要更明確的引導。
- 可用在哪裡：產生 L0 和 L1 的 prompt，寫明用途：L0 給 similar search，L1 給 rerank。不要死規定格式。
- 注意：換成較弱的模型時，可能需要更明確的步驟。

## Sources

- [SAG: SQL-Retrieval Augmented Generation with Query-Time Dynamic Hyperedges (arXiv)](https://arxiv.org/abs/2606.15971)
- [SAG GitHub (Zleap-AI)](https://github.com/Zleap-AI/SAG)
- [OpenViking context layers](https://www.mintlify.com/volcengine/OpenViking/concepts/context-layers)
- [OpenViking GitHub](https://github.com/stone16/OpenViking)
- [OpenViking 介紹（apidog）](https://apidog.com/blog/openviking/)
- [OpenViking 分析（zby.github.io）](https://zby.github.io/commonplace/notes/related-systems/openviking)
- [OpenViking 評論（besthub）](https://www.besthub.dev/articles/is-openviking-s-file-system-based-agent-memory-a-real-innovation-or-just-a-rag-facelift-0175835b40ff)
- [AI Agent Memory Systems Comparison（Lyzr，提到 Memory Bank 會整併新舊記憶）](https://www.lyzr.ai/blog/ai-agent-memory-systems-comparison/)
- [What Is Agent Memory?（Vectorize，提到混放記憶會分不出事實與整合後的知識）](https://vectorize.io/what-is-agent-memory)
- [Anthropic: The components of agent memory（原文；我無法直接打開）](https://www.anthropic.com/research/components-of-agent-memory)
- [The Components of Agent Memory（agientry，近乎完整的轉載，我實際讀的版本）](https://agientry.com/en/articles/anthropic-components-of-agent-memory)
