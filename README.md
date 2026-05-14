# Help Desk Ticket Viewer

A minimal help desk interface with AI-powered ticket summaries.

- **Backend**: FastAPI + PostgreSQL (async SQLAlchemy + asyncpg)
- **Frontend**: React + TypeScript + Vite
- **AI**: Server-Sent Events streaming via OpenAI-compatible API (`unsloth/Qwen3.5-9B`)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Database setup + seed (run once)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
# I seeded db while testing, do not know if you are going to clean in or not.
python scripts/seed_db.py 
```

### 2. Start both servers

**Terminal 1 — backend (with venv activated):**

```bash
cd backend
.venv\Scripts\activate   # or: source .venv/bin/activate
uvicorn app.main:app --reload
# runs on http://localhost:8000
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm install
npm run dev
# runs on http://localhost:5173
```

Open **http://localhost:5173** in your browser.

> Alternatively, use the provided `start.ps1` (Windows) or `start.sh` (Unix) to launch both with a single command.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tickets` | List all tickets (optional `?status=open\|in_progress\|resolved`) |
| GET | `/api/tickets/{id}` | Single ticket |
| GET | `/api/tickets/{id}/summary` | Stream AI summary via SSE |
| GET | `/health` | Health check |

---

## Discussion Questions

### 1. AI Dev Stack

**Claude Code** (model: `claude-sonnet-4-6`) was used as a development assistant throughout — helping think through architecture decisions, accelerating boilerplate, debugging issues (e.g. diagnosing Qwen3's thinking mode from raw stream inspection, tracking down the Windows asyncio/asyncpg incompatibility), and looking up API behaviour I wasn't certain about.

The help desk LLM feature uses **`unsloth/Qwen3.5-9B`** — the model served by the provided API endpoint.

---

### 2. API Discovery: How I found the model name

I hit the standard OpenAI-compatible models endpoint: `GET /v1/models`. It came back with a single entry — `unsloth/Qwen3.5-9B`.

From there I ran a quick test with `stream: true` via the `openai` Python SDK (pointing `base_url` at the provided API). That's when I noticed something odd: the model was producing hundreds of tokens but none of them were showing up as readable content. After logging the raw chunks I could see that everything was landing in `delta.reasoning_content` — the model's internal chain-of-thought — while `delta.content` stayed `null`.

It turned out Qwen3 defaults to "thinking mode", where it reasons through a problem internally before writing the final answer. For a streaming summary widget that's not useful behaviour — the user would just stare at a blank screen while the model thinks. Disabling it was a one-liner: `extra_body={"chat_template_kwargs": {"enable_thinking": False}}`. With that in place, tokens came through on `delta.content` immediately as expected.

---

### 3. Streaming Architecture

When the user clicks "Generate Summary", the browser opens a native `EventSource` connection to `GET /api/tickets/{id}/summary`. FastAPI handles that with a `StreamingResponse` using `text/event-stream` as the media type, backed by an async generator.

Inside the generator, the backend fetches the ticket from PostgreSQL and then opens a streaming request to the LLM API using the `AsyncOpenAI` client with `stream=True`. Each token chunk that comes back gets immediately forwarded to the browser as an SSE frame: `data: {"content": "token"}\n\n`. The browser's `onmessage` handler appends each token to React state, so the text appears word by word as it arrives. When the LLM finishes, the backend sends `data: [DONE]\n\n` and the frontend closes the connection.

A few edge cases worth noting: if the LLM is slow to start, the HTTP connection stays open and the user sees a pulsing "Connecting to AI…" indicator. If the stream drops mid-way, the `async for` raises and the generator sends an error frame before exiting — the frontend also has an `onerror` handler as a second safety net. If the user closes the tab, the ASGI server cancels the async generator, which cancels the upstream request too, so there's no resource leak.

---

### 4. Database Schema

```sql
CREATE TABLE tickets (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(255)  NOT NULL,
    description TEXT          NOT NULL,
    status      VARCHAR(20)   NOT NULL DEFAULT 'open',
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT tickets_status_check
        CHECK (status IN ('open', 'in_progress', 'resolved'))
);
```

I used `TIMESTAMPTZ` throughout rather than plain `TIMESTAMP` — storing timezone-aware timestamps means the values are unambiguous regardless of where the server runs. The `status` constraint lives at the database level as the primary enforcement point, with Pydantic as a secondary check in the API layer.

For a production system handling thousands of tickets with full-text search I'd add a few things:

- A GIN index on a generated `tsvector` column for fast full-text search:
  ```sql
  ALTER TABLE tickets ADD COLUMN search_vector tsvector
      GENERATED ALWAYS AS (
          to_tsvector('english', title || ' ' || description)
      ) STORED;
  CREATE INDEX tickets_fts_idx ON tickets USING GIN(search_vector);
  ```
- B-tree indexes on `status` (for the filter query) and `created_at` (for sorting)
- Keyset pagination (`WHERE created_at < $cursor ORDER BY created_at DESC LIMIT 20`) instead of `OFFSET` — `OFFSET` gets expensive fast because Postgres still has to scan and discard all the skipped rows
- Range partitioning by `created_at` if the table grows into the millions

---

### 5. Credentials Handling

Credentials are in a `.env` file loaded by `pydantic-settings`. The file is listed in `.gitignore` — only `.env.example` with placeholder values is committed.

In production I'd handle this differently:

- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, or the platform's native secret injection for something like Railway or Render) rather than `.env` files on disk
- Inject secrets at runtime, not baked into image layers
- Rotate the LLM API key and database password on a schedule
- Give the application a dedicated database user with only the privileges it actually needs, rather than a superuser
- Keep the database off the public internet entirely — the backend should be the only thing that can reach it, ideally over a private network

---

### 6. Tradeoffs

Things I skipped due to time:

- Authentication / authorization (the API is fully open)
- Ticket CRUD — create, update, delete (currently read-only)
- Pagination (all tickets returned in one response)
- Full-text search
- Real-time updates (new tickets don't appear without a page refresh)
- Ticket comments or attachments
- Docker / Docker Compose setup
- Tests

If I had another three hours, I'd prioritise in this order:

1. **Pagination** — `LIMIT/OFFSET` to start, keyset later. Without it, the ticket list will break the moment someone adds real data.
2. **Create ticket** — a simple form so reviewers can add their own test data without touching the database directly.
3. **Docker Compose** — so the backend runs in a container with the right Python version rather than depending on the reviewer's local setup.

---

### 7. Time Spent

Approximately 3 hours total.

Two things took longer than I expected. First, the SSE path — making sure backpressure propagated correctly through FastAPI's `StreamingResponse`, and that the Vite dev proxy wasn't buffering frames. Second, discovering the Qwen3 thinking mode issue: the model was producing hundreds of tokens that were completely invisible to the user. I had to log the raw chunk objects to see they were landing in `delta.reasoning_content` rather than `delta.content` — the fix was simple once I understood what was happening.

While waiting for the provided database to become accessible, I ran the full stack locally against a native PostgreSQL instance, which also let me catch and fix a Windows-specific asyncpg issue (asyncpg requires `WindowsSelectorEventLoopPolicy` on Windows rather than the default ProactorEventLoop).
