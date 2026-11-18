---
source_project: system design & code style
source_file: claude/earnings-video2text-gcp-to-onprem-handover-pattern.md
title: 財報影音轉文字流程:GCP(tMIC)→ On-prem 交接
first_exported: 2026-11-18
updated: 2026-11-18
---
# 財報影音轉文字流程:GCP(tMIC)→ On-prem 交接

> 白板(第三頁):https://claude.ai/artifact/Ssfexn43mRV9viZAHEXnLS
> 第二頁(AI Transcript 流程,本頁的來源):https://claude.ai/artifact/9Jiq9Dfk1VQxAe2RxU5Yci
> 相關文件:`claude/earnings-transcript-gcp-to-onprem-handover-pattern.md`
>
> 本頁沿用第二頁的流程,只改了 GCP 這一側。**GCS → Adapter → On-prem(BDP:Raw Layer、DAG、Stage Layer;再接第二個 DAG 與 tMIC Portal)完全相同**,元件說明與設計原因請看上面那份文件,這裡不重複。
>
> 註記:元件順序來自使用者描述。各元件的角色說明(Gemini 做影音轉文字、Claude 做處理、web search 補查資料等),是依常見做法**推斷**的,不是實際規格。與負責團隊對齊時以他們的版本為準。

---

## 與第二頁的差異

| 項目 | 第二頁 | 第三頁 |
|---|---|---|
| Event Calendar | [SCPM] | **[BIAP]** |
| 第 3 步 | AI Transcript | **Video2text** |
| 資料來源 | FACTSET Transcript、BBG-FA、BBG-SEG | 只留 **FACTSET Transcript**;新增 **YouTube API (Earnings Source)** |
| 外部服務 | Claude API service | Claude API service,**多接 Web search tool**;新增 **Gemini API (Video2text)** |

---

## 流向圖(文字版,只畫 GCP 側)

```
【GCP (tMIC)】
  FACTSET Transcript ──────────────┐
  YouTube API (Earnings Source) ───┤  (資料來源,流入 Video2text)
  Gemini API (Video2text) ◄────────┤  (Video2text 呼叫,雙向)
  Claude API service ◄─────────────┘  (Video2text 呼叫,雙向)
      ▲
      └──► Web search tool            (Claude API 呼叫,雙向)

  1. Event Calendar [BIAP] → 2. Pubsub → 3. Video2text → 4. GCS → 5. Adapter → (進入 on-prem,同第二頁)
```

---

## 流程範例(推斷)

輸入:某公司 Q3 財報記者會,排在 Event Calendar [BIAP],記者會有 YouTube 影片。
輸出:記者會的處理結果,顯示在 tMIC Portal。

| Step | 動作 |
|---|---|
| 1 | Event Calendar [BIAP] 記錄記者會的時間 |
| 2 | 事件到時,Pubsub 發出一則訊息,內容有公司與時間 |
| 3 | Video2text 收到訊息。它透過 YouTube API 取得記者會影片,呼叫 Gemini API 把影片轉成文字,參考 FACTSET Transcript,再呼叫 Claude API service 處理。Claude 需要時會用 Web search tool 查外部資料 |
| 4 | 處理結果寫成檔案,存到 GCS |
| 5~10 | 同第二頁:Adapter 交接 → Raw Layer → DAG → Stage Layer → DAG → tMIC Portal |

---

## 元件說明(只列新增的)

### Video2text(影音轉文字)
- 作用:把財報記者會的影片,變成可讀的文字。
- 類比:會議速記員。聽影片,寫成逐字稿。
- 不同點:它不是自己聽,而是呼叫 Gemini API 去做,自己負責串接與彙整。

### YouTube API(Earnings Source)
- 作用:取得記者會影片的來源與資訊。
- 類比:圖書館的借書櫃台。你問書名,它給你書的位置。
- 不同點:它提供的是影片的存取方式,不負責把影片變成文字。

### Gemini API(Video2text)
- 作用:呼叫 Google 的模型,把影片內容轉成文字。
- 類比:外包的翻譯公司。你送影片,它回傳文字。
- 不同點:Gemini 在白板上是「被呼叫的服務」,所以箭頭是雙向(請求與回應)。

### Web search tool(網路搜尋工具)
- 作用:讓 Claude 在處理時,可以上網查資料。
- 類比:查字典。遇到不確定的詞,翻書查證。
- 不同點:是 Claude 自己決定要不要查,不是每次都會呼叫。

---

## 設計原因(推斷)

| 元件 | 為什麼放在這個位置 |
|---|---|
| YouTube API + Gemini API | 記者會常以影片形式發布。先把影片轉成文字,後面的處理才能沿用文字流程 |
| 保留 FACTSET Transcript | 官方逐字稿可以當對照,也可能在影片轉文字失敗時當備援 |
| Claude API + Web search tool | 處理文字時,遇到需要外部背景的內容,可以自行查證 |
| 其餘 5~10 步不變 | 輸出都是一份檔案,交接與落地的方式可以共用 |

---

## 與負責團隊對齊的確認清單

- Event Calendar [BIAP] 與 [SCPM] 差在哪?誰維護?
- 同一場記者會同時有 FACTSET Transcript 與 Gemini 轉出的文字時,以哪一份為準?差異怎麼處理?
- YouTube 影片不可用(尚未上架、直播中、被下架)時,怎麼處理?要重試嗎?
- Gemini API 對影片長度與大小有沒有限制?長記者會怎麼切?
- Web search tool 的使用範圍:可以搜尋哪些網域?成本與次數有沒有上限?搜尋結果怎麼標註來源?
- Claude API service 與 Gemini API 是直接呼叫,還是經過內部封裝的服務?
- 第 5~10 步是否真的與 AI Transcript 流程共用同一組 DAG 與資料表?

## 下一步學習

Tool use(工具呼叫):Claude 怎麼決定何時呼叫 Web search tool,以及呼叫的結果怎麼回到對話裡。
