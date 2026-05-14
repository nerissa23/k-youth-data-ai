# Week 1: Data Component

## Project Description
In this week, the goal is to construct an ETL pipeline which extracts raw HTML data from webpage sources, transform them into a structured JSON format, and finally load into a relational SQLite database.

## Setup Instructions
To setup this project in your workspace, follow the steps below:

1. Ensure you have `VS Code` installed with the following extensions: 

- `Error Lens by Alexander`
- `Python by Microsoft`
- `SQLite3 Editor by yy0931`

2. In your VS Code terminal, `git clone` this project into your local workspace.

3. Install `uv` using any of the standalone installers [here](https://docs.astral.sh/uv/getting-started/installation/) according to your OS.

4. Run `uv venv` to create a virtual environment for managing your packages and libraries for this project.

5. Run `uv sync` to install/add packages required in this project (list is specified in `uv.lock`).

6. You are ready to run the project!

## Usage
To run this project, refer to `main.py` for all the available commands:

_Prequisite: Activate your virtual env if not yet active._

1. To execute the entire pipeline, running `python main.py all` will execute all the modules in `ingestor.py`, `processor.py`, `loader.py` and `profiler.py` and return its respective outputs in the terminal.

2. If you wish to execute the modules one by one, you may run `python main.py xx`, with `xx` being any of the commands found in `main.py`.

3. The expected inputs and outputs for each module are as follows:

    | Module | Input | Output |
    | :--- | :--- | :--- |
    | `ingestor.py` | `data/0_source/*.mhtml` | `data/1_bronze/*.html` |
    | `processor.py` | `data/1_bronze/*.html` | `data/2_silver/*.json` |
    | `loader.py` | `data/2_silver/*.json` | `data/3_gold/jobs.db` (SQLite) |
    | `profiler.py` | `jobs.db` | Terminal summary |

## Technical Reflections
### Module 1: The Extractor (Medallion & Lakehouses)
Why is it useful to keep the original raw HTML files instead of directly inserting processed data into the database? What problems become easier to debug or recover from?
- **Answer**: Keeping the raw HTML files allows you to troubleshoot and re-process easier if it turns out your parsing logic is faulty. For example, when extracting the relevant information for a job listing (source_id, job_title, company, description), if any one of the fields are incorrect or sourced from the wrong html tag, you can directly re-extract the information again from the HTML files with `beautiful soup`, instead of having to ingest the MHTML files again (start from beginning). It is also more useful for analysing the DOM structure of the joblisting compared to the MIME structure we see in .mhtml files.

### Module 2: Treatment Plant (ETL vs ELT & Scale)
Why do cloud systems prefer loading raw data first before cleaning it (ELT)? What problems happen when processing files sequentially, and how does distributed processing help?
- **Answer**: Cloud systems (commonly in large modern enterprises) prefer ELT pipelines over ETL because the former allows for faster processing and insights. Since ELT pipelines mostly leverage powerful cloud-native computing resources, it is elastic and easily scalable, making it ideal for large scale data processing.

    In ETL pipelines, the sequential processing before loading the data into a target database is difficult to scale and slows the system down as data size increases. In contrast, ELT pipelines load data directly into the destination system and transform it in parallel (distribute transformation workloads across multiple computer nodes simultaneously) whenever it needs, increasing throughput.

### Module 3: The Blueprint & The Vault (Storage & Contracts)
What should happen if an important field like job_title disappears? Why fail early instead of silently inserting nulls into DB? How does INSERT OR IGNORE help prevent duplicate records?
- **Answer**: If mandatory fields like job_title disappears, the data record should be rejected and skip insertion into database. We can also log some progress statements to keep track of which records are successfully written to and not. It is better to implement early handling such as this instead of inserting nulls into the database as null values impacts the data quality and require explicit SQL queries to be detected. The INSERT OR IGNORE query on the other hand simply skips an insertion if a record with the same ID already exists, so while it doesn't help detect null values, it prevents duplicate records in the DB table.

### Module 4: The QA Inspector & Orchestrator (Orchestration & DAGs)
What happens if processor.py crashes halfway? How are automated orchestration tools more reliable than manual retries with Python scripts?
- **Answer**: If processor.py crashes halfway during execution, there may be some records written into json files in `data/2_silver/` dir. In the case where the extraction of the important fields uses an incorrect logic or method, the written json files may also be faulty/contain the wrong data themselves. An automated orchestration tool which orchestrates the entire pipeline from start to end will help solve this issue by re-executing the entire pipeline, refreshing all the files in the data directory, making it more reliable than manual retries.
