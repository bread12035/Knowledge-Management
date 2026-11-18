---
source_project: system design & code style
source_file: claude/webhook-idempotent-worker-outbox-pattern.md
title: 業界經典範例整合：Idempotent Webhook Gateway + Worker/Monitor 職責分離 + Explicit Completion Signal（Transactional Outbox 模式）
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：Idempotent Webhook Gateway + Worker/Monitor 職責分離 + Explicit Completion Signal（Transactional Outbox 模式）

> 本篇由排程自動整理，隨機挑選過去討論中的概念合併而成，作為「system design & coding style」專案的知識累積。

## 這次合併了哪些概念

這次從專案裡挑了三個過去在不同情境下各自出現、但骨子裡都在回答「外部事件進來之後，系統該怎麼安全且正確地處理」這個問題的概念，合併成一個完整的實作範例：

1. **engineering.md（common/worker/monitor/helper 分層）**：worker 負責處理 pubsub 訊息層的例外與 ack/nack（「這則訊息有沒有處理成功」），monitor 負責業務流程的判斷（「這件事實際上該不該發生」）；兩者職責明確分離，且你有「用 module/seam 邊界當 fixed point，每次改動後人工複查過去結果是否還成立」的習慣。
2. **log-pipeline-architecture（completion marker 取代固定時間緩衝）**：資料是否可讀，用一個明確的完成訊號（signal）去判斷，而不是靠猜一個固定的時間差；下游消費者用「事件」而非「時間」來同步。
3. **chat-service-auth-design（Authentication／Authorization 分層）**：Client 端的請求先在 Gateway 層做 Authentication（驗證這則請求真的來自宣稱的來源、簽章有沒有被竄改），通過之後才進到後端做 Authorization（這個來源能不能觸發這個業務動作）；驗證規則（issuer、算法白名單）寫死在 Gateway 端，不信任呼叫方宣稱的來源。

把這三個放在一起看，會發現它們正好對應到「接收外部系統送進來的事件（webhook）」這件事裡三個缺一不可的層面：**這個事件真的是合法來源送的嗎（access）**、**這個事件我是不是已經處理過了（idempotency / completion signal）**、**傳輸層失敗跟業務邏輯判斷錯誤要怎麼分開處理（worker vs monitor）**。這正是 Stripe、GitHub、Shopify 這類平台的 webhook 處理架構，以及微服務領域裡 Transactional Outbox / Idempotent Consumer 模式反覆出現的標準做法。

## 業界經典範例

這個模式在業界有具體的先例可以對照：

- **Stripe 官方推薦的 Webhook 處理架構**：Stripe 送出的每個 event 都帶有簽章（signature），接收端第一步一定是驗證這個簽章是不是真的用你的 webhook secret 簽出來的——這一步完全獨立於「這個 event 要不要處理」的業務邏輯，正是 chat-service-auth-design 裡「Authentication 集中在 Gateway、不信任呼叫方宣稱來源」的具體場景。驗證通過之後，Stripe 官方文件明確建議：先回 200 表示「我收到了」，把真正的處理丟到背景 worker，並且用 event 本身的 idempotency key 去判斷「這個 event 我是不是已經處理過」——如果同一個 event 因為網路重試被送了兩次，不能因此把同一筆款項扣兩次帳。這個 idempotency key 的角色，跟你在 log-pipeline-architecture 裡用 completion marker 判斷「這批資料是否已經完整、可以往下處理」，本質上是同一件事：**用一個明確的、可核對的訊號，取代「猜這應該是新的」的假設**。
- **GitHub Webhooks + 背景 Worker（Sidekiq / Resque 這類 job queue）的經典組合**：GitHub 送 webhook 時會在 header 帶一個 `X-Hub-Signature`，接收端的 Web 層（相當於你的 worker）唯一的工作就是驗證簽章、把 payload 丟進 job queue、然後立刻回應——不在這一層做任何業務判斷。真正「這個 PR 該不該觸發 CI」「這個 push 事件該不該通知團隊」的判斷，留給背景 job（相當於你的 monitor）去做。如果 Web 層在驗證訊息格式時失敗，它會回一個 4xx 讓 GitHub 重試；但如果背景 job 判斷「這個分支不在白名單裡，不用觸發」，那是一個成功處理、只是決定不動作，這兩種失敗/決定不該混在同一層——這正是 worker（傳輸層 ack/nack）跟 monitor（業務判斷）分離的價值。
- **Chris Richardson 在 microservices.io 提出的 Transactional Outbox / Idempotent Consumer 模式**：這是微服務領域處理「事件要怎麼可靠地被送出跟消費」的經典手法。發送端把「業務資料的變更」跟「要發出的事件」寫進同一個資料庫交易（transaction），避免「資料改了但事件沒送出」或「事件送了但資料沒改成功」這種不一致；消費端則要做到 Idempotent Consumer——就算同一個事件因為 at-least-once 的傳輸語意被重複送達，也要能靠一個明確的「已處理事件 ID」記錄，判斷這次是不是重複，不會重複執行業務邏輯。這跟你 completion marker 的精神完全一致，只是一個用在「批次資料是否完整」，一個用在「單筆事件是否已處理」。

你在 log-pipeline-architecture 裡「用 completion marker 取代固定時間緩衝」的判斷，跟 Stripe/GitHub 用 idempotency key 判斷「這個 event 是不是新的」，其實是同一個業界共識的兩種應用場域：**同步與去重的依據，應該是明確的信號（signal），而不是時間或次數的猜測**。

## 使用場景（Use Case）

