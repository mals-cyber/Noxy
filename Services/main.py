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

get_vector_db()

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

class ChatRequest(BaseModel):
    username: str = None
    userId: str = None
    message: str

    def __init__(self, **data):
        super().__init__(**data)
        if not self.username and not self.userId:
            raise ValueError("Either 'username' or 'userId' must be provided")

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


