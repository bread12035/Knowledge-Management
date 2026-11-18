---
id: km-dreaming-design
title: 使用者的 dreaming 實作決定（D1–D5）與本 repo
type: decision
summary: lead 改 optional、note 由 skill 或 workflow 寫、analyzer 做成 worker pool、note 與 transcript 配對
domains: [ai-new-tech]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#13]
evidence: [使用者決定, 我的判斷, OPTIONAL]
related: [dreaming, single-writer, optimistic-concurrency, memory-salience, agent-memory, injected-context]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 使用者的 dreaming 實作決定（D1–D5）與本 repo

> lead 改 optional、note 由 skill 或 workflow 寫、analyzer 做成 worker pool、note 與 transcript 配對

## 重點
- D1：lead 改為 optional；日常流程固定，由確定性程式（cron 腳本）編排。理由：範例中 lead 佔約 47% 成本 {使用者決定}
- D2：note 由 skill（手動，覺得有意義時）或 workflow 最後一步（自動）寫 {使用者決定}
- D3：analyzer 做成 worker pool，軟性認領任務，用 `content_sha256` 防寫入衝突，最後 organizer 總結 {使用者決定}
- D4：同一 session 的 note 與 transcript 配對交給 analyzer，用 transcript 檢查 note；note 也當不可信輸入 {使用者決定}
- D5：文件三用（使用者、agent、實作參考）；遇到 OPTIONAL 先問使用者 {使用者決定}

## 細節
- 拿掉 lead 後要自己補：對帳、預算與逾時、並行寫入保護 {我的判斷}
- 未驗證的假設 V1 到 V6：例如檔案工具是否支援 precondition、不用 lead 能否啟動 workflow {我的判斷}
- O1 到 O12 是實作前必須問使用者的可選項目 {OPTIONAL}

**本 repo 的對應（2026-11-18 與使用者確認）：**
| 項目 | 做法 |
| --- | --- |
| L1 transcript | 兩個 project 排程把文件逐字匯出到 `raw/<source>/` |
| 編排（O1） | 沒有 lead；Claude Code 排程依 `prompts/dream.md` 執行，機械部分由 `scripts/km.py` 做 |
| 寫入保護 | [[single-writer]]：producer 只寫 raw，consumer 只寫其他路徑；push 衝突用 rebase 重試（[[optimistic-concurrency]] 的 git 版） |
| `_index.md`（O7） | 只由最後的 organizer 步驟重建 |
| 重試（O8） | push 最多 3 次；ingest 連續失敗 3 次標記 failed |
| 審查（O10） | 直接寫入 main，不開 PR；使用者看 `review/` 週報與 log |
| Injected context（O12） | `PRIMER.md` 每週（deep 模式）更新，由使用者決定是否貼進 project |

## 在設計中怎麼用
- 引用這頁說明這個知識庫為什麼這樣分工、哪些決定已經做了不必重談。
- 改動 `CLAUDE.md` 或 `prompts/dream.md` 前，先確認不違反 D1 到 D5。

## 相關
- [[dreaming]]：概念與 Anthropic 的兩種實作
- [[single-writer]]、[[optimistic-concurrency]]：寫入保護
- [[memory-salience]]：D2 的 note 怎麼寫
- [[agent-memory]]、[[injected-context]]：四層與 PRIMER
