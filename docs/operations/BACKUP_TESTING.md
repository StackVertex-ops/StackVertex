# Backup Restore Testing

**Zweck:** Regelmäßig validieren dass Backups funktionieren  
**Frequenz:** Monatlich  
**Dauer:** ~10-15 Minuten  
**Automatisiert:** ✅ Ja (via Script)

---

## Quick Start

```bash
# Staging Environment testen
cd infrastructure/terraform/scripts
./test-backup-restore.sh staging

# Production Environment testen (vorsichtig!)
./test-backup-restore.sh production
```

---

## Was wird getestet?

1. **DynamoDB Backup & Restore**
   - Point-in-Time Backup erstellen
   - In Test-Tabelle wiederherstellen
   - Item-Count vergleichen
   - Sample-Daten verifizieren

2. **S3 Backup & Restore**
   - Bucket-Sync in Test-Bucket
   - Object-Count vergleichen
   - Integrität prüfen

3. **Cleanup**
   - Test-Ressourcen automatisch löschen
   - Backup-Snapshot entfernen

---

## Output

**Success:**
```
✅ BACKUP RESTORE TEST PASSED
DynamoDB: 1234 items restored correctly
S3:       567 objects synced correctly
Duration: 180 seconds
```

**Failure:**
```
❌ Item count mismatch! Expected: 1234, Got: 1200
```

---

## Troubleshooting

**Error: "Source table not found"**
- Lösung: Richtige Environment prüfen (staging/production)

**Error: "Backup failed"**
- Lösung: PITR (Point-in-Time Recovery) in DynamoDB aktivieren

**Error: "Restore timeout"**
- Lösung: Restore dauert länger bei großen Tabellen (normal)

---

## Schedule

**Empfohlene Frequenz:**
- Development: Optional
- Staging: Monatlich
- Production: Monatlich (PFLICHT!)

**Cron Setup:**
```bash
# Jeden 1. des Monats um 3 Uhr morgens
0 3 1 * * /path/to/test-backup-restore.sh production >> /var/log/backup-test.log 2>&1
```

---

## Compliance

**ISO 27001:** A.12.3.1 (Backup-Verifikation)  
**SOC 2:** CC6.1 (Data Backup Testing)  
**DSGVO:** Art. 32 (Wiederherstellbarkeit)

---

**Erstellt:** 2026-05-17  
**Script:** `infrastructure/terraform/scripts/test-backup-restore.sh`
