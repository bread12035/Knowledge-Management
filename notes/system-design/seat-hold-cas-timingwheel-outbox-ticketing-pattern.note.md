---
raw: raw/system-design/seat-hold-cas-timingwheel-outbox-ticketing-pattern.md
raw_sha256: bf4b707b380273298bd2df8c33e6abca0038eb3c42bfa113359bace6f9a9e907
source: system-design
title: 業界經典範例整合：演唱會選位 Seat Hold — CAS 搶位 + Timing Wheel 到期釋放 + Outbox 出票
generated: 2026-11-22
---
# 業界經典範例整合：演唱會選位 Seat Hold — CAS 搶位 + Timing Wheel 到期釋放 + Outbox 出票（note）

## 一句話
座位分兩步賣：先用 CAS 暫時占住並設到期時間，再付款買下；到期由 min-heap reaper 釋放，付款與釋放兩邊都用條件寫入，由資料庫決定唯一贏家，出票事件用 outbox 和座位狀態一起 commit。

## 主張
原文是排程自動合併的整理文，沒有證據標記；一律標 {討論結論}。程式範例的數字（600 秒、t=650 等）是教學示意，標 {示意}。

### §合併了哪些概念
- 本篇合併三個既有概念：CAS 搶座位、min-heap / timing wheel 釋放過期保留、outbox 在付款成功後發出出票事件 {討論結論} (§合併概念)

### §業界經典範例
- Ticketmaster、KKTIX、拓元：選位後座位保留 10 分鐘，時間到沒付款就回到市場 {討論結論} (§業界範例)
- Booking.com、Airbnb 訂房先暫扣房間、付款後才確認；航空公司 PNR hold 保留到某時間點，過期自動取消 {討論結論} (§業界範例)
- 這類設計叫 Seat Hold：先「暫時占住」，再「付款買下」 {討論結論} (§業界範例)

### §故事
- 兩人同時以 version = 0 搶同一座位，資料庫一次只執行一個 UPDATE；後到者條件不成立、更新 0 列，回「這個位子剛被選走」 {示意} (§故事 Step 1)
- 保留期內記錄 `hold_id` 與 `hold_until`；到期沒付，reaper 在 deadline 醒來把座位放回 `free` {示意} (§故事 Step 2–3)
- 付款成功在同一個 transaction 把座位改成 `sold` 並寫一筆 outbox（`ticket-<hold_id>`），出票服務之後讀 outbox 寄票 {示意} (§故事 Step 4)
- 過期後才到的付款，以舊 `hold_id` 條件更新失敗 → 拒絕並觸發退款，座位不會賣兩次 {示意} (§故事 Step 5)

### §為什麼採用這些技術
- 搶位用 CAS 不用悲觀鎖：開賣時多數人點不同座位，衝突少，搶輸只要重選、代價低，符合「衝突少、重做便宜 → 樂觀鎖」 {討論結論} (§Why)
- 若用悲觀鎖，每人都先 `SELECT ... FOR UPDATE` 佔住連線，開賣尖峰時連線池會先爆 {討論結論} (§Why)
- 釋放用 min-heap 不用每秒掃全表：幾萬筆保留中多數未到期，min-heap 只看堆頂；百萬級改用 Kafka 式 hierarchical timing wheel，插入與到期接近 O(1) {討論結論} (§Why)
- 釋放也用 CAS：reaper 的 UPDATE 帶 `WHERE hold_id = ? AND status = 'held'`，付款先成功時 reaper 更新 0 列 {討論結論} (§Why)
- 付款的 UPDATE 帶 `hold_until > now`，所以就算 reaper 還沒跑，過期付款也會被拒絕；兩邊都是條件寫入，誰先到都不出錯 {討論結論} (§Why)
- 出票用 outbox 不直接呼叫 API：先改 DB 再呼叫 API，API 失敗會「賣了但沒票」；出票服務用 `event_id` 去重，重送只出一張 {討論結論} (§Why)

### §重點要解決的問題
- 四個問題四個解法：超賣 → CAS；占位不付 → `hold_until` + min-heap reaper；付款與到期競態 → 兩邊 CAS、資料庫決定贏家；賣了沒出票 → outbox {討論結論} (§重點問題)

### §可執行範例
- 四組 golden case：兩人搶同位、保留過期後他人買下、過期付款被拒、付款先到時 reaper 不動作；SQLite 模擬全部 PASS {討論結論} (§範例)
- Postgres 搶位語句：`UPDATE seats SET status='held', hold_id=$1, hold_until=now()+interval '10 min', version=version+1 WHERE id=$2 AND status='free' AND version=$3`；rowcount = 0 回前端「位子剛被選走」 {討論結論} (§範例)

### §下一步
- 下一個概念：Virtual Waiting Room，在流量進到 CAS 前先排隊限流，避免開賣瞬間打爆資料庫 {討論結論} (§下一步)

## 變更
- （首次產生）

## 候選連結
- wiki：optimistic-concurrency-x-pessimistic-lock（CAS 選擇規則的實例）、pessimistic-lock、event-driven-timer、lease-reaper（同為「到期回收」）、transactional-outbox、idempotent-consumer、golden-regression-gate、reliable-event-processing
- ai-new-tech：optimistic-concurrency（`content_sha256` 的軟性認領任務 ↔ CAS 搶位；D3 的 claim 沒有到期時間，seat hold 有 `hold_until` + reaper）
