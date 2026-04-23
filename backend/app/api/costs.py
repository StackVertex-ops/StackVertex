"""Cost Estimation API Endpoints.

REST API für Cost Estimation.
"""

import logging
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.repositories.architecture import ArchitectureRepository
from app.schemas.cost import CostEstimateResponse, ComponentCostResponse
from app.services.cost_estimator import CostEstimator

logger = logging.getLogger(__name__)

router = APIRouter()
cost_estimator = CostEstimator()


@router.post(
    "/costs/estimate",
    response_model=CostEstimateResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate Architecture Costs",
    description="Berechnet geschätzte Kosten für eine Architecture ohne zu speichern",
    responses={
        200: {"description": "Cost estimate successful"},
        422: {"description": "Invalid architecture JSON"},
        500: {"description": "Internal server error"},
    },
)
async def estimate_cost_from_json(
    architecture_json: Dict[str, Any] = Body(..., description="Architecture JSON"),
) -> CostEstimateResponse:
    """Berechnet Kosten für Architecture JSON.

    Args:
        architecture_json: Architecture Definition

    Returns:
        CostEstimateResponse mit Details

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        # Estimate costs
        estimate = cost_estimator.estimate_architecture_cost(architecture_json)

        # Convert to response
        return CostEstimateResponse(
            total_hourly=float(estimate.total_hourly),
            total_monthly=float(estimate.total_monthly),
            total_yearly=float(estimate.total_yearly),
            currency=estimate.currency,
            components=[
                ComponentCostResponse(
                    component_id=comp.component_id,
                    component_type=comp.component_type,
                    component_name=comp.component_name,
                    hourly_cost=float(comp.hourly_cost),
                    monthly_cost=float(comp.monthly_cost),
                    breakdown={k: float(v) for k, v in comp.breakdown.items()},
                )
                for comp in estimate.components
            ],
            breakdown_by_type={
                k: float(v) for k, v in estimate.breakdown_by_type.items()
            },
        )

    except Exception as e:
        logger.error(f"Error estimating costs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating costs: {str(e)}",
        )


@router.get(
    "/costs/architectures/{architecture_id}/estimate",
    response_model=CostEstimateResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate Costs for Saved Architecture",
    description="Berechnet geschätzte Kosten für eine gespeicherte Architecture",
    responses={
        200: {"description": "Cost estimate successful"},
        404: {"description": "Architecture not found"},
        500: {"description": "Internal server error"},
    },
)
async def estimate_cost_for_architecture(
    architecture_id: UUID,
) -> CostEstimateResponse:
    """Berechnet Kosten für gespeicherte Architecture.

    Args:
        architecture_id: UUID der Architecture

    Returns:
        CostEstimateResponse

    Raises:
        HTTPException: 404 wenn nicht gefunden
    """
    try:
        # Load architecture
        repo = ArchitectureRepository()
        item = repo.get(architecture_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Architecture with ID {architecture_id} not found",
            )

        # Estimate costs
        estimate = cost_estimator.estimate_architecture_cost(
            item["architecture_json"]
        )

        # Convert to response
        return CostEstimateResponse(
            total_hourly=float(estimate.total_hourly),
            total_monthly=float(estimate.total_monthly),
            total_yearly=float(estimate.total_yearly),
            currency=estimate.currency,
            components=[
                ComponentCostResponse(
                    component_id=comp.component_id,
                    component_type=comp.component_type,
                    component_name=comp.component_name,
                    hourly_cost=float(comp.hourly_cost),
                    monthly_cost=float(comp.monthly_cost),
                    breakdown={k: float(v) for k, v in comp.breakdown.items()},
                )
                for comp in estimate.components
            ],
            breakdown_by_type={
                k: float(v) for k, v in estimate.breakdown_by_type.items()
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error estimating costs for architecture {architecture_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating costs: {str(e)}",
        )
