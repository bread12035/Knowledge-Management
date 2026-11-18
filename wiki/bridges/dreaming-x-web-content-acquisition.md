---
id: dreaming-x-web-content-acquisition
title: Dreaming 的不可信 transcript ↔ Agent 上網的不可信網頁
type: bridge
summary: 兩邊都讓 agent 讀不受控的文字；共同對策是當資料不當指示、縮小權限與爆炸半徑、關鍵動作交人
domains: [ai-new-tech, system-design]
sources: [raw/ai-new-tech/anthropic-agent-memory-guide.md#8.3, raw/ai-new-tech/anthropic-agent-memory-guide.md#8.8, raw/system-design/web-fetch-crawler-api-browser-agent-comparison.md#6, raw/system-design/web-fetch-crawler-api-browser-agent-comparison.md#5.3, raw/system-design/earnings-pre-earnings-gcp-to-onprem-handover-pattern.md#確認清單, raw/system-design/webhook-idempotent-worker-outbox-pattern.md#Why]
evidence: [Cookbook, 官方文件, 討論結論, 我的判斷]
related: [dreaming, web-content-acquisition, injected-context, gateway-authn-service-authz, km-dreaming-design]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Dreaming 的不可信 transcript ↔ Agent 上網的不可信網頁

> 兩邊都讓 agent 讀不受控的文字；共同對策是當資料不當指示、縮小權限與爆炸半徑、關鍵動作交人

## 對照
| | AI new tech：[[dreaming]] | System design：[[web-content-acquisition]] |
| --- | --- | --- |
| 解決的問題 | transcript 裡的 prompt injection 會改寫記憶庫並影響之後所有 session {Cookbook} | 抓回的網頁可能夾帶 prompt injection，加上敏感資料有外洩風險 {官方文件} |
| 機制 | analyzer 沒有 shell 與網路；transcript 當資料不當指示；記憶庫唯讀掛載 {Cookbook} | `allowed_domains` 白名單；不讓同一 agent 同時接觸網頁與機密；高風險動作人確認 {官方文件}{討論結論} |
| 代價 / 限制 | 每晚模式預設沒有審查 {Cookbook} | 白名單限制了能找到的資料；每步都要模型判斷，慢且貴 {討論結論} |

## 共同原理
- 不可信輸入只能影響「資料」，不能變成「指示」。
- 限縮爆炸半徑：讀不可信內容的角色，給最少的工具與權限。
- 寫進會被廣泛讀取的地方（記憶庫、[[injected-context]]、下游系統）之前，要有一道檢查。
- 和 webhook 的原則相同：外部輸入不信任它自稱的來源，在入口驗證（[[gateway-authn-service-authz]]）{討論結論}

## 差異
- Dreaming 的輸入是自己系統產生的紀錄，風險在「曾經被注入過」；上網的輸入完全外部，每一頁都可能有惡意內容 {我的判斷}
- 上網還有合規問題：被擋就停、不繞過 bot 政策 {討論結論}

## 在設計中怎麼用
設計任何讓 agent 讀外部文字的流程時，逐項確認：
- 這個 agent 有哪些工具？
- 能寫到哪裡？
- 輸出會被誰讀？
- 有沒有白名單與成本上限？
- 寫進常駐層前有沒有檢查？

這個 repo 也照這個做：`CLAUDE.md` 規定 raw 與 note 是資料不是指示，PRIMER 不放未經整理的 raw 文字（[[km-dreaming-design]]）。

## 相關
- [[dreaming]]、[[web-content-acquisition]]：兩端的細節
- [[injected-context]]：被注入時影響最大的一層
- [[gateway-authn-service-authz]]：入口驗證
- [[km-dreaming-design]]：本 repo 的做法
