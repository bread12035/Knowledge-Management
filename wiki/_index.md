# Wiki Index

自動產生（`python3 scripts/km.py index`），請勿手改。更新日期：2026-11-18。
標記：`AI` = ai-new-tech，`SD` = system-design。引用格式：`KM:<slug>`。

## 主題總覽 Topics

- [[agent-harness-design]] `AI` — 使用者以檔案為中心的 agent system：入口地圖、EXEC_PLAN、五層記憶、三個省 token 機制、scale-out 與 Preprocess
- [[agent-memory]] `AI` — Transcripts → Notes → Wiki → Injected context，dreaming 在背景校正與整理各層
- [[ai-evaluation]] `AI` — 離線題庫加 paired test 擋壞版本、線上 A/B 證明更好；前提是題庫與 grader 都代表 User，決策過主指標與護欄兩關

## 概念 Concepts

- [[cuped]] `AI` — 用實驗前就有、且不受新版影響的資料扣掉本來的差異，變異約縮小為 (1 − ρ²) 倍
- [[dreaming]] `AI` — 離線回頭檢視 transcripts 與現有記憶，校正錯誤、建 wiki、提升關鍵筆記、補缺口
- [[golden-dataset]] `AI` — 固定題庫要代表 User 的需求：分 dev 與 held-out、對照題目分布、補尾部風險、持續回填失敗
- [[grader-alignment]] `AI` — 讓 LLM judge 的判斷與 User 一致、無偏、穩定：用 kappa、McNemar、mutation test、順序交換檢查，用理由與偏好修正
- [[harness2]] `AI` — 不改模型、不需標準答案，針對單一任務 Propose-Probe-Compose 改善 harness，並把有效的原因存進 library
- [[injected-context]] `AI` — 每個 session 都載入的一小層；放關鍵規則加指向下層的指標，錯誤會擴散到所有 session
- [[llm-wiki]] `AI` — LLM 把原始資料編譯成互相連結的頁面；跨文件問題幫助最大，但會膨脹、需要維護
- [[memory-salience]] `AI` — 寫記憶是預測；強模型自己判斷什麼值得記比固定規則好，告訴它目的而不是規定怎麼用
- [[ontology-knowledge-graph]] `AI` — Ontology 規定允許哪些類型與關係，Graph 存真實的節點與邊；用 ontology 當 LLM 抽取與檢查的標準
- [[paired-test]] `AI` — 同一題 A、B 都回答，用每題的差做檢定，扣掉題目難度的雜訊；依結果型態事先選檢定
- [[skill-state]] `AI` — 每步只給程序規格、結構化狀態與最新觀察，推理用完即丟，prompt 大小固定

## 設計模式 Patterns

- [[error-analysis-loop]] `AI` — 讀真實失敗、分類計數，再把失敗類型寫成測試並回填題庫、回歸集與 judge rubric
- [[optimistic-concurrency]] `AI` — 寫入時附上讀到的版本 hash，不符就失敗並重讀重試，避免 last-write-wins
- [[pass-by-reference]] `AI` — 大資料留在執行環境，context 只放 handle 與有界預覽，模型寫程式取聚合結果
- [[primary-guardrail-gate]] `AI` — 一個主指標下結論，加幾個事先定好門檻的「不能變差」指標；任何一個沒過就不採用
- [[progressive-disclosure]] `AI` — 給 agent 一個小而穩定的入口，再用指標教它往哪裡找細節，而不是一次塞進所有規則
- [[promotion-gate]] `AI` — 新教訓、規則、決策先放待定區，在多個案例重複出現且有證據才升到長期或常駐層
- [[single-writer]] `AI` — 每份資料只讓一個寫入者負責，從結構上消除並行寫入衝突

## 設計決定 Decisions

- [[agent-system-memory-layers]] `AI` — 依壽命分任務記憶、任務結果、長期知識、失敗記憶、證據五層，並用四條規則把下層內容往上升
- [[km-dreaming-design]] `AI` — lead 改 optional、note 由 skill 或 workflow 寫、analyzer 做成 worker pool、note 與 transcript 配對

## 跨領域連結 Bridges

（尚無）
