from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Services.chatbot_logic import chat_with_azure
from Services.kb_loader import load_knowledge_base
from Data.chatbot_db import SessionLocal, engine
from Models.dataModels import Base, User, Conversation, ChatMessage
from Services.vector_store import setup_vector_db
from fastapi.responses import FileResponse
import os

setup_vector_db("KnowledgeBase.json")
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chatbot API")

# CORS middleware for Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kb_items = load_knowledge_base("KnowledgeBase.json")

class ChatRequest(BaseModel):
    username: str
    message: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Noxy API is running"}

PDF_FOLDER = "MockData"

@app.get("/download-pdf")
def download_pdf(filename: str):
    file_path = os.path.join(PDF_FOLDER, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")

@app.post("/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Username == request.username).first()
    if not user:
        user = User(Username=request.username)
        db.add(user)
        db.commit()
        db.refresh(user)

    convo = (
        db.query(Conversation)
        .filter(Conversation.UserId == user.UserId)
        .order_by(Conversation.StartedAt.desc())
        .first()
    )
    if not convo:
        convo = Conversation(UserId=user.UserId)
        db.add(convo)
        db.commit()
        db.refresh(convo)

    chat_history = db.query(ChatMessage).filter(ChatMessage.ConvoId == convo.ConvoId).all()

    conversation_history = [
       {"role": "system", "content":
        "Your name is Noxy, an AI chatbot designed to assist new employees with onboarding. "
        "Do not state your name unless asked. "
        "Detect the language of the user: "
        "- If the user writes in Cebuano or Bisaya, answer in Cebuano. "
        "- Otherwise, answer in English. "
        "- Answer in maximum of three sentences only and avoid using em-dash.  "
        "Guide the user in a friendly, professional manner. Answer in maximum two sentences."
        "Never say you lack information, never mention a database, and never say 'I don't know'."
        "Avoid using em-dash. "
        }]

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
    user = db.query(User).filter(User.Username == username).first()
    if not user:
        return {"error": "User not found"}

    convo = (
        db.query(Conversation)
        .filter(Conversation.UserId == user.UserId)
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


