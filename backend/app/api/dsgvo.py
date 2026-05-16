"""
DSGVO (GDPR) Compliance API Endpoints

Implements EU GDPR requirements:
- Art. 15: Right to Access (Data Export)
- Art. 16: Right to Rectification
- Art. 17: Right to Erasure ("Right to be Forgotten")
- Art. 18: Right to Restriction of Processing
- Art. 20: Right to Data Portability
- Art. 21: Right to Object
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.dsgvo_service import (
    export_user_data,
    delete_user_data,
    anonymize_user_data,
    get_user_consents,
    update_user_consent,
    generate_data_export_json,
    schedule_user_deletion,
)

router = APIRouter(prefix="/api/v1/dsgvo", tags=["DSGVO"])


# ===========================
# Data Models
# ===========================


class DataExportRequest(BaseModel):
    """Request for data export (Art. 15)"""

    format: str = "json"  # json, csv, pdf
    include_metadata: bool = True


class DataExportResponse(BaseModel):
    """Response for data export request"""

    export_id: str
    status: str  # pending, ready, expired
    download_url: Optional[str]
    expires_at: datetime
    created_at: datetime


class DataDeletionRequest(BaseModel):
    """Request for data deletion (Art. 17)"""

    reason: str  # user_request, account_closure, other
    confirmation: bool  # Must be True
    delete_backups: bool = True  # Also delete from backups


class DataDeletionResponse(BaseModel):
    """Response for data deletion request"""

    deletion_id: str
    status: str  # scheduled, in_progress, completed
    scheduled_at: datetime
    estimated_completion: datetime
    message: str


class DataRectificationRequest(BaseModel):
    """Request for data rectification (Art. 16)"""

    field: str  # email, name, etc.
    old_value: str
    new_value: str
    reason: Optional[str]


class ConsentUpdateRequest(BaseModel):
    """Request to update consent"""

    consent_type: str  # marketing, analytics, third_party
    granted: bool
    reason: Optional[str]


class ConsentResponse(BaseModel):
    """User consent status"""

    consent_type: str
    granted: bool
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]


# ===========================
# API Endpoints
# ===========================


@router.get("/data-export", response_model=DataExportResponse)
async def request_data_export(
    format: str = "json",
    include_metadata: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """
    Art. 15 DSGVO: Right to Access (Datenauskunft)

    Erstellt einen Export aller personenbezogenen Daten des Users.

    **Enthält:**
    - Profil-Daten (Name, Email, etc.)
    - Erstellte Architekturen (JSON)
    - Deployments Historie
    - Audit Logs (Zugriffe, Änderungen)
    - Consent History

    **Formate:**
    - json: Strukturiertes JSON (maschinell lesbar)
    - csv: CSV-Dateien in ZIP (Excel-kompatibel)
    - pdf: PDF-Report (menschlich lesbar)

    **Compliance:**
    - Export wird innerhalb 30 Tage erstellt (DSGVO Art. 15 Abs. 3)
    - Download-Link ist 7 Tage gültig
    - Export wird nach 7 Tagen automatisch gelöscht
    """
    try:
        # Create export request
        export_data = await export_user_data(
            user_id=current_user.id,
            format=format,
            include_metadata=include_metadata,
            db=db,
        )

        # Schedule background task for large exports
        if background_tasks:
            background_tasks.add_task(
                generate_data_export_json, current_user.id, export_data["export_id"]
            )

        return DataExportResponse(
            export_id=export_data["export_id"],
            status="pending",  # Will be "ready" when background task completes
            download_url=export_data.get("download_url"),
            expires_at=export_data["expires_at"],
            created_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create data export: {str(e)}"
        )


@router.get("/data-export/{export_id}/download")
async def download_data_export(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download data export file

    **Security:**
    - Nur der User selbst kann seinen Export downloaden
    - Export-Link ist nur 7 Tage gültig
    - Nach Download wird Export als "accessed" markiert
    """
    try:
        # Verify export belongs to current user
        export_data = await get_user_export(export_id, current_user.id, db)

        if not export_data:
            raise HTTPException(status_code=404, detail="Export not found")

        if export_data["status"] != "ready":
            raise HTTPException(
                status_code=400, detail=f"Export status: {export_data['status']}"
            )

        # Check expiration
        if datetime.utcnow() > export_data["expires_at"]:
            raise HTTPException(status_code=410, detail="Export has expired")

        # Stream file
        return StreamingResponse(
            export_data["file_stream"],
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="overcloud_data_export_{export_id}.json"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download export: {str(e)}"
        )


