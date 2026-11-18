---
source_project: system design & code style
source_file: claude/earnings-pre-earnings-gcp-to-onprem-handover-pattern.md
title: Pre-earnings 流程:GCP(tMIC)→ On-prem 交接
first_exported: 2026-11-18
updated: 2026-11-18
---
# Pre-earnings 流程:GCP(tMIC)→ On-prem 交接

> 白板(第四頁):https://claude.ai/artifact/K8CXAqXsgicQijU4Z5HcgS
> 第三頁(Video2text 流程,本頁的來源):https://claude.ai/artifact/Ssfexn43mRV9viZAHEXnLS
> 相關文件:
> - `claude/earnings-video2text-gcp-to-onprem-handover-pattern.md`(第三頁)
> - `claude/earnings-transcript-gcp-to-onprem-handover-pattern.md`(第二頁;GCS 之後的第 5~10 步與 BDP 的說明在這裡)
> - `claude/web-fetch-crawler-api-browser-agent-comparison.md`、`claude/http-api-vs-html-curl-cloudflare-bot-policy.md`(web fetch 被網站擋下時的相關討論)
>
> 本頁沿用第三頁的流程,只改了 GCP 這一側。**GCS → Adapter → On-prem(BDP:Raw Layer、DAG、Stage Layer;再接第二個 DAG 與 tMIC Portal)完全相同**,不重複說明。
>
> 註記:元件順序來自使用者描述。「Pre-earnings」實際做什麼(此處推斷為財報前的準備處理)、Claude 如何使用兩個工具,是依常見做法**推斷**的,不是實際規格。與負責團隊對齊時以他們的版本為準。

---

## 與第三頁的差異

| 項目 | 第三頁 | 第四頁 |
|---|---|---|
| Event Calendar | [BIAP] | [BIAP](不變) |
| 第 3 步 | Video2text | **Pre-earnings** |
| 資料來源 | FACTSET Transcript、YouTube API | **全部移除** |
| 外部服務 | Gemini API、Claude API(+ Web search tool) | **Gemini API 移除**;Claude API 保留,工具為 **Web search tool + Web fetch tool(新增)** |

結果:這一頁的 GCP 側沒有固定的資料來源。Pre-earnings 取得資料的唯一途徑,是 Claude API 透過兩個工具上網查與抓。

---

## 流向圖(文字版,只畫 GCP 側)

```
【GCP (tMIC)】
  Web search tool ◄──► Claude API service ◄──► Web fetch tool   (Claude 呼叫工具,雙向)
                              ▲
                              │ (Pre-earnings 呼叫,雙向)
                              ▼
  1. Event Calendar [BIAP] → 2. Pubsub → 3. Pre-earnings → 4. GCS → 5. Adapter → (進入 on-prem,同第二、三頁)
```

---

## 流程範例(推斷)

輸入:某公司的財報記者會即將舉行,排在 Event Calendar [BIAP]。
輸出:財報前的處理結果,顯示在 tMIC Portal。

| Step | 動作 |
|---|---|
| 1 | Event Calendar [BIAP] 記錄這場財報的時間 |
| 2 | 事件到時,Pubsub 發出一則訊息,內容有公司與時間 |
| 3 | Pre-earnings 收到訊息,呼叫 Claude API service。Claude 用 Web search tool 找相關網頁,再用 Web fetch tool 讀取需要的網頁內容,整理成處理結果 |
| 4 | 處理結果寫成檔案,存到 GCS |
| 5~10 | 同第二頁:Adapter 交接 → Raw Layer → DAG → Stage Layer → DAG → tMIC Portal |

---

## 元件說明(只列新增的)

### Pre-earnings(財報前處理)
- 作用:在財報發布前,先彙整與準備相關資訊。
- 註記:名稱來自使用者描述,具體內容是推斷。
- 不同點:跟前兩頁不同,它沒有固定的輸入資料,完全靠 Claude 上網取得。

### Web fetch tool(網頁抓取工具)
- 作用:讓 Claude 讀取指定網址的完整內容。
- 類比:Web search 像查圖書目錄,告訴你有哪些書。Web fetch 像把指定那本書借來讀。
- 不同點:抓取是直接連到網站,所以可能被網站的防機器人機制擋下。搜尋則是查搜尋引擎的結果,比較不會被擋。

### Web search tool(網路搜尋工具)
- 見第三頁文件。這裡的差別是:它現在是 Pre-earnings 找資料的起點,後面接 Web fetch tool 讀內文。

---

## 設計原因(推斷)

| 元件 | 為什麼放在這個位置 |
|---|---|
| 移除固定資料來源 | 財報前還沒有逐字稿與影片,能用的資料只有網路上已公開的資訊 |
| Web search + Web fetch 一起用 | 先搜尋找到網頁,再抓取內文。只搜尋會只拿到摘要 |
| 兩個工具都由 Claude API 呼叫 | 由 Claude 判斷要查什麼、要讀哪一頁,不用事先寫死資料來源 |
| 其餘 4~10 步不變 | 輸出都是一份檔案,交接與落地方式可以共用 |

---

## 與負責團隊對齊的確認清單

- Pre-earnings 的輸出是什麼內容?給誰看?跟財報後的流程是同一個 Portal 頁面嗎?
- Web fetch 被網站擋下(防機器人、需登入、內容用 JavaScript 載入)時,怎麼處理?要不要有備援方案?
- Web search 與 Web fetch 可以存取哪些網域?要不要限制白名單?
- 網頁內容會不會夾帶惡意指令(prompt injection)?抓回來的內容怎麼處理?
- 搜尋與抓取的次數、成本有沒有上限?單次 Pre-earnings 最多可以呼叫幾次?
- 輸出內容的來源怎麼標註?使用者能不能點回原始網頁?
- Event Calendar [BIAP] 的事件,什麼時候觸發 Pre-earnings(財報前幾天?幾小時?)

## 下一步學習

Tool use(工具呼叫):Claude 怎麼決定何時呼叫 Web search 或 Web fetch,以及工具的結果怎麼回到對話裡。
