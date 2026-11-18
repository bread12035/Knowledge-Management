---
id: paired-test
title: Paired test（成對檢定）
type: concept
summary: 同一題 A、B 都回答，用每題的差做檢定，扣掉題目難度的雜訊；依結果型態事先選檢定
domains: [ai-new-tech]
sources: [raw/ai-new-tech/paired-test-guide.md#2, raw/ai-new-tech/paired-test-guide.md#3, raw/ai-new-tech/paired-test-guide.md#5, raw/ai-new-tech/ab-test-ai-evaluation-guide.md#2.9]
evidence: [討論結論, 示意, 我的判斷]
related: [ai-evaluation, cuped, golden-dataset, primary-guardrail-gate, harness2]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Paired test（成對檢定）

> 同一題 A、B 都回答，用每題的差做檢定，扣掉題目難度的雜訊；依結果型態事先選檢定

## 重點
- A、B 面對同一個對象（同一題）就是 paired；設計是 paired 就要用 paired 檢定 {討論結論}
- 每題自己和自己比，題目難度在 B − A 時被扣掉；12 題範例 independent p = 0.67、paired p = 0.00005，資料一樣結論相反（已驗算）{示意}
- 選檢定看結果型態，而且要在測試前決定：對錯 → McNemar；連續分數 → paired t；等級或有極端值 → Wilcoxon；勝負 → sign test {討論結論}
- p-value 只說像不像運氣；要報差異大小與 95% 信賴區間，並看下界是否超過 MDE {討論結論}
- 樣本數由差異 δ 與 ψ（A、B 不一致的比例）決定；差異減半，題數約 4 倍 {討論結論}

## 細節
**McNemar**：只有 b（A 對 B 錯）與 c（A 錯 B 對）有資訊；b + c 小於約 25 用 exact（`binomtest`）。200 題範例 b = 8、c = 22，+7%，CI +1.7% 到 +12.3%，p = 0.016；當成獨立比較 p = 0.07 {示意}

**題數表**（α 0.05、power 80%，已驗算）{討論結論}：
| δ | ψ = 15% | ψ = 20% | ψ = 30% |
| --- | --- | --- | --- |
| 10% | 115 | 155 | 233 |
| 7% | 238 | 318 | 478 |
| 5% | 469 | 626 | 940 |

```python
from scipy.stats import norm
def mcnemar_n(delta, psi, alpha=0.05, power=0.8):
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    return ((za * psi**0.5 + zb * (psi - delta**2) ** 0.5) ** 2) / delta**2
```

**Paired 設計就是 θ = 1 的 [[cuped]]** {討論結論}

## 在設計中怎麼用
執行 7 步 {討論結論}：
0. 事先寫：假設（只改一處）、主要指標與檢定、護欄與門檻、α 與 MDE、決策規則
1. 固定題庫，每題 question_id，分開發用與驗收用
2. A、B 各答；多跑幾次先彙整成每題一個值（樣本是題數，不是題數 × 次數）
3. 盲評：同評審、同 rubric、不標版本，兩兩比較交換順序
4. 用 question_id 對齊，算 d 或 b、c
5. 用事先決定的檢定，報差異、CI、p、題數、b + c
6. 檢查護欄（[[primary-guardrail-gate]]）
7. 決策並看 b 格的退步案例，新失敗加進題庫

**陷阱**：重複執行當獨立樣本；看完結果才挑檢定；同一文件出的多題彼此相關；反覆針對同一題庫調 prompt（離線版 peeking）；忽略 b 格 {討論結論}{我的判斷}

## 相關
- [[ai-evaluation]]：評估總覽
- [[cuped]]：線上、不同使用者時的變異降低
- [[golden-dataset]]：題目從哪來
- [[primary-guardrail-gate]]：檢定之後的決策
- [[harness2]]：Harness² 候選的驗收方法
