# Google Trends 台股注意力研究：修正版作品集摘要

## 專案定位

我用 Google Trends 週搜尋量、FinMind 股價與法人資料，研究台股大型權值股的投資人注意力是否與短期報酬和價格動能有關。

## 重大修正

後續稽核發現舊版管線有 critical availability / look-ahead bias：Google Trends 週資料的日期標籤被當成訊號可用日，可能把尚未完整可取得的週資料用於當週交易測試。

## 修正方式

- 建立 as-of contract：`observation_period_start`、`observation_period_end`、`available_at`、`signal_date`、`first_tradeable_at`、`return_start`、`return_end`。
- Google Trends 週資料至少延遲一個完整週期後才可形成訊號。
- forward return 從訊號真正可交易之後開始。
- 新增 no-look-ahead assertions 與單元測試。
- corrected 輸出使用 `_asof_safe`，不覆蓋舊結果。

## 目前結論

截至 2026-08-02，此 checkout 缺少真實 `data/raw/` 與 `data/processed/`，因此尚未能重跑 corrected 結果。舊版「attention 是 conditional momentum amplifier」只能視為未修正對齊下的 retrospective association，不可作為可交易預測策略。

## 展示能力

這個專案展示的是研究工程能力：能追查資料時間語意、主動推翻舊結論、把前視偏誤落成可測試契約，並誠實保留新舊結果 provenance。
