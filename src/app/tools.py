import ast

from langchain_core.documents import Document
from langchain_core.tools import tool
from qdrant_client.models import FieldCondition, Filter, MatchValue

from src.app.config import TOP_K, RERANKER
from src.app.models import ResultResume, Resume, ResumeEvidence
from src.app.helpers import search_similarity_vector, find_resumes

@tool
def search_candidates(query: str, limit : int = 5, category: str | None = None) -> list[ResultResume]:
    """Melakukan pencarian kandidat berdasarkan query user, limit adalah jumlah kandidat yang unik"""

    # Melakukan pemanggilan data sampai limit yang direquest user
    documents : list[ResultResume] = []
    top_k = TOP_K * limit
    search_attempt = 1
    unique_resumes : list[int] = []
    prev_results_total = 0;
    while True:
        search_results = search_similarity_vector(query, top_k, category)

        for doc, score in search_results:
            if str(doc.metadata['resume_id']) not in unique_resumes :
                unique_resumes.append(str(doc.metadata['resume_id']))

                highest_evidence = ResumeEvidence(chunk_index=doc.metadata['chunk_index'], text=doc.page_content, score=score)
                documents.append(ResultResume(id=None, resume_str=None, rerank_score=None, resume_id=doc.metadata['resume_id'], highest_evidence=highest_evidence, category=doc.metadata['category']))

        if len(unique_resumes) >= limit or (prev_results_total != 0 and prev_results_total == len(search_results)) : break
        else :
            top_k *= (search_attempt ** 2) * limit
            search_attempt+=1
            prev_results_total = len(search_results)

    # Ambil data dari database sql
    resumes = find_resumes(unique_resumes)

    for doc in documents:
        selected_resume = next((x for x in resumes if int(x['resume_id']) == doc.resume_id), -1)
        doc.resume_str = selected_resume['resume_str'];
        doc.id = selected_resume['id'];

    reranked_result = reranker_resumes(query, documents, limit)

    return reranked_result

def reranker_resumes(query, documents: list[ResultResume], limit):
    """"Melakukan reranker dari resume yang sudah diperoleh"""
    pairs = [
        [query, doc.highest_evidence.text]
        for doc in documents
    ]

    scores = RERANKER.predict(pairs)

    for doc, score in zip(documents, scores):
        doc.rerank_score = float(score)


    result = sorted(
        documents,
        key=lambda x: x.rerank_score,
        reverse=True
    )

    print(result[:limit])
    return result[:limit];

@tool
def execute_query_tool(query: str) -> str:
    """Eksekusi query SQL SELECT ke database dan gunakan hasilnya
    JANGAN gunakan selain perintah SELECT"""

    try:
        query_result = DB.run(query)
    except Exception as e:
        query_result = f"Error: {e}"
    return query_result

@tool
def extract_candidate_profile(resume_id: int) -> Resume | str:
    """Mengambil informasi secara lengkap seorang kandidat berdasarkan resume_id.
    Gunakan tool ini ketika membutuhkan informasi detail tentang kandidat tertentu"""

    find_resume = find_resumes(resume_ids=[resume_id])

    if not find_resume:
        return f"Kandidat dengan resume_id {resume_id} tidak ditemukan."

    result = find_resume[0];

    resume = Resume(id=result['id'], resume_id=result['resume_id'], resume_str=result['resume_str'], category=result['category'])
    print(resume)
    return resume

@tool
def extract_candidate_profiles(resume_ids: list[int]) -> list[Resume] | str:
    """Mengambil informasi secara lengkap Lebih dari 1 Kandidat.
    Gunakan tool ini untuk mengesktrak detail tentang kandidat-kandidat tertentu"""

    find_resume_exec = find_resumes(resume_ids)

    if not find_resume_exec:
        return f"Kandidat tidak ditemukan."

    resumes: list[Resume] = []
    for result in find_resume_exec:
        resumes.append(Resume(id=result['id'], resume_id=result['resume_id'], resume_str=result['resume_str'], category=result['category']))

    return resumes

if __name__ == "__main__" :
    t01 = search_candidates.invoke({
        "query": "Carikan saya kandidat dengan mastery software engineering berpengalaman 5 tahun",
        "limit": 5,
        "category": None
    })

    t02 = extract_candidate_profile.invoke({
        "resume_id": 55712978
    })

    t03 = extract_candidate_profiles.invoke({
        "resume_ids": [55712978,18316239,93112113]
    })

    print(t01)
    print(t02)
    print(t03)
