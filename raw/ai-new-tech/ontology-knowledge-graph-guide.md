---
source_project: AI new tech & studies
source_file: claude/Ontology 與 Knowledge Graph 指南
title: Ontology 與 Knowledge Graph 指南
first_exported: 2026-11-18
updated: 2026-11-18
---
# Ontology 與 Knowledge Graph 指南

> 目標：用 Ontology 當標準，讓 LLM 從文件抽出 entity 和 relation，建成 Knowledge Graph。
> 狀態：學習中。下一個要學的是 GraphRAG（一個問題進來，怎麼決定走 Graph 還是 RAG，並合併結果）。

---

## 1. 核心概念：Ontology 和 Graph 差在哪裡

- **Ontology（本體）**：一份規格。它定義「有哪些類型的東西」和「類型之間允許有哪些關係」。
- **Knowledge Graph（知識圖譜）**：真實資料。用節點（node）和邊（edge）存放。

一句話：Ontology 規定哪些 entity 和 relation 可以存在，Graph 存放真正存在的那些。

注意：Ontology 不是「產生」entity，是「規定」entity 可以長什麼樣子。

**類比**

| | 資料庫 / 程式 | 知識圖譜 |
|---|---|---|
| 規格 | schema / class 定義 | Ontology |
| 真實資料 | rows / objects | Graph |

**哪裡不一樣**：一般 schema 只負責檢查格式。Ontology 還帶有語意，系統可以靠它推出資料裡沒寫出來的事。例如定義了「Engineer 是 Employee 的一種」，系統就知道 Engineer 也是 Employee。

**小例子**

Ontology：
- 類型：`Person`、`Company`
- 關係：`works_at`，只能從 `Person` 指向 `Company`

輸入兩筆資料：
- `Alice works_at TSMC`：合法，存進 Graph。
- `Alice works_at Bob`：Bob 是 `Person`，不是 `Company`，不合法，被擋下。

---

## 2. 為什麼需要 Ontology

沒有標準，LLM 每次抽取都會用不同的名字。Graph 會變得很亂，查不到東西。

**小例子**

兩份文件，內容是同一件事：
- 文件 A：「台積電僱用王小明」
- 文件 B：「Wang Xiaoming works for TSMC」

沒有 ontology：LLM 可能抽出 `台積電 —employs→ 王小明` 和 `Wang Xiaoming —works_for→ TSMC`。Graph 有 4 個節點和 2 種關係名。查「誰在 TSMC 工作」，一條也查不到。

有 ontology：類型只有 `Person`、`Company`，關係只有 `works_at`。LLM 兩次都抽出 `(王小明: Person) —works_at→ (TSMC: Company)`。類型和關係一致，下一步才能合併。

---

## 3. 抽取循環與 Ontology 的位置

現在的主流做法是：給 LLM 一個標準，然後反覆抽取、檢查、合併。這個「標準」就是 ontology。

- Step 1：把 ontology 放進 prompt，當作抽取的標準。
- Step 2：LLM 從每一段文件抽出 entity 和 relation。
- Step 3：用 ontology 檢查結果，不合法的退回重抽。
- Step 4：合併重複的 entity（entity resolution）。
- Step 5：寫入 Graph。

Ontology 主要用在 Step 1 和 Step 3。Ontology 是整個循環的標準，不是整個循環本身。

---

## 4. Entity Resolution（實體消歧合併）

Entity resolution 是判斷兩個名字是不是同一個東西，是的話就合成一個節點。

文件沒有統一的 ID。同一家公司在不同文件裡可能寫成不同名字。不合併，Graph 裡就會有好幾個節點代表同一個東西。

**流程**

- Step 1：按 ontology 的類型分組。只比較同類型的 entity。
- Step 2：快速篩選。用文字相似度或 embedding 找出「可能相同」的配對。
- Step 3：判斷。對沒把握的配對，把上下文給 LLM 問：「這兩個是同一個嗎？」
- Step 4：合併。選一個標準名稱（canonical name），其他名字存成別名（alias），原本指向舊節點的邊全部改指向新節點。

**小例子**

輸入 4 個節點：`台積電`（Company）、`TSMC`（Company）、`Taiwan Semiconductor Manufacturing Co.`（Company）、`王小明`（Person）。

- Step 1：3 個 Company 分在一組，`王小明` 不參與比較。
- Step 2：3 個名字被標為可能相同。
- Step 3：LLM 看到三者上下文都在講同一家新竹的晶圓代工廠，判斷相同。
- Step 4：輸出 1 個節點，標準名稱 `TSMC`，別名 `[台積電, Taiwan Semiconductor Manufacturing Co.]`。原本 `王小明 —works_at→ 台積電` 的邊，現在指向 `TSMC`。

**類比**：像手機通訊錄的「合併重複聯絡人」。

**哪裡不一樣**：通訊錄有電話號碼這種硬指標可以對。文件裡的 entity 沒有唯一 ID，只能靠名字和上下文猜。猜錯會把兩個不同的人（例如兩個都叫王小明的同事）合成一個，而且事後很難發現。

Ontology 在這裡的作用：讓比較範圍變小。`Person` 不會被拿去跟 `Company` 合併。

---

## 5. Ontology 怎麼建立

有兩種建法：

- **Top-down（由上而下）**：人先寫好 ontology，再用它去抽取資料。
- **Bottom-up（由下而上）**：先讓 LLM 讀文件，提出它看到的類型和關係，再整理成 ontology。

主流做法是兩者混合：LLM 提案，人審核定案。

**為什麼需要人**：只有你知道這個系統之後要回答什麼問題。LLM 只能看到文件裡有什麼，不知道哪些對你重要。

**流程**

- Step 1：從文件中取樣，不用全部讀。全部放進去通常超過 context 長度上限，也沒必要，因為類型會一直重複出現。
- Step 2：LLM 對每一批樣本提出「候選類型」和「候選關係」。
- Step 3：把候選合併。這跟 entity resolution 是同一個問題，只是對象從 entity 換成類型。
- Step 4：人審核。刪除、改名、合併、補上限制。
- Step 5：定案成 ontology v1，放進抽取循環。之後 LLM 發現新類型，只標記起來等人審核，不自動加入。

**小例子**

LLM 讀完 3 批 HR 文件，提案：
- 類型：`Employee`、`Staff`、`Worker`、`Company`、`Dept`、`Department`
- 關係：`works_at`、`employed_by`、`belongs_to`

人審核後，ontology v1：
- 類型：`Employee`、`Company`、`Department`
- 關係：`works_at`（`Employee` → `Company`）、`belongs_to`（`Employee` → `Department`）

沒有人審核，`Employee`、`Staff`、`Worker` 會變成 3 個類型，同樣的混亂又回來了。

---

## 6. Ontology 實際的格式

實際上，ontology 是一份結構化的檔案，列出允許的類型、關係和限制。給 LLM 用時，最常見的寫法是 JSON Schema 或 Pydantic。

**為什麼用這種格式**：現在的 LLM API 支援 structured output（結構化輸出）。你給它一份 schema，它就只能回傳符合這份 schema 的 JSON。這份 schema 同時是抽取時的標準，和抽取後的檢查表。

**流程**

- Step 1：用 Pydantic 把 ontology 寫成程式碼。
- Step 2：把這份 schema 當作輸出格式，交給 LLM。
- Step 3：LLM 讀文件，回傳 JSON。
- Step 4：Pydantic 驗證。不合格就報錯，重新抽取。

**小例子**

```python
from typing import Literal
from pydantic import BaseModel

class Entity(BaseModel):
    name: str
    type: Literal["Employee", "Company", "Department"]

class Relation(BaseModel):
    source: str
    relation: Literal["works_at", "belongs_to"]
    target: str

class Extraction(BaseModel):
    entities: list[Entity]
    relations: list[Relation]
```

輸入文件：「王小明在 TSMC 的 AI 部門工作」

LLM 回傳：

```json
{
  "entities": [
    {"name": "王小明", "type": "Employee"},
    {"name": "TSMC", "type": "Company"},
    {"name": "AI 部門", "type": "Department"}
  ],
  "relations": [
    {"source": "王小明", "relation": "works_at", "target": "TSMC"},
    {"source": "王小明", "relation": "belongs_to", "target": "AI 部門"}
  ]
}
```

如果 LLM 寫成 `"type": "Staff"`，Pydantic 會直接報錯，因為 `Staff` 不在允許清單裡。

**類比**：像一張有下拉選單的表單，LLM 只能從選單裡挑。

**哪裡不一樣**：下拉選單只能檢查每個欄位的值，不能檢查組合合不合理。上面的 schema 擋不住 `Company works_at Employee` 這種方向錯的關係。要擋這個，要另外寫 validator（自訂檢查函式）。

---

## 7. Ontology + Graph 對比 RAG：好處與壞處

**情境**：公司的 business rule 和 domain knowledge，原本放在一張一張表和文件裡，用 RAG 取回。現在改成先抽成 ontology 和 Graph，再查詢。這是另一種呈現知識的方式。

**兩個小修正**

- Graph 不是取代文件。它是把藏在文字裡的關係，先抽出來，存成明確的連線。
- Ontology 只能放「有哪些類型和關係」這類結構規則。像「滿 3 年才能請特休」這種條件規則，不會自動變成 Graph 的一部分。

**用同一個問題比較**

問題：「AI 部門主管的下屬，負責哪些專案？」

RAG 的做法：
- Step 1：把問題轉成 embedding（一串代表意思的數字）。
- Step 2：找出最相似的幾段文字。
- Step 3：LLM 讀這幾段文字，自己拼出答案。

Graph 的做法：
- Step 1：找到節點 `AI 部門`。
- Step 2：沿著邊走：`AI 部門 —head→ 主管 —manages→ 下屬 —works_on→ 專案`。
- Step 3：回傳走到的專案。

輸出：`[專案 A, 專案 B]`。

**好處**

| 好處 | 說明 |
|---|---|
| 多跳問題答得準 | 答案分散在好幾份文件時，RAG 容易漏掉其中一段。Graph 沿著邊走就能串起來。 |
| 可以追溯 | 每條邊可以記錄它來自哪份文件。答案錯了，容易查原因。 |
| 數量和一致性 | 一個名字只有一個節點，所以「這個部門有幾個人」可以精確計算。RAG 只看到幾段文字，數不準。 |

**壞處**

| 壞處 | 說明 |
|---|---|
| 建置成本高 | 要寫 ontology、跑抽取、做 entity resolution，還要人審核。 |
| 資訊會流失 | Ontology 決定哪些東西留下來。不符合類型的細節、表格裡的數字、例外條件，都可能被丟掉。 |
| 維護困難，錯誤難發現 | 文件更新後，Graph 要跟著更新。抽取錯誤或合併錯誤，會變成看起來很確定的錯誤事實，比 RAG 找不到資料更難發現。 |

**結論**：通常不是二選一。關係類的問題交給 Graph，細節和原文交給 RAG。把兩者合在一起用，就叫 GraphRAG。

---

## 8. 重點整理

| 名詞 | 白話 | 在循環中的位置 |
|---|---|---|
| Ontology | 規格：有哪些類型、哪些關係可以存在 | Step 1（標準）、Step 3（檢查） |
| Knowledge Graph | 真實資料：節點和邊 | Step 5（存放結果） |
| Entity resolution | 判斷兩個名字是不是同一個東西並合併 | Step 4 |
| Top-down / Bottom-up | 人先寫規格 / LLM 先提案 | 建立 ontology 的兩種方式 |
| Structured output | 強迫 LLM 只回傳符合 schema 的 JSON | 實作 Step 2、Step 3 |
| Graph vs RAG | Graph 擅長關係和數量，RAG 擅長原文細節 | 查詢階段，兩者可以合用 |

## 9. 下一步

學 GraphRAG：一個問題進來，系統怎麼決定走 Graph 還是走 RAG，並把兩邊的結果合在一起。
