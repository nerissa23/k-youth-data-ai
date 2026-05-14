from pathlib import Path
from paths import DATA_DIR
import os
import sqlite3

def run_data_profile(db_path):
    db_file = Path(db_path)/"jobs.db"

    # check if db_path exist, if not return safely
    if not os.path.isfile(db_file):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # total records
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_recs = cursor.fetchone()[0]
    print(f"📈 Total Records: {total_recs}")

    # null values in job_title, company, desc
    cursor.execute(
        """
        SELECT
            SUM(CASE WHEN job_title IS NULL THEN 1 ELSE 0 END) AS job_title,
            SUM(CASE WHEN company IS NULL THEN 1 ELSE 0 END) AS company,
            SUM(CASE WHEN description IS NULL THEN 1 ELSE 0 END) AS description
        FROM jobs
        """
    )
    res = cursor.fetchone()
    nulls = dict(res)
    missing = [f"{col}: {count}" for col, count in nulls.items()]
    print(f"❓ Missing values -> {', '.join(missing)}")

    # avg desc length
    cursor.execute(
        """
        SELECT avg(length(description)) FROM jobs
        """
    )
    res = cursor.fetchone()[0]
    print(f"📝 Avg Description Length: {res:.0f} chars")

    # shortest desc length & source_id, job_title
    cursor.execute(
        """
        SELECT source_id, job_title, min(length(description)) AS length FROM jobs
        """
    )
    shortest = dict(cursor.fetchone())
    print(f"⚠️  Shortest Description: {shortest["length"]} chars")
    rec = [f"{source_id}: {job_title}" for source_id, job_title in shortest.items()]
    print(f"   ↳ {' | '.join(rec[0:-1])}")

    # longest desc length & source_id, job_title
    cursor.execute(
        """
        SELECT source_id, job_title, max(length(description)) AS length FROM jobs
        """
    )
    longest = dict(cursor.fetchone())
    print(f"⚠️  Longest Description: {longest["length"]} chars")
    rec = [f"{source_id}: {job_title}" for source_id, job_title in longest.items()]
    print(f"   ↳ {' | '.join(rec[0:-1])}")

    conn.close()

def profile():
    print("\n--- 🔍 DATA QUALITY REPORT ---")
    db_path = DATA_DIR/"3_gold"
    run_data_profile(db_path)