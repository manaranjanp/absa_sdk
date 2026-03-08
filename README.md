# ABSA Agent System

A multi-agent **Aspect-Based Sentiment Analysis** pipeline for restaurant reviews, built with [Google ADK](https://google.github.io/adk-docs/) (Agent Development Kit) and [LiteLLM](https://docs.litellm.ai/) for multi-provider LLM support.

## What It Does

The system processes customer reviews through a **7-stage sequential pipeline**:

1. **Toxicity Detection** — Screens reviews for toxic/abusive content; toxic reviews are terminated with no response
2. **Aspect Extraction** — Identifies aspects (food quality, service, ambiance, cleanliness) from a canonical taxonomy
3. **Sentiment Analysis** — Classifies sentiment per aspect (VERY_POSITIVE → VERY_NEGATIVE)
4. **Sentiment Aggregation** — Updates running EWMA scores per restaurant per aspect in SQLite
5. **Policy Evaluation & Escalation** — Checks operational alert rules and creates callback tickets based on customer tier
6. **Response Generation** — Composes a personalized, brand-consistent customer response
7. **Output Guardrail** — Validates the response against configurable quality rules before publishing

---

## Project Structure

```
absa/
├── agents/                  # 7 subagent modules (one per pipeline stage)
├── config/
│   ├── policy_document.json # Operational alerts + tier escalation rules
│   └── output_guardrails.json # Response validation rules
├── data/
│   ├── sample_reviews.json  # 55 sample reviews (various aspects/sentiments)
│   └── brand_voice_guidelines.md
├── db/
│   └── database.py          # SQLite schema and initialization
├── pipeline/
│   └── absa_pipeline.py     # SequentialAgent orchestrator
├── tools/
│   ├── sentiment_db_tools.py # Score update/retrieval functions
│   └── escalation_db_tools.py # Ticket creation/query functions
├── run_pipeline.py           # CLI runner script
├── absa_notebook.ipynb       # Interactive Jupyter notebook
├── observability.py          # LangSmith tracing setup
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (at minimum, one LLM provider)
```

### 3. Run the Pipeline

**Single review:**
```bash
python run_pipeline.py --review '{"review_id":"test1","restaurant_id":"REST-1042","customer_id":"CUST-001","customer_name":"Jane","customer_tier":"Gold","review_text":"The pasta was cold and the service was slow.","review_timestamp":"2026-03-01T12:00:00Z","source_platform":"google_reviews"}'
```

**Random samples from dataset:**
```bash
python run_pipeline.py --sample 3
```

**Full batch from file:**
```bash
python run_pipeline.py --batch data/sample_reviews.json
```

### 4. Interactive Notebook

```bash
jupyter notebook absa_notebook.ipynb
```

---

## Switching LLM Providers

The pipeline supports any LLM accessible through LiteLLM. Use the `--model` flag or set `DEFAULT_MODEL` in `.env`:

| Provider | Model String | Required Env Var |
|----------|-------------|-----------------|
| OpenAI | `openai/gpt-4o` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-3-5-sonnet-20241022` | `ANTHROPIC_API_KEY` |
| Google | `gemini/gemini-2.0-flash` | `GOOGLE_API_KEY` |
| Groq | `groq/llama3-8b-8192` | `GROQ_API_KEY` |
| xAI | `xai/grok-2` | `XAI_API_KEY` |

Example:
```bash
python run_pipeline.py --sample 3 --model anthropic/claude-3-5-sonnet-20241022
```

---

## LangSmith Observability

All LLM interactions are automatically traced to [LangSmith](https://smith.langchain.com/) when configured.

**Setup:**
1. Create a LangSmith account at https://smith.langchain.com/
2. Set in `.env`:
   ```
   LANGSMITH_API_KEY=your-key
   LANGSMITH_PROJECT=absa-agent-pipeline
   LANGSMITH_TRACING=true
   ```
3. Traces appear in the LangSmith dashboard under your project

---

## Configuration

All policy rules, thresholds, and guidelines are externally configurable — no code changes needed.

**`config/policy_document.json`** — Operational alert rules (threshold breaches, trend monitoring) and customer tier escalation rules (Platinum/Gold/Silver/Standard).

**`config/output_guardrails.json`** — Response validation rules with severity levels (CRITICAL blocks publishing, WARNING flags, INFO logs only).

**`data/brand_voice_guidelines.md`** — Brand tone, vocabulary, and response structure guidelines.

---

## Database

The system uses SQLite for lightweight local storage:

**`sentiment_scores` table** — Running EWMA aggregate scores per restaurant per aspect.

**`escalations` table** — Callback tickets with priority, SLA, assigned team, and deduplication logic.

The database file (`absa.db`) is created automatically on first run.

---

## Deployment Guidelines

### Local Development
1. Clone the repository
2. `pip install -r requirements.txt`
3. Copy and configure `.env`
4. Run with `python run_pipeline.py --sample 1`

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "run_pipeline.py", "--batch", "data/sample_reviews.json"]
```

### Production Considerations

**Scaling**: Each subagent can be scaled independently. For high throughput, consider running multiple pipeline instances with a shared database (migrate from SQLite to PostgreSQL).

**Database**: Replace SQLite with PostgreSQL or a managed database service for production workloads. The `db/database.py` module provides a clean abstraction layer for this migration.

**Configuration Management**: Move `config/` files to a centralized configuration service (AWS Parameter Store, HashiCorp Vault, etc.) for multi-environment support with hot-reloading.

**Monitoring**: LangSmith provides LLM-level observability. Add application-level monitoring (Prometheus/Grafana) for pipeline throughput, latency, and error rates.

**Security**: Store API keys in a secrets manager. Enable PII encryption for review data. Implement RBAC for configuration and audit log access.

**CI/CD**: Run the pipeline against a curated test set (`--sample 5`) in CI to catch regressions in agent instructions or model behavior changes.

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | One provider key needed | OpenAI API key |
| `ANTHROPIC_API_KEY` | One provider key needed | Anthropic API key |
| `GOOGLE_API_KEY` | One provider key needed | Google AI API key |
| `XAI_API_KEY` | One provider key needed | xAI/Grok API key |
| `LANGSMITH_API_KEY` | No | LangSmith observability key |
| `LANGSMITH_PROJECT` | No | LangSmith project name |
| `DEFAULT_MODEL` | No | Default LLM model string |
| `DATABASE_PATH` | No | SQLite database file path |
