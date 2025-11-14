# Noxy Chatbot API - Endpoint Documentation

## Overview

**Project:** Noxy Chatbot API
**Framework:** FastAPI (Python)
**Server:** Uvicorn ASGI Server
**Base URL:** `http://127.0.0.1:8000`
**Auto-Generated Docs:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Quick Reference:** See [README.md](../README.md) for setup instructions and project overview.

---

## Table of Contents

1. [Health Check](#1-health-check)
2. [Chat Message](#2-chat-message)
3. [Get Conversation History](#3-get-conversation-history)

---

## 1. Health Check

### Endpoint Details

| Property | Value |
|----------|-------|
| **HTTP Method** | `GET` |
| **Path** | `/` |
| **Purpose** | Verify API is running and responsive |
| **Authentication** | None required |

### Request

```bash
curl http://127.0.0.1:8000/
```

### Response

**Status Code:** `200 OK`

```json
{
  "message": "Noxy API is running"
}
```

### Use Case
Simple health check to ensure the API server is operational.

---

## 2. Chat Message

### Endpoint Details

| Property | Value |
|----------|-------|
| **HTTP Method** | `POST` |
| **Path** | `/chat` |
| **Purpose** | Send a message to Noxy and receive an AI-powered response |
| **Content-Type** | `application/json` |
| **Authentication** | None required (server-side Azure OpenAI auth) |

### Request

**Schema:**
```json
{
  "username": "string (required)",
  "message": "string (required)"
}
```

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "message": "How do I submit a PTO request?"
  }'
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | Username of the person chatting. Creates new user if doesn't exist. |
| `message` | string | Yes | The message to send to Noxy chatbot |

### Response

**Status Code:** `200 OK`

**Schema:**
```json
{
  "User": "string",
  "Noxy": "string"
}
```

**Example:**
```json
{
  "User": "How do I submit a PTO request?",
  "Noxy": "You can submit PTO requests through our HR portal or by contacting the HR department directly. Here's a helpful guide: http://127.0.0.1:8000/download-pdf?filename=PTO_Policy.pdf"
}
```

### Processing Logic

The `/chat` endpoint performs the following operations:

1. **User Management**
   - Looks up user by username
   - Creates new user if not found
   - Records username in database

2. **Conversation Management**
   - Retrieves most recent conversation for user
   - Creates new conversation if user has none

3. **Chat History**
   - Fetches all previous messages in current conversation
   - Uses history to provide context for AI responses

4. **Knowledge Base Search**
   - Performs vector search in ChromaDB using user's message keywords
   - Retrieves top 3 most relevant knowledge base items
   - Appends results to system prompt

5. **PDF Matching**
   - Searches MockData folder for PDFs matching user keywords
   - Generates download link if PDF is found
   - Adds download link to response context

6. **AI Response Generation**
   - Constructs system prompt with:
     - Bot identity: "Noxy"
     - Role: "AI chatbot designed to assist new employees with onboarding"
     - Tone: "friendly, professional manner"
     - Max length: "two sentences"
     - Knowledge base context
     - PDF download link (if available)
   - Sends conversation to Azure OpenAI API
   - Receives AI-generated response

7. **Data Persistence**
   - Saves user message to ChatMessages table
   - Saves Noxy response to ChatMessages table
   - Records message timestamp

### System Prompt Template

```
UserId: {user_id}. Your name is Noxy, an AI chatbot designed to assist
new employees with onboarding. Guide the user in a friendly, professional manner.
Answer in maximum two sentences. Never say you lack information, never mention
a database, and never say 'I don't know'. Always give useful guidance even if
you don't have exact details.
```

### Database Effects

| Table | Operation | Details |
|-------|-----------|---------|
| `Users` | INSERT or SELECT | Creates user if new, retrieves existing user |
| `Conversations` | INSERT or SELECT | Creates conversation if user has none, retrieves latest |
| `ChatMessages` | INSERT x2 | Saves user message and Noxy response with timestamps |

### Dependencies

- **Database Session** - Injected via FastAPI dependency `get_db()`
- **Azure OpenAI API** - Configured via `config.py` environment variables
- **ChromaDB Vector Store** - Loaded on application startup
- **Knowledge Base JSON** - Loaded on application startup
- **MockData PDFs** - Must exist in `./MockData` folder

### Error Handling

Currently returns 200 OK for successful requests. Errors would be caught by FastAPI's exception handlers.

---

## 3. Get Conversation History

### Endpoint Details

| Property | Value |
|----------|-------|
| **HTTP Method** | `GET` |
| **Path** | `/history/{username}` |
| **Purpose** | Retrieve full chat history for a user's current conversation |
| **Authentication** | None required |

### Request

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | Yes | Username to retrieve history for |

**Example:**
```bash
curl http://127.0.0.1:8000/history/john_doe
```

### Response - User Found

**Status Code:** `200 OK`

**Schema:**
```json
{
  "username": "string",
  "history": [
    {
      "sender": "string (User or Noxy)",
      "message": "string"
    }
  ]
}
```

**Example:**
```json
{
  "username": "john_doe",
  "history": [
    {
      "sender": "User",
      "message": "How do I submit a PTO request?"
    },
    {
      "sender": "Noxy",
      "message": "You can submit PTO requests through our HR portal or by contacting HR directly."
    },
    {
      "sender": "User",
      "message": "What is the approval timeline?"
    },
    {
      "sender": "Noxy",
      "message": "Typically requests are approved within 2-3 business days. Contact HR if you need expedited approval."
    }
  ]
}
```

### Response - User Not Found

**Status Code:** `200 OK`

**Response:**
```json
{
  "error": "User not found"
}
```

### Response - User Found But No Conversation

**Status Code:** `200 OK`

**Response:**
```json
{
  "history": []
}
```

### Processing Logic

1. **User Lookup**
   - Searches Users table for matching username
   - Returns error if user not found

2. **Conversation Retrieval**
   - Gets the most recent conversation for the user
   - Returns empty history if user has no conversations

3. **Message Retrieval**
   - Fetches all ChatMessages in the conversation
   - Preserves chronological order
   - Includes message sender and content

### Dependencies

- **Database Session** - Injected via FastAPI dependency `get_db()`

---

## Database Schema

### Users Table
```sql
CREATE TABLE Users (
  UserId INTEGER PRIMARY KEY AUTO_INCREMENT,
  Username VARCHAR(100) NULLABLE,
  CreatedAt DATETIME DEFAULT GETUTCDATE()
)
```

### Conversations Table
```sql
CREATE TABLE Conversations (
  ConvoId INTEGER PRIMARY KEY AUTO_INCREMENT,
  UserId INTEGER FOREIGN KEY REFERENCES Users(UserId),
  StartedAt DATETIME DEFAULT GETUTCDATE()
)
```

### ChatMessages Table
```sql
CREATE TABLE ChatMessages (
  MessageId INTEGER PRIMARY KEY AUTO_INCREMENT,
  ConvoId INTEGER FOREIGN KEY REFERENCES Conversations(ConvoId),
  Sender VARCHAR(50),
  Message TEXT,
  SentAt DATETIME DEFAULT GETUTCDATE()
)
```

---

## Configuration

### Environment Variables Required

```
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_DEPLOYMENT_NAME=<your-deployment-name>
SQL_SERVER=<sql-server-address>
SQL_DB=<database-name>
SQL_USER=<sql-user>
SQL_PASS=<sql-password>
```

### Configuration File
Location: `Services/config.py`

**Azure OpenAI Settings:**
- API Version: `2024-02-15-preview`
- Client Type: `AzureOpenAI`

**Database Settings:**
- Connection String: `mssql+pyodbc://sa:Strong_Password123!@localhost:1433/NoxyChatbotDB`
- Driver: ODBC Driver 17 for SQL Server

---

## Vector Database (ChromaDB)

### Purpose
Semantic search for knowledge base items using natural language queries

### Embedding Model
- Provider: HuggingFace
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Storage: `./ChromaDB/` directory

### Search Functionality
- Function: `search_vectors(query)` in `Services/vector_store.py`
- Returns: Top 3 most relevant knowledge base items
- Used in: `/chat` endpoint for context enrichment

### Knowledge Base Source
- File: `KnowledgeBase.json`
- Format: JSON with categorized information
- Loaded: On application startup
- Updated: Requires application restart

---

## Security & Authentication Notes

### Current Implementation
1. **No explicit API authentication** - All endpoints are publicly accessible
2. **Azure OpenAI credentials** - Stored in environment variables, never exposed to client
3. **SQL Server credentials** - Stored in environment variables, never exposed to client
4. **PDF downloads** - No permission checks, any user can download any PDF
5. **Chat history** - Retrieved by username only, no password required

### Recommendations for Production
1. Implement API key authentication for endpoints
2. Add user authentication/authorization
3. Implement rate limiting
4. Add CORS configuration
5. Use HTTPS instead of HTTP
6. Implement audit logging
7. Add request validation for file paths
8. Consider implementing role-based access control (RBAC)

---

## Error Handling

| Error Scenario | Current Behavior | HTTP Status |
|---|---|---|
| User not found (history) | Returns error object | 200 |
| File not found (download) | Returns error object | 200 |
| No conversation history | Returns empty array | 200 |
| Invalid request body | Would be caught by Pydantic | 422 |

**Note:** All endpoints currently return status 200. Error handling could be improved with appropriate HTTP status codes (404, 400, 500).

---

## Related Services

### chatbot_logic.py
- Location: `Services/chatbot_logic.py`
- Main Function: `chat_with_azure(user_input, conversation)`
- Purpose: Orchestrates vector search, PDF matching, and Azure OpenAI API calls

### vector_store.py
- Location: `Services/vector_store.py`
- Main Functions:
  - `setup_vector_db(json_path)` - Initialize ChromaDB
  - `search_vectors(query)` - Perform semantic search

### kb_loader.py
- Location: `Services/kb_loader.py`
- Main Function: `load_knowledge_base(path)`
- Purpose: Load and flatten KnowledgeBase.json into queryable format

### config.py
- Location: `Services/config.py`
- Purpose: Environment variable management and Azure OpenAI client setup

### chatbot_db.py
- Location: `Data/chatbot_db.py`
- Purpose: SQLAlchemy database connection and session management

---

## Project Structure

```
Noxy/
├── Services/
│   ├── main.py                 # API endpoints (ALL ROUTES)
│   ├── chatbot_logic.py        # Azure OpenAI integration
│   ├── vector_store.py         # ChromaDB search
│   ├── kb_loader.py            # Knowledge base loading
│   ├── config.py               # Configuration
│   └── __init__.py
├── Models/
│   └── dataModels.py           # SQLAlchemy ORM models
├── Data/
│   └── chatbot_db.py           # Database connection
├── Documentation/
│   └── API_ENDPOINTS.md        # This file
├── ChromaDB/                   # Vector database storage
├── MockData/                   # PDF files for download
├── KnowledgeBase.json          # Knowledge base source
├── requirements.txt            # Python dependencies
├── .env                        # Configuration (not in repo)
└── README.md                   # Project overview
```

---

## Quick Start Examples

### 1. Check API Health
```bash
curl http://127.0.0.1:8000/
```

### 2. Send Chat Message
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_smith",
    "message": "What are the office hours?"
  }'
```

### 3. Get Chat History
```bash
curl http://127.0.0.1:8000/history/jane_smith
```

---

## Additional Resources

- **Swagger Interactive Documentation:** `http://localhost:8000/docs`
- **ReDoc Static Documentation:** `http://localhost:8000/redoc`
- **FastAPI Official Docs:** https://fastapi.tiangolo.com/
- **Azure OpenAI Documentation:** https://learn.microsoft.com/en-us/azure/ai-services/openai/
- **ChromaDB Documentation:** https://docs.trychroma.com/

---

**Last Updated:** 2025-11-14
**Documentation Version:** 1.1
**Changes:** Removed download-pdf endpoint documentation (endpoint has been removed from the codebase)
