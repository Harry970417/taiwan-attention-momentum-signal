# 作品集文字版：Google Trends 台股注意力研究（修正版狀態）

本專案原本想檢驗：台股大型權值股的 Google Trends 搜尋量異常上升，是否能預測短期超額報酬，並且這個效果是否獨立於價格動能與法人買賣超。

在後續方法稽核中，我發現原始版本存在一個 critical 問題：Google Trends 的週資料被用日期標籤直接對齊到當週交易訊號。若該日期代表週資料的觀測週起始日，舊管線就可能把尚未完整可取得的整週搜尋量拿來測同週或緊接著的 forward return，形成 availability / look-ahead bias。

我因此把研究從「漂亮的顯著結果」退回到工程與研究方法修復：

- 建立明確 as-of contract：`observation_period_start`、`observation_period_end`、`available_at`、`signal_date`、`first_tradeable_at`、`return_start`、`return_end`。
- 採保守假設：Google Trends 週資料至少延遲一個完整週期後才可形成訊號。
- 讓 forward return 從真正可交易之後開始。
- 加入 no-look-ahead assertions。
- 新增測試涵蓋跨週、跨月、跨年、假日、缺資料、Google Trends 週界線與 trailing z-score。
- 舊結果不覆蓋，改用 `_asof_safe` 輸出 corrected 結果，並用 provenance table 標記舊結果為 superseded / invalidated。

截至 2026-08-02，此 checkout 沒有 `data/raw/` 與 `data/processed/`，所以 corrected 結果尚未能用真實原始資料重跑。舊版「attention 是 conditional momentum amplifier」的說法目前只能視為未修正資料對齊下的 retrospective association，不可寫成 real-time tradable predictive strategy。

這個專案目前最能展示的能力，不是找到一個可交易訊號，而是：能主動追查資料時間語意、推翻自己原本較好看的結論、把前視偏誤寫成可測試的程式契約，並保留新舊結果 provenance。
