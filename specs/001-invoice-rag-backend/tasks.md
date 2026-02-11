# 任務清單：AI 智能發票管家後端

**輸入**: 設計文件來自 `/specs/001-invoice-rag-backend/`
**前置條件**: plan.md（必要）、spec.md（必要）、research.md、data-model.md、contracts/

**測試**: 依據憲法原則 VI，TDD + BDD 為必要。

**組織方式**: 任務按使用者故事分組，支援獨立實作與測試。

## 格式: `[ID] [P?] [故事] 描述`

- **[P]**: 可平行執行（不同檔案、無依賴）
- **[故事]**: 對應使用者故事（如 US1、US2、US3）
- 描述中包含確切檔案路徑

---

## 第 1 階段：專案初始化

**目的**: 專案建立與基本結構

- [X] T001 依 plan.md 建立專案目錄結構（`app/`、`app/models/`、`app/schemas/`、`app/api/v1/`、`app/services/`、`app/core/`、`tests/`、`tests/unit/`、`tests/integration/`、`tests/bdd/features/`、`tests/bdd/step_defs/`）
- [X] T002 建立 `requirements.txt`，包含依賴：fastapi, uvicorn, sqlmodel, psycopg2-binary, chromadb, google-genai, python-jose[cryptography], passlib[bcrypt], python-multipart, httpx, pytest, pytest-bdd, pytest-asyncio, pytest-cov
- [X] T003 [P] 建立 `app/core/config.py`，設定環境變數（DATABASE_URL, GEMINI_API_KEY, JWT_SECRET_KEY, JWT_EXPIRATION_DAYS, CHROMA_HOST, CHROMA_PORT）
- [X] T004 [P] 建立 `app/core/constants.py`，定義 VALID_CATEGORIES 清單（餐飲、日用品、交通、居住、娛樂、服飾、醫療、教育、工作、社交、寵物、其他）與 CategoryEnum
- [X] T005 [P] 建立 `app/core/logging.py`，設定結構化 JSON 日誌（user_id、endpoint、duration_ms、status 欄位）
- [X] T006 [P] 建立 `.env.example`，包含所有必要環境變數
- [X] T007 [P] 建立 `docker-compose.yml`，含 3 個服務：api（FastAPI）、db（PostgreSQL）、chromadb（ChromaDB）
- [X] T008 [P] 建立 `Dockerfile`，用於 FastAPI 應用程式

---

## 第 2 階段：基礎建設（阻塞性前置條件）

**目的**: 所有使用者故事實作前必須（MUST）完成的核心基礎設施

**⚠️ 關鍵**: 此階段未完成前，不可開始任何使用者故事

- [X] T009 建立 `app/database.py`，含 SQLModel engine、session 依賴注入、create_db_and_tables 函式
- [X] T010 建立 `app/main.py`，含 FastAPI 應用實例、lifespan 處理器（DB 初始化、ChromaDB 初始化）、`/health` 健康檢查端點、v1 路由掛載於 `/api/v1`
- [X] T011 [P] 建立 `app/models/user.py`，定義 User SQLModel（id、username、hashed_password、created_at）
- [X] T012 [P] 建立 `app/models/invoice.py`，定義 Invoice SQLModel（id、user_id FK、invoice_number、store_name、total_amount、date、category、raw_text、ai_raw_output、created_at）與 (user_id, invoice_number) 唯一約束
- [X] T013 [P] 建立 `app/models/invoice_item.py`，定義 InvoiceItem SQLModel（id、invoice_id FK 含串聯刪除、name、price、quantity）
- [X] T014 建立 `app/services/vector_store.py`，含 ChromaDB 客戶端初始化、add_items、delete_by_invoice、search 方法（所有操作以 user_id metadata 過濾）
- [X] T015 建立 `app/services/validators.py`，含 validate_invoice 函式（金額 >= 0、日期 <= 今天、店名非空、品項 >= 1、分類屬於 VALID_CATEGORIES）
- [X] T016 建立 `tests/conftest.py`，含共用 fixtures：測試用資料庫 session、測試用 FastAPI 客戶端（httpx AsyncClient）、測試使用者工廠、認證 token 工廠

**檢查點**: 基礎設施就緒 — 可開始實作使用者故事

---

## 第 3 階段：使用者故事 1 — 使用者註冊與登入（優先級：P1）🎯 MVP

**目標**: 使用者可註冊帳號並登入取得 JWT 權杖

**獨立測試**: 註冊帳號 → 登入 → 取得 token → 存取受保護端點

### 使用者故事 1 的測試 ⚠️

> **注意：必須先撰寫測試並確認失敗（Red），再進行實作**

- [X] T017 [P] [US1] 建立 BDD 功能檔 `tests/bdd/features/auth.feature`，場景：註冊成功、使用者名稱重複、登入成功、密碼錯誤、未帶 token 存取
- [X] T018 [P] [US1] 建立單元測試 `tests/unit/test_auth.py`，測試密碼雜湊、JWT 建立、JWT 驗證、過期 token 處理
- [X] T019 [P] [US1] 建立整合測試 `tests/integration/test_auth.py`，測試 POST /api/v1/auth/register（成功 + 重複）、POST /api/v1/auth/login（成功 + 密碼錯誤）、未帶 token 回傳 401

### 使用者故事 1 的實作

- [X] T020 [US1] 建立 `app/auth.py`，含 hash_password、verify_password（bcrypt）、create_access_token、decode_access_token（JWT HS256）、get_current_user 依賴注入
- [X] T021 [US1] 建立 `app/schemas/auth.py`，含 AuthRequest（username、password）、UserResponse（id、username、created_at）、TokenResponse（access_token、token_type）
- [X] T022 [US1] 建立 `app/api/v1/auth.py`，含 POST /register（建立使用者，回傳 201 或 409）與 POST /login（驗證憑證，回傳 token 或 401）
- [X] T023 [US1] 建立 BDD 步驟定義 `tests/bdd/step_defs/test_auth_steps.py`，實作 auth.feature 場景
- [X] T024 [US1] 執行所有 US1 測試並確認全部通過（Green）

**檢查點**: 使用者故事 1 完整可用，可獨立測試

---

## 第 4 階段：使用者故事 2 — 拍照上傳與 AI 發票解析（優先級：P1）

**目標**: 使用者上傳發票照片，AI 解析為結構化資料並回傳（不存入 DB）

**獨立測試**: 上傳圖片 → 收到含店名、日期、金額、品項、分類的 JSON 結果

### 使用者故事 2 的測試 ⚠️

> **注意：必須先撰寫測試並確認失敗（Red），再進行實作**

- [X] T025 [P] [US2] 建立 BDD 功能檔 `tests/bdd/features/invoice_parse.feature`，場景：解析成功、無效圖片、分類回退至「其他」、驗證錯誤（負數金額、未來日期）、解析後圖片未保留
- [X] T026 [P] [US2] 建立單元測試 `tests/unit/test_ai_parser.py`，測試解析回應驗證、分類正規化（未知 → 其他）、429/503 重試邏輯（mock Gemini）、結構化輸出解析
- [X] T027 [P] [US2] 建立單元測試 `tests/unit/test_validators.py`，測試 validate_invoice：有效發票通過、負數金額失敗、未來日期失敗、空店名失敗、無品項失敗、無效分類失敗
- [X] T028 [P] [US2] 建立整合測試 `tests/integration/test_invoices_parse.py`，測試 POST /api/v1/invoices/parse（有效圖片搭配 mock Gemini）、未帶認證回傳 401

### 使用者故事 2 的實作

- [X] T029 [US2] 建立 `app/schemas/invoice.py`，含 ParsedInvoice、ParsedItem、InvoiceCreate、ItemCreate、InvoiceUpdate、InvoiceResponse、InvoiceDetailResponse、ItemResponse、CalendarDay schema（category 欄位使用 CategoryEnum）
- [X] T030 [US2] 建立 `app/services/ai_parser.py`，含 parse_invoice 函式：接受圖片位元組、呼叫 Gemini 1.5 Flash（多模態 + JSON 結構化輸出）、指數退避重試（最多 3 次，1s→2s→4s，僅 429/5xx）、分類正規化至黃金 12 類（回退「其他」）、回傳 ParsedInvoice。圖片位元組不得（MUST NOT）被儲存。
- [X] T031 [US2] 建立 `app/api/v1/invoices.py`，含 POST /parse 端點：接受 multipart 檔案上傳、呼叫 ai_parser.parse_invoice、執行 validators.validate_invoice、回傳 ParsedInvoice（含 validation_errors）、Gemini 不可用時回傳 503
- [X] T032 [US2] 建立 BDD 步驟定義 `tests/bdd/step_defs/test_invoice_parse_steps.py`，實作 invoice_parse.feature 場景
- [X] T033 [US2] 執行所有 US2 測試並確認全部通過（Green）

**檢查點**: 使用者故事 2 完整可用，可獨立測試

---

## 第 5 階段：使用者故事 3 — 發票確認儲存與管理（優先級：P1）

**目標**: 使用者確認解析結果後儲存，並可瀏覽、編輯、刪除發票

**獨立測試**: 儲存發票 → 列表查詢 → 單筆查詢 → 修改 → 刪除，每步驗證資料正確

