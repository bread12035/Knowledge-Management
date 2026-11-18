---
id: dreaming
title: Dreaming（記憶整合）
type: concept
summary: 離線回頭檢視 transcripts 與現有記憶，校正錯誤、建 wiki、提升關鍵筆記、補缺口
domains: [ai-new-tech]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#6, raw/ai-new-tech/anthropic-agent-memory-guide.md#7, raw/ai-new-tech/anthropic-agent-memory-guide.md#8]
evidence: [原文, 官方文件, Cookbook, 我的判斷]
related: [agent-memory, llm-wiki, injected-context, single-writer, pass-by-reference, km-dreaming-design, harness2, dreaming-x-web-content-acquisition]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Dreaming（記憶整合）

> 離線回頭檢視 transcripts 與現有記憶，校正錯誤、建 wiki、提升關鍵筆記、補缺口

## 重點
- 一個 session 只看得到自己的 context，寫筆記時不知道之後需要什麼；dreaming 讓 Claude 事後回頭整理 {原文}
- 五個用途：校正記憶、建立 [[llm-wiki]]、把關鍵筆記提升到 [[injected-context]]、依目標聚焦、補上缺口 {原文}
- 原文只說在離線或閒置時執行，沒有指定觸發方式或排程 {原文}
- 成本是主要限制：建議集中在易變資訊，或依存取頻率調整 dreaming 頻率 {原文}
- 表示層需要持續運算維護，否則會累積錯誤或幻覺 {原文}

## 細節
- **校正：** Pokémon Mt. Moon 中，dreaming 對照 transcript 改正「PokéCenter 在東側」的錯誤，Claude 在第 1,935 個動作到達 Cerulean；未校正與無記憶都沒到 {原文}
- **聚焦：** 通用指示讓多個 agent 寫同一張表，57 個事實只剩 41 個；改成每份合約一頁後全部保留。本質是並行寫入衝突，修法是 [[single-writer]] {原文}{我的判斷}
- **補缺口：** 第二次 dreaming 把 9 個指向不存在頁面的連結改指向既有頁，條目 38→41、連結 225→278 {原文}
- **兩種實作：**
  - Dreams API：讀一個記憶庫加 1 到 100 個 session，輸出新記憶庫，輸入不改；`instructions` 是高層引導不是編輯器 {官方文件}
  - Cookbook DIY：lead + 每份 transcript 一個 analyzer + 最後一個 organizer；任務只傳路徑（[[pass-by-reference]]）；11 份 transcript 約 $0.36 {Cookbook}
- Cookbook 的 organizer 規則：重複合併留 `MOVED TO` stub；較晚的更正採新值，否則寫 `CONFLICT:` 不猜 {Cookbook}

## 在設計中怎麼用
- 什麼情況用：記憶由多個 session 零散寫入、會過期、會重複時。
- 怎麼用：讀不可信的原始紀錄當資料不當指示；每頁單一寫入者；跑完對帳（預期、處理、失敗）。
- 代價：每次執行都花 token；每晚模式預設沒有人工審查。
- 這個 repo 的做法見 [[km-dreaming-design]]。

## 相關
- [[agent-memory]]：dreaming 整理的四層
- [[harness2]]：另一種「事後回顧、存下有效教訓」的機制
- [[km-dreaming-design]]：這個知識庫的 dreaming 設計
- [[dreaming-x-web-content-acquisition]]：跨領域：不可信輸入的共同對策
