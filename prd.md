# AI 智能發票管家 (AI Invoice RAG Assistant) - PRD

**版本：** v1.0 (MVP)
**負責人：** Amanda
**技術棧：** Flutter, Python (FastAPI), SQLModel, ChromaDB, Gemini 1.5 Flash
**開發時程：** 2-4 週
**團隊：** 獨立開發者

---

## 1. 產品概述 (Product Overview)

本專案旨在解決傳統記帳軟體輸入繁瑣、查詢不直觀的問題。透過 **RAG (Retrieval-Augmented Generation)** 技術，用戶可以利用自然語言對自己的消費紀錄進行深度提問與分析。

### 核心價值
- **自動化：** 拍照即記帳，無需手動輸入。
- **智能化：** AI 自動分類與品項解析。
- **語義搜尋：** 透過對話找尋消費脈絡（例如：我這週花多少錢在喝咖啡？）。

### MVP 範圍與延後項目

| 功能 | MVP v1.0 | v1.1 |
|------|----------|------|
| 單張發票拍照上傳與 AI 解析 | ✅ | |
| AI 預填 + 用戶確認/修正 | ✅ | |
| RAG 語義查詢 + SQL 精確查詢 | ✅ | |
| 多輪對話（短期記憶 5 輪） | ✅ | |
| 行事曆檢視發票歷史 | ✅ | |
| 固定分類清單 | ✅ | |
| 重複發票偵測（發票號碼） | ✅ | |
| 動態圖表（對話內嵌入圖表） | | ✅ |
| AI 自癒（錯誤智能修正） | | ✅ |
| 多張連續掃描 (Batch Scanning) | | ✅ |
| 品項新增/刪除（編輯畫面） | | ✅ |
| Refresh Token 機制 | | ✅ |

---

## 2. 系統架構 (System Architecture)

### 技術組件
- **Frontend:** Flutter (Mobile App, Material Design 3)
- **Backend:** Python FastAPI (RESTful API, OpenAPI Spec 先行)
- **Database:** PostgreSQL (透過 SQLModel 進行 ORM 操作)
- **Vector Store:** ChromaDB (儲存品項 Embeddings, Docker volume + PostgreSQL 同步持久化)
- **AI Models:** Gemini 1.5 Flash (OCR / Embedding / RAG Reasoning / Function Calling)

### 架構流程

```
Flutter App
    │
    ├── [拍照/上傳] ──→ POST /api/v1/invoices/parse
    │                        │
    │                        ├── Gemini Vision (OCR + 分類，合併為單次呼叫)
    │                        ├── 後端驗證層
    │                        └── 回傳結構化結果 → 用戶確認/修正
    │                                                │
    │                        ┌───────────────────────┘
    │                        ├── 存入 PostgreSQL (Invoice + InvoiceItem)
    │                        ├── 存入 ChromaDB (每品項一個向量)
    │                        └── 保留 AI 原始輸出 (ai_raw_output) + 用戶修正版
    │
    └── [對話查詢] ──→ POST /api/v1/chat
                          │
                          ├── Gemini Function Calling (意圖路由)
                          │     ├── query_database() → SQL 聚合查詢
                          │     ├── search_invoices() → ChromaDB 語義檢索
                          │     ├── get_spending_summary() → 消費摘要
                          │     └── get_category_breakdown() → 分類統計
                          │
                          └── Gemini 彙整回答 (繁體中文)
```

### 持久化策略
- **ChromaDB 雙重持久化：** Docker volume 日常使用 + PostgreSQL 保留向量資料副本（可重建）
- **發票圖片：** AI 解析完成後不保留原始圖片，僅保留結構化資料與 `raw_text`

---

## 3. 功能需求 (Functional Requirements)

### F1: 使用者認證系統 (Auth)

- **註冊：** 僅需 `username` + `password`，不需 email 驗證
- **登入：** 基於 **JWT** 的認證機制，確保資料隔離 (Multi-tenancy)
- **Token 策略：** MVP 使用長效期 JWT（7 天），v1.1 再加入 refresh token 機制
- **安全性：** 密碼使用 bcrypt 雜湊儲存

### F2: 智能發票解析 (AI Parsing)

#### 支援格式
- 電子發票截圖
- 常見紙本發票（超商、連鎖店等格式固定的紙本發票）

#### 解析流程
1. 用戶拍攝或上傳發票照片
2. 後端串接 **Gemini 1.5 Flash 視覺模型**（OCR + 分類合併為單次 LLM 呼叫）
3. 後端驗證層檢查結果合理性（金額 ≥ 0、日期不在未來、必填欄位完整）
4. 回傳結構化結果至前端，進入用戶確認/修正畫面
5. 用戶確認後存入資料庫

#### 解析輸出格式
```json
{
  "invoice_number": "AB-12345678",
  "store_name": "星巴克",
  "date": "2026-02-10",
  "total_amount": 150,
  "items": [{"name": "拿鐵", "price": 150, "quantity": 1}],
  "category": "餐飲",
  "raw_text": "原始 OCR 內容..."
}
```

#### 降級策略
- AI 解析結果一律進入「預填 + 用戶確認」畫面
- 用戶可修改所有欄位（MVP 不支援新增/刪除品項，v1.1 加入）
- 同時保留 AI 原始輸出與用戶修正版本，供未來 prompt 改進與微調使用

#### 重複偵測
- **主要：** 以 `invoice_number` 為主鍵（同一用戶下唯一）
- **輔助：** 比對 `store_name` + `total_amount` + `date` 組合
- 偵測到重複時提醒用戶，由用戶決定是否仍要儲存

#### 後端驗證規則
| 欄位 | 驗證規則 |
|------|---------|
| `total_amount` | ≥ 0，數字型態 |
| `date` | 不晚於今天，合法日期格式 |
| `store_name` | 非空字串 |
| `items` | 至少一個品項，每個品項 price ≥ 0 |
| `category` | 必須在固定分類清單內 |
| `invoice_number` | 格式驗證（若有） |

### F3: RAG 語義查詢助手 (Chat Assistant)

#### 查詢架構：SQL + RAG 混合 (Gemini Function Calling)

系統使用 Gemini 的 **Function Calling** 能力作為意圖路由，LLM 自行決定呼叫哪些工具：

| Tool | 用途 | 範例問題 |
|------|------|---------|
| `query_database` | SQL 聚合查詢（精確計算） | 「這個月總共花了多少？」 |
| `search_invoices` | ChromaDB 語義檢索 | 「上次買咖啡是在哪裡？」 |
| `get_spending_summary` | 時段消費摘要 | 「上週的消費概況」 |
| `get_category_breakdown` | 分類統計明細 | 「餐飲佔比多少？」 |

#### 對話機制
- **多輪對話：** 保留當次 session 最近 **5 輪** Q&A 作為上下文
- **短期記憶：** 僅在 session 內有效，不持久化對話歷史
- **回答語言：** 固定使用**繁體中文**回答
- **安全性：** 所有查詢嚴格過濾 `user_id`，防止資料外洩

#### Embedding 策略
- **粒度：** 每個 `InvoiceItem` 獨立生成一個向量
- **內容：** 將品項資訊組成描述文字再 embed，例如：`"2026-02-10 在星巴克購買拿鐵 $150 (餐飲)"`
- **Metadata：** 向量附帶 `user_id`, `invoice_id`, `date`, `category` 用於過濾

---

## 4. 非功能需求 (Non-Functional Requirements)

### 效能
- 單筆發票上傳至看到解析結果：**15 秒以內**
- 解析 pipeline 採非同步處理，前端顯示 loading 動畫與進度提示

### API 成本控制
- **請求合併：** OCR 與分類合併為單次 Gemini 呼叫，減少 API 請求數
- **Context Caching：** 利用 Gemini Context Caching 快取 system prompt，降低 token 消耗
- **佇列 + 重試：** 請求佇列控制並行度，觸及 rate limit 時指數退避重試
- 預期月預算 < NT$200（善用 Gemini 1.5 Flash 免費額度）

### 安全性
- RAG 檢索與 SQL 查詢嚴格執行 `user_id` 過濾
- 前後端雙重驗證（前端即時回饋 + 後端再次驗證）
- 密碼 bcrypt 雜湊，JWT 簽章驗證
- SQL 查詢使用參數化，防止 SQL injection

### 部署
- 自架 Docker (Home Server) 或 Oracle Cloud Always Free
- Docker Compose 管理多容器（API, DB, ChromaDB）
- 開發階段使用 FastAPI Swagger UI 進行接口管理

### API 版本管理
- **Contract-First：** 利用 FastAPI 自動生成 OpenAPI Spec，前後端依 spec 開發
- MVP 期間維持 v1 不做破壞性變更

---

## 5. 資料庫 Schema 設計 (Data Schema)

### User Table
| 欄位 | 型態 | 說明 |
|------|------|------|
| `id` | Integer (PK) | 主鍵 |
| `username` | String (Unique, Index) | 用戶名 |
| `hashed_password` | String | bcrypt 雜湊密碼 |
| `created_at` | DateTime | 建立時間 |

### Invoice Table
| 欄位 | 型態 | 說明 |
|------|------|------|
| `id` | Integer (PK) | 主鍵 |
| `user_id` | ForeignKey(User.id) | 所屬用戶 |
| `invoice_number` | String (Nullable, Index) | 發票號碼（同一用戶下唯一） |
| `store_name` | String | 店家名稱 |
| `total_amount` | Float | 總金額 |
| `date` | Date | 消費日期 |
| `category` | String | 分類（來自固定清單） |
| `raw_text` | Text | 原始 OCR 內容備查 |
| `ai_raw_output` | JSON | AI 原始解析結果（供未來改進用） |
| `created_at` | DateTime | 建立時間 |

### InvoiceItem Table
| 欄位 | 型態 | 說明 |
|------|------|------|
| `id` | Integer (PK) | 主鍵 |
| `invoice_id` | ForeignKey(Invoice.id) | 所屬發票 |
| `name` | String | 品項名稱 |
| `price` | Float | 品項單價 |
| `quantity` | Integer (Default: 1) | 數量 |

### ChromaDB 向量資料 (同步副本保存於 PostgreSQL)
| Metadata | 說明 |
|----------|------|
| `user_id` | 用戶 ID（檢索過濾用） |
| `invoice_id` | 對應發票 ID |
| `item_id` | 對應品項 ID |
| `date` | 消費日期 |
| `category` | 分類 |

---

## 6. 固定分類清單 (Category List)

以下為建議的初始分類清單（共 12 類），涵蓋台灣用戶常見消費場景：

| 分類 | 說明 | 範例 |
|------|------|------|
| 🍔 餐飲 | 外食、飲料、咖啡 | 星巴克、便當店、手搖飲 |
| 🛒 日用品 | 日常生活用品、清潔用品 | 超市、藥妝店 |
| 🚗 交通 | 加油、大眾運輸、停車 | 高鐵、Uber、加油站 |
| 🏠 居住 | 房租、水電、網路 | 電費、房租 |
| 🎮 娛樂 | 電影、遊戲、串流 | Netflix、KTV |
| 👕 服飾 | 衣服、鞋子、配件 | Uniqlo、百貨公司 |
| 🏥 醫療 | 看診、藥品、保健 | 診所、藥局 |
| 📚 教育 | 書籍、課程、文具 | 博客來、線上課程 |
| 💼 工作 | 辦公用品、設備 | 文具、3C 配件 |
| 🎁 社交 | 禮物、聚餐分攤 | 禮品店 |
| 🐾 寵物 | 寵物食品、醫療 | 寵物店、獸醫 |
| 📦 其他 | 無法歸類的消費 | 雜項 |

> AI 解析時從此清單中選擇最適合的分類。用戶在確認畫面可修改分類。

---

## 7. 前端規格 (Frontend Specification)

### 技術選型
- **框架：** Flutter
- **設計語言：** Material Design 3
- **圖表套件：** fl_chart（v1.1 動態圖表用）

### 導航結構

底部 Tab 導航 (Bottom Navigation Bar) + 中央凸出 FAB (Floating Action Button)

```
┌─────────────────────────────────┐
│                                 │
│         [主要內容區域]            │
│                                 │
├────┬────┬────┬────┬────────────┤
│ 🏠 │ 📅 │ 📷 │ 💬 │   ⚙️      │
│首頁 │日曆 │FAB │對話 │  設定     │
└────┴────┴────┴────┴────────────┘
```

| Tab | 功能 |
|-----|------|
| 首頁 | 概覽頁面：本月總支出、最近幾筆發票 |
| 日曆 | 行事曆檢視發票歷史 |
| FAB (中央) | 拍照/上傳發票（主要動作入口） |
| 對話 | RAG 對話助手 |
| 設定 | 帳戶管理、登出 |

### 主要畫面

#### 7.1 登入/註冊頁
- 帳號 + 密碼表單
- 登入/註冊切換

#### 7.2 首頁 (Dashboard)
- 本月總支出金額
- 最近 5 筆發票摘要清單
- 快捷入口至拍照與對話

#### 7.3 行事曆頁
- 月曆檢視，每個日期格子顯示**筆數 + 總額**（如「3 筆 / $450」）
- 點擊日期展開當天發票列表
- 點擊單筆發票進入明細頁

#### 7.4 發票拍照/上傳流程
1. 點擊中央 FAB → 選擇「拍照」或「從相簿選取」
2. 拍照/選取後顯示預覽
3. 確認上傳 → 顯示 loading 動畫（15 秒內完成）
4. AI 解析完成 → 進入確認/修正畫面

#### 7.5 發票確認/修正畫面
- 顯示 AI 預填的所有欄位：
  - 發票號碼、店名、日期、總金額、分類（下拉選單，固定清單）
  - 品項清單（MVP 僅可修改，不可新增/刪除）
- 「確認儲存」按鈕
- 前端即時驗證（金額 ≥ 0、日期格式等）

#### 7.6 發票明細頁
- 顯示完整發票資訊與所有品項
- 可編輯（進入修正畫面）
- 可刪除

#### 7.7 對話助手頁
- 聊天式 UI（氣泡訊息）
- 輸入框 + 送出按鈕
- 多輪對話，保留最近 5 輪上下文
- 回答固定使用繁體中文
- v1.1：回答中可嵌入動態圖表

#### 7.8 設定頁
- 顯示用戶名
- 登出按鈕

---

## 8. API 端點設計 (API Endpoints)

### Auth
| Method | Path | 說明 |
|--------|------|------|
| POST | `/api/v1/auth/register` | 用戶註冊 |
| POST | `/api/v1/auth/login` | 用戶登入，回傳 JWT |

### Invoices
| Method | Path | 說明 |
|--------|------|------|
| POST | `/api/v1/invoices/parse` | 上傳圖片，回傳 AI 解析結果（不存入 DB） |
| POST | `/api/v1/invoices` | 用戶確認後正式儲存發票 |
| GET | `/api/v1/invoices` | 取得發票列表（支援日期範圍篩選） |
| GET | `/api/v1/invoices/{id}` | 取得單筆發票明細（含品項） |
| PUT | `/api/v1/invoices/{id}` | 修改發票 |
| DELETE | `/api/v1/invoices/{id}` | 刪除發票 |
| GET | `/api/v1/invoices/calendar` | 取得行事曆摘要（每日筆數+總額） |

### Chat
| Method | Path | 說明 |
|--------|------|------|
| POST | `/api/v1/chat` | 發送對話訊息，回傳 AI 回答 |

> 所有 `/api/v1/invoices/*` 和 `/api/v1/chat` 端點皆需 JWT Bearer Token。

---

## 9. 目錄結構 (Folder Structure)

```
/
├── app/                      # 後端核心程式碼
│   ├── main.py               # FastAPI 入口與生命週期管理
│   ├── database.py           # SQLModel Engine 與 Session 設定
│   ├── auth.py               # JWT 加密與驗證邏輯
│   ├── models/               # SQLModel 資料模型定義
│   │   ├── user.py
│   │   ├── invoice.py
│   │   └── invoice_item.py
│   ├── api/                  # API 路由分層 (v1)
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── invoices.py
│   │       └── chat.py
│   ├── services/             # 業務邏輯層
│   │   ├── ai_parser.py      # Gemini 發票解析（OCR + 分類合併呼叫）
│   │   ├── rag_service.py    # RAG 檢索與 Function Calling 邏輯
│   │   ├── vector_store.py   # ChromaDB 操作與同步
│   │   └── validators.py     # 後端資料驗證規則
│   └── core/
│       ├── config.py         # 設定與環境變數
│       └── queue.py          # 請求佇列與 rate limit 管理
├── .env                      # 環境變數 (API Keys, DB Config)
├── docker-compose.yml        # 多容器環境配置 (API, DB, ChromaDB)
└── Dockerfile                # 後端鏡像定義
```

---

## 10. 成本與部署計劃 (Cost & Deployment)

- **運算：** 自架 Docker (Home Server) 或 Oracle Cloud Always Free
- **AI API：** Gemini 1.5 Flash 免費額度，透過請求合併 + context caching 降低消耗
- **維護：** 預期月預算 < NT$200

---

## 11. v1.1 延後功能規格摘要

以下功能確認延後至 v1.1，此處記錄設計意圖供後續開發參考：

### 動態圖表
- LLM 在回答中決定是否需要圖表及圖表類型
- 後端回傳結構化圖表配置 `{type, data, labels}`
- 前端使用 fl_chart 套件渲染

### AI 自癒 (Self-Healing)
- 後端驗證失敗時，根據錯誤類型採用不同修正策略：
  - 金額錯誤 → 重新 OCR 該區域
  - 日期錯誤 → 推斷修正（如 2025-13-01 → 提示用戶）
  - 分類錯誤 → 重新分類
- 若自癒仍失敗則交給用戶處理

### 多張連續掃描 (Batch Scanning)
- 支援一次掃多張發票，即時逐張非同步解析
- 搭配非同步排隊機制，用戶可邊掃邊看結果
- 完成後推播通知

### 品項完整編輯
- 確認畫面支援新增遺漏品項、刪除錯誤品項

### Refresh Token
- 短期 access token (15-30 分鐘) + refresh token 自動續期

---

## 12. 待辦清單 (Todo List)

### Phase 1: 基礎建設（第 1 週）
- [ ] 初始化 FastAPI 專案與 Docker Compose (API + PostgreSQL + ChromaDB)
- [ ] 實作 SQLModel 資料模型 (User, Invoice, InvoiceItem)
- [ ] 實作使用者註冊/登入 API (JWT)
- [ ] 建立 OpenAPI Spec 基礎結構

### Phase 2: 核心功能（第 2 週）
- [ ] 整合 Gemini 1.5 Flash 發票解析邏輯（OCR + 分類合併呼叫）
- [ ] 實作後端驗證層
- [ ] 實作發票 CRUD API
- [ ] 整合 ChromaDB 向量儲存（每品項一向量）+ PostgreSQL 同步

### Phase 3: RAG 對話（第 3 週）
- [ ] 實作 Gemini Function Calling 工具定義
- [ ] 實作 SQL 聚合查詢工具
- [ ] 實作 ChromaDB 語義檢索工具
- [ ] 實作多輪對話 API（5 輪短期記憶）
- [ ] 請求佇列與 rate limit 管理

### Phase 4: Flutter 前端（第 2-4 週並行）
- [ ] Flutter 專案初始化 (Material Design 3)
- [ ] 登入/註冊頁面
- [ ] 底部導航 + FAB 結構
- [ ] 發票拍照/上傳 + 確認修正畫面
- [ ] 行事曆檢視頁面
- [ ] 對話助手頁面
- [ ] 首頁 Dashboard
