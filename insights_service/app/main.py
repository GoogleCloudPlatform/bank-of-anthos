
from fastapi import FastAPI
from app.api.v1.endpoints import insights, health

app = FastAPI(title="Personalized Financial Insights")

# Include Routers
app.include_router(insights.router, prefix="/api/v1/insights", tags=["Insights"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
