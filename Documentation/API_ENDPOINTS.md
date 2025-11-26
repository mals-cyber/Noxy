# Noxy API Documentation(main.py)

## Overview

The `main.py` file implements the FastAPI REST API for the Noxy HR onboarding chatbot. It provides endpoints for chat interactions, conversation history, user task progress, and vector database document management.

---

## Application Setup

### FastAPI Initialization

```python
app = FastAPI(title="Chatbot API")
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5164",
        "http://127.0.0.1:5164",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Purpose:** Enables cross-origin requests from development servers (Vite, React, ASP.NET)

**Allowed Origins:**
- Port 3000 - React/Node.js dev server
- Port 5173 - Vite dev server
- Port 5164 - ASP.NET backend

---

## Data Models

### ChatRequest

```python
class ChatRequest(BaseModel):
    username: str = None
    userId: str = None
    message: str
```

**Fields:**
- `username` (optional): User's username
- `userId` (optional): User's unique identifier
- `message` (required): User's chat message

**Validation:** At least one of `username` or `userId` must be provided

**Example:**
```json
{
  "userId": "user-123",
  "message": "What are the office hours?"
}
```

---

### UploadDocumentRequest

```python
class UploadDocumentRequest(BaseModel):
    url: str
```

**Fields:**
- `url` (required): Public URL to JSON, PDF, or Markdown file

**Example:**
```json
{
  "url": "https://example.blob.core.windows.net/container/document.json"
}
```

---

### DeleteDocumentRequest

```python
class DeleteDocumentRequest(BaseModel):
    url: str
```

**Fields:**
- `url` (required): Original URL of document to delete

**Example:**
```json
{
  "url": "https://example.blob.core.windows.net/container/document.json"
}
```

---

### UpdateDocumentRequest

```python
class UpdateDocumentRequest(BaseModel):
    old_url: str
    new_url: str
```

**Fields:**
- `old_url` (required): URL of document to replace
- `new_url` (required): URL of new document version

**Example:**
```json
{
  "old_url": "https://example.blob.core.windows.net/container/old_document.json",
  "new_url": "https://example.blob.core.windows.net/container/new_document.json"
}
```

---

## Database Dependency

### get_db()

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Purpose:** Provides database session management with automatic cleanup

**Usage Pattern:**
```python
@app.post("/endpoint")
def endpoint(db: Session = Depends(get_db)):
    # Use db session
    pass
    # Session automatically closed after request
```

---

## API Endpoints

### 1. Health Check

**Route:** `GET /`

**Description:** Verifies API is running

**Response:**
```json
{
  "message": "Noxy API is running"
}
```

**Status Code:** 200 OK

**Example cURL:**
```bash
curl http://localhost:8000/
```

---

### 2. Chat Endpoint

**Route:** `POST /chat`

**Description:** Main conversation endpoint that processes user messages and returns AI-generated responses

**Request Body:**
```json
{
  "username": "john.doe",
  "userId": "user-123",
  "message": "What documents do I need for onboarding?"
}
```

**Response:**
```json
{
  "User": "What documents do I need for onboarding?",
  "Noxy": "For onboarding, you'll need a valid government ID, proof of address, and your TIN number."
}
```

**Status Codes:**
- `200 OK` - Successful response
- `422 Unprocessable Entity` - Invalid request body

**Error Response:**
```json
{
  "error": "User not found"
}
```

#### Process Flow

1. **User Lookup**
   - Searches by `userId` first (if provided)
   - Falls back to `username` search
   - Returns error if user not found

2. **Conversation Management**
   - Retrieves most recent conversation for user
   - Creates new conversation if none exists
   - Links conversation to user via `UserId`

3. **Chat History Retrieval**
   - Fetches all messages from current conversation
   - Builds conversation history array
   - Formats as role-content pairs (user/assistant)

4. **Message Storage**
   - Saves user's message to database
   - Marks sender as "User"
   - Links to current conversation

5. **Task Progress Fetch**
   - Retrieves user's onboarding task status
   - Passes to AI agent for context-aware responses

6. **AI Response Generation**
   - Calls `ask_noxy()` with message, user_id, and task_progress
   - Agent processes query and generates response

7. **Bot Message Storage**
   - Saves Noxy's response to database
   - Marks sender as "Noxy"
   - Links to current conversation

8. **Response Return**
   - Returns both user message and bot response

**Example cURL:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-123",
    "message": "What are the office hours?"
  }'
```

---

### 3. Get Chat History

**Route:** `GET /history/{username}`

**Description:** Retrieves complete conversation history for a user

**Path Parameters:**
- `username` (required): User's username

**Response:**
```json
{
  "username": "john.doe",
  "history": [
    {
      "sender": "User",
      "message": "Hello"
    },
    {
      "sender": "Noxy",
      "message": "Hi! How can I help you with your onboarding today?"
    },
    {
      "sender": "User",
      "message": "What documents do I need?"
    },
    {
      "sender": "Noxy",
      "message": "You'll need a valid government ID, proof of address, and your TIN number."
    }
  ]
}
```

**Empty History Response:**
```json
{
  "username": "john.doe",
  "history": []
}
```

**Error Response:**
```json
{
  "error": "User not found"
}
```

**Status Codes:**
- `200 OK` - Success (even if history is empty)
- `422 Unprocessable Entity` - Invalid username format

**Example cURL:**
```bash
curl http://localhost:8000/history/john.doe
```

---

### 4. Get User Task Progress

**Route:** `GET /user-task-progress/{user_id}`

**Description:** Retrieves onboarding task progress for a specific user

**Path Parameters:**
- `user_id` (required): User's unique identifier

**Response:**
```json
[
  {
    "taskId": 1,
    "taskTitle": "Submit ID Documents",
    "taskDescription": "Upload a valid government-issued ID (passport, driver's license, or national ID)",
    "status": "Pending",
    "updatedAt": "2025-11-26T10:30:00"
  },
  {
    "taskId": 2,
    "taskTitle": "Complete Tax Forms",
    "taskDescription": "Fill out and submit BIR Form 2316 and W-4",
    "status": "In Progress",
    "updatedAt": "2025-11-26T11:15:00"
  },
  {
    "taskId": 3,
    "taskTitle": "Company Orientation",
    "taskDescription": "Attend the new hire orientation session",
    "status": "Completed",
    "updatedAt": "2025-11-25T14:20:00"
  }
]
```

**Empty Response:**
```json
[]
```

**Task Status Values:**
- `Pending` - Not yet started
- `In Progress` - Currently being worked on
- `Completed` - Finished

**Example cURL:**
```bash
curl http://localhost:8000/user-task-progress/user-123
```

---

### 5. Upload Document

**Route:** `POST /upload-document`

**Description:** Uploads a document to the vector database for semantic search. Accepts public URLs pointing to JSON, PDF, or Markdown files.

**Request Body:**
```json
{
  "url": "https://example.blob.core.windows.net/container/hr-policies.pdf"
}
```

**Supported File Types:**

| Extension | Description | Processing Method |
|-----------|-------------|-------------------|
| `.json` | Structured Q&A format | Parsed as JSON |
| `.pdf` | PDF documents | Text extracted via PyMuPDF |
| `.md` | Markdown files | Split by headers with bullet expansion |

**Success Response:**
```json
{
  "success": true,
  "documents_added": 24,
  "file_type": "pdf",
  "message": "Successfully injected 24 chunks from PDF file"
}
```

**Error Responses:**

Invalid URL:
```json
{
  "success": false,
  "documents_added": 0,
  "file_type": null,
  "message": "Invalid request: 'url' must be a non-empty string"
}
```

Download Error:
```json
{
  "success": false,
  "documents_added": 0,
  "file_type": null,
  "message": "Failed to download file from URL"
}
```

Processing Error:
```json
{
  "success": false,
  "documents_added": 0,
  "file_type": null,
  "message": "Error processing PDF: Invalid file format"
}
```

**Status Codes:**
- `200 OK` - Request processed (check `success` field)

**Process Flow:**
1. Validates URL format and type
2. Downloads file from provided URL
3. Processes file based on extension
4. Chunks content for vector storage
5. Injects chunks into ChromaDB
6. Returns statistics

**Example cURL:**
```bash
curl -X POST http://localhost:8000/upload-document \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://storage.blob.core.windows.net/docs/handbook.pdf"
  }'
```

---

### 6. Delete Document

**Route:** `POST /delete-document`

**Description:** Removes all chunks of a document from the vector database using its original upload URL

**Request Body:**
```json
{
  "url": "https://example.blob.core.windows.net/container/old-policy.json"
}
```

**Success Response:**
```json
{
  "success": true,
  "documents_deleted": 18,
  "message": "Successfully deleted 18 chunks from vector database"
}
```

**Error Responses:**

Document Not Found:
```json
{
  "success": false,
  "documents_deleted": 0,
  "message": "No documents found with the specified URL"
}
```

Invalid URL:
```json
{
  "success": false,
  "documents_deleted": 0,
  "message": "Invalid request: 'url' must be a non-empty string"
}
```

**Status Codes:**
- `200 OK` - Request processed (check `success` field)

**Important Notes:**
- URL must exactly match the original upload URL
- Deletion is permanent and cannot be undone
- All chunks associated with the URL are removed

**Example cURL:**
```bash
curl -X POST http://localhost:8000/delete-document \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://storage.blob.core.windows.net/docs/outdated.pdf"
  }'
```

---

### 7. Update Document

**Route:** `POST /update-document`

**Description:** Replaces an existing document with a new version in a single atomic operation

**Request Body:**
```json
{
  "old_url": "https://example.blob.core.windows.net/container/policy-v1.pdf",
  "new_url": "https://example.blob.core.windows.net/container/policy-v2.pdf"
}
```

**Success Response:**
```json
{
  "success": true,
  "documents_deleted": 15,
  "documents_added": 18,
  "file_type": "pdf",
  "message": "Successfully updated document: deleted 15 chunks, added 18 chunks"
}
```

**Error Responses:**

Old Document Not Found:
```json
{
  "success": false,
  "documents_deleted": 0,
  "documents_added": 0,
  "file_type": null,
  "message": "Document at old_url not found: No documents with specified URL"
}
```

Partial Success (Deletion OK, Injection Failed):
```json
{
  "success": false,
  "documents_deleted": 15,
  "documents_added": 0,
  "file_type": null,
  "message": "Deletion succeeded (15 chunks removed) but injection failed: File download error"
}
```

Invalid URLs:
```json
{
  "success": false,
  "documents_deleted": 0,
  "documents_added": 0,
  "file_type": null,
  "message": "Invalid request: 'old_url' must be a non-empty string"
}
```

**Status Codes:**
- `200 OK` - Request processed (check `success` field)

**Process Flow:**

**Phase 1: Deletion**
1. Validates `old_url` format
2. Searches vector database for matching documents
3. Deletes all chunks with matching URL
4. Returns error if URL not found

**Phase 2: Injection**
1. Validates `new_url` format
2. Downloads file from `new_url`
3. Processes and chunks new content
4. Injects into vector database
5. Returns combined statistics

**Important Notes:**
- If deletion fails, injection is not attempted
- If deletion succeeds but injection fails, returns partial success
- Original document is removed even if new injection fails
- Supports cross-format updates (e.g., JSON to PDF)

**Example cURL:**
```bash
curl -X POST http://localhost:8000/update-document \
  -H "Content-Type: application/json" \
  -d '{
    "old_url": "https://storage.blob.core.windows.net/docs/handbook-2024.pdf",
    "new_url": "https://storage.blob.core.windows.net/docs/handbook-2025.pdf"
  }'
```

---

## Helper Functions

### get_user_task_progress()

```python
def get_user_task_progress(user_id: str, db: Session):
    progress = (
        db.query(UserOnboardingTaskProgress)
        .join(OnboardingTask)
        .filter(UserOnboardingTaskProgress.UserId == user_id)
        .all()
    )
    
    return [
        {
            "taskId": p.TaskId,
            "taskTitle": p.Task.Title,
            "taskDescription": p.Task.Description,
            "status": p.Status,
            "updatedAt": p.UpdatedAt
        }
        for p in progress
    ]
```

**Purpose:** Fetches and formats user's onboarding task progress

**Parameters:**
- `user_id`: User's unique identifier
- `db`: Database session

**Returns:** List of dictionaries containing task progress information

