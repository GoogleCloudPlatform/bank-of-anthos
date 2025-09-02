
import asyncio
from app.utils.logger import logger
from app.api.v1.models.user import UserData, Transaction

async def fetch_user_data(user_id: str) -> UserData:
    """
    Simulates fetching user data from Bank of Anthos APIs.
    Replace with actual API calls or MCP integration.
    """
    try:
        # Simulated data
        transactions = [
            Transaction(category="food", amount=300),
            Transaction(category="transport", amount=150),
            Transaction(category="entertainment", amount=200),
        ]
        user_data = UserData(
            user_id=user_id,
            income=5000,
            transactions=transactions,
            credit_limit=2000,
            current_balance=1500
        )
        return user_data
    except Exception as e:
        logger.error(f"Error fetching data for user {user_id}: {e}")
        raise
