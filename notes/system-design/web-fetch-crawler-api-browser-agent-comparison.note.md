---
raw: raw/system-design/web-fetch-crawler-api-browser-agent-comparison.md
raw_sha256: c156901869aff74bb3c04ee01f679e5aa599a8eb9192f2c9a1864d6c1b7a9d70
source: system-design
title: Web fetch、爬蟲 API 與 Browser Agent：Agent 怎麼取得網頁內容
generated: 2026-11-18
---
# Web fetch、爬蟲 API 與 Browser Agent：Agent 怎麼取得網頁內容（note）

## 一句話
Agent 取得網頁的方法只差在「讀到原始 HTML 還是執行 JS 後的 DOM」與「瀏覽器在哪裡」；依序選官方 API → web fetch → 爬蟲 API / 自有 headless → browser agent，並把網頁內容當不可信輸入。

## 主張
原文沒有逐條證據標記：引用 Claude 官方文件（「文件註明」「官方建議」）的條目 → {官方文件}；雲端 agent 產品的發布資訊 → {第三方}；其餘 → {討論結論}。產品資訊以 2026-11-11 為準。

### §1 一句話結論
- 選擇順序：有官方 API 先用官方 API；靜態頁面用 web fetch；靠 JS 渲染且流程固定用爬蟲 API 服務或自己的 headless browser；需要判斷、點擊、多步操作用 browser agent {討論結論} (§1)

### §2 基本概念
- 讀取點 ① 是 server 回傳的原始 HTML（「檢視網頁原始碼」），web fetch 讀這裡；讀取點 ② 是執行 JS 後的 DOM（F12 Elements），所有用瀏覽器的方法讀這裡 {討論結論} (§2)
- 判斷方法：要的資料在「檢視原始碼」裡，web fetch 就夠；不在就需要能執行 JS 的瀏覽器 {討論結論} (§2)
- SPA 商品頁的原始 HTML 可能只有 `<div id="app"></div>`，web fetch 看不到商品名與價格 {示意} (§2)

### §4 方法比較
- 爬蟲 API 服務（Firecrawl、ScrapingBee、Jina Reader）在服務商遠端 headless 渲染並轉 markdown，agent 呼叫一次，適合大量、固定格式抓取 {討論結論} (§4)
- Playwright MCP、Chrome DevTools MCP 在本機 headless 以「快照 → 決定 → 動作 → 再快照」迴圈運作，適合自動化、測試與需要判斷的操作 {討論結論} (§4)
- Claude in Chrome 用使用者自己的 Chrome（有畫面），沿用已登入狀態 {討論結論} (§4)
- Web fetch 請求一般網頁網址拿回 HTML，不是在打 API；web search 查搜尋引擎索引回傳網址與摘要，不讀 HTML {討論結論} (§4)
- Browser agent 看的是畫好的 DOM，不直接打網站背後的 API {討論結論} (§4)

### §5 Browser agent 運作
- 快照有兩種：畫面截圖（需視覺模型）與 DOM／accessibility tree 快照（只留可互動元素並編號，純文字模型即可）{討論結論} (§5.1)
- 不直接餵原始 DOM，因為常有幾十萬 token 且雜訊多 {討論結論} (§5.1)
- 每次動作後要等頁面穩定再取新快照，元素編號會重新計算 {討論結論} (§5.2)
- 自建架構：content script ↔ extension service worker ↔ WebSocket 或 Native Messaging ↔ Agent 服務 ↔ OpenAI 相容 API ↔ 地端模型（vLLM、Ollama）{討論結論} (§5.3)
- 自建時把 extension 能力包成工具 `get_snapshot()`、`click(ref)`、`type(ref, text)`、`navigate(url)`，以 WebSocket 或 MCP server 接上 {討論結論} (§5.3)
- 自建的優點是頁面資料不離開公司、沿用登入 session；代價是地端模型 tool calling 與長 context 較弱、快照吃 token、每步呼叫一次模型所以慢 {討論結論} (§5.3)
- 自建的主要問題：prompt injection、extension 權限等同本人、canvas/iframe/shadow DOM 讀不到、元素編號過期導致無限迴圈、Chrome MV3 service worker 休眠需處理長連線 {討論結論} (§5.3)
- 捲動載入的做法：捲動 → 等 DOM 穩定（例如 `MutationObserver` 一段時間無變動）→ 重新快照 → 比對新元素，沒有新元素即到底，並設步數上限 {討論結論} (§5.4)
- 無限捲動背後常是分頁（`?page=2`），找到規律就可直接用 web fetch 逐頁抓 {討論結論} (§5.4)
- iframe 要注入每個 frame 且編號帶 frame id；shadow DOM 要遞迴進 shadowRoot，並設深度上限 {討論結論} (§5.4)
- 分工原則：重複固定的動作寫成複合工具（`scroll_to_bottom()`、`expand_all()`），模型只做判斷，更快、更省 token、更穩 {討論結論} (§5.4)

