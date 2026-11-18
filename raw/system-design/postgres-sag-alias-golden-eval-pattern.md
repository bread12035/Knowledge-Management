---
source_project: system design & code style
source_file: claude/postgres-sag-alias-golden-eval-pattern.md
title: 業界經典範例整合：Postgres-only 的 SAG 式知識檢索（Query-time Join + Alias 展開 + 時間過濾 + Golden Eval）
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Postgres-only 的 SAG 式知識檢索（Query-time Join + Alias 展開 + 時間過濾 + Golden Eval）

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。（2026-10-26）

## 這次合併了哪些概念

1. **rag-methods-comparison（SAG）**：每段文字變成一個 event 加一組 entity。關係不在寫入時建，查詢時才用 SQL join 串起來。
2. **rag-methods-comparison（建議：alias 表 + event_time 欄位）**：SAG 不做 entity 去重，所以要自己加 alias 對照表；時間用 WHERE 過濾。
3. **postgres-hub（Postgres 單一樞紐）**：event、entity、alias、向量、全文都放同一個 Postgres。
4. **structured-rag-golden-eval-hexagonal（Golden dataset + Port/Adapter）**：`EntityExtractor` 是 port；每次改規則先跑固定案例。

## 業界經典範例

- **企業搜尋（Glean、Notion AI Search）**：不先建全域 graph，而是查詢時結合關鍵字、語意、權限、時間來找資料。
- **Elasticsearch / OpenSearch 的 synonym filter**：同義詞表在查詢時展開（TSMC = 台積電）。
- **Supabase hybrid search**：同一個 Postgres 內做全文加向量。
- **Entity linking 的 alias table**：Wikidata 用 alias 欄位處理同一個東西的不同寫法。

## 使用場景

你做一個「投資研究筆記」問答。新聞有人寫 TSMC，有人寫台積電。你問：「台積電近況」。

- Step 1（Ingest）：每則新聞一次抽取，寫入 `events`（一句摘要 + `event_time`）和 `event_entity`（entity 列表）。新資料直接追加，不和舊資料比對。
- Step 2（Query 前處理）：從問題抽出 entity：`台積電`。用 `alias` 表展開成 `台積電, TSMC`。
- Step 3（Query-time join）：SQL 用 `JOIN event_entity` 找出共用這些 entity 的 event。依命中 entity 數量排序。
- Step 4（時間過濾）：若問「9 月以後」，加 `WHERE event_time >= '2026-09-01'`。
- Step 5（Golden eval）：改 alias 或排序規則前，先跑固定案例。結果變了就擋下改動。

輸入：「台積電近況」。輸出：兩則 event，一則寫 TSMC，一則寫台積電。

## 為什麼採用這些技術

- **Query-time join，而非寫入時建全域 graph**：寫入時每段獨立處理，成本低，不用和全部舊資料對齊。關係只在被問到時才算。
- **Alias 表，而非靠 LLM 去重**：SAG 不去重，是它的設計選擇，不是 bug。同名不同寫法由一張可讀、可改、可測的小表補上。確定性的事，不交給 LLM 猜。
- **event_time 欄位 + WHERE**：時間是精確條件。能用 SQL 查的，不用語意猜。
- **Postgres 單一樞紐**：資料量是幾萬筆等級。一個 DB，一個備份，不另養 graph DB。
- **Port/Adapter（`EntityExtractor`）**：正式環境用 LLM 抽 entity；測試用字典。核心邏輯不變，測試可重複。
- **Golden cases**：沒有 alias 會漏資料。這個失敗要被固定成測資，之後改規則才不會悄悄退步。

## 重點要解決的問題

1. 同一個東西有不同寫法（TSMC / 台積電），join 接不起來。解法：Alias 表。
2. 新資料不斷進來，全域 graph 難維護。解法：寫入只追加，關係查詢時才建。
3. 「最近」「9 月後」這類條件，向量搜尋不擅長。解法：`event_time` + WHERE。
4. 改規則後不知道有沒有壞掉。解法：Golden cases。
5. 問題裡沒有已知 entity 時，不亂回。解法：空結果，再交給向量或全文路徑補。

## 可執行範例（SQLite 模擬；四組 golden case 全部 PASS）

