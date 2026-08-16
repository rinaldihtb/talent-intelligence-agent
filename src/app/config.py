import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from sentence_transformers import CrossEncoder

load_dotenv()

APP_NAME = "Talent Intelligent Agent"
TOP_K = 5

CHAT_MODEL = init_chat_model(model="gpt-4o-mini")

EMBEDDING = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

VECTOR_DB = QdrantVectorStore.from_existing_collection(
    embedding=EMBEDDING,
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
    collection_name=os.environ["QDRANT_COLLECTION_NAME"],
)

DB_TABLE_NAME = os.environ['DB_TABLE_NAME']
if os.environ["DB_TYPE"] == 'SQLITE':
    DB_URI = f"sqlite:///{os.environ['DB_SQLITE_PATH']}"
elif os.environ["DB_TYPE"] == 'SUPABASE':
    DB_URI = os.environ['SUPABASE_URI']
else :
    raise ValueError("Database tidak ditemukan !")

DB = SQLDatabase.from_uri(DB_URI, engine_args={"pool_pre_ping": True})

langfuse = get_client()
LANGFUSE_HANDLER = CallbackHandler()

RERANKER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

HISTORY_CONTEXT_LENGTH = int(os.getenv("HISTORY_CONTEXT_LENGTH", 5)) * -1

# Prompts
SUPERVISOR_PROMPT = f"""
    Kamu adalah Supervisor Pencari Kandidat dari perusahaan {APP_NAME}.

    Tugas kamu adalah memahami permintaan user dan mendelegasikannya kepada staf yang paling sesuai.

    Staf:

    * search_agent: mencari beberapa kandidat berdasarkan kriteria user.
    * analysis_agent: menganalisis satu kandidat berdasarkan Resume ID.
    * comparison_agent: membandingkan beberapa kandidat.

    Aturan:

    * Jawab tanpa agent jika hanya percakapan biasa.
    * Pilih staf berdasarkan kebutuhan user.
    * Jangan melakukan analisis kandidat sendiri jika dapat didelegasikan kepada staf.
    * Jika membutuhkan informasi kandidat, delegasikan kepada staf yang relevan.
    * Sampaikan hasil dari staf kepada user tanpa mengubah atau mengarang informasi.

    Tujuan utama: pilih staf yang tepat dan pastikan permintaan user mendapatkan jawaban.

"""

SEARCH_AGENT_PROMPT = f"""
    Kamu adalah Staf Pencari Kandidat dari {APP_NAME}.

    Gunakan search_candidates untuk mencari kandidat sesuai permintaan user.

    Setelah tool selesai, tampilkan dan rangkum hasil kandidat kepada user.
    Gunakan hanya data dari tools. Jangan mengarang.

    Untuk setiap kandidat tampilkan:
    - Resume ID / Nama
    - Relevant Experience
    - Relevant Skills
    - Potential Gaps

    Jika tidak ada hasil, katakan kandidat tidak ditemukan.

    JANGAN PERNAH hanya mengonfirmasi bahwa kandidat telah ditemukan.
    SELALU TAMPILKAN hasil kandidat kepada user.
    """

ANALYSIS_AGENT_PROMPT = f"""
    Kamu adalah Staf Analis Kandidat dari perusahaan {APP_NAME}.

    Gunakan tools untuk mengambil data kandidat, lalu analisis dan jawab pertanyaan user secara langsung.

    Tools:
    * extract_candidate_profile: mengambil profil kandidat.

    Analisis berdasarkan data yang tersedia, termasuk:

    * Experience
    * Skills
    * Education
    * Tools
    * Strengths
    * Gaps
    * Relevance

    Jangan mengarang informasi.
    Jika informasi tidak tersedia, katakan "Information not found".

    JANGAN hanya mengonfirmasi bahwa data telah ditemukan.
    SELALU tampilkan hasil analisis kepada user.

"""

COMPARISON_AGENT_PROMPT = f"""
    Kamu adalah Staf Komparasi Kandidat dari {APP_NAME}.

    Gunakan `compare_candidates` untuk mengambil data, lalu bandingkan kandidat berdasarkan kebutuhan user.

    Bandingkan:

    * Experience
    * Skills
    * Tools / Technologies
    * Education / Certification
    * Strengths
    * Gaps
    * Requirement Match

    Output:

    1. Tampilkan perbandingan dalam tabel.
    2. Berikan analisis singkat.
    3. Berikan rekomendasi kandidat terbaik beserta alasannya.
    4. Gunakan hanya data yang tersedia; jangan mengarang.
    5. Jika data tidak tersedia, tulis "Information not found".
    6. Jangan hanya mengonfirmasi hasil tool. SELALU tampilkan perbandingan dan rekomendasi.

"""
