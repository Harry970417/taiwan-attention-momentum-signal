# Taiwan Attention Momentum Signal

繁中說明版。英文版見 [README.md](README.md)。

## 重大方法狀態（2026-08-02）

本專案舊版 headline 結果已標記為 **superseded / invalidated**，不得再解讀為
real-time tradable predictive strategy。

根因是舊管線把 Google Trends 週資料的日期標籤直接當成訊號可用日。若該日期其實是
Google Trends 週資料的觀測週起始日，舊分析就可能在同一週交易測試中使用當時尚未完整可取得的
SVI，形成 availability / look-ahead bias。

修正後管線已建立 as-of-safe contract：

`observation_period_start` -> `observation_period_end` -> `available_at` ->
`signal_date` -> `first_tradeable_at` -> `return_start` -> `return_end`

保守規則是：未能證明當時已可取得的週資料，不得用於當週交易；Google Trends 週資料至少延遲一個完整週期後才形成訊號；forward return 必須從訊號真正可交易之後開始。

目前此 checkout 缺少 `data/raw/` 與 `data/processed/`，因此尚未用真實原始資料重跑出
`*_asof_safe` corrected 結果。在 corrected 結果產生前，本研究只能降級描述為
**retrospective association study**，不是可即時交易的預測策略。

## 目前可相信的內容

- 程式層級已加入 as-of-safe 日期欄位與 no-look-ahead assertions。
- 新增測試涵蓋跨週、跨月、跨年、假日、缺 forward 價格、Google Trends 週界線與 trailing z-score。
- 舊結果表已透過 `results/tables/legacy_results_provenance.csv` 標記為 superseded / invalidated。
- `results/tables/asof_safe_legacy_comparison.csv` 會在 corrected 結果存在時產生新舊差異表；目前因 corrected tables 尚未生成而標示 blocked。

## 舊結論狀態

舊版曾主張 Google Trends attention 是「conditional momentum amplifier」。此說法目前只能作為未修正 alignment 下的 retrospective association，不可作為 corrected empirical conclusion，也不可寫成可交易預測策略。

## 如何重跑 corrected pipeline

需要真實原始資料，不可使用 `data/sample/` 當研究證據：

```powershell
python scripts\run_data_collection.py
python scripts\run_event_study.py
python scripts\run_momentum_control.py
python scripts\run_institutional_flow_analysis.py
```

如果 Google Trends / FinMind API quota、授權、歷史資料不足或資料定義漂移導致資料不完整，必須停止對應子流程並如實回報，不得用 demo、mock 或 synthetic data 補成研究結果。
