from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Services.chatbot_logic import chat_with_azure
from Data.chatbot_db import SessionLocal, engine
from Models.dataModels import Base, ApplicationUser, Conversation, ChatMessage
from fastapi.responses import FileResponse
import os
from vector.store import get_vector_db
from vector.inject import inject_document_from_url

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

    reply = chat_with_azure(request.message, conversation_history)

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


