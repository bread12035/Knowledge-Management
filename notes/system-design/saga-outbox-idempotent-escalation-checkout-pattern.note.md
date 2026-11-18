---
raw: raw/system-design/saga-outbox-idempotent-escalation-checkout-pattern.md
raw_sha256: 1e0287e02805f1b88837d58a0d87d8beca2a91d842359c1f1f9d8a9912351002
source: system-design
title: 業界經典範例整合：電商結帳 Saga（補償交易）= Outbox + Idempotent Consumer + Escalation
generated: 2026-11-18
---
# 業界經典範例整合：電商結帳 Saga（補償交易）（note）

## 一句話
跨服務結帳（reserve → charge → ship）用 Saga 取代 2PC：每步本地交易 + transactional outbox 可靠送出，失敗先帶 idempotency key 重試，用盡就反向補償，補償也失敗則 dead-letter 並 escalate 給值班人員。

## 主張
證據標記對應：原文由排程自動整理，沒有證據標記 → 全部 {討論結論}（§6 程式碼原文自稱「已驗證輸出」，仍標 {討論結論}）。

### §1 合併了哪些概念
- 合併 `transactional-outbox-lease-reaper-idempotent-consumer-pattern`、`dunning-retry-webhook-idempotent-timingwheel-pattern`、`pagerduty-escalation-chatops-runbook-pattern`，補上 dunning 文件的「下一步學習」Saga {討論結論} (§1)

### §2 業界經典對照
- Saga Pattern（Hector Garcia-Molina, 1987）把長流程拆成多個本地交易，每步有對應補償動作 {討論結論} (§2)
- Uber Cadence／Temporal、AWS Step Functions 把 Saga 狀態持久化，由引擎管理重試與補償 {討論結論} (§2)

### §3 使用場景
- Orchestrator 依序發 reserve → charge → ship；ship 用 idempotency key `o2:ship` 重試 3 次仍失敗，就反向補償 refund → release，訂單標失敗 {討論結論} (§3)
- 補償本身失敗時進 dead-letter 並 page 值班人員 {討論結論} (§3)

### §4 為什麼採用這些技術
- 三個服務不共用資料庫；2PC 會鎖資源，且協調者當機就卡住，所以用 Saga {討論結論} (§4)
- 已扣款不能撤銷只能退款：補償是新的業務動作，不是 rollback {討論結論} (§4)
- 重試與補償都會重送；沒有 idempotency key，客戶可能被退款兩次 {討論結論} (§4)
- 「狀態更新」和「發下一步事件」要同一個交易（outbox），否則 Saga 會中途斷掉 {討論結論} (§4)
- 自動補償不是萬能，最後一道防線是人（escalation）{討論結論} (§4)

### §5 重點要解決的問題
- 四個問題對應四個解法：跨服務一致性 → Saga + 補償；重複動作 → idempotency key；流程中途斷 → Outbox + Lease Reaper；補償失敗 → dead-letter + escalation {討論結論} (§5)

### §6 可執行範例
- 範例中每步以 `{order}:{step}` 為 key 去重；`saga("o2", fail_at="ship")` 產生 `['reserve','charge','refund','release']` 與 `DEAD_LETTER->page on-call` {討論結論} (§6)

### §7 設計提醒
- Saga 狀態要存資料庫，記憶體狀態重啟就丟 {討論結論} (§7)
- 補償必須可重複執行，且不可失敗到無法處理 {討論結論} (§7)
- Orchestration 易除錯、Choreography 耦合低但難追蹤；先用 orchestration {討論結論} (§7)
- 改流程前先跑三條 golden cases：全成功、中途失敗、補償失敗 {討論結論} (§7)

### §8 下一步學習
- 下一步學 Orchestration vs Choreography {討論結論} (§8)

## 變更
- （首次產生）

## 候選連結
- system-design：dunning-retry-webhook-idempotent-timingwheel-pattern、transactional-outbox-lease-reaper-idempotent-consumer-pattern、pagerduty-escalation-chatops-runbook-pattern、webhook-idempotent-worker-outbox-pattern
- wiki：golden-dataset（golden cases 回歸）、single-writer（orchestrator 集中指揮）、agent-harness-design（狀態持久化與重試）
