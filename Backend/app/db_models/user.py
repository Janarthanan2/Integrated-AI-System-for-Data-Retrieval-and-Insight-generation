"""
User model for authentication
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from passlib.context import CryptContext

from .base import Base

# Password hashing context - using pbkdf2_sha256 for better compatibility
# bcrypt can have issues on some Windows installations
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and set the password"""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.password_hash)
    
    def __repr__(self):
        return f"<User {self.email}>"
