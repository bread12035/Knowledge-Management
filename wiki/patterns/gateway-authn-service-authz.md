---
id: gateway-authn-service-authz
title: Gateway 認證、服務授權（AuthN at gateway, AuthZ in service）
type: pattern
summary: Authentication 集中在單一入口的 Gateway，白名單寫死不信任自稱來源；後端服務只做 Authorization
domains: [system-design]
sources: [raw/system-design/trino-gateway-oidc-watermark-pattern.md#為什麼採用這些技術, raw/system-design/pagerduty-escalation-chatops-runbook-pattern.md#Why, raw/system-design/webhook-idempotent-worker-outbox-pattern.md#Why, raw/system-design/onprem-to-gcp-traffic-flow-dns-proxy-gateway-mesh-pattern.md#設計原因]
evidence: [使用者決定, 討論結論]
related: [reliable-event-processing, worker-monitor-split, earnings-gcp-onprem-handover]
status: active
created: 2026-11-18
last_dreamed: 2026-11-18
review_count: 0
next_review: 2026-11-19
---
# Gateway 認證、服務授權（AuthN at gateway, AuthZ in service）

> Authentication 集中在單一入口的 Gateway，白名單寫死不信任自稱來源；後端服務只做 Authorization

## 重點
- Chat-service：Client 從 Keycloak 拿 JWT，API Gateway（FastAPI）驗簽與 issuer，後端只做 Authorization {使用者決定}
- Realm URL 與演算法白名單寫死在 Gateway，不信任 client 傳來的值，防 JWT algorithm confusion 與 issuer 偽造 {使用者決定}
- 每個下游各自驗證除了重複，還容易出現「相信呼叫方宣稱的來源」的漏洞 {討論結論}
- 驗證收斂到 Gateway 後，worker 與 monitor 可假設身份為真，不必每層重驗 {討論結論}
- Log 系統的 PowerBI、自建 App、Claude（MCP）都經同一個 stateless Gateway 查 Trino；PowerBI 不可直接下 SQL {使用者決定}

## 細節
- 併發 < 3、每 3 小時更新，Gateway 不需要狀態層或快取，有狀態中間層是過度設計 {使用者決定}
- Webhook：Stripe 帶簽章、GitHub 帶 `X-Hub-Signature`；Web 層只驗簽、丟 queue、立刻回應 {討論結論}
- 單一出入口：企業出口 reverse proxy、GCP 入口 GKE Gateway、跨邊界的 Adapter，都是為了集中管控與稽核 {討論結論}
- Lyft trino-gateway：多個 Trino 前放 stateless gateway，負責路由、限流、集中驗證 {討論結論}

## 在設計中怎麼用
- 什麼情況用：有多種來源（Slack、webhook、App、BI、agent）呼叫同一組服務。
- 怎麼用：一個入口驗身份（簽章、issuer、演算法白名單寫死）→ 帶已驗證身份往下 → 服務只判斷「這個人能不能做這件事」。
- 代價：Gateway 是單點，要做高可用；Gateway 保持 deep module，只轉發與驗證，不扛快取等額外職責。

## 相關
- [[reliable-event-processing]]：事件進來的第一層
- [[worker-monitor-split]]：驗證之後的分層
- [[earnings-gcp-onprem-handover]]：單一出入口的實例
