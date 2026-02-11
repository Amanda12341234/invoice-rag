from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import hash_password, verify_password, create_access_token
from app.database import get_session
from app.models.user import User
from app.schemas.auth import AuthRequest, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: AuthRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username == request.username)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    user = User(username=request.username, hashed_password=hash_password(request.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(request: AuthRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == request.username)).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
