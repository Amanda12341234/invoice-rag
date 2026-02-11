# 技術研究：AI 智能發票管家後端

**日期**: 2026-02-10
**分支**: `001-invoice-rag-backend`

## R1: Gemini 1.5 Flash — 發票 OCR + 分類整合

**決策**: 使用 Gemini 1.5 Flash 的多模態能力，將 OCR 與分類合併為單次 API 呼叫。透過 structured output（JSON mode）確保回傳格式一致。

**理由**: 單次呼叫減少延遲與成本；Gemini 1.5 Flash 支援圖片輸入與 JSON 結構化輸出；免費額度充足供 MVP 使用。

**替代方案**:
- 分離 OCR（Google Vision API）+ 分類（Gemini text）：兩次 API 呼叫，成本與延遲加倍
- 本地 OCR（Tesseract）+ Gemini 分類：繁體中文 OCR 品質不穩定

## R2: ChromaDB 向量儲存策略

**決策**: 每個 InvoiceItem 獨立生成一個向量，文字格式為 `"{date} 在{store_name}購買{item_name} ${price} ({category})"`。使用 ChromaDB Python client 直連，Docker volume 持久化。

**理由**: 品項粒度的向量可支援「上次買咖啡在哪？」類型的精確語義搜尋；ChromaDB 輕量易部署，適合 MVP 規模。

**替代方案**:
- 發票粒度向量：搜尋精度不足，無法區分同一張發票的不同品項
- Pinecone / Weaviate：過度設計，增加外部依賴與成本

## R3: RAG 查詢路由 — Gemini Function Calling

**決策**: 使用 Gemini Function Calling 作為意圖路由，定義 4 個工具函式：`query_database`（SQL 聚合）、`search_invoices`（語義檢索）、`get_spending_summary`（時段摘要）、`get_category_breakdown`（分類統計）。

**理由**: LLM 自行判斷使用哪些工具，避免手動意圖分類的維護成本；Function Calling 回傳結構化的函式呼叫，後端執行後將結果交回 LLM 彙整回答。

**替代方案**:
- 關鍵字路由：無法處理自然語言的多樣性
- LangChain Agent：增加額外依賴，Gemini 原生 Function Calling 已足夠

## R4: JWT 認證策略

**決策**: 使用 python-jose 產生 HS256 JWT，有效期 7 天，存放 user_id 於 payload。密碼使用 bcrypt 雜湊（passlib[bcrypt]）。

**理由**: MVP 簡單方案，7 天長效期減少使用者重新登入的頻率；HS256 效能好、實作簡單。v1.1 再考慮 refresh token。

**替代方案**:
- RS256：需管理金鑰對，MVP 不需要
- Session-based auth：需額外 session store，增加複雜度

## R5: 指數退避重試策略

**決策**: AI 服務呼叫包裝重試邏輯：最多 3 次，初始等待 1 秒，每次倍增（1s → 2s → 4s）。僅對 429 與 5xx 錯誤重試。

**理由**: Gemini 免費額度有 rate limit，指數退避為業界標準做法；3 次重試在 15 秒解析時間預算內可接受（最差情況 1+2+4=7 秒用於重試）。

**替代方案**:
- tenacity 套件：功能豐富但 MVP 自製簡單裝飾器即可
- 無重試：rate limit 頻繁時使用者體驗差

## R6: 結構化日誌

**決策**: 使用 Python 標準 `logging` 模組，JSON 格式輸出，每筆日誌包含 `user_id`、`endpoint`、`duration_ms`、`status`。關鍵操作：解析、儲存、對話、認證失敗。

**理由**: 標準庫無額外依賴；JSON 格式便於未來接入日誌收集系統；符合憲法開發工作流程要求。

**替代方案**:
- structlog：功能更豐富但增加依賴
- loguru：非標準庫，與 uvicorn 整合需額外設定
