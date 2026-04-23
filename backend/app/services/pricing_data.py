"""Pricing Data Loader.

Lädt und cached statische AWS Pricing-Daten.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal
from functools import lru_cache

logger = logging.getLogger(__name__)


class PricingDataLoader:
    """Lädt AWS Pricing-Daten aus JSON-Dateien."""

    def __init__(self, pricing_dir: Optional[Path] = None):
        """Initialisiert Loader.

        Args:
            pricing_dir: Verzeichnis mit Pricing-Dateien (default: backend/data/aws_pricing)
        """
        if pricing_dir is None:
            # Default: backend/data/aws_pricing
            backend_dir = Path(__file__).parent.parent.parent
            pricing_dir = backend_dir / "data" / "aws_pricing"

        self.pricing_dir = pricing_dir
        logger.info(f"Pricing data directory: {self.pricing_dir}")

        # Cache für geladene Pricing-Daten
        self._cache: Dict[str, Dict[str, Any]] = {}

    @lru_cache(maxsize=32)
    def _load_pricing_file(self, filename: str) -> Dict[str, Any]:
        """Lädt Pricing-Datei und cached das Ergebnis.

        Args:
            filename: Dateiname (z.B. "ec2_pricing.json")

        Returns:
            Pricing-Daten als Dict

        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
        """
        file_path = self.pricing_dir / filename

        if not file_path.exists():
            logger.error(f"Pricing file not found: {file_path}")
            raise FileNotFoundError(f"Pricing file not found: {filename}")

        with open(file_path, "r") as f:
            data = json.load(f)

        logger.debug(f"Loaded pricing data from {filename}")
        return data

    def get_ec2_price(
        self,
        instance_type: str,
        region: str = "us-east-1"
    ) -> Optional[Decimal]:
        """Gibt EC2 Preis pro Stunde zurück.

        Args:
            instance_type: Instance Type (z.B. "t3.micro")
            region: AWS Region

        Returns:
            Preis pro Stunde als Decimal, oder None wenn nicht gefunden
        """
        try:
            pricing = self._load_pricing_file("ec2_pricing.json")
            region_pricing = pricing.get("regions", {}).get(region, {})
            instance_pricing = region_pricing.get(instance_type)

            if instance_pricing:
                return Decimal(str(instance_pricing["hourly"]))

            logger.warning(
                f"EC2 pricing not found for {instance_type} in {region}"
            )
            return None

        except Exception as e:
            logger.error(f"Error loading EC2 pricing: {e}")
            return None

    def get_rds_price(
        self,
        instance_class: str,
        region: str = "us-east-1"
    ) -> Optional[Decimal]:
        """Gibt RDS Preis pro Stunde zurück.

        Args:
            instance_class: Instance Class (z.B. "db.t3.micro")
            region: AWS Region

        Returns:
            Preis pro Stunde als Decimal, oder None wenn nicht gefunden
        """
        try:
            pricing = self._load_pricing_file("rds_pricing.json")
            region_pricing = pricing.get("regions", {}).get(region, {})
            instance_pricing = region_pricing.get(instance_class)

            if instance_pricing:
                return Decimal(str(instance_pricing["hourly"]))

            logger.warning(
                f"RDS pricing not found for {instance_class} in {region}"
            )
            return None

        except Exception as e:
            logger.error(f"Error loading RDS pricing: {e}")
            return None

    def get_rds_storage_price(
        self,
        storage_type: str = "gp3",
        region: str = "us-east-1"
    ) -> Optional[Decimal]:
        """Gibt RDS Storage Preis pro GB pro Stunde zurück.

        Args:
            storage_type: Storage Type (gp3, gp2, io1)
            region: AWS Region

        Returns:
            Preis pro GB pro Stunde als Decimal
        """
        try:
            pricing = self._load_pricing_file("rds_pricing.json")
            storage_pricing = pricing.get("storage", {}).get(storage_type)

            if storage_pricing:
                return Decimal(str(storage_pricing["hourly_per_gb"]))

            logger.warning(f"RDS storage pricing not found for {storage_type}")
            return Decimal("0.000137")  # Default gp3 price

        except Exception as e:
            logger.error(f"Error loading RDS storage pricing: {e}")
            return Decimal("0.000137")

    def get_s3_price(
        self,
        storage_class: str = "standard",
        region: str = "us-east-1"
    ) -> Optional[Decimal]:
        """Gibt S3 Storage Preis pro GB pro Monat zurück.

        Args:
            storage_class: Storage Class (standard, intelligent_tiering, glacier)
            region: AWS Region

        Returns:
            Preis pro GB pro Monat als Decimal
        """
        try:
            pricing = self._load_pricing_file("s3_pricing.json")
            storage_classes = pricing.get("storage_classes", {})
            class_pricing = storage_classes.get(storage_class, {}).get(region, {})

            # Für standard: first_50tb
            if "first_50tb" in class_pricing:
                return Decimal(str(class_pricing["first_50tb"]))
            # Für glacier: storage
            elif "storage" in class_pricing:
                return Decimal(str(class_pricing["storage"]))
            # Für intelligent_tiering: frequent_access
            elif "frequent_access" in class_pricing:
                return Decimal(str(class_pricing["frequent_access"]))

            logger.warning(
                f"S3 pricing not found for {storage_class} in {region}"
            )
            return Decimal("0.023")  # Default standard price

        except Exception as e:
            logger.error(f"Error loading S3 pricing: {e}")
            return Decimal("0.023")

    def get_lambda_price(
        self,
        region: str = "us-east-1"
    ) -> Dict[str, Decimal]:
        """Gibt Lambda Pricing zurück.

        Args:
            region: AWS Region

        Returns:
            Dict mit requests_per_million und compute_per_gb_second
        """
        try:
            pricing = self._load_pricing_file("lambda_pricing.json")
            region_pricing = pricing.get("regions", {}).get(region, {})

            return {
                "requests_per_million": Decimal(
                    str(region_pricing.get("requests", {}).get("per_million", 0.20))
                ),
                "compute_per_gb_second": Decimal(
                    str(region_pricing.get("compute", {}).get("per_gb_second", 0.0000166667))
                ),
            }

        except Exception as e:
            logger.error(f"Error loading Lambda pricing: {e}")
            return {
                "requests_per_million": Decimal("0.20"),
                "compute_per_gb_second": Decimal("0.0000166667"),
            }

    def get_all_ec2_instances(self, region: str = "us-east-1") -> Dict[str, Dict]:
        """Gibt alle verfügbaren EC2 Instance Types für eine Region zurück.

        Args:
            region: AWS Region

        Returns:
            Dict mit Instance Types und ihren Details
        """
        try:
            pricing = self._load_pricing_file("ec2_pricing.json")
            return pricing.get("regions", {}).get(region, {})
        except Exception as e:
            logger.error(f"Error loading EC2 instances: {e}")
            return {}
