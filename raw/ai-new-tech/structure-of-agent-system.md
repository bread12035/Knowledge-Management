---
source_project: AI new tech & studies
source_file: Structure of agent system
title: Structure of agent system
first_exported: 2026-11-18
updated: 2026-11-18
---
# Agent System 技術參考文件

Oct 1, 2026 · @Ryan

## 1. 設計目標與原則

這份文件定義一套以檔案為中心的 agent system 骨架：任務可中斷後接續、記憶分層、token 成本可控，並能從單機檔案擴充到資料庫。它沿用 OpenAI 的 Tax AI 與 harness engineering 的檔案結構，入口檔改為 CLAUDE.md，且**不使用 worktree**。

**證據標記**：\[OpenAI\] 出自 OpenAI 文章或文件；\[報告\] 出自你 2026-10-01 整理的 token 成本研究報告；\[推論\] 本文件的設計建議，尚未驗證。

| # | 決策 | 做法 | 解決什麼 |
| --- | --- | --- | --- |
| 1 | 入口地圖 | CLAUDE.md 約 100 行，只放目錄與規則，細節放 docs/ | context 是稀缺資源，巨大的指令檔會過時、難以驗證 |
| 2 | 任務狀態 | 每個任務一份 EXEC\_PLAN.md | 中斷後只靠這份文件就能接續 |
| 3 | 記憶分層 | 任務記憶 / 任務結果 / 長期知識 / 失敗記憶 / 證據 | 不同壽命的資訊分開存放 |
| 4 | 不用 worktree | 單一工作目錄；每個任務有自己的 tasks/\<ID>/ 目錄；證據唯讀 | 簡化環境，代價見第 9 節 |
| 5 | 省 token | pass by reference、caveman、SKILL.state | 資料、輸出文字、狀態傳遞三種成本 |
| 6 | Scale-out | SQLite .db，再往上用 MCP 串外部 DB | 資料量與並行度成長 |
| 7 | Preprocess | knowledge/ 的 L0 到 L2 與 next.md，與主流程分開 | 任務之外整理進度與大資料，方便下一次任務 |

**核心原則**：agent 在執行時看不到的東西就等於不存在，所以規則、決策與狀態都要寫成檔案或資料表 \[OpenAI\]。

**名詞速查**

| 名詞 | 一句話解釋 |
| --- | --- |
| Harness | 包在模型外面的程式層，負責組 prompt、跑迴圈、執行動作、管理狀態 |
| CLAUDE.md | Claude Code 每次對話自動載入的專案說明檔，本文件把它當入口地圖 |
| Progressive disclosure | 漸進式揭露：先給小而穩定的入口，再教 agent 往哪裡找更多 |
| EXEC\_PLAN | Execution Plan，自成一體、隨時更新的任務計畫文件 |
| Eval | 用一組有標準答案的案例量測表現的測試 |
| Handle / DataRef | 指向大量資料的薄引用，prompt 只放它與有界預覽 |
| Pass by reference | 資料留在執行環境，prompt 只放引用；相對的是 pass by value，把資料全文放進 prompt |
| Caveman | 讓 agent 用極簡文體回覆以減少 output token 的 skill |
| SKILL.state | Google 論文提出的 runtime：每步只給模型規格、結構化狀態與最新觀察 |
| MCP | Model Context Protocol，讓 agent 以標準方式呼叫外部工具與資料來源 |
| LLM wiki | Karpathy 提出的模式：LLM 把原始資料編譯成可維護的 markdown wiki |
| Preprocess | 任務之外的整理階段：進度比對與大資料 ETL |
| L0 / L1 / L2 | 資料三層：原始、整理、摘要；與第 6 節的儲存階層 S1 到 S3 是不同概念 |
| ETL | Extract、Transform、Load：取出、轉換、載入 |
| Output style | Claude Code 的設定，改變回覆的文體，放在 .claude/output-styles/ |

## 2. 檔案結構與 CLAUDE.md 入口地圖

CLAUDE.md 只當約 100 行的目錄，細節放 docs/，任務狀態放 tasks/\<ID>/，讓 agent 只在需要時才往下讀。

```text
project/
├── CLAUDE.md                      入口地圖（約 100 行）
├── .claude/
│   ├── skills/
│   │   ├── pass-by-reference/SKILL.md   即 pass_by_reference.md
│   │   ├── skill-state/SKILL.md         即 skill.state.md
│   │   └── ...                    其他操作手冊
│   ├── output-styles/
│   │   └── caveman.md             極簡文體（內容見附錄 A）
│   └── agents/<name>.md           subagent 定義（選用）
├── docs/                          長期知識
│   ├── architecture/
│   ├── decisions/                 已做過的決策與理由（ADR）
│   └── failures/                  已知失敗模式的說明
├── knowledge/                     Preprocess 產物（衍生，可重建）
│   ├── l0/<source>/               原始層，不可變
│   ├── l1/<source>.db             整理層
│   ├── l2/<topic>.md              摘要層
│   ├── index.md                   L2 目錄，任務 agent 先讀
│   ├── log.md                     只追加的操作紀錄
│   └── next.md                    下一步與要反問的問題
├── preprocess/
│   ├── SCHEMA.md                  來源、頁面格式、lint 規則
│   └── etl/                       L0 到 L1 到 L2 的腳本
├── tasks/<TASK-ID>/               一個任務一個目錄
│   ├── task.yaml                  任務規格與驗收指令
│   ├── EXEC_PLAN.md               任務記憶（進度、決策、發現）
│   ├── state.json                 精簡狀態，給每一步與 subagent 用
│   └── RESULTS.md                 任務結果
├── evals/                         失敗記憶與成功定義
│   ├── datasets/
│   ├── suites/                    targeted 與 regression
│   └── graders/
├── evidence/<TASK-ID>/            任務用的唯讀快照，由 L0、L1 取出
└── sandbox/<TASK-ID>/             不進版控；放 data.db 等大資料
```

