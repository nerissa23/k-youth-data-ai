import json
import time
import os
import sqlite3
import re
from pathlib import Path
from itertools import islice
from prompt_model import prompt_model

BATCH_SIZE = 2
RETRY_DUR = 60
MAX_ATTEMPT = 3
MODEL = "gemini-2.5-flash-lite"

def chunks(data: dict, SIZE: int = 10):
    """Create sub-dictionaries from `data` by slicing into `SIZE` slices"""
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

def send_prompt(model: str, batch_desc: list) -> list | None:
    """Sends one prompt to model for the entire batch

    Returns: parsed list of tech stacks OR None on failure
    """

    prompt = f"""
        ## INSTRUCTIONS
        You are a data tagging assistant. Analyse the description of several job listings and extract the tech stack for each role.
        
        ## YOUR TASK
        You will be given a numbered list of job descriptions.
        Return ONLY a JSON array where each element is a comma-separated string of technologies for the corresponding job. No explanation, no markdown, no extra text.

        Example output format:
        ["Python, SQL, Tableau", "Java, Spring Boot, Docker", "React, Node.js, MongoDB"]

        ## JOB DESCRIPTIONS
        {chr(10).join(f"{i+1}. {desc}" for i, desc in enumerate(batch_desc))}

        IMPORTANT: Return exactly {len(batch_desc)} elements in the array, one per job.
        If a job has no technologies mentioned, use "-".
    """

    raw = prompt_model(model, prompt)

    # detect error strings returned by prompt_model()
    if raw.startswith("[Gemini Error]") or raw.startswith("[Ollama Error]"):
        if "429" in raw:
            raise RateLimitError(raw)
        print(raw)
        return None

    try:
        # extract JSON array from raw string using regex
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            # model did not return a list, fail
            return None
        return json.loads(match.group())
    except (json.JSONDecodeError, ValueError):
        return None

def update_table(cursor, source_id, tech_stack):
    """Populate tech stack column by source_id; return exec result status"""

    try:
        cursor.execute(f"""
            UPDATE jobs
            SET tech_stack = '{tech_stack}'
            WHERE source_id = '{source_id}' AND
            tech_stack IS NULL
        """)

        if cursor.rowcount == 1:
            return f"Analysed Job {source_id}: {tech_stack}"
    except Exception as e:
        return f"Error updating table: {e}"

def process_in_batch(conn, cursor, res):
    """Split rows into batches, send prompt for data tagging to model per batch, update table"""

    # for each batch
    for index, batch in enumerate(chunks(res, BATCH_SIZE)):
        # cleaning description text from whitespace chars
        batch_desc = [
            re.sub(r'\s+', ' ', desc).strip()
            for desc in batch.values()
        ]

        for attempt in range(1, MAX_ATTEMPT + 1):
            try:
                tech_stack = send_prompt(MODEL, batch_desc)

                # validate tech_stack response from model
                if tech_stack is None or len(tech_stack) != len(batch_desc):
                    print(f"[Batch {index}] Attempt {attempt} failed: Mismatch between batch size and response")
                    continue # retry attempt

                # update DB table
                for src_id, stack in zip(batch.keys(), tech_stack):
                    result = update_table(cursor, src_id, stack)
                    result and print(result)
                conn.commit()
                break
            except RateLimitError as e:
                print(f"RateLimitError: {e}")
                time.sleep(RETRY_DUR)
                continue
            except Exception as e:
                print(f"[Batch {index}] Attempt {attempt} failed: {type(e).__name__}: {e}")
                continue

def tag_data(db_url: str) -> None:
    if not os.path.isfile(db_url):
        print(f"Database not found at {db_url}")
        return

    try:
        with sqlite3.connect(db_url) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT source_id, description FROM jobs WHERE tech_stack IS NULL")
            res = cursor.fetchall()

            if not res:
                print("No data to tag")
                return
            
            res = dict(res)

            process_in_batch(conn, cursor, res)
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    except Exception as e:
        print(f"{type(e).__name__}: {e}")

if __name__ == "__main__":
    DB_PATH = Path("data/jobs_d1.db")
    tag_data(DB_PATH)

class RateLimitError(Exception):
    pass