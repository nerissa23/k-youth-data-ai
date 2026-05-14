from pathlib import Path
from paths import DATA_DIR
import sqlite3
import os
import json

def load_all_jsons(input_dir, output_dir):
    if not os.path.isdir(input_dir):
        print(f"❗ Input directory not found")
        return
    
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    try:
        files = os.listdir(input_dir)
        insert_count = 0
        if len(files) == 0:
            print(f"❗ Input directory is empty")
            return

        for file in files:
            json_path = os.path.join(input_dir, file)
            db_path = Path(output_dir)/"jobs.db"
            json_str = Path(json_path).read_text(encoding="utf-8")
            data = json.loads(json_str)

            # connect() accepts db file path as arg
            with sqlite3.connect(db_path) as conn:
                # cursor: exec CRUD ops, queries, fetches
                cursor = conn.cursor()
                create_table_schema(cursor)

                # loading work
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO jobs (source_id, job_title, company, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (data["source_id"], data["job_title"], data["company"], data["description"])
                )

                if cursor.rowcount == 1:
                    insert_count += 1
                    print(f"✅ Inserted: {file}")
                else:
                    print(f"⏭️ Skipped (duplicate): {file}")
                    
                conn.commit()

        print_summary(len(files), insert_count, len(files)-insert_count)
    except sqlite3.Error as e:
        print(f"SQLIte Error: {e}")
    except Exception as e:
        print(f"Error loading JSON to DB: {e}")

def create_table_schema(cursor):
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                source_id TEXT PRIMARY KEY,
                job_title TEXT,
                company TEXT,
                description TEXT,
                tech_stack TEXT
            )
            """
        )
    except Exception as e:
        print(f"❗ Error creating schema: {e}")

def print_summary(total, success, fail):
    print(f"\n📊 Gold Summary:\nTotal: {total} | Inserted: {success} | Skipped: {fail}")

def load():
    input = DATA_DIR/"2_silver"
    output = DATA_DIR/"3_gold"
    load_all_jsons(input, output)