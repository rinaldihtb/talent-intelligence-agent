import ast
from .config import DB, TOP_K, VECTOR_DB, DB_TABLE_NAME
from langchain_core.documents import Document
from src.app.models import Resume

def search_similarity_vector(query: str, top_k: int = TOP_K, category: str | None = None) -> list[tuple[Document, float]]:
    """"Mencari daftar resume yang memiliki nilai similarity besar"""
    if category:
        filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.category",
                    match=MatchValue(value=category)
                )
            ]
        )

        results = VECTOR_DB.similarity_search_with_score(query=query, k=top_k, filter=filter)
    else :
        results = VECTOR_DB.similarity_search_with_score(query=query, k=top_k)

    return results;

def find_resumes(resume_ids: list[int]) -> list[Resume]:
    """Helper untuk menemukan resume ke database SQL"""
    # Ambil data dari database sql
    resume_query = f"""
                    SELECT id, resume_id, resume_str, category
                    FROM {DB_TABLE_NAME}
                    WHERE resume_id IN ({','.join(map(str, resume_ids))})
                    """
    resumes_exec = DB.run(resume_query, include_columns=True)

    # DB.run() mengembalikan string
    if not resumes_exec:
         return []

    return ast.literal_eval(resumes_exec)