| 路徑 | 用途 | 誰寫 | 進版控 |
| --- | --- | --- | --- |
| CLAUDE.md | 入口地圖：先讀什麼、規則、去哪裡找 | 人與 agent，需審查 | 是 |
| docs/ | 長期知識，架構、決策、失敗模式 | agent 起草，人審查 | 是 |
| tasks/\<ID>/ | 單一任務的規格、計畫、狀態、結果 | agent | 是 |
| evals/ | 驗收與回歸測試 | agent 起草，人審查 grader | 是 |
| evidence/ | 任務用的唯讀快照，由 L0、L1 取出 | 流程匯出，不由 agent 改 | 視大小而定 |
| sandbox/ | 大資料與中間產物，pass by reference 用 | agent | 否 |
| .claude/skills/、.claude/output-styles/ | 操作手冊與文體設定，內容見附錄 A | 人與 agent，需審查 | 是 |
| knowledge/ | Preprocess 產物：L0、L1、L2、index、log、next | Preprocess，不手改 | L2、index、next 進；L0、L1 視大小而定 |
| preprocess/ | Preprocess 的規則與 ETL 腳本 | 人與 agent，需審查 | 是 |

**CLAUDE.md 的寫法**：像目錄，不像百科。OpenAI 試過「一份超大的指令檔」，失敗原因是它會擠掉任務本身的 context、什麼都重要等於什麼都不重要、很快過時、也無法用機制檢查 \[OpenAI\]。範例骨架：

```markdown
# CLAUDE.md

## 開始任何任務前
1. 讀 knowledge/next.md 與 knowledge/index.md（若有）
2. 讀 tasks/<ID>/task.yaml，再讀 EXEC_PLAN.md 與 state.json
3. 沿用 docs/decisions/ 已有的決策，不要重新討論

## 規則
- 大資料放 sandbox/<ID>/，prompt 只放 handle 與預覽（skill: pass-by-reference）
- 多步驟任務與 subagent 交接用 state.json（skill: skill-state）
- 每個停點更新 EXEC_PLAN.md 的 Progress
- 修改 evals/graders/ 要在 RESULTS.md 單獨標註
- 證據不足或不適合自動處理時，標記 needs-human 並停止
- 不手改 knowledge/；它由 Preprocess 產生

## 去哪裡找
- 架構 → docs/architecture/
- 已知失敗模式 → docs/failures/
- 操作手冊 → .claude/skills/
```

**Skills 與 Output style 的角色**：`.claude/skills/` 底下每個 skill 是一個目錄與一份 SKILL.md；agent 一開始只看到名稱與描述，需要時才載入全文，這是 progressive disclosure 的第二層 \[OpenAI\]。所以 pass\_by\_reference.md 與 skill.state.md 在 Claude Code 裡要放成 `pass-by-reference/SKILL.md` 與 `skill-state/SKILL.md`，目錄名用小寫與連字號 \[推論\]。Output style 則是 `.claude/output-styles/` 底下的單一 markdown 檔，檔名成為樣式名稱，內容會直接加進 system prompt \[Claude Code 文件\]。分工是：CLAUDE.md 放「永遠成立的規則」，skill 放「做某類事的步驟」，output style 放「怎麼說話」。

**不用 worktree 的後果**：任務隔離改靠 tasks/\<ID>/ 目錄、sandbox/\<ID>/ 與唯讀的 evidence/，而不是每個任務一份獨立的程式碼 checkout \[推論\]。同時修改同一份程式碼的任務要排隊，不能並行。

## 3. EXEC\_PLAN.md：任務狀態

EXEC\_PLAN.md 是單一任務的工作記憶：自成一體、每個停點都更新，讓任何新 session 只靠它就能接續，不需要任何對話歷史 \[OpenAI\]。

**必備章節**（沿用 OpenAI cookbook 的 ExecPlan 做法）：

| 章節 | 內容 | 更新時機 |
| --- | --- | --- |
| Purpose | 這個任務要達成什麼、為什麼 | 開始時 |
| Progress | 帶時間戳的 checkbox，已完成與剩餘 | 每個停點 |
| Surprises & Discoveries | 執行中發現的非預期事實 | 發現當下 |
| Decision Log | 做了什麼決定、為什麼；中途改方向要寫原因 | 每次決策 |
| Acceptance | 可執行的驗收指令與預期輸出 | 開始時，改範圍時修訂 |
| Outcomes & Retrospective | 結果與回顧，結案前必填 | 結案時 |

**範例骨架**（任務：修正 parser 對空字串的 crash）：

```markdown
# EXEC_PLAN: parser 空字串 crash

本文件是 living document，必須隨進度更新，且自成一體。

## Purpose
parse("") 會拋 IndexError；改為回傳 None，不改公開 API。

## Progress
- [x] 2026-10-01 10:02 重現問題，tests/test_parser.py 失敗
- [ ] 修改 src/parser.py 的邊界判斷
- [ ] 跑 targeted eval 與 regression suite

## Surprises & Discoveries
- 空白字串 "   " 走同一條路徑，也會 crash（log: sandbox/T-17/run1.txt）

## Decision Log
- 2026-10-01：回傳 None 而非丟例外，理由：呼叫端已有 None 檢查

## Acceptance
pytest tests/test_parser.py 全綠；evals/suites/parser-regression 無退步

## Outcomes & Retrospective
（結案時填寫）
```

