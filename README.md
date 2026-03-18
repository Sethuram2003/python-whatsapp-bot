# 🤖 AI WhatsApp Bot

A production-ready AI-powered WhatsApp bot built with **FastAPI**, **LangGraph**, and **MCP (Model Context Protocol)**. Supports text and image messages, tool-calling agents, and a pluggable MCP server architecture — all containerized with Docker.

---

## ✨ Features

- 📨 **Receive & respond to WhatsApp messages** via Meta Cloud API webhooks
- 🧠 **Agentic AI responses** powered by LangGraph + LangChain (Ollama / Groq models)
- 🖼️ **Image understanding** — downloads, summarizes, and responds to image messages
- 🔧 **MCP tool support** — extensible via the included `SimpleMcp` server (time, random, math) or external MCP servers (e.g. Tavily web search)
- 🔒 **Webhook security** — SHA-256 signature validation on all incoming payloads
- 🐳 **Fully Dockerized** — FastAPI bot + MCP server run as separate services via Docker Compose
- 💬 **Conversation memory** — per-user thread state via LangGraph `InMemorySaver`

---

## 🏗️ Architecture

```
WhatsApp User
     │  (HTTPS)
     ▼
Meta Cloud API
     │  Webhook POST
     ▼
┌─────────────────────────┐
│   FastAPI App (:8000)   │
│                         │
│  POST /webhook          │
│   ├── Verify signature  │
│   ├── Parse message     │
│   │    ├── text         │
│   │    └── image → summarize (Ollama)
│   └── LangGraph Agent   │
│        ├── Groq/Ollama LLM
│        └── MCP Tools ──►│
└─────────────────────────┘
          │ SSE/HTTP
          ▼
┌─────────────────────────┐
│  SimpleMcp Server (:8001)│
│  Tools:                 │
│   • get_current_time    │
│   • add_numbers         │
│   • random_number       │
└─────────────────────────┘
```

---

## 📁 Project Structure

```
├── app/
│   ├── main.py                  # FastAPI entrypoint
│   ├── api/routes/
│   │   └── webhook.py           # GET (verification) + POST (messages)
│   └── core/
│       ├── config.py            # Pydantic settings from .env
│       ├── dependencies.py      # Signature verification dependency
│       ├── LangAgent.py         # LangGraph agent factory (chat + image)
│       ├── prompt.py            # System prompts
│       └── WhatsApp.py          # Message processing & Meta API calls
├── McpServers/
│   └── SimpleMcp/
│       ├── main.py              # FastMCP server with utility tools
│       ├── auth.py              # API key middleware
│       └── Dockerfile
├── docker/fastapi/Dockerfile
├── compose.yaml
└── example.env
```

---

## 🚀 Quick Start

### Prerequisites

