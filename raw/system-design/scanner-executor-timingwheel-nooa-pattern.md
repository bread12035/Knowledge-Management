---
source_project: system design & code style
source_file: claude/scanner-executor-timingwheel-nooa-pattern.md
title: 業界經典範例整合：Scanner/Executor Reconciliation + Timing Wheel 排程 + NOOA Pass-by-Reference
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Scanner/Executor Reconciliation + Timing Wheel 排程 + NOOA Pass-by-Reference

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。

## 這次合併了哪些概念

這次從記憶庫裡挑了四個表面上分屬不同專案、但骨子裡是同一種「事件驅動排程」問題的討論，合併成一個完整的實作範例：

1. **earnings-pipeline**：你在做的自動化財報/事件行事曆系統，用兩個 cronjob 分工——Scanner 定期更新事件的日期時間，Executor 偵測並觸發即將到來的事件；Executor 本身雖然是 cronjob 觸發喚醒，但醒來後改用 min-heap（最小堆）在 pod 內部做事件驅動排程，而不是單純的固定間隔輪詢（interval polling）。
2. **coding-harness-design**：NOOA 風格的 typed state，以及「pass by reference」的設計原則——大量資料透過 pandas/SQLite 傳遞，而不是整包塞進 LLM 的 context；generator/evaluator 搭配 human-in-the-loop 的驗證關卡。
3. **engineering.md**：你慣用的專案結構——common/ 放共用基礎設施，worker 負責 pubsub 事件邏輯與例外處理（message-seam 的 ack/nack），monitor 負責業務流程判斷，helper/utility 處理細節函式。
4. **ai-searchable-knowledge-base**：你認為 naive RAG 對於「把人類可讀的知識轉成 AI 可搜尋格式」這件事是不夠的——這個結論其實跟「大資料集不該整包塞進 context，要用結構化查詢」是同一個原則的兩種應用場域。

把這四個放在一起看，會發現它們共同指向同一個業界經典模式——**Reconciliation Loop + Precise Timer（協調迴圈 + 精確計時器）**，這正是排程系統（scheduler）與工作流引擎（workflow engine）領域幾十年來反覆出現的標準架構。

## 業界經典範例：Scanner/Executor 分工 + Timing Wheel

這個模式在業界有非常具體的先例可以對照：

- **Apache Airflow 的 Scheduler / Executor 分工**：Scheduler 持續掃描（scan）DAG 定義與 metadata DB，判斷哪些 task 到期該跑（這就是你的 Scanner 在做的事——讓「排程表」保持新鮮），然後把真正要執行的工作交給 Executor（Celery/Kubernetes Executor）去分派。Scheduler 關心「什麼時候該跑、跑的計畫有沒有變」，Executor 關心「現在就把這個任務跑起來」——兩者職責明確分離。
- **Quartz Scheduler 的 misfire 機制**：Quartz 用一個優先權佇列（本質上就是 min-heap）管理所有 trigger 的下次觸發時間，內部只需要不斷 peek 堆頂就知道「下一個要發生的事件是什麼時候」，是 O(log n) 插入、O(1) 取得最近事件，遠比每秒輪詢一次「現在幾點、誰到期了」有效率；同時 Quartz 另外有一個「misfire 偵測」機制，定期核對排程表跟現實世界有沒有脫節（例如伺服器當機錯過了觸發時間），這跟你 Scanner 的角色幾乎一模一樣。
- **Kafka 的 Purgatory + Hierarchical Timing Wheel**：Kafka 需要同時管理數以百萬計的「延遲請求」（例如等待多個 replica 都寫入完成才回應 client），如果每個延遲請求都用一個 timer thread 去等，系統會被壓垮；Kafka 借用 Linux kernel 的 timing wheel 演算法，用階層式的時間輪取代單一 min-heap，在請求量極大時把插入/刪除都做到接近 O(1)。這說明同一個「用資料結構取代輪詢」的原則，會隨著規模不同演化出不同的實作（小規模用 min-heap 就夠，巨量並發才需要 timing wheel）。

你在 earnings-pipeline 裡「Executor 醒來後改用 min-heap 做內部排程，而不是固定間隔輪詢」的決定，其實就是在重新實作 Quartz/Airflow 這類排程系統解決的同一個問題：**如何讓系統既能精準地在對的時間點觸發事件，又不必為了精準而燒 CPU 做無意義的輪詢**。

## 使用場景（Use Case）

想像一個具體的交易日：早上 8 點，Scanner cronjob 醒來，去掃一輪即將公佈財報的公司清單，發現某家公司把財報時間從原訂的下午 4 點延後到隔天早上——這是「現實世界的排程本來就會變動」，Scanner 的工作就是把這個變動寫回資料庫，讓「事件行事曆」隨時保持正確。與此同時，Executor pod 也是被 cronjob 定期喚醒（例如每 10 分鐘一次），但它醒來之後不會傻傻地每 10 分鐘才檢查一次「現在有沒有事件到期」——它會把目前資料庫裡「未來即將發生」的事件全部載入一個 min-heap，堆頂就是最近的下一個事件，用一個 sleep-until-next-event 的迴圈,精準地在事件發生的那一刻觸發，而不是等到下一次 cronjob 週期才發現「已經晚了 9 分鐘」。中間如果 Executor 觸發了一個需要 LLM 幫忙摘要財報內容的動作，資料量可能是幾百列的歷史財務數字，這時候不會把整張表格塞進 prompt，而是丟進一個暫存的 SQLite，讓 agent 用 SQL 查詢它需要的欄位——這就是 pass by reference 在真實資料流裡的樣子。