**與 state.json 的分工**：EXEC\_PLAN.md 給「人與冷啟動的 session」讀，內容完整、有敘述；state.json 給「每一步的 prompt 與 subagent」讀，只放當下需要的欄位（見第 5 節）。兩者不重複：決策與理由寫在 EXEC\_PLAN，state.json 只放決策的結論 \[推論\]。

**何時需要 ExecPlan**：複雜功能或大型重構才寫完整的；小改動用一兩行的輕量計畫就夠 \[OpenAI\]。

**結案後**：EXEC\_PLAN 保留在 tasks/\<ID>/ 當歷史；有價值的決策與失敗模式依第 4 節的升級規則抽出，寫進 docs/ 與 evals/。

## 4. Memory 五層

記憶依「壽命」與「用途」分成五層，每層有固定的載體、寫入時機與讀取方式；系統本身不依賴對話記憶，每個 session 從乾淨的 context 開始，需要的內容都從檔案或資料表讀回來 \[推論\]。

| 層 | 載體 | 保存什麼 | 寫入時機 | 壽命 |
| --- | --- | --- | --- | --- |
| 任務記憶 | tasks/\<ID>/EXEC\_PLAN.md、state.json | 進度、發現、決策與理由、當下狀態 | 每個停點 | 任務期間，結案後轉歷史 |
| 任務結果 | tasks/\<ID>/RESULTS.md、PR | 前後 eval 分數、regression 是否通過、尚存疑點 | 結案時 | 永久，當作歷史紀錄 |
| 長期知識 | docs/、.claude/skills/ | 架構、已做決策（ADR）、操作手冊、慣例 | 決策確定、流程穩定時 | 永久，需定期檢查是否過時 |
| 失敗記憶 | evals/（datasets、suites、graders）、docs/failures/ | 出過的錯與對應的測試案例；修好的問題變成永久的 regression 案例 | 每次修好一個失敗之後 | 永久，只增不減 |
| 證據 | evidence/、SQLite 或 DB 的唯讀資料 | 實際發生過什麼：trace、來源檔、原始輸出 | 由流程匯出 | 依資料政策，agent 不可改 |

**範例**：任務「修正 parser 對空字串的 crash」結案時，各層留下的東西：

- 任務記憶：EXEC\_PLAN 記下「空白字串也會 crash」的發現與「回傳 None」的決策。
- 任務結果：RESULTS 記下 targeted eval 由失敗轉通過，regression 無退步。
- 長期知識：「parser 對空輸入一律回傳 None」寫進 docs/decisions/，之後不再重新討論。
- 失敗記憶：空字串與空白字串各加入一個案例到 evals/suites/parser-regression。
- 證據：當初重現問題的 log 留在 evidence/，不被改動。

**升級規則**（把下層的內容往上層搬）：

1. EXEC\_PLAN 的 Decision Log 中，會影響未來任務的決策 → 抽出成 docs/decisions/ 的一份 ADR。
2. 任何被修好的失敗 → 至少一個 eval 案例進 regression suite。
3. 同一類失敗出現第二次 → 在 docs/failures/ 寫一份說明，並在 CLAUDE.md 加一行指標。
4. RESULTS 中標示「證據模糊」的項目 → 不自動升級，交人判斷。

**讀取原則**：agent 不一次讀完所有層。先讀 CLAUDE.md 與當前任務的任務記憶，需要時再依指標往長期知識、失敗記憶與證據走 \[OpenAI\]。

**與 Claude Code 內建記憶的關係**：Claude Code 的 subagent 有 `memory` 欄位，會載入 MEMORY.md 的前 200 行或 25KB，屬於「知識持久」而非「process 持久」\[報告\]。本設計把重要內容放在上表的檔案裡，內建記憶只當輔助，避免同一份知識存在兩處而分叉 \[推論\]。

## 5. 節省 token 的三個機制

三個機制各管一種成本：資料進 context 的成本交給 pass by reference，輸出文字量交給 caveman，跨步驟與跨 agent 的狀態傳遞交給 SKILL.state。三者不互相取代，可以疊加。以下數字與限定條件都來自你整理的研究報告 \[報告\]。

三個機制各有一份設定檔：`.claude/skills/pass-by-reference/SKILL.md`、`.claude/skills/skill-state/SKILL.md` 與 `.claude/output-styles/caveman.md`，內容見附錄 A。

### 5.1 Pass by reference

**做法**：資料留在執行環境，模型只看到變數名加上有界預覽（型別、真實長度、頭尾幾筆），再寫程式去操作完整資料；只有模型自己選擇印出的小結果才會進 context。出自 NVIDIA 的 NOOA 論文（六項 agent harness 能力之一）。

**流程範例**：

1. 工具把 50 萬列 CSV 下載到 `sandbox/<ID>/`，載入成 DataFrame 或寫進 `data.db`。
2. context 只放：`df = DataFrame(rows=500000, cols=12, head/tail 各 5 列)`。
3. 模型寫 `df.groupby('region').revenue.sum()`，只印出聚合結果。
4. 進入 context 的只有十幾行；原始資料從未被寫進 prompt cache。

**判準**：看「這份資料的完整內容有沒有變成 prompt 字元」，與用什麼查詢引擎無關。用 SQL 只取 10 列再貼進 prompt，仍然是 pass by value。

**證據與限定**：

