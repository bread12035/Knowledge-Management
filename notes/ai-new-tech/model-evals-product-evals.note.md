---
raw: raw/ai-new-tech/model-evals-product-evals.md
raw_sha256: c989307f7f58be846a1ec354d6106fb2b3561af8e0d25b157e69462d23b334f3
source: ai-new-tech
title: Model evals & Product evals
generated: 2026-11-18
---
# Model evals & Product evals（note）

## 一句話
評估 agent、retrieval、system 的核心是兩個代表性：題庫代表 User 的需求（A）、Grader 代表 User 的評斷（B）；User 難接觸是限制條件；決策用 paired 2×2 + McNemar 加護欄閘門，失敗由 error analysis 回流題庫。

## 主張
原文證據標記對應：[論文] → {原文}、[案例] → {第三方}（公司自報）、[一般知識] → {討論結論}、[建議] → {我的判斷}、[示意] → {示意}。

### §0 兩個代表性
- 核心目標 A：golden test dataset 代表全體 User 的需求；目標 B：Grader（LLM-as-judge）代表 User 的評斷；兩者缺一不可 {我的判斷} (§0)
- 「User 難接觸、時間有限」是限制條件，不是目標 {我的判斷} (§0)
- 題庫分 dev 集（調整用）與 held-out 集（只在決定是否採用時用）；同一批題既調又驗會 overfitting to the test set {討論結論} (§0.1)
- 題庫代表 User 看四件事：比例、內容、難度、邊界；Grader 代表 User 看三件事：一致、無偏、穩定 {我的判斷} (§0.2)
- 標註的人是開發者或專家時不一定等於 User，要用線上訊號檢查 judge 是否預測 User 的真實反應 {我的判斷} (§0.4)
- 代表性只能檢查，不能證明：冷啟動只有舊系統處理過的問題 {討論結論} (§0.4)

### §2 Model evals vs Product evals
- Model evals：固定任務比較模型或 prompt，問「哪個版本比較強」；Product evals：真實 User 與流量下是否有用，要處理分布、Grader、安全、成本、延遲 {我的判斷} (§2)
- Model evals 是 Product evals 的零件；Model evals 分數高不代表 Product evals 好 {我的判斷} (§2)

### §4 評分基礎
- Agent 的正確答案是最終狀態加過程規則（看 tool-call log）；retrieval 是 gold passage ID（recall@k、MRR、nDCG）；system 是標準答案加引用檢查 {討論結論} (§4)
- 能用 Code 評分就用 Code，LLM judge 只用在 Code 做不到的地方 {討論結論} (§4)
- Agent 非確定性：報告 pass@k（k 次至少一次成功）或 pass^k（k 次全部成功）{討論結論} (§4)

### §5 題庫貼近 User（目標 A）
- 冷啟動 + 分層抽樣：舊紀錄依「角色 × 任務 × 難度」分層，報告依流量加權並列出子群分數；限制是 survivorship bias、PII、舊標籤過期 {討論結論} (§5.2)
- Red Team 另成一套必須全過的測試集，不和一般題庫平均；跨領域資安用「角色 × 資料領域」權限矩陣與 canary 字串，洩漏率要求為零 {我的判斷} (§5.2)
- 權限要在系統層強制執行，不要只靠 prompt {討論結論} (§5.2)
- 模擬使用者只能補缺口，必須用真實紀錄驗證分布 {我的判斷} (§5.2)
- 題目分布對照用 TVD = 0.5 × Σ|p − q|；修正方法是補題或加權（權重 = 流量比例 ÷ 題庫比例）{討論結論} (§5.3)
- 範例：題庫平均新版 86.5% 看似進步，依流量加權卻從 79.5% 退步到 77.7%；TVD = 0.20 {示意} (§5.3)
- 小層加權會放大雜訊（20 題的 Wilson 95% CI 34% 到 74%），只靠加權不夠要補題 {我的判斷} (§5.3)
- 難度用舊版跑 k 次的通過率分帶；全是易題會飽和、全是難題也看不出差異；分開報告易中難 {我的判斷} (§5.3)

