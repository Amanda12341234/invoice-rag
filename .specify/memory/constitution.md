<!--
  === 同步影響報告 ===
  版本變更: 1.0.0 → 1.1.0
  修改原則: 無
  新增原則: VI. 測試驅動開發（TDD + BDD）
  新增區段: 無
  移除區段: 無
  範本更新狀態:
    - .specify/templates/plan-template.md ✅ 無需變更（Constitution Check 為通用欄位）
    - .specify/templates/spec-template.md ✅ 無需變更（已包含驗收場景區段）
    - .specify/templates/tasks-template.md ✅ 無需變更（已包含測試先行指引）
  延後項目: 無
-->

# AI 智能發票管家 後端憲法

## Core Principles

### I. 黃金 12 類分類制度（不可違反）

所有發票分類必須（MUST）嚴格使用以下 12 個固定分類，不得新增、刪除或重新命名。
變更分類清單需透過憲法修正程序。

固定分類清單：
- 餐飲、日用品、交通、居住、娛樂、服飾
- 醫療、教育、工作、社交、寵物、其他

規則：
- AI 解析輸出的 `category` 欄位必須（MUST）從上述清單中選擇
- 資料庫 `Invoice.category` 欄位必須（MUST）在 API 驗證層檢查是否屬於此清單
- 前端分類選擇器必須（MUST）僅顯示這 12 個選項
- 任何不在清單內的分類值必須（MUST）被 API 驗證層拒絕並回傳錯誤

### II. 圖片即用即刪原則（不可違反）

上傳的發票圖片在 AI 解析完成後必須（MUST）立即銷毀，
系統僅保留結構化資料與 `raw_text`。

規則：
- 圖片資料僅可（MUST）在解析請求的生命週期內存在於記憶體或暫存區
- Gemini 回傳解析結果後，圖片必須（MUST）立即丟棄
- 任何端點、服務或背景任務皆不得（MUST NOT）將原始圖片位元組寫入磁碟或資料庫
- `ai_raw_output` JSON 欄位保留 AI 回應結果，而非圖片本身
- 日誌系統不得（MUST NOT）記錄圖片的 Base64 編碼或二進位內容

### III. API 路由規範

所有 API 端點必須（MUST）定義在 `/api/v1` 前綴之下。

規則：
- 每個 Router 必須（MUST）掛載於 `/api/v1/` 路徑下
- 除健康檢查端點（`/health`、`/readiness`）外，不得（MUST NOT）在根路徑 `/` 或版本前綴外定義任何端點
- 需要破壞性變更時，必須（MUST）透過憲法修正程序引入新版本前綴（如 `/api/v2`）
- MVP 期間：v1 必須（MUST）維持向後相容，不得進行破壞性變更

### IV. 資料隔離（多租戶安全）

所有資料存取必須（MUST）限定於已驗證的使用者範圍內。

規則：
- 每個涉及使用者資料的資料庫查詢必須（MUST）包含 `user_id` 過濾條件
- ChromaDB 向量搜尋必須（MUST）在 metadata 中以 `user_id` 進行過濾
- RAG 工具中的 SQL 聚合查詢必須（MUST）強制執行 `user_id` 範圍限制
- 任何 API 端點不得（MUST NOT）回傳屬於其他使用者的資料

### V. 簡潔與 YAGNI 原則

程式碼必須（MUST）保持精簡且目的明確。

規則：
- 僅實作當前 MVP 範圍內定義的功能
- 除非已有兩個以上具體使用場景，否則不得（MUST NOT）建立抽象層
- 優先使用直接的 SQLModel 查詢，避免 Repository 模式
- 組態設定必須（MUST）透過環境變數與單一 `config.py` 管理
- 新增依賴套件必須（MUST）於 PR 說明中附上理由

### VI. 測試驅動開發（TDD + BDD）（不可違反）

所有功能開發必須（MUST）遵循測試先行的紀律，結合 TDD 與 BDD 方法論。

**TDD 流程（Red-Green-Refactor）：**
- 實作任何功能前，必須（MUST）先撰寫對應的單元測試
- 測試必須（MUST）先執行並確認失敗（Red），再進行實作使其通過（Green）
- 通過後可進行重構（Refactor），但必須（MUST）確保測試持續通過
- 每個 service 函式與驗證邏輯必須（MUST）有對應的單元測試

**BDD 流程（行為驅動）：**
- 每個 API 端點必須（MUST）撰寫行為驗收測試，使用 Given-When-Then 格式描述場景
- 驗收測試必須（MUST）涵蓋正常路徑與主要錯誤路徑
- 使用者故事（User Story）的驗收條件必須（MUST）可直接對應至可執行的測試案例
- 測試場景描述必須（MUST）使用業務語言，而非技術實作細節

**通用規則：**
- 測試框架使用 `pytest`，BDD 場景使用 `pytest-bdd` 或等效工具
- 不得（MUST NOT）在測試未通過的狀態下合併程式碼
- 測試覆蓋率目標：關鍵路徑（解析、對話、認證）必須（MUST）達到 80% 以上
- 每個 PR 必須（MUST）包含對應的測試變更，無測試的功能 PR 不得合併

## 技術約束

- **程式語言**：Python 3.11+
- **框架**：FastAPI（支援非同步）
- **ORM**：SQLModel（SQLAlchemy + Pydantic）
- **資料庫**：PostgreSQL
- **向量資料庫**：ChromaDB（Docker volume + PostgreSQL 同步備份）
- **AI 模型**：Gemini 1.5 Flash（OCR、Embedding、RAG 推理、Function Calling）
- **認證**：JWT（密碼使用 bcrypt 雜湊）
- **容器化**：Docker Compose（API + PostgreSQL + ChromaDB）
- **測試框架**：pytest + pytest-bdd（或等效 BDD 工具）

新增核心依賴必須（MUST）在 PR 描述中說明理由。

## 開發工作流程

- **Contract-First**：利用 FastAPI 自動產生 OpenAPI Spec，前後端依據 Spec 獨立開發
- **Test-First**：所有功能實作前必須（MUST）先有失敗的測試（TDD Red 階段）
- **輸入驗證**：所有使用者輸入必須（MUST）在 API 邊界使用 Pydantic 模型驗證；內部服務呼叫可信任已驗證的資料
- **錯誤處理**：使用 FastAPI `HTTPException` 搭配適當的 HTTP 狀態碼；不得（MUST NOT）靜默吞掉例外
- **日誌記錄**：使用 Python `logging` 模組，包含結構化上下文（user_id、endpoint、duration）以利除錯

## Governance

- 本憲法優先於所有臨時做法與口頭約定
- 修正必須（MUST）更新本文件、遞增版本號，並在頂部的同步影響報告中記錄變更
- 所有 PR 必須（MUST）驗證是否符合 6 項核心原則
- 若違反任何原則，必須（MUST）在 PR 中記錄違反原因並取得明確核准
- 超出原則允許範圍的複雜度必須（MUST）以書面形式說明理由
- 版本號遵循語意化版本規則：MAJOR（原則移除或重新定義）、MINOR（新增原則或擴充）、PATCH（措辭修正）

**Version**: 1.1.0 | **Ratified**: 2026-02-10 | **Last Amended**: 2026-02-10
