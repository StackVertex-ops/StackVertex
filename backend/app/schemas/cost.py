"""Cost Estimation Schemas.

Pydantic schemas für Cost API Responses.
"""


from pydantic import BaseModel, Field


class ComponentCostResponse(BaseModel):
    """Response Schema für Component Cost."""

    component_id: str = Field(..., description="Component ID")
    component_type: str = Field(..., description="Component Type")
    component_name: str = Field(..., description="Component Name")
    hourly_cost: float = Field(..., description="Hourly cost in USD")
    monthly_cost: float = Field(..., description="Monthly cost in USD")
    breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Cost breakdown by category"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "component_id": "web_server",
                "component_type": "ec2",
                "component_name": "Web Server",
                "hourly_cost": 0.0104,
                "monthly_cost": 7.59,
                "breakdown": {
                    "compute": 7.59
                }
            }
        }


class CostEstimateResponse(BaseModel):
    """Response Schema für Cost Estimate."""

    total_hourly: float = Field(..., description="Total hourly cost in USD")
    total_monthly: float = Field(..., description="Total monthly cost in USD")
    total_yearly: float = Field(..., description="Total yearly cost in USD")
    currency: str = Field(default="USD", description="Currency")
    components: list[ComponentCostResponse] = Field(
        default_factory=list,
        description="Cost breakdown per component"
    )
    breakdown_by_type: dict[str, float] = Field(
        default_factory=dict,
        description="Cost breakdown by component type"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_hourly": 0.15,
                "total_monthly": 109.5,
                "total_yearly": 1314.0,
                "currency": "USD",
                "components": [
                    {
                        "component_id": "web_server",
                        "component_type": "ec2",
                        "component_name": "Web Server",
                        "hourly_cost": 0.0104,
                        "monthly_cost": 7.59,
                        "breakdown": {"compute": 7.59}
                    }
                ],
                "breakdown_by_type": {
                    "ec2": 45.5,
                    "rds": 64.0
                }
            }
        }
