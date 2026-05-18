"""AWS Credentials API - Management von Kunden AWS Credentials.

Unterstützt AssumeRole (bevorzugt) und Access Keys (Fallback).
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.repositories.aws_credential import AWSCredentialRepository
from app.services.audit_logger import log_audit

logger = logging.getLogger(__name__)
router = APIRouter()

credential_repo = AWSCredentialRepository()


class CreateCredentialRequest(BaseModel):
    """Request für neue AWS Credentials."""
    name: str = Field(..., min_length=1, max_length=100)
    credential_type: str = Field(..., pattern="^(assume_role|access_key)$")
    region: str = Field(default="us-east-1")

    # AssumeRole Fields
    role_arn: str | None = Field(None, pattern="^arn:aws:iam::\\d{12}:role/.+$")
    external_id: str | None = Field(None, min_length=2, max_length=1224)

    # Access Key Fields
    access_key_id: str | None = Field(None, pattern="^AKIA[0-9A-Z]{16}$")
    secret_access_key: str | None = Field(None, min_length=40)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production AWS Account",
                "credential_type": "assume_role",
                "role_arn": "arn:aws:iam::123456789012:role/OverCloudDeploymentRole",
                "external_id": "unique-external-id-123",
                "region": "us-east-1"
            }
        }


class CredentialResponse(BaseModel):
    """Response mit Credential Metadata (ohne Secrets)."""
    id: str
    org_id: str
    name: str
    credential_type: str
    region: str
    status: str
    last_verified: str | None
    created_at: str


@router.post("/aws-credentials", response_model=CredentialResponse)
async def create_credentials(
    request: CreateCredentialRequest,
    current_user: dict = Depends(get_current_user)
):
    """Erstellt neue AWS Credentials.

    Args:
        request: Credential Request
        current_user: Aktueller User

    Returns:
        Credential Metadata

    Raises:
        HTTPException: Bei Validierungsfehler
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    try:
        credential = credential_repo.create(
            org_id=UUID(org_id),
            credential_type=request.credential_type,
            name=request.name,
            role_arn=request.role_arn,
            external_id=request.external_id,
            access_key_id=request.access_key_id,
            secret_access_key=request.secret_access_key,
            region=request.region
        )

        logger.info(
            f"AWS Credential erstellt: {credential['id']} "
            f"(Org: {org_id}, Type: {request.credential_type})"
        )

        # Audit Log
        log_audit(
            user=str(current_user["id"]),
            action="aws_credentials.create",
            resource_type="aws_credential",
            resource_id=UUID(credential["id"]),
            details={
                "name": request.name,
                "credential_type": request.credential_type,
                "region": request.region,
                "organisation_id": str(org_id)
            }
        )

        return CredentialResponse(**credential)

    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Credentials: {e}")
        raise HTTPException(500, detail="Interner Fehler") from e


@router.post("/aws-credentials/{credential_id}/verify")
async def verify_credentials(
    credential_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Verifiziert AWS Credentials durch Test-Connection.

    Args:
        credential_id: Credential ID
        current_user: Aktueller User

    Returns:
        Verification Result

    Raises:
        HTTPException: Bei fehlenden Credentials
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    try:
        # Verifiziere Credentials
        is_valid = credential_repo.verify_credentials(credential_id)

        # Audit Log
        log_audit(
            user=str(current_user["id"]),
            action="aws_credentials.verify",
            resource_type="aws_credential",
            resource_id=UUID(credential_id),
            details={
                "valid": is_valid,
                "organisation_id": str(org_id)
            }
        )

        return {
            "credential_id": credential_id,
            "valid": is_valid,
            "message": "Credentials gültig" if is_valid else "Credentials ungültig"
        }

    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Fehler bei Credential Verification: {e}")
        raise HTTPException(500, detail="Verification fehlgeschlagen") from e


@router.get("/aws-credentials", response_model=List[CredentialResponse])
async def list_credentials(
    current_user: dict = Depends(get_current_user)
):
    """Listet alle AWS Credentials der Organisation.

    Args:
        current_user: Aktueller User

    Returns:
        Liste von Credentials

    Raises:
        HTTPException: Bei fehlender Organisation
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    credentials = credential_repo.list_by_org(UUID(org_id))

    return [CredentialResponse(**cred) for cred in credentials]


@router.delete("/aws-credentials/{credential_id}")
async def delete_credentials(
    credential_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Löscht AWS Credentials.

    Args:
        credential_id: Credential ID
        current_user: Aktueller User

    Returns:
        Delete Confirmation

    Raises:
        HTTPException: Bei fehlenden Credentials
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    try:
        credential_repo.delete(credential_id)

        logger.info(f"AWS Credential gelöscht: {credential_id} (Org: {org_id})")

        # Audit Log
        log_audit(
            user=str(current_user["id"]),
            action="aws_credentials.delete",
            resource_type="aws_credential",
            resource_id=UUID(credential_id),
            details={
                "organisation_id": str(org_id)
            }
        )

        return {
            "message": "Credentials gelöscht",
            "credential_id": credential_id
        }

    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Credentials: {e}")
        raise HTTPException(500, detail="Löschen fehlgeschlagen") from e


@router.get("/aws-credentials/setup-guide")
async def get_setup_guide():
    """Gibt Setup Guide für AssumeRole zurück.

    Returns:
        Setup Instructions als Markdown
    """
    guide = """
# AWS Credentials Setup Guide

## Option 1: AssumeRole (Empfohlen)

### 1. IAM Role in Ihrem AWS Account erstellen

```bash
# Ersetzen Sie {OverCloudAccountID} mit der OverCloud Account ID
aws iam create-role --role-name OverCloudDeploymentRole \\
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{OverCloudAccountID}:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "your-unique-external-id"
        }
      }
    }]
  }'
```

### 2. Notwendige Policies anhängen

```bash
# EC2, S3, VPC Permissions
aws iam attach-role-policy --role-name OverCloudDeploymentRole \\
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

aws iam attach-role-policy --role-name OverCloudDeploymentRole \\
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy --role-name OverCloudDeploymentRole \\
  --policy-arn arn:aws:iam::aws:policy/AmazonVPCFullAccess
```

### 3. In OverCloud eintragen

- **Role ARN**: `arn:aws:iam::123456789012:role/OverCloudDeploymentRole`
- **External ID**: Ihr unique External ID
- **Region**: `us-east-1` (oder Ihre bevorzugte Region)

---

## Option 2: Access Keys (Fallback)

⚠️ **Nicht empfohlen** - Verwenden Sie AssumeRole für bessere Security!

### 1. IAM User erstellen

```bash
aws iam create-user --user-name overcloud-deployer
```

### 2. Policies anhängen (siehe oben)

### 3. Access Keys erstellen

```bash
aws iam create-access-key --user-name overcloud-deployer
```

### 4. In OverCloud eintragen

- **Access Key ID**: `AKIA...`
- **Secret Access Key**: `...`
- **Region**: `us-east-1`

⚠️ **Speichern Sie diese Keys sicher!**

---

## Security Best Practices

1. **Verwenden Sie immer External ID** bei AssumeRole
2. **Principle of Least Privilege** - Nur notwendige Permissions vergeben
3. **Rotieren Sie Access Keys regelmäßig** (falls verwendet)
4. **Aktivieren Sie CloudTrail** für Audit Logs
5. **Verwenden Sie MFA** für IAM Users (falls Access Keys)
"""

    return {"guide": guide}
