---
source_project: AI new tech & studies
source_file: Hakka agent system reference
title: Hakka agent system reference
first_exported: 2026-11-18
updated: 2026-11-18
---
# Agent 省 token 與 subagent 設計：研究摘要報告

整理日期：2026-10-01
用途：放進 agent context，作為設計 harness 時的決策依據。
證據標記：✅ 來源直接支持　⚠️ 部分支持，需限定條件　❓ 找不到證據（屬推論或假設）

---

## 1. 一頁摘要

| # | 結論 | 判定 | 關鍵限定 |
|---|------|------|----------|
| 1 | Caveman 降低 output token；subagent 下可能降低表現 | ⚠️ | output token 降幅有實測（10 題平均 65%，範圍 22–87%）。「降低 requests 次數」❓ 找不到證據。「subagent 表現下降」❓ 無直接實測，只是合理假設 |
| 2 | 能多輪對話解決就不要用 subagent | ✅ | Claude Code 官方文件與論文方向一致；例外是「大量輸出隔離」與「獨立可並行」 |
| 3 | 資料放 sandbox，用 pandas/SQLite 取用，降低 cache write | ⚠️ | 機制成立且有 NOOA 的 token 對比；但 cache write 的美元數字在 Hakka results，本次未能讀取。前提是「只印預覽或聚合結果」 |
| 4 | SKILL.state 在 subagent 下降成本也提升表現，關鍵是 state JSON 設計 | ⚠️ | 論文只測 single-agent；subagent 是延伸，未驗證。「schema 設計是關鍵」✅ |
| 5 | Persistent subagent 降低每次啟動消耗 | ⚠️ | 「persistent」有三種不同機制（resume / memory / fork）；resume 會累積歷史，cache 有 TTL |

---

## 2. 名詞表

- **Harness**：包在模型外面的程式層，負責組 prompt、跑迴圈、執行動作、管理狀態。同一個模型換 harness，成績與成本可差很多。
- **Output style vs Skill**：Output style 是改寫 Claude Code 的 system prompt 區段；Skill 是按需載入的規則檔。兩者對 subagent 的影響不同（見 3.1）。
- **Subagent**：另開一個獨立 context window 的工作者，只回傳摘要給主 agent。
- **Fork**：繼承整段對話的 subagent（Claude Code 用 `/subtask` 啟動），system prompt、tools、model 與主 session 相同。
- **Pass by reference**：資料留在執行環境，prompt 只放變數名與有界預覽，模型寫 code 操作完整資料。**Pass by value**：資料全文變成 prompt 字元。
- **Cache write / Cache read**：prompt cache 寫入與命中的 input token，單價不同；Hakka 另依 TTL 分 1 小時與 5 分鐘兩種單價。
- **SKILL.state**：Google 論文提出的 runtime；每步只給模型「程序規格 + 結構化狀態 + 最新觀察」，推理過程用完即丟。
- **State patch**：模型輸出的 JSON 增量更新（key 設為 null 代表刪除），由 runtime 驗證後合併。
- **Sufficient statistic**：狀態足以代表「對未來決策有影響的全部過去」，所以可以丟掉歷史。

---

## 3. 各主題細節

### 3.1 Caveman output style

**是什麼**：JuliusBrussee/caveman，skill/plugin，支援 30+ 種 agent。讓 agent 用極簡文體回覆，code、指令、路徑、錯誤訊息保持原樣。另有獨立的 output-style 版本（carlosduplar），自稱約降 40% output token。

**流程與範例**：README 示範一段解釋 React 重複渲染原因的文字，由 69 token 壓到 19 token，診斷與修法（用 `useMemo`）都保留，只刪客套與連接詞。

**證據**
- 10 個一般 coding prompt，output token 平均 1214 → 294（−65%）。最高 87%（React error boundary），最低 22%（callback 改 async/await，因為本來就以 code 為主）。
- 維護者自己說明：只縮 output；skill 規則本身每輪約佔 1–1.5k input token；整個 session 的節省低於表格；原本就簡短的工作可能反而虧錢。
- 另有 proxy 組件縮減 input（54 次 benchmark 總計 −33.2%，其中 HTML 案例 +9.9% 反而變多）。

**關於你的兩個說法**
- 「降低 requests 次數」：所有來源只談 token，沒有提到 request 次數變少。❓
- 「subagent 可能降低表現」：Claude Code 文件指出 subagent 用自己的 system prompt，所以 **output style 版不會影響 subagent**（fork 除外）。Skill 版則靠載入規則；caveman 另附 `cavecrew-investigator/builder/reviewer` 壓縮版 subagent presets。表現下降的可能機制是「subagent 回報被壓太短，主 agent 拿不到足夠資訊」，但這是假設，沒有實測。❓

**建議**：只在主對話的敘述性回覆使用。subagent 的回報用結構化欄位（見 3.4），不靠文體壓縮。用自己的 cost model 量測後再決定。

---

### 3.2 多輪對話 vs subagent

**Claude Code 官方準則**
- 用主對話：需要來回修改、多階段共享大量 context、小而準的修改、對延遲敏感。
- 用 subagent：任務產生大量之後不再引用的輸出、需要限制工具或權限、任務自足且只回傳摘要。

**成本來源**：subagent 從全新 context 開始，初始內容包含自己的 system prompt、CLAUDE.md、git status、預載 skills、主 agent 寫的任務訊息；它自己發的 request 也計入同一份用量上限；結果回傳後還會佔主 context。

**論文佐證**（arXiv 2609.09233，僅讀到摘要片段，全文 PDF 無法解析）：skill 內容若是鬆散知識，直接放進主 context 的效果較好；只有當 skill 是「有明確輸入輸出契約的程序抽象」時，subagent 才有優勢，且對較小模型的增益最大。subagent 總 token 明顯更多，因為每個 subagent 都要重新收到主 agent 已有的資訊；peak context 通常較低，但弱模型時降幅較小，甚至反轉。

**決策流程**
1. 這個任務需要之前對話的內容嗎？需要 → 主對話（或 fork）。
2. 產出很大、之後不會再引用嗎？是 → subagent。
3. 子任務互相獨立、可並行嗎？是 → 多個 subagent。
4. 以上皆否 → 繼續主對話多輪。

**範例**
- 「修 bug → 跑測試 → 再修」：主對話多輪。
- 「掃整個 repo，列出所有用到舊 API 的位置」：subagent，只回傳清單。
- hakka-vibe 的 `/code-review`：Standards 與 Spec 兩條軸線互相獨立，並行跑子代理，屬於合理的例外。

---

### 3.3 Pass by reference（NVIDIA NOOA 論文）

**機制**：模型看到的是變數名加有界預覽（型別、真實長度、頭尾樣本），例如 `records = list(len=100, [:5]=[...], [-5:]=[...])`。完整物件留在執行環境，模型寫 Python 操作它，只有模型自己選擇 print 的小結果才進 context。

**流程範例**
1. 工具把 50 萬列 CSV 下載到 sandbox，載入成 `df` 或寫進 SQLite。
2. context 只放：`df = DataFrame(rows=500000, cols=12, head/tail 5 列)`。
3. 模型寫 `df.groupby('region').revenue.sum()`，只 print 聚合結果。
4. 進入 context 的只有這十幾行；原始資料從未被寫進 cache。

**證據**
- SWE-bench Verified（GPT-5.5 xhigh）：NOOA 82.2%，約 28 次呼叫、1.1M token；PI 78.2%，66 次呼叫、2.2M token；OpenCode 78.6%，約 1.3M token。論文把差異歸因於工具輸出以 live value 保留，而不是反覆序列化進 transcript，並避開有損壓縮、保住 prefix-cache 重用。
- 注意：這是整體 harness 比較，pass by reference 只是其中一個因素，不能單獨歸功。
- context 排版為 KV-cache 設計：靜態前綴在前、事件歷史只追加、會變動的區塊放尾端。

**Cache write 的推論**：只有進入 context 的內容才會被寫進 cache，所以資料不進 context 就沒有對應的 cache write。❓ 論文沒有單獨拆出 cache write 的數字；Hakka 的 cost model 以美元計價，這部分數據需另外讀取。

**判準（Hakka CONTEXT.md）**：看「這份資料的完整內容有沒有變成 prompt 字元」，與用什麼查詢引擎無關。用 SQL 只取 10 列再貼進 prompt，仍然是 pass by value。

**邊界**
- 論文分級：只給檔案路徑屬弱的 reference（沒有型別，要自己從文字重建）；sandbox 型 code mode 常在邊界序列化成複本，失去 live reference。NOOA 在同一 process 內執行以保留 live reference，隔離另靠 sandbox。Claude Agent SDK 的「工作區檔案」在論文評分屬 Partial。
- MCP 工具一次回傳的 JSON 結果會整包進 context。若走 MCP，應回傳「handle + 預覽」而不是全文。
- 小模型在批次 bookkeeping 類壓力測試通過率 70.8%，大模型 93.9%；小模型對 code-as-action 的紀律較差。

---

### 3.4 SKILL.state（Google，arXiv 2608.26263）

注意：論文名稱是 SKILL.state，作者來自 Google LLC 與 Purdue。

**架構**：第 t 步，模型只收到三樣東西：不變的程序規格 P、結構化狀態 Σt、最新觀察 Ot。模型輸出推理、state patch、動作；runtime 驗證 patch、合併、執行動作，推理過程丟棄。結果是 prompt 大小固定（O(1)），累積 token 隨步數線性成長（O(T)），而一般「歷史累加」是 O(T²)。

**流程範例（論文 warehouse）**
1. 觀察：「Customer ordered item_12」。
2. 模型查狀態，得知 item_12 在 shelf_42。
3. 輸出 patch `{"inventory": {"shelf_42": null}}` 加動作 `Ship item_12 shelf_42`。
4. runtime 合併 patch、執行動作；本步的推理不再出現在後續 prompt。

**數據**
- Warehouse T=100：SKILL.state 65,408 token，Stateful（LangGraph 風格）1,062,387 token（16.2 倍差）。
- T=200：SKILL.state 準確率 0.94，約 122k token；Memory（摘要式）準確率 0.84，6,175,509 token。
- InterCode CTF：pass@1 54.2%（ReAct 43.2%），總 token −60.4%。
- τ-Bench：Retail 58.3%、Airline 32.4%；Airline 比 ReAct 少 40.5% token。
- 雜訊注入下維持 ≥0.97；外部狀態被偷改時恢復步數為 0（歷史式基線需 5–8 步）。
- 預算匹配對照（約 1,800 token）：滑動視窗 0.18、摘要上限 0.52、LLMLingua 0.22、結構化 state 0.94。關鍵是「結構化狀態」，不是單純縮短。

**Schema**：每個 domain 寫一次，不是每個任務一次。CTF 全部 100 題共用同一個 5 欄位 schema：discovered_flags、tested_hypotheses、active_files、working_dir、cmd_summary。

**限制**
- 只評測 single-agent。論文說可延伸到 multi-agent（以共享 state 取代傳逐字稿），但需要處理並行寫入衝突，未測。所以「subagent 下也有效」是延伸，不是已驗證。⚠️
- 失效情境：事先不知道 schema；某個早期觀察當時沒被認為重要而沒寫進 state；任務目標本身就是歷史（稽核、追溯）。
- 小模型的失敗 68% 是更新時誤刪既有 key，所以 patch 要用合併語意，並由 runtime 驗證、失敗就 rollback 重試。

**Subagent handoff 的設計原則（我的推演，非論文內容）**
- 放進 state：任務目標、已確定的決策、檔案或資料的引用（handle）、未解問題、完成條件。
- 不放：推理過程、完整 log、已被取代的假設。
- 大型資料以 handle 引用（接 3.3）。

示意，非論文內容：

```json
{
  "goal": "修正 parser 對空字串的 crash",
  "decided": ["不改公開 API", "測試放 tests/test_parser.py"],
  "refs": {"failing_log": "/work/logs/run3.txt", "df": "DataRef(rows=52k)"},
  "open": ["空字串是否應回傳 None？"],
  "done_when": "pytest tests/test_parser.py 全綠"
}
```

---

### 3.5 Persistent subagent

文件中的「持續」有三種，意義不同：

| 機制 | 持續的是什麼 | 備註 |
|------|--------------|------|
| Resume（`SendMessage` 帶 agentId 或名稱） | 同一個 instance 的完整歷史與工具集 | 可讀回原 run 暖好的 prompt cache；Explore 與 Plan 是一次性，不能 resume |
| `memory` 欄位（user / project / local） | 跨 session 的知識目錄 | system prompt 會載入 `MEMORY.md` 前 200 行或 25KB；是知識持久，不是 process 持久 |
| Fork（`/subtask`） | 繼承整段對話 | 首次 request 重用主 session 的 cache，比新開 subagent 便宜，但繼承全部 context |

**啟動成本由什麼組成**：system prompt、CLAUDE.md（含 AGENTS.md）、git status、預載 skills、任務訊息。

**降低啟動成本的做法（文件）**
- `omitClaudeMd: true` 讓自訂 subagent 不載入 CLAUDE.md（v2.1.271 起）。
- Explore 與 Plan 內建就跳過 CLAUDE.md 與 git status。
- 各 subagent 的 description 合計超過 15,000 token 會警告，細節應放在 system prompt 本文。
- `experimental.cacheTtl` 可選 5m 或 1h。

**邊界**
- Resume 保留完整歷史，歷史會持續變長，又回到 O(T²) 問題。
- Cache 有 TTL；閒置超過 TTL 後再 resume，推論上會重新付 cache write。❓
- 設計構想（未驗證）：借 SKILL.state 的精神，讓 subagent 把 state 寫進自己的 memory 檔，而不是靠歷史累積。

---

## 4. Hakka vibe 專案摘錄

來源：https://github.com/bread12035/hakka-vibe（讀取的分支：`claude/mattpocock-skills-hakkavibe-pvs0ru`）。目的：「在保留 agent 能力的前提下節省 token 費用」。

**可讀到的內容**：CONTEXT.md、CLAUDE.md、目錄結構（`.claude/skills`、`docs`、`fixtures`、`prompts`、`results`、`src/hakka_vibe`、`tests`）。

**CONTEXT.md 重點**：這是一個可重用的 Python agent harness，加上一組量測各種 harness 設計省多少 token 成本的實驗。
- Agent = Python class；method 是 capability；field 是 typed state。「Skill」專指 Claude Code skill，不拿來稱呼 agent 的 method。
- **DataRef**：指向 process 內大量資料的薄引用，生命週期只有一次任務，模型只看預覽。**MemoryStore**：跨 session 知識存放，尚未實作。
- 實驗結構：Experiment（編號 1–6，每個只動一個變因）→ Arm（受測條件）→ Run（每個 arm 跑 3 次）。Fixture 是凍結的生成 repo，內含機械注入的 bug；**Calibration gate**：baseline 少於 8 輪就視為太簡單，需加深後重生。
- 成本一律換算成美元；cache write 分 1h 與 5m 兩種單價；thinking token 計為 output。

**CLAUDE.md 重點**：四階段流程（釐清需求 → 需求轉任務 → implement + tdd → 定期審核架構），每階段指定 mattpocock skills；`/code-review` 以 Standards 與 Spec 兩軸並行子代理。寫 agent code 時分層：結構聽 `nooa-design`，判準聽 `codebase-design`（ADR-0001）。

**未取得**：`results/` 與 `docs/` 目錄被 GitHub 拒絕自動存取，所以 Experiment 1–6 的數字沒有納入本報告。

---

## 5. 待驗證項目

1. Hakka results 的實際數字（尤其 cache write 的美元節省）：需貼上 results 或摘要。
2. Caveman 對 subagent 表現的實測：沒有找到。
3. Caveman 是否降低 request 次數：沒有證據。
4. SKILL.state 在 subagent 或 multi-agent 的實測：論文未測。
5. arXiv 2609.09233 全文：PDF 無法解析，只讀到搜尋摘要；作者與機構未確認。
6. Cache TTL 過期後 resume 的實際成本：屬推論，建議用 cost model 實測。

---

## 6. 給 agent 的操作規則（可直接作為 context）

1. 預設在主對話多輪完成。只有「大量輸出隔離」「需限制工具」「自足且有明確 I/O 契約」「獨立可並行」才派 subagent。
2. 大資料落地到 sandbox（SQLite 或 pandas），context 只放 handle、預覽與聚合結果；不要把查詢結果全文貼回 context。
3. 派 subagent 時用 state JSON 傳 handoff，不貼對話歷史；回報也用結構化欄位。
4. 需要接續的 subagent 用 resume，不要重開；歷史過長或 cache 已過期就重開並帶 state。
5. 啟動成本用 `omitClaudeMd`、精簡 description、必要時用 Explore/Plan 這類內建輕量 subagent 壓低。
6. Caveman 只用在主對話敘述；subagent 回報保留結構欄位；是否採用以美元 cost model 實測為準，不憑 token 數字。

---

## 參考來源

- Caveman：https://github.com/JuliusBrussee/caveman ；output style 版：https://github.com/carlosduplar/caveman-output-style-claude-code
- NVIDIA NOOA 論文：https://arxiv.org/abs/2607.20709 ；部落格：https://developer.nvidia.com/blog/six-agent-harness-capabilities-for-higher-model-performance/
- SKILL.state：https://arxiv.org/abs/2608.26263
- Subagents vs Agent Skills：https://arxiv.org/abs/2609.09233（僅摘要片段）
- Claude Code subagents 文件：https://code.claude.com/docs/en/sub-agents
- Hakka vibe：https://github.com/bread12035/hakka-vibe
