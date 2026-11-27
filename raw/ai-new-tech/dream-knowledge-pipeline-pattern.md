---
source_project: AI new tech & studies
source_file: claude/dream-knowledge-pipeline-pattern.md
title: Dream：知識自動整理與多跳查詢架構
first_exported: 2026-11-28
updated: 2026-11-28
---
# Dream：知識自動整理與多跳查詢架構

## 1. 背景
你在兩個 claude.ai Projects（AI new tech & studies、system design & code style）學習。
Dream 把這些對話自動收進 GitHub repo `bread12035/Knowledge-Management`，整理成 LLM wiki，再用 skill `ask-knowledge-manager` 查詢。

注意：以下細節是我推論的，不是你的正式規格。請在第 6 節確認。

Whiteboard：https://claude.ai/artifact/58ttyVoBYz9LEiGDsD4WWF

## 2. 流程圖（文字版，虛線 = related 連結）

```
[Claude.ai]                     [GitHub repo]
1. Projects ──> 2. 排程任務 ──> 3. raw/ ──> 4. Cronjob
                                                │
                                                ▼
                         5. wiki/ 知識圖 (concept / pattern / topic / decision)
                              9a ─────> 10 (related, 第 2 hop)
                              ┆          ┆
                              9b         topic ┄┄ decision
                              ▲
6. 你提問 ──> 7. ask-knowledge-manager ──> 8. _index.md ──┘
                 │
                 ▼
            11. 新說明（問是否上網補充）
```

## 3. 步驟與小例子
輸入：你在 Project 討論「Agent memory」。

| Step | 動作 | 輸出 |
|---|---|---|
| 1 | 你在 Project 對話並寫 note | session transcript、note |
| 2 | Scheduled task 抓出內容，推到 repo | `raw/<source>/<slug>.md` |
| 3 | Cronjob 讀 raw/，建頁、寫 `related`、更新 `_index.md` | `wiki/agent-memory.md` 等頁 |
| 4 | 你問「我的知識庫有沒有 agent memory？」 | 問題 |
| 5 | Skill 先讀 `_index.md`，選 3 到 5 頁 | 第 1 hop 頁 |
| 6 | 需要時沿 `related` 多走一層 | 第 2 hop 頁 |
| 7 | 整理成新說明，並問要不要上網補充 | 答案 + 缺口 |

## 4. 元件說明
**Scheduled task**：定時從 Project 抓內容。它像是郵差，每天固定收信。不同點：它只收信，不整理。

**Cronjob**：定期把 raw/ 變成 wiki 頁，並寫 `related`。它像是圖書館員，把新書分類、貼標籤。不同點：標籤（related）建立的是頁與頁的關係，不是分類架子。

**wiki 知識圖**：每頁是一個 node，`related` 是 edge。它像是維基百科的內部連結。不同點：連結由 LLM 判斷相關性，不是人工加。

**`_index.md`**：每頁一行 summary 的入口。它像是書的目錄。不同點：它用語意選頁，不是關鍵字比對。

**ask-knowledge-manager**：唯讀 skill。讀 index、選頁、沿 related 最多多走一層，再整理成新說明。每次回答後都問是否上網補充。

## 5. 設計理由
| 元件 | 為什麼放這裡 |
|---|---|
| raw/ 與 wiki/ 分開 | 原始資料不改，整理結果可重建 |
| Cronjob | 不用每次討論後手動整理 |
| `_index.md` | 先用一份小檔縮小範圍，不用掃全部頁 |
| 只走一層 related | 避免離題與讀太多 |
| 每次問是否上網 | wiki 沒寫的不用自己的知識補 |

相關文件：`claude/Ontology 與 Knowledge Graph 指南`、`claude/Anthropic Agent Memory 整理指南`。

## 6. 要和自己確認的清單
- 第二個 Project 是否就是「system design & code style」？
- Cronjob 實際跑在哪裡（Claude scheduled task、GitHub Actions，或別處）？
- Scheduled task 是否同時抓 transcript 和 note，還是兩個任務？
- `related` 由 Cronjob 一次寫入，還是每次更新都重算？
- 第 2 hop 的上限是否維持一層？

## 7. 下一步
下一個要學的概念：Cronjob 怎麼判斷兩頁「相關」並寫出 `related`。
