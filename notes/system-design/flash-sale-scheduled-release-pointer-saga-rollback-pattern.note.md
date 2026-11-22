---
raw: raw/system-design/flash-sale-scheduled-release-pointer-saga-rollback-pattern.md
raw_sha256: f8a165153ab53015797370c540525d0beaf369c2624d9e04b407a60e56c58c64
source: system-design
title: 業界經典範例整合：黑色星期五「準點開賣」= Scanner/Executor 排程 + Release Pointer 發布 + Saga 回滾
generated: 2026-11-22
---
# 業界經典範例整合：黑色星期五「準點開賣」= Scanner/Executor 排程 + Release Pointer 發布 + Saga 回滾（note）

## 一句話
準點開賣要「準時、整組、可退回」：Scanner/Executor 決定何時發布，immutable release + pointer 讓整組價格原子生效，發布中途失敗用 Saga 補償把 pointer 指回上一版並 page 值班。

## 主張
原文是排程自動合併的整理文，沒有證據標記；一律標 {討論結論}。範例的時間與數字是教學示意，標 {示意}。

### §1 合併了哪些概念
- 三個概念各管一件事：Scanner/Executor 決定「什麼時候」發布、SSOT release + pointer 決定「發布什麼」與怎麼原子切換、Saga 決定「失敗時」怎麼退回 {討論結論} (§1)
- 本篇用 Saga 補償回答 SSOT 文件留下的「下一步：Rollback」 {討論結論} (§前言)

### §2 業界經典對照
- Shopify / Amazon Prime Day 的預約開賣、LaunchDarkly 的 scheduled flag change、Netflix / Spinnaker 的多步驟發布失敗自動 rollback {討論結論} (§2)

### §3 故事
- 用 cronjob 每 10 分鐘檢查，最晚會晚 9 分鐘開賣；改用 Executor 把排程放進 min-heap、sleep 到堆頂時間再觸發 {示意} (§3 第一個問題)
- Executor 醒來前 Scanner 可能已改時間，所以觸發前要重新讀排程表 {討論結論} (§3 第一個問題)
- 3000 個價格逐一寫進 GCS，service 可能讀到半新半舊；先整組上傳到不可變的 `r_0042/`，最後只改 `current.json`，改一個檔案是原子的 {討論結論} (§3 第二個問題)
- 發布三步：upload → switch pointer → purge CDN；CDN 回 503 重試 3 次仍失敗時，pointer 已切新版但 CDN 還送舊價，兩邊不一致 {示意} (§3 第三個問題)
- 補償動作：`switch` 的補償是 `switch_back`（pointer 改回 `r_0041`）；`upload` 的補償是 `keep_release`（什麼都不刪，release 保留當歷史） {討論結論} (§3 第三個問題)
- 每一步帶 idempotency key（例 `bf2026:switch_back`），重送只做一次；補償完成後 page 值班「開賣失敗，已回到上一版」 {討論結論} (§3 第三個問題)

### §4 控制權流動
- 行銷只寫 Postgres（SSOT）→ Scanner 寫排程 `(00:00, bf2026, r_0042)` → Executor 睡到 00:00 觸發 Saga → 成功則 pointer = `r_0042`；失敗則反向補償回 `r_0041` 並 page {討論結論} (§4)

### §5 可執行範例
- Store 以 step key 記錄已完成步驟做冪等；失敗時把已套用步驟的補償反向執行 {討論結論} (§5)
- 驗證輸出：全成功 log 為 upload、switch、purge_cdn；purge_cdn 失敗時 log 為 upload、switch、switch_back、keep_release，pointer 回 `r_0041` {討論結論} (§5)

### §6 為什麼採用這些技術
- Scanner/Executor 分開，避免「排程表新不新」與「準不準時」互相拖累 {討論結論} (§6)
- 用 Saga 補償而非 rollback transaction：GCS 與 CDN 不在同一個 transaction 裡，無法一起撤銷 {討論結論} (§6)
- Idempotency key 防止 Executor 重啟後重送讓 pointer 被切換兩次；escalation 處理補償也失敗的情況 {討論結論} (§6)

### §7 重點要解決的問題
- 準時 → Scanner + Executor + min-heap；整組生效 → immutable release + 原子切換 pointer；可退回 → Saga 補償 + idempotency key + escalation {討論結論} (§7)

### §8 設計提醒
- Pointer 切換本身就是最便宜的 rollback，只改一個檔案，所以補償很簡單 {討論結論} (§8)
- Release 永遠不刪；回滾不是「刪掉新的」，而是「指回舊的」 {討論結論} (§8)
- Executor 觸發前要再讀一次 Postgres，確認活動沒被取消 {討論結論} (§8)
- Saga 狀態要寫進 Postgres，Executor 重啟後才知道做到哪一步 {討論結論} (§8)
- Golden cases 三條路徑：全成功、purge_cdn 失敗、switch_back 也失敗 {討論結論} (§8)

### §9 下一步
- 下一個概念：service 如何得知 pointer 已變更（polling `current.json` vs 推播通知），決定客戶多快看到新價 {討論結論} (§9)

## 變更
- （首次產生）

## 候選連結
- wiki：single-source-of-truth（rollback 的答案）、saga-compensation（非 transaction 資源的補償）、event-driven-timer（觸發前重讀 SSOT）、idempotent-consumer、golden-regression-gate、reliable-event-processing
- ai-new-tech：dreaming / injected-context（PRIMER 是常駐層，等同「每個 session 都讀的 pointer」；錯誤擴散範圍類比 CDN 舊價）—關聯偏弱，先不建 bridge
