import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.db.database import async_session_maker
from backend.db.enums import ProjectStage, RiskAppetite, SessionStatus
from backend.db.projects import Project
from backend.db.sessions import Session
from backend.db.users import User
from backend.modules.agents.service import AgentWorkflowService


router = APIRouter(prefix="/workflow", tags=["workflow"])


class FullCycleRequest(BaseModel):
    raw_intent: str = Field(..., min_length=10, description="Свободное описание идеи")
    project_name: str = Field(default="Новая идея")
    user_email: str | None = Field(default=None)
    display_name: str | None = Field(default=None)
    vertical_key: str = Field(default="it_startup")
    stage: ProjectStage = Field(default=ProjectStage.IDEA)
    risk_appetite: RiskAppetite = Field(default=RiskAppetite.BALANCED)
    team_size: int | None = Field(default=None, ge=1)
    runway_months: float | None = Field(default=None, ge=0)
    geography: str | None = Field(default="RU")
    trust_score: float = Field(default=0.3, ge=0.0, le=1.0)
    iteration: int = Field(default=1, ge=0)
    project_context: dict[str, Any] = Field(default_factory=dict)


@router.post("/full-cycle")
async def run_full_cycle(payload: FullCycleRequest) -> dict[str, Any]:
    async with async_session_maker() as db:
        user = await _get_or_create_user(
            db=db,
            email=payload.user_email,
            display_name=payload.display_name,
        )

        project = Project(
            user_id=user.id,
            name=payload.project_name,
            vertical_key=payload.vertical_key,
            stage=payload.stage,
            risk_appetite=payload.risk_appetite,
            team_size=payload.team_size,
            runway_months=Decimal(str(payload.runway_months)) if payload.runway_months is not None else None,
            geography=payload.geography,
        )
        db.add(project)
        await db.flush()

        session = Session(
            project_id=project.id,
            status=SessionStatus.DRAFT,
        )
        db.add(session)
        await db.flush()

        service = AgentWorkflowService(db)
        merged_project_context = {
            "project_name": payload.project_name,
            "vertical_key": payload.vertical_key,
            "stage": payload.stage.value,
            "risk_appetite": payload.risk_appetite.value,
            "team_size": payload.team_size,
            "runway_months": payload.runway_months,
            "geography": payload.geography,
            "trust_score": payload.trust_score,
            "iteration": payload.iteration,
            **payload.project_context,
        }
        result = await service.run_analysis(
            session=session,
            raw_intent=payload.raw_intent,
            project_context=merged_project_context,
            commit=True,
        )

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
            },
            "project": {
                "id": str(project.id),
                "name": project.name,
                "vertical_key": project.vertical_key,
                "stage": project.stage.value,
                "risk_appetite": project.risk_appetite.value,
                "team_size": project.team_size,
                "runway_months": float(project.runway_months) if project.runway_months is not None else None,
                "geography": project.geography,
            },
            "session": {
                "id": str(session.id),
                "status": session.status.value,
            },
            "result": result,
        }


async def _get_or_create_user(
    *,
    db,
    email: str | None,
    display_name: str | None,
) -> User:
    resolved_email = email or f"demo-{uuid.uuid4().hex[:12]}@local.test"
    existing = await db.scalar(select(User).where(User.email == resolved_email))
    if existing is not None:
        if display_name and existing.display_name != display_name:
            existing.display_name = display_name
        return existing

    user = User(
        email=resolved_email,
        display_name=display_name,
    )
    db.add(user)
    await db.flush()
    return user