**Used By:**
- `/chat` endpoint - provides context to AI agent
- `/user-task-progress/{user_id}` endpoint - direct access

---

## Database Models Used

### ApplicationUser
- Stores user account information
- Primary Key: `Id`
- Fields: `UserName`, timestamps

### Conversation
- Represents chat sessions
- Foreign Key: `UserId` (references ApplicationUser)
- Fields: `ConvoId`, `StartedAt`

### ChatMessage
- Individual messages in conversations
- Foreign Key: `ConvoId` (references Conversation)
- Fields: `MessageId`, `Sender`, `Message`, timestamp

### OnboardingTask
- Predefined onboarding tasks
- Primary Key: `TaskId`
- Fields: `Title`, `Description`

### UserOnboardingTaskProgress
- Tracks user progress on tasks
- Foreign Keys: `UserId`, `TaskId`
- Fields: `Status`, `UpdatedAt`

---

## Environment Variables

Required environment variables (configured in separate files):

```bash
# Database connection
SQL_SERVER=localhost,1433
SQL_DB=NOXDb
SQL_USER=sa
SQL_PASS=Chang123!

# Azure Storage Blob Credentials
AZURE_BLOB_BASE_URL="https://noxstorageacct01.blob.core.windows.net/onboarding-materials"
AZURE_BLOB_LIST_URL="http://localhost:5164/api/onboarding/materials/blobs"
AZURE_STORAGE_ACCOUNT_NAME=noxstorageacct01

# Azure OpenAI (used by noxy_agent.py)
AZURE_OPENAI_API_KEY=E2dCUfo86bsJRVeqmhIfVPQDO4S7tTIXlojE1AaP3YE99BvR2inQJQQJ99BKACYeBjFXJ3w3AAABACOGBJyY
AZURE_OPENAI_ENDPOINT=https://azoai-fgtrain3.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini_FG3

AZURE_EMBEDDING_API_KEY=E2dCUfo86bsJRVeqmhIfVPQDO4S7tTIXlojE1AaP3YE99BvR2inQJQQJ99BKACYeBjFXJ3w3AAABACOGBJyY
AZURE_EMBEDDING_ENDPOINT=https://azoai-fgtrain3.openai.azure.com/openai/deployments/text-embedding-ada-002-FG03/embeddings?api-version=2023-05-15
AZURE_EMBEDDING_API_VERSION=2024-02-01
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-ada-002-FG03
```

---

## Running the Application

### Development Mode

```bash
uvicorn main:app --reload
```

**Options:**
- `uvicorn main:app --reload` - Auto-restart on code changes
- `uvicorn main:app --reload --host 0.0.0.0` - Accept connections from any IP
- `uvicorn main:app --reload --port 8000` - Listen on port 8000

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Options:**
- `--workers 4` - Run 4 worker processes

---

## Error Handling

### User Not Found
```json
{
  "error": "User not found"
}
```

Occurs when provided username or userId doesn't exist in database.

### Validation Errors
FastAPI automatically returns 422 status with detailed validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Vector Database Errors
Handled within endpoint with descriptive messages:
- File download failures
- Unsupported file formats
- Processing errors
- Database connection issues

---

## Best Practices

1. **Always provide userId** - More reliable than username for user lookup
2. **Use update-document** - Preferred over delete + upload for document updates
3. **Validate URLs** - Ensure URLs are accessible before uploading
4. **Monitor vector DB size** - Large databases may impact search performance
5. **Handle partial failures** - Check individual operation success in update responses
6. **Implement retry logic** - For transient failures in document operations
7. **Clean up old documents** - Regularly delete outdated content

---

## API Testing

### Using cURL

```bash
# Health check
curl http://localhost:8000/

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-123", "message": "Hello"}'

# History
curl http://localhost:8000/history/john.doe

# Task progress
curl http://localhost:8000/user-task-progress/user-123

# Upload document
curl -X POST http://localhost:8000/upload-document \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/doc.pdf"}'
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Chat
response = requests.post(f"{BASE_URL}/chat", json={
    "userId": "user-123",
    "message": "What are the office hours?"
})
print(response.json())

# Get history
response = requests.get(f"{BASE_URL}/history/john.doe")
print(response.json())
```
