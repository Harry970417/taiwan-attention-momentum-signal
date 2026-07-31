# 重現指南

驗證日期：2026-07-31 — 以下步驟中標註「✅ 本次已驗證」的部分已實際執行確認；
標註「未驗證」的部分因外部 API 速率限制/時間成本，本次未實際跑完整流程，
依 README 既有說明轉錄，供讀者知悉尚未獨立覆核。

---

## 0. 為什麼資料夾裡看不到完整資料

`data/processed/attention_weekly_panel_50.csv`（50 檔股票 × 全部週數的完整面板）**沒有**
被提交到 git（見 `.gitignore`：`data/raw/`、`data/processed/`、`data/cache/` 均排除）。
這是刻意設計，不是遺漏——資料要靠公開 API（Google Trends + FinMind）重新產生，
避免 repo 內含過期或無法驗證來源的資料快照。

只有 `data/sample/attention_weekly_panel_sample.csv`（3 檔股票 × 20 週的示範資料）被提交，
可用來檢視欄位結構，不需要跑完整流程。

## 1. 環境安裝 — ✅ 本次已驗證可正常 import 與編譯

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

本次稽核以 `python -m py_compile src/*.py scripts/*.py app/streamlit_app.py` 確認
所有原始碼可正確編譯（無語法錯誤、無明顯 import 期失敗）。

## 2. 完整資料管線 — 未驗證（受 Google Trends 速率限制，預期耗時 30–60 分鐘以上）

```bash
python scripts/run_all.py
```

或分階段執行：

```bash
python scripts/run_data_collection.py         # Google Trends + FinMind 抓取
python scripts/run_event_study.py             # CAAR 事件研究
python scripts/run_momentum_control.py        # v0.3 動能控制
python scripts/run_institutional_flow_analysis.py  # v0.4 法人籌碼控制
```

Google Trends 對同一 IP 的請求有嚴格速率限制，`pytrends` 端已內建重試機制，
但仍可能因限流而中途失敗；README 已就此風險做出說明，本次稽核未重新驗證此風險是否仍然存在。

## 3. Streamlit 研究儀表板 — ✅ 本次已驗證（含修復後行為）

```bash
streamlit run app/streamlit_app.py
```

**驗證方式**：在完整面板資料（步驟 2 的產出）不存在的情況下啟動（即一般人剛 clone 這個
repo、還沒有跑過資料管線的真實狀態），實際用瀏覽器開啟並截圖確認：

- 修復前：整頁只顯示紅色錯誤訊息「找不到 .../attention_weekly_panel_50.csv」，
  沒有任何研究內容或引導，第一次接觸的使用者完全看不出這個專案在做什麼。
- 修復後：預設顯示「研究總覽」頁，包含 30 秒摘要、3 分鐘圖表walkthrough（CAAR 事件研究圖
  + 雙重排序熱力圖，讀取 `results/figures/` 下已提交的靜態圖片，不需要完整面板資料）、
  限制摘要、完整版文件連結。只有「資料總覽」「注意力雷達」「個股查詢」三個需要完整面板資料的
  頁面會在資料不存在時從側邊欄隱藏（而非顯示壞掉的畫面）。

若已產生完整面板資料，全部 5 個頁面（研究總覽／資料總覽／注意力雷達／個股查詢／研究結果）
都會出現在側邊欄。

## 4. 驗證輸出數字是否與報告一致 — 未驗證

`docs/research_findings.md`、`README.md` §8 Main Results 中的數字（CAR@+8w=+14.2%、
ICIR≈0.31 等）本次未重新逐一比對 `results/tables/` 的實際輸出檔案內容。
若需要高強度驗證，建議：

```bash
python scripts/run_all.py
# 完成後比對：
diff <(cat results/tables/*.csv) <(參考 docs/research_findings.md 中的數字)
```

## 5. 已知會擋路的地方

- **FinMind 免費額度**：`docs/limitations.md` 與 README 提及套件版本相依性問題，
  若安裝新版 Python 環境時 FinMind 相依套件衝突，參考 `requirements.txt` 鎖定版本。
- **Google Trends 限流**：預期正常現象，非程式錯誤，`run_all.py` 已有重試邏輯。
- **中文字型**：`app/streamlit_app.py` 已設定 `Microsoft JhengHei` 作為 matplotlib 中文字型，
  非 Windows 環境（如 Linux CI）需自行安裝對應中文字型，否則圖表中文標籤會顯示方框。
