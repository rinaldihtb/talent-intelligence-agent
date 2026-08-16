import os
import sqlite3
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "SQLITE")
DATASET_PATH = os.environ["DATASET_PATH"]
DB_SQLITE_PATH = os.environ["DB_SQLITE_PATH"]
TABLE_NAME = os.environ["DB_TABLE_NAME"]

BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))


def seed_sqlite(dataset):
    with sqlite3.connect(Path(DB_SQLITE_PATH)) as db:
        db.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        db.execute(f"""
            CREATE TABLE {TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                resume_id INTEGER,
                resume_str TEXT,
                category TEXT
            )
        """)

        for start in range(0, len(dataset), BATCH_SIZE):
            batch = dataset.iloc[start:start + BATCH_SIZE]

            rows = [
                (
                    row.id,
                    row.resume_id,
                    row.resume_str,
                    row.category,
                )
                for row in batch.itertuples(index=False)
            ]

            db.executemany(
                f"""
                INSERT INTO {TABLE_NAME}
                (id, resume_id, resume_str, category)
                VALUES (?, ?, ?, ?)
                """,
                rows,
            )

        db.commit()


def seed_supabase(dataset):
    db = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_PUBLIC_KEY"],
    )

    db.table(TABLE_NAME).delete().neq("id", 0).execute()

    for start in range(0, len(dataset), BATCH_SIZE):
        batch = dataset.iloc[start:start + BATCH_SIZE]

        rows = batch[
            ["id", "resume_id", "resume_str", "category"]
        ].to_dict("records")

        db.table(TABLE_NAME).insert(rows).execute()


def main():
    start = time.perf_counter()
    dataset = pd.read_csv(DATASET_PATH)

    if DB_TYPE == "SQLITE":
        seed_sqlite(dataset)

    elif DB_TYPE == "SUPABASE":
        seed_supabase(dataset)

    else:
        raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}")

    print(
        f"Seeded {len(dataset)} rows "
        f"in {time.perf_counter() - start:.2f}s"
    )


if __name__ == "__main__":
    main()