- NOOA 在 SWE-bench Verified 以約 1.1M token 達到 82.2%，PI 用約 2.2M token 只有 78.2%；但這是整體 harness 的比較，pass by reference 只是因素之一，不能單獨歸功。
- 「資料不進 context 就沒有 cache write」是合理推論；論文沒有單獨拆出 cache write 的數字。
- 只給檔案路徑屬於弱的 reference：模型看不到型別，得自己從文字重建。
- MCP 工具的回傳結果會整包進 context，所以走 MCP 時，工具本身要回傳「handle + 預覽」，不是全文（見第 6 節）。
- 小模型較不守 code-as-action 的紀律：批次 bookkeeping 壓力測試通過率 70.8%，大模型 93.9%。

### 5.2 Caveman

**做法**：JuliusBrussee/caveman 這個 skill 讓 agent 用極簡文體回覆，code、指令、路徑與錯誤訊息保持原樣。範例：一段解釋 React 重複渲染原因的文字，由 69 token 壓到 19 token，診斷與修法都保留，只刪客套與連接詞。

**證據與限定**：

- 10 個一般 coding prompt，output token 平均由 1214 降到 294（約 65%）；最高 87%，最低 22%（原本就以 code 為主的任務降幅小）。
- 只縮 output；規則本身每輪約佔 1 到 1.5k input token，原本就簡短的工作可能反而虧。
- 「降低 request 次數」：找不到證據。
- 「subagent 表現下降」：沒有實測。Claude Code 的 subagent 用自己的 system prompt，所以 output-style 版對它本來就無效（fork 除外）。

**本設計的用法**：只用在主對話的敘述性回覆。subagent 的回報用結構化欄位，不靠文體壓縮。EXEC\_PLAN、RESULTS、docs/ 是給人與冷啟動 session 讀的，保持完整句子，不套 caveman \[推論\]。是否採用以美元計價的 cost model 實測為準，不只看 token 數。

### 5.3 SKILL.state

**做法**：Google（與 Purdue）的 SKILL.state 論文（arXiv 2608.26263）讓每一步的 prompt 固定只有三樣東西：不變的程序規格、結構化狀態、最新觀察。模型輸出推理、**state patch**（JSON 增量更新，key 設為 null 代表刪除）與動作；runtime 驗證 patch、合併、執行動作，推理過程丟棄。結果是每步 prompt 大小固定，累積 token 隨步數線性成長，而一般「歷史累加」是平方成長。

**流程範例**（論文的 warehouse 情境）：

1. 觀察：「Customer ordered item\_12」。
2. 模型查狀態，得知 item\_12 在 shelf\_42。
3. 輸出 patch `{"inventory": {"shelf_42": null}}` 與動作 `Ship item_12 shelf_42`。
4. runtime 合併 patch 並執行動作；本步的推理不再出現在後續 prompt。

**證據**：

- Warehouse T=100：SKILL.state 65,408 token，Stateful 基線 1,062,387 token（相差 16.2 倍）。
- InterCode CTF：pass@1 54.2%（ReAct 43.2%），總 token 減少 60.4%。
- 預算匹配對照（約 1,800 token）：滑動視窗 0.18、摘要上限 0.52、結構化 state 0.94。關鍵是「結構化狀態」，不是單純縮短。

**限定**：

- 論文只評測 single-agent。延伸到 multi-agent 需要處理並行寫入衝突，尚未測試，所以「在 subagent 下有效」是推論。
- Schema 是每個 domain 寫一次，不是每個任務一次；CTF 的 100 題共用同一個 5 欄位 schema。
- 失效情境：事先不知道 schema；某個早期觀察當時沒被認為重要而沒寫進 state；任務目標本身就是歷史（稽核、追溯）。
- 小模型的失敗有 68% 是更新時誤刪既有 key，所以 patch 要用合併語意，由 runtime 驗證，失敗就 rollback 重試。

**本設計的 state.json**（示意，非論文內容）：放在 `tasks/<ID>/state.json`，只放任務需要的欄位；大資料用 handle 引用。

```json
{
  "goal": "修正 parser 對空字串的 crash",
  "decided": ["不改公開 API", "測試放 tests/test_parser.py"],
  "refs": {"failing_log": "evidence/T-17/run3.txt", "df": "DataRef(sandbox/T-17/data.db, rows=52k)"},
  "open": ["空字串是否應回傳 None？"],
  "done_when": "pytest tests/test_parser.py 全綠"
}
```

放進 state：任務目標、已確定的決策、資料的 handle、未解問題、完成條件。不放：推理過程、完整 log、已被取代的假設 \[推論\]。

### 5.4 使用規則

1. 預設在主對話多輪完成。只有「大量輸出需隔離」「需限制工具」「自足且有明確輸入輸出契約」「子任務獨立可並行」才派 subagent。
2. 大資料落地到 sandbox，context 只放 handle、預覽與聚合結果。
3. 派 subagent 時用 state.json 交接，不貼對話歷史；回報也用結構化欄位。
4. 需要接續的 subagent 用 resume，不重開；歷史過長或 cache 已過期就重開並帶 state。
5. 啟動成本用精簡的 subagent description、`omitClaudeMd` 等設定壓低。
6. Caveman 只用在主對話敘述。

## 6. Scale-out：SQLite .db 與 MCP 串接資料庫

資料量與並行度成長時，第一步是把大資料放進 SQLite 的 .db 檔，更大規模再用 MCP 串外部資料庫；不論哪一層，agent 的 context 裡都只放 handle 與預覽。

&#91;embedded content: 儲存階層 · S1 到 S3，3 層\]

換層只改取資料的後端，不改 agent 的流程；文字類的記憶（CLAUDE.md、EXEC\_PLAN、docs/）一直留在檔案，不進資料庫，資料庫只放高量的結構化資料。

