from pydantic import BaseModel
from typing import List, Dict

class Transaction(BaseModel):
    category: str
    amount: float

class UserData(BaseModel):
    user_id: str
    income: float
    transactions: List[Transaction]
    credit_limit: float
    current_balance: float

