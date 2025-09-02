
from app.services.user_service import fetch_user_data
from app.utils.logger import logger
import asyncio

async def generate_insight(user_id: str):
    """
    Core function to generate financial insights.
    """
    try:
        user_data = await fetch_user_data(user_id)

        # Spending breakdown
        spending_breakdown = {}
        for t in user_data.transactions:
            spending_breakdown[t.category] = spending_breakdown.get(t.category, 0) + t.amount

        # Credit utilization
        credit_utilization = user_data.current_balance / user_data.credit_limit

        # Savings recommendation
        savings_recommendation = "Save 20% of your income"
        if sum(spending_breakdown.values()) > user_data.income * 0.8:
            savings_recommendation = "Consider reducing your spending to save more."

        # Placeholder for Gemini-generated narrative
        narrative = f"User {user_id} has a credit utilization of {credit_utilization*100:.1f}%."

        insight = {
            "user_id": user_id,
            "savings_recommendation": savings_recommendation,
            "spending_breakdown": spending_breakdown,
            "credit_utilization": credit_utilization,
            "narrative": narrative
        }
        return insight
    except Exception as e:
        logger.error(f"Error generating insight for {user_id}: {e}")
        raise
