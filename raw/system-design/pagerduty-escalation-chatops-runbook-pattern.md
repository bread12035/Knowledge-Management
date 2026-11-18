---
source_project: system design & code style
source_file: claude/pagerduty-escalation-chatops-runbook-pattern.md
title: 業界經典範例整合：Timing-Wheel Escalation Engine + Authenticated ChatOps Gateway + Structured Runbook Retrieval
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Timing-Wheel Escalation Engine + Authenticated ChatOps Gateway + Structured Runbook Retrieval

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。

## 這次合併了哪些概念

這次從專案裡挑了三個表面上分屬不同主題、但骨子裡都在回答「值班/事故處理系統該怎麼設計」這個問題的概念，合併成一個完整的實作範例：

1. **earnings-pipeline（Scanner/Executor + min-heap 排程）**：用兩個角色分工——一個負責讓「排程表」保持新鮮（偵測變動），一個負責在對的時間點精準觸發（event-driven，而非固定間隔輪詢）；Executor 內部用 min-heap 只關心「下一個」該發生的事件。
2. **chat-service-auth-design（Authentication／Authorization 分層）**：Client 從 Keycloak 拿到 JWT，由 API Gateway 集中做 Authentication（驗證簽章、驗證 issuer），後端 Service 只管 Authorization（這個人能不能做這件事）；realm URL 與演算法白名單寫死在 Gateway 端，不信任 Client 宣稱的來源。
3. **ai-searchable-knowledge-base（Structured Retrieval 取代 naive RAG）**：公司內部知識庫是為人類閱讀而寫的 HTML（含表格、截圖），naive RAG 的向量相似度檢索會拆散表格的欄位對應關係；正確做法是先把內容轉成有明確 schema 的結構化資料，再用查詢（query）取代語意猜測（guess）。

把這三個放在一起看，會發現它們正好對應到「值班/事故應變系統」裡三個缺一不可的層面：**什麼時候該通知誰（timing）**、**通知的管道跟身份怎麼驗證（access）**、**被通知的人該怎麼快速查到正確的處理步驟（knowledge）**。這正是 PagerDuty、Opsgenie 這類 on-call 平台，以及 ChatOps 事故應變機器人反覆出現的標準架構。

## 業界經典範例

這個模式在業界有具體的先例可以對照：

- **PagerDuty / Opsgenie 的 Escalation Policy（升級策略）引擎**：一個事件觸發後，如果值班的第一線工程師在指定時間內沒有 acknowledge，系統要自動「升級」通知下一層（例如 team lead、on-call manager）。這套引擎的核心跟你在 earnings-pipeline 裡「Executor 用 min-heap 做內部排程」是同一個問題——同時間可能有成百上千個「等待升級」的計時器在跑，如果每個都用固定間隔輪詢去檢查「時間到了沒」，會浪費大量運算資源；用優先權佇列（min-heap，或規模更大時像 Kafka Purgatory 那樣用 hierarchical timing wheel）只需要 peek 堆頂，就知道下一個該升級的事件是什麼時候，時間到了才醒來。
- **Slack ChatOps 機器人（例如 Slack 官方的 workflow bot、Netflix 的 ChatOps 內部工具）**：值班工程師收到通知後，通常會在 Slack 裡直接跟 bot 互動——「這個 alert 之前發生過嗎」「這支服務的 runbook 在哪」。這些請求最終都要打到後端的 API Gateway，而 Slack、PagerDuty webhook、內部 App 三種不同來源的呼叫，都需要走同一套集中式的身份驗證，這正是 chat-service-auth-design 裡「Authentication 集中在 Gateway，Service 只管 Authorization」的具體場景：Gateway 要先確認「這真的是 Slack/PagerDuty 送來的合法請求」，而不是讓每個下游服務各自驗證一次簽章。
- **Runbook 自動化平台（例如 Rundeck、內部 Confluence + 搜尋外掛）常見的失敗模式**：多數公司一開始都是把 runbook 寫成給人看的 wiki 頁面，事故發生時工程師手忙腳亂地用關鍵字全文搜尋，常常找到的是過時或部分相關的頁面。比較成熟的做法（呼應 Uber QueryGPT / Microsoft GraphRAG 的思路）是把 runbook 拆解成結構化資料——「服務名稱、症狀、對應處理步驟、負責團隊」變成一張表的欄位，事故發生時用查詢（依服務名稱、症狀關鍵字過濾）取代對整份 wiki 做向量相似度比對，才不會因為 chunk 切斷段落而遺失「這個症狀對應哪個處理步驟」的精確關係。

你在這三個過去討論裡分別得出的判斷——「排程用 event-driven 取代 polling」「認證要集中在 Gateway」「知識檢索要用結構化查詢取代向量猜測」——組合起來，其實就是在重新拼出一套完整的 on-call 事故應變系統該有的樣子。

## 使用場景（Use Case）