| 層 | 載體 | 適用情境 | 升級訊號 \[推論\] |
| --- | --- | --- | --- |
| S1 | sandbox/\<ID>/data.db（SQLite 單一檔案） | 單機、單一任務、資料可在本機處理 | 多個 session 要共用同一份資料 |
| S2 | 共用的 .db 檔，經 MCP 工具唯讀查詢 | 多個 session 或 agent 共用證據與失敗記憶 | 需要多機存取、細緻權限、並行寫入 |
| S3 | 外部資料庫（伺服器端），經 MCP 工具 | 大量資料、多人多機、需要稽核與權限 | 無，這已是最高一層 |

SQLite 是單一檔案、不需要伺服器；同一個檔案同一時間只能有一個寫入者（WAL 模式下讀者不會被擋）\[一般知識\]。所以並行寫入多了，就是往 S2 與 S3 移動的主要訊號。

**資料庫放什麼**（示意 \[推論\]）：

| 資料 | 對應的記憶層 | 表 |
| --- | --- | --- |
| trace、來源檔索引 | 證據 | evidence\_rows |
| 失敗發現與分組 | 失敗記憶 | findings |
| eval 案例與執行結果 | 失敗記憶、任務結果 | eval\_cases、eval\_runs |
| 任務索引與結案摘要 | 任務結果 | tasks |

**MCP 工具的設計規則** \[推論\]：

1. 回傳 handle、欄位名稱、列數與預覽，不回傳全文。原因是 MCP 工具的結果會整包進 context \[報告\]；判準與 5.1 相同：完整內容變成 prompt 字元，就是 pass by value。
2. 只提供唯讀查詢，強制 limit 與逾時，資料庫帳號本身也是唯讀角色。
3. 另提供 `fetch_to_sandbox(handle)`，把結果落地成 sandbox 裡的 .db，細部運算在 sandbox 用 SQL 或 pandas 做。
4. 寫入（失敗記憶、結果索引）走獨立工具，由流程帶 task ID 完成，不開放任意 SQL 寫入。
5. 敏感資料只開放該任務需要的範圍，必要時遮罩欄位。

## 7. Preprocess：任務之外的整理階段

Preprocess 是在 agent 修改核心邏輯之外另設的整理階段，做兩件事：比對過去完成的內容與目標，產出下一步與要反問的問題；把大資料整理成 L0、L1、L2 三層，讓下一次任務直接讀整理好的結果。

&#91;embedded content: Preprocess 流程 · 兩條整理線，1 個反問出口\]

任務 agent 開工時先讀 next.md 與 L2 的目錄，需要細節才往 L1、L0 下鑽；Preprocess 只寫 knowledge/，不碰程式碼。

**概念來源：LLM wiki**。Karpathy 提出的 LLM wiki 是一種模式，不是產品：raw/ 放不可變的原始資料，wiki/ 由 LLM 編譯並維護，CLAUDE.md 或 AGENTS.md 這類 schema 檔規範怎麼做；操作有 ingest（讀新資料、寫摘要、更新 index、記 log）、query 與 lint（健康檢查）\[LLM wiki 介紹，僅讀到搜尋摘要\]。重點是 LLM 先讀一次原始資料並編譯成結構化頁面，之後查詢讀 wiki，不必每次重讀原文。本設計沿用這個結構，再加上結構化的大資料。

| LLM wiki | 本設計 |
| --- | --- |
| raw/ 不可變的原始資料 | knowledge/l0/ |
| wiki/ 的頁面 | knowledge/l2/ 摘要頁，加上 knowledge/l1/ 的整理表 |
| index.md、log.md | knowledge/index.md、knowledge/log.md |
| schema 檔 | preprocess/SCHEMA.md（Preprocess 專用規則）；入口仍是 CLAUDE.md |
| ingest | ETL：L0 到 L1 到 L2 |
| query | 任務 agent 先讀 next.md 與 index.md，再讀 L2 |
| lint | 定期檢查：過時、矛盾、缺來源、孤立頁 |

### 7.1 工作一：進度整理與下一步

這一步把「已經做完的事」和「目標」放在一起看，回答三個問題：還缺什麼、下一步做什麼、有哪些資訊必須問 User。流程如下 \[推論\]：

1. 讀已完成的內容：各任務的 RESULTS.md、EXEC\_PLAN 的 Outcomes、eval 結果、docs/decisions/。
2. 讀目標：docs/ 裡的專案目標與 task.yaml 的驗收條件。若沒有目標文件，直接把「缺目標」列為要反問的問題。
3. 比對已完成與目標，列出缺口。
4. 產出 knowledge/next.md：已完成摘要、與目標的缺口、建議的下一個任務與理由、缺少的資訊。
5. 反問 User 時，每題附上建議答案，並依「對下一步的影響」排序（沿用 hakka-vibe 的 grill-me 做法）。

**next.md 範例**（示意）：

```markdown
# next.md（2026-10-01 產生）

## 已完成
- T-17 parser 空字串 crash：已修，regression 無退步

## 與目標的缺口
- 目標「parser 的邊界輸入都有 eval」：只覆蓋空字串，缺 None 與超長字串

## 建議下一步
- T-18 補 None 與超長字串的 eval（同類失敗，成本低）

## 需要反問 User
1. 超長字串的上限是多少？ 建議答案：沿用現有設定的 limit
```

### 7.2 工作二：大資料的 ETL 與 L0 到 L2

ETL 是 Extract、Transform、Load：從來源取出資料、轉換、再載入到目的地。這裡把它做成三層，讓下一次任務可以直接用快取，不必從原始資料重來。L0、L1、L2 是你定的分層，概念上接近「原始、整理、精煉」的三段式 \[一般知識\]。