### §6 Claude API 與 Claude Code 工具
- Claude API 的 web fetch tool 是 server tool，支援 PDF，不支援靠 JS 動態渲染的網站，可用 `allowed_domains` 限制網域 {官方文件} (§6)
- 官方文件警告：web fetch 遇到不可信輸入加上敏感資料時有資料外洩風險 {官方文件} (§6)
- Browser use tool 是 client toolset，型別 `browser_toolset_20260801`，瀏覽器環境由使用者提供並執行；在 Claude API 為正式版，列出 Google Cloud 可用，Azure 待確認 {官方文件} (§6)
- 任務只在網頁內時，官方建議用 browser use 而非 computer use；只讀給定網址時 web fetch 較輕量 {官方文件} (§6)
- Claude Code 要 headless 用 MCP：`claude mcp add playwright -- npx @playwright/mcp@latest --headless --isolated` 或 `claude mcp add chrome-devtools -- npx chrome-devtools-mcp@latest --headless=true --isolated=true`，重啟後用 `claude mcp list` 確認 Connected {討論結論} (§6)
- 沒有螢幕的伺服器環境一定要用 headless；Claude in Chrome 不能 headless {討論結論} (§6)
- Playwright MCP 支援 Chrome、Firefox、Safari，適合自動化與 CI/CD；Chrome DevTools MCP 只支援 Chrome，適合除錯、效能、網路分析 {討論結論} (§6)
- Claude in Chrome 是 beta 的 Chrome 擴充功能，限付費方案（Pro、Max、Team、Enterprise），只支援 Google Chrome；Team/Enterprise 由管理員控制開關與網站白名單、黑名單 {官方文件} (§6)
- Claude Duet（2026-10-21，研究預覽）需 Pro 或 Max、美國帳號、候補名單邀請，Team 與 Enterprise 目前不符合；發訊息、付款、簽文件、刪除前要核准 {官方文件} (§6)
- Muse（Meta，2026-09-08）與 Grok Bot（xAI，2026-08-11）都是雲端 VM 瀏覽器；Grok Bot 每筆購物扣款要人工核准 {第三方} (§6)
- 雲端 agent 產品的瀏覽器在廠商雲端，頁面資料會送到廠商；共同原則是有連接器或 API 先用，沒有才用瀏覽器 {第三方} (§6)

### §7 HTML 轉 markdown
- 自己抓 HTML 時先移除 `script`、`style`、`nav`、`footer`，再用 `trafilatura`、`readability` 抽主要內容，最後用 `turndown`、`html2text` 轉 markdown；web fetch 與 browser use 的 `read_page` 已處理過 {討論結論} (§7)
- 財報表格轉 markdown 容易因合併儲存格、多層表頭錯位，且寫在表格上方的單位（千元、百萬）容易被濾掉 {討論結論} (§7)
- 表格改用 `pandas.read_html` 解析成資料表再轉 CSV 或 JSON 給模型 {討論結論} (§7)
- 抽出的數字要用程式驗算（例如加總是否對得上），不要只信模型 {討論結論} (§7)

### §8 風險與邊界
- 瀏覽器不是繞過反爬：CAPTCHA、Cloudflare 挑戰、IP 信譽、行為偵測、流量限制都解決不了；Claude 遇到登入頁或 CAPTCHA 會暫停 {討論結論} (§8)
- 偽裝指紋、破解 CAPTCHA 這類規避措施不採用；使用爬蟲 API 服務也不代表可無視網站規則 {討論結論} (§8)
- 合理做法：先找官方 API、RSS、資料授權；有權限的內容用自己登入的瀏覽器；控制頻率、遵守 `robots.txt`；重要來源直接申請存取 {討論結論} (§8)
- 網頁內容是不可信輸入：限制網域白名單，避免同一個 agent 同時接觸網頁與內部機密資料 {討論結論} (§8)
- 高風險動作（送出、刪除、付款）要人工確認，並設步數上限 {討論結論} (§8)
- 能固定的流程寫成固定 workflow，只有需要判斷的步驟交給 LLM {討論結論} (§8)

### §9 選擇指南
- 決策步驟：官方 API → 資料在原始碼就 web fetch → JS 載入但找得到背後網址或分頁規律就 web fetch 直打 → 流程固定量大用爬蟲 API 或 headless → 需判斷多步操作用 browser agent → 需已登入網站用 Claude in Chrome {討論結論} (§9)

### §10 待確認
- 未定：Azure 是否支援 browser use tool、公司對頁面資料送雲端模型的政策、目標網站服務條款與 `robots.txt` {討論結論} (§10)

## 變更
- （首次產生）

## 候選連結
- system-design：http-api-vs-html-curl-cloudflare-bot-policy（反爬與 bot 政策）、price-watch-tiered-fetch-cas-outbox-freshness-pattern（分層 fetch）、rag-methods-comparison（HTML 轉結構化內容）、structured-rag-golden-eval-hexagonal-pattern（表格轉結構化資料）
- wiki：agent-harness-design（固定 workflow + LLM 只做判斷、複合工具）、pass-by-reference（表格轉資料表而非整包塞 context）、primary-guardrail-gate（高風險動作人工核准）、progressive-disclosure（快照只留可互動元素）
