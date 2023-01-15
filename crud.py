from sqlalchemy.orm import Session
import numpy as np

from . import models, schemas
from . import utils

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_loan(db: Session, loan_id: int):
    return db.query(models.Loan).filter(models.Loan.id == loan_id).first()


def get_schedules_by_loan(db: Session, loan_id: int):
    return db.query(models.Schedule).filter(models.Schedule.loan_id == loan_id)


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def get_loans(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Loan).offset(skip).limit(limit).all()

def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def create_user_loan(db: Session, loan: schemas.LoanCreate, user_id: int):
    loan_data = loan.dict()
    db_loan = models.Loan(**loan.dict(), owner_id=user_id)
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)

    P = loan_data['amount']
    r = loan_data['annual_interest_rate']/(100*12)
    n = int(loan_data['loan_term_in_months'])
    A = utils.amortize_loan(P,r,n)
    
    schedules = [
        {
            "month": 0,
            "remaining_balance": P,
            "monthly_payment": A,
        }
    ]
    for i in range(1,n):
        month = i
        remaining_balance = schedules[i-1]["remaining_balance"] * (1+r) - A
        monthly_payment = min(A,remaining_balance)
        schedules.append({
            "month": month,
            "remaining_balance": remaining_balance,
            "monthly_payment": monthly_payment,
        })

    for s in schedules:
        db_schedule = models.Schedule(**s, loan_id=db_loan.id)
        db.add(db_schedule)

    db.commit()
    return db_loan