## 為什麼採用這些技術（Why）

Scanner 跟 Executor 分成兩個獨立的 cronjob，是因為「排程表要不要更新」跟「事件要不要觸發」是兩種完全不同節奏、不同重要性的工作：前者可以容忍稍微的延遲（財報時間改了,晚個幾分鐘發現沒關係）,後者一旦錯過觸發窗口就沒有意義。把兩者混在同一支程式裡,會讓「檢查行事曆有沒有變」跟「精準觸發」互相拖累彼此的節奏,這正是你在 coding-harness-design 裡強調的 deep-module 概念的延伸——**介面要窄、職責要單一**,一個模組只回答一個問題。

Executor 內部用 min-heap 而非固定間隔輪詢，是因為固定間隔輪詢（例如每分鐘檢查一次）天生就有「精準度」與「資源消耗」的取捨：間隔調短則觸發夠精準但浪費運算資源去做大量空轉檢查,調長則省資源但觸發時間會有系統性的延遲誤差。Min-heap 讓系統永遠只關心「下一個」該發生的事件,用事件驅動（event-driven）取代時間驅動（time-driven）,這跟你在 log-pipeline-architecture 用 completion marker 取代固定時間緩衝、用「訊號」取代「猜測的時間差」,是同一個核心原則在不同場景下的體現。

用 NOOA 的 pass by reference 而不是把大量資料直接塞進 LLM context,是因為 context 是有限且昂貴的資源——塞進去的資料越多,單次呼叫的成本越高,模型也越容易在長 context 中「迷失」重要細節（這也呼應了 ai-searchable-knowledge-base 那邊「純粹把大量內容丟給 AI 讀」不如「先結構化、讓 AI 用查詢的方式取用」的結論）。讓 agent 透過程式碼（SQL/pandas）去查詢它真正需要的那一小部分資料,而不是每次都全量傳輸,這正是 typed state 加上「code as action」的具體實踐。

common/ 平台模組加上 worker/monitor/helper 的分層,是為了讓「訊息傳輸層的錯誤處理」（worker 負責的 pubsub ack/nack）跟「業務邏輯層的判斷」（monitor 負責決定要不要真的觸發這個事件）不要糾纏在一起——如果一次 pubsub 訊息處理失敗,你會想知道那是「網路傳輸出問題,該重試」還是「業務邏輯本身判斷有誤,重試也沒用」,這兩種失敗需要完全不同的應對方式,分層讓這個判斷變得容易稽核。

## 重點要解決的問題

把這四個概念合在一起看,這個架構真正要解決的問題可以歸納成四點:第一,**精準度與資源消耗的取捨**——用 min-heap／timing wheel 取代固定間隔輪詢,讓系統只在真正該醒來的時候醒來,而不是不斷猜測「是不是時候了」。第二,**「排程表是否新鮮」與「觸發是否精準」要分開處理**——Scanner 負責讓行事曆貼近現實世界的變動,Executor 負責在對的時間點精準開火,混在一起會讓兩種節奏互相干擾。第三,**避免把大量資料無差別地塞進 LLM context**——用 pass by reference（SQLite/pandas 加上結構化查詢）取代整包傳輸,同時降低成本與模型判斷失準的風險,這個原則在「事件觸發後需要 AI 摘要資料」與「把人類知識庫轉成 AI 可搜尋格式」這兩個看似無關的場景裡其實是同一件事。第四,**傳輸層錯誤與業務邏輯錯誤要能分辨**——worker 層的 ack/nack 只回答「這則訊息有沒有處理成功」,真正該不該執行的商業判斷留給 monitor,這樣出問題時才能快速定位是哪一層出錯。

## 延伸一步:如果把 human-in-the-loop 也用上

如果 Executor 觸發的動作涉及真的會影響決策的自動化行為（例如根據財報數字自動生成一份給交易員參考的摘要,甚至觸發下單邏輯的前置判斷）,可以把 coding-harness-design 的 generator/evaluator 模式搬過來:generator 負責在事件觸發當下產出摘要或建議動作,evaluator（或真人）負責在動作被真正執行前,快速核對「這個判斷有沒有明顯不合理的地方」（例如摘要引用了不存在的數字、建議動作與歷史模式明顯矛盾）,只有通過這道關卡才放行。這讓「用 min-heap 做到精準觸發」跟「觸發後的動作是否可信」變成兩個獨立但互補的驗證層——時間精準只解決「什麼時候做」,human-in-the-loop 解決「做的內容對不對」。
