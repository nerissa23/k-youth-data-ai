from pathlib import Path
import sqlite3
import os
import json
import logging
from hashlib import sha256

def load_all_jsons(input_dir, output_dir):
    print("\n🥇 Gold:...")

    if not os.path.isdir(input_dir):
        logging.error(f"❗ Input directory not found")
        return
    
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    try:
        files = os.listdir(input_dir)
        insert_count = 0
        if len(files) == 0:
            logging.error(f"❗ Input directory is empty")
            return

        for file in files:
            json_path = os.path.join(input_dir, file)
            db_path = Path(output_dir)/"jobs.db" # boleh letak luar loop
            json_str = Path(json_path).read_text(encoding="utf-8")
            data = json.loads(json_str)
            job_title = data["job_title"]
            company = data["company"]
            desc = data["description"]
            source_id = data["source_id"]

            hash_input = f"{job_title.strip().lower()}|{company.strip().lower()}|{desc.strip().lower()}"
            content_hash = sha256(hash_input.encode()).hexdigest()

            # connect() accepts db file path as arg
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row

                # cursor: exec CRUD ops, queries, fetches
                cursor = conn.cursor()
                # create_table_schema(cursor, True, "content_hash", "TEXT")
                create_table_schema(cursor)

                # BONUS: solve INSERT OR IGNORE problem
                cursor.execute("SELECT content_hash FROM jobs WHERE source_id = ?", (source_id,))
                existing = cursor.fetchone()
                # (a,b) -> tuple -> existing["source_id"]

                if existing is None:
                    # new record, can insert
                    cursor.execute("INSERT INTO jobs VALUES (?, ?, ?, ?, ?)",
                                   source_id, job_title, company, desc, content_hash)
                    insert_count += 1
                    logging.info(f"✅ Inserted: {file}")
                elif existing["content_hash"] != content_hash:
                    # record exists but content changed, need to update
                    cursor.execute(
                        """
                        UPDATE jobs SET job_title=?, company=?, description=? content_hash=?
                        WHERE source_id=?
                        """,
                        (job_title, company, desc, content_hash, source_id)
                    )
                    logging.info(f"🔄 Updated: {file}")
                else:
                    # record exists and same content
                    logging.warning(f"⏭️  Skipped (duplicate): {file}")
                    
                conn.commit()

        print_summary(len(files), insert_count, len(files)-insert_count)
    except sqlite3.Error as e:
        logging.error(f"❗ SQLIte Error: {e}")
        raise(e)
    except Exception as e:
        logging.error(f"❗ Error loading JSON to DB: {e}")

def create_table_schema(cursor, new_col=False, col_name="", col_type=""):
    try:
        if new_col:
            cursor.execute(
                f"""
                ALTER TABLE jobs ADD COLUMN {col_name} {col_type}
                """
            )
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    source_id TEXT PRIMARY KEY,
                    job_title TEXT,
                    company TEXT,
                    description TEXT,
                    tech_stack TEXT,
                    content_hash TEXT
                )
                """
            )
    except Exception as e:
        logging.error(f"❗ Error creating schema: {e}")

def print_summary(total, success, fail):
    print(f"\n📊 Gold Summary:\nTotal: {total} | Inserted: {success} | Skipped: {fail}")