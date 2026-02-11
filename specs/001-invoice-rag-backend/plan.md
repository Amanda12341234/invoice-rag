# 實作計畫：AI 智能發票管家後端

**分支**: `001-invoice-rag-backend` | **日期**: 2026-02-10 | **規格**: [spec.md](./spec.md)
**輸入**: 功能規格來自 `/specs/001-invoice-rag-backend/spec.md`

## 摘要

建構 AI 智能發票管家的 FastAPI 後端，提供使用者認證、發票圖片 AI 解析（Gemini 1.5 Flash）、發票 CRUD、ChromaDB 向量儲存，以及 RAG 語義對話查詢功能。系統嚴格遵守黃金 12 類分類、圖片即用即刪、API `/api/v1` 路由規範。

## 技術上下文

**語言/版本**: Python 3.11+
**主要依賴**: FastAPI, SQLModel, ChromaDB, google-genai, python-jose (JWT), bcrypt, python-multipart
**儲存**: PostgreSQL (SQLModel ORM) + ChromaDB (向量儲存)
**測試**: pytest + pytest-bdd + httpx (AsyncClient)
**目標平台**: Linux Docker 容器（自架或 Oracle Cloud Always Free）
**專案類型**: 單一專案（後端 API only，前端 Flutter 獨立開發）
**效能目標**: 單筆發票解析 < 15 秒；一般端點 < 5 秒回應
**限制**: 月 AI 成本 < NT$200；Gemini 免費額度為主；個位數使用者
**規模/範圍**: MVP 個人使用，< 10 使用者，< 10,000 筆發票

## 憲法檢查

*關卡：必須在第 0 階段研究前通過。第 1 階段設計完成後重新檢查。*

| # | 原則 | 狀態 | 說明 |
|---|------|------|------|
| I | 黃金 12 類分類制度 | ✅ 通過 | FR-006 明確限定 12 類；Pydantic Enum 驗證 |
| II | 圖片即用即刪 | ✅ 通過 | FR-007 明確要求解析後丟棄；圖片僅在記憶體中處理 |
| III | API 路由規範 | ✅ 通過 | 所有端點設計於 `/api/v1/` 下 |
| IV | 資料隔離 | ✅ 通過 | FR-015 所有查詢含 user_id 過濾 |
| V | 簡潔與 YAGNI | ✅ 通過 | 僅實作 MVP 範圍功能，無多餘抽象 |
| VI | TDD + BDD | ✅ 通過 | 使用 pytest + pytest-bdd，測試先行 |

## 專案結構

### 文件（本功能）

```text
specs/001-invoice-rag-backend/
├── plan.md              # 本檔案
├── research.md          # 第 0 階段產出
├── data-model.md        # 第 1 階段產出
├── quickstart.md        # 第 1 階段產出
├── contracts/           # 第 1 階段產出（OpenAPI）
└── tasks.md             # 第 2 階段產出（/speckit.tasks）
```

### 原始碼（專案根目錄）

```text
app/
├── main.py               # FastAPI 入口與生命週期管理
├── database.py           # SQLModel Engine 與 Session 設定
├── auth.py               # JWT 建立與驗證邏輯
├── models/               # SQLModel 資料模型
│   ├── user.py
│   ├── invoice.py
│   └── invoice_item.py
├── schemas/              # Pydantic 請求/回應模型
│   ├── auth.py
│   ├── invoice.py
│   └── chat.py
├── api/                  # API 路由 (v1)
│   └── v1/
│       ├── auth.py
│       ├── invoices.py
│       └── chat.py
├── services/             # 業務邏輯層
│   ├── ai_parser.py      # Gemini 發票解析
│   ├── rag_service.py    # RAG 檢索與 Function Calling
│   ├── vector_store.py   # ChromaDB 操作
│   └── validators.py     # 後端資料驗證
└── core/
    ├── config.py          # 環境變數設定
    ├── constants.py       # 黃金 12 類等常數
    └── logging.py         # 結構化日誌設定

tests/
├── conftest.py           # 共用 fixtures
├── bdd/
│   ├── features/         # .feature 檔案（Given-When-Then）
│   └── step_defs/        # 步驟定義
├── integration/
│   ├── test_auth.py
│   ├── test_invoices.py
│   └── test_chat.py
└── unit/
    ├── test_validators.py
    ├── test_ai_parser.py
    └── test_vector_store.py
```

**結構決策**: 採用 PRD 定義的單一後端專案結構，符合憲法原則 V（簡潔）。`app/` 為應用程式碼，`tests/` 含 BDD features、整合測試與單元測試。

## 複雜度追蹤

> 無違反項目，無需記錄。
