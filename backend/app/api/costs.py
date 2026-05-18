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
from app.services.cost_calculator import calculate_blueprint_cost

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
        ) from e


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
        ) from e


@router.post(
    "/costs/estimate-blueprint",
    status_code=status.HTTP_200_OK,
    summary="Estimate Blueprint Costs",
    description="Berechnet Kosten für Blueprint mit gegebener Konfiguration",
    responses={
        200: {"description": "Cost estimate successful"},
        400: {"description": "Invalid configuration"},
        500: {"description": "Internal server error"},
    },
)
async def estimate_blueprint_cost(
    blueprint_id: str = Body(..., description="Blueprint ID"),
    configuration: Dict[str, Any] = Body(..., description="Blueprint Configuration"),
) -> Dict[str, Any]:
    """Berechnet Kosten für Blueprint-Konfiguration.

    Alias für calculate_live_cost für bessere API-Semantik.

    Args:
        blueprint_id: ID des Blueprints
        configuration: User-Konfiguration

    Returns:
        Cost breakdown
    """
    return await calculate_live_cost(blueprint_id, configuration)


@router.post(
    "/costs/calculate-live",
    status_code=status.HTTP_200_OK,
    summary="Calculate Live Blueprint Costs",
    description="Berechnet Kosten in Echtzeit basierend auf Blueprint Form-Eingaben",
    responses={
        200: {"description": "Cost calculation successful"},
        400: {"description": "Invalid configuration"},
        500: {"description": "Internal server error"},
    },
)
async def calculate_live_cost(
    blueprint_id: str = Body(..., description="Blueprint ID"),
    configuration: Dict[str, Any] = Body(..., description="Blueprint Configuration"),
) -> Dict[str, Any]:
    """Berechnet Kosten in Echtzeit basierend auf Form-Eingaben.

    Dieser Endpoint wird vom Frontend bei jedem Field-Change aufgerufen.

    Args:
        blueprint_id: ID des Blueprints (z.B. "static-website")
        configuration: User-Konfiguration aus Form

    Returns:
        Dict mit CostBreakdown Details

    Raises:
        HTTPException: Bei Fehlern
    """
    try:
        # Calculate costs
        cost_breakdown = calculate_blueprint_cost(blueprint_id, configuration)

        # Convert to JSON-serializable format
        return {
            "items": [
                {
                    "service": item.service,
                    "resource": item.resource,
                    "amount": float(item.amount),
                    "unit": item.unit,
                    "quantity": float(item.quantity),
                    "total": float(item.total),
                }
                for item in cost_breakdown.items
            ],
            "subtotal": float(cost_breakdown.subtotal),
            "tax": float(cost_breakdown.tax),
            "total": float(cost_breakdown.total),
            "currency": cost_breakdown.currency,
            "period": cost_breakdown.period,
            "assumptions": cost_breakdown.assumptions,
        }

    except ValueError as e:
        logger.error(f"Validation error in live cost calculation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {str(e)}",
        ) from e

    except Exception as e:
        logger.error(f"Error calculating live costs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating costs: {str(e)}",
        ) from e