想像凌晨兩點，生產環境某支服務的錯誤率突然飆高，監控系統觸發一個 incident。Escalation Engine 立刻用 min-heap 排出「如果 5 分鐘內沒人 ack，就升級給下一位」的計時器——這裡不能用固定間隔輪詢（例如每分鐘掃一次所有 pending incident），因為同時間可能有數百個不同嚴重程度、不同升級時限的計時器在跑，min-heap 讓系統只在真正該醒來的那一刻醒來，不多浪費一次 CPU cycle。

通知送到值班工程師的 Slack 之後，他在 Slack 裡直接問 ChatOps bot：「這支服務上一次發生類似錯誤是什麼時候，當時怎麼處理的？」這個請求會經過 API Gateway：Gateway 先驗證這則訊息真的來自合法的 Slack workspace（Authentication），確認身份後才把請求轉給後端服務判斷「這位工程師有沒有權限看這支服務的事故記錄」（Authorization）。通過驗證後，後端不會傻傻地把整份 runbook wiki 塞給 LLM 做語意搜尋，而是用結構化查詢——依服務名稱、錯誤訊息關鍵字，去查詢一張「症狀 → 處理步驟 → 負責團隊」的結構化資料表——精準撈出對應的處理步驟跟過去類似事故的記錄，而不是回傳一堆語意相近但可能過時或答非所問的段落。

## 為什麼採用這些技術（Why）

Escalation 計時器用 min-heap 而非固定間隔輪詢，原因跟 earnings-pipeline 一致：固定間隔輪詢天生要在「精準度」跟「資源消耗」之間取捨——輪詢間隔調短會精準但浪費運算資源做大量空轉檢查，調長則會有系統性的觸發延遲。事故升級這種場景對「延遲」特別敏感（多等一分鐘可能就是多一分鐘的生產環境故障），所以用事件驅動（event-driven）的 min-heap，讓系統永遠只關心「下一個」該升級的事件，是精準度跟資源消耗這對取捨下更好的解法。

Authentication 集中在 API Gateway、不讓每個下游服務各自驗證，是因為身份驗證的邏輯（這則訊息真的來自 Slack/PagerDuty 嗎、簽章對不對）本質上跟「業務邏輯要不要授權這個操作」是兩個完全不同層次的關注點。如果讓每個下游服務各自實作一套驗證，不只是重複勞動，更危險的是容易出現前面提過的經典漏洞——相信呼叫方宣稱的來源、而不是用寫死在 Gateway 端的白名單去驗證，等於給了偽造請求可乘之機。把 Authentication 收斂到一個地方，其餘服務只要專心回答「這個已驗證身份的人，能不能做這件事」。

Runbook 檢索改用結構化查詢而非 naive RAG，是因為「服務名稱對應哪個處理步驟」本質上是精準的欄位對應關係，而不是語意相近的問題——把這種資料硬塞進向量相似度框架，等於用猜的方式回答一個其實有標準答案的問題。事故當下工程師需要的是「馬上跳到正確的處理步驟」，而不是「讀幾段語意相關但可能過時的文字自己判斷」，這正是 structured retrieval 用查詢取代猜測的核心價值，在時間壓力最大的場景裡體現得最明顯。

## 重點要解決的問題

把這三個概念合在一起看，這個架構真正要解決的問題可以歸納成三點：第一，**通知與升級的時效性**——事故應變最怕的就是「該通知的人沒被準時通知到」，用 min-heap／timing wheel 這類事件驅動的資料結構取代固定間隔輪詢，才能在不燒資源的前提下做到精準觸發。第二，**多種呼叫來源的身份要能被統一、可信地驗證**——Slack、PagerDuty webhook、內部 App 都可能是觸發或查詢事故的入口，如果每個入口各自驗證身份，既難維護也容易留下偽造請求的漏洞；把 Authentication 收斂到 Gateway 一層，才能讓安全政策一致且可稽核。第三，**事故當下的知識檢索要精準、不能靠猜**——凌晨兩點手忙腳亂時，工程師沒有時間篩選一堆語意相關但答非所問的段落；把 runbook 轉成結構化資料、用查詢取代向量相似度猜測，才能在最需要準確答案的時刻，真正給出準確答案。

## 延伸一步：如果把 generator/evaluator 也用上

如果想讓這套系統再進一步自動化，可以把 coding-harness-design 裡的 generator/evaluator 模式接上來：generator 在事故發生當下，根據結構化查詢到的歷史記錄跟症狀，自動生成一份「可能原因＋建議處理步驟」的摘要；evaluator（或真人值班工程師）在真正採取行動前，快速核對這份摘要有沒有明顯不合理的地方（例如引用了不存在的服務、建議的處理步驟跟歷史模式明顯矛盾）。這樣一來，「精準地在對的時間通知對的人」（timing）解決的是「什麼時候該做」，而 generator/evaluator 加上 human-in-the-loop 解決的是「AI 建議的處理方式對不對」——兩層驗證各自獨立、互不干擾，卻共同組成一套更完整的事故應變自動化系統。
