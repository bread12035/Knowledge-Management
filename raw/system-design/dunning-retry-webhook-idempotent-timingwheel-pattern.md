---
source_project: system design & code style
source_file: claude/dunning-retry-webhook-idempotent-timingwheel-pattern.md
title: 業界經典範例整合：訂閱扣款失敗重試系統（Dunning）= Idempotent Webhook + Min-Heap/Timing Wheel 排程 + Worker/Monitor 分層
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：訂閱扣款失敗重試系統（Dunning）= Idempotent Webhook + Min-Heap/Timing Wheel 排程 + Worker/Monitor 分層

> 本篇由排程自動整理（2026-11-02）。隨機挑選 2 個過去的 pattern 文件合併：`webhook-idempotent-worker-outbox-pattern` 與 `scanner-executor-timingwheel-nooa-pattern`。這兩篇一篇管「事件怎麼安全進來」，一篇管「事件怎麼精準在未來觸發」。合起來正好是一個完整的業界經典：**訂閱制服務的扣款失敗重試（Dunning）**。

## 1. 這次合併了哪些概念

| 來源 | 取用的概念 | 在本範例的角色 |
|---|---|---|
| webhook-idempotent-worker-outbox | Gateway 驗簽（Authentication）、Idempotent Consumer（已處理 event ID）、Transactional Outbox | 接收金流商的 `invoice.payment_failed` 事件，保證只處理一次 |
| webhook-idempotent-worker-outbox | worker（ack/nack）與 monitor（業務判斷）分層 | 傳輸錯誤和「要不要重試扣款」分開處理 |
| scanner-executor-timingwheel-nooa | Executor 用 min-heap／timing wheel 做 sleep-until-next-event | 精準在「第 1 天、第 3 天、第 7 天」觸發重試 |
| scanner-executor-timingwheel-nooa | Scanner 保持排程表新鮮（reconciliation） | 客戶中途更新信用卡時，取消或提前重試 |

## 2. 業界經典對照

- **Stripe Billing 的 Smart Retries / Dunning**：扣款失敗不是馬上停權。系統先寄通知，再在未來幾個時間點重試，最後才取消訂閱。Stripe 同時用簽章過的 webhook 通知你的後端狀態變化，並要求接收端冪等。
- **Netflix、Spotify 的「付款失敗寬限期」**：服務不會馬上斷。這給客戶時間更新卡片，減少非自願流失（involuntary churn）。
- **Kafka 的 Hierarchical Timing Wheel**：當要排程的「未來重試」多到百萬級，單一 min-heap 的 O(log n) 開始吃力，改用 timing wheel 讓插入與取消接近 O(1)。

## 3. 使用場景（一個小而完整的例子）

情境：SaaS 公司，月費 $30，客戶 Alice 的信用卡過期。

輸入與輸出，一步一步：

- Step 1：金流商送出 `invoice.payment_failed`（event id = `evt_001`，帶簽章）。
- Step 2：Gateway 驗簽。通過。Issuer 與演算法白名單寫死在 Gateway。
- Step 3：Worker 查「已處理 event ID 表」。`evt_001` 不在表內。Worker 在**同一個資料庫交易**中寫入：(a) 已處理記錄 `evt_001`；(b) outbox 事件 `PaymentFailed(alice)`。然後 ack。
- Step 4：金流商因為網路抖動又送了一次 `evt_001`。Worker 查表發現已處理，直接 ack，不再往下傳。
- Step 5：Monitor 讀到 `PaymentFailed(alice)`。業務判斷：這是第 1 次失敗，要排「第 +1 天、+3 天、+7 天」三次重試，最後 +7 天仍失敗就降級帳號。Monitor 把三個到期時間寫入 `retry_schedule` 表。
- Step 6：Executor（cronjob 喚醒）載入未來的 `retry_schedule` 到 min-heap。堆頂是 Alice 的 +1 天重試。Executor sleep 到那一刻，觸發重試扣款。
- Step 7：第 +2 天，Alice 更新了信用卡。Scanner 發現卡片狀態變了，把 Alice 剩餘的重試改為「立刻重試一次」。若成功，取消後面所有排程。

最終輸出：Alice 被扣款一次（不是兩次），服務沒有被誤停，她只收到一封該收的通知信。

## 4. 為什麼採用這些技術

- **Gateway 驗簽**：webhook 是公開 endpoint，任何人都能打。不驗簽，攻擊者可以偽造「付款成功」事件拿到免費服務。
- **Idempotent Consumer**：金流商保證 at-least-once（寧可重送不漏送）。沒有去重，一次網路重試就可能讓客戶被通知兩次，或排出兩組重試而重複扣款。
- **Transactional Outbox**：「記錄已處理」與「產生下游事件」在同一交易。這避免「標記已處理但事件遺失」，使客戶永遠沒被重試。
- **Worker／Monitor 分層**：worker 只回答「訊息安全收到了嗎」；monitor 只回答「該不該重試」。出錯時一眼可知是哪層。Worker 重試是安全的，因為去重在上游。
- **Min-heap 取代固定間隔輪詢**：固定每分鐘輪詢，不是浪費 CPU 就是遲到。堆頂永遠是下一個事件，精準且省資源。規模更大時換 timing wheel。
- **Scanner 分離**：「排程表是否仍正確」（客戶改卡、客服手動取消）和「到點觸發」節奏不同。分開，兩邊都簡單。

## 5. 重點要解決的問題

1. **重複扣款／重複排程**：at-least-once 傳輸加上冪等消費，保證業務動作恰好生效一次（effectively-once）。
2. **偽造事件**：身份集中在 Gateway 驗證。
3. **重試時間精準且低成本**：事件驅動排程，而不是輪詢猜時間。
4. **排程與現實脫節**：客戶改卡、退訂，Scanner 負責 reconcile，不會對已解約客戶重試。
5. **除錯可定位**：傳輸層、去重層、業務層、排程層各自可稽核。

## 6. 可延伸的設計提醒

- 重試動作本身也要冪等：扣款 API 帶 idempotency key（例如 `alice-2026-11-invoice-attempt-1`），避免 Executor 崩潰重啟後重打。
- Executor 崩潰時，heap 是記憶體狀態。重啟後從 `retry_schedule` 表重建。真相來源（source of truth）永遠是資料庫，不是 heap。
- 若要讓 LLM 草擬催款信：只傳 Alice 的 ID，讓 agent 用 SQL 查需要的欄位（pass by reference），並讓人或 evaluator 在寄出前複核。

## 7. 下一步學習

最自然的下一個概念：**Saga pattern**（把「扣款、開通、發票、通知」這種跨服務的多步驟流程，在任一步失敗時如何補償回滾）。
