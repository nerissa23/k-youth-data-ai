# Week 2: AI Component

## Project Overview

In this week, the goal is to build an AI component that analyses job listings and identify skill gaps from a candidate's resume. We can break it into 3 subcomponents:
- `prompt_model.py`: a unified interface to prompt both local (Ollama) and cloud-based (Gemini) LLMs
- `tag_data.py`: reads job listings from an sqlite database and populate `tech_stack` column with LLM-extracted technologies from job descriptions
- `find_skill_gaps.py`: reads a resume, extract the candidate's tech skills using LLM, then compare against all jobs' tech stacks in the database to identify the candidate's skill gaps in the job market

Crucial skills learned: data tagging with LLMs, regex matching, integrating AI into applications, MCPs

## Setup Instructions

**Prerequisites**
- Python 3.14
- `uv` package manager (can install [here](https://docs.astral.sh/uv/getting-started/installation/))
- [Ollama](https://ollama.com/download) v0.24.x installed and running
- A Google AI Studio key from https://aistudio.google.com/
- 8 GB RAM, 10 GB storage (for local Ollama models)

**To setup this project in your workspace, follow the steps below:**

1. In your VS Code terminal, `git clone` this project into your local workspace and `cd` into `week_2/`.

2. Run `uv venv` to create a virtual environment for managing your packages and libraries for this project.

3. Run `uv sync` to install/add packages required in this project (list is specified in `uv.lock` and `pyproject.toml`).

4. Verify Ollama is running:

    ```bash
    curl 127.0.0.1:11434
    # Expected: Ollama is running
    ```

5. Pull Ollama models

    ```bash
    ollama pull llama3.1
    ollama pull phi3
    ollama pull deepseek-r1:1.5b
    ```

6. Create a `.env` file in the `week_2/` directory:
    ```
    GOOGLE_API_KEY=your-api-key-here
    ```
    Make sure you DO NOT commit this file. It should be listed in `.gitignore`. 
    
    NOTE: `.env.example` is an environment variable template file for you to see the variables that has to be set in your .env file. This file can be committed to git.

7. Create a `data/` directory at the root of this project, and store all your database and resume files to start running the project.

## Usage

#### 1. Tag job descriptions in the database
```bash
uv run tag_data.py
# Optional args:
uv run tag_data.py <model> <db_path>
```
NOTE: Running the command without optional args will automatically use default model and database path specified in the program.

#### Expected Output:
```
(week-2) PS C:\Users\neris\VsCode Projects\42kl\k-youth-data-ai\week_2> uv run tag_data.py
Analyzed Job 91347112: Java, Spring Boot, Python, PyTorch, TensorFlow, scikit-learn, PostgreSQL, MySQL, Oracle, Git, Docker, Kubernetes, AWS, Azure, GCP, Kafka, RabbitMQ, Redis
Analyzed Job 91533584: PHP, Python, Node.js, MySQL, MongoDB, RESTful API, Linux, Alibaba Cloud, AWS, Docker, CI/CD, Nginx
...
...
```

---

#### 2. Find skill gaps from a resume
```bash
uv run find_skill_gaps.py
# Optional args:
uv run find_skill_gaps.py <model> <resume_path> <db_path>
```
NOTE: Running the command without optional args will automatically use default model, resume, and database path specified in the program.

#### Expected Output:
```
(week-2) PS C:\Users\neris\VsCode Projects\42kl\k-youth-data-ai\week_2> uv run find_skill_gaps.py
gaps=['alibaba cloud', 'aws', 'cd', 'ci', 'ci/cd', 'datastudio', 'docker', 'fastapi', 'flask', 'git', 'github actions', 'google cloud', 'grafana', 'java', 'kafka', 'kubernetes', 'langchain', 'linux', 'llamaindex', 'mongodb', 'nginx', 'node.js', 'oracle', 'php', 'postgresql', 'power bi', 'prometheus', 'pytorch', 'r', 'rabbitmq', 'redis', 'restful api', 'scikit-learn', 'spring boot', 'tableau', 'tensorflow']
```

---

#### 3. Prompt a model directly
```bash
uv run prompt_model.py <model> "<prompt>"
# Example:
uv run prompt_model.py llama3.1 "tell me one Malaysian joke"
uv run prompt_model.py gemini-2.5-flash "what is machine learning?"
```
NOTE: Available models: `llama3.1`, `phi3`, `deepseek-r1:1.5b`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-3-flash-preview`

#### Expected Output:
```
(week_2) PS C:\Users\neris\VsCode Projects\42kl\k-youth-data-ai\week_2> uv run prompt_model.py gemini-2.5-flash "explain what is mcp in 3 sentences"

--- RESPONSE ---

MCP stands for **Microsoft Certified Professional**, a foundational certification program offered by Microsoft to validate an individual's skills and expertise with their various technologies. Achieving MCP status typically meant passing a single Microsoft certification exam, signifying a recognized level of technical proficiency. While the "MCP" designation itself has been retired, Microsoft continues to offer a comprehensive suite of role-based certifications under the broader "Microsoft Certified" banner today.
```

## API/Function Reference

### 1. `prompt_model.py`
**`prompt_model(model, prompt, config=None) -> str`**
- Unified entry point to prompt any supported model. Strips the model and prompt strings, then routes to `ollama_prompt()` or `gemini_prompt()` based on whether the model name matches a known Ollama or Gemini model. Optionally accepts a `GenerateContentConfig` object which is forwarded to `ollama_prompt()` or `gemini_prompt()` if requires custom config for content generation. Returns an error string prefixed with `[Error]` if the model or prompt is empty, or if the model is not in either supported list.

**`gemini_prompt(model, prompt, config=None) -> str`**
- Calls the Google Gemini API via `genai.Client`. Returns `[Error]` if `API_KEY` is not set. Passes `config` as a keyword argument only when provided. Returns error strings prefixed with `[Gemini Error]` for `errors.APIError`, and `[Error] {ExceptionType}: {message}` for all other exceptions.

**`ollama_prompt(model, prompt) -> str`**
- Calls a locally running Ollama model using `ollama.generate()`. Returns the model's response string on success. Returns an error string prefixed with `[Ollama Error]` on any exception.

These three functions interact as follows: `prompt_model()` is the caller; `ollama_prompt()` and `gemini_prompt()` are the internal implementations selected based on model name.

---

### 2. `tag_data.py`

**`tag_data(db_url: str) -> None`**
- Entry point. Validates that `db_url` is a non-empty string pointing to an existing file. Fetches all rows from the `jobs` table where `tech_stack IS NULL OR tech_stack = '-'`, converts them to a `{source_id: description}` dict, and passes to `process_in_batch()`. Prints `[Error] No data to tag` if no untagged rows exist. Handles `sqlite3.Error` and general exceptions, printing errors without crashing.

**`process_in_batch(conn, cursor, res)`**
- Splits `res` into chunks of `BATCH_SIZE` using `chunks()`. For each batch, cleans description text with `re.sub(r"\s+", " ", desc)`, then enters a retry loop up to `MAX_ATTEMPT` times. On each attempt, calls `extract_tech_stack()` and validates that the returned list length matches `len(batch_desc)`. On mismatch or `None` return, prints `[Batch {index}] Attempt {attempt} failed: Mismatch between batch size and response` and sleeps `RETRY_DUR` seconds before retrying. On success, calls `update_table()` for each row, prints the result, commits the transaction, and breaks out of the retry loop.

**`extract_tech_stack(batch_desc: list) -> list | None`**
- Builds a numbered prompt from `batch_desc` and calls `prompt_model()`. Checks if the raw response starts with `[Gemini Error]`, `[Ollama Error]`, or `[Error]` and returns `None` if so. Otherwise uses `re.search(r"\[.*\]", raw, re.DOTALL)` to extract a JSON array from the response, parses it with `json.loads()`, and returns the resulting list. Returns `None` on `json.JSONDecodeError` or `ValueError`, or if no match is found.

**`update_table(cursor, source_id, tech_stack) -> str | None`**
- Executes a SQL `UPDATE` on the `jobs` table setting `tech_stack` for the given `source_id`, with an `AND tech_stack IS NULL` guard to prevent overwriting existing values. Returns `"Analysed Job {source_id}: {tech_stack}"` if `cursor.rowcount == 1`, `None` if no row was updated, or an error string prefixed with `[Error]` on exception.

**`chunks(data: dict, SIZE: int = 10)`**
- Generator that yields sub-dictionaries from `data` by slicing `SIZE` keys at a time using `itertools.islice`.

---

### 3. `find_skill_gaps.py`

**`find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult`**
- Entry point. Validates that both path strings are non-empty, that both files exist, and that `API_KEY` is set. Reads the resume as a UTF-8 string, calls `extract_resume_skills()`, then opens the SQLite DB and calls `get_job_skills()`. Computes gaps using `job_skills.difference(resume_skills)`, sorts and lowercases the result, and returns a `SkillGapResult`. Returns `SkillGapResult(gaps=[])` on any validation failure or exception, printing a descriptive `[Error]` message in each case.

**`extract_resume_skills(resume_text: str) -> set | None`**
- Builds a prompt instructing the model to extract only technical skills and return a JSON array. Creates a `GenerateContentConfig` with `temperature=0` and `seed=42` for deterministic output, and passes it to `prompt_model()`. Retries up to `MAX_ATTEMPTS` (3) times. On each attempt, checks for error string prefixes, then uses `re.search(r"\[.*\]", raw, re.DOTALL)` to extract the JSON array, parses it, and passes each skill through `normalise_skills()` to build a set. Returns `None` after all attempts fail.

**`get_job_skills(cursor) -> set`**
- Queries all non-null, non-`"-"` `tech_stack` values from the `jobs` table. Reads results in chunks using `cursor.fetchmany(BATCH_SIZE)` in a `while True` loop until no rows remain. Passes each `tech_stack` string through `normalise_skills()` and accumulates results into a single set.

**`normalise_skills(raw: str) -> set`**
- Splits a raw comma-separated skill string, strips and lowercases each item, skips empty strings and `"-"`, applies `apply_aliases()`, adds the result to the set, and also adds `/`-split variants of any item containing `/` (e.g. `c/c++` → adds `c` and `c++` in addition to `c/c++`).

**`apply_aliases(skill: str) -> str`**
- Looks up `skill` in the `ALIASES` dict imported from `aliases.py`. Returns the mapped canonical form if found, or the original string unchanged.

**`SkillGapResult`** (Pydantic BaseModel)
```python
class SkillGapResult(BaseModel):
    gaps: List[str]
```

### 4. `aliases.py`

Defines a module-level `ALIASES` dict mapping variant skill name strings to their canonical forms. Imported by `find_skill_gaps.py` and used in `apply_aliases()`. Current mappings cover JavaScript ecosystem variants, database name variants, cloud provider abbreviations, ML library aliases, and formatting differences (e.g. `powerbi` → `power bi`).

## Data/Assumptions

### Database schema (`jobs` table)

The following columns are used by this project:

| Column | Used by | Purpose |
|---|---|---|
| `source_id` | `tag_data.py`, `find_skill_gaps.py` | Primary key to identify each row |
| `description` | `tag_data.py` | Input text for tech stack extraction |
| `tech_stack` | `tag_data.py`, `find_skill_gaps.py` | Populated by `tag_data.py`; read by `find_skill_gaps.py` |

### Input format

- `db_url` must be a path to a valid SQLite `.db` file containing a `jobs` table with the columns above
- `input_file_path` must be a path to a plain `.txt` resume file encoded in UTF-8
- `tag_data.py` must be run before `find_skill_gaps.py` — `find_skill_gaps.py` reads from `tech_stack` and will return empty gaps if no rows are tagged

### Assumptions

- Job descriptions and resume text are in English
- Slight inaccuracies in LLM tech stack extraction are acceptable
- Certifications and non-technical skills such as leadership or management are excluded from extraction
- Skills containing `/` (e.g. `C/C++`, `CI/CD`) are split into variants and treated as separate matchable entries
- Skill name variations are normalised via `aliases.py` before comparison — both the resume and job sides use the same normalisation

### Data flow

```
resume.txt ──► extract_resume_skills() ──► normalise_skills() ──► resume_skills (set)
                                                                            │
jobs table ──► get_job_skills() ──► normalise_skills() ──► job_skills (set)
                                                                            │
                                    job_skills.difference(resume_skills)
                                                                            │
                                                            SkillGapResult.gaps (sorted, lowercase)
```

## Testing

The following scenarios were tested manually by running the scripts and observing output and database state.

| Scenario | How to reproduce | Expected behaviour |
|---|---|---|
| Tag untagged DB | Run `uv run tag_data.py` with a DB where `tech_stack IS NULL` | Each row logs `Analysed Job {id}: {stack}`, DB populated |
| Re-run on already tagged DB | Run `uv run tag_data.py` again on same DB | Prints `[Error] No data to tag`, DB unchanged |
| LLM returns wrong number of items | Triggered by inconsistent model output | Prints `[Batch {n}] Attempt {n} failed: Mismatch...`, retries up to `MAX_ATTEMPT` times |
| Find gaps with valid resume and tagged DB | Run `uv run find_skill_gaps.py` | Prints `gaps=[...]` sorted lowercase list |
| Missing API key | Remove or empty `GOOGLE_API_KEY` in `.env` | Prints `[Error] GOOGLE_API_KEY not set`, returns `SkillGapResult(gaps=[])` |
| Missing resume file | Pass a non-existent path | Prints `[Error] Resume file not found`, returns `SkillGapResult(gaps=[])` |
| Missing DB file | Pass a non-existent DB path | Prints `[Error] Database not found`, returns `SkillGapResult(gaps=[])` |
| Empty resume file | Pass a `.txt` file with no content | Prints `[Error] Resume file is empty`, returns `SkillGapResult(gaps=[])` |
| No internet, Gemini called | Disconnect network and run either script | `Exception` caught, prints `[Error] {ExceptionType}: ...`, no crash |

### Determinism

`find_skill_gaps.py` passes `temperature=0` and `seed=42` via `GenerateContentConfig` to the Gemini model when extracting resume skills. Running the same resume file multiple times produces the same `gaps` list.


## Limitations

- **Alias map must be maintained manually** — `aliases.py` only covers a fixed set of known variations; new mismatches must be added by hand
- **Only `.txt` resume input is supported** — no handling for PDF or other formats
- Token optimisation techniques and algorithms not applied
- Prompting format may still be enhanced


## Architecture Reflection

- **Design Choices**
    
    Why you structured your system the way you did (modularity, separation of concerns, etc.)

    `prompt_model.py` is structured as an abstraction layer so that `tag_data.py` and `find_skill_gaps.py` do not need to know which backend they are using. Adding a new model only requires updating the model lists and routing logic in one place.

    In `find_skill_gaps.py`, skill normalisation is handled in a single `normalise_skills()` function, applied consistently to both resume skills and job skills before comparison. This ensures the set difference is performed on a uniform representation. Alias mappings are separated into `aliases.py` to keep data out of logic code and make them easy to update independently.

    Batch processing in `tag_data.py` sends one LLM prompt per batch of job descriptions rather than one per row. This reduces the number of API calls and is justified by the free tier rate limits documented in `rate_limits.txt`.
    
- **Trade-offs**
    
    What you chose to prioritize (e.g. simplicity vs scalability, speed vs accuracy)

    In `find_skill_gaps.py`, simplicity was chosen where I used set difference over a loop-based comparison because it is concise and expressive for this use case, and does not require an explicit iteration over all job skills. As a result, I find there was no need to do batch processing for `resume_skills` and `job_skills` comparison. Instead, my batching logic was implemented in `get_job_skills()` function, when getting job skills from database. This is to ensure in cases where the database has a lot of rows (rows > 10000), reading the table won't require loading it entirely to memory. Intead, we process it batch by batch.
    
- **Improvements**
    
    What you would change or extend if given more time (e.g. better architecture, optimizations, additional features)

    Given more time, the following would be worth implementing:

    - Support interpreting resumes in different file formats (e.g. .pdf,.word, etc.)
    - Better skill comparison to catch near-matches that aliases miss (e.g. "spring" matching "spring boot")
    - Implement FastMCP
    - Token optimisation techniques
