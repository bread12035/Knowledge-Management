---
id: memory-salience
title: 寫筆記：預測、salience 與 steering（Memory salience）
type: concept
summary: 寫記憶是預測；強模型自己判斷什麼值得記比固定規則好，告訴它目的而不是規定怎麼用
domains: [ai-new-tech]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#3]
evidence: [原文, 我的判斷]
related: [agent-memory, injected-context, km-dreaming-design]
status: active
created: 2026-11-18
last_dreamed: 2026-11-22
review_count: 1
next_review: 2026-11-29
---
# 寫筆記：預測、salience 與 steering（Memory salience）

> 寫記憶是預測；強模型自己判斷什麼值得記比固定規則好，告訴它目的而不是規定怎麼用

## 重點
- 寫下記憶就是在預測：規則預測模式會重複，已驗證的事實預測之後可以直接信賴 {原文}
- Salience 是「什麼值得記」：Fable 5 只存畫面看不到的策略、計畫與測試過的規則，用 9 個檔案拿 4 枚徽章；Sonnet 3.7 什麼都存，413 個檔案只拿 1 枚 {原文}
- 詳細紀錄會因狀態變動而過期，還讓 agent 花更多力氣搜尋記憶 {原文}
- 「只記錄失敗」這條固定規則拿掉大部分記憶增益（Opus 5 −0.234）{原文}
- Steering 對舊模型幫助最大：Sonnet 4.6 加「先讀記憶、測試理論」從 0.364 升到 0.641 {原文}

## 細節
- CL-Bench 1.0（無記憶 → 有記憶）：Opus 5.5 0.655 → 0.838；Opus 5 0.564 → 0.828；Opus 4.7 0.383 → 0.700；Sonnet 4.6 0.330 → 0.364 {原文}
- Opus 5 第一個完全閉合學習迴圈：條目含規則、證據、之前問題的答案、陷阱警告 {原文}
- Fable 5 的 `global.md` 像儀表板：目前目標、預先寫好的計畫、使用記憶的規則 {原文}

## 在設計中怎麼用
- 給前沿模型的指示：使用者要求時、或明顯值得記時才寫，其餘交給模型判斷 {原文}
- 指示寫「記憶的目的」，例如「讓下一個 session 更快開始：寫決定、踩過的坑、確認過的做法」，不要寫死規則 {我的判斷}
- 一條好筆記的形狀：規則 + 證據 + 適用條件 + 陷阱。
- 這個 repo 的 note 規則（`CLAUDE.md` §3）就是照這個原則寫的。

## 相關
- [[agent-memory]]：筆記是第 2 層
- [[injected-context]]：最常被讀的筆記放這裡
- [[km-dreaming-design]]：note 怎麼觸發與寫入
