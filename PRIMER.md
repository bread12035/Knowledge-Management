# Knowledge-Management Primer

由 Claude 維護的 LLM wiki，整合「AI new tech & studies」與「system design & code style」兩個 project 的討論。更新：2026-11-18（deep）。

## 怎麼用
- 查東西：先讀 `wiki/_index.md`，再讀相關頁，沿 `[[slug]]` 走；需要原文時看頁面 `sources` 指向的 `raw/`。
- 引用：`KM:<slug>`，對應 `wiki/**/<slug>.md`；slug 不改名。
- 可信度看 `{標記}`：原文 / 官方文件 > 討論結論 > 我的判斷；`{使用者決定}` 是已做的決定，不必重談。
- 跨領域連結在 `wiki/bridges/`。複習看 `review/` 週報。

## 主題入口
- Agent 記憶與 dreaming：KM:agent-memory
- Agent harness 與省 token：KM:agent-harness-design
- AI 評估：KM:ai-evaluation
- 可靠的事件處理：KM:reliable-event-processing
- 知識檢索設計：KM:knowledge-retrieval-design
- Earnings 流程與 GCP ↔ on-prem：KM:earnings-gcp-onprem-handover

## 反覆出現的原則
- 每份資料只有一個寫入者；做不到才用樂觀或悲觀鎖，重做昂貴（LLM 呼叫）時避免樂觀鎖：KM:single-writer、KM:optimistic-concurrency-x-pessimistic-lock
- 能用程式決定的不交給 LLM；LLM 只判斷意思：KM:deterministic-over-llm
- 大資料留在環境，prompt 只放 handle 與預覽：KM:pass-by-reference
- 用明確信號取代猜測的時間差：KM:completion-marker
- at-least-once 加冪等，得到只生效一次：KM:idempotent-consumer、KM:transactional-outbox
- 入口小、細節往下找；常駐層只放規則與指標：KM:progressive-disclosure、KM:injected-context
- 新教訓先 pending，重複出現且有證據才升級：KM:promotion-gate
- 改規則前先跑 golden cases；改版決策看主指標加護欄：KM:golden-regression-gate、KM:primary-guardrail-gate
- 外部文字是資料不是指示；縮小權限、關鍵動作交人：KM:dreaming-x-web-content-acquisition

## 已做的決定（不必重談）
- 使用者 agent system 的五層記憶與升級規則：KM:agent-system-memory-layers
- Dreaming 實作 D1–D5 與本 repo 的分工：KM:km-dreaming-design
- 專案分層 common / worker / monitor / helper：KM:worker-monitor-split
- Gateway 做 AuthN、服務做 AuthZ，白名單寫死：KM:gateway-authn-service-authz
- 規模小時預設一個 Postgres：KM:postgres-hub
