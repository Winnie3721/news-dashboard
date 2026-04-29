# 新聞看板 — GitHub 部署指南

第一次部署：跟著步驟做，約 10 分鐘。

---

## 前置：你的資訊

- GitHub username：`Winnie3721`
- 預定 repo 名稱：`news-dashboard`
- 完成後網址：`https://winnie3721.github.io/news-dashboard/`

---

## 步驟 1：在 GitHub 建立空 repo（網頁操作，2 分鐘）

1. 登入 https://github.com/Winnie3721
2. 右上角 `+` → `New repository`
3. 設定：
   - **Repository name**：`news-dashboard`
   - **Description**：`Personal daily intelligence dashboard`（可選）
   - **Visibility**：選 **Public**（公開，這樣 Actions 完全免費 + 才能用 Pages）
   - **不要勾** Initialize this repository with（README、.gitignore、license 都不要勾，我們自己上傳）
4. 點 `Create repository`
5. 看到「Quick setup」頁面後，**保留這個分頁**，等下會用到網址

---

## 步驟 2：在你電腦初始化 git 並推上 GitHub（5 分鐘）

打開 PowerShell 或 Git Bash，貼這串指令（一次貼整段）：

```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板

git init -b main
git add .
git config user.name "Winnie3721"
git config user.email "你的 GitHub 註冊用 Email"
git commit -m "Initial commit: 新聞看板 v0.1"
git remote add origin https://github.com/Winnie3721/news-dashboard.git
git push -u origin main
```

⚠ **記得把第 4 行的 `你的 GitHub 註冊用 Email` 改成你的真實 Email**（與 GitHub 帳號的一致）

第一次 push 會跳出登入視窗：用瀏覽器登入 GitHub 即可。

---

## 步驟 3：開啟 GitHub Pages（網頁操作，1 分鐘）

1. 進你的 repo：https://github.com/Winnie3721/news-dashboard
2. 點上方 `Settings`
3. 左側選單點 `Pages`
4. 設定：
   - **Source**：`Deploy from a branch`
   - **Branch**：`main` / `/ (root)`
5. 點 `Save`
6. 大約 30 秒~2 分鐘後，畫面上會出現綠色框：
   `Your site is live at https://winnie3721.github.io/news-dashboard/`

→ 點開這個網址 = 看到你的 Dashboard ✓

---

## 步驟 4：開啟 GitHub Actions 自動更新（網頁操作，1 分鐘）

1. 進 repo 上方 `Actions` 分頁
2. 第一次進來會看到「Workflows aren't being run on this fork」之類提示，點 `I understand my workflows, go ahead and enable them`
3. 左側看到 `Auto Update Dashboard` workflow
4. 點進去，右上角有 `Run workflow` 按鈕（手動觸發測試一次）
5. 看到綠色 ✓ 表示成功（約 2 分鐘）

之後就會 **每天 06:50 + 18:00 TPE 自動跑**，不需要你做任何事。

---

## 步驟 5：之後怎麼維護？

### 每天早上：編輯 Intelligence Layer

**方法 A（最方便，手機也能用）**
1. 打開 https://github.com/Winnie3721/news-dashboard/edit/main/data/intel.json
2. 改 thesis、top_3_events、why_it_matters 等欄位
3. 拉到最下面 `Commit changes` → 直接點 `Commit changes`
4. 30 秒~1 分鐘後 Dashboard 自動更新

**方法 B（在你電腦改）**
```bash
cd C:\Users\wenny\Desktop\WorkSpace\新聞看板
git pull
# 編 data/intel.json
git add data/intel.json
git commit -m "intel: <日期>"
git push
```

### 想加新聞來源 / 改設定

```bash
git pull
# 編 src/config.py 或 dashboard/template.html
git add -A
git commit -m "<簡述>"
git push
```

修改 `src/` 或 `dashboard/template.html` 後，下次 cron 跑（或手動 Run workflow）就會用新版生效。

---

## 排程說明

| 任務 | 觸發時機 | 內容 |
|------|---------|------|
| 自動抓取 | 每天 06:50 TPE | 新聞 + 加密 + 股市 + 機構報告 + 重 build dashboard |
| 自動抓取 | 每天 18:00 TPE | 同上 |
| 手動觸發 | 隨時可從 Actions 介面按 `Run workflow` | 同上 |

> ⚠ Actions 排程**不保證精準**，可能延遲 0-15 分鐘。對 7 點看 Dashboard 可接受。

---

## 故障排除

| 症狀 | 可能原因 | 解法 |
|------|---------|------|
| Pages 網址 404 | Pages 還沒部署完 | 等 2 分鐘再開 |
| Actions 紅 X | RSS 來源暫時掛掉 | 看 Actions log；通常下一輪自動恢復 |
| Push 被拒 | 沒登入或無權限 | 重新登入 GitHub |
| Actions 沒跑 | 帳號剛建沒驗證 | Settings → Actions → 開啟 |

---

## 之後的下一步（Phase 2）

當你想接 WhatsApp + AI 摘要時：
1. 申請 Claude API key + CallMeBot 啟用
2. 把 key 放 GitHub Secrets（不會公開）
3. 讓 Action 在抓完之後產 AI brief + 推 WhatsApp

那時候我們再做。

---

## 你需要的資源

- GitHub username: `Winnie3721`（已知）
- GitHub 註冊 email：（部署時填入）
- 部署網址（部署後）：`https://winnie3721.github.io/news-dashboard/`
