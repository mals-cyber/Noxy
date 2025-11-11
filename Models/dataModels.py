from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "Users"
    UserId = Column(Integer, primary_key=True, autoincrement=True)
    Username = Column(String(100), nullable=True)
    CreatedAt = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "Conversations"
    ConvoId = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey("Users.UserId"))
    StartedAt = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "ChatMessages"
    MessageId = Column(Integer, primary_key=True, autoincrement=True)
    ConvoId = Column(Integer, ForeignKey("Conversations.ConvoId"))
    Sender = Column(String(50))  # 'User' or 'Noxy'
    Message = Column(String) 
    SentAt = Column(DateTime, default=datetime.utcnow)
