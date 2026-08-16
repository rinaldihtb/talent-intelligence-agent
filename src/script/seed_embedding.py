import time
import uuid
import os

import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.app.config import VECTOR_DB

DATASET_PATH = os.environ['DATASET_PATH']

BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))


def create_documents(dataset):

    # Menggunakan RecursiveCharacterTextSplitter, yang paling pintar untuk proses chunking.
    # 800 Karakter, Overap 100
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )
    documents = []
    document_ids = []

    # 2000an Resume Diproses Chunking.
    # 1 Resume bisa generate 4-20 Documents
    for row in dataset.itertuples(index=False):

        # Input informasi Resume_id dan category pada setiap dokumen
        chunks = splitter.create_documents(
            texts=[row.resume_str],
            metadatas=[
                {
                    "resume_id": row.resume_id,
                    "category": row.category,
                }
            ],
        )
        for chunk_index, chunk in enumerate(chunks):
            # Menambahkan informasi chunk_index ke document,
            chunk.metadata["chunk_index"] = chunk_index
            documents.append(chunk)

            # generate document_id dengan uuid unik untuk mencegah duplikasi data di vector database
            document_id = uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{row.resume_id}_{chunk_index}",
            )
            document_ids.append(str(document_id))

    # Array Dokuments
    # Array Dokument IDS
    return documents, document_ids


def generate_documents(dataset, vector_database):
    start_time = time.perf_counter() ## Logging Purpose
    dataset_count = len(dataset) ## Logging Purpose

    # Melakukan chunking
    documents, document_ids = create_documents(dataset)

    document_count = len(documents)

    # 20 ribu+ Dokumen setelah proses chunking
    # Proses insert dilakukan per 100 Dokumen dengan metode BulkInsert

    for batch_start in range(0, document_count, BATCH_SIZE):
        batch_number = (batch_start // BATCH_SIZE) + 1
        batch_end = batch_start + BATCH_SIZE
        batch_documents = documents[batch_start:batch_end]
        batch_ids = document_ids[batch_start:batch_end]

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                # Bulk Insert Vector Database
                vector_database.add_documents(
                    documents=batch_documents,
                    ids=batch_ids,
                )
                break
            except Exception as error:
                print(
                    f"Batch {batch_number} failed "
                    f"(attempt {attempt}/{MAX_ATTEMPTS}): {error}"
                )

                if attempt == MAX_ATTEMPTS:
                    raise

                time.sleep(RETRY_DELAY)

        processed_count = min(batch_end, document_count)
        progress = processed_count / document_count
        print(
            f"Processed {processed_count}/{document_count} "
            f"documents ({progress:.1%})"
        )

    elapsed_seconds = time.perf_counter() - start_time
    summary = (
        f"Seeding completed: {dataset_count} dataset rows, "
        f"{document_count} documents, {elapsed_seconds:.2f} seconds"
    )

    print(summary)


if __name__ == "__main__":
    dataset = pd.read_csv(DATASET_PATH)
    generate_documents(dataset, VECTOR_DB)