- [Docker & Docker Compose](https://docs.docker.com/get-docker/)
- A [Meta Developer account](https://developers.facebook.com/) with a WhatsApp Business App
- [ngrok](https://ngrok.com/) (for local development)

---

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd sethuram2003-python-whatsapp-bot
```

Copy the example environment file and fill in your credentials:

```bash
cp example.env .env
```

```env
# .env
ACCESS_TOKEN=""          # Meta API access token (24h or system user token)
APP_ID=""                # Meta App ID
APP_SECRET=""            # Meta App Secret (used for webhook signature verification)
RECIPIENT_WAID=""        # Your WhatsApp number with country code (e.g. +91XXXXXXXXXX)
VERSION="v18.0"          # Meta Graph API version
PHONE_NUMBER_ID=""       # WhatsApp Business phone number ID
VERIFY_TOKEN=""          # Any string you choose — used for webhook verification
```

Create the MCP server env file:

```bash
cp McpServers/SimpleMcp/.env.example McpServers/SimpleMcp/.env  # or create manually
```

```env
# McpServers/SimpleMcp/.env
API_KEY="your-secret-key"
```

---

### 2. Run with Docker Compose

```bash
docker compose up --build
```

| Service    | Port   | Description              |
|------------|--------|--------------------------|
| `fastapi`  | `8000` | Main WhatsApp bot API    |
| `simplemcp`| `8001` | MCP utility tool server  |

---

### 3. Expose with ngrok

> Meta requires a publicly accessible HTTPS URL with a static domain.

```bash
ngrok http 8000 --domain your-domain.ngrok-free.app
```

---

### 4. Configure the Meta Webhook

1. Go to your [Meta App Dashboard](https://developers.facebook.com/apps/) → **WhatsApp → Configuration**
2. Set **Callback URL** to: `https://your-domain.ngrok-free.app/webhook`
3. Set **Verify Token** to the same value as `VERIFY_TOKEN` in your `.env`
4. Click **Verify and Save** — your app should log `WEBHOOK_VERIFIED`
5. Click **Manage** → Subscribe to the **messages** field

---

## 🔐 Webhook Security

Every incoming POST request is authenticated using **HMAC SHA-256 signature verification**:

1. Meta signs each payload with your `APP_SECRET` and includes it in the `X-Hub-Signature-256` header
2. The `verify_signature` dependency in `dependencies.py` recomputes the signature and compares it
3. Requests with missing or mismatched signatures are rejected with `HTTP 403`

---

## 🤖 AI Agent

The bot uses a **LangGraph ReAct agent** with:

| Component        | Default             | Purpose                        |
|------------------|---------------------|--------------------------------|
| Chat LLM         | `kimi-k2:1t-cloud` (Ollama) | Main conversational agent |
| Vision LLM       | `qwen3.5:397b-cloud` (Ollama) | Image summarization      |
| Web Search       | Tavily MCP (`npx tavily-mcp`) | Live web search          |
| Local Tools      | `SimpleMcp` server  | Time, math, random numbers     |
| Memory           | `InMemorySaver`     | Per-user thread conversation   |

To swap models, update `LangAgent.py`:

```python
# Use Groq instead of Ollama
from langchain_groq import ChatGroq
llm = ChatGroq(model="llama-3.3-70b-versatile")
```

---

## 🔧 SimpleMcp Server

The included MCP server provides basic utility tools secured by an API key header (`X-API-Key`).

| Tool              | Description                          |
|-------------------|--------------------------------------|
| `get_current_time`| Returns current date and time        |
| `add_numbers`     | Adds two integers                    |
| `random_number`   | Returns random int in a given range  |

The server runs on `streamable-http` transport at port `8001`. To add new tools:

```python
# McpServers/SimpleMcp/main.py
@mcp.tool()
async def my_tool(input: str) -> str:
    """Description of what this tool does."""
    return result
```

---

## 📬 Supported Message Types

| Type    | Handling                                                     |
|---------|--------------------------------------------------------------|
| `text`  | Passed directly to the LangGraph agent                       |
| `image` | Downloaded from Meta API → base64 encoded → summarized by vision LLM → summary passed to agent |
| Other   | Unsupported type is noted in the agent's context             |

---

## 🛠️ Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal, run the MCP server
cd McpServers/SimpleMcp
python main.py
```

---

## ☁️ Deploying to Production

Build and push the image:

```bash
# For AMD64 (most cloud providers)
docker build --platform=linux/amd64 -t your-registry/whatsapp-bot .
docker push your-registry/whatsapp-bot
```

For a long-lived Meta access token (beyond 24 hours):

1. Create a [System User](https://business.facebook.com/settings/system-users) in Meta Business Settings
2. Assign your WhatsApp app with full control
3. Generate a token with **60-day** or **never-expire** validity
4. Select all permissions to avoid API errors

---

## 📋 Environment Variable Reference

| Variable          | Required | Description                                          |
|-------------------|----------|------------------------------------------------------|
| `ACCESS_TOKEN`    | ✅       | Meta API Bearer token for sending messages           |
| `APP_ID`          | ✅       | Your Meta App ID                                     |
| `APP_SECRET`      | ✅       | Your Meta App Secret (for signature verification)    |
| `RECIPIENT_WAID`  | ✅       | Your WhatsApp number with country code               |
| `VERSION`         | ✅       | Meta Graph API version (e.g. `v18.0`)                |
| `PHONE_NUMBER_ID` | ✅       | WhatsApp Business phone number ID                    |
| `VERIFY_TOKEN`    | ✅       | Custom string for webhook verification               |

---

## 📄 License

MIT License — see [LICENCE.txt](./LICENCE.txt)

---

## 🙏 Credits

Based on the original guide by [Datalumina](https://www.datalumina.com/) / [@daveebbelaar](https://www.youtube.com/@daveebbelaar).
Extended with LangGraph agents, MCP tool integration, image understanding, and Docker Compose orchestration.
