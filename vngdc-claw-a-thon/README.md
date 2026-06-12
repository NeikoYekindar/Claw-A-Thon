# code-log-analyst

A GreenNode AgentBase agent specializing in code analysis and log analysis.

## Prerequisites

- Python 3.10+
- A GreenNode IAM Service Account ([create one here](https://iam.console.vngcloud.vn/service-accounts))

## Setup

1. Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell):
   python -m venv venv; venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Configure LLM

Set the following in `.env`:

```
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1
LLM_MODEL=your-model-name
MEMORY_ID=your-memory-id
```

## Run Locally

```bash
python main.py
```

Test it (memory requires both headers):
```bash
curl -X POST http://127.0.0.1:8080/invocations \
  -H "Content-Type: application/json" \
  -H "X-GreenNode-AgentBase-User-Id: test-user" \
  -H "X-GreenNode-AgentBase-Session-Id: test-session-1" \
  -d '{"message": "Analyze this log: ERROR NullPointerException at line 42"}'
```

Health check:
```bash
curl http://127.0.0.1:8080/health
```

## Project Structure

- `main.py` - Agent entrypoint with code & log analysis logic
- `Dockerfile` - Container image definition
- `requirements.txt` - Python dependencies
- `.greennode.json` - AgentBase configuration
- `.env.example` - Environment variable template
