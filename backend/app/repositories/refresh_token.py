"""Refresh Token Repository (DynamoDB).

Manages Refresh Tokens with Token Rotation for secure JWT authentication.
"""

import hashlib
from datetime import datetime
from uuid import UUID, uuid4

from boto3.dynamodb.conditions import Key

from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository):
    """Repository für Refresh Tokens mit Token Rotation.

    Features:
    - Token Rotation: Jeder Refresh gibt neues Refresh Token
    - Token Hashing: Tokens werden gehasht gespeichert (nicht im Klartext)
    - Automatic TTL: DynamoDB löscht abgelaufene Tokens automatisch
    - Revocation: Tokens können invalidiert werden (z.B. bei Logout)
    """

    def create(self, user_id: UUID, token: str, expires_at: datetime) -> dict:
        """Speichert Refresh Token.

        Args:
            user_id: User UUID
            token: Refresh Token (JWT)
            expires_at: Ablaufdatum

        Returns:
            Token Item
        """
        token_id = str(uuid4())
        token_hash = self._hash_token(token)

        item = {
            "PK": f"USER#{user_id}",
            "SK": f"REFRESH_TOKEN#{token_id}",
            "id": token_id,
            "user_id": str(user_id),
            "token_hash": token_hash,
            "expires_at": expires_at.isoformat(),
            "revoked": False,
            # GSI für Token Lookup (via Hash)
            "GSI1PK": f"REFRESH_TOKEN#{token_hash}",
            "GSI1SK": "METADATA",
            # TTL für automatisches Cleanup (Unix Timestamp)
            "ttl": int(expires_at.timestamp())
        }

        return self._put_item(item)

    def get_by_token(self, token: str) -> dict | None:
        """Findet Refresh Token via GSI.

        Args:
            token: Refresh Token (JWT)

        Returns:
            Token Item oder None
        """
        token_hash = self._hash_token(token)

        items, _ = self._query(
            key_condition=Key("GSI1PK").eq(f"REFRESH_TOKEN#{token_hash}") &
                          Key("GSI1SK").eq("METADATA"),
            index_name="GSI1"
        )

        if not items:
            return None

        token_item = items[0]

        # Check if expired
        expires_at = datetime.fromisoformat(token_item["expires_at"])
        if datetime.utcnow() > expires_at:
            return None

        # Check if revoked
        if token_item.get("revoked"):
            return None

        return token_item

    def revoke(self, token_id: str, user_id: UUID) -> dict:
        """Revoked Refresh Token (Token Rotation).

        Args:
            token_id: Token UUID
            user_id: User UUID

        Returns:
            Updated token item
        """
        return self._update_item(
            pk=f"USER#{user_id}",
            sk=f"REFRESH_TOKEN#{token_id}",
            updates={"revoked": True}
        )

    def revoke_all_for_user(self, user_id: UUID) -> int:
        """Revoked alle Refresh Tokens eines Users (bei Logout all devices).

        Args:
            user_id: User UUID

        Returns:
            Anzahl revoked Tokens
        """
        # Query all refresh tokens for user
        items, _ = self._query(
            key_condition=Key("PK").eq(f"USER#{user_id}") &
                          Key("SK").begins_with("REFRESH_TOKEN#")
        )

        # Revoke each
        count = 0
        for item in items:
            if not item.get("revoked"):
                self._update_item(
                    pk=item["PK"],
                    sk=item["SK"],
                    updates={"revoked": True}
                )
                count += 1

        return count

    def delete_expired(self) -> int:
        """Löscht abgelaufene Tokens (TTL cleanup).

        Hinweis: DynamoDB TTL macht das automatisch, diese Methode
        ist nur für manuelle Cleanups nötig.

        Returns:
            Anzahl gelöschter Tokens
        """
        now = datetime.utcnow()

        # Scan for expired tokens (should be rare with TTL)
        items, _ = self._scan(limit=100)  # Limit to avoid long scans

        count = 0
        for item in items:
            if "expires_at" in item:
                expires_at = datetime.fromisoformat(item["expires_at"])
                if expires_at < now:
                    self._delete_item(pk=item["PK"], sk=item["SK"])
                    count += 1

        return count

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash Token für sichere Speicherung (SHA256).

        Args:
            token: Token im Klartext

        Returns:
            SHA256 Hash (Hex)
        """
        return hashlib.sha256(token.encode()).hexdigest()
