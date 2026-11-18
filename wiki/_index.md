# Wiki Index

自動產生（`python3 scripts/km.py index`），請勿手改。更新日期：2026-11-18。
標記：`AI` = ai-new-tech，`SD` = system-design。引用格式：`KM:<slug>`。

## 主題總覽 Topics

- [[agent-harness-design]] `AI` — 使用者以檔案為中心的 agent system：入口地圖、EXEC_PLAN、五層記憶、三個省 token 機制、scale-out 與 Preprocess
- [[agent-memory]] `AI` — Transcripts → Notes → Wiki → Injected context，dreaming 在背景校正與整理各層
- [[ai-evaluation]] `AI` — 離線題庫加 paired test 擋壞版本、線上 A/B 證明更好；前提是題庫與 grader 都代表 User，決策過主指標與護欄兩關
- [[earnings-gcp-onprem-handover]] `SD` — Event Calendar 觸發 GCP 上的 AI 處理，結果先落地 GCS，再經單一 Adapter 交回 on-prem 的 Raw → Stage → Portal；三條流程只差 GCP 側
- [[knowledge-retrieval-design]] `SD` — 檢索方法的差別在關係何時建；實務上 SQL 縮範圍、摘要層找與排、原文當證據，精確欄位用結構化查詢不用向量猜
- [[reliable-event-processing]] `SD` — at-least-once 傳輸下讓業務效果只發生一次：outbox、冪等消費、lease 回收、Saga 補償、精準計時、明確完成信號

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
- [[pessimistic-lock]] `SD` — 先鎖再做讓後到者等待；和樂觀鎖的差別只在衝突何時處理，重做昂貴時選悲觀鎖或 single writer queue
- [[skill-state]] `AI` — 每步只給程序規格、結構化狀態與最新觀察，推理用完即丟，prompt 大小固定

## 設計模式 Patterns

- [[completion-marker]] `SD` — 用 completion marker、commit、idempotency key 這類明確信號判斷資料是否可讀或事件是否已處理，不用固定時間緩衝
- [[deterministic-over-llm]] `AI/SD` — SQL、公式、程式、Code 評分能確定的部分不讓 LLM 猜；LLM 只做判斷意思、摘要與模糊決策
- [[error-analysis-loop]] `AI` — 讀真實失敗、分類計數，再把失敗類型寫成測試並回填題庫、回歸集與 judge rubric
- [[event-driven-timer]] `SD` — Scanner 讓排程表貼近現實，Executor 用 min-heap 或 timing wheel 睡到下一個事件才醒，取代固定間隔輪詢
- [[event-log-current-state]] `SD` — 事實只追加寫進 event log，現在狀態用 view 或 materialized view 算；明細可算出餘額，餘額不能還原明細
- [[gateway-authn-service-authz]] `SD` — Authentication 集中在單一入口的 Gateway，白名單寫死不信任自稱來源；後端服務只做 Authorization
- [[golden-regression-gate]] `SD` — 把正常與失敗路徑固定成可執行的 golden cases，改規則、prompt、schema 前先跑，結果變了就擋下
- [[hybrid-search-rrf]] `SD` — 關鍵字排名與向量排名各算一次，用 RRF 只看名次合併，同時抓到精確名詞與同義說法
- [[idempotent-consumer]] `SD` — 用已處理事件 ID 或 idempotency key 去重，讓重送、重試、補償都只生效一次
- [[lease-reaper]] `SD` — 用 FOR UPDATE SKIP LOCKED 領工作並設 lease，到期沒 ack 由 reaper 放回，worker 當機不會卡死
- [[optimistic-concurrency]] `AI` — 寫入時附上讀到的版本 hash，不符就失敗並重讀重試，避免 last-write-wins
- [[pass-by-reference]] `AI/SD` — 大資料留在執行環境，context 只放 handle 與有界預覽，模型寫程式取聚合結果
- [[primary-guardrail-gate]] `AI` — 一個主指標下結論，加幾個事先定好門檻的「不能變差」指標；任何一個沒過就不採用
- [[progressive-disclosure]] `AI` — 給 agent 一個小而穩定的入口，再用指標教它往哪裡找細節，而不是一次塞進所有規則
- [[promotion-gate]] `AI/SD` — 新教訓、規則、決策先放待定區，在多個案例重複出現且有證據才升到長期或常駐層
- [[saga-compensation]] `SD` — 跨服務流程拆成多個本地交易，失敗先冪等重試，用盡就反向補償，補償失敗進 dead-letter 交人
- [[single-source-of-truth]] `SD` — 只有一個地方可以編輯，其他都是單向產生、可重建的複本；發布時整組寫入不可變 release，最後原子切換 pointer
- [[single-writer]] `AI/SD` — 每份資料只讓一個寫入者負責，從結構上消除並行寫入衝突
- [[transactional-outbox]] `SD` — 業務變更與要發出的事件寫進同一個 DB transaction，再由 relay 送出，避免資料改了事件沒發
- [[web-content-acquisition]] `SD` — 官方 API → 背後 JSON → web fetch → headless / 爬蟲服務 → browser agent，由便宜到貴；被擋就停交人，網頁內容一律當不可信輸入

## 設計決定 Decisions

- [[agent-system-memory-layers]] `AI` — 依壽命分任務記憶、任務結果、長期知識、失敗記憶、證據五層，並用四條規則把下層內容往上升
- [[km-dreaming-design]] `AI` — lead 改 optional、note 由 skill 或 workflow 寫、analyzer 做成 worker pool、note 與 transcript 配對
- [[postgres-hub]] `SD/AI` — 規模小時一個 PostgreSQL 加 extensions 同時當 relational、向量、queue、排程，不為每個需求另養服務
- [[worker-monitor-split]] `SD` — worker 管訊息傳輸與 ack/nack，monitor 只做業務判斷，common 放共用基礎設施；對應 hexagonal 的 adapter、core、port

## 跨領域連結 Bridges

- [[dreaming-x-web-content-acquisition]] `AI/SD` — 兩邊都讓 agent 讀不受控的文字；共同對策是當資料不當指示、縮小權限與爆炸半徑、關鍵動作交人
- [[golden-dataset-x-golden-regression-gate]] `AI/SD` — 同一個工具的兩種用法：AI 評估用統計比較兩版，系統設計用斷言擋住退步；都要求事先固定、只改一處、失敗回填
- [[llm-wiki-x-knowledge-retrieval-design]] `AI/SD` — 兩邊都在寫入時先整理、查詢時先看小的再往下鑽；差別是 wiki 用 LLM 寫的連結頁，檢索設計用 SQL 篩選加 L0/L1/L2 摘要
- [[optimistic-concurrency-x-pessimistic-lock]] `AI/SD` — 兩者都在處理「兩個寫入者改同一份資料」；差別只在衝突何時處理，而重做成本決定該選哪一個
- [[skill-state-x-event-log-current-state]] `AI/SD` — 兩者都在決定「保留歷史還是只保留狀態」；SKILL.state 丟掉歷史只留狀態，event log 保留歷史再算出狀態