### 使用者故事 3 的測試 ⚠️

> **注意：必須先撰寫測試並確認失敗（Red），再進行實作**

- [X] T034 [P] [US3] 建立 BDD 功能檔 `tests/bdd/features/invoice_crud.feature`，場景：儲存發票含品項、發票號碼重複提醒、日期篩選列表查詢、取得發票明細、更新發票、刪除發票同步移除品項與向量、使用者隔離（使用者 A 無法看見使用者 B 資料）
- [X] T035 [P] [US3] 建立整合測試 `tests/integration/test_invoices.py`，測試所有 CRUD 端點：POST /invoices（201 + 409 重複）、GET /invoices（含日期篩選）、GET /invoices/{id}（200 + 404）、PUT /invoices/{id}、DELETE /invoices/{id}（204 + 驗證串聯刪除）、跨使用者隔離

### 使用者故事 3 的實作

- [X] T036 [US3] 在 `app/api/v1/invoices.py` 新增 CRUD 端點：POST /（儲存已確認發票 + 建立向量、以 invoice_number 偵測重複，號碼為空時回退至「店名+金額+日期」比對）、GET /（列表含 start_date/end_date 篩選，user_id 限定）、GET /{id}（明細含品項，user_id 限定）、PUT /{id}（更新 + 重建向量）、DELETE /{id}（串聯刪除品項 + 向量）
- [X] T037 [US3] 更新 `app/services/vector_store.py`，整合發票 CRUD：建立時 → 為每個 InvoiceItem 呼叫 add_items、更新時 → delete_by_invoice + add_items、刪除時 → delete_by_invoice
- [X] T038 [US3] 建立 BDD 步驟定義 `tests/bdd/step_defs/test_invoice_crud_steps.py`，實作 invoice_crud.feature 場景
- [X] T039 [US3] 執行所有 US3 測試並確認全部通過（Green）

**檢查點**: 使用者故事 1、2、3 皆獨立可用 — 核心 MVP 完成

---

## 第 6 階段：使用者故事 4 — 行事曆摘要查詢（優先級：P2）

**目標**: 使用者查詢月份摘要，取得每日發票筆數與總額

**獨立測試**: 儲存多日發票 → 查詢月份摘要 → 驗證每日筆數與金額正確

### 使用者故事 4 的測試 ⚠️

- [X] T040 [P] [US4] 建立整合測試 `tests/integration/test_calendar.py`，測試 GET /api/v1/invoices/calendar：回傳每日筆數與總金額、遵守 user_id 過濾、空月份回傳空陣列

### 使用者故事 4 的實作

- [X] T041 [US4] 在 `app/api/v1/invoices.py` 新增行事曆端點：GET /calendar，接受 year 與 month 查詢參數，回傳 CalendarDay 陣列（date、count、total_amount），依日期分組，user_id 限定
- [X] T042 [US4] 執行所有 US4 測試並確認全部通過（Green）

**檢查點**: 使用者故事 4 獨立可用

---

## 第 7 階段：使用者故事 5 — RAG 語義對話查詢（優先級：P2）

**目標**: 使用者以自然語言提問，系統結合 SQL 精確查詢與語義檢索回答

**獨立測試**: 儲存發票 → 問「這個月花了多少？」→ 驗證金額正確；問「上次買咖啡在哪？」→ 驗證語義結果相關

### 使用者故事 5 的測試 ⚠️

- [X] T043 [P] [US5] 建立 BDD 功能檔 `tests/bdd/features/chat.feature`，場景：聚合查詢（月花費）、語義搜尋（上次買咖啡）、多輪對話（追問）、使用者隔離、回覆使用繁體中文
- [X] T044 [P] [US5] 建立單元測試 `tests/unit/test_rag_service.py`，測試工具函式定義、query_database 回傳正確聚合結果（mock DB）、search_invoices 回傳相關結果（mock ChromaDB）、對話歷史截斷至 5 輪
- [X] T045 [P] [US5] 建立整合測試 `tests/integration/test_chat.py`，測試 POST /api/v1/chat：有效查詢回傳答案 + 來源、未帶認證回傳 401、使用者隔離（使用者 A 查詢僅看見使用者 A 資料）

### 使用者故事 5 的實作

