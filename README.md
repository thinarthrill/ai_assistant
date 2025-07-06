# 🧠 LLM API Stack — FastAPI + LangChain + OpenAI + Auth

This repository provides a modular stack to deploy LLM-powered assistants via secure API endpoints, using FastAPI, LangChain, OpenAI, and retrieval-based question answering.

---

## 📁 Components Overview

### 1. `api_llm.py` — FastAPI Application

A production-ready FastAPI app exposing secure endpoints for:

* `/openai` — General knowledge assistant (uses `functions.py`)
* `/qazpmichapter` — PMI Kazakhstan assistant (uses `qazpmichapterfunctions.py`)
* `/upload_file`, `/openai_image`, `/openai_whisper` — optional endpoints for file/image/voice processing

🔐 Token-based signature verification is used for authentication.

### 2. `functions.py` — Igor Volnukhin’s Personal AI Assistant

Uses a private knowledge base (from `igorvolnukhinai_kb.txt`) and:

* LangChain’s `MarkdownHeaderTextSplitter`
* FAISS vector store for semantic search
* ChatOpenAI model with strict instruction: act as Igor’s digital twin

### 3. `qazpmichapterfunctions.py` — PMI Kazakhstan Chapter Assistant

Based on a document (`qazpmichapter_kb.txt`) converted to structured markdown, it creates a QA system with:

* GPT-4.1-mini
* Official-style system prompt: always act as a PMI representative
* Returns accurate, relevant, and professional answers based on internal knowledge

---

## 🔐 Authentication

API requests must include:

* `client_id`
* `signature` — HMAC-SHA256 of request body (excluding `signature`) using the shared token

Tokens are defined in `AUTHORIZED_TOKENS` in `api_llm.py`.

---

## ⚙️ Technologies

* Python 3.11+
* FastAPI
* LangChain
* OpenAI (GPT-4.1-mini)
* FAISS
* dotenv
* PRAW (for Reddit, if extended)

---

## 🧪 How to Run

```bash
uvicorn api_llm:llm --reload
```

---

## 📬 Example Request (POST /openai)

```json
{
  "client_id": "client_1",
  "signature": "<calculated_signature>",
  "query": "Расскажи про мой опыт управления ИТ-проектами"
}
```

---

## 📌 Notes

* Update `.env` with OpenAI keys and tokens
* Modify knowledge base files for other assistants
* Adjust LangChain prompt templates for tone or use case

---

## 👤 Author

Developed by **Igor Volnukhin** — combining AI, APIs, and knowledge retrieval for practical assistant use cases.
