import chromadb

from app.core.config import settings


class VectorStore:
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST, port=settings.CHROMA_PORT
        )
        self.collection = self.client.get_or_create_collection("invoice_items")

    def add_items(
        self,
        items: list[dict],
        user_id: int,
        invoice_id: int,
        store_name: str,
        invoice_date: str,
        category: str,
    ):
        if not items:
            return
        ids = [f"item_{item['id']}" for item in items]
        documents = [
            f"{invoice_date} 在{store_name}購買{item['name']} ${item['price']} ({category})"
            for item in items
        ]
        metadatas = [
            {
                "user_id": user_id,
                "invoice_id": invoice_id,
                "item_id": item["id"],
                "date": invoice_date,
                "category": category,
            }
            for item in items
        ]
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def delete_by_invoice(self, invoice_id: int):
        self.collection.delete(where={"invoice_id": invoice_id})

    def search(self, query: str, user_id: int, n_results: int = 10) -> list[dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"user_id": user_id},
        )
        items = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                items.append({"document": doc, "metadata": metadata})
        return items


vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store


def init_vector_store():
    global vector_store
    try:
        vector_store = VectorStore()
    except Exception:
        vector_store = None