- [X] T046 [US5] 建立 `app/schemas/chat.py`，含 ChatRequest（message、conversation_history）、ChatMessage（role、content）、ChatResponse（answer、sources）
- [X] T047 [US5] 建立 `app/services/rag_service.py`，定義 4 個 Gemini Function Calling 工具（query_database、search_invoices、get_spending_summary、get_category_breakdown），各工具函式以 user_id 限定範圍，handle_chat 方法傳送訊息 + 歷史（最多 5 輪）至 Gemini，執行工具呼叫，回傳繁體中文最終回答。非消費查詢需禮貌引導回消費主題。
- [X] T048 [US5] 建立 `app/api/v1/chat.py`，含 POST / 端點：接受 ChatRequest，呼叫 rag_service.handle_chat（傳入 current_user.id），回傳 ChatResponse
- [X] T049 [US5] 建立 BDD 步驟定義 `tests/bdd/step_defs/test_chat_steps.py`，實作 chat.feature 場景
- [X] T050 [US5] 執行所有 US5 測試並確認全部通過（Green）

**檢查點**: 所有使用者故事皆獨立可用

---

## 第 8 階段：收尾與跨功能優化

**目的**: 影響多個使用者故事的改善項目

- [X] T051 [P] 在 `app/services/` 所有服務方法中加入結構化日誌呼叫（ai_parser、rag_service、vector_store），使用 `app/core/logging.py`
- [X] T052 [P] 建立 `app/api/v1/__init__.py` 路由聚合，驗證所有路由掛載於 `/api/v1/` 下
- [X] T053 [P] 執行完整測試套件含覆蓋率：`pytest --cov=app --cov-report=term-missing`，驗證關鍵路徑（認證、解析、對話）覆蓋率達 80% 以上
- [X] T054 驗證憲法合規：確認無圖片持久化、所有查詢含 user_id 過濾、所有分類驗證使用黃金 12 類、所有端點在 /api/v1 下

---

## 依賴關係與執行順序

### 階段依賴

- **初始化（第 1 階段）**: 無依賴 — 可立即開始
- **基礎建設（第 2 階段）**: 依賴初始化完成 — 阻塞所有使用者故事
- **US1（第 3 階段）**: 依賴基礎建設 — 不依賴其他故事
- **US2（第 4 階段）**: 依賴基礎建設 — 不依賴其他故事
- **US3（第 5 階段）**: 依賴基礎建設 + US2 的 schema（T029）
- **US4（第 6 階段）**: 依賴 US3（需要 DB 中的發票資料）
- **US5（第 7 階段）**: 依賴 US3（需要發票資料 + ChromaDB 中的向量）
- **收尾（第 8 階段）**: 依賴所有使用者故事完成

### 使用者故事依賴

- **US1（P1）**: 基礎建設後獨立
- **US2（P1）**: 基礎建設後獨立
- **US3（P1）**: 依賴 US2 的 schema；若 schema 共享則可平行開始
- **US4（P2）**: 依賴 US3（發票 CRUD 必須存在）
- **US5（P2）**: 依賴 US3（發票資料 + 向量儲存必須存在）

### 各使用者故事內部順序

- 測試必須（MUST）先撰寫並確認失敗（TDD Red 階段）
- Model/Schema 先於 Service
- Service 先於端點
- BDD 步驟定義在端點實作之後
- 所有實作完成後執行 Green 驗證

### 平行執行機會

- T003、T004、T005、T006、T007、T008（初始化階段）可平行執行
- T011、T012、T013（所有 Model）可平行執行
- T017、T018、T019（US1 測試）可平行執行
- T025、T026、T027、T028（US2 測試）可平行執行
- T034、T035（US3 測試）可平行執行
- T043、T044、T045（US5 測試）可平行執行
- US1 與 US2 可在基礎建設完成後平行開發

---

## 實作策略

### MVP 優先（使用者故事 1-3）

1. 完成第 1 階段：初始化
2. 完成第 2 階段：基礎建設（關鍵 — 阻塞所有故事）
3. 完成第 3 階段：US1 — 認證 → 獨立測試
4. 完成第 4 階段：US2 — AI 解析 → 獨立測試
5. 完成第 5 階段：US3 — 發票 CRUD → 獨立測試
6. **暫停並驗證**: 核心 MVP（認證 + 解析 + CRUD）完整可用

### 漸進式交付

7. 加入第 6 階段：US4 — 行事曆 → 獨立測試
8. 加入第 7 階段：US5 — RAG 對話 → 獨立測試
9. 完成第 8 階段：收尾 → 完整測試套件通過，覆蓋率驗證

---

## 備註

- [P] 任務 = 不同檔案、無依賴
- [故事] 標籤對應特定使用者故事
- 憲法原則 VI 要求 TDD+BDD：所有測試任務必須（MUST）先執行並確認失敗
- 憲法原則 I：所有分類驗證使用 constants.py 中的 CategoryEnum
- 憲法原則 II：T030 與 T031 不得（MUST NOT）持久化圖片位元組
- 每個任務或邏輯群組完成後提交 commit
- 可在任何檢查點暫停，獨立驗證該故事
