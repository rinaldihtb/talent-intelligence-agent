# Candidate / Talent Intelligence

Aplikasi **Candidate/Talent Intelligence** berbasis Streamlit untuk mencari, menganalisis, dan membandingkan kandidat dari data resume. Orkestrasi percakapan menggunakan LangChain dan LangGraph (supervisor dengan agen pencarian, analisis, dan komparasi). Data profil kandidat disimpan di SQLite atau Supabase, sedangkan potongan resume diindeks di Qdrant agar pencarian kandidat memakai vector similarity dan reranking.

## Struktur penting

```text
main.py                         # Entry point Streamlit
src/app/                        # Konfigurasi, agen, tools, dan helper
src/script/seed_database.py     # Seed dataset ke SQLite atau Supabase
src/script/seed_embedding.py    # Buat embedding dan seed ke Qdrant
data/dataset.csv.gz             # Dataset resume
.env.example                    # Template konfigurasi
requirements.txt                # Dependensi Python
```

Dataset yang disertakan memiliki kolom `id`, `resume_id`, `resume_str`, dan `category`. Seeder database dan Qdrant memakai nama kolom tersebut.

## Prasyarat

- Python dan `pip`
- OpenAI API key, karena aplikasi menggunakan `gpt-4o-mini` dan embedding `text-embedding-3-small`
- Instance Qdrant dan collection tujuan
- Salah satu database: SQLite (lokal) atau Supabase

## Setup lokal

Jalankan seluruh perintah dari root repository.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Jika lingkungan Anda menyediakan perintah `python` alih-alih `python3`, gunakan perintah tersebut secara konsisten.

## Salin dan isi environment

```bash
cp .env.example .env
```

Isi `.env` sesuai backend yang dipakai. Jangan commit file ini.

### Konfigurasi minimum: SQLite

```env
DATASET_PATH=./data/dataset.csv.gz

OPENAI_API_KEY=<openai-api-key>
# OPENAI_BASE_URL=  # opsional jika memakai endpoint OpenAI-compatible

QDRANT_URL=<qdrant-url>
QDRANT_API_KEY=<qdrant-api-key>
QDRANT_COLLECTION_NAME=<nama-collection>

DB_TYPE=SQLITE
DB_SQLITE_PATH=./data/resume.sqlite
DB_TABLE_NAME=resumes

BATCH_SIZE=100
MAX_ATTEMPTS=3
RETRY_DELAY=2
```

### Konfigurasi alternatif: Supabase

Gunakan nilai Qdrant dan OpenAI yang sama, lalu ganti bagian database menjadi:

```env
DB_TYPE=SUPABASE
DB_TABLE_NAME=resumes
SUPABASE_URL=<supabase-project-url>
SUPABASE_PUBLIC_KEY=<supabase-publishable-or-anon-key>
SUPABASE_URI=<postgresql-sqlalchemy-uri>
```

`SUPABASE_URI` wajib ditambahkan meskipun belum tercantum di `.env.example`: variabel ini dibaca oleh `src/app/config.py` ketika aplikasi memakai Supabase. `SUPABASE_PUBLIC_KEY` dipakai oleh script seeding. Pastikan key dan kebijakan RLS Supabase mengizinkan operasi `delete` serta `insert` untuk tabel tersebut.

Untuk observability Langfuse, isi `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, dan `LANGFUSE_BASE_URL` yang tersedia pada template; fitur ini terpisah dari alur seeding.

## Siapkan tabel Supabase (hanya bila memakai Supabase)

Script `src/script/seed_database.py` tidak membuat tabel Supabase. Buat tabel `resumes` terlebih dahulu melalui SQL Editor Supabase, dengan struktur yang sesuai dengan data yang diseed:

```sql
create table resumes (
  id bigint primary key,
  resume_id bigint,
  resume_str text,
  category text
);
```

## Seed data relasional

Pilih backend lewat `DB_TYPE` pada `.env`, lalu jalankan:

```bash
python3 src/script/seed_database.py
```

- `DB_TYPE=SQLITE` akan membuat atau mengganti tabel `resumes` di `DB_SQLITE_PATH`.
- `DB_TYPE=SUPABASE` akan menghapus seluruh baris tabel target lalu memasukkan dataset secara batch.

> Seeding bersifat destruktif untuk tabel target: SQLite menjalankan `DROP TABLE`, sedangkan Supabase menghapus data sebelum insert.

## Seed Qdrant

Pastikan `QDRANT_URL`, `QDRANT_API_KEY`, dan `QDRANT_COLLECTION_NAME` telah diisi. Collection Qdrant harus sudah tersedia dan kompatibel dengan embedding OpenAI `text-embedding-3-small` yang dipakai aplikasi. Kemudian jalankan:

```bash
python3 src/script/seed_embedding.py
```

Script ini memecah setiap `resume_str` menjadi chunk (800 karakter dengan overlap 100), membuat embedding, lalu mengunggahnya ke collection dalam batch. ID dokumen dibuat deterministik dari `resume_id` dan indeks chunk, sehingga menjalankan ulang proses akan menargetkan ID chunk yang sama.

## Jalankan Streamlit

Setelah database relasional dan Qdrant selesai diseed, jalankan:

```bash
streamlit run main.py
```

Streamlit akan menampilkan antarmuka **Recruitement Assistant Chatbot**. Agen pencarian memakai Qdrant untuk menemukan resume relevan, lalu mengambil detail kandidat dari SQLite atau Supabase untuk analisis dan perbandingan.

## Troubleshooting

- **`KeyError` atau variabel environment tidak ditemukan**: pastikan `.env` ada di root repository dan semua variabel untuk backend yang dipilih telah diisi.
- **Gagal terhubung Qdrant**: periksa URL, API key, dan nama collection; konfigurasi Qdrant dibaca saat aplikasi atau seeder embedding diimpor.
- **Gagal seed Supabase**: pastikan tabel `resumes` sudah dibuat dan key/RLS mengizinkan penghapusan serta penambahan baris.
- **Database SQLite tidak ditemukan**: jalankan seeder database terlebih dahulu dan pastikan `DB_SQLITE_PATH` pada `.env` sama dengan path yang digunakan saat menjalankan aplikasi.
