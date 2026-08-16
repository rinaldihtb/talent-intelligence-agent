from pydantic import BaseModel, Field

class ResumeEvidence(BaseModel):
    chunk_index: int = Field(..., description="Index dari potongan dokumen")
    text: str = Field(..., description="Potongan dari dokumen")
    score: float = Field(..., description="Nilai cosine simillarity pada query")

class ResultResume(BaseModel):
    id: int | None = Field(..., description="Index dokumen dari database")
    resume_id: int = Field(..., description="Nomor Unik Resume")
    resume_str :str | None = Field(..., description="Keseluruhan Konten dari Resume")
    category :str = Field(..., description="Category dari resume")
    highest_evidence: ResumeEvidence = Field(..., description="Data vektor yang punya kedekatan tertinggi dari query")
    rerank_score : float | None = Field(..., description="Menunjukkan score dari proses reranking")

class Resume(BaseModel):
    id: int = Field(..., description="Index dokumen dari database")
    resume_id: int = Field(..., description="Nomor Unik Resume")
    resume_str :str = Field(..., description="Keseluruhan Konten dari Resume")
    category :str = Field(..., description="Category dari resume")
