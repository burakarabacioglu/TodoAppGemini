from fastapi import APIRouter, Depends, Path, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse
import logging

from database import SessionLocal
from models import Todo
from routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from routers.auth import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/todo",
    tags=["Todos"],
)

templates = Jinja2Templates(directory="templates")


class TodoRequest(BaseModel):
    title: str = Field(min_length=3),
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(gt=0, lt=6)
    complete: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response


def get_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        role: str = payload.get('role')

        if username is None or user_id is None:
            return None
        return {'username': username, 'id': user_id, 'role': role}
    except JWTError:
        return None


@router.get("/todo-page", status_code=status.HTTP_200_OK)
async def render_todo_page(request: Request, db: db_dependency):
    try:
        # Use our cookie handler
        user = get_user_from_cookie(request)

        if user is None:
            return redirect_to_login()

        todos = db.query(Todo).filter(Todo.owner_id == user.get('id')).all()

        # FIX: Also fixed the dictionary syntax typo from `user: "user"` to `"user": user`
        return templates.TemplateResponse(
            "todo.html",
            {"request": request, "todos": todos, "user": user}
        )
    except Exception as e:
        logger.error(f"Error rendering todo page: {e}")
        return redirect_to_login()



@router.get("/")
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(Todo).filter(Todo.owner_id == user.get('id')).all()

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def get_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@router.post("/create_todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, todo_request: TodoRequest, db: Session = Depends(get_db)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = Todo(**todo_request.model_dump(), owner_id=user.get('id'))
    db.add(todo)
    db.commit()

@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id : int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.complete = todo_request.complete

    db.add(todo)
    db.commit()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(todo)
    db.commit()