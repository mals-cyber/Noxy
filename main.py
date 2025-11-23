from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Data.chatbot_db import SessionLocal, engine
from Models.dataModels import Base, ApplicationUser, Conversation, ChatMessage
from fastapi.responses import FileResponse
import os
from vector.store import get_vector_db, delete_documents_by_url
from vector.inject import inject_document_from_url
from agent.noxy_agent import ask_noxy
from Models.dataModels import UserOnboardingTaskProgress, OnboardingTask


get_vector_db()

app = FastAPI(title="Chatbot API")

# CORS middleware for Vite development and ASP.NET backend
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

class ChatRequest(BaseModel):
    username: str = None
    userId: str = None
    message: str

    def __init__(self, **data):
        super().__init__(**data)
        if not self.username and not self.userId:
            raise ValueError("Either 'username' or 'userId' must be provided")


class UploadDocumentRequest(BaseModel):
    url: str

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.blob.core.windows.net/container/document.json"
            }
        }


class DeleteDocumentRequest(BaseModel):
    url: str

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.blob.core.windows.net/container/document.json"
            }
        }


class UpdateDocumentRequest(BaseModel):
    old_url: str
    new_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "old_url": "https://example.blob.core.windows.net/container/old_document.json",
                "new_url": "https://example.blob.core.windows.net/container/new_document.json"
            }
        }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Noxy API is running"}


@app.post("/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    # Look up user by userId first, then by username
    user = None
    if request.userId:
        user = db.query(ApplicationUser).filter(ApplicationUser.Id == request.userId).first()
    elif request.username:
        user = db.query(ApplicationUser).filter(ApplicationUser.UserName == request.username).first()

    if not user:
        return {"error": "User not found"}

    convo = (
        db.query(Conversation)
        .filter(Conversation.UserId == user.Id)
        .order_by(Conversation.StartedAt.desc())
        .first()
    )
    if not convo:
        convo = Conversation(UserId=user.Id)
        db.add(convo)
        db.commit()
        db.refresh(convo)

    chat_history = db.query(ChatMessage).filter(ChatMessage.ConvoId == convo.ConvoId).all()

    conversation_history = []

    for msg in chat_history:
        role = "user" if msg.Sender == "User" else "assistant"
        conversation_history.append({"role": role, "content": msg.Message})

    user_msg = ChatMessage(ConvoId=convo.ConvoId, Sender="User", Message=request.message)
    db.add(user_msg)
    db.commit()

    task_progress = get_user_task_progress(request.userId, db)
    reply = ask_noxy(request.message, user_id=request.userId, task_progress=task_progress)

    bot_msg = ChatMessage(ConvoId=convo.ConvoId, Sender="Noxy", Message=reply)
    db.add(bot_msg)
    db.commit()

    return {"User": request.message, "Noxy": reply}

@app.get("/history/{username}")
def get_history(username: str, db: Session = Depends(get_db)):
    user = db.query(ApplicationUser).filter(ApplicationUser.UserName == username).first()
    if not user:
        return {"error": "User not found"}

    convo = (
        db.query(Conversation)
        .filter(Conversation.UserId == user.Id)
        .order_by(Conversation.StartedAt.desc())
        .first()
    )
    if not convo:
        return {"history": []}

    history = db.query(ChatMessage).filter(ChatMessage.ConvoId == convo.ConvoId).all()

    return {
        "username": username,
        "history": [
            {"sender": msg.Sender, "message": msg.Message}
            for msg in history
        ]
    }

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


@app.get("/user-task-progress/{user_id}")
def get_user_task_progress_endpoint(user_id: str, db: Session = Depends(get_db)):
    return get_user_task_progress(user_id, db)

@app.post("/upload-document")
def upload_document(request: UploadDocumentRequest):
    """
    Upload and inject a JSON, PDF, or Markdown document into the vector database.

    This endpoint accepts a public Azure Blob Storage URL or any public file URL,
    downloads the file, and injects it into ChromaDB for semantic search.

    Args:
        request: UploadDocumentRequest with 'url' field

    Returns:
        JSON response with:
        - success: bool indicating if injection was successful
        - documents_added: int number of chunks added to vector DB
        - file_type: str ("json", "pdf", "md", or None on error)
        - message: str descriptive message

    Supported file types:
    - .json: Structured Q&A format (uses existing JSON loader)
    - .pdf: PDF documents (text extracted via PyMuPDF)
    - .md: Markdown documentation (split by headers with bullet point expansion)

    Example:
        POST /upload-document
        {
            "url": "https://example.blob.core.windows.net/container/faq.json"
        }

        Response:
        {
            "success": true,
            "documents_added": 12,
            "file_type": "json",
            "message": "Successfully injected 12 chunks from JSON file"
        }
    """
    try:
        # Validate URL format
        if not request.url or not isinstance(request.url, str):
            return {
                "success": False,
                "documents_added": 0,
                "file_type": None,
                "message": "Invalid request: 'url' must be a non-empty string"
            }

        result = inject_document_from_url(request.url)
        return result

    except Exception as e:
        return {
            "success": False,
            "documents_added": 0,
            "file_type": None,
            "message": f"Unexpected error: {str(e)}"
        }


@app.post("/delete-document")
def delete_document(request: DeleteDocumentRequest):
    """
    Delete a document from the vector database by its original URL.

    This endpoint removes all chunks of a document that was previously uploaded
    via the /upload-document endpoint. The deletion is based on the original
    URL that was used during upload.

    Args:
        request: DeleteDocumentRequest with 'url' field (the original upload URL)

    Returns:
        JSON response with:
        - success: bool indicating if deletion was successful
        - documents_deleted: int number of chunks removed from vector DB
        - message: str descriptive message

    Example:
        POST /delete-document
        {
            "url": "https://example.blob.core.windows.net/container/faq.json"
        }

        Response:
        {
            "success": true,
            "documents_deleted": 12,
            "message": "Successfully deleted 12 chunks from vector database"
        }
    """
    try:
        # Validate URL format
        if not request.url or not isinstance(request.url, str):
            return {
                "success": False,
                "documents_deleted": 0,
                "message": "Invalid request: 'url' must be a non-empty string"
            }

        documents_deleted = delete_documents_by_url(request.url)
        return {
            "success": True,
            "documents_deleted": documents_deleted,
            "message": f"Successfully deleted {documents_deleted} chunks from vector database"
        }

    except ValueError as e:
        return {
            "success": False,
            "documents_deleted": 0,
            "message": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "documents_deleted": 0,
            "message": f"Unexpected error: {str(e)}"
        }


@app.post("/update-document")
def update_document(request: UpdateDocumentRequest):
    """
    Update a document in the vector database by replacing the old version with a new one.

    This endpoint performs a two-phase operation:
    1. Deletes all chunks of the document at old_url from the vector database
    2. Downloads and injects the document from new_url into the vector database

    The operation tracks both deletion and injection statistics separately,
    allowing visibility into partial success scenarios (e.g., deletion succeeds
    but injection fails).

    Args:
        request: UpdateDocumentRequest with 'old_url' and 'new_url' fields
            - old_url: The original URL of the document to be replaced
            - new_url: The URL of the new document to inject

    Returns:
        JSON response with:
        - success: bool indicating if the entire update was successful
        - documents_deleted: int number of chunks removed from vector DB
        - documents_added: int number of chunks added to vector DB
        - file_type: str ("json", "pdf", "md", or None on error)
        - message: str descriptive message

    Supported file types for new_url:
    - .json: Structured Q&A format
    - .pdf: PDF documents (text extracted via PyMuPDF)
    - .md: Markdown documentation (split by headers with bullet point expansion)

    Error scenarios:
    - If old_url not found: Returns error without attempting to inject
    - If deletion succeeds but injection fails: Returns partial success with error details
    - If both URLs are invalid: Returns validation error

    Example:
        POST /update-document
        {
            "old_url": "https://example.blob.core.windows.net/container/old.json",
            "new_url": "https://example.blob.core.windows.net/container/new.json"
        }

        Success Response:
        {
            "success": true,
            "documents_deleted": 12,
            "documents_added": 15,
            "file_type": "json",
            "message": "Successfully updated document: deleted 12 chunks, added 15 chunks"
        }

        Partial Failure Response:
        {
            "success": false,
            "documents_deleted": 12,
            "documents_added": 0,
            "file_type": None,
            "message": "Deletion succeeded (12 chunks removed) but injection failed: File download error"
        }
    """
    try:
        # Validate URLs format
        if not request.old_url or not isinstance(request.old_url, str):
            return {
                "success": False,
                "documents_deleted": 0,
                "documents_added": 0,
                "file_type": None,
                "message": "Invalid request: 'old_url' must be a non-empty string"
            }

        if not request.new_url or not isinstance(request.new_url, str):
            return {
                "success": False,
                "documents_deleted": 0,
                "documents_added": 0,
                "file_type": None,
                "message": "Invalid request: 'new_url' must be a non-empty string"
            }

        # Phase 1: Delete old document
        try:
            documents_deleted = delete_documents_by_url(request.old_url)
        except ValueError as e:
            # old_url not found in vector database
            return {
                "success": False,
                "documents_deleted": 0,
                "documents_added": 0,
                "file_type": None,
                "message": f"Document at old_url not found: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "documents_deleted": 0,
                "documents_added": 0,
                "file_type": None,
                "message": f"Error deleting old document: {str(e)}"
            }

        # Phase 2: Inject new document
        try:
            injection_result = inject_document_from_url(request.new_url)

            # Check if injection was successful
            if injection_result.get("success"):
                return {
                    "success": True,
                    "documents_deleted": documents_deleted,
                    "documents_added": injection_result.get("documents_added", 0),
                    "file_type": injection_result.get("file_type"),
                    "message": f"Successfully updated document: deleted {documents_deleted} chunks, added {injection_result.get('documents_added', 0)} chunks"
                }
            else:
                # Injection failed - return partial success
                return {
                    "success": False,
                    "documents_deleted": documents_deleted,
                    "documents_added": 0,
                    "file_type": None,
                    "message": f"Deletion succeeded ({documents_deleted} chunks removed) but injection failed: {injection_result.get('message', 'Unknown error')}"
                }

        except Exception as e:
            # Injection failed with exception - return partial success
            return {
                "success": False,
                "documents_deleted": documents_deleted,
                "documents_added": 0,
                "file_type": None,
                "message": f"Deletion succeeded ({documents_deleted} chunks removed) but injection failed: {str(e)}"
            }

    except Exception as e:
        return {
            "success": False,
            "documents_deleted": 0,
            "documents_added": 0,
            "file_type": None,
            "message": f"Unexpected error during update: {str(e)}"
        }
 