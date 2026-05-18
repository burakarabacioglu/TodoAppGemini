from fastapi import APIRouter
from pydantic import BaseModel

from models import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    hashed_password: str
    role: str

@router.post("/auth")
async def create_user(create_user_request: CreateUserRequest):
    user = User(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        is_active=True,
        hashed_password=create_user_request.hashed_password,
        role=create_user_request.role
    )