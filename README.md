# LIYANA-pro-API-v2

Production-oriented FastAPI backend for Liyana 3.0. It provides an Android-friendly `POST /chat` endpoint and calls Ollama Cloud's official chat API using Python `requests`.

## Requirements

- Python 3.10 or newer
- An Ollama API key with cloud API access

The default model is `beam:cloud`. Ollama's official model library currently lists this cloud model, but account access and availability may vary. Set `OLLAMA_MODEL` to another model available to your Ollama account when needed.

## Local setup

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set the API key through the environment; the application reads it only from `OLLAMA_API_KEY` and never includes it in a response or log:

```bash
# macOS/Linux
export OLLAMA_API_KEY="your_ollama_api_key"
# Optional overrides
export OLLAMA_MODEL="beam:cloud"
export PORT="8000"
```

PowerShell equivalent:

```powershell
$env:OLLAMA_API_KEY = "your_ollama_api_key"
$env:OLLAMA_MODEL = "beam:cloud"
$env:PORT = "8000"
```

Run locally:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Interactive API documentation is available at `/docs` while the server is running.

## API

### `GET /health`

Returns `{"status":"ok"}` and does not check or expose credentials.

### `POST /chat`

Preferred conversation format:

```json
{
  "messages": [
    {"role": "system", "content": "You are Liyana, a helpful assistant."},
    {"role": "user", "content": "Hello"}
  ]
}
```

Roles supported are `system`, `user`, and `assistant`. For older clients, a single `message` string is accepted and treated as a user message:

```json
{"message": "Hello"}
```

Successful responses use the Android-compatible format:

```json
{"response": "Hello! How can I help?"}
```

Invalid request bodies return `422`; missing server-side API configuration returns `503`; Ollama request timeouts return `504`; upstream connection, API, and malformed-response failures return `502`. Error responses do not include the Ollama response body.

## Render deployment

1. Create a new **Web Service** in Render and select this project directory as its root directory if deploying from a larger repository.
2. Set **Build Command** to `pip install -r requirements.txt`.
3. Set **Start Command** to `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Add `OLLAMA_API_KEY` in the Render service's **Environment** settings. Store the real key there as a secret; do not add it to source control or README files.
5. Optionally set `OLLAMA_MODEL` to a cloud model available to your account. If omitted, it defaults to `beam:cloud`.
6. Deploy the service. Render provides `PORT`; the start command binds Uvicorn to it. Check the deployment at `/health` and use `/docs` to inspect the API.

The service uses HTTPS to call `https://ollama.com/api/chat` with `Authorization: Bearer $OLLAMA_API_KEY` and a non-streaming JSON request.