想像你的系統要接收一個上游合作夥伴（例如金流服務商，或是內部另一個團隊的服務）用 webhook 送過來的事件——「這筆訂單的付款狀態變成已完成」。請求先打到 Gateway：Gateway 第一步驗證這個請求的簽章是不是真的用雙方約定的 secret 簽出來的，issuer 跟允許的簽章演算法都寫死在 Gateway 端，不接受請求本身宣稱「我是誰」。驗證通過之後，Gateway 不會自己決定「這筆訂單要不要標記完成」，而是把這個已驗證身份的事件轉給 worker。

Worker 這一層唯一關心的是「這則訊息有沒有被正確接收並存進暫存區」——它會先檢查這個事件的 ID 有沒有出現在「已處理事件」的記錄裡（completion marker 的角色，這裡是以事件為單位而非以批次為單位）。如果是重複送達（例如上游因為沒收到 ack 而重試），worker 直接 ack 掉、不往下傳，避免同一筆付款被處理兩次；如果是新事件，才把它放進 queue 交給 ack/nack 機制保護，網路層失敗就 nack 讓上游重試，跟業務邏輯完全無關。

真正判斷「這筆訂單狀態該不該從『處理中』轉成『已完成』、要不要觸發後續的出貨流程」，是 monitor 層的工作——它讀到的已經是「保證只會處理一次、身份也已經驗證過」的事件，可以專心做業務判斷,不用再操心「這個請求到底安不安全」「這個事件是不是重複的」這些跟業務邏輯無關的問題。

## 為什麼採用這些技術（Why）

Authentication 集中在 Gateway、寫死 issuer 與演算法白名單，是因為外部合作夥伴送進來的 webhook 本質上是「不受信任的輸入」——如果信任請求 header 裡宣稱的來源，等於給了偽造請求可乘之機（例如惡意方直接打你的 endpoint,宣稱自己是合法的付款服務商）。把這一層驗證收斂到 Gateway,讓後面的 worker 跟 monitor 都可以安心假設「進來的事件身份是真的」,不用每一層都重新驗證一次,這跟 chat-service-auth-design 裡的判斷完全一致。

用明確的「已處理事件 ID」記錄（completion marker 的事件版本）而不是猜測,是因為 webhook 的傳輸語意通常是 at-least-once——上游為了保證訊息一定送達,寧可重複送也不要漏送,所以接收端一定要有能力判斷「這個我是不是已經處理過」。如果沒有這個機制,任何網路抖動造成的重試都可能讓同一筆業務動作被執行兩次,在金流這類場景裡這是不能接受的錯誤;而如果用「猜」的方式(例如假設同個 event 短時間內不會重複送達,所以不用檢查),等於把系統的正確性建立在一個不可靠的假設上,這正是 log-pipeline-architecture 裡「用信號取代猜測的時間差」原則的延伸應用。

worker 跟 monitor 分層,是因為「這則訊息有沒有安全地被接收、有沒有重複」跟「這個業務動作實際上該不該發生」是兩個完全不同層次的關注點,混在一起會讓除錯變得困難——如果一筆付款狀態沒有正確更新,你會想先分辨「是網路傳輸層根本沒收到這則訊息」還是「訊息收到了,但業務邏輯判斷有誤」,這兩種問題需要完全不同的人去查、用完全不同的方式修。把這兩層分開,也讓「重試」這個動作變得安全:worker 層的重試只是「再送一次同一個訊息」,不會因為業務邏輯被重複觸發而產生副作用,因為去重的判斷已經在更上游的地方做掉了。

## 重點要解決的問題

把這三個概念合在一起看,這個架構真正要解決的問題可以歸納成三點:第一,**外部輸入的身份必須先被集中驗證,才能讓下游安心處理**——webhook 本質上是攤在公開網路上的 endpoint,任何人都可以嘗試打它,把 Authentication 收斂到 Gateway 一層,是防止偽造事件混入系統的第一道關卡。第二,**at-least-once 的傳輸語意下,重複事件必須被明確識別、而不能靠猜**——用一個可核對的「已處理事件 ID」記錄取代「假設不會重複」的僥倖心態,才能在網路重試發生時,保證業務動作只被執行一次。第三,**傳輸層的成功與否,跟業務邏輯的判斷結果,必須能被獨立追蹤**——worker 只回答「這則訊息有沒有安全存進系統」,monitor 只回答「這個已保證唯一的事件該怎麼處理」,出問題時才能快速定位到底是哪一層出錯,也才能讓「重試」這個動作永遠是安全的。

## 延伸一步:如果把 generator/evaluator 也接上來

如果這個 webhook 系統接收的事件,後續需要更複雜的自動化判斷(例如根據付款事件自動生成一份對帳摘要,或是根據事件內容自動決定要不要觸發退款流程),可以把 coding-harness-design 裡的 generator/evaluator 模式接到 monitor 這一層:generator 根據已驗證、已去重的事件內容,生成建議的處理動作(例如「這筆訂單狀態應該更新為已完成,並觸發出貨通知」);evaluator(或是真人在關鍵動作前的複核)負責在動作真正被執行前,核對這個建議有沒有明顯不合理之處(例如金額對不上、訂單狀態轉換不符合預期的狀態機路徑)。這樣一來,「事件是否合法、是否重複」(access + idempotency)解決的是「這個輸入能不能信任」,而 generator/evaluator 解決的是「根據這個輸入做出的業務判斷對不對」——兩層驗證各自獨立,卻共同組成一套更完整的事件驅動處理系統。
