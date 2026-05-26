#!/usr/bin/env python3
"""Seed Example FAQs.

Erstellt Beispiel-FAQs für StackVertex.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.dynamodb import get_dynamodb_table
from app.repositories.faq import FaqRepository

EXAMPLE_FAQS = [
    # Allgemein
    {
        "category": "general",
        "question": "Was ist StackVertex?",
        "answer": """StackVertex ist eine Plattform zur **anforderungsbasierten Modellierung** von Cloud-Infrastruktur.

Statt Terraform-Code zu schreiben, beschreibst du in JSON **was** du brauchst - StackVertex generiert automatisch:
- Terraform/OpenTofu Code
- Architektur-Diagramme
- Kosten-Schätzungen
- Security-Analysen

Alle Entscheidungen sind **versionierbar** und **transparent**.""",
        "status": "published",
        "sort_order": 0,
    },
    {
        "category": "general",
        "question": "Für wen ist StackVertex geeignet?",
        "answer": """StackVertex ist ideal für:

- **DevOps-Teams**, die Terraform-Code standardisieren wollen
- **Startups**, die schnell produktionsreife Infrastruktur brauchen
- **Enterprise-Kunden**, die Multi-Cloud-Support benötigen
- **Alle**, die Cloud-Infrastruktur verstehen und kontrollieren wollen

Keine Terraform-Kenntnisse erforderlich!""",
        "status": "published",
        "sort_order": 1,
    },
    {
        "category": "general",
        "question": "Welche Cloud-Provider werden unterstützt?",
        "answer": """Aktuell (MVP Phase):
- ✅ **AWS** (vollständig)

In Planung (2024):
- 🔜 **Azure**
- 🔜 **Google Cloud (GCP)**

Die JSON-basierte Architektur ermöglicht **Vendor-Lock-In-freien** Wechsel zwischen Providern.""",
        "status": "published",
        "sort_order": 2,
    },

    # Preise
    {
        "category": "pricing",
        "question": "Was kostet StackVertex?",
        "answer": """StackVertex nutzt ein **nutzungsbasiertes** Pricing-Modell:

- **Free Tier**: 3 Architekturen, 5 Deployments/Monat - kostenlos
- **Pro**: €29/Monat - unlimitiert
- **Enterprise**: Custom Pricing - SLA, Support, Self-Hosting

**Keine versteckten Kosten!** Du zahlst nur die AWS-Kosten deiner Infrastruktur.""",
        "status": "published",
        "sort_order": 0,
    },
    {
        "category": "pricing",
        "question": "Fallen zusätzliche Cloud-Kosten an?",
        "answer": """Ja, aber **StackVertex ist transparent**:

- Vor jedem Deployment siehst du eine **Kosten-Schätzung**
- Du zahlst nur die **tatsächlichen AWS-Kosten**
- StackVertex hat **keine Aufschläge** auf deine Cloud-Kosten

Beispiel: Eine kleine Web-App kostet ca. **$20-50/Monat** auf AWS.""",
        "status": "published",
        "sort_order": 1,
    },

    # Technik
    {
        "category": "technical",
        "question": "Wie funktioniert das JSON-First-Prinzip?",
        "answer": """Alle Architektur-Entscheidungen werden als **JSON** gespeichert:

```json
{
  "version": "1.0.0",
  "requirements": {
    "type": "web-app",
    "scalability": "high"
  },
  "architecture": {
    "components": [...]
  }
}
```

Daraus wird **automatisch** Terraform-Code generiert. JSON ist die **einzige Wahrheit** (Source of Truth).""",
        "status": "published",
        "sort_order": 0,
    },
    {
        "category": "technical",
        "question": "Kann ich den generierten Terraform-Code anpassen?",
        "answer": """**Nein** - das ist Absicht!

Der Terraform-Code ist **generierter Output**, nicht die Wahrheit. Änderungen machst du in der JSON-Datei.

**Vorteil**: Terraform bleibt konsistent und versionierbar.

Für individuelle Anpassungen kannst du **Custom Templates** definieren.""",
        "status": "published",
        "sort_order": 1,
    },

    # Sicherheit
    {
        "category": "security",
        "question": "Wie sicher ist StackVertex?",
        "answer": """StackVertex folgt **Best Practices**:

- 🔐 **Keine hardcoded Secrets** - alles über AWS Secrets Manager
- ✅ **AssumeRole statt Access Keys** - IAM-basiert
- 📊 **Audit Logs** - alle Aktionen werden geloggt
- 🛡️ **Least Privilege** - minimale Berechtigungen
- 🔒 **AES-256 Verschlüsselung** - at rest & in transit

**DSGVO-konform** und **SOC2-ready**.""",
        "status": "published",
        "sort_order": 0,
    },
    {
        "category": "security",
        "question": "Wo werden meine Daten gespeichert?",
        "answer": """**Separation of Concerns**:

- **StackVertex (Plattform)**: Metadata, JSON-Schemas, Logs → EU (Frankfurt)
- **Deine Infrastruktur**: Produktions-Daten, Secrets → Dein AWS-Account

StackVertex hat **keinen Zugriff** auf deine Produktionsdaten!""",
        "status": "published",
        "sort_order": 1,
    },

    # Support
    {
        "category": "support",
        "question": "Wie erreiche ich den Support?",
        "answer": """**Mehrere Wege**:

- 📧 **Email**: support@stackvertex.io
- 💬 **Feedback-Widget** auf der Seite
- 📚 **Dokumentation**: docs.stackvertex.io
- 🐛 **GitHub Issues**: github.com/AndySchw/StackVertex

**Response Time**:
- Free: Best-Effort
- Pro: 24h
- Enterprise: SLA""",
        "status": "published",
        "sort_order": 0,
    },
]


def seed_faqs():
    """Seed example FAQs."""
    print("🌱 Seeding example FAQs...")

    table = get_dynamodb_table()
    faq_repo = FaqRepository(table=table)

    # Check if FAQs already exist
    existing, _ = faq_repo.list_faqs(limit=1)
    if existing:
        print(f"⚠️  FAQs already exist. Skipping seed.")
        return

    # Create FAQs
    for faq_data in EXAMPLE_FAQS:
        try:
            faq = faq_repo.create_faq(
                category=faq_data["category"],
                question=faq_data["question"],
                answer=faq_data["answer"],
                status=faq_data["status"],
                sort_order=faq_data["sort_order"],
                created_by="system",
            )
            print(f"✅ Created FAQ: {faq['question'][:50]}...")
        except Exception as e:
            print(f"❌ Failed to create FAQ: {e}")

    print(f"\n✨ Created {len(EXAMPLE_FAQS)} example FAQs!")


if __name__ == "__main__":
    seed_faqs()
