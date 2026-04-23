#!/usr/bin/env python3
"""Validiert die geseedeten Architekturen gegen das JSON-Schema."""

import sys
import json
from pathlib import Path

# Python-Path anpassen
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from jsonschema import validate, ValidationError
from app.models.database import SessionLocal
from app.models.architecture import Architecture


def validate_architectures():
    """Validiert alle Architekturen in der Datenbank gegen das Schema."""

    # Lade JSON Schema
    schema_path = backend_dir.parent / "docs" / "json-schemas" / "architecture-v1.0.0.schema.json"

    if not schema_path.exists():
        print(f"❌ Schema-Datei nicht gefunden: {schema_path}")
        return False

    with open(schema_path) as f:
        schema = json.load(f)

    print("=" * 60)
    print("🔍 Validiere Architekturen gegen JSON-Schema")
    print("=" * 60)
    print()

    db = SessionLocal()
    all_valid = True

    try:
        architectures = db.query(Architecture).all()

        if not architectures:
            print("⚠️  Keine Architekturen in der Datenbank gefunden")
            print("   Führe zuerst 'scripts/seed.sh' aus")
            return False

        for arch in architectures:
            try:
                # Validiere architecture_json gegen Schema
                validate(instance=arch.architecture_json, schema=schema)
                print(f"✅ {arch.name}")
                print(f"   Version: {arch.version}")
                print(f"   Provider: {arch.architecture_json['metadata']['provider']}")
                print(f"   Komponenten: {len(arch.architecture_json['architecture']['components'])}")
                print()
            except ValidationError as e:
                all_valid = False
                print(f"❌ {arch.name}")
                print(f"   Validierungsfehler: {e.message}")
                print(f"   Pfad: {' > '.join(str(p) for p in e.path)}")
                print()

        if all_valid:
            print("=" * 60)
            print(f"✨ Alle {len(architectures)} Architekturen sind schema-konform!")
            print("=" * 60)
        else:
            print("=" * 60)
            print("❌ Einige Architekturen haben Validierungsfehler")
            print("=" * 60)

        return all_valid

    finally:
        db.close()


if __name__ == "__main__":
    success = validate_architectures()
    sys.exit(0 if success else 1)
