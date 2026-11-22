---
id: seat-hold
title: 兩段式保留與到期釋放（Seat hold）
type: pattern
summary: 先用 CAS 暫時占住並設到期時間，再確認買下；到期由 reaper 釋放，確認與釋放兩邊都用條件寫入，讓資料庫決定唯一贏家
domains: [system-design]
sources: [raw/system-design/seat-hold-cas-timingwheel-outbox-ticketing-pattern.md#業界經典範例, raw/system-design/seat-hold-cas-timingwheel-outbox-ticketing-pattern.md#為什麼採用這些技術, raw/system-design/seat-hold-cas-timingwheel-outbox-ticketing-pattern.md#重點要解決的問題, raw/system-design/seat-hold-cas-timingwheel-outbox-ticketing-pattern.md#可執行範例（SQLite 模擬；四組 golden case 全部 PASS）]
evidence: [討論結論, 示意, 我的判斷]
related: [pessimistic-lock, event-driven-timer, lease-reaper, transactional-outbox, idempotent-consumer, golden-regression-gate, reliable-event-processing, optimistic-concurrency-x-pessimistic-lock]
status: active
created: 2026-11-22
last_dreamed: 2026-11-22
review_count: 0
next_review: 2026-11-29
---
# 兩段式保留與到期釋放（Seat hold）

> 先用 CAS 暫時占住並設到期時間，再確認買下；到期由 reaper 釋放，確認與釋放兩邊都用條件寫入，讓資料庫決定唯一贏家

## 重點
- 稀缺資源分兩步賣：先「暫時占住」（`held` + `hold_until`），再「付款買下」（`sold`）；Ticketmaster、KKTIX 保留 10 分鐘，訂房暫扣、航空 PNR hold 同理 {討論結論}
- 搶位用 CAS 不用悲觀鎖：開賣時多數人點不同座位，衝突少、搶輸只要重選；悲觀鎖的 `SELECT ... FOR UPDATE` 會讓尖峰時連線池先爆 {討論結論}
- 到期釋放用 min-heap 只看最早到期的那筆，不每秒掃全表；百萬級改用 hierarchical timing wheel（[[event-driven-timer]]）{討論結論}
- 付款與到期的競態靠兩邊都是條件寫入解決：reaper 帶 `hold_id = ? AND status = 'held'`，付款帶 `hold_until > now`；誰先到都不會超賣 {討論結論}
- 「座位變 sold」與「要出票」用 [[transactional-outbox]] 同一個 transaction commit；出票服務用 `event_id` 去重（[[idempotent-consumer]]）{討論結論}

## 細節
搶位語句（Postgres）{討論結論}：
```sql
UPDATE seats
SET status = 'held', hold_id = $1, hold_until = now() + interval '10 min', version = version + 1
WHERE id = $2 AND status = 'free' AND version = $3;
-- rowcount = 0 → 回前端「位子剛被選走」
```
- 付款：`UPDATE ... SET status='sold' WHERE id=? AND hold_id=? AND status='held' AND hold_until>?`；成功才寫 outbox，失敗就 rollback 並退款 {討論結論}
- 晚到的付款（保留已過期）以舊 `hold_id` 條件更新失敗 → 拒絕並退款；即使 reaper 還沒跑也一樣 {示意}
- 四條 golden cases：兩人搶同位、保留過期後他人買下、過期付款被拒、付款先到時 reaper 不動作 {討論結論}
- 和 [[lease-reaper]] 是同一個結構：領取時設到期時間，到期沒完成就放回；差別是 lease 回收的是工作，hold 回收的是資源 {我的判斷}
- 下一步：Virtual Waiting Room 在流量進到 CAS 之前先排隊限流 {討論結論}

## 在設計中怎麼用
- 什麼情況用：有限資源要先占再確認，中間有一段使用者或外部系統的延遲（付款、審核、填表）。
- 怎麼用：
  1. 每列帶 `status`、`hold_id`、`hold_until`、`version`。
  2. 占住、確認、釋放三個動作都是條件 UPDATE，看 rowcount 判斷成敗。
  3. 到期用 event-driven timer 觸發，不輪詢全表。
  4. 確認與發事件放同一個 transaction。
  5. 先寫好上面四條 golden cases（[[golden-regression-gate]]）。
- 代價：保留期間資源對其他人不可用，TTL 太長浪費、太短讓人來不及付款；晚到的付款要有退款路徑 {我的判斷}

## 相關
- [[pessimistic-lock]]：為什麼這裡選 CAS
- [[optimistic-concurrency-x-pessimistic-lock]]：跨領域：重做成本決定鎖的選擇；AI 端的任務認領缺少到期時間
- [[event-driven-timer]]：到期釋放的計時
- [[lease-reaper]]：同結構，回收的是工作
- [[transactional-outbox]]、[[idempotent-consumer]]：出票只發生一次
- [[reliable-event-processing]]：整體脈絡
