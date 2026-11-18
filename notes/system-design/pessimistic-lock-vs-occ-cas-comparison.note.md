---
raw: raw/system-design/pessimistic-lock-vs-occ-cas-comparison.md
raw_sha256: 39771ec2cedc07091618fa74061d3b3ebc2ccde2b99d844ccc95b6e027e0c064
source: system-design
title: 悲觀鎖 (Pessimistic Lock) vs 樂觀鎖 (OCC / CAS)
generated: 2026-11-18
---
# 悲觀鎖（Pessimistic Lock）vs 樂觀鎖（OCC / CAS）（note）

## 一句話
悲觀鎖與樂觀鎖的唯一差別是衝突在哪個時間點處理：悲觀鎖先鎖再做（後到者等待），樂觀鎖先做、寫入時用 CAS 比對版本憑證（後到者重做）；重做昂貴（如 LLM 呼叫）時選悲觀鎖或 single writer queue。

## 主張
證據標記對應：原文是學習筆記，沒有證據標記 → 全部 {討論結論}。

### 前言
- 本篇對照 DataFrame cache 設計（key 鎖）與 Dreaming 討論（SHA256 憑證）{討論結論} (前言)

### §1 一句話版本
- 悲觀鎖假設一定衝突，先鎖再做；樂觀鎖（OCC）假設衝突不常發生，先做、寫入時才檢查 {討論結論} (§1)
- 悲觀鎖在開始前處理衝突（B 等待）；樂觀鎖在寫入時處理衝突（B 重做）{討論結論} (§1)

### §2 名詞
- CAS（Compare-And-Swap）是樂觀鎖的核心動作：「如果現在還是 H1，才寫入新值」{討論結論} (§2)
- Version token 代表資料現在是哪一版；本例用 SHA256 hash（H1、H2、H3）{討論結論} (§2)
- 樂觀鎖像 Git push 被拒後先 pull 再 push；差別是 Git 重做的是合併，樂觀鎖預設重做整個處理流程 {討論結論} (§2)

### §3 流程對照
- 悲觀鎖代價：B 全程等待，但拿到鎖後用的是 A 做完的資料 {討論結論} (§3)
- 樂觀鎖流程：A、B 都讀到 H1 → A 先寫入成功、憑證變 H2 → B 以 H1 寫入被拒 → B 讀 H2 重做 → 寫入成功、憑證變 H3 {討論結論} (§3)
- 樂觀鎖代價：B 的工作白做一次 {討論結論} (§3)

### §4 其他方法
- Lease Lock：悲觀鎖加過期時間，持有者掛掉時鎖自動失效，其他人不會永遠卡住 {討論結論} (§4)
- Read-Write Lock：多人可同時讀，寫時只能一人 {討論結論} (§4)
- Single Writer Queue：所有寫入排成一條隊由一個 worker 依序處理，沒有衝突也不用鎖 {討論結論} (§4)
- Merge：發現過期時不整個重做，而是合併雙方改動，像 Git three-way merge {討論結論} (§4)

### §5 怎麼選
- 衝突少、重做便宜 → 樂觀鎖 {討論結論} (§5)
- 衝突多 → 悲觀鎖或 Single Writer Queue {討論結論} (§5)
- 重做很貴（例如一次 LLM 呼叫要花錢）→ 悲觀鎖或 Single Writer Queue {討論結論} (§5)
- 持有鎖者可能中途掛掉 → 悲觀鎖要加 Lease {討論結論} (§5)
- 讀多寫少 → Read-Write Lock 或樂觀鎖 {討論結論} (§5)

### §6 下一步
- 下一步學資料庫 CAS 寫法 `UPDATE ... WHERE version = ?` 與寫入失敗的自動重試 {討論結論} (§6)

## 變更
- （首次產生）

## 候選連結
- system-design：transactional-outbox-lease-reaper-idempotent-consumer-pattern（lease）、price-watch-tiered-fetch-cas-outbox-freshness-pattern（CAS）、single-source-of-truth-postgres-gcs-release-pattern（409 版本衝突）
- wiki：optimistic-concurrency、single-writer、dreaming、km-dreaming-design（SHA256 憑證）、skill-state
