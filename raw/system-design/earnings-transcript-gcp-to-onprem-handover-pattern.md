---
source_project: system design & code style
source_file: claude/earnings-transcript-gcp-to-onprem-handover-pattern.md
title: 財報逐字稿流程:GCP(tMIC)→ On-prem 交接
first_exported: 2026-11-18
updated: 2026-11-18
---
# 財報逐字稿流程:GCP(tMIC)→ On-prem 交接

> 白板(第二頁):https://claude.ai/artifact/9Jiq9Dfk1VQxAe2RxU5Yci
> 第一頁(On-prem → GCP 流量流向):https://claude.ai/artifact/FLn6KkjSryhFqgkPfd52Jt
> 相關文件:`claude/onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern.md`(使用者請求從 on-prem 進 GCP 的方向;本文是資料從 GCP 交接回 on-prem 的方向)
>
> 註記:元件順序來自使用者描述。各元件的角色說明、兩個 DAG 各做什麼、各資料來源的內容,是依常見做法**推斷**的,不是實際規格。與負責團隊對齊時以他們的版本為準。

---

## 流向圖(文字版)

白板版面:GCP (tMIC) 在上,On-prem 在下。On-prem 內的 Raw Layer、DAG、Stage Layer 另外用 **BDP** 方框包起來。

```
【GCP (tMIC)】
  FACTSET Transcript ─┐
  BBG-FA ─────────────┤
  BBG-SEG ────────────┤ (資料來源,流入 AI Transcript)
  Claude API service ◄┴─► (AI Transcript 呼叫,雙向)
                          │
  1. Event Calendar [SCPM] → 2. Pubsub → 3. AI Transcript → 4. GCS → 5. Adapter
                                                                        │
═══════════════════════════════ 進入 on-prem ═══════════════════════════│═══
                                                                        ▼
【企業內部 On-prem】
  ┌─ BDP ──────────────────────────────────────────┐
  │ 6. MinIO Raw Layer → 7. DAG → 8. MinIO Stage Layer │ → 9. DAG → 10. tMIC Portal
  └────────────────────────────────────────────────┘
```

---

## 流程範例(推斷)

輸入:某公司 Q3 財報記者會,排在 Event Calendar。
輸出:記者會的摘要,顯示在 tMIC Portal。

| Step | 動作 |
|---|---|
| 1 | Event Calendar [SCPM] 記錄記者會的時間 |
| 2 | 事件到時,Pubsub 發出一則訊息,內容有公司與時間 |
| 3 | AI Transcript 收到訊息。它從 FACTSET 取逐字稿,從 BBG-FA、BBG-SEG 取資料,並呼叫 Claude API service 處理 |
| 4 | 處理結果寫成檔案,存到 GCS |
| 5 | Adapter 取走 GCS 的檔案,送進企業內部 |
| 6 | MinIO Raw Layer 原樣保存這份檔案(BDP 內) |
| 7 | 第一個 DAG 檢查並整理資料,從 Raw 搬到 Stage(BDP 內) |
| 8 | MinIO Stage Layer 保存整理後的資料(BDP 內) |
| 9 | 第二個 DAG 把 Stage 的資料送到 Portal |
| 10 | 使用者在 tMIC Portal 看到摘要 |

---

## 元件說明

### Pubsub(發布/訂閱訊息)
- 作用:一方發出訊息,另一方訂閱並收到。發送者與接收者不需要直接連線。
- 類比:廣播電台。電台廣播,有開收音機的人才收得到。
- 不同點:Pubsub 的訊息會被暫存,接收者晚一點上線也能收到。

### DAG(Directed Acyclic Graph,有向無環圖)
- 作用:把一組工作任務排成有先後順序的流程,而且不會繞回頭。
- 類比:食譜的步驟。先洗菜,再切菜,再炒。
- 不同點:DAG 由排程系統自動執行,失敗時可以重試。

### Adapter(轉接器)
- 作用:把一邊的格式與介面,轉成另一邊能接收的樣子。
- 類比:電源轉接頭。
- 不同點:Adapter 也是這張圖裡**跨越邊界**的一步,所以出入口的權限、網路與失敗重送都要管。

### Raw Layer 與 Stage Layer(原始層與整理層)
- 作用:Raw 原樣保存收到的資料。Stage 保存整理過、結構清楚的資料。
- 類比:倉庫的「進貨區」與「上架區」。
- 不同點:Raw 一旦寫入就不改,所以 Stage 出錯時,可以從 Raw 重做。

### BDP 方框
- 作用:在白板上,把 Raw Layer、DAG、Stage Layer 圈成同一個平台範圍。
- 註記:BDP 的全名與實際範圍,我沒有資料,方框是依使用者指示畫的。第二個 DAG 與 Portal 畫在 BDP 外面。

---

## 設計原因(推斷)

| 元件 | 為什麼放在這個位置 |
|---|---|
| Event Calendar + Pubsub | 用事件觸發,不用人手動啟動,也不用一直輪詢 |
| 資料來源接在 AI Transcript 上游 | 逐字稿與財務資料都在這一步彙整,後面只傳處理結果 |
| GCS 在 Adapter 之前 | 讓 GCP 端的產出先落地。交接失敗時,檔案還在,可重送 |
| Adapter 在邊界上 | 邊界只留一個出入口,方便管控與稽核 |
| Raw → Stage 分兩層 | Raw 保留原貌,Stage 提供乾淨資料,出錯可重跑 |
| 兩段 DAG | 每段只做一件事,失敗時知道是哪一段 |

---

## 與負責團隊對齊的確認清單

- Event Calendar [SCPM] 是誰維護?事件變更(改期、取消)會再發 Pubsub 訊息嗎?
- AI Transcript 失敗時,Pubsub 會重送嗎?重送會不會產生重複結果?(冪等性)
- BBG-FA、BBG-SEG 各自提供什麼資料?更新頻率是多少?
- Claude API service 是內部封裝的服務,還是直接呼叫 Claude API?
- Adapter 是拉(pull)還是推(push)?跨越 GCP 與 on-prem 走專線還是 VPN?
- BDP 的全名是什麼?它的範圍是否只有 Raw、DAG、Stage 三個元件?
- 兩個 DAG 各自負責什麼?第一個是 Raw → Stage,第二個是不是 Stage → Portal?第二個 DAG 在不在 BDP 內?
- 從 GCS 寫入到 Portal 顯示,目前整體延遲是多少?最慢的是哪一段?

## 下一步學習

冪等性(Idempotency):Pubsub 重送訊息、Adapter 重送檔案時,怎麼確保同一份資料不會被處理兩次。