### §6 Grader 貼近 User（目標 B）
- Cohen's kappa 是扣掉運氣的一致率；範例原始一致率 92% 但 kappa 只有 0.46，人說錯的 10 題 judge 只抓到 4 題 {示意} (§6.2)
- 分子群算 kappa，並和人與人之間的 kappa 比較，那是 judge 能達到的上限 {我的判斷} (§6.2)
- 同一張 judge vs 人的 2×2 表：kappa 看對角線（一致嗎），McNemar 看非對角線（偏鬆還是偏嚴）{討論結論} (§6.2)
- Mutation test：對人工確認的好答案注入錯誤（改數字、刪條件、加幻覺），沒抓到的就是 judge 盲區 {討論結論} (§6.2)
- 預測效度（judge 分數是否預測線上訊號）是「judge 像不像 User」最直接的檢查 {討論結論} (§6.2)
- judge prompt 一改就要重新校準 {討論結論} (§6.2)
- 順序偏差有論文記錄：強 judge 也會偏好某個位置，對調答案後會改變結論 {原文} (§6.3)
- 順序交換實驗：每對答案兩種順序各評一次，分成一致、跟著位置、不穩定；只有兩次一致才算贏，其他算平手 {討論結論} (§6.3)
- 要報告順序一致率與第一位置贏的比例，不要只報整體勝率；跟著位置超過約 20% 時先修 judge prompt {我的判斷} (§6.3)
- Counterbalancing 也用在 Arena 左右位置、paired 跑測的執行先後（快取與狀態隔離）、RAG 段落順序 {我的判斷} (§6.3)
- Grader 就是 reward function；SFT 式是把 User 的理由寫進 rubric 與 few-shot，RLHF 式是用 User 的二選一校準或挑選 grader；兩者都是類比，不改權重 {我的判斷} (§6.4)
- RLHF 式分兩層：User 選答案（算 pairwise accuracy）與 User 選 grader 輸出（挑 grader 版本）{我的判斷} (§6.4)
- Grader 偏好長答案（length bias）是 reward hacking 的縮小版：用它當優化目標，系統會學著寫長 {我的判斷} (§6.4)
- 修 grader 流程：兩版 prompt 只改一處、盲選、隨機左右、User 選並寫理由；理由先 pending，2 到 3 個案例重複才升級成 rubric 規則；規則用通用說法不抄專有名詞 {我的判斷} (§6.5)
- Criteria drift：User 打分的過程會改變自己的標準（EvalGen），要定期拿舊案例重問 {原文} (§6.5, §6.7)
- GEPA 取樣軌跡、用自然語言反思、保留 Pareto frontier 上的多個候選；論文實驗是任務型 benchmark，不是 grader 對齊 {原文} (§6.6)
- MLflow 的 GEPA 對齊最少需要 10 筆有人工標註的 trace；grader 標註集要另外切 train 與 held-out {原文} (§6.6)
- Dropbox 用 GEPA 讓 relevance judge 的 NMSE 從 8.83 降到 4.86，調整新模型從 1 到 2 週降到 1 到 2 天 {第三方} (§6.6)
- Dropbox 的三個風險：優化器複製範例關鍵字而過擬合、候選擅自改評分尺度（任務漂移）、整份重寫風險太高要限制小修改 {第三方} (§6.6)
- Harness² 的裁判是模型，本節的裁判是 User，所以 Harness² 沒有解決代表 User 的問題 {我的判斷} (§6.8)
- Grader 像 User 不會讓系統沒意義：檢查比做容易（generation-verification gap）、grader 有標準答案、離線可以慢而貴 {我的判斷} (§6.9)
- Grader 與系統用同一個模型時可能有同樣盲點並偏愛自家答案，準確度要用人工標註另外量 {討論結論} (§6.9)

