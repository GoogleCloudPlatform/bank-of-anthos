from app.services.user_service import fetch_user_data
from app.utils.logger import logger
import os
import asyncio

# Optional Gemini client
from google.cloud import aiplatform

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "projects/YOUR_PROJECT/locations/us-central1/publishers/google/models/gemini-text-bison-001")

async def generate_insight(user_id: str):
    """
    Generate financial insights for a user including spending breakdown,
    credit utilization, dynamic savings recommendations, and Gemini narrative.
    """
    try:
        user_data = await fetch_user_data(user_id)

        # --- Spending Breakdown ---
        spending_breakdown = {}
        for t in user_data.transactions:
            spending_breakdown[t.category] = spending_breakdown.get(t.category, 0) + t.amount

        total_spent = sum(spending_breakdown.values())

        # --- Credit Utilization ---
        credit_utilization = user_data.current_balance / max(user_data.credit_limit, 1)

        # --- Dynamic Savings Recommendation ---
        savings_ratio = (user_data.income - total_spent) / max(user_data.income, 1)
        if savings_ratio < 0.1:
            savings_recommendation = "Your spending is high this month. Consider reducing discretionary expenses."
        elif savings_ratio < 0.2:
            savings_recommendation = "Try to save at least 20% of your income next month."
        else:
            savings_recommendation = "Good job! You are saving a healthy portion of your income."

        # --- Gemini-driven Contextualized Narrative ---
        narrative = await generate_gemini_narrative(user_data, spending_breakdown, credit_utilization, savings_recommendation)

        # Assemble insight
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


async def generate_gemini_narrative(user_data, spending_breakdown, credit_utilization, savings_recommendation):
    """
    Use Gemini AI to generate a personalized financial narrative.
    """
    try:
        # Construct prompt for Gemini
        prompt = f"""
        User ID: {user_data.user_id}
        Income: {user_data.income}
        Credit Utilization: {credit_utilization:.2f}
        Spending Breakdown: {spending_breakdown}
        Savings Recommendation: {savings_recommendation}

        Generate a friendly, personalized financial advice narrative based on this data.
        """

        # Initialize Gemini client
        client = aiplatform.gapic.PredictionServiceClient()
        response = client.predict(
            name=GEMINI_MODEL_NAME,
            instances=[{"content": prompt}],
        )

        narrative_text = response.predictions[0].get("content", savings_recommendation)
        return narrative_text
    except Exception as e:
        logger.error(f"Gemini narrative generation failed: {e}")
        # Fallback to default narrative
        return savings_recommendation