@router.post("/data-deletion", response_model=DataDeletionResponse)
async def request_data_deletion(
    request: DataDeletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """
    Art. 17 DSGVO: Right to Erasure ("Right to be Forgotten")

    Löscht alle personenbezogenen Daten des Users unwiderruflich.

    **Was wird gelöscht:**
    - User Account (Email, Password Hash, etc.)
    - Alle Architekturen & Deployments
    - S3 Buckets (Customer Data)
    - Audit Logs (werden anonymisiert)
    - Backups (optional, nach Bestätigung)

    **Was bleibt erhalten:**
    - Anonymisierte Audit Logs (für Compliance)
    - Aggregierte Analytics (keine PII)
    - Rechnungsdaten (gesetzliche Aufbewahrungspflicht: 10 Jahre)

    **Compliance:**
    - Löschung erfolgt innerhalb 30 Tage (DSGVO Art. 17 Abs. 1)
    - Unwiderruflich nach Start (7 Tage Widerrufsfrist)
    - Bestätigung per Email erforderlich

    **Hinweis:** Account-Löschung kann nicht rückgängig gemacht werden!
    """
    # Validate confirmation
    if not request.confirmation:
        raise HTTPException(
            status_code=400,
            detail="Deletion confirmation required. Set confirmation=true to proceed.",
        )

    try:
        # Schedule deletion (with 7-day grace period)
        deletion_data = await schedule_user_deletion(
            user_id=current_user.id,
            reason=request.reason,
            delete_backups=request.delete_backups,
            db=db,
        )

        # Send confirmation email
        if background_tasks:
            background_tasks.add_task(
                send_deletion_confirmation_email,
                current_user.email,
                deletion_data["deletion_id"],
            )

        return DataDeletionResponse(
            deletion_id=deletion_data["deletion_id"],
            status="scheduled",
            scheduled_at=deletion_data["scheduled_at"],
            estimated_completion=deletion_data["estimated_completion"],
            message="Your data will be deleted in 7 days. You will receive a confirmation email.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to schedule deletion: {str(e)}"
        )


@router.delete("/data-deletion/{deletion_id}/cancel")
async def cancel_data_deletion(
    deletion_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel scheduled data deletion (within 7-day grace period)

    **Hinweis:** Nur möglich solange Status "scheduled" ist.
    Nach Start der Löschung (Status "in_progress") ist kein Widerruf mehr möglich.
    """
    try:
        result = await cancel_scheduled_deletion(deletion_id, current_user.id, db)

        if not result:
            raise HTTPException(
                status_code=404, detail="Deletion request not found or already processed"
            )

        return {"message": "Deletion cancelled successfully", "deletion_id": deletion_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel deletion: {str(e)}"
        )


@router.patch("/data-rectification")
async def request_data_rectification(
    request: DataRectificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Art. 16 DSGVO: Right to Rectification (Recht auf Berichtigung)

    Korrigiert fehlerhafte personenbezogene Daten.

    **Erlaubte Felder:**
    - email (mit Email-Verification)
    - name
    - company
    - billing_address

    **Nicht änderbar:**
    - user_id (immutable)
    - created_at (audit trail)
    - password (use /auth/change-password instead)
    """
    # Validate field
    allowed_fields = ["email", "name", "company", "billing_address"]
    if request.field not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Field '{request.field}' cannot be modified. Allowed: {allowed_fields}",
        )

    try:
        # Update field
        updated_user = await update_user_field(
            user_id=current_user.id,
            field=request.field,
            old_value=request.old_value,
            new_value=request.new_value,
            reason=request.reason,
            db=db,
        )

        return {
            "message": f"Field '{request.field}' updated successfully",
            "field": request.field,
            "new_value": request.new_value,
            "updated_at": datetime.utcnow(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update field: {str(e)}"
        )


@router.get("/consents", response_model=list[ConsentResponse])
async def get_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all user consents (Art. 7 DSGVO: Consent Management)

    **Consent Types:**
    - **required**: Terms of Service (immer required für Account)
    - **marketing**: Email Marketing (opt-in)
    - **analytics**: Usage Analytics (opt-in)
    - **third_party**: Datenübermittlung an Dritte (opt-in)
    """
    try:
        consents = await get_user_consents(current_user.id, db)
        return consents

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch consents: {str(e)}")


@router.post("/consents")
async def update_consent(
    request: ConsentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update consent (Art. 7 DSGVO: Consent can be withdrawn at any time)

    **Important:** Consent withdrawal applies immediately.
    Example: Revoking "analytics" consent stops all analytics tracking.
    """
    try:
        result = await update_user_consent(
            user_id=current_user.id,
            consent_type=request.consent_type,
            granted=request.granted,
            reason=request.reason,
            db=db,
        )

        action = "granted" if request.granted else "revoked"
        return {
            "message": f"Consent '{request.consent_type}' {action} successfully",
            "consent_type": request.consent_type,
            "granted": request.granted,
            "updated_at": datetime.utcnow(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update consent: {str(e)}")


@router.get("/processing-activities")
async def get_processing_activities(
    current_user: User = Depends(get_current_user),
):
    """
    Art. 13/14 DSGVO: Information about data processing activities

    **Transparency:** Zeigt alle Verarbeitungstätigkeiten für User-Daten
    """
    return {
        "processing_activities": [
            {
                "activity": "Account Management",
                "purpose": "User authentication and profile management",
                "legal_basis": "Contract (Art. 6 Abs. 1 lit. b DSGVO)",
                "data_categories": ["email", "password_hash", "name"],
                "retention_period": "Until account deletion",
            },
            {
                "activity": "Infrastructure Deployment",
                "purpose": "Deploy and manage cloud infrastructure",
                "legal_basis": "Contract (Art. 6 Abs. 1 lit. b DSGVO)",
                "data_categories": ["architecture_json", "deployment_logs"],
                "retention_period": "2 years after last deployment",
            },
            {
                "activity": "Security Monitoring",
                "purpose": "Detect and prevent security incidents",
                "legal_basis": "Legitimate Interest (Art. 6 Abs. 1 lit. f DSGVO)",
                "data_categories": ["ip_address", "user_agent", "audit_logs"],
                "retention_period": "90 days",
            },
            {
                "activity": "Analytics (opt-in)",
                "purpose": "Improve product and user experience",
                "legal_basis": "Consent (Art. 6 Abs. 1 lit. a DSGVO)",
                "data_categories": ["usage_statistics", "feature_interactions"],
                "retention_period": "12 months",
                "consent_required": True,
            },
        ]
    }


# ===========================
# Helper Functions (to be implemented in dsgvo_service.py)
# ===========================


async def get_user_export(export_id: str, user_id: str, db: Session):
    """Retrieve export data by ID (to be implemented)"""
    # TODO: Implement in dsgvo_service.py
    pass


async def cancel_scheduled_deletion(deletion_id: str, user_id: str, db: Session):
    """Cancel scheduled deletion (to be implemented)"""
    # TODO: Implement in dsgvo_service.py
    pass


async def update_user_field(
    user_id: str, field: str, old_value: str, new_value: str, reason: str, db: Session
):
    """Update user field with audit trail (to be implemented)"""
    # TODO: Implement in dsgvo_service.py
    pass


async def send_deletion_confirmation_email(email: str, deletion_id: str):
    """Send deletion confirmation email (to be implemented)"""
    # TODO: Implement email service
    pass
