---
source_project: AI new tech & studies
source_file: claude/agent evaluation: Harness 2 & AB test 指南
title: agent evaluation: Harness 2 & AB test 指南
first_exported: 2026-11-18
updated: 2026-11-18
---
# Agent evaluation: Harness 2 & AB test 指南

整理日期：2026-11-09
用途：學習 Harness²（Google 的遞迴 agent harness 框架），並和 A/B test（標準答案、paired test）對照。改 prompt 或 workflow 步驟時，用來決定該用哪種做法、怎麼實作。
證據標記：[論文] 出自 arXiv:2610.14224 的摘要或整理頁；[README] 出自 GitHub repo 說明；[第三方] 出自部落格或報導，未在論文確認；[一般知識] 統計與實驗設計的通用做法；[建議] 本文件的設計建議，尚未在你的專案驗證；[示意] 教學用的假設數字。
相關文件：《AB test 評估 AI 指南》（power analysis、CUPED、sequential testing 的完整說明）。

---

## 1. 一頁摘要

| # | 主題 | 一句話 |
| --- | --- | --- |
| 1 | Harness² | 不改模型，讓 agent 在工作時自動改善包在模型外面的 harness，不需要標準答案 [論文] |
| 2 | 第一層：Propose-Probe-Compose | 針對當前任務，提出修改、在同一任務上試跑、只保留有行為證據的修改 [論文] |
| 3 | 第二層：harnessing-level recursion | 把「這次為什麼有效」存進 library，讓下一個任務更快提出好修改 [論文] |
| 4 | A/B test | 靠隨機分組與結果指標比較兩組，不需要每題的正確答案 [一般知識] |
| 5 | 標準答案 + paired test | 同一題 A、B 都回答，對答案，只看結果不同的題目做檢定 [一般知識] |
| 6 | 兩者的差別 | paired test 證明「改動平均有效嗎」；Harness² 找出「這個任務該怎麼改」 [建議] |
| 7 | 能不能加 A/B 概念 | 護欄最適合；power analysis 與 CUPED 可部分引入；Harness² 本身沒有這些 [建議] |
| 8 | 最佳搭配 | Harness² 產生候選，paired test 加護欄驗收 [建議] |

---

## 2. Harness² 是什麼

### 2.1 基本資料

- 論文：Harness²: Recursive Agent Harnessing for an Open World，arXiv:2610.14224，2026-10-09 提交，Northwestern University 與 Google Cloud AI Research [論文]。
- 程式碼：github.com/google-research/harness2，Apache 2.0 授權。README 說明它不是 Google 官方支援的產品 [README]。
- 它是 Python framework 加 CLI，**不是 Claude skill** [README]。但它能編輯的八個元件裡有 skills，所以它是「會寫出 skill 的工具」。
- 成績（作者自報）：GLM-5 與 Gemini 3.5 Flash 在三個 benchmark 上，相對基礎 harness 最多進步 11.5 點（WorkBuddy-Bench）、4.5 點（JobBench）、11.8 個百分點（LAB）[論文]。

### 2.2 要解決的問題

- 開放世界的任務在設計 harness 時沒見過，到了測試時又是新的，所以沒有 ground-truth verifier（能判斷答案對不對的檢查器）來引導修改 [論文]。
- 既有方法多半針對固定任務、unit test 或驗證回饋來優化，然後部署一個靜態設定。任務一變，設定就可能失效 [論文]。
- 手動改 prompt 很慢，而且多半靠猜。

### 2.3 名詞

| 名詞 | 白話 |
| --- | --- |
| Harness | 包在模型外面、讓模型能當 agent 行動的系統：prompt、tool、memory、skill、orchestration 等 [README] |
| Execution harness | 被改善的系統，共八個可編輯元件：system prompt、guardrails、memory、tool guidance、subagents、skills、scripts、plugins（中介層）[README] |
| Improvement harness（R） | 負責改善的機制，裡面有 library。第二層更新的就是它 [論文] |
| Reference execution | 用目前的 harness 先跑一次任務，留下的參考執行與軌跡 [論文] |
| Library | 存放過往採用的 harness 與經驗紀錄的地方 [論文] |

注意名稱：八個元件裡的 **guardrails** 是 harness 內部的規則（例如「交付前要檢查」）；A/B test 的 **guardrail metrics** 是評估用的指標。名字一樣，用途不同。

