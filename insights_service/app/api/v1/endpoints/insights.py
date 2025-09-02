
from fastapi import APIRouter, HTTPException
from app.services.insight_service import generate_insight
from app.api.v1.models.insight import InsightResponse

router = APIRouter()

@router.get("/{user_id}", response_model=InsightResponse)
async def get_insight(user_id: str):
    """
    Endpoint to fetch personalized financial insights for a user.
    """
    try:
        insight = await generate_insight(user_id)
        return insight
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
