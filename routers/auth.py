from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from starlette import status

from models import User
from database import SessionLocal
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    hashed_password: str
    role: str

def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return True

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency, create_user_request: CreateUserRequest):
    user = User(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        is_active=True,
        hashed_password=bcrypt_context.hash(create_user_request.hashed_password),
        role=create_user_request.role
    )
    db.add(user)
    db.commit()

@router.post("/token", status_code=status.HTTP_201_CREATED)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = ''
    return {"access_token": token, "token_type": "bearer"}