"""Invoice Repository.

Manages invoices, payments, and billing history.
"""

from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional
from boto3.dynamodb.conditions import Key

from app.repositories.base import BaseRepository
from app.models.billing import InvoiceStatus


class InvoiceRepository(BaseRepository):
    """Repository für Invoice Management."""

    def create(
        self,
        org_id: UUID,
        invoice_number: str,
        period_start: datetime,
        period_end: datetime,
        line_items: List[Dict[str, Any]],
        subtotal: float,
        tax: float,
        total: float,
        stripe_invoice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new invoice.

        Args:
            org_id: Organisation UUID
            invoice_number: Unique invoice number
            period_start: Billing period start
            period_end: Billing period end
            line_items: List of invoice line items
            subtotal: Subtotal amount
            tax: Tax amount (VAT)
            total: Total amount
            stripe_invoice_id: Optional Stripe invoice ID

        Returns:
            Created invoice
        """
        invoice_id = str(uuid4())

        item = {
            "PK": f"ORG#{org_id}",
            "SK": f"INVOICE#{invoice_number}",
            "id": invoice_id,
            "invoice_number": invoice_number,
            "org_id": str(org_id),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "line_items": line_items,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "status": InvoiceStatus.DRAFT.value,
            "payment_method": "stripe",
            "stripe_invoice_id": stripe_invoice_id,
            "paid_at": None,
            "due_date": None,
            # GSI für Invoice Lookup
            "GSI1PK": f"INVOICE#{invoice_id}",
            "GSI1SK": "METADATA",
        }

        return self._put_item(item)

    def get_by_number(
        self,
        org_id: UUID,
        invoice_number: str
    ) -> Optional[Dict[str, Any]]:
        """Get invoice by number.

        Args:
            org_id: Organisation UUID
            invoice_number: Invoice number

        Returns:
            Invoice or None
        """
        return self._get_item(
            pk=f"ORG#{org_id}",
            sk=f"INVOICE#{invoice_number}"
        )

    def get_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID.

        Args:
            invoice_id: Invoice UUID

        Returns:
            Invoice or None
        """
        items, _ = self._query(
            key_condition=Key("GSI1PK").eq(f"INVOICE#{invoice_id}"),
            index_name="GSI1"
        )

        return items[0] if items else None

    def list_by_org(
        self,
        org_id: UUID,
        limit: int = 50,
        status_filter: Optional[InvoiceStatus] = None
    ) -> List[Dict[str, Any]]:
        """List invoices for organisation.

        Args:
            org_id: Organisation UUID
            limit: Maximum number to return
            status_filter: Optional status filter

        Returns:
            List of invoices (newest first)
        """
        if status_filter:
            items, _ = self._query(
                key_condition=Key("PK").eq(f"ORG#{org_id}") &
                             Key("SK").begins_with("INVOICE#"),
                filter_condition=Key("status").eq(status_filter.value),
                scan_index_forward=False,
                limit=limit
            )
        else:
            items, _ = self._query(
                key_condition=Key("PK").eq(f"ORG#{org_id}") &
                             Key("SK").begins_with("INVOICE#"),
                scan_index_forward=False,
                limit=limit
            )

        return items

    def update_status(
        self,
        org_id: UUID,
        invoice_number: str,
        status: InvoiceStatus,
        paid_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Update invoice status.

        Args:
            org_id: Organisation UUID
            invoice_number: Invoice number
            status: New status
            paid_at: Payment timestamp (if paid)

        Returns:
            Updated invoice
        """
        updates = {"status": status.value}

        if paid_at:
            updates["paid_at"] = paid_at.isoformat()

        return self._update_item(
            pk=f"ORG#{org_id}",
            sk=f"INVOICE#{invoice_number}",
            updates=updates
        )

    def mark_as_sent(
        self,
        org_id: UUID,
        invoice_number: str,
        due_date: datetime
    ) -> Dict[str, Any]:
        """Mark invoice as sent to customer.

        Args:
            org_id: Organisation UUID
            invoice_number: Invoice number
            due_date: Payment due date

        Returns:
            Updated invoice
        """
        return self._update_item(
            pk=f"ORG#{org_id}",
            sk=f"INVOICE#{invoice_number}",
            updates={
                "status": InvoiceStatus.SENT.value,
                "sent_at": datetime.utcnow().isoformat(),
                "due_date": due_date.isoformat()
            }
        )

    def mark_as_paid(
        self,
        org_id: UUID,
        invoice_number: str,
        paid_at: Optional[datetime] = None,
        payment_intent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark invoice as paid.

        Args:
            org_id: Organisation UUID
            invoice_number: Invoice number
            paid_at: Payment timestamp (defaults to now)
            payment_intent_id: Stripe payment intent ID

        Returns:
            Updated invoice
        """
        updates = {
            "status": InvoiceStatus.PAID.value,
            "paid_at": (paid_at or datetime.utcnow()).isoformat()
        }

        if payment_intent_id:
            updates["payment_intent_id"] = payment_intent_id

        return self._update_item(
            pk=f"ORG#{org_id}",
            sk=f"INVOICE#{invoice_number}",
            updates=updates
        )

    def get_overdue_invoices(self) -> List[Dict[str, Any]]:
        """Get all overdue invoices.

        Returns:
            List of overdue invoices
        """
        now = datetime.utcnow().isoformat()

        items, _ = self._scan(
            filter_condition=Key("SK").begins_with("INVOICE#") &
                           Key("status").eq(InvoiceStatus.SENT.value) &
                           Key("due_date").lt(now)
        )

        return items

    def calculate_total_revenue(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Calculate total revenue in a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Revenue breakdown
        """
        items, _ = self._scan(
            filter_condition=Key("SK").begins_with("INVOICE#") &
                           Key("status").eq(InvoiceStatus.PAID.value) &
                           Key("paid_at").between(
                               start_date.isoformat(),
                               end_date.isoformat()
                           )
        )

        total_revenue = sum(item.get("total", 0.0) for item in items)
        total_tax = sum(item.get("tax", 0.0) for item in items)
        total_subtotal = sum(item.get("subtotal", 0.0) for item in items)

        return {
            "total_revenue": round(total_revenue, 2),
            "total_tax": round(total_tax, 2),
            "total_subtotal": round(total_subtotal, 2),
            "invoice_count": len(items)
        }

    def generate_invoice_number(self, org_id: UUID, month: str) -> str:
        """Generate unique invoice number.

        Args:
            org_id: Organisation UUID
            month: Month in format YYYY-MM

        Returns:
            Invoice number (e.g., INV-2026-05-12a3b4c5)
        """
        org_short = str(org_id)[:8]
        return f"INV-{month}-{org_short}"
