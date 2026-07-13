import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.app.models.auth import Base, User
import backend.app.models.user_domain
import backend.app.models.knowledge
import backend.app.models.crowd
import backend.app.models.incident
import backend.app.models.volunteer
import backend.app.models.transit
import backend.app.models.accessibility
import backend.app.models.command
import backend.app.models.dashboard
import backend.app.models.ai

from backend.app.models.ai import AIRecommendation, AIRiskAssessment
from backend.app.repositories.ai_repository import AIRecommendationRepository, AIRiskAssessmentRepository

test_db_url = "sqlite+aiosqlite:///./test_ai_repo.db"

@pytest.fixture(autouse=True)
async def setup_db():
    old_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_db_url
    engine = create_async_engine(test_db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if old_db_url is not None:
        os.environ["DATABASE_URL"] = old_db_url
    else:
        os.environ.pop("DATABASE_URL", None)
    if os.path.exists("./test_ai_repo.db"):
        try:
            os.remove("./test_ai_repo.db")
        except Exception:
            pass

@pytest.mark.asyncio
async def test_recommendation_and_risk_crud(setup_db):
    async_session = setup_db
    async with async_session() as session:
        rec_repo = AIRecommendationRepository(session)
        risk_repo = AIRiskAssessmentRepository(session)

        # Create recommendation
        rec = AIRecommendation(
            recommendation_type="Transit",
            recommendation="Increase bus capacity",
            confidence=0.88,
            priority="Medium",
            reason="Bus lines congested",
            status="Proposed"
        )
        await rec_repo.create(rec)
        await rec_repo.commit()

        # Retrieve
        fetched_rec = await rec_repo.get_by_id(rec.id)
        assert fetched_rec is not None
        assert fetched_rec.recommendation == "Increase bus capacity"

        # Create risk assessment
        risk = AIRiskAssessment(
            crowd_risk=15.0,
            overall_risk=20.0,
            status="LOW",
            explanation="Nominal conditions"
        )
        await risk_repo.create(risk)
        await risk_repo.commit()

        fetched_risk = await risk_repo.get_latest()
        assert fetched_risk is not None
        assert fetched_risk.overall_risk == 20.0
