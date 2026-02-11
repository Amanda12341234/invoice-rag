from datetime import date

from app.core.logging import logger
from google import genai
from google.genai import types
from sqlalchemy import func, extract
from sqlmodel import Session, select

from app.core.config import settings
from app.models.invoice import Invoice
from app.services.vector_store import VectorStore

TOOL_DEFINITIONS = [
    {
        "name": "query_database",
        "description": "查詢指定期間的發票聚合資料（總金額、筆數）",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期間，格式 YYYY-MM 或 YYYY"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "search_invoices",
        "description": "語義搜尋發票品項，例如「咖啡」「晚餐」",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜尋關鍵字"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_spending_summary",
        "description": "取得指定期間的花費摘要",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期間 YYYY-MM"},
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_category_breakdown",
        "description": "取得指定期間各分類的花費統計",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "期間 YYYY-MM"},
            },
            "required": ["period"],
        },
    },
]


def query_database(session: Session, user_id: int, period: str) -> dict:
    query = select(
        func.count(Invoice.id).label("count"),
        func.coalesce(func.sum(Invoice.total_amount), 0).label("total"),
    ).where(Invoice.user_id == user_id)

    parts = period.split("-")
    if len(parts) >= 2:
        query = query.where(extract("year", Invoice.date) == int(parts[0]))
        query = query.where(extract("month", Invoice.date) == int(parts[1]))
    elif len(parts) == 1:
        query = query.where(extract("year", Invoice.date) == int(parts[0]))

    result = session.exec(query).first()
    return {"count": result[0], "total": float(result[1])}


def search_invoices(vector_store: VectorStore, user_id: int, query: str) -> list[dict]:
    return vector_store.search(query=query, user_id=user_id, n_results=5)


def get_spending_summary(session: Session, user_id: int, period: str) -> dict:
    return query_database(session, user_id, period)


def get_category_breakdown(session: Session, user_id: int, period: str) -> list[dict]:
    query = select(
        Invoice.category,
        func.count(Invoice.id).label("count"),
        func.sum(Invoice.total_amount).label("total"),
    ).where(Invoice.user_id == user_id)

    parts = period.split("-")
    if len(parts) >= 2:
        query = query.where(extract("year", Invoice.date) == int(parts[0]))
        query = query.where(extract("month", Invoice.date) == int(parts[1]))

    query = query.group_by(Invoice.category)
    results = session.exec(query).all()
    return [{"category": r[0], "count": r[1], "total": float(r[2])} for r in results]


def truncate_history(history: list[dict], max_turns: int = 5) -> list[dict]:
    max_messages = max_turns * 2
    if len(history) <= max_messages:
        return history
    return history[-max_messages:]


SYSTEM_PROMPT = """你是 AI 智能發票管家的對話助手。請使用繁體中文回答。
你可以使用提供的工具來查詢使用者的消費記錄。
如果使用者的問題與消費、發票、記帳無關，請禮貌地引導回消費相關主題。
回答時請簡潔明瞭，附上相關的數據。"""


async def handle_chat(
    session: Session,
    vector_store: VectorStore,
    user_id: int,
    message: str,
    conversation_history: list[dict] | None = None,
) -> dict:
    logger.info("Chat request", extra={"user_id": user_id, "status": "started"})
    history = truncate_history(conversation_history or [])

    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=t["parameters"],
                )
                for t in TOOL_DEFINITIONS
            ]
        )
    ]

    contents = [types.Content(parts=[types.Part.from_text(text=SYSTEM_PROMPT)], role="user")]
    for msg in history:
        contents.append(
            types.Content(parts=[types.Part.from_text(text=msg["content"])], role=msg["role"])
        )
    contents.append(types.Content(parts=[types.Part.from_text(text=message)], role="user"))

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=types.GenerateContentConfig(tools=tools),
    )

    sources = []

    # Process function calls
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.function_call:
                fc = part.function_call
                args = dict(fc.args) if fc.args else {}

                if fc.name == "query_database":
                    result = query_database(session, user_id, args.get("period", ""))
                elif fc.name == "search_invoices":
                    result = search_invoices(vector_store, user_id, args.get("query", ""))
                    for item in result:
                        meta = item.get("metadata", {})
                        sources.append({
                            "invoice_id": meta.get("invoice_id"),
                            "store_name": None,
                            "date": meta.get("date"),
                            "relevance": item.get("document"),
                        })
                elif fc.name == "get_spending_summary":
                    result = get_spending_summary(session, user_id, args.get("period", ""))
                elif fc.name == "get_category_breakdown":
                    result = get_category_breakdown(session, user_id, args.get("period", ""))
                else:
                    result = {"error": "Unknown function"}

                # Send function result back
                contents.append(response.candidates[0].content)
                contents.append(
                    types.Content(
                        parts=[types.Part.from_function_response(name=fc.name, response={"result": result})],
                        role="user",
                    )
                )

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(tools=tools),
                )

    answer = ""
    if response.candidates and response.candidates[0].content.parts:
        answer = "".join(
            part.text for part in response.candidates[0].content.parts if part.text
        )

    return {"answer": answer or "抱歉，我無法回答這個問題。", "sources": sources}
