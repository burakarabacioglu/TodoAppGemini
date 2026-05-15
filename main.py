from fastapi import FastAPI, Depends, Path, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

from database import engine, SessionLocal
from models import Base, Todo

app = FastAPI()

Base.metadata.create_all(engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/read_all")
async def read_all(db: db_dependency):
    return db.query(Todo).all()

@app.get("/get_by_id/{todo_id}", status_code=status.HTTP_200_OK)
async def get_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
