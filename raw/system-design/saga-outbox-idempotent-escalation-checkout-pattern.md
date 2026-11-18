---
source_project: system design & code style
source_file: claude/saga-outbox-idempotent-escalation-checkout-pattern.md
title: 業界經典範例整合：電商結帳 Saga（補償交易）= Outbox + Idempotent Consumer + Escalation
first_exported: 2026-11-18
updated: 2026-11-18
---
# 業界經典範例整合：電商結帳 Saga（補償交易）= Outbox + Idempotent Consumer + Escalation

> 本篇由排程自動整理（2026-11-09）。隨機挑選 3 篇過去文件：`transactional-outbox-lease-reaper-idempotent-consumer-pattern`、`dunning-retry-webhook-idempotent-timingwheel-pattern`、`pagerduty-escalation-chatops-runbook-pattern`。其中 dunning 文件的「下一步學習」正是 Saga，這次補上。

## 1. 這次合併了哪些概念

| 來源 | 取用的概念 | 在本範例的角色 |
|---|---|---|
| outbox + lease | Transactional Outbox、Lease、Idempotent Consumer | 每個 Saga 步驟的事件可靠送出，重送不會重做 |
| dunning | 重試 + idempotency key | 每一步失敗先重試，不要馬上回滾 |
| pagerduty | Escalation | 補償也失敗或重試用盡，通知人處理 |
| （新）Saga | 補償交易（compensating transaction） | 跨服務沒有分散式交易，失敗時反向抵銷 |

## 2. 業界經典對照

- **Saga Pattern（Hector Garcia-Molina, 1987；microservices.io）**：長流程拆成多個本地交易。每一步有對應的補償動作。
- **Uber Cadence / Temporal、AWS Step Functions**：把 Saga 狀態持久化，重試與補償由引擎管理。
- **Stripe / 訂票系統**：先預留、再扣款、再出貨；失敗就退款、釋放庫存。

## 3. 使用場景（小而完整）

情境：客戶下單。流程是 reserve（保留庫存）→ charge（扣款）→ ship（出貨）。三個服務，三個資料庫。

- Step 1：Orchestrator 對 `o2` 發 `reserve`。成功。Outbox 記下事件。
- Step 2：發 `charge`。成功。
- Step 3：發 `ship`。倉庫系統故障。重試 3 次（idempotency key = `o2:ship`），仍失敗。
- Step 4：Orchestrator 反向補償：先 `refund`，再 `release`。每個補償也帶 key，重送只做一次。
- Step 5：訂單標成失敗。若補償本身失敗，進 dead-letter，並 page 值班人員。

輸入：`o2`，ship 一直失敗。輸出：客戶沒被扣款，庫存已釋放，日誌是 `reserve, charge, refund, release`。

## 4. 為什麼採用這些技術

- **Saga，而非分散式交易（2PC）**：三個服務不共用資料庫。2PC 會鎖資源，且協調者當機就卡住。
- **補償，而非 rollback**：已經扣款的錢不能「撤銷」，只能「退款」。補償是新的業務動作。
- **Idempotency key**：重試與補償都會重送。沒有 key，客戶會被退款兩次。
- **Outbox**：「狀態更新」和「發下一步事件」要同一個交易，否則 Saga 會中途斷掉。
- **Escalation**：自動補償不是萬能。最後一道防線是人。

## 5. 重點要解決的問題

1. 跨服務沒有 transaction，如何保持一致。解法：Saga + 補償。
2. 失敗後重複動作。解法：Idempotency key。
3. Saga 流程中途斷掉。解法：Outbox + Lease Reaper。
4. 補償也失敗。解法：Dead-letter + Escalation。

## 6. 可執行範例（已驗證輸出）

```python
class Svc:
    def __init__(s): s.done=set(); s.log=[]
    def run(s,key,name,fn):            # idempotent step
        if key in s.done: return
        fn(); s.done.add(key); s.log.append(name)

def saga(order, fail_at=None, attempts_max=3):
    S=Svc(); steps=[("reserve","release"),("charge","refund"),("ship","cancel_ship")]
    applied=[]
    for step,comp in steps:
        ok=False
        for a in range(attempts_max):
            if step==fail_at: continue
            S.run(f"{order}:{step}",step,lambda:None); ok=True; break
        if not ok:
            for _,c in reversed(applied): S.run(f"{order}:{c}",c,lambda:None)
            return S.log,"DEAD_LETTER->page on-call"
        applied.append((step,comp))
    return S.log,"OK"
```

輸出：

```
saga("o1")                  -> ['reserve','charge','ship'], OK
saga("o2", fail_at="ship")  -> ['reserve','charge','refund','release'], DEAD_LETTER->page on-call
```

## 7. 設計提醒

- Saga 狀態要存資料庫。記憶體狀態重啟就丟。
- 補償必須可重複執行，且不可失敗到無法處理。
- Orchestration（中央協調）易除錯；Choreography（事件接力）耦合低但難追蹤。先用前者。
- 新增 golden cases：全成功、中途失敗、補償失敗三條路徑，改流程前先跑。

## 8. 下一步學習

最自然的下一個概念：**Orchestration vs Choreography**（Saga 該由誰指揮）。
