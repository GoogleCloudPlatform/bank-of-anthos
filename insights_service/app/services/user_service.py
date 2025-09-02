import httpx
import os
from app.api.v1.models.user import UserData, Transaction
from app.utils.logger import logger

BASE_URL = os.getenv("BOA_BASE_URL", "http://bank-of-anthos-service")

async def fetch_user_data(user_id: str) -> UserData:
    """
    Fetch user info, account, and transaction data from Bank of Anthos APIs.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch user info
            user_resp = await client.get(f"{BASE_URL}/users/{user_id}")
            user_resp.raise_for_status()
            user_info = user_resp.json()

            # Fetch account info
            account_resp = await client.get(f"{BASE_URL}/accounts/{user_id}")
            account_resp.raise_for_status()
            account_info = account_resp.json()

            # Fetch transactions
            tx_resp = await client.get(f"{BASE_URL}/transactions?user_id={user_id}")
            tx_resp.raise_for_status()
            tx_data = tx_resp.json()

        transactions = [Transaction(category=tx['category'], amount=tx['amount']) for tx in tx_data]

        return UserData(
            user_id=user_id,
            income=user_info.get("income", 0),
            transactions=transactions,
            credit_limit=account_info.get("credit_limit", 0),
            current_balance=account_info.get("balance", 0)
        )
    except Exception as e:
        logger.error(f"Error fetching data for user {user_id}: {e}")
        raise
