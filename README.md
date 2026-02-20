# Knowledge-to-Action Search System

Multi-tenant enterprise search for sales training data. Enforces strict company/user-level data isolation via Pinecone metadata pre-filtering.

**Stack:** FastAPI + LangChain + OpenAI (GPT-4o-mini) + OpenAI embeddings + Pinecone | React + TypeScript + Vite + Tailwind CSS

---

## Project Overview

This is a secure, multi-tenant Generative Search Engine that allows Sales Representatives to retrieve specific data from their assigned knowledge base and personal performance history. The system implements strict data isolation, intent-driven retrieval, and a three-tier guardrail system to prevent hallucinations and out-of-scope queries.

### Key Features

- **Multi-Tenant Security**: Company and user-level data isolation with JWT authentication
- **Intent Classification**: Three-tier response system (grounded, general knowledge, out-of-scope)
- **RAG Pipeline**: Vector search with Pinecone + LLM generation with citations
- **Streaming Responses**: Token-by-token answer streaming for better UX
- **Rich Citations**: Deep-linked citations (PDF pages, video timestamps)
- **Recommendation Engine**: Suggests 2-3 relevant follow-up contents after each query
- **Assignment-Based Access**: Users only see content from their assigned plays

---

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- API Keys:
  - OpenAI API key (for embeddings and LLM)
  - Pinecone API key (for vector database)
  - Anthropic API key (optional, if using Claude)

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd search-agent-master
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

**Required `.env` variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
PINECONE_API_KEY=pcsk-your-key-here
PINECONE_INDEX_NAME=search-agent-index
PINECONE_ENVIRONMENT=us-east-1-aws

JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
DEMO_PASSWORD=demo1234

# DATA_DIR defaults to <project_root>/searchAgent
MODEL=gpt-4o-mini  # or claude-sonnet-4-6
EMBEDDING_MODEL=text-embedding-3-large
```

### 3. Data Ingestion (One-Time)

Ensure the `searchAgent` folder with `database/` and `assets/` is in your project root, then:

```bash
python -m backend.ingestion.run_ingestion
```

**Expected output:** ~268 vectors uploaded to Pinecone (148 knowledge + 120 submissions)

### 4. Start Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 5. Start Frontend

```bash
cd frontend
npm install

# Create frontend/.env
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

npm run dev
```

Frontend available at: http://localhost:5173

---

## Authentication

All demo users share the password: **`demo1234`**

**Example usernames:**
- `aaron-veldra` (Veldra Therapeutics)
- `frank-hexaloom` (Hexaloom Nanoworks)
- `alice-veldra` (Veldra Therapeutics)
- `daphne-kyberon` (Kyberon Cloud)

---

## Demo Test Cases

### 1. Cross-Company Isolation
```
Login: aaron-veldra (Veldra company)
Query: "What is Hexenon?"
Expected: Tier 3 response - out of scope (Hexaloom product)
```

### 2. Grounded Knowledge Search
```
Login: aaron-veldra
Query: "What is the eradication rate for Streptococcus pneumoniae?"
Expected: "94.2%" with citation [amproxin_guide.pdf: Page X]
```

### 3. General Professional Knowledge
```
Login: any user
Query: "How do I handle price objections?"
Expected: Tier 2 response with disclaimer "based on general sales knowledge"
```

### 4. Out-of-Scope Guardrail
```
Login: any user
Query: "Tell me a joke"
Expected: Tier 3 response - "specialized search engine for assigned materials"
```

### 5. Personal Submission Search
```
Login: daphne-kyberon
Query: "What did I say about GridMaster?"
Expected: Results from user's own submissions only
```

### 6. Assignment-Based Access
```
Login: aaron-veldra (assigned to Amproxin play)
Query: "How does Lydrenex protect the amygdala?" (Nuvia play - not assigned)
Expected: No results found
```

---

## Architecture

### Backend Structure
```
backend/
├── api/              # FastAPI routes (auth, search)
├── core/             # Security, data store, LLM factory
├── models/           # Pydantic schemas
├── pipeline/         # Intent → Retrieve → Generate → Recommend
├── ingestion/        # Data loading & vector upsertion
└── main.py           # FastAPI app entry point
```

### Frontend Structure
```
frontend/src/
├── api/              # API client & search service
├── components/       # React components (auth, search)
├── hooks/            # Custom hooks (useAuth, useSearch)
├── store/            # Zustand state management
└── types/            # TypeScript interfaces
```

### Security Model

| Layer | Mechanism |
|-------|-----------|
| Company isolation | `company_id` always in Pinecone pre-filter |
| Assignment fence | `play_id $in assigned_play_ids` (server-side) |
| User isolation | `user_id $eq ctx.user_id` for submissions |
| JWT | `company_id` always read from JWT, never request body |

### Three-Tier Response System

1. **Tier 1 (Grounded)**: Query matches assigned knowledge/submissions → answer with citations
2. **Tier 2 (General)**: Professional query but no grounding → LLM knowledge with disclaimer
3. **Tier 3 (Out-of-Scope)**: Non-professional query → boundary guardrail message

---

## Technology Stack

**Backend:**
- FastAPI (web framework)
- LangChain (LLM orchestration)
- OpenAI GPT-4o-mini (LLM generation)
- OpenAI text-embedding-3-large (embeddings)
- Pinecone (vector database)
- PyJWT (authentication)
- Pydantic (validation)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Zustand (state management)
- Axios (HTTP client)

**Testing:**
- Pytest (backend unit tests)
- Playwright (E2E tests)

---

## Running Tests

### Backend Tests
```bash
pytest tests/
```

### E2E Tests
```bash
cd e2e
npm install
npx playwright test
```

---

## Project Highlights

### Implemented (Core Requirements)
- Multi-tenant architecture with strict data isolation
- JWT-based authentication with company_id enforcement
- Intent classification with three-tier guardrail system
- RAG pipeline with Pinecone vector search
- Streaming responses with rich citations
- Recommendation engine
- Assignment-based access control
- Cross-company and cross-user security tests


---

