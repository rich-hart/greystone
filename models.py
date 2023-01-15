from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Numeric
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")

class Loan(Item):
    __tablename__ = 'loans'
    __mapper_args__ = {'polymorphic_identity': 'loan'}

    id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    amount = Column(Numeric(precision=19,scale=4))
    annual_interest_rate = Column(Float)
    loan_term_in_months = Column(Integer)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"))
    month = Column(Integer)
    remaining_balance = Column(Numeric(precision=19,scale=4))
    monthly_payment = Column(Numeric(precision=19,scale=4))
