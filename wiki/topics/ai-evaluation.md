---
id: ai-evaluation
title: AI 評估總覽（AI evaluation）
type: topic
summary: 離線題庫加 paired test 擋壞版本、線上 A/B 證明更好；前提是題庫與 grader 都代表 User，決策過主指標與護欄兩關
domains: [ai-new-tech]
sources: [raw/ai-new-tech/ab-test-ai-evaluation-guide.md#1, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#2.4, raw/ai-new-tech/model-evals-product-evals.md#0, raw/ai-new-tech/model-evals-product-evals.md#2, raw/ai-new-tech/model-evals-product-evals.md#11]
evidence: [討論結論, 第三方, 我的判斷]
related: [paired-test, cuped, golden-dataset, grader-alignment, primary-guardrail-gate, error-analysis-loop, harness2]
status: active
created: 2026-11-18
last_dreamed: 2026-11-19
review_count: 1
next_review: 2026-11-22
---
# AI 評估總覽（AI evaluation）

> 離線題庫加 paired test 擋壞版本、線上 A/B 證明更好；前提是題庫與 grader 都代表 User，決策過主指標與護欄兩關

## 重點
- 主線：離線評估（題庫 + LLM 評審 + [[paired-test]]）擋掉壞的 → 小流量線上 A/B 證明真的更好 → 事先寫好的規則決定 {第三方}
- 兩個代表性：題庫代表 User 的需求（[[golden-dataset]]）、grader 代表 User 的評斷（[[grader-alignment]]）；User 難接觸是限制條件不是目標 {我的判斷}
- Model evals 比哪個版本強，Product evals 看 User 用起來好不好；前者是後者的零件 {我的判斷}
- 能用 Code 評分就用 Code，LLM judge 只用在 Code 做不到的地方 {討論結論}
- 決策兩關：主指標顯著變好，且護欄都沒變差（[[primary-guardrail-gate]]）{討論結論}

## 細節
**評分對象** {討論結論}：agent 看最終狀態加過程規則（tool-call log），報 pass@k 或 pass^k；retrieval 看 gold passage（recall@k、MRR、nDCG）；system 看標準答案加引用。

**線上 A/B 的關鍵步驟** {討論結論}：一次只改一個變因；事先算樣本（基準 60%、偵測 +6% 每組約 1,000 人；差異減半樣本約 4 倍）；以使用者為單位 hash 分組、兩組同時跑；先 5% 灰度；跑滿 1 到 2 週；先檢查 SRM；分群只當探索。

**Peeking 與 sequential testing** {討論結論}：A/A 模擬中看 5 次誤判率 14.1%、10 次 19.3%。要中途看就事先定檢查點，預設 O'Brien-Fleming（5 次門檻 0.00001、0.0013、0.0084、0.023、0.041）。提早停會高估效果。離線題庫一次跑完不需要。

**沒有標準答案時**：行為 proxy 指標、成對偏好比較（sign test）、[[harness2]] 這類行為比對；但都要回到有答案的驗收 {討論結論}{我的判斷}

**分階段落地** {我的判斷}：
1. Code 評分、冷啟動題庫與分布對照、dev / held-out、一次 [[error-analysis-loop]]、3 到 5 個護欄
2. 分層標註、judge 的 kappa / McNemar / mutation test、順序交換、手動修 grader、Red Team
3. PPI 與 [[cuped]]、GEPA、被動訊號對照、Arena

## 在設計中怎麼用
- 每次實驗前填實驗計畫表：假設、離線結果、主要與護欄指標、樣本、中途檢查、CUPED、決策規則（事先寫、不改）。
- 失敗案例一律回到題庫，由 [[error-analysis-loop]] 驅動。

## 相關
- [[paired-test]]、[[cuped]]：統計方法
- [[golden-dataset]]：目標 A
- [[grader-alignment]]：目標 B
- [[primary-guardrail-gate]]：決策
- [[error-analysis-loop]]：回饋迴圈
- [[harness2]]：沒有答案時的改善方法
