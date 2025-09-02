
import pytest
from app.services.insight_service import generate_insight
import asyncio

@pytest.mark.asyncio
async def test_generate_insight():
    user_id = "test_user"
    insight = await generate_insight(user_id)
    assert insight["user_id"] == user_id
    assert "savings_recommendation" in insight
    assert "spending_breakdown" in insight
    assert "credit_utilization" in insight
