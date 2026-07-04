# 檔案完整性檢查報告

## 1. 檢查時間

2026-07-04 20:42(+08:00)

## 2. 檢查的主要資料夾

本機的 GitHub repo 工作副本([taiwan-attention-momentum-signal](https://github.com/Harry970417/taiwan-attention-momentum-signal),
分支 `main`)

本次檢查**未重新執行任何資料蒐集或研究計算**,僅檢查既有檔案的完整性、
連結、格式、PDF 可用性、禁用詞與敏感資訊。

## 3. 檢查的檔案清單

- 根目錄:`README.md`、`README_zh.md`、`requirements.txt`、`.gitignore`、`LICENSE`
- `docs/`:`methodology.md`、`literature_review.md`、`research_findings.md`、
  `limitations.md`、`portfolio_writeup_zh.md`、`portfolio_pdf_page_zh.md`、
  `autobiography_excerpt_zh.md`、`interview_pitch_zh.md`
- `reports/`:`final_research_report.md`、`TAS_v0.2_Result_Snapshot.md`、
  `TAS_v0.3_Momentum_Control_Report.md`、`TAS_v0.4_Final_Research_Interpretation.md`、
  `repo_quality_check.md`
- `exports/TAS_推甄作品集頁面.pdf`
- `results/figures/`(8 個圖檔)、`results/tables/`(8 個 CSV)
- `src/`、`app/`、`scripts/`、`config/`(結構性確認,未逐檔審閱程式碼)

全部 24 項結構性檢查(任務 1 清單)皆存在,無缺失,無需從 GitHub 歷史或
備份資料夾復原任何檔案。

## 4. PDF 是否可開啟

**發現重大問題並已修正。** `exports/TAS_推甄作品集頁面.pdf`(修正前
38,752 bytes)實際內容是 Chrome 的「無法存取你的檔案 / ERR_FILE_NOT_FOUND」
錯誤頁面,而不是真正的作品集摘要——原因是先前產生 PDF 時,`--print-to-pdf`
使用了 Git Bash 的 POSIX 風格路徑(`file:///c/Users/...`)而非 Windows
風格路徑,導致 Chrome 找不到來源 HTML,把自己的錯誤頁面存成了 PDF;先前
的視覺驗證誤用了另一份用正確路徑重繪的截圖,沒有驗證到真正被 commit 的
那份 PDF。

修正方式:改用 `file:///C:/...` 正確路徑重新以 headless Chrome 從
`docs/portfolio_pdf_page_zh.md` 轉出的 HTML 產生 PDF,並收緊版面 CSS
margin/字級以壓回 1 頁,以 `pypdf` 逐字抽取驗證內容。

修正後結果:
- 檔案大小:226,706 bytes
- 頁數:**1 頁**
- 內文包含「CAAR」「v0.2」「github.com/Harry970417」等預期字串
- **不含** `ERR_FILE_NOT_FOUND`、「無法存取你的檔案」等錯誤頁面字樣
- 標題、九大區塊、三階段修正表格皆完整呈現(以螢幕截圖覆核排版無破版)

## 5. README 連結是否正常

檢查 `README.md`、`README_zh.md` 全部相對連結(共 26 條),逐一以檔案系統
確認目標存在。發現 1 處缺漏:`reports/final_research_report.md` 存在於
repo 中,但兩份 README 都沒有連結到它——已在 `README.md` 第 9 節
「Research Evolution」補上「Final Research Report」連結。其餘連結全部
正常,無需修正。

## 6. Markdown 是否正常

檢查全部 15 個 `.md` 檔案:
- 標題層級:皆為 H1 → H2(→ H3)正常遞增,無跳級
- 表格:皆正常,無破版
- 亂碼:無 U+FFFD 替代字元
- 斷行:無「條件式」被切斷等異常換行
- 多餘符號:無孤立 `--` 分隔線、無未閉合的程式碼區塊
- 個人絕對路徑:`reports/repo_quality_check.md` 開頭原本記錄了一段本機
  絕對路徑,已於後續修正中改寫為通用描述,現況為 PASS(無殘留)
- 舊檔案引用:無殘留對 `admissions_three_versions_zh.md` 等已刪除草稿的引用

發現並修正 2 處小格式問題(標題缺空格):
- `reports/TAS_v0.3_Momentum_Control_Report.md`:「Regression Evidence(Fama-MacBeth)」→「Regression Evidence (Fama-MacBeth)」
- `reports/TAS_v0.4_Final_Research_Interpretation.md`:「Strategy Group Comparison(研究型排序比較,非交易策略)」→ 加空格

## 7. 禁用詞檢查結果

全文搜尋中英文禁用詞清單(穩定獲利、可直接交易、打敗市場、獨立 alpha、
投資建議、guaranteed、profitable trading strategy、beat the market、
predict stock price、independent alpha factor)。

共 12 處命中,**逐一檢視後全部屬於否定式表述**(例如「不構成投資建議」
「不是能獨立於動能存在的 alpha」「not an independent alpha factor」「不能
包裝成…獨立 alpha 因子」),符合允許保留的用法,**無需修改**。

## 8. 敏感資訊檢查結果

搜尋 `C:\Users\`、`api_key`、`token`、`secret`、`password` 等關鍵字於全
專案(排除 `.git/`):僅 `.gitignore` 本身列出這些字樣作為排除規則,無任何
實際洩漏。專案中不存在 `.env`、`secrets.toml`、`*.key`、`*.token` 等檔案。
`.gitignore` 已涵蓋所需全部規則,無需修改。

## 9. 是否有缺失檔案

無。任務 1 清單中的所有檔案與資料夾皆存在。

## 10. 已自動修正哪些問題

1. **(重大)** 重新產出 `exports/TAS_推甄作品集頁面.pdf`(原檔為壞掉的
   Chrome 錯誤頁面,現為正確的 1 頁摘要)
2. 在 `README.md` 補上 `reports/final_research_report.md` 的連結
3. 修正 2 處 `reports/` 標題缺空格的小格式問題

## 11. 是否已 commit / push

是,詳見本次任務最終回報中的 commit hash。

## 12. 最終狀態

修正後,repo 結構完整、PDF 可正常開啟且內容正確、README 連結全部有效、
Markdown 格式一致、禁用詞與敏感資訊檢查皆為 PASS、`.gitignore` 規則齊全、
`data/raw`/`data/processed` 未被追蹤。**Repo 可公開提供給教授或面試官
審閱。**
