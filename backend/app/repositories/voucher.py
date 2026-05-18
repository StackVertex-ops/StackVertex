"""Voucher Repository.

Verwaltet Gutscheine/Voucher für Rabatte auf Subscriptions.
"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from boto3.dynamodb.conditions import Key, Attr

from app.repositories.base import BaseRepository


class VoucherRepository(BaseRepository):
    """Repository für Voucher Management."""

    def create(
        self,
        code: str,
        discount_type: str,
        discount_value: float,
        applies_to: str,
        max_uses: int = 1,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        created_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Erstellt neuen Gutschein.

        Args:
            code: Eindeutiger Gutscheincode (z.B. "FRIEND2026")
            discount_type: "percentage" oder "fixed"
            discount_value: Rabattwert (10, 25, 50, 75, 100 für Prozent, oder fixer €-Betrag)
            applies_to: "base_fee", "aws_percentage", oder "both"
            max_uses: Maximale Verwendungen (1 für einmalig, -1 für unbegrenzt)
            valid_from: Gültig ab (optional)
            valid_until: Gültig bis (optional)
            created_by: User ID des Erstellers (SuperAdmin)

        Returns:
            Erstellter Voucher

        Raises:
            ValueError: Wenn Code bereits existiert
        """
        # Code muss uppercase sein (case-insensitive)
        code = code.upper()

        # Prüfe ob Code bereits existiert
        existing = self.get_by_code(code)
        if existing:
            raise ValueError(f"Voucher code '{code}' already exists")

        # Validierung
        if len(code) < 4 or len(code) > 32:
            raise ValueError("Code must be between 4 and 32 characters")

        if not code.isalnum():
            raise ValueError("Code must contain only A-Z and 0-9")

        if discount_value <= 0:
            raise ValueError("Discount value must be greater than 0")

        if discount_type == "percentage" and discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100%")

        if applies_to not in ["base_fee", "aws_percentage", "both"]:
            raise ValueError("applies_to must be 'base_fee', 'aws_percentage', or 'both'")

        if valid_until and valid_until < datetime.utcnow():
            raise ValueError("valid_until must be in the future")

        item = {
            "PK": f"VOUCHER#{code}",
            "SK": "METADATA",
            "code": code,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "applies_to": applies_to,
            "max_uses": max_uses,
            "current_uses": 0,
            "valid_from": valid_from.isoformat() if valid_from else None,
            "valid_until": valid_until.isoformat() if valid_until else None,
            "created_by": str(created_by) if created_by else None,
            "is_active": True,
            "used_by": [],  # Liste von user_ids
            # GSI für schnelle Lookup aller Vouchers
            "GSI1PK": "VOUCHERS",
            "GSI1SK": code,
        }

        return self._put_item(item)

    def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Findet Voucher anhand Code (case-insensitive).

        Args:
            code: Gutscheincode

        Returns:
            Voucher item oder None
        """
        code = code.upper()
        return self._get_item(f"VOUCHER#{code}", "METADATA")

    def validate(self, code: str, user_id: UUID) -> Dict[str, Any]:
        """Validiert ob Voucher verwendet werden kann.

        Args:
            code: Gutscheincode
            user_id: User ID der verwenden möchte

        Returns:
            Dict mit Validierungsergebnis und Details

        Raises:
            ValueError: Wenn Voucher nicht gefunden oder ungültig
        """
        voucher = self.get_by_code(code)

        if not voucher:
            raise ValueError(f"Voucher code '{code}' not found")

        # Prüfe ob aktiv
        if not voucher.get("is_active", False):
            raise ValueError("Voucher has been deactivated")

        # Prüfe Zeitfenster
        now = datetime.utcnow()

        if voucher.get("valid_from"):
            valid_from = datetime.fromisoformat(voucher["valid_from"])
            if now < valid_from:
                raise ValueError(f"Voucher not yet valid (valid from {valid_from.date()})")

        if voucher.get("valid_until"):
            valid_until = datetime.fromisoformat(voucher["valid_until"])
            if now > valid_until:
                raise ValueError(f"Voucher expired on {valid_until.date()}")

        # Prüfe max_uses
        max_uses = voucher.get("max_uses", 1)
        current_uses = voucher.get("current_uses", 0)

        if max_uses != -1 and current_uses >= max_uses:
            raise ValueError(f"Voucher usage limit reached ({max_uses} uses)")

        # Prüfe ob User bereits verwendet hat
        used_by = voucher.get("used_by", [])
        if str(user_id) in used_by:
            raise ValueError("You have already used this voucher")

        # Voucher ist gültig
        return {
            "valid": True,
            "code": voucher["code"],
            "discount_type": voucher["discount_type"],
            "discount_value": voucher["discount_value"],
            "applies_to": voucher["applies_to"],
            "remaining_uses": max_uses - current_uses if max_uses != -1 else -1
        }

    def redeem(self, code: str, user_id: UUID) -> Dict[str, Any]:
        """Markiert Voucher als verwendet.

        Args:
            code: Gutscheincode
            user_id: User ID

        Returns:
            Aktualisierter Voucher

        Raises:
            ValueError: Wenn Voucher nicht validiert werden kann
        """
        # Validiere zuerst
        self.validate(code, user_id)

        code = code.upper()
        voucher = self.get_by_code(code)

        # Inkrementiere current_uses
        current_uses = voucher.get("current_uses", 0)
        used_by = voucher.get("used_by", [])
        used_by.append(str(user_id))

        updates = {
            "current_uses": current_uses + 1,
            "used_by": used_by,
            "last_used_at": datetime.utcnow().isoformat()
        }

        return self._update_item(
            pk=f"VOUCHER#{code}",
            sk="METADATA",
            updates=updates
        )

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> tuple[List[Dict[str, Any]], int]:
        """Listet alle Vouchers (für Admin).

        Args:
            skip: Pagination offset
            limit: Max items
            include_inactive: Inkludiere deaktivierte Vouchers

        Returns:
            Tuple von (items, total_count)
        """
        # Query via GSI1
        items, _ = self._query(
            key_condition=Key("GSI1PK").eq("VOUCHERS"),
            index_name="GSI1",
            limit=limit + skip
        )

        # Filter deaktivierte wenn nicht gewünscht
        if not include_inactive:
            items = [item for item in items if item.get("is_active", False)]

        total = len(items)
        items = items[skip:skip + limit]

        return items, total

    def deactivate(self, code: str) -> Dict[str, Any]:
        """Deaktiviert Voucher (soft delete).

        Args:
            code: Gutscheincode

        Returns:
            Aktualisierter Voucher

        Raises:
            ValueError: Wenn Voucher nicht gefunden
        """
        code = code.upper()
        voucher = self.get_by_code(code)

        if not voucher:
            raise ValueError(f"Voucher code '{code}' not found")

        return self._update_item(
            pk=f"VOUCHER#{code}",
            sk="METADATA",
            updates={
                "is_active": False,
                "deactivated_at": datetime.utcnow().isoformat()
            }
        )

    def reactivate(self, code: str) -> Dict[str, Any]:
        """Reaktiviert deaktivierten Voucher.

        Args:
            code: Gutscheincode

        Returns:
            Aktualisierter Voucher

        Raises:
            ValueError: Wenn Voucher nicht gefunden
        """
        code = code.upper()
        voucher = self.get_by_code(code)

        if not voucher:
            raise ValueError(f"Voucher code '{code}' not found")

        return self._update_item(
            pk=f"VOUCHER#{code}",
            sk="METADATA",
            updates={
                "is_active": True,
                "reactivated_at": datetime.utcnow().isoformat()
            }
        )

    def get_usage_stats(self, code: str) -> Dict[str, Any]:
        """Gibt Nutzungsstatistiken für Voucher zurück.

        Args:
            code: Gutscheincode

        Returns:
            Dict mit Statistiken

        Raises:
            ValueError: Wenn Voucher nicht gefunden
        """
        voucher = self.get_by_code(code)

        if not voucher:
            raise ValueError(f"Voucher code '{code}' not found")

        max_uses = voucher.get("max_uses", 1)
        current_uses = voucher.get("current_uses", 0)
        remaining = max_uses - current_uses if max_uses != -1 else -1

        return {
            "code": voucher["code"],
            "max_uses": max_uses,
            "current_uses": current_uses,
            "remaining_uses": remaining,
            "usage_percentage": (current_uses / max_uses * 100) if max_uses > 0 else 0,
            "unique_users": len(voucher.get("used_by", [])),
            "is_active": voucher.get("is_active", False),
            "valid_from": voucher.get("valid_from"),
            "valid_until": voucher.get("valid_until"),
            "last_used_at": voucher.get("last_used_at")
        }
