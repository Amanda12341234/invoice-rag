# 資料模型：AI 智能發票管家後端

**日期**: 2026-02-10
**分支**: `001-invoice-rag-backend`

## 實體

### 使用者 (User)

| 欄位 | 型態 | 約束 | 說明 |
|------|------|------|------|
| id | Integer | 主鍵, 自動遞增 | 主鍵 |
| username | String(50) | 唯一, 非空, 索引 | 使用者名稱 |
| hashed_password | String(255) | 非空 | bcrypt 雜湊密碼 |
| created_at | DateTime | 非空, 預設=現在 | 建立時間 |

**驗證規則**:
- username：1-50 字元，英數字與底線
- password（輸入）：最少 6 字元

### 發票 (Invoice)

| 欄位 | 型態 | 約束 | 說明 |
|------|------|------|------|
| id | Integer | 主鍵, 自動遞增 | 主鍵 |
| user_id | Integer | 外鍵(User.id), 非空, 索引 | 所屬使用者 |
| invoice_number | String(20) | 可空, 索引 | 發票號碼 |
| store_name | String(100) | 非空 | 店家名稱 |
| total_amount | Float | 非空, >= 0 | 總金額 |
| date | Date | 非空, <= 今天 | 消費日期 |
| category | String(10) | 非空, 屬於黃金12類 | 分類 |
| raw_text | Text | 可空 | 原始 OCR 內容 |
| ai_raw_output | JSON | 可空 | AI 原始解析結果 |
| created_at | DateTime | 非空, 預設=現在 | 建立時間 |

**唯一約束**: (user_id, invoice_number) — 同一使用者下發票號碼唯一（invoice_number 非空時生效）

**驗證規則**:
- total_amount >= 0
- date <= 今天
- store_name 非空
- category 必須屬於：餐飲、日用品、交通、居住、娛樂、服飾、醫療、教育、工作、社交、寵物、其他

### 品項 (InvoiceItem)

| 欄位 | 型態 | 約束 | 說明 |
|------|------|------|------|
| id | Integer | 主鍵, 自動遞增 | 主鍵 |
| invoice_id | Integer | 外鍵(Invoice.id), 非空, 串聯刪除 | 所屬發票 |
| name | String(100) | 非空 | 品項名稱 |
| price | Float | 非空, >= 0 | 品項單價 |
| quantity | Integer | 非空, 預設=1, >= 1 | 數量 |

**驗證規則**:
- 每張發票至少 1 個品項
- price >= 0
- quantity >= 1

## 關聯關係

```text
使用者 (1) ──< 發票 (N)      # 一個使用者擁有多張發票
發票 (1) ──< 品項 (N)        # 一張發票包含多個品項
```

## 向量儲存（ChromaDB）

非關聯式，不在 SQLModel 中定義。以 Collection 形式儲存：

**Collection**: `invoice_items`

| 欄位 | 說明 |
|------|------|
| id | `item_{InvoiceItem.id}` |
| document | `"{date} 在{store_name}購買{item_name} ${price} ({category})"` |
| embedding | Gemini Embedding 向量 |
| metadata.user_id | 使用者 ID（查詢過濾用） |
| metadata.invoice_id | 發票 ID |
| metadata.item_id | 品項 ID |
| metadata.date | 消費日期（ISO 字串） |
| metadata.category | 分類 |

**生命週期同步**:
- 發票建立 → 為每個品項建立向量
- 發票修改 → 刪除舊向量 + 建立新向量
- 發票刪除 → 刪除對應所有品項向量