| 層 | 內容 | 載體 | 能進 context 嗎 | 可由上一層重建嗎 |
| --- | --- | --- | --- | --- |
| L0 原始層 | 原樣落地的資料，附來源、時間、hash、欄位說明 | knowledge/l0/\<source>/（檔案或 SQLite .db） | 不能 | 不能，這是事實來源，不可變 |
| L1 整理層 | 清理、型別化、去重、關聯後的結構化資料 | knowledge/l1/\<source>.db（SQLite 表） | 不能，用 SQL 取聚合結果 | 能，由 L0 重跑 |
| L2 摘要層 | 聚合指標、LLM 寫的摘要頁、索引 | knowledge/l2/\<topic>.md、index.md | 能，頁面小而有界 | 能，由 L1 重算 |

**流程範例**（客戶訂單，50 萬列 CSV）：

1. Extract：CSV 以 pass by reference 載入 SQLite，原樣寫入 L0，記錄 hash 與欄位；prompt 只收 handle 與預覽。
2. Transform：用 SQL 或 pandas 清理型別、去重、關聯產品表，結果寫入 L1。
3. Load 與摘要：算出聚合（各區域營收、異常筆數），寫成 L2 摘要頁；LLM 只讀聚合結果與有界樣本，負責摘要與解讀，並在頁面標明引用的 L1 表與查詢。
4. 更新 knowledge/index.md（每頁一行摘要），在 knowledge/log.md 追加一筆紀錄。

**L2 頁面範例**（示意）：

```markdown
---
source: orders-2026-09
l0: knowledge/l0/orders-2026-09/（hash: <sha256>）
l1: knowledge/l1/orders.db 的 orders_clean
generated: 2026-10-01
---
# 訂單摘要（示意）
- 總筆數：500000
- 各區域營收：見 L1 的 revenue_by_region
- 異常筆數與判斷規則：見 L1 的 anomalies
```

**快取與失效**：下一次任務依 L2、L1、L0 的順序讀取，夠用就停。L0 的 hash 改變，對應的 L1 與 L2 就失效並重跑；沒變就直接用。L2 頁面的來源引用與產生時間，讓 agent 能自己判斷是否過期 \[推論\]。

**與第 6 節的關係**：L1 預設是 SQLite 的 .db；規模變大時，L1 可以搬到共用資料庫並經 MCP 查詢，L2 仍然是 md 檔。

### 7.3 何時執行

| 時機 | 做什麼 | 產出 |
| --- | --- | --- |
| 任務結案後 | 把 RESULTS 與新決策整理進 L2，把該升級的內容寫成 docs 提案，更新 next.md | next.md、log.md |
| 新資料來源到達 | ingest：L0 到 L1 到 L2 | knowledge/ 各層、index.md |
| 開始新任務前 | next.md 已過期就重新產生 | next.md |
| 定期，或資料變動後 | lint：過時頁、矛盾、缺來源、孤立頁、index 與檔案不一致 | 檢查結果寫入 log.md |

頻率是我的建議 \[推論\]；LLM wiki 的做法也是定期做健康檢查，所以這一步建議固定排程。

### 7.4 規則

1. L0 不可變；任何修正都只寫在 L1。
2. Preprocess 只寫 knowledge/ 與 next.md；不改程式碼、evals、docs。需要改的地方寫進 next.md 的建議，由人或下一個任務決定。
3. 能用程式做的不用 LLM：ETL 用腳本；LLM 只做摘要、缺口分析與反問。
4. LLM 讀的是聚合結果與有界樣本，不是 L0 全文（pass by reference，見第 5 節）。
5. 每個 L2 頁面都要有來源引用與產生時間。
6. 任務 agent 的讀取順序固定為 next.md、index.md、L2、L1、L0。
7. 不把 L1 的查詢結果全文貼回 prompt，否則就變成 pass by value。

## 8. 端到端流程範例

一個任務從建立到結案是一條固定路徑：每一步都把狀態寫回檔案，通過驗收才升級記憶，證據不足就停下來交給人。

&#91;embedded content: 任務流程 · 8 步，1 個判斷，1 個停止出口\]

「通過」指 targeted eval 通過，且 regression suite 沒有退步。下表說明各步寫進哪一層記憶 \[推論\]：

| 步驟 | 寫入或讀取 | 記憶層 |
| --- | --- | --- |
| 建立任務 | 寫 task.yaml、EXEC\_PLAN.md、state.json | 任務記憶 |
| 讀入口地圖 | 讀 CLAUDE.md，再依指標讀 docs/ 與 skills | 長期知識（讀） |
| 取證據 | 把 evidence/ 的資料載入 sandbox 的 .db，只留 handle 在 context | 證據（讀） |
| 重現問題 | 跑 targeted eval；失敗結果寫入 Progress 與 Surprises & Discoveries | 任務記憶 |
| 修改並驗證 | 改程式；決策寫入 Decision Log；更新 state.json | 任務記憶 |
| 寫入結果與升級 | 寫 RESULTS.md；決策進 docs/decisions/；失敗案例進 evals/ | 任務結果、長期知識、失敗記憶 |
| 結案 | 填 Outcomes & Retrospective，狀態標為完成 | 任務記憶 |
| needs-human | 在 EXEC\_PLAN 的 open 項目與 RESULTS 寫明缺什麼證據，然後停止 | 任務記憶、任務結果 |

**範例結局**：重現時 targeted eval 失敗；修改後通過，regression 無退步；結案時把「空輸入一律回傳 None」升級成一份 ADR，並在 evals/suites/parser-regression 新增空字串與空白字串兩個案例。

**有 Preprocess 產物時**：第 2、3 步改成先讀 knowledge/next.md 與 index.md，並從 L2、L1 取資料，不必從原始資料重新載入（第 7 節）。

