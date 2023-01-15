from typing import List

import numpy as np

from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)

@app.post("/users/{user_id}/loans/", response_model=schemas.Loan)
def create_loan_for_user(
    user_id: int, loan: schemas.LoanCreate, db: Session = Depends(get_db)
):
    return crud.create_user_loan(db=db, loan=loan, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.get("/loans/", response_model=List[schemas.Loan])
def read_loans(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    loans = crud.get_loans(db, skip=skip, limit=limit)
    return loans

@app.get("/loans/{loan_id}", response_model=schemas.Loan)
def read_user(loan_id: int, db: Session = Depends(get_db)):
    db_loan = crud.get_loan(db, loan_id=loan_id)
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    return db_loan

@app.get("/loans/{loan_id}/schedule/", response_model=schemas.Loan)
def get_schedules_for_loan(loan_id: int, db: Session = Depends(get_db)):
    db_schedules = crud.get_schedules_by_loan(db, loan_id=loan_id)
    formatted_schedules = []
    for s in db_schedules:
        formatted_schedules.append({
            'month': s.month,
            'remaining_balance': f"${s.remaining_balance:.2f}",
            'monthly_payment': f"${s.monthly_payment:.2f}",
        })
    content = jsonable_encoder(formatted_schedules)
    return JSONResponse(content=content)