### 2.4 第一層：Propose → Probe → Compose（任務層遞迴）

只針對「當前這一個任務」改善 harness。

1. **Step 0**：用原 harness 跑一次，得到 reference execution [論文]。
2. **Propose**：提出兩個候選。一個是 invariant 候選，針對規劃、使用工具這類通用缺陷；另一個是針對當前領域的候選 [論文]。
3. **Probe**：每個候選在同一個任務上，用相同設定執行，並與參考執行比對 [論文]。
4. **Compose**：依具體觀察，合併有證據支持的修改，或保留原本的 harness [論文]。

預算 k 控制遞迴次數，有兩種模式 [論文][README]：

- Parallel（平行）：同時探測 K 個通用候選與 K 個領域候選。k 大於 1 時，由 agentic selector 拿匿名化的成品，對照任務要求挑出最終 harness。
- Sequential（序列）：串接 k 次對比步驟，每一步接在前一步的 harness 和累積的執行歷史上。

### 2.5 第二層：harnessing-level recursion（跨任務學習）

為什麼需要：第一層每個任務都從基礎 harness 重新開始，學不到東西。直接重用高度客製的 harness，在條件改變時會引入雜訊 [論文]。所以第二層只存「為什麼有效」，並選擇性重用。

更新公式（論文）：`R(t+1) = UPDATE(R(t), H*(t), D(t))`。白話：新的 R = 舊的 R + 這次採用的 harness + 這次完整的改善紀錄（參考執行、候選、Compose 決定、選出的結果）。

流程：

1. 任務 t 做完第一層，得到採用的 harness 與完整紀錄。
2. Experience reflector 回顧紀錄，抽出教訓：哪些修改解決了哪些缺陷，在什麼條件下有效 [論文]。
3. 過濾：只有被執行對比支持的教訓才保留，證據不足就不存 [論文]。
4. 存入 library。每筆有兩部分：可執行的 harness 與經驗紀錄，另有索引供之後查詢 [論文]。
5. 下一個任務仍從基礎 harness 出發，但 Propose 會以 library 為條件，重用或改寫舊元件 [論文]。

論文的消融實驗：拿掉 library，WorkBuddy-Bench 與 JobBench 的分數都下降；更大預算累積的 library，能支持之後更強的修改；跨 benchmark 遷移經驗也有幫助。來源頁面沒有給具體數字 [論文]。

### 2.6 證據與限制

- 作者承認：比較能引導決定，但不能證明輸出是對的 [第三方，轉述論文]。
- 實驗中改寫 harness 的 editor 是 Claude Opus 4.8；主要結果用前沿模型當 editor，弱模型的進步可能有一部分來自這點 [第三方]。
- 不是處處贏：LAB 上 Meta-Harness 對 Gemini（Codex）得 76.5，Harness² 一步是 75.6 [第三方]。
- 成績是作者自報，來自與廠商相關的論文。
- 評估 Harness² 時，benchmark 分數仍靠各 benchmark 的 rubric，也就是標準答案。「不需要標準答案」指的是執行期間的改善過程 [第三方]。
- 有報導提到論文曾出現 55 分的輸出被選得比 95 分的好。這是二手說法，未在論文確認，僅供參考。

---

## 3. A/B test 的相關概念

完整說明見《AB test 評估 AI 指南》。這裡只放與 Harness² 對照所需的部分。

### 3.1 核心：不需要「每題的正確答案」

A/B test 靠兩樣東西 [一般知識]：

- Randomization（隨機分組）：兩組在所有已知與未知因素上，平均來說都一樣。
- Outcome metric（結果指標）：量使用者的實際行為，不量「答案對不對」。

流程：選行為指標 → 隨機分組 → 算兩組平均差 → 統計檢定（p-value 與信賴區間）。

### 3.2 有標準答案時：paired test

同一題，A、B 都回答，比較每一題的差 [一般知識]。

| 分數型態 | 檢定 |
| --- | --- |
| 對 / 錯 | McNemar test（小樣本用 exact 版） |
| 連續分數 | Paired t-test；偏斜或等級少時用 Wilcoxon |
| 勝 / 負（評審二選一） | Sign test |

注意：重複執行不是獨立樣本，先彙整成每題一個值；題目要用 ID 對齊；評審要盲評。

### 3.3 Power analysis

測試前先算需要幾題或幾人 [一般知識]。成對設計要看「A、B 結果不同的比例 ψ」。差異縮小一半，樣本約變 4 倍。

```python
from scipy.stats import norm

def mcnemar_n(delta, psi, alpha=0.05, power=0.8):
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    return ((za * psi**0.5 + zb * (psi - delta**2) ** 0.5) ** 2) / delta**2

# mcnemar_n(0.10, 0.20) ≈ 155
```

### 3.4 Guardrail metrics（護欄指標）

主要指標只選一個，另設幾個「不能變差」的指標，例如成本、延遲、幻覺率、拒答率。護欄用「不能超過的門檻」來定，因為樣本少時，很小的變差測不出顯著 [一般知識]。

### 3.5 CUPED

用實驗前的資料扣掉使用者本來的差異，降低雜訊。變異約縮小為 (1 − ρ²) 倍 [一般知識]。

- 適合：線上 A/B，不同的人用 A 或 B，而且有歷史資料。
- 離線 paired 設計已內建同樣的精神：同一題拿 B 減 A，等於 θ = 1 的 CUPED。

### 3.6 Sequential testing

事先設計好檢查點，讓你中途可以看結果又不讓誤判率變高。預設用 O'Brien-Fleming 邊界。離線評估題庫固定、一次跑完，不需要 [一般知識]。

### 3.7 沒有標準答案時，統計學怎麼做

| 做法 | 說明 | 注意 |
| --- | --- | --- |
| 行為指標（proxy metric） | 用點擊、留存、轉人工率代替「對錯」 | 指標可能被刷高但品質沒變好 |
| 成對偏好比較 | 評審只選「哪個比較好」，用 sign test | LLM 評審要交換 A、B 順序各跑一次 |
| 檢查量測本身 | A/A test、SRM、評審一致性（Cohen's kappa） | A/A 不該有差異 |

---

## 4. 並排比較（情境：一個任務，修改 prompt 或 workflow 步驟）

| | 標準答案 + paired test | 行為差異（Harness²） |
| --- | --- | --- |
| 事先要有什麼 | 題庫與專家答案 | 只要一個任務 |
| 比較單位 | 很多題，每題 A、B 配對 | 一個任務，參考版本對候選版本 |
| 誰判斷 | 答案比對加統計檢定 | 模型比對行為與成品 |
| 結論的形式 | 「B 比 A 好 9%，p = 0.0014」 | 「這個修改在這個任務有效，因為找到附件 C」 |
| 能回答 | 改動**平均**有沒有效 | 改動**對這個任務**怎麼調 |
| 不能回答 | 新類型任務怎麼辦 | 改動是否真的比較好、好多少 |
| 統計工具 | power analysis、paired test、CUPED、護欄 | 原生沒有，要自己加 |
| 前期成本 | 高（建題庫） | 低 |
| 主要風險 | 題庫不代表真實任務、過度擬合題庫 | 看起來有進步其實是錯的；單次結果很吵；挑到運氣好的候選 |

---

## 5. 完整範例

情境 [示意]：公司的合約助理，任務是「從供應商合約抽出付款條件，輸出 JSON」。要改的地方：在 prompt 加一個 workflow 步驟「交付前回查原文，並寫出頁碼」。A 是原 prompt，B 是加了這一步的 prompt。

### 5.1 做法一：標準答案 + paired test

1. **Step 0 事先寫決策規則。** 一次只改一個變因。主要指標：「全部欄位都對」的比例。規則：主要指標顯著提升且護欄沒變差，才採用。
2. **Step 1 Power analysis。** MDE +10%，ψ 保守取 20%，顯著水準 0.05，power 80%，需約 155 份。加 30% 緩衝，用 200 份。此設計下真有 10% 差異時，抓到的機率約 89%。
3. **Step 2 建題庫。** 200 份已去識別化的真實合約，法務寫標準答案。分「開發用」與「驗收用」，驗收用的不拿來調 prompt。
4. **Step 3 配對執行。** 同一份合約 A、B 各答一次，用合約編號對齊。輸出有隨機性就跑 3 次取多數決。樣本數是 200 份，不是 600 次。
5. **Step 4 McNemar exact test。**

| | B 對 | B 錯 |
| --- | --- | --- |
| **A 對** | 130 | 6 |
| **A 錯** | 24 | 40 |

A 答對 68%，B 答對 77%，差異 +9%，95% 信賴區間約 +4% 到 +14%，p ≈ 0.0014（已用程式驗算）。

6. **Step 5 檢查護欄。**

| 護欄 | A | B | 門檻 | 結果 |
| --- | --- | --- | --- | --- |
| 每份成本 | $0.030 | $0.042 | 不超過 $0.045 | 通過 |
| 延遲 | 28 秒 | 36 秒 | 不超過 45 秒 | 通過 |
| 頁碼對不上原文的比例 | 4% | 3% | 不可變差 | 通過 |
| 「無法判斷」比例 | 3% | 5% | 不可大幅上升 | 通過 |

7. **Step 6 決策。** 主要指標通過，護欄通過，採用 B。

更正紀錄：先前討論曾用 100 份合約的版本。以 ψ = 18%、差異 10% 計算，100 份的 power 只有約 66%，不夠。所以本文件改用 200 份。

### 5.2 做法二：行為差異（Harness² 風格）

任務是一份**新合約，沒有標準答案**。標 [建議] 的是我加入的 A/B 概念，不是 Harness² 內建。

1. **Step 0 事先寫規則。[建議]** 行為證據用程式驗證：每個欄位附的原文引用必須真的出現在 PDF 裡。這是沒有答案時最便宜的檢查。護欄：JSON 格式正確、引用存在、成本不超過參考版本的 1.5 倍。
2. **Step 1 量雜訊。[建議]** 這是 power analysis 的縮小版。參考版本重跑 3 次。3 次都是「Net 30」代表雜訊小；若出現 Net 30、Net 45、Net 30，代表雜訊大。修改的效果必須大過這個雜訊。
3. **Step 2 Propose。** 候選 1（通用）：交付前回查並寫頁碼。候選 2（領域）：先搜附件與修訂條款。
4. **Step 3 Probe。** 每個候選也跑 3 次。**[建議]** 比較「候選減參考」，不是比絕對值（θ = 1 的 CUPED 想法）。候選 2：3 次中有 3 次找到附件 C 的「Net 45」，引用通過檢查。候選 1：0 次找到附件，但引用 3 次都通過。
5. **Step 4 Compose 加護欄。** 候選 2 成本 +20%，候選 1 成本 +10%，都在 1.5 倍內。兩個都保留，合成新 harness。
6. **Step 5 確認執行。[建議]** 合成後的 harness 用新的隨機種子再跑一次，防止「挑到運氣好的候選」（winner's curse）。沒退步才採用。
7. **輸出：** 改良後的 harness、這份合約的成品（Net 45，附頁碼），和一條存進 library 的教訓：「付款條件可能在附件覆寫，先搜附件」。

### 5.3 第二層的例子

- 任務 1（供應商 X）：存下「先搜附件」的教訓與搜附件的 skill，適用條件是合約含 Exhibit 或 Amendment。
- 任務 2（供應商 Y 的採購合約）：Propose 查索引，直接提出「先搜附件」的候選，不必從零摸索。
- 任務 3（沒有附件的短合約）：教訓不適用。任務從基礎 harness 出發，不帶整份客製 harness，所以不會被無用規則拖累。

### 5.4 概念對照

| 概念 | 做法一 | 做法二（加入後）[建議] |
| --- | --- | --- |
| Power analysis | 算題數：155 份，加緩衝用 200 份 | 算每個候選要重跑幾次，效果要大過雜訊 |
| Guardrail metrics | 成本、延遲、頁碼錯誤率、無法判斷比例，有明確門檻 | 程式可驗證的規則：格式、引用存在、成本倍數 |
| CUPED | paired 已內建（θ = 1）；線上才用真正的 CUPED | 參考執行當共變量，比較差值 |
| 多重比較與 winner's curse | 一個主要指標 | 確認執行；候選越多越要確認 |
| 事先寫規則 | 實驗計畫表 | Step 0 的規則 |
| 防止過度擬合 | 開發用與驗收用分開 | 用做法一的題庫驗收 |
| 能下的結論 | 平均有效，有信賴區間 | 這個任務有效，有行為證據 |

---

## 6. 適用情境 [建議]

| 情境 | 建議 |
| --- | --- |
| 任務類型固定、會重複很多次，且能建題庫與答案 | 做法一。題庫一次建好，之後每次改版都能驗證 |
| 任務每次都不一樣，沒有現成答案 | 做法二，用來產生候選與經驗 |
| 要做上線與否的決策，需要有數字與信賴區間 | 做法一，或做法二加做法一驗收 |
| 想找出「為什麼這個任務做不好」 | 做法二，它的軌跡對比會指出哪一步不同 |
| 任務有副作用（寫資料庫、寄信、下單） | 避免做法二。Probe 會在同一任務上重跑候選，副作用會重複發生 [README] |
| 高風險任務（法律、財務、安全） | 做法二的結果不能直接採用，一定要經做法一驗收，必要時人工複查 |
| 任務很便宜、改善空間小 | 不值得用做法二。一個任務 k = 1 就要 4 次 executor 與 3 次 improver [第三方] |
| 使用者很少的內部系統 | 偏向離線：做法一的 paired test，不用線上 CUPED |

---

## 7. 實作細節

### 7.1 安裝與執行 Harness²

需求：Linux、Python 3.12、uv。模型相關的 benchmark 另需 Node.js 20+、Google Cloud CLI；LAB 另需 Pandoc 與 Poppler，WorkBuddy-Bench 另需 Docker [README]。

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e '.[render]'

# 不需要模型金鑰的 demo
harness2-demo --output runs/demo --k 2

# 安裝並檢查 benchmark（lab / jb / wb）
harness2-setup lab
harness2-check --bench lab

# 先預覽，再跑一個任務
harness2 --bench lab --k 1 --mode parallel \
  --only-domains antitrust-competition --max-tasks 1 --dry-run
harness2 --bench lab --k 1 --mode parallel \
  --only-domains antitrust-competition --max-tasks 1

# 評分與報告（參數要和上一步一致）
harness2-judge --bench lab --k 1 --mode parallel
harness2-report --bench lab --k 1 --mode parallel
```

重要參數 [README]：`--bench`（jb、lab、WorkBuddy-Bench）、`--k`（任務層遞迴預算）、`--mode parallel|sequential`、`--substrate cx`（改用 Codex，預設是 OpenCode）、`--dry-run`。重跑同一個指令會接續上次的進度。

模型設定：預設走 Vertex AI。設定檔要填 Google Cloud 專案，以及 solver（做任務）、improver（改 harness）、judge（評分）三個模型，再用 `gcloud auth application-default login` 登入 [第三方]。用 Codex 需要 Responses API 端點，release 內含 `harness2-bridge`（本機的 LiteLLM 伺服器）[第三方]。

### 7.2 讀結果

結果在 `runs/`，依 benchmark 與子集分類。每個任務資料夾有 `summary.json`、成品、採用的 harness、反思筆記與評分結果 [README]。採用的 harness 是 improver 寫出的檔案樹 [第三方]：

- 一律載入：`systemprompt.md`、`guardrails.md`、`LongTermMEMORY.md`、`tool_descriptions/`
- 依需要載入：`skills/`、`scripts/`、`sub_agents/`、`plugin/`
- `selection/`：為什麼選這個候選
- `library/`：教訓（第三方說有每領域的 `EXPERIENCE.md`；論文頁面沒有確認依領域分組）

### 7.3 成本與安全

- 程式沒有花費上限。一個任務、k = 1、單一模式，會有 4 次 executor rollout、3 次 improver session，外加一次 reflection。第三方作者的一個真實 HR 任務花了約 22 美元 [第三方]。先設雲端預算警示。
- executor 的網路不受限制，Codex 的 sandbox 是關閉的。評估前要先限制網路，避免 agent 查到 benchmark 的答案或評分標準 [README]。
- 評分與報告必須用和 refinement 完全相同的 benchmark、executor、子集、k、模式與 seed [README]。

### 7.4 接自己的任務

內建 CLI 只支援三個 benchmark。要加自己的任務，要實作 `BenchmarkAdapter` 協定，包含 `tasks()`、`domain_of()`、`task_prompt()`、`execute()`、`delivered()`、`trajectory()`、`base_harness()`、`validate_tree()`、`score()`。demo adapter 是最好的參考 [第三方]。

README 沒有說明改好的 harness 要怎麼載入你自己的 agent。所以「直接拿來改善你的 Claude Code」目前沒有文件支持 [README]。

### 7.5 做法一的實作

```python
from scipy.stats import binomtest

# 對/錯：McNemar exact test
b, c = 6, 24   # b: A對B錯, c: A錯B對
p = binomtest(min(b, c), b + c, 0.5).pvalue   # ≈ 0.0014
```

- 用 question_id 對齊 A 與 B。
- 重複執行先彙整成每題一個值。
- 護欄逐項檢查門檻；樣本少時，用「不得超過的門檻」，不要只看顯著。
- 記錄：實驗計畫表模板見《AB test 評估 AI 指南》第 5 節。

### 7.6 串接流程 [建議]

1. 在新任務上用 Harness² 產生改良候選（做法二）。
2. 在驗收題庫上做 paired test，加護欄（做法一）。護欄要包含 Propose 多花的成本。
3. 通過才採用。失敗案例加進題庫。
4. 有使用者流量時，才再做小流量線上 A/B；使用者少就跳過。

### 7.7 教訓升級閘門（用於第二層）[建議]

教訓的證據只來自一個任務。「被執行對比支持」不等於統計驗證。如果一次運氣好的結果被存成經驗，之後會影響所有任務。

| 關卡 | 做法 |
| --- | --- |
| 先放 pending | 新教訓先不進 library |
| 重複驗證才升級 | 至少在 2 到 3 個不同任務重複出現，才升級。這和你 Agent System 文件的升級規則一致：同類失敗第二次才寫進 docs |
| 用做法一驗收 | 升級前在驗收題庫跑 paired test 加護欄 |
| 證據模糊交給人 | 對應 Agent System 文件的規則 4：不自動升級 |
| 定期 lint | 模型換版本後，舊教訓可能過期，要定期檢查 |

量 library 本身有沒有用：用「有 library」對「沒有 library」，同一批任務配對比較。題數用 power analysis 算，基礎 harness 的分數可當共變量（CUPED 想法）。

---

## 8. 限定與待驗證

- 本文件第 5 節的所有數字（合約、成本、延遲、各種比例）都是教學用示意，不是真實專案資料。樣本數與 McNemar 的 p 值、信賴區間已用程式驗算。
- Harness² 的流程以論文摘要、整理頁與 README 為準，我沒有讀到論文全文。Compose 的判斷準則與 selector 的細節，來源沒有詳述。
- 第 2.6 節的 editor 模型、對 Meta-Harness 的比較、55 分對 95 分的說法，來自第三方整理，未在論文確認。
- 把 power analysis、護欄、CUPED 放進 Harness² 的做法是我的建議，沒有找到任何實測。
- `library/` 的組織方式、改好的 harness 如何載入自己的 agent，README 與論文頁面都沒有說明。
- 還沒涵蓋：實際接自己的任務時 BenchmarkAdapter 的完整寫法、futility stopping、pairwise preference 的 Bradley-Terry 模型。

---

## 9. 來源

**Harness²**
- [GitHub: google-research/harness2](https://github.com/google-research/harness2)（README）
- [alphaxiv：Harness² 論文頁（arXiv:2610.14224）](https://alphaxiv.org/abs/2610.14224)
- [hyper.ai：Harness² 論文整理](https://hyper.ai/en/papers/2610.14224)
- [i-scoop：Harness² 報導](https://www.i-scoop.eu/harness2-google/)
- [Jahanzaib：Harness2 設定指南（第三方）](https://www.jahanzaib.ai/blog/google-harness2-setup-guide)
- [Tech Jack Solutions：Harness² 簡報](https://techjacksolutions.com/ai-brief/google-research-open-sources-harness-recursive-agent/)
- [inside.com.tw：Harness² 報導](https://www.inside.com.tw/article/42679-google-harness2-open-source-recursive-agent-harness-propose-probe-compose)

**A/B test**
- 見《AB test 評估 AI 指南》第 8 節（Anthropic、OpenAI、Google 評估文件；MT-Bench；CUPED 原論文；Kohavi 等人的書）。
