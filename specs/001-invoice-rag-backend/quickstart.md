# 快速開始：AI 智能發票管家後端

## 前置需求

- Python 3.11+
- Docker & Docker Compose
- Gemini API Key（取得方式：https://ai.google.dev/）

## 環境設定

1. 複製環境變數檔案：

```bash
cp .env.example .env
```

2. 編輯 `.env`，填入必要設定：

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/invoice_rag
GEMINI_API_KEY=your-gemini-api-key
JWT_SECRET_KEY=your-random-secret-key
JWT_EXPIRATION_DAYS=7
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

## 啟動服務

### Docker Compose（推薦）

```bash
docker-compose up -d
```

啟動 3 個容器：API server、PostgreSQL、ChromaDB。

### 本地開發

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動 PostgreSQL + ChromaDB（僅基礎設施）
docker-compose up -d db chromadb

# 執行資料庫遷移
python -m app.database

# 啟動 API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 驗證啟動

```bash
# 健康檢查
curl http://localhost:8000/health

# 查看 API 文件
open http://localhost:8000/docs
```

## 執行測試

```bash
# 全部測試
pytest

# 僅單元測試
pytest tests/unit/

# 僅 BDD 測試
pytest tests/bdd/

# 僅整合測試（需啟動 DB + ChromaDB）
pytest tests/integration/

# 含覆蓋率
pytest --cov=app --cov-report=term-missing
```

## 快速體驗

```bash
# 1. 註冊
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'

# 2. 登入取得 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}' | jq -r '.access_token')

# 3. 上傳發票解析
curl -X POST http://localhost:8000/api/v1/invoices/parse \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invoice.jpg"

# 4. 對話查詢
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "這個月花了多少錢？"}'
```
