---
raw: raw/ai-new-tech/ontology-knowledge-graph-guide.md
raw_sha256: 71a077c04077f4dc4cec335d130234c09f1d48f8c00c2c304d2c398ad5342263
source: ai-new-tech
title: Ontology 與 Knowledge Graph 指南
generated: 2026-11-18
---
# Ontology 與 Knowledge Graph 指南（note）

## 一句話
Ontology 是規格（允許哪些類型與關係），Knowledge Graph 是資料；用 ontology 當 LLM 抽取與檢查的標準，加上 entity resolution，才能建出一致可查的圖。

## 主張
### §1 核心概念
- Ontology 定義有哪些類型的東西、類型之間允許哪些關係；Knowledge Graph 用節點與邊存放真實資料 {討論結論} (§1)
- Ontology 不產生 entity，而是規定 entity 可以長什麼樣子 {討論結論} (§1)
- Ontology 對應 schema / class 定義，Graph 對應 rows / objects；差別是 ontology 帶語意，可以推出沒寫出來的事（Engineer 是 Employee 的一種）{討論結論} (§1)

### §2 為什麼需要
- 沒有 ontology，LLM 每次抽取會用不同的名字與關係名，Graph 變亂、查不到東西 {討論結論} (§2)

### §3 抽取循環
- 主流做法：ontology 放進 prompt 當標準 → 抽取 → 用 ontology 檢查、不合法退回重抽 → entity resolution → 寫入 Graph {討論結論} (§3)
- Ontology 主要用在 Step 1（標準）與 Step 3（檢查），是循環的標準，不是循環本身 {討論結論} (§3)

### §4 Entity resolution
- 流程：按類型分組只比同類 → 文字相似度或 embedding 快速篩選 → 沒把握的交給 LLM 看上下文判斷 → 選 canonical name、其他存 alias、舊邊改指新節點 {討論結論} (§4)
- 文件中的 entity 沒有唯一 ID，只能靠名字和上下文猜；錯合併（兩個同名的人）事後很難發現 {討論結論} (§4)
- Ontology 讓比較範圍變小：Person 不會跟 Company 合併 {討論結論} (§4)

### §5 Ontology 怎麼建立
- Top-down 是人先寫 ontology；bottom-up 是 LLM 讀文件提案；主流是 LLM 提案、人審核定案 {討論結論} (§5)
- 需要人，因為只有人知道系統之後要回答什麼問題 {討論結論} (§5)
- 建立時取樣即可，不用讀全部文件，因為類型會一直重複出現 {討論結論} (§5)
- 合併候選類型與 entity resolution 是同一個問題，只是對象換成類型 {討論結論} (§5)
- 定案成 v1 後，LLM 發現的新類型只標記等人審核，不自動加入 {討論結論} (§5)

### §6 實際格式
- Ontology 給 LLM 用時，最常見寫成 JSON Schema 或 Pydantic，搭配 structured output {討論結論} (§6)
- 同一份 schema 同時是抽取時的標準與抽取後的檢查表 {討論結論} (§6)
- `Literal` 型別只檢查單一欄位的值，擋不住方向錯的關係（Company works_at Employee），要另寫 validator {討論結論} (§6)

### §7 Ontology + Graph vs RAG
- Graph 不取代文件，而是把藏在文字裡的關係抽出來存成明確的連線 {討論結論} (§7)
- Ontology 只放結構規則；「滿 3 年才能請特休」這類條件規則不會自動變成 Graph 的一部分 {討論結論} (§7)
- Graph 的好處：多跳問題答得準、每條邊可追溯來源、數量與一致性可精確計算 {討論結論} (§7)
- Graph 的壞處：建置成本高、不符合類型的細節會流失、抽取或合併錯誤會變成看起來很確定的錯誤事實 {討論結論} (§7)
- 通常不是二選一：關係類問題交給 Graph，細節和原文交給 RAG，合用即 GraphRAG {討論結論} (§7)

### §9 下一步
- 學習狀態：下一個要學 GraphRAG，即問題進來時如何決定走 Graph 或 RAG 並合併結果 {討論結論} (§9)

## 變更
- （首次產生）

## 候選連結
- 本 source：anthropic-agent-memory-guide（wiki 是另一種知識表示；organizer 合併重複 ↔ entity resolution；wiki 跨文件題 87% vs 73% ↔ Graph 多跳問題）
- system-design：資料庫 schema 與 constraint、正規化與唯一鍵、validator / domain model、資料去重、schema 演進與審核
