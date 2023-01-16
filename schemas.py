from typing import List, Union

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: Union[str, None] = None

class LoanBase(ItemBase):
    amount: float
    annual_interest_rate: float
    loan_term_in_months: float

class ScheduleBase(BaseModel):
    month: int
    remaining_balance: float
    monthly_payment: float


class ItemCreate(ItemBase):
    pass


class LoanCreate(LoanBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class Loan(LoanBase):
    id: int

    class Config:
        orm_mode = True


class Schedule(ScheduleBase):
    id: int
    loan_id: int

    class Config:
        orm_mode = True



class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True
