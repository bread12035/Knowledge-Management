---
raw: raw/system-design/http-api-vs-html-curl-cloudflare-bot-policy.md
raw_sha256: e84fe8bc63eb0866216a747cddb5ca5f92e1e39c826d1faebdec640f504d1dd7
source: system-design
title: HTTP API、網頁 HTML、curl 與 Cloudflare bot 政策
generated: 2026-11-18
---
# HTTP API、網頁 HTML、curl 與 Cloudflare bot 政策（note）

## 一句話
HTTP 是協定、curl／web fetch／瀏覽器是客戶端、JSON API 與 HTML 是回傳形式；取資料先找 API、沒有才讀 HTML；網站前的 Cloudflare 會依來源、方法、頻率、白名單決定放行、限速、挑戰或封鎖。

## 主張
原文沒有逐條證據標記，是一次學習討論的整理（2026-11-11）；一律標 {討論結論}。§5 的 Cloudflare 產品行為原文在文末列出 Cloudflare 官方文件為來源，但沒有逐條對應，仍標 {討論結論}，且只適用於 2026-11-11 當時的產品狀態。營收數字為示例。

### §1 一句話結論
- HTTP 是協定；curl、web fetch、瀏覽器是客戶端；API 與 HTML 是 server 回傳內容的形式，不是方法 {討論結論} (§1)
- 取資料的順序：先找 API，沒有 API 才讀 HTML {討論結論} (§1)

### §2 三個層次
- 三層：① 協定（HTTP）② 客戶端（curl、瀏覽器、web fetch、Python `requests`）③ 回傳形式（JSON API、HTML）{討論結論} (§2)
- 同一個客戶端（curl）可以請求 API 也可以請求網頁 {討論結論} (§2)

### §3 HTTP API 與網頁 HTML
- HTTP API 回傳給程式用、格式固定的資料（通常 JSON），像合約；HTML 給人看、沒有合約，網站改版程式或模型就可能讀錯 {討論結論} (§3)
- API 路線由程式理解資料，單位在欄位裡；web fetch 路線由模型從轉出的文字找值，單位在表格上方時容易漏看 {討論結論} (§3)
- 比較：API 穩定性高、結果可預測，常見阻礙是 API key 與流量限制；HTML 改版就壞、模型可能讀錯，常見阻礙是 bot challenge、cache、JS 渲染 {討論結論} (§3)
- 網站通常對網頁加 bot challenge，對有 key 的 API 較不擋 {討論結論} (§3)
- 同一份資料常有兩條路：SEC EDGAR 有 `data.sec.gov` JSON；台灣證交所有 OpenAPI（`openapi.twse.com.tw`），欄位要先自己確認；一般公司官網通常只有 IR 頁面 HTML {討論結論} (§3)
- 中間路線：網頁背後常是 JS 呼叫 JSON API，可用瀏覽器 F12 Network 分頁找出網址直接打，不必解析 HTML {討論結論} (§3)

### §4 curl 與 web fetch
- curl 照 HTTP 送請求、原樣輸出；web fetch 是 Claude 的工具，送請求後把 HTML 轉成文字或 markdown 交給模型 {討論結論} (§4)
- curl 與 web fetch 都不執行 JS，看到的都是原始 HTML {討論結論} (§4)
- 同一個 curl 指令結果不同，差別只在 URL 另一端回傳什麼 {討論結論} (§4)

### §5 Cloudflare 如何處理 bot 請求
- Cloudflare 是 reverse proxy 加 CDN；啟用代理後 DNS 回傳 Cloudflare 的 IP，請求先到 Cloudflare，它看到的來源 IP 來自連線本身 {討論結論} (§5.1)
- 判斷依據：來源（User-Agent、IP、簽章、TLS 指紋）、HTTP method、頻率（請求次數、bot 分數）、白名單 {討論結論} (§5.2)
- User-Agent 容易偽造，不能單獨當身分證明 {討論結論} (§5.2, §6)
- 守規矩的 bot 用唯一 user-agent、公開 IP 範圍或 Web Bot Auth 簽章表明身分 {討論結論} (§5.2)
- 四種動作：放行、限速（預設回 429）、挑戰（JS challenge、Turnstile）、封鎖（回 403）；不只開和關 {討論結論} (§5.3)
- AI bot 可用 Block AI bots 一次擋掉，或用 WAF 自訂規則細分 {討論結論} (§5.3)
- AI Crawl Control 的封鎖用 WAF 自訂規則，比 Cloudflare bot 規則先執行 {討論結論} (§5.4)
- Block AI bots 優先於「允許已驗證 bot」；兩者都開時已驗證的 AI bot 仍會被擋 {討論結論} (§5.4)
- Pay per crawl 在 bot 規則之後執行；要用 pay per crawl 必須先關 Block AI bots {討論結論} (§5.4)
- 被限速、挑戰、封鎖的請求停在 Cloudflare，不會到源站 {討論結論} (§5.5)
- Web fetch 不執行 JS，遇到挑戰無法通過驗證，會停在那裡 {討論結論} (§5.6)
- curl、web fetch 與瀏覽器走同一路徑，差別只在被判成哪一種動作 {討論結論} (§5.6)
- 命中 CDN 快取時可能讀到舊內容；網站快取時間越長，舊內容越久 {討論結論} (§5.6)

### §6 容易搞混的點
- Web fetch 不是在打 API，它請求一般網頁網址、拿回 HTML {討論結論} (§6)
- DNS 不檢查 IP，只把流量導到 Cloudflare {討論結論} (§6)

### §7 待確認
- 未確認：台灣證交所 OpenAPI 是否有需要的財報欄位 {討論結論} (§7)
- 未確認：目標網站實際的 Cloudflare 規則與快取時間，要問網站擁有者 {討論結論} (§7)

### §8 下一步可學
- 學習狀態：下一步是 HTTP method／header／status code、F12 Network 找背後 JSON API、Cloudflare bot score 與 JS challenge {討論結論} (§8)

## 變更
- （首次產生）

## 候選連結
- system-design：web-fetch-crawler-api-browser-agent-comparison（本文是其前置概念）、price-watch-tiered-fetch-cas-outbox-freshness-pattern（被擋就停）、onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern（DNS 導流、reverse proxy）、trino-gateway-oidc-watermark-pattern
- wiki：progressive-disclosure（先便宜來源）、primary-guardrail-gate（edge 的 policy 決策）
