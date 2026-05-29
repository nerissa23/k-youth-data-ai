# Week 3 System Integration and Application

## Project Overview
In this week, we combined the pipelines from week 1 and 2 to build a fuilly functioning **chatbot application** with a working frontend for users to interact with. 

The goal of this project is to build and containerise a full-stack chat application consisting of a frontend, backend, and an AI model integration; with Docker Compose as the orchestrator.

**Tech stack:**
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript, Jinja2
- **Backend**: Python, FastAPI
- **AI models** = Ollama (local LLMs) & Google Gemini (via API)
- **Infrastructure**: Docker, Docker Compose

**Use cases**:
- General chat with an AI assistant
- Resume analysis
    - Summarise a resume
    - Find skill gaps based on real job market data
    - Answer questions about an uploaded resume


## Setup Instructions
### Prerequisites (Docker)
- [Docker](https://docs.docker.com/get-started/get-docker/) installed with engine running
- Docker Compose (included with Docker Desktop)
- [Ollama](https://ollama.com/download) installed and running on your machine (for local LLM support)
- (Optional) A Google AI Studio key from https://aistudio.google.com/ (only required if using google models)

### Prerequisites (Manual)
- Python 3.14
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package manager
- [Ollama](https://ollama.com/download) installed and running
- (Optional) A Google AI Studio key

### Environment Variables
Create a `.env` file in `week_3/` by copying the provided template:
```bash
cp .env.example .env
```

Then fill in the values:
```python
# frontend
BACKEND_URL=http://localhost:8001

# backend
GOOGLE_API_KEY=your-google-api-key-here         # optional: if wanna use gemini models
DB_NAME=jobs_d1.db                              # which job db to use
MODEL=llama3.1                                  # ai model to use
OLLAMA_HOST=http://host.docker.internal:11434   # docker: points to host machine's ollama
                                                # manual: use http://localhost:11434 instead
```
Note: `OLLAMA_HOST` must be `http://host.docker.internal:11434` when running with Docker, and `http://localhost:11434` when running manually. This is because Docker containers cannot reach the host machine via localhost.

### Database setup
Before running the application, copy the `.db` files from your Week 2 output into the backend:
```
backend/src/week_2/data/jobs_d1.db
backend/src/week_2/data/jobs.db       # optional second database
```
Make sure the `tech_stack` column in the database is already populated. If not, run `tag_data.py` from Week 2 first.


### Running with Docker
1. Make sure Ollama is running on your machine and the model is pulled:
    ```bash
    ollama pull llama3.1
    ollama serve
    ```

2. From `week_3/`, build and start all services:
    ```bash
    docker-compose up --build
    ```

3. Visit `http://localhost:8000` in your browser.

4. To stop all services:
    ```bash
    docker-compose down
    ```

### Running without Docker (Manual)
1. From`week_3/`, setup the virtual environment:
    ```bash
    uv venv
    uv sync
    ```

2. Verify Ollama is running:
    ```bash
    curl 127.0.0.1:11434
    # Expected: Ollama is running
    ```

3. Start both services in separate terminals:
    ```bash
    # Terminal 1 -> frontend
    cd frontend
    uv run uvicorn src.app:app --reload --port 8000

    # Terminal 2 -> backend
    cd backend
    uv run uvicorn src.app:app --reload --port 8001
    ```

4. Visit `http://localhost:8000` in your browser.


## Usage
### Sending a message
Type a message in the input field and press Enter or click Send. Use Shift + Enter to add a new line without sending.

### Uploading a resume
Click the upload icon to attach a resume file (`.pdf`, `.docx`, or `.txt`). The file preview will appear above the input field. You can remove it by clicking the ✕ on the tag.

### Expected Behaviour
| Input | Output |
|---|---|
| Message only, no file | General AI response |
| File only, no message | Skill gap analysis (default) |
| File + "find my skill gaps" | Skill gap analysis filtered by user context |
| File + "summarise my resume" | Resume summary |
| File + any other question | AI answers using resume as context |

## API/Function Reference
### API Endpoints

#### 1. `POST /chat`

The backend exposes a single endpoint that handles all chat interactions.

##### Request body (JSON):
```json
{
  "message": "find my skill gaps focusing on cloud skills",
  "file_text": "extracted plain text content of the uploaded resume"
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
|`message` | `string` | No | The user's message or instruction |
| `file_text` |	`string` | No | Plain text extracted from the uploaded resume |


##### Response (JSON):
```json
{
  "reply": "Based on your resume, here are your skill gaps:\n\n• aws\n• azure\n• kubernetes"
}
```

#### 2. `GET /`
The frontend exposes a GET endpoint that serves the chat page.

- **Request**: No body — standard browser GET request
- **Response**: HTML page rendered by Jinja2 from `chat_page.html`, with `BACKEND_URL` injected as a template variable


### Key Backend Functions
| Function | Description |
| --- | --- |
| `detect_task()` | Detect what the user wants to do with file attached based on their input message
| `summarise_resume()` | Generate a summary of the resume attached by user using the model configured in `.env`

### Key Frontend Functions
| Function | Description |
| --- | --- |
| `sendMessage()` | Extracts file text, sends JSON request to backend, renders response
| `extractFileText(file)` | Extracts text from PDF using PDF.js, or reads `.txt`/`.docx` as plain text
| `appendMessage(role, text, fileNames)` | Renders a chat bubble in the chat history
| `renderFilePreview()` | Shows attached file tags above the input field
| `removeFile(index)` | Removes an attached file from the preview

### Frontend/Backend Communication over Docker
The frontend and backend run as separate containers on a shared Docker bridge network named `week3-network`. Within this network, each service is reachable by its service name as a hostname.

However, the `POST /chat` fetch request is made by the browser (via JavaScript), not by the frontend container itself. Because the browser runs on the host machine and not inside Docker, it cannot resolve internal Docker hostnames like `backend`. Instead, the browser reaches the backend through Docker's port mapping:

```
Browser → http://localhost:8001/chat → Docker port mapping → backend container (port 8001)
```

This is why `BACKEND_URL=http://localhost:8001` is used in `.env` rather than `http://backend:8001`. The internal Docker hostname would only be relevant if the frontend Python code was making server-side requests to the backend.


## Data/Assumptions
### JSON Message Structure
All communication between the frontend and backend uses JSON over HTTP. The request and response structures are:

#### Request (`POST /chat`):
```json
{
  "message": "string → the user's typed input, can be empty if file is attached",
  "file_text": "string → plain text extracted from the uploaded file, empty if no file"
}
```

#### Response
```json
{
  "reply": "string → the chatbot's response, always present"
}
```


### Assumptions
| Assumption | Detail |
|---|---|
| **File format** | Uploaded files are expected to be `.pdf`, `.docx`, or `.txt`. Other formats are not supported and may return empty text |
| **PDF type** | PDFs must be text-based. Scanned or image-based PDFs will produce little to no extracted text since PDF.js cannot perform OCR |
| **File size** | No strict file size limit is enforced, but very large files may cause slow text extraction in the browser or slow model processing on the backend |
| **Message length** | No hard limit on message length, but very long inputs may exceed the model's context window and produce degraded responses |
| **Multiple files** | Multiple files can be attached to the preview, but only the first file is processed and sent to the backend. Subsequent files are ignored. |
| **Database populated** | The `tech_stack` column in the job database must already be populated before running the application. Skill gap analysis depends entirely on this data |
| **Ollama running** | When using local models, Ollama must be running on the host machine before starting the containers. The backend will fail to generate responses if Ollama is unreachable |
| **Stateless requests** | Each request is independent. The backend has no memory of previous messages, so context from earlier in a conversation is not carried forward |

### Data Flow
1. User types a message and optionally attaches a resume file.
2. On send, the frontend extracts text from the file (PDF.js for PDFs).
3. Frontend sends a `POST /chat` request with `{ message, file_text }` as JSON.
4. Backend receives the request and detects intent (task to do):
    - No file → general chat via `prompt_model()`
    - File + skill gap intent → `find_skill_gaps()` against job database
    - File + summary intent → `summarise_resume()` via `prompt_model()`
    - File + other → `prompt_model()` with resume as context
5. Backend returns `{ reply }` as JSON.
6. Frontend renders the reply as a chat bubble.


## Testing
### Frontend test cases

| Test | Steps | Expected |
|---|---|---|
| Send text only | Type "hello" and press Enter | General AI response appears |
| Send file only | Attach a PDF, click Send | Skill gap list returned |
| Send file + context | Attach PDF, type "focus on cloud skills" | Filtered skill gap list |
| Send file + summary | Attach PDF, type "summarise my resume" | Resume summary returned |
| Remove attached file | Click ✕ on file tag | File removed, send button hides if no text |
| Shift+Enter | Press Shift+Enter in textarea | New line added, message not sent |

### Backend test cases (curl)

```bash
# General chat
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "file_text": ""}'

# Skill gap analysis
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "find my skill gaps", "file_text": "Python developer with Django and PostgreSQL experience"}'

# Resume summary
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "summarise my resume", "file_text": "Python developer with Django and PostgreSQL experience"}'
```

### Verifying Frontend/Backend Communication in Docker

To confirm both containers are running and communicating correctly:

1. Run `docker compose ps` — both `frontend-1` and `backend-1` should show status `Up`

2. Test the backend directly from your machine:
    ```bash
    curl -X POST http://localhost:8001/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "hello", "file_text": ""}'
    ```
   A valid JSON response confirms the backend container is reachable via port mapping.

3. Open `http://localhost:8000` in your browser and send a message — if a response appears, the full frontend → backend flow is working correctly over Docker.

4. To inspect container logs for errors:
    ```bash
    docker compose logs frontend
    docker compose logs backend
    ```


## Limitations

- **No chat memory:** Each message is stateless. If a resume is uploaded and analysed, a follow-up question in the next message will not have access to the previous context unless the file is attached again.
- **No persistent chat history:** Refreshing the browser resets all messages. Chat is not saved to any database.
- **Basic jailbreak protection:** The resume text is checked for common injection patterns before processing, but sophisticated adversarial inputs may still bypass the checks.
- **PDF text extraction quality:** PDF.js extracts text from text-based PDFs reliably, but scanned or image-based PDFs will return little to no text.
- **Single file per message:** Only one resume file can be processed per message.


## Architecture Reflection

- **Design Choices**
    
    Why you chose a microservices architecture (frontend/backend separation). Explain the benefits of containerizing each service with Docker.

    _Answer_:

    **Frontend/backend separation** was chosen to ensure modularity and loose coupling between the two services. With separate codebases, each service manages its own dependencies, logic, and configuration independently. This reduces complexity during development, makes debugging easier by isolating issues to one layer, and improves security by ensuring the frontend never has direct access to the database or AI model.

    **Containerising with Docker** solves the "it works on my machine" problem. By packaging each service with its exact Python version, dependencies, and configuration into an image, the application runs identically on any machine with Docker installed — whether that's a teammate's laptop or a cloud server. Docker Compose adds orchestration on top, allowing both services to be started with a single command while sharing a private network.
    
- **Trade-offs**
    
    What you chose to prioritize (e.g., ease of deployment with Docker Compose vs. performance, simplicity of the chat interface vs. advanced features).

    _Answer_:

    **Docker Compose vs performance:** Docker Compose prioritises ease of deployment and local development over raw performance. A production system would use an orchestrator like Kubernetes for load balancing and scaling, but Compose is far simpler for a project of this scope.

    **Simplicity vs features:** The chat interface is intentionally minimal — no authentication, no persistent history, no multi-turn memory. This kept development focused on the core integration between the frontend, backend, and AI pipeline, which was the primary objective of the week.

    **Client-side PDF parsing:** Extracting PDF text in the browser using PDF.js keeps the backend stateless and avoids file uploads, which aligns with the JSON-only API design. The trade-off is that complex or scanned PDFs may not parse well on the frontend.
    
- **Improvements**
    
    What you would change or extend if given more time (e.g., using a more robust frontend framework, adding a database to store chat history, deploying the application to the cloud).

    _Answer_:

    - **Chat memory:** Maintain conversation history per session so follow-up questions don't require re-uploading the resume
    - **Persistent chat history:** Store conversations in a database so users can revisit previous sessions
    - **Enhanced jailbreak protection:** Implement more robust input sanitisation and prompt hardening
    - **Model selection UI:** Allow users to select their preferred AI model directly from the interface without editing code
    - **Streaming responses:** Stream the model's output token by token for a more responsive chat experience