from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class ApplicationUser(Base):
    """
    Extended user model that mirrors AspNetCore Identity's IdentityUser.
    Stores application-specific user information beyond standard Identity fields.
    """
    __tablename__ = "AspNetUsers"
    __table_args__ = {"schema": "dbo"}

    Id = Column(String(450), primary_key=True)  # AspNetCore IdentityUser uses string IDs
    UserName = Column(String(256), unique=True, nullable=True)
    Email = Column(String(256), nullable=True)
    NormalizedEmail = Column(String(256), nullable=True)
    EmailConfirmed = Column(Boolean, default=False)
    PasswordHash = Column(Text, nullable=True)
    SecurityStamp = Column(Text, nullable=True)
    ConcurrencyStamp = Column(Text, nullable=True)
    PhoneNumber = Column(Text, nullable=True)
    PhoneNumberConfirmed = Column(Boolean, default=False)
    TwoFactorEnabled = Column(Boolean, default=False)
    LockoutEnd = Column(DateTime, nullable=True)
    LockoutEnabled = Column(Boolean, default=True)
    AccessFailedCount = Column(Integer, default=0)

    # Custom properties
    FirstName = Column(String(100), nullable=True)
    LastName = Column(String(100), nullable=True)
    DepartmentId = Column(Integer, ForeignKey("dbo.Departments.Id"), nullable=True)
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, nullable=True)
    Phone = Column(String(20), nullable=True)
    Address = Column(String(500), nullable=True)
    StartDate = Column(DateTime, nullable=True)
    EmployeeId = Column(String(50), unique=True, nullable=True)

    # Relationships
    Department = relationship("Department", foreign_keys=[DepartmentId], back_populates="Users")
    ManagedDepartment = relationship(
        "Department",
        foreign_keys="Department.ManagerId",
        back_populates="Manager",
        uselist=False
    )
    Conversations = relationship("Conversation", back_populates="User")

    def get_full_name(self):
        """Gets the user's full name by combining first and last names."""
        parts = [self.FirstName, self.LastName]
        return " ".join(p for p in parts if p).strip()


class Department(Base):
    """
    Represents an organizational department.
    """
    __tablename__ = "Departments"
    __table_args__ = {"schema": "dbo"}

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(100), nullable=False)
    Description = Column(String(500), nullable=True)
    ManagerId = Column(String(450), ForeignKey("dbo.AspNetUsers.Id"), nullable=True)
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, nullable=True)

    # Relationships
    Manager = relationship("ApplicationUser", foreign_keys=[ManagerId], back_populates="ManagedDepartment")
    Users = relationship("ApplicationUser", foreign_keys="ApplicationUser.DepartmentId", back_populates="Department")


class Conversation(Base):
    """
    Represents a Conversation entity containing chat messages between a user and Noxy.
    """
    __tablename__ = "Conversations"
    __table_args__ = {"schema": "dbo"}

    ConvoId = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(String(450), ForeignKey("dbo.AspNetUsers.Id"), nullable=True)
    StartedAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    User = relationship("ApplicationUser", back_populates="Conversations")
    Messages = relationship("ChatMessage", back_populates="Conversation")


class ChatMessage(Base):
    """
    Represents a ChatMessage entity in a conversation.
    """
    __tablename__ = "ChatMessages"
    __table_args__ = {"schema": "dbo"}

    MessageId = Column(Integer, primary_key=True, autoincrement=True)
    ConvoId = Column(Integer, ForeignKey("dbo.Conversations.ConvoId"), nullable=False)
    Sender = Column(String(50), nullable=True)  # 'User' or 'Noxy'
    Message = Column(Text, nullable=True)
    SentAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    Conversation = relationship("Conversation", back_populates="Messages")


class OnboardingFolder(Base):
    """
    Represents a folder/category for organizing onboarding tasks.
    """
    __tablename__ = "OnboardingFolders"
    __table_args__ = {"schema": "dbo"}

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Title = Column(String(200), nullable=False)
    Description = Column(String(1000), nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, nullable=True)

    # Relationships
    Tasks = relationship("OnboardingTask", back_populates="Folder")


class OnboardingTask(Base):
    """
    Represents a specific onboarding task within a folder.
    """
    __tablename__ = "OnboardingTasks"
    __table_args__ = {"schema": "dbo"}

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Title = Column(String(200), nullable=False)
    Description = Column(String(1000), nullable=False)
    FolderId = Column(Integer, ForeignKey("dbo.OnboardingFolders.Id"), nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, nullable=True)

    # Relationships
    Folder = relationship("OnboardingFolder", back_populates="Tasks")
    Materials = relationship("OnboardingMaterial", back_populates="Task")
    Steps = relationship("OnboardingSteps", back_populates="Task")


class OnboardingMaterial(Base):
    """
    Represents a material (file) associated with an onboarding task.
    """
    __tablename__ = "OnboardingMaterials"
    __table_args__ = {"schema": "dbo"}

    Id = Column(Integer, primary_key=True, autoincrement=True)
    FileName = Column(String(256), nullable=False)
    FileType = Column(String(50), nullable=False)
    Url = Column(String(500), nullable=False)
    TaskId = Column(Integer, ForeignKey("dbo.OnboardingTasks.Id"), nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, nullable=True)

    # Relationships
    Task = relationship("OnboardingTask", back_populates="Materials")


class OnboardingSteps(Base):
    """
    Represents a step within an onboarding task.
    """
    __tablename__ = "OnboardingSteps"
    __table_args__ = {"schema": "dbo"}

    Id = Column(Integer, primary_key=True, autoincrement=True)
    StepDescription = Column(String(1000), nullable=False)
    SequenceOrder = Column(Integer, nullable=False)
    TaskId = Column(Integer, ForeignKey("dbo.OnboardingTasks.Id"), nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, nullable=True)

    # Relationships
    Task = relationship("OnboardingTask", back_populates="Steps")
