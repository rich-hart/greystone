from typing import List

import numpy as np

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import crud, models, schemas, utils
from .database import SessionLocal, engine


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def fake_hash_password(password: str):
    return password + "notreallyhashed"


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = crud.get_user_by_email(next(get_db()),token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if current_user.is_active:
        return current_user
    raise HTTPException(status_code=400, detail="Inactive user")


@app.post("/token")
async def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_email(db,form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.email, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user



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
def read_loans(user_id : int = 0, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if user_id:
        loans = crud.get_loans_by_owner(db, user_id)
    else:
        loans = crud.get_loans(db, skip=skip, limit=limit)
    return loans


def has_access(db, loan_id, user_id):
    db_item = crud.get_item(db, item_id=loan_id)
    current_members = db.query(models.Member).filter(models.Member.loan_id == loan_id)
    for member in current_members:
        if member.user_id == user_id:
            return True
    return False


@app.get("/loans/{loan_id}", response_model=schemas.Loan)
def read_loan(loan_id: int,  db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_loan = crud.get_loan(db, loan_id=loan_id)
    if db_loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    if not has_access(db, loan_id, current_user.id):
        raise HTTPException(status_code=404, detail="Not authorized to view loan.")

    return db_loan


@app.get("/loans/{loan_id}/schedule/")
def get_schedules_for_loan(loan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if not has_access(db, loan_id, current_user.id):
        raise HTTPException(status_code=404, detail="Not authorized to view loan.")
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


@app.get("/loans/{loan_id}/summary/")
def get_summary_for_loan(loan_id: int, month: int = 0,  db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    if not has_access(db, loan_id, current_user.id):
        raise HTTPException(status_code=404, detail="Not authorized to view loan.")

    db_schedules = crud.get_schedules_by_loan(db, loan_id=loan_id)
    db_loan = crud.get_loan(db, loan_id=loan_id)
    summary = {
        'month': month,
        "current_principal_balance": float(db_schedules[month].remaining_balance),
        'aggregate_principal': 0.0,
        'aggregate_interest': 0.0,
    }

    for i in range(month):
        P = float(db_schedules[i].remaining_balance)
        r = float(db_loan.annual_interest_rate/(100))
        n = 12
        interest = utils.interest_payment(P,r,n)
        principal = float(db_schedules[i].monthly_payment) - interest
        summary['aggregate_interest'] = summary['aggregate_interest'] + interest
        summary['aggregate_principal'] = summary['aggregate_principal'] + principal
    summary['current_principal_balance'] = f"${summary['current_principal_balance']:.2f}"
    summary['aggregate_principal'] = f"${summary['aggregate_principal']:.2f}"
    summary['aggregate_interest'] = f"${summary['aggregate_interest']:.2f}"
    content = jsonable_encoder(summary)
    return JSONResponse(content=content)

@app.post("/loans/{loan_id}/share/", response_model=schemas.Member)
def share_loan_with_user(loan_id: int, member: schemas.MemberCreate,  db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_item = crud.get_item(db, item_id=loan_id)
    if not db_item.owner_id == current_user.id:
        raise HTTPException(status_code=404, detail="Not authorized to share loan.")
    db_member = crud.create_loan_member(db, member=member, loan_id=loan_id)
    return db_member

