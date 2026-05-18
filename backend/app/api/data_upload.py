"""Data Upload API - Docker Images, Static Files, DockerHub Import.

Erlaubt Upload von User-Daten zu OverCloud S3 Bucket.
"""

import logging
from typing import List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError

from app.api.auth import get_current_user
from app.config import settings
from app.services.audit_logger import log_audit

logger = logging.getLogger(__name__)
router = APIRouter()

# S3 Client
s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

# TODO: Aus Terraform Output oder Config laden
USER_DATA_BUCKET = settings.S3_LARGE_ITEMS_BUCKET  # Placeholder - muss angepasst werden


@router.post("/data-upload/docker-image")
async def upload_docker_image(
    deployment_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload Docker Image (.tar/.tar.gz) zu OverCloud S3.

    Args:
        deployment_id: ID des Deployments
        file: Docker Image als .tar oder .tar.gz
        current_user: Aktueller User (via Depends)

    Returns:
        Upload Info mit S3 Key und Größe

    Raises:
        HTTPException: Bei fehlenden Permissions oder Upload-Fehler
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    # Validate File Type
    if not file.filename.endswith(('.tar.gz', '.tar')):
        raise HTTPException(400, detail="Nur .tar.gz oder .tar Dateien erlaubt")

    # Validate File Size (max 5GB)
    MAX_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
    if file.size and file.size > MAX_SIZE:
        raise HTTPException(413, detail=f"Datei zu groß (max {MAX_SIZE / (1024**3):.1f}GB)")

    # S3 Path: {org_id}/{deployment_id}/docker-images/{filename}
    s3_key = f"{org_id}/{deployment_id}/docker-images/{file.filename}"

    try:
        # Upload to S3 (streaming)
        s3_client.upload_fileobj(
            file.file,
            USER_DATA_BUCKET,
            s3_key,
            ExtraArgs={
                'ServerSideEncryption': 'aws:kms',
                'Metadata': {
                    'uploaded_by': str(current_user["id"]),
                    'deployment_id': deployment_id,
                    'original_filename': file.filename
                }
            }
        )

        logger.info(
            f"Docker Image hochgeladen: {s3_key} "
            f"(User: {current_user['id']}, Size: {file.size})"
        )

        # Audit Log
        log_audit(
            action="data_upload.docker_image",
            user=str(current_user["id"]),
            resource_type="docker_image",
            resource_id=s3_key,
            details={
                "deployment_id": deployment_id,
                "filename": file.filename,
                "size_bytes": file.size
            }
        )

        return {
            "message": "Docker Image erfolgreich hochgeladen",
            "s3_key": s3_key,
            "size_bytes": file.size,
            "bucket": USER_DATA_BUCKET
        }

    except ClientError as e:
        logger.error(f"S3 Upload fehlgeschlagen: {e}")
        raise HTTPException(500, detail=f"Upload fehlgeschlagen: {str(e)}")


@router.post("/data-upload/files")
async def upload_files(
    deployment_id: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload Static Files (build/, configs, etc.).

    Args:
        deployment_id: ID des Deployments
        files: Liste von Files
        current_user: Aktueller User

    Returns:
        Liste der hochgeladenen Files

    Raises:
        HTTPException: Bei Upload-Fehler
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    uploaded_files = []
    failed_files = []

    for file in files:
        # S3 Path (preserve directory structure)
        s3_key = f"{org_id}/{deployment_id}/static-files/{file.filename}"

        try:
            s3_client.upload_fileobj(
                file.file,
                USER_DATA_BUCKET,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'aws:kms',
                    'Metadata': {
                        'uploaded_by': str(current_user["id"]),
                        'deployment_id': deployment_id
                    }
                }
            )

            uploaded_files.append({
                "filename": file.filename,
                "s3_key": s3_key,
                "size_bytes": file.size
            })

            logger.info(f"File hochgeladen: {s3_key}")

        except ClientError as e:
            logger.error(f"Upload fehlgeschlagen für {file.filename}: {e}")
            failed_files.append({
                "filename": file.filename,
                "error": str(e)
            })

    # Audit Log
    log_audit(
        action="data_upload.static_files",
        user=str(current_user["id"]),
        resource_type="static_files",
        resource_id=deployment_id,
        details={
            "deployment_id": deployment_id,
            "uploaded_count": len(uploaded_files),
            "failed_count": len(failed_files)
        }
    )

    return {
        "message": f"{len(uploaded_files)} Files erfolgreich hochgeladen",
        "uploaded": uploaded_files,
        "failed": failed_files
    }


@router.post("/data-upload/from-dockerhub")
async def import_from_dockerhub(
    deployment_id: str,
    image: str,
    background_tasks: BackgroundTasks,
    dockerhub_username: str = None,
    dockerhub_token: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Import Docker Image von DockerHub.

    Läuft im Background:
    1. docker pull {image}
    2. docker save {image} -o /tmp/image.tar.gz
    3. Upload to S3
    4. Cleanup

    Args:
        deployment_id: ID des Deployments
        image: Docker Image (z.B. "nginx:latest")
        background_tasks: FastAPI Background Tasks
        dockerhub_username: DockerHub Username (optional, für private Images)
        dockerhub_token: DockerHub Token (optional)
        current_user: Aktueller User

    Returns:
        Status Message (async processing)
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    # Validate Image Name
    if not image or "/" not in image and ":" not in image:
        raise HTTPException(400, detail="Ungültiger Image Name (Format: repo/name:tag)")

    # Schedule Background Task
    background_tasks.add_task(
        _import_dockerhub_image,
        org_id=org_id,
        deployment_id=deployment_id,
        image=image,
        dockerhub_username=dockerhub_username,
        dockerhub_token=dockerhub_token,
        user=str(current_user["id"])
    )

    logger.info(f"DockerHub Import gestartet: {image} (Deployment: {deployment_id})")

    return {
        "message": "DockerHub Import gestartet",
        "image": image,
        "deployment_id": deployment_id,
        "status": "processing"
    }


async def _import_dockerhub_image(
    org_id: str,
    deployment_id: str,
    image: str,
    dockerhub_username: str,
    dockerhub_token: str,
    user_id: str
):
    """Background Task: Import Docker Image von DockerHub.

    Args:
        org_id: Organisation ID
        deployment_id: Deployment ID
        image: Docker Image Name
        dockerhub_username: DockerHub Username (optional)
        dockerhub_token: DockerHub Token (optional)
        user_id: User ID (für Audit Log)
    """
    import subprocess
    import tempfile
    from pathlib import Path

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tar_file = temp_path / "image.tar.gz"

            # 1. Docker Login (falls Credentials vorhanden)
            if dockerhub_username and dockerhub_token:
                logger.info(f"Docker Login als {dockerhub_username}")
                subprocess.run(
                    ["docker", "login", "-u", dockerhub_username, "--password-stdin"],
                    input=dockerhub_token.encode(),
                    check=True
                )

            # 2. Docker Pull
            logger.info(f"Docker Pull: {image}")
            subprocess.run(["docker", "pull", image], check=True)

            # 3. Docker Save
            logger.info(f"Docker Save: {image} -> {tar_file}")
            subprocess.run(
                ["docker", "save", image, "-o", str(tar_file)],
                check=True
            )

            # 4. Compress (gzip)
            logger.info("Komprimiere Image...")
            subprocess.run(["gzip", str(tar_file)], check=True)
            tar_gz_file = Path(str(tar_file) + ".gz")

            # 5. Upload to S3
            s3_key = f"{org_id}/{deployment_id}/docker-images/{image.replace('/', '_')}.tar.gz"

            logger.info(f"Upload zu S3: {s3_key}")
            with open(tar_gz_file, 'rb') as f:
                s3_client.upload_fileobj(
                    f,
                    USER_DATA_BUCKET,
                    s3_key,
                    ExtraArgs={
                        'ServerSideEncryption': 'aws:kms',
                        'Metadata': {
                            'uploaded_by': user_id,
                            'deployment_id': deployment_id,
                            'source': 'dockerhub',
                            'original_image': image
                        }
                    }
                )

            logger.info(f"DockerHub Import erfolgreich: {image}")

            # Audit Log
            log_audit(
                action="data_upload.dockerhub_import",
                user=user_id,
                resource_type="docker_image",
                resource_id=s3_key,
                details={
                    "deployment_id": deployment_id,
                    "image": image,
                    "s3_key": s3_key
                }
            )

    except subprocess.CalledProcessError as e:
        logger.error(f"DockerHub Import fehlgeschlagen: {e}")
        # TODO: Update Deployment Status auf "failed"

    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim DockerHub Import: {e}")


@router.get("/data-upload/list/{deployment_id}")
async def list_uploaded_files(
    deployment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Listet alle hochgeladenen Files für ein Deployment.

    Args:
        deployment_id: Deployment ID
        current_user: Aktueller User

    Returns:
        Liste von Files mit Metadata
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    prefix = f"{org_id}/{deployment_id}/"

    try:
        response = s3_client.list_objects_v2(
            Bucket=USER_DATA_BUCKET,
            Prefix=prefix
        )

        files = []
        for obj in response.get('Contents', []):
            # Hole Metadata
            metadata_response = s3_client.head_object(
                Bucket=USER_DATA_BUCKET,
                Key=obj['Key']
            )

            files.append({
                "key": obj['Key'],
                "size_bytes": obj['Size'],
                "last_modified": obj['LastModified'].isoformat(),
                "metadata": metadata_response.get('Metadata', {})
            })

        return {
            "deployment_id": deployment_id,
            "files": files,
            "total_size_bytes": sum(f['size_bytes'] for f in files)
        }

    except ClientError as e:
        logger.error(f"Fehler beim Auflisten der Files: {e}")
        raise HTTPException(500, detail=str(e))


@router.delete("/data-upload/{deployment_id}")
async def delete_deployment_data(
    deployment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Löscht alle hochgeladenen Daten für ein Deployment.

    Args:
        deployment_id: Deployment ID
        current_user: Aktueller User

    Returns:
        Delete Summary
    """
    org_id = current_user.get("organisation_id")
    if not org_id:
        raise HTTPException(400, detail="User muss in einer Organisation sein")

    prefix = f"{org_id}/{deployment_id}/"

    try:
        # Liste alle Objects
        response = s3_client.list_objects_v2(
            Bucket=USER_DATA_BUCKET,
            Prefix=prefix
        )

        objects = response.get('Contents', [])
        if not objects:
            return {"message": "Keine Daten gefunden", "deleted_count": 0}

        # Lösche alle Objects
        delete_keys = [{'Key': obj['Key']} for obj in objects]

        s3_client.delete_objects(
            Bucket=USER_DATA_BUCKET,
            Delete={'Objects': delete_keys}
        )

        logger.info(f"Deployment Daten gelöscht: {deployment_id} ({len(objects)} Files)")

        # Audit Log
        log_audit(
            action="data_upload.delete_deployment_data",
            user=str(current_user["id"]),
            resource_type="deployment_data",
            resource_id=deployment_id,
            details={
                "deployment_id": deployment_id,
                "deleted_count": len(objects)
            }
        )

        return {
            "message": f"{len(objects)} Files gelöscht",
            "deleted_count": len(objects)
        }

    except ClientError as e:
        logger.error(f"Fehler beim Löschen: {e}")
        raise HTTPException(500, detail=str(e))
