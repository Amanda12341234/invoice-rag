import asyncio
import json

from app.core.logging import logger
from google import genai
from google.genai import errors as genai_errors, types

from app.core.config import settings
from app.core.constants import VALID_CATEGORIES

PARSE_PROMPT = """你是一個發票解析助手。請分析這張發票圖片，回傳 JSON 格式：
{
  "invoice_number": "發票號碼（若無則 null）",
  "store_name": "店家名稱",
  "date": "YYYY-MM-DD",
  "total_amount": 數字,
  "items": [{"name": "品名", "price": 數字, "quantity": 數量}],
  "category": "分類（餐飲/日用品/交通/居住/娛樂/服飾/醫療/教育/工作/社交/寵物/其他）",
  "raw_text": "原始 OCR 文字"
}
僅回傳 JSON，不要其他文字。"""


def normalize_category(category: str | None) -> str:
    if category and category in VALID_CATEGORIES:
        return category
    return "其他"


async def parse_invoice(image_bytes: bytes) -> dict:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                            types.Part.from_text(text=PARSE_PROMPT),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(text)
            result["category"] = normalize_category(result.get("category"))
            logger.info("Invoice parsed successfully", extra={"status": "success"})
            return result
        except (genai_errors.ClientError, genai_errors.ServerError) as e:
            status_code = getattr(e, "code", None) or getattr(getattr(e, "response", None), "status_code", None)
            if status_code in (429, 500, 502, 503) and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
                continue
            raise
    raise RuntimeError("Max retries exceeded")