### §7 User 難接觸（限制條件）
- 把 User 的時間只花在最有價值的地方 {我的判斷} (§7)
- 被動訊號（重問率、轉人工率、複製率、放棄率）是 proxy，要先和人工標註對照過才能信 {討論結論} (§7.1)
- 分層標註：開發團隊先標並註記不確定，只有難題升級專家，並隨機審計沒升級的題；專家只標難題會有 selection bias {我的判斷} (§7.1)
- Arena 用 Bradley-Terry 估強度，約 100 分 ≈ 64% 勝率；只回答哪個好，不回答對不對 {原文} (§7.1)
- PPI 用少量隨機抽樣的人工標註估計 judge 的系統性偏差並扣掉；範例 N = 2000、n = 100 時 CI 從 ±7.4% 縮到 ±5.8% {示意} (§7.1)
- DOE 減少要測的條件數，不減少標註次數，有 aliasing 風險 {討論結論} (§7.1)
- CUPED 範例 ρ ≈ 0.81，變異降為 0.32 倍，約只需三分之一題數 {示意} (§7.2)
- PPI 與 CUPED 概念相近：都用便宜且與結果相關的數字降低雜訊；PPI 用 judge 分數，CUPED 用實驗前資料 {討論結論} (§7.2)
- Judge 改版後，舊的 X 要用同一個 judge 重算才可比 {討論結論} (§7.2)

### §8 決策
- 只有在題庫與 Grader 都有代表性時，決策結論才可信 {我的判斷} (§8)
- 第一關主指標：paired 2×2 + McNemar；每題隨機決定先跑 A 或 B {我的判斷} (§8.1)
- 第二關護欄：子群底線、成本與延遲、安全零容忍、過度拒答、回歸題；任何一個沒過就不採用 {我的判斷} (§8.2)
- 「沒有變差」用 non-inferiority 檢查：信賴區間下界 > −margin 才通過 {討論結論} (§8.2)
- 子群非劣性所需題數：ψ = 15%、margin 3 點約 1030 題，5 點約 371 題；小子群很難證明沒變差 {討論結論} (§8.2)
- Rule of three：n 次測試 0 次失敗，95% 失敗率上界約 3/n；零容忍安全要靠系統層權限強制，測試只是驗證 {討論結論} (§8.2)
- 護欄太多會增加誤報，只放最重要的幾個，必要時 Bonferroni {討論結論} (§8.2)

### §10 Error analysis
- 流程：收集約 100 筆 trace → open coding（每筆一句自由筆記）→ axial coding 成 failure taxonomy → 計數排序 → 重複到 saturation → 寫成 evals（能用 Code 的寫 Code 測試，主觀的寫 LLM judge）{討論結論} (§10)
- Error analysis 的輸出餵給題庫、回歸測試集、judge rubric {我的判斷} (§10)
- 與 Structure of agent system 的升級規則一致：同樣的失敗出現兩次就寫進文件或測試；證據模糊交人判斷 {我的判斷} (§10)

### §11 分階段落地
- 第 1 階段先做：能 Code 評分的全用 Code、冷啟動小題庫與分布對照、分 dev 與 held-out、做一次 error analysis、定 3 到 5 個護欄 {我的判斷} (§11)
- 第 2 階段：分層標註、judge 的 kappa / McNemar / mutation test、順序交換、手動修 grader、Red Team 題集 {我的判斷} (§11)
- 第 3 階段：PPI 與 CUPED、GEPA 優化 judge、被動訊號對照、Arena {我的判斷} (§11)
- 贏家詛咒：從很多版本挑最好的，真實表現通常比量到的低 {討論結論} (§12)

## 變更
- （首次產生）

## 候選連結
- 本 source：ab-test-ai-evaluation-guide、paired-test-guide、agent-evaluation-harness-2-ab-test-guide（§6.8 對照）、structure-of-agent-system（升級規則、evals/ 的失敗記憶）、anthropic-agent-memory-guide（pending → 升級 ↔ promote；criteria drift ↔ 記憶過期）
- system-design：權限在系統層強制（defense in depth）、回歸測試、測試資料分層、監控指標與 SLO、canary 與 feature flag
