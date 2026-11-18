---
raw: raw/ai-new-tech/agent-evaluation-harness-2-ab-test-guide.md
raw_sha256: 81bb30d9514b2becd3ba0b3cdc7e592fb9d934f5bc875994d820480fe7eb04f1
source: ai-new-tech
title: agent evaluation: Harness 2 & AB test 指南
generated: 2026-11-18
---
# agent evaluation: Harness 2 & AB test 指南（note）

## 一句話
Harness² 不需要標準答案就能針對單一任務改善 harness（Propose-Probe-Compose）並跨任務累積教訓；它找出「怎麼改」，paired test 加護欄證明「平均有沒有效」，兩者串接使用。

## 主張
原文證據標記對應：[論文] [README] → {原文}、[第三方] → {第三方}、[一般知識] → {討論結論}、[建議] → {我的判斷}、[示意] → {示意}。

### §2.1–2.3 Harness² 基本資料
- Harness²（arXiv:2610.14224，Northwestern 與 Google Cloud AI Research）不改模型，讓 agent 在工作時改善包在模型外的 harness {原文} (§2.1)
- 它是 Python framework 加 CLI，不是 Claude skill，但能改寫的元件包含 skills {原文} (§2.1)
- 作者自報相對基礎 harness 最多進步 11.5 點（WorkBuddy-Bench）、4.5 點（JobBench）、11.8 個百分點（LAB）{原文} (§2.1)
- 要解決的問題：開放世界任務沒有 ground-truth verifier，靜態部署的 harness 在任務變化時會失效 {原文} (§2.2)
- Execution harness 有八個可編輯元件：system prompt、guardrails、memory、tool guidance、subagents、skills、scripts、plugins {原文} (§2.3)
- Harness 內的 guardrails 是規則；A/B test 的 guardrail metrics 是評估指標；同名不同義 {討論結論} (§2.3)

### §2.4 第一層：Propose → Probe → Compose
- 先用原 harness 跑一次得到 reference execution {原文} (§2.4)
- Propose 兩個候選：通用缺陷（invariant）與當前領域各一 {原文} (§2.4)
- Probe 在同一任務、相同設定下執行候選並與參考執行比對；Compose 只合併有行為證據的修改，否則保留原 harness {原文} (§2.4)
- 預算 k 控制遞迴次數，有 parallel（selector 挑匿名成品）與 sequential 兩種模式 {原文} (§2.4)

### §2.5 第二層：跨任務學習
- 每個任務仍從基礎 harness 出發；library 只存「為什麼有效」並選擇性重用，避免高度客製的 harness 帶入雜訊 {原文} (§2.5)
- 更新：R(t+1) = UPDATE(R(t), H*(t), D(t))；experience reflector 抽出教訓，只保留被執行對比支持的教訓 {原文} (§2.5)
- 消融實驗：拿掉 library 分數下降；更大預算累積的 library 支持更強的修改；跨 benchmark 遷移經驗有幫助（無具體數字）{原文} (§2.5)

### §2.6 證據與限制
- 比較能引導決定，但不能證明輸出是對的 {第三方} (§2.6)
- 實驗中 editor 是 Claude Opus 4.8，弱模型的進步可能部分來自強 editor {第三方} (§2.6)
- 「不需要標準答案」只指執行期間的改善過程；評估 Harness² 本身仍靠 benchmark rubric {第三方} (§2.6)

### §3 A/B test 概念（對照用）
- A/B test 靠隨機分組與結果指標，不需要每題的正確答案 {討論結論} (§3.1)
- 離線 paired 設計等於 θ = 1 的 CUPED {討論結論} (§3.5)
- 離線評估題庫固定、一次跑完，不需要 sequential testing {討論結論} (§3.6)
- 沒有標準答案時：行為 proxy 指標、成對偏好比較（sign test）、檢查量測本身（A/A test、SRM、Cohen's kappa）{討論結論} (§3.7)

### §4 並排比較
- 標準答案加 paired test 回答「改動平均有沒有效」，不能回答新類型任務怎麼辦 {我的判斷} (§4)
- Harness² 回答「這個任務該怎麼改」，不能回答改動是否真的比較好、好多少 {我的判斷} (§4)
- Harness² 的主要風險：看起來有進步其實是錯的、單次結果很吵、挑到運氣好的候選 {我的判斷} (§4)

### §5 完整範例（合約助理）
- 做法一範例：MDE +10%、ψ 20% 需約 155 份，加 30% 緩衝用 200 份；McNemar b = 6、c = 24，+9%，p ≈ 0.0014（已驗算）{示意} (§5.1)
- 更正：先前用 100 份合約，ψ = 18%、差異 10% 時 power 只有約 66%，所以改用 200 份 {討論結論} (§5.1)
- 做法二加入的 A/B 概念：引用必須真的出現在 PDF（便宜的程式檢查）、參考版本重跑 3 次量雜訊、比較候選減參考、合成後用新 seed 確認以防 winner's curse {我的判斷} (§5.2)
- 第二層例子：「先搜附件」的教訓只在合約有 Exhibit 或 Amendment 時適用；沒有附件的任務從基礎 harness 出發，不被無用規則拖累 {示意} (§5.3)

### §6 適用情境
- 任務固定重複且能建題庫 → 做法一；任務每次不同、沒有答案 → 做法二產生候選 {我的判斷} (§6)
- 有副作用的任務（寫資料庫、寄信、下單）避免做法二，因為 Probe 會重跑 {原文} (§6)
- 高風險任務的做法二結果不能直接採用，一定要經做法一驗收 {我的判斷} (§6)
- 一個任務 k = 1 就要 4 次 executor 與 3 次 improver；真實 HR 任務約花 22 美元，程式沒有花費上限 {第三方} (§6, §7.3)

### §7 實作細節
- executor 網路不受限、Codex sandbox 關閉，評估前要限制網路，避免查到答案或評分標準 {原文} (§7.3)
- 評分與報告必須用與 refinement 完全相同的 benchmark、executor、子集、k、模式與 seed {原文} (§7.3)
- 接自己的任務要實作 `BenchmarkAdapter`；README 沒說明改好的 harness 如何載入自己的 agent {第三方} (§7.4)
- 串接流程：Harness² 產生候選 → 驗收題庫 paired test 加護欄（含 Propose 多花的成本）→ 通過才採用 → 失敗案例加進題庫 {我的判斷} (§7.6)
- 教訓升級閘門：新教訓先 pending；在 2 到 3 個不同任務重複出現才升級；升級前用做法一驗收；證據模糊交給人；模型換版後定期 lint {我的判斷} (§7.7)
- 升級閘門與使用者 Agent System 文件的規則一致：同類失敗第二次才寫進 docs，證據模糊不自動升級 {我的判斷} (§7.7)
- 量 library 是否有用：同一批任務「有 library」對「沒有 library」配對比較 {我的判斷} (§7.7)

## 變更
- （首次產生）

## 候選連結
- 本 source：anthropic-agent-memory-guide（library ↔ dreaming 的記憶層；只存有證據的教訓 ↔ analyzer Verify；教訓升級 ↔ promote）、paired-test-guide、ab-test-ai-evaluation-guide
- system-design：使用者 Agent System 文件的升級規則（同類失敗第二次才寫進 docs）、ADR / 決策紀錄、副作用與冪等性、可重現性（固定 seed 與設定）
