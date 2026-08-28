# 90 秒面試說明

我做了一個台股研究專案，用 Google Trends 週搜尋量搭配 FinMind 股價與法人資料，檢驗投資人注意力是否和短期報酬、價格動能有關。

這個專案最重要的地方不是舊版結果顯著，而是我後來發現並修正了一個 critical 方法問題：Google Trends 週資料的日期標籤不能直接當成訊號可用日。若那是觀測週起始日，舊版就可能用了當時還不完整的整週搜尋量，造成 look-ahead bias。

我把修正落成工程契約：每筆週資料都要有 `observation_period_start`、`observation_period_end`、`available_at`、`signal_date`、`first_tradeable_at`、`return_start`、`return_end`。在不能證明 Google Trends 歷史發布時點的情況下，我採保守做法，至少延遲一個完整週期後才產生訊號，forward return 也必須從真正可交易之後開始。

目前此 checkout 缺少真實 raw data，所以 corrected 結果還不能重跑；舊結論已降級為 retrospective association study，而不是 real-time tradable predictive strategy。這個專案展示的是我能把資料時間語意、研究設計和程式測試接起來，也能在結果變差時誠實修正結論。
