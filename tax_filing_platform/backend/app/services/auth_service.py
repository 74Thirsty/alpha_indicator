from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, payload: UserCreate) -> User:
        if self.db.query(User).filter(User.email == payload.email.lower()).first():
            raise ValueError("email already registered")
        user = User(email=payload.email.lower(), password_hash=pwd_context.hash(payload.password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.db.query(User).filter(User.email == email.lower(), User.is_active.is_(True)).first()
        if user and pwd_context.verify(password, user.password_hash):
            return user
        return None