## 9. 實作檢查清單、取捨與待決問題

最大的取捨是不用 worktree：環境變簡單，但修改同一份程式碼的任務只能排隊。下面依序列出實作清單、各決策的代價，以及尚未驗證的問題。

**實作檢查清單**

- [ ] 建立 CLAUDE.md（約 100 行）與 docs/ 目錄骨架
- [ ] 定義 task.yaml 欄位與 EXEC\_PLAN.md 範本
- [ ] 定義 state.json schema（每個 domain 一次）；patch 用合併語意，由 runtime 驗證，失敗就 rollback
- [ ] 建立 sandbox/\<ID>/ 與 DataRef 預覽格式
- [ ] 建立 evals/ 骨架；grader 的改動在 RESULTS.md 單獨標註
- [ ] 把 evidence/ 設為唯讀（檔案權限或 DB 唯讀角色）
- [ ] 結案時執行升級規則檢查（決策 → docs、失敗 → evals）
- [ ] 建立以美元計價的 cost model，區分 cache write 與 cache read
- [ ] 定義停止條件：證據不足時標記 needs-human 並停止

* [ ] 放入 `.claude/skills/pass-by-reference`、`skill-state` 與 `.claude/output-styles/caveman.md`（附錄 A），重啟 Claude Code 後確認載入
* [ ] 寫 preprocess/SCHEMA.md 與 ETL 腳本，先跑通一個資料來源的 L0 到 L2
* [ ] 設定 Preprocess 的觸發時機：結案後、新資料到達、定期 lint

**取捨**

| 決策 | 好處 | 代價 | 緩解 \[推論\] |
| --- | --- | --- | --- |
| 不用 worktree | 環境簡單，不必管理多份 checkout | 改動同一份程式碼的任務不能並行；失敗時沒有獨立分支可整個丟棄 | 改程式的任務排隊，唯讀任務才並行；用 git branch 與提交點回復 |
| CLAUDE.md 保持短 | 省 context、容易維護 | 依賴指標，agent 可能漏讀 | 用 lint 檢查連結與新鮮度 |
| state.json | 每步 prompt 固定大小 | schema 設計失誤會遺失資訊 | schema 事先測試；完整敘述另留在 EXEC\_PLAN |
| Pass by reference | 資料不進 context | agent 必須會寫程式；小模型紀律較差 | 提供預先寫好的查詢工具與範例 |
| agent 可改 grader | 能排除誤判的雜訊 | 可能為了通過而放寬標準 | grader 變更單獨標註，由人審查 |
| Preprocess 與 L0 到 L2 | 下一次任務直接讀整理好的結果，省 token 與時間 | 多一條要維護的流程；L2 可能過期或摘要有誤 | L2 帶來源引用與 hash；定期 lint；人審查 next.md |
| caveman 當 output style | 主對話的 output token 下降 | 規則本身每輪佔 input；不適合人要細讀的文件 | 只用在主對話；結果檔與 docs 不套用 |

**待決問題**（目前沒有證據）

- 多個 agent 並行寫同一份 state 時，衝突如何處理？SKILL.state 論文未測。
- Caveman 對 subagent 表現與 request 次數的實際影響。
- Resume 的 subagent 在 cache 過期後，實際要多付多少 cache write。
- Hakka vibe 的 results 中，cache write 的美元節省數字（需要你貼上）。
- 從 SQLite 換成外部 DB 的門檻：取決於並行寫入與資料量，要用自己的負載量測。

* Preprocess 自動產生的 next.md 與反問清單，品質怎麼驗證？目前沒有證據，建議前幾次都由人審查。
* L0 的 hash 改變就重跑 L1 與 L2，資料量大時重算成本多高？
* Hakka vibe 專案的 prompts 資料夾沒能讀到，附錄 A 的三份檔案是依研究報告與公開來源撰寫，需要和原檔對齊。

## 附錄 A：.claude 設定檔內容

以下三份檔案是可以直接放進專案的草稿。你提到的 Hakka vibe 專案生成的版本，我沒能讀到：該 repo 的 CLAUDE.md 說明 `.claude/skills/` 收錄的是 mattpocock/skills，而 prompts/ 等資料夾 GitHub 不允許自動讀取。所以內容依你的研究報告、NOOA 與 SKILL.state 論文的描述，以及公開的 caveman skill 撰寫；你貼上原檔後，我再對齊。

### A.1 .claude/skills/pass-by-reference/SKILL.md（即 pass\_by\_reference.md）

```markdown
---
name: pass-by-reference
description: 處理大資料（檔案、查詢結果、trace、log、CSV）時使用。資料留在 sandbox，prompt 只放 handle 與有界預覽，用程式取聚合結果。
---

# Pass by reference

## 判準
看「這份資料的完整內容有沒有變成 prompt 的字元」。有，就是 pass by value，要避免。
用 SQL 只取 10 列再貼進 prompt，仍然是 pass by value。

## 步驟
1. 資料量大到不該整份讀進 context 時，先落地到 sandbox/<TASK-ID>/（SQLite .db 或 DataFrame）。
2. context 只放 handle 與有界預覽：型別、真實長度、欄位，加上頭尾各 5 筆。
   例：df = DataFrame(rows=500000, cols=12, head/tail 各 5 列)
3. 用程式操作完整資料，只印聚合結果或有界樣本。
4. 查詢結果也先落地，不貼回 prompt。
5. handle 寫進 state.json 的 refs，不貼資料本文。

## 禁止
- cat 或 print 整個檔案、整張表
- SELECT * 且沒有 LIMIT
- 把 DataFrame 或查詢結果轉成文字再貼回對話

## 走 MCP 時
- 工具結果會整包進 context，所以工具要回傳 handle、欄位與預覽，不回傳全文。
- 需要細算時，用 fetch_to_sandbox(handle) 落地，再用 SQL 或 pandas。

## 提醒
- 只給檔案路徑是弱的 reference：沒有型別，要自己從文字重建。要附上預覽。
- 小模型較不守這個紀律：先確認預覽格式，再寫程式。
```

### A.2 .claude/skills/skill-state/SKILL.md（即 skill.state.md）

```markdown
---
name: skill-state
description: 多步驟任務或交接給 subagent 時使用。每一步只讀程序規格、tasks/<ID>/state.json 與最新觀察；用 patch 更新狀態；推理過程不留存。
---

# SKILL.state

## 每一步的輸入
1. 程序規格：本 skill 與 tasks/<ID>/task.yaml（不變）
2. 狀態：tasks/<ID>/state.json
3. 最新觀察：剛執行完的結果

## 每一步的輸出
- state patch：JSON 增量更新，key 設為 null 代表刪除
- 下一個動作
- 推理過程不寫進任何檔案

## Patch 規則
- 用合併語意，不整份覆寫
- 沒提到的 key 一律保留，不得誤刪
- 先驗證 schema，失敗就 rollback 並重試

## state.json 放什麼
任務目標、已確定的決策、資料的 handle、未解問題、完成條件。

## state.json 不放什麼
推理過程、完整 log、已被取代的假設。

## Schema
每個 domain 設計一次，不是每個任務一次。
範例欄位：goal、decided、refs、open、done_when。

## 不適用的情境
- 事先不知道 schema
- 早期觀察當時沒被認為重要，所以沒寫進 state
- 任務目標本身就是歷史（稽核、追溯）

## 交接給 subagent
- 派工：傳 state.json 路徑與 handle，不貼對話歷史
- 回報：結構化欄位 status、patch、refs、open
- 多個 subagent 不並行寫同一份 state.json；各寫自己的 patch 檔，由主 agent 合併
```

最後一條是設計建議：SKILL.state 論文只評測 single-agent，並行寫入衝突尚未測試 \[報告\]。

### A.3 .claude/output-styles/caveman.md

```markdown
---
name: caveman
description: 極簡文體。只用在主對話的敘述性回覆，減少 output token。code、指令、路徑、錯誤訊息保持原樣。
keep-coding-instructions: true
---

用最少的字回答，像聰明的穴居人。

## 規則
- 刪掉客套、冠詞、填充詞與重複的連接詞
- 可以用片段句，只要不產生歧義
- 診斷與修法要完整，不省略結論
- code、指令、路徑、識別字、錯誤訊息逐字保留
- 用使用者的語言回答
- 只輸出極簡版，不附一份正常版，也不寫「caveman mode on」

## 恢復正常文體的情況
- 安全警告與不可逆操作的確認
- 使用者表示沒看懂或重複提問
- 步驟順序太容易被誤解時

## 不套用
- EXEC_PLAN.md、RESULTS.md、docs/ 與 knowledge/ 裡的檔案：這些是給人與冷啟動 session 讀的，寫完整句子
- subagent 的回報：用結構化欄位，不靠文體壓縮
```

`keep-coding-instructions: true` 的原因：自訂 output style 預設會拿掉 Claude Code 內建的軟體工程指令，設為 true 才會保留 \[Claude Code 文件\]。新增檔案後要重啟 Claude Code，樣式才會出現在選單 \[第三方文件\]。規則前五條取自 caveman skill 的描述 \[公開來源\]；「恢復正常文體」與「不套用」是本設計的建議 \[推論\]。原版另有 lite、full、ultra 三種強度，這份只做單一強度。

## 來源

以下 OpenAI 頁面為本次開啟閱讀：[Building self-improving tax agents with Codex](https://openai.com/index/building-self-improving-tax-agents-with-codex/)、[Harness engineering](https://openai.com/index/harness-engineering/)。ExecPlan 做法見 [cookbook](https://developers.openai.com/cookbook/articles/codex_exec_plans)（僅讀到搜尋摘要）。

標記 \[報告\] 的內容取自你先前整理的研究報告，其來源為：[Caveman](https://github.com/JuliusBrussee/caveman)、[NVIDIA NOOA 論文](https://arxiv.org/abs/2607.20709) 與 [NVIDIA 部落格](https://developer.nvidia.com/blog/six-agent-harness-capabilities-for-higher-model-performance/)、[SKILL.state 論文](https://arxiv.org/abs/2608.26263)、[Claude Code subagents 文件](https://code.claude.com/docs/en/sub-agents)、[Hakka vibe](https://github.com/bread12035/hakka-vibe)。

本次新增的來源：LLM wiki 見 [starmorph 的介紹](https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide) 與 [Pebblous 的報告](https://blog.pebblous.ai/report/karpathy-llm-wiki/en/)（僅讀到搜尋摘要）；Claude Code 的 [output styles 文件](https://code.claude.com/docs/en/output-styles)（僅讀到搜尋摘要）；caveman 的規則參考 [skills.sh 的 caveman](https://www.skills.sh/microsoft/hve-core/caveman) 與 [skillselion 的描述](https://skillselion.com/skills/juliusbrussee/skills/caveman)（僅讀到搜尋摘要）；Hakka vibe 的 [CLAUDE.md](https://github.com/bread12035/hakka-vibe/blob/claude/mattpocock-skills-hakkavibe-pvs0ru/CLAUDE.md) 與 [CONTEXT.md](https://github.com/bread12035/hakka-vibe/blob/claude/mattpocock-skills-hakkavibe-pvs0ru/CONTEXT.md) 為本次開啟閱讀。
