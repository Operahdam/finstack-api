
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


def register_user(db: Session, data: UserCreate) -> User:
    email = str(data.email).strip().lower()

    existing = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(409, detail="Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(data.password),
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            detail="Email already registered",
        )


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = db.execute(
        select(User).where(User.email == email.strip().lower())
    ).scalar_one_or_none()

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
