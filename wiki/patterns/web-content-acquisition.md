---
id: web-content-acquisition
title: 取得網頁資料的階梯（Web content acquisition）
type: pattern
summary: 官方 API → 背後 JSON → web fetch → headless / 爬蟲服務 → browser agent，由便宜到貴；被擋就停交人，網頁內容一律當不可信輸入
domains: [system-design]
sources: [raw/system-design/web-fetch-crawler-api-browser-agent-comparison.md#2, raw/system-design/web-fetch-crawler-api-browser-agent-comparison.md#5.4, raw/system-design/web-fetch-crawler-api-browser-agent-comparison.md#6, raw/system-design/http-api-vs-html-curl-cloudflare-bot-policy.md#3, raw/system-design/http-api-vs-html-curl-cloudflare-bot-policy.md#5.3, raw/system-design/price-watch-tiered-fetch-cas-outbox-freshness-pattern.md#Why]
evidence: [討論結論, 官方文件]
related: [deterministic-over-llm, earnings-gcp-onprem-handover, dreaming-x-web-content-acquisition]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# 取得網頁資料的階梯（Web content acquisition）

> 官方 API → 背後 JSON → web fetch → headless / 爬蟲服務 → browser agent，由便宜到貴；被擋就停交人，網頁內容一律當不可信輸入

## 重點
- HTTP 是協定；curl、web fetch、瀏覽器是客戶端；API 與 HTML 是回傳形式。先找 API，沒有才讀 HTML {討論結論}
- 關鍵判斷：要的資料在「檢視原始碼」裡，web fetch 就夠；不在就需要能執行 JS 的瀏覽器 {討論結論}
- 分層抓取依成本由低到高；遇到 403 或 Cloudflare 挑戰就停、記為 `<source>:blocked` 交給人，不偽裝、不升級繞過 {討論結論}
- Browser agent 以「快照 → 決定 → 動作 → 再快照」運作；重複固定的動作寫成複合工具，模型只做判斷 {討論結論}
- Web fetch 遇到不可信輸入加上敏感資料時有資料外洩風險；Claude 的 web fetch tool 可用 `allowed_domains` 限制網域 {官方文件}

## 細節
- 中間路線：網頁背後常是 JS 呼叫 JSON API，用 F12 Network 找到網址直接打（SEC `data.sec.gov`、TWSE OpenAPI）{討論結論}
- API 是有合約的固定格式；HTML 沒有合約，網站改版程式或模型就可能讀錯（例如單位在表格上方被漏看）{討論結論}
- Cloudflare 四種動作：放行、限速（429）、挑戰、封鎖（403）；User-Agent 容易偽造不能當身分證明 {討論結論}
- Browser agent 用 accessibility tree 快照（只留可互動元素並編號）而不是原始 DOM（常幾十萬 token）；每次動作後等頁面穩定再快照，編號會重算 {討論結論}
- 無限捲動背後常是分頁（`?page=2`），找到規律就直接 web fetch 逐頁抓 {討論結論}
- 記下每筆資料的來源層級，可統計「多少靠 browser 才拿到」當成本指標 {討論結論}

## 在設計中怎麼用
- 設計 agent 上網時：定網域白名單、每次執行的搜尋或抓取次數與成本上限、輸出要附可點回的來源。
- 不讓同一個 agent 同時接觸不可信網頁內容與機密資料；高風險動作要人確認。
- 被擋商品或頁面交給 freshness watchdog 浮出給人處理（申請 API、聯絡對方）。

## 相關
- [[deterministic-over-llm]]：固定動作寫成工具，LLM 只做判斷
- [[earnings-gcp-onprem-handover]]：Pre-earnings 只靠 web search + fetch 的實例
- [[dreaming-x-web-content-acquisition]]：跨領域：不可信輸入的共同對策
