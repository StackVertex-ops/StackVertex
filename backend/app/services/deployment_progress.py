"""Deployment Progress Tracking.

Berechnet Progress Percentage und Schätzungen basierend auf Deployment Status.
"""

from datetime import datetime
from typing import Dict, Optional, Any

from app.models.deployment import DeploymentStatus


# Status → Progress Mapping (in %)
STATUS_PROGRESS_MAP: Dict[DeploymentStatus, int] = {
    DeploymentStatus.PENDING: 0,
    DeploymentStatus.GENERATING: 10,
    DeploymentStatus.INITIALIZING: 25,
    DeploymentStatus.PLANNING: 40,
    DeploymentStatus.APPLYING: 60,
    DeploymentStatus.SUCCESS: 100,
    DeploymentStatus.FAILED: 100,
    DeploymentStatus.DESTROYED: 100,
    DeploymentStatus.CANCELLED: 100,
    DeploymentStatus.DESTROYING: 80,
}

# Status → Step Description
STATUS_STEP_MAP: Dict[DeploymentStatus, str] = {
    DeploymentStatus.PENDING: "Waiting to start",
    DeploymentStatus.GENERATING: "Generating Terraform code",
    DeploymentStatus.INITIALIZING: "Initializing Terraform",
    DeploymentStatus.PLANNING: "Planning infrastructure changes",
    DeploymentStatus.APPLYING: "Applying infrastructure changes",
    DeploymentStatus.SUCCESS: "Deployment completed successfully",
    DeploymentStatus.FAILED: "Deployment failed",
    DeploymentStatus.DESTROYED: "Infrastructure destroyed",
    DeploymentStatus.CANCELLED: "Deployment cancelled",
    DeploymentStatus.DESTROYING: "Destroying infrastructure",
}

# Average duration per step (in seconds) - empirical values
AVERAGE_STEP_DURATIONS: Dict[DeploymentStatus, float] = {
    DeploymentStatus.GENERATING: 5.0,
    DeploymentStatus.INITIALIZING: 10.0,
    DeploymentStatus.PLANNING: 15.0,
    DeploymentStatus.APPLYING: 120.0,  # Longest step
    DeploymentStatus.DESTROYING: 60.0,
}


def get_progress_info(deployment: Dict[str, Any]) -> Dict:
    """Berechnet Progress-Informationen für Deployment.

    Args:
        deployment: Deployment item (dict from DynamoDB)

    Returns:
        Dict mit progress_percentage, current_step, elapsed_seconds, estimated_remaining_seconds
    """
    # Get status
    status = DeploymentStatus(deployment["status"])

    # Progress Percentage
    progress_percentage = STATUS_PROGRESS_MAP.get(status, 0)

    # Current Step
    current_step = STATUS_STEP_MAP.get(
        status,
        f"Unknown status: {status}"
    )

    # Elapsed Time
    started_at = deployment.get("started_at")
    completed_at = deployment.get("completed_at")

    if started_at:
        # Parse ISO timestamp strings
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))

        if completed_at:
            elapsed = (completed_at - started_at).total_seconds()
        else:
            elapsed = (datetime.utcnow() - started_at).total_seconds()
    else:
        elapsed = 0.0

    # Check if deployment is running
    is_running = status in [
        DeploymentStatus.PENDING,
        DeploymentStatus.GENERATING,
        DeploymentStatus.INITIALIZING,
        DeploymentStatus.PLANNING,
        DeploymentStatus.APPLYING,
        DeploymentStatus.DESTROYING,
    ]

    # Estimated Remaining Time (nur für laufende Deployments)
    estimated_remaining = None
    if is_running:
        estimated_remaining = _estimate_remaining_time(deployment)

    return {
        "progress_percentage": progress_percentage,
        "current_step": current_step,
        "elapsed_seconds": round(elapsed, 2),
        "estimated_remaining_seconds": (
            round(estimated_remaining, 2) if estimated_remaining else None
        ),
    }


def _estimate_remaining_time(deployment: Dict[str, Any]) -> Optional[float]:
    """Schätzt verbleibende Zeit basierend auf aktuellem Status.

    Args:
        deployment: Deployment item (dict from DynamoDB)

    Returns:
        Geschätzte verbleibende Zeit in Sekunden, oder None
    """
    current_status = DeploymentStatus(deployment["status"])

    # Summiere verbleibende Schritte
    remaining_steps = []

    if current_status == DeploymentStatus.PENDING:
        remaining_steps = [
            DeploymentStatus.GENERATING,
            DeploymentStatus.INITIALIZING,
            DeploymentStatus.PLANNING,
            DeploymentStatus.APPLYING,
        ]
    elif current_status == DeploymentStatus.GENERATING:
        remaining_steps = [
            DeploymentStatus.INITIALIZING,
            DeploymentStatus.PLANNING,
            DeploymentStatus.APPLYING,
        ]
    elif current_status == DeploymentStatus.INITIALIZING:
        remaining_steps = [
            DeploymentStatus.PLANNING,
            DeploymentStatus.APPLYING,
        ]
    elif current_status == DeploymentStatus.PLANNING:
        remaining_steps = [DeploymentStatus.APPLYING]
    elif current_status == DeploymentStatus.APPLYING:
        # Almost done, estimate 50% of apply time remaining
        return AVERAGE_STEP_DURATIONS.get(DeploymentStatus.APPLYING, 120.0) * 0.5
    elif current_status == DeploymentStatus.DESTROYING:
        return AVERAGE_STEP_DURATIONS.get(DeploymentStatus.DESTROYING, 60.0) * 0.5
    else:
        return None

    # Summiere durchschnittliche Dauern
    total_remaining = sum(
        AVERAGE_STEP_DURATIONS.get(step, 0.0)
        for step in remaining_steps
    )

    return total_remaining if total_remaining > 0 else None