```python
import sqlite3
from collections import Counter

class EntityExtractor:                 # port: 正式環境換成 LLM；測試用字典
    def __init__(self, vocab): self.vocab = vocab
    def extract(self, text): return {v for v in self.vocab if v.lower() in text.lower()}

def init(db):
    db.executescript("""
    CREATE TABLE events(id INTEGER PRIMARY KEY, summary TEXT, event_time TEXT);
    CREATE TABLE event_entity(event_id INT, entity TEXT);
    CREATE TABLE alias(alias TEXT PRIMARY KEY, canonical TEXT);
    CREATE INDEX ix_ee ON event_entity(entity);""")

def ingest(db, ext, summary, t):       # 寫入：一段 = 一個 event + 一組 entity（不做去重）
    eid = db.execute("INSERT INTO events(summary,event_time) VALUES (?,?)", (summary, t)).lastrowid
    for e in ext.extract(summary): db.execute("INSERT INTO event_entity VALUES (?,?)", (eid, e))

def expand_alias(db, ents):            # 建議：查詢時展開 alias
    out = set(ents)
    for e in ents:
        r = db.execute("SELECT canonical FROM alias WHERE alias=?", (e,)).fetchone()
        if r: out.add(r[0])
        out |= {a for (a,) in db.execute("SELECT alias FROM alias WHERE canonical=?", (e,))}
    return out

def search(db, ext, question, since=None, use_alias=True, k=3):
    ents = ext.extract(question)
    if use_alias: ents = expand_alias(db, ents)
    if not ents: return []
    q = ",".join("?"*len(ents))        # 查詢時才 join：共用 entity 的 event 串起來
    sql = f"""SELECT e.id, e.summary, COUNT(*) FROM events e JOIN event_entity x ON x.event_id=e.id
              WHERE x.entity IN ({q}) {"AND e.event_time>=?" if since else ""}
              GROUP BY e.id ORDER BY COUNT(*) DESC, e.event_time DESC LIMIT {k}"""
    return [r[1] for r in db.execute(sql, [*ents, *([since] if since else [])])]

VOCAB = ["TSMC","台積電","CoWoS","Nvidia","產能"]
DOCS = [("TSMC 宣布 CoWoS 擴產", "2026-03-01"),
        ("台積電 法說會：CoWoS 產能吃緊", "2026-09-10"),
        ("Nvidia 追加 CoWoS 訂單", "2026-09-20"),
        ("無關新聞：咖啡漲價", "2026-09-21")]
GOLDEN = [  # (問題, since, use_alias, 預期)
  ("台積電 近況", None, False, {"台積電 法說會：CoWoS 產能吃緊"}),                 # 沒有 alias：漏掉 TSMC 那筆
  ("台積電 近況", None, True,  {"台積電 法說會：CoWoS 產能吃緊","TSMC 宣布 CoWoS 擴產"}),  # 有 alias：兩種寫法都找到
  ("台積電 近況", "2026-09-01", True, {"台積電 法說會：CoWoS 產能吃緊"}),            # 時間過濾
  ("今天天氣", None, True, set()),                                                  # 無 entity：不亂回
]
if __name__ == "__main__":
    for name, use_alias in [("with alias", True)]:
        pass
    db = sqlite3.connect(":memory:"); init(db); ext = EntityExtractor(VOCAB)
    db.execute("INSERT INTO alias VALUES ('台積電','TSMC')")
    for s,t in DOCS: ingest(db, ext, s, t)
    for q,since,ua,exp in GOLDEN:
        got = search(db, ext, q, since, ua)
        print("PASS" if set(got)==exp else "FAIL", q, since, ua, got)
```

輸出：

```
PASS 台積電 近況 None False ['台積電 法說會：CoWoS 產能吃緊']
PASS 台積電 近況 None True ['台積電 法說會：CoWoS 產能吃緊', 'TSMC 宣布 CoWoS 擴產']
PASS 台積電 近況 2026-09-01 True ['台積電 法說會：CoWoS 產能吃緊']
PASS 今天天氣 None True []
```

## 延伸一步

- 加向量與 BM25 找 seed event，再用 join 展開（這才是完整 SAG 流程）；兩條排名用 RRF 合併。
- 把 `EntityExtractor` 換成 LLM，golden dataset 要加入模糊案例。
- Alias 表可由 LLM 提議、人確認後才寫入（human-in-the-loop）。
