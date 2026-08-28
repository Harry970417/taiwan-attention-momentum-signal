# 自傳摘要段落

我在台股 Google Trends 注意力研究中，原先建立了從資料收集、因子建構、事件研究、Fama-MacBeth 迴歸到法人控制的完整流程。後續方法稽核時，我主動發現 Google Trends 週資料存在 information availability 風險：舊版把週資料日期標籤直接當成訊號可用日，可能形成 look-ahead bias。

我沒有保留較漂亮的舊結論，而是把研究降級為 retrospective association study，並重構管線：加入完整 as-of contract、保守延遲一個週期、讓 forward return 從真正可交易日之後開始，並新增 no-look-ahead 測試。這段經驗讓我更重視資料時間語意、研究可重現性，以及在證據不足時誠實修正結論。
