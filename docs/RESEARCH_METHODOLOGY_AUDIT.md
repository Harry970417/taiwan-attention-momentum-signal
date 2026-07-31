# 獨立方法論稽核記錄

稽核日期：2026-07-31
稽核者：本次任務（不同於原研究撰寫過程），目的是在把研究包裝成公開展示頁之前，
先獨立驗證「有沒有前視偏誤／資料對齊錯誤／結論誇大」，而不是照抄專案自己的說法。

---

## 1. 稽核範圍與方法

依使用者要求檢查的項目：attention 資料日期、週資料對齊、forward return 是否正確延後、
look-ahead bias、Google Trends 標準化、缺失資料處理、事件重疊、樣本選擇、產業分類、
法人資料對齊、迴歸標準誤、顯著性解讀、圖表與文字結論是否一致、相關性是否被誤寫成因果關係、
是否誇大獲利能力。

方法：直接讀取 `src/` 原始碼（非只看文件描述），對照 `docs/limitations.md`、
`docs/methodology.md`、`README.md` 的既有揭露是否與程式碼行為一致。

## 2. Forward return 是否有前視偏誤 — **未發現問題**

`src/attention_factor.py::build_for_stock()`：

```python
for n in FORWARD_WINDOWS:
    s_fwd = window_return(price["close"], date, n, "forward")
    ...
```

`window_return(..., "forward")` 的實作：

```python
d0 = nearest_at_or_after(idx, date)
d1 = nearest_at_or_after(idx, date + pd.Timedelta(weeks=n_weeks))
```

即 `future_{n}w_return` 一律是「從當週（含）往後 n 週」的報酬，起點不早於事件週本身，
在機制上不會把事件週之後才發生的價格資訊，錯誤地混進事件週當下的 `attention_z` 中
（`attention_z`／`attention_shock` 只用 `SVI` 與其 52 週移動平均/標準差計算，
兩者的計算窗口都在 `date` 或更早）。**未發現前視偏誤。**

## 3. 週資料對齊 — 已知限制，揭露方式合理

`nearest_at_or_after` / `nearest_at_or_before` 對齊到最近的實際交易日，而非強制假設
每週固定星期幾都有資料，可正確處理國定假日、颱風假等非交易日造成的資料缺口。
未發現對齊邏輯錯誤。

## 4. Google Trends 跨股票標準化 — 已知限制，且已證明不影響核心結論

`docs/limitations.md` 明確揭露 pytrends 的 0–100 標準化不能跨請求直接比較，並說明
所有假設檢定都只用「股票對自己歷史的標準化分數」（`attention_z`），不使用跨股票原始 SVI 水準。
稽核確認：`attention_z`、`attention_shock` 的計算公式（`(SVI-SVI_MA52)/SVI_STD52`）
確實只依賴同一檔股票的歷史序列，此揭露與程式碼行為一致，不是文件寫好聽而已。

## 5. 事件時間重疊與統計顯著性 — 已知限制，揭露誠實

`docs/limitations.md` 指出注意力事件在日曆時間上高度群聚（部分週有 16–26/50 檔同時觸發），
一般 t 檢定與 bootstrap 信賴區間未修正橫斷面相關性，可能高估顯著性；Fama-MacBeth 迴歸
用了週群聚穩健標準誤部分緩解，但作者自己也承認「未完全解決」。**此為稽核中發現的
最需要讀者留意的方法論限制**，但屬於誠實揭露而非隱瞞，本次稽核未發現比既有文件描述更嚴重的問題。

## 6. 產業固定效果 — 已知限制，且作者已正確判斷該結果不可信

30 個產業對應 50 檔股票，多數產業僅 1–2 檔成分股。`limitations.md` 明確指出，v0.3 產業固定效果
模型的 R²≈0.89 是過度配適假影，其在 1 週窗口失去顯著性**不應**被解讀為對效應本身的反證。
稽核同意此判斷：以每組 1–2 個觀測值估計固定效果，統計上本來就不可靠，作者的處理方式
（明確標註不可信、不用於支持或反駁主結論）是正確的研究誠信做法。

## 7. 法人資料單位 — 已知限制，已修正過一次且揭露正確

FinMind 免費層級的三大法人買賣超資料只有「股數」，沒有「金額」，但變數名稱沿用
`*_net_buy_value_*`（因為要跟原始變數規格保持一致）。`limitations.md` 已明確聲明此為股數
而非金額，稽核抽查 `data/sample/attention_weekly_panel_sample.csv` 的
`foreign_net_buy_value_1w` 等欄位數值量級（約 -3.6×10⁷ 到 -1.3×10⁸），與「股數」量級相符，
不是誤植的金額欄位。

## 8. 結論措辭是否誇大 — **未發現誇大**

檢查 `README.md` §3 Key Finding、§15 Disclaimer 與 `docs/limitations.md` 的用詞：
全文使用「conditional amplifier」（條件式放大器）而非「independent predictive signal」
（獨立預測訊號），明確排除「可交易策略」「投資建議」的定位，並在 §13 逐項列出樣本侷限
（僅 50 檔大型股、多頭期間、未模擬交易成本與放空限制）。**未發現把相關性寫成因果關係、
或把統計顯著結果包裝成獲利保證的情況。**

## 9. 稽核未涵蓋的部分（誠實聲明）

受限於時間，本次稽核**未**重新執行完整資料管線（Google Trends 重新抓取需 30–60 分鐘且
受速率限制）、**未**獨立重算 CAAR／IC／Fama-MacBeth 的數值是否與 `results/tables/` 完全吻合
（僅檢查程式邏輯與抽樣資料，未逐行重跑統計檢定）。若需要更高強度的驗證，建議下一輪執行
`python scripts/run_all.py` 並比對輸出數字與 `docs/research_findings.md` 是否一致。

## 10. 結論

本次獨立稽核**未發現前視偏誤、資料對齊錯誤、或結論誇大**。專案既有的 `docs/limitations.md`
揭露品質高，且經程式碼比對後確認揭露內容與實際實作行為一致，不是文件寫得好聽但程式碼另一套。
唯一建議加強的是第 5 點（日曆群聚導致的顯著性高估）在對外展示頁面（Streamlit 研究總覽）
中應該更顯眼地提及，本次已在 `app/streamlit_app.py` 的「研究總覽」頁加入限制摘要區塊處理。
