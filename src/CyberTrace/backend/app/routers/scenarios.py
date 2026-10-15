"""Synthetic scenario listing + loading, per PROJECT_PLAN.md section 9.
Any authenticated user may load a scenario (it only creates a new
is_synthetic case owned by them) and all authenticated users can see all
synthetic cases (same shared-read rule as `cases.py`)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.scenario import ScenarioInfo, ScenarioLoadResponse
from app.services.scenarios import SCENARIOS, load_scenario

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioInfo])
async def list_scenarios() -> list[ScenarioInfo]:
    return [
        ScenarioInfo(key=key, name=info["name"], description=info["description"])
        for key, info in SCENARIOS.items()
    ]


@router.post("/{scenario_key}/load", response_model=ScenarioLoadResponse, status_code=status.HTTP_201_CREATED)
async def load_scenario_endpoint(
    scenario_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScenarioLoadResponse:
    if scenario_key not in SCENARIOS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown scenario")

    result = await load_scenario(db, scenario_key, current_user.id)
    return ScenarioLoadResponse(
        case=result["case"],
        records_parsed=result["records_parsed"],
        records_failed=result["records_failed"],
        gaps_detected=result["gaps_detected"],
    )
