# Knowledge-Management

由 Claude 維護的 LLM wiki。依 `raw/ai-new-tech/anthropic-agent-memory-guide.md` 的四層記憶模型設計。

```
[project 排程 ×2]     → raw/<source>/                L1 Transcript（逐字原文）
[Claude Code 排程]    → notes/ → wiki/ → PRIMER.md   L2 Note → L3 Wiki → L4 Injected context
```

| 路徑 | 內容 |
| --- | --- |
| `raw/ai-new-tech/`、`raw/system-design/` | 兩個 project 匯出的原文（只增不刪） |
| `notes/` | 每份原文抽出的原子化主張 |
| `wiki/` | 主題頁；入口 `wiki/_index.md` |
| `review/` | 每週複習週報 |
| `PRIMER.md` | 閱讀入口（≤ 4,096 字元），可貼進 project instructions |
| `dream/` | 處理狀態、執行紀錄、bridge 候選 |
| `prompts/` | 三個排程的 prompt |
| `CLAUDE.md` | wiki 維護規則（consumer 自動載入） |
| `scripts/km.py` | 變更偵測、目錄重建、lint |

## 排程

| 排程 | 在哪裡 | 時間（Asia/Taipei） | Prompt |
| --- | --- | --- | --- |
| AI new tech 匯出 | claude.ai project「AI new tech & studies」 | 每天 01:20 | `prompts/project-export-ai-new-tech.md` |
| System design 匯出 | claude.ai project「system design & code style」 | 每天 01:50 | `prompts/project-export-system-design.md` |
| Dreaming | Claude Code 雲端排程（本 repo） | 每天 03:10；週日為 deep 模式 | `prompts/dream.md` |
