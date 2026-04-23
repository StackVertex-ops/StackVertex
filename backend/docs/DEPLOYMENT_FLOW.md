# Deployment Flow Documentation

> **OverCloud Async Deployment Architecture**  
> Wie Deployments funktionieren, warum async, und wie man sie verwendet

---

## 🎯 Überblick

OverCloud verwendet **asynchrone Background-Deployments** statt synchrone Requests.

**Warum?**
- Terraform Deployments dauern **1-10 Minuten** (manchmal länger)
- HTTP Timeouts würden bei langen Deployments zuschlagen
- User können andere Dinge tun während das Deployment läuft
- Bessere Skalierbarkeit (kein blockierter Request-Thread)

**Wie?**
- **POST /deploy** startet Deployment → gibt sofort **ID + Status** zurück
- **Background Task** führt Terraform aus
- **Polling oder WebSocket** für Status-Updates
- **Logs** werden gestreamt während Deployment läuft

---

## 📊 Deployment Lifecycle

### Status Flow Diagramm

```
                    ┌─────────────┐
                    │   PENDING   │  (Initial State)
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ GENERATING  │  (Terraform code generation)
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │INITIALIZING │  (terraform init)
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  PLANNING   │  (terraform plan)
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
            ┌─────────────┐  ┌──────────┐
            │  APPLYING   │  │  FAILED  │  (Error in plan)
            └──────┬──────┘  └──────────┘
                   │
            ┌──────┴──────┐
            │             │
            ▼             ▼
      ┌─────────┐   ┌──────────┐
      │ SUCCESS │   │  FAILED  │  (Error in apply)
      └────┬────┘   └────┬─────┘
           │             │
           │             ▼
           │      ┌──────────────┐
           │      │   RETRYING   │──┐
           │      └──────────────┘  │
           │             ▲          │
           │             └──────────┘
           │
           ▼
    ┌─────────────┐
    │ DESTROYING  │  (User triggered)
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │  DESTROYED  │  (Final state)
    └─────────────┘

    ┌──────────────┐
    │  CANCELLED   │  (User cancelled before completion)
    └──────────────┘
```

### Status Bedeutung

| Status | Beschreibung | Dauer | Kann gecancelt werden? |
|--------|--------------|-------|------------------------|
| `PENDING` | Wartet auf Start | < 1s | ✅ Ja |
| `GENERATING` | Terraform Code wird generiert | 1-5s | ✅ Ja |
| `INITIALIZING` | `terraform init` läuft | 5-30s | ✅ Ja |
| `PLANNING` | `terraform plan` läuft | 10-60s | ✅ Ja |
| `APPLYING` | `terraform apply` läuft | 1-10min | ⚠️ Gefährlich |
| `SUCCESS` | Deployment erfolgreich | - | ❌ Nein (destroy stattdessen) |
| `FAILED` | Fehler aufgetreten | - | ❌ Nein (retry möglich) |
| `DESTROYING` | `terraform destroy` läuft | 1-5min | ❌ Nein |
| `DESTROYED` | Stack gelöscht | - | ❌ Nein |
| `CANCELLED` | User hat abgebrochen | - | ❌ Nein |

---

## 🚀 Deployment Workflow

### 1. Deployment starten

**Request:**
```bash
curl -X POST http://localhost:8001/api/v1/architectures/{arch_id}/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "deployed_by": "andy@example.com",
    "terraform_version": "1.9.0"
  }'
```

**Response (sofort):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "architecture_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "PENDING",
  "terraform_version": "1.9.0",
  "deployed_by": "andy@example.com",
  "started_at": "2026-04-20T10:00:00Z",
  "workspace_path": "/tmp/overcloud-deployments/550e8400...",
  "created_at": "2026-04-20T10:00:00Z",
  "updated_at": "2026-04-20T10:00:00Z"
}
```

**Was passiert:**
- ✅ Deployment-Eintrag in DynamoDB erstellt
- ✅ Background Task gestartet (FastAPI `BackgroundTasks`)
- ✅ Response sofort zurück (< 100ms)

### 2. Status abfragen (Polling)

**Option A: Einfaches Polling (alle 2-5 Sekunden)**
```bash
curl http://localhost:8001/api/v1/deployments/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PLANNING",
  "progress_percentage": 50,
  "estimated_duration_seconds": 120,
  "elapsed_seconds": 45,
  "current_step": "Running terraform plan...",
  "logs": [
    {"timestamp": "2026-04-20T10:00:05Z", "level": "INFO", "message": "Generating Terraform code..."},
    {"timestamp": "2026-04-20T10:00:10Z", "level": "INFO", "message": "Running terraform init..."},
    {"timestamp": "2026-04-20T10:00:45Z", "level": "INFO", "message": "Running terraform plan..."}
  ]
}
```

**Option B: Dedicated Logs Endpoint**
```bash
curl http://localhost:8001/api/v1/deployments/550e8400.../logs?since=2026-04-20T10:00:45Z
```

**Response:**
```json
{
  "deployment_id": "550e8400-e29b-41d4-a716-446655440000",
  "logs": [
    {"timestamp": "2026-04-20T10:00:45Z", "level": "INFO", "message": "Running terraform plan..."},
    {"timestamp": "2026-04-20T10:00:47Z", "level": "DEBUG", "message": "Terraform plan output: ..."}
  ],
  "has_more": true,
  "total_logs": 156
}
```

### 3. WebSocket Real-time Updates (Alternative)

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8001/api/v1/deployments/550e8400.../ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Status:', update.status);
  console.log('Progress:', update.progress_percentage + '%');
  console.log('Current Step:', update.current_step);
};
```

**Received Messages:**
```json
{
  "type": "status_update",
  "deployment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PLANNING",
  "progress_percentage": 50,
  "current_step": "Running terraform plan..."
}
```

```json
{
  "type": "log",
  "deployment_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-20T10:00:47Z",
  "level": "INFO",
  "message": "Terraform plan completed successfully"
}
```

```json
{
  "type": "completed",
  "deployment_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "terraform_outputs": {
    "vpc_id": "vpc-123456",
    "instance_public_ip": "54.123.45.67"
  }
}
```

### 4. Deployment fertig

**Success:**
```bash
curl http://localhost:8001/api/v1/deployments/550e8400...
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "progress_percentage": 100,
  "started_at": "2026-04-20T10:00:00Z",
  "completed_at": "2026-04-20T10:05:23Z",
  "terraform_outputs": {
    "vpc_id": "vpc-123456",
    "instance_public_ip": "54.123.45.67",
    "s3_bucket_name": "my-app-assets-20260420"
  }
}
```

**Failed:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FAILED",
  "progress_percentage": 65,
  "error_message": "Error applying plan: resource vpc-123456 already exists",
  "started_at": "2026-04-20T10:00:00Z",
  "completed_at": "2026-04-20T10:03:12Z"
}
```

---

## 🛠️ Deployment Operations

### Cancel Deployment (während es läuft)

**Wann sinnvoll:**
- Fehler bemerkt (falsche Config)
- Deployment dauert zu lange
- Status: `PENDING`, `GENERATING`, `INITIALIZING`, `PLANNING`

**Request:**
```bash
curl -X POST http://localhost:8001/api/v1/deployments/550e8400.../cancel
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "CANCELLED",
  "cancelled_at": "2026-04-20T10:02:15Z"
}
```

**⚠️ Warnung:** Cancel während `APPLYING` ist gefährlich!
- Terraform könnte in inkonsistentem Zustand sein
- Besser: Warten bis fertig, dann `destroy` benutzen

### Retry Failed Deployment

**Wann sinnvoll:**
- Temporärer Fehler (AWS API Timeout)
- Credential Issue behoben
- Quota erhöht

**Request:**
```bash
curl -X POST http://localhost:8001/api/v1/deployments/550e8400.../retry
```

**Response:**
```json
{
  "id": "660f9511-f3ac-52e5-b827-557766551111",
  "architecture_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "PENDING",
  "parent_deployment_id": "550e8400-e29b-41d4-a716-446655440000",
  "retry_count": 1
}
```

**Was passiert:**
- ✅ Neues Deployment erstellt (neue ID!)
- ✅ Gleiche Architecture
- ✅ Gleiche Config
- ✅ Retry Counter erhöht

### Destroy Deployment (Stack löschen)

**Wann sinnvoll:**
- Deployment nicht mehr benötigt
- Kosten sparen
- Fehlerhafte Infrastruktur aufräumen

**Request:**
```bash
curl -X DELETE http://localhost:8001/api/v1/deployments/550e8400...
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DESTROYING",
  "progress_percentage": 0,
  "current_step": "Running terraform destroy..."
}
```

**Was passiert:**
- ✅ Status → `DESTROYING`
- ✅ Background Task startet `terraform destroy`
- ✅ Polling funktioniert wie bei Deploy
- ✅ Final Status: `DESTROYED`

**⚠️ Warnung:** Destroy ist IRREVERSIBEL!
- Alle Ressourcen werden gelöscht
- Daten können verloren gehen
- Terraform State bleibt erhalten (für Audit)

---

## 🔍 Background Task Implementation

### Wie funktioniert das intern?

**File:** `app/services/deployment_manager.py`

```python
from fastapi import BackgroundTasks

async def deploy_architecture_async(
    deployment_id: str,
    background_tasks: BackgroundTasks
):
    # 1. Create deployment record
    deployment = await deployment_repo.create(...)
    
    # 2. Start background task
    background_tasks.add_task(
        _execute_deployment,
        deployment_id=deployment_id
    )
    
    # 3. Return immediately
    return deployment

async def _execute_deployment(deployment_id: str):
    """Runs in background thread."""
    try:
        # Update status: GENERATING
        await update_status(deployment_id, "GENERATING")
        terraform_code = generate_terraform(architecture)
        
        # Update status: INITIALIZING
        await update_status(deployment_id, "INITIALIZING")
        await run_command("terraform init")
        
        # Update status: PLANNING
        await update_status(deployment_id, "PLANNING")
        plan_output = await run_command("terraform plan")
        
        # Update status: APPLYING
        await update_status(deployment_id, "APPLYING")
        apply_output = await run_command("terraform apply -auto-approve")
        
        # Update status: SUCCESS
        await update_status(deployment_id, "SUCCESS")
        
    except Exception as e:
        # Update status: FAILED
        await update_status(deployment_id, "FAILED", error=str(e))
```

### Progress Berechnung

**File:** `app/services/deployment_progress.py`

```python
STATUS_PROGRESS_MAP = {
    DeploymentStatus.PENDING: 0,
    DeploymentStatus.GENERATING: 10,
    DeploymentStatus.INITIALIZING: 20,
    DeploymentStatus.PLANNING: 50,
    DeploymentStatus.APPLYING: 70,
    DeploymentStatus.SUCCESS: 100,
    DeploymentStatus.FAILED: -1,
}

def get_progress_info(deployment: Dict) -> Dict:
    status = DeploymentStatus(deployment["status"])
    progress = STATUS_PROGRESS_MAP.get(status, 0)
    
    # Estimate time remaining
    elapsed = (datetime.utcnow() - deployment["started_at"]).total_seconds()
    
    if status == DeploymentStatus.PLANNING:
        estimated_total = 120  # 2 minutes
    elif status == DeploymentStatus.APPLYING:
        estimated_total = 300  # 5 minutes
    else:
        estimated_total = elapsed
    
    return {
        "progress_percentage": progress,
        "elapsed_seconds": elapsed,
        "estimated_duration_seconds": estimated_total,
        "current_step": _get_step_description(status)
    }
```

---

## 📈 Best Practices

### Client-Side Polling

**❌ Schlecht: Polling alle 100ms**
```javascript
setInterval(() => {
  fetch('/api/v1/deployments/' + id);
}, 100);  // Zu häufig!
```

**✅ Gut: Polling alle 2-5 Sekunden**
```javascript
async function pollDeployment(deploymentId) {
  while (true) {
    const response = await fetch(`/api/v1/deployments/${deploymentId}`);
    const deployment = await response.json();
    
    updateUI(deployment);
    
    if (['SUCCESS', 'FAILED', 'CANCELLED', 'DESTROYED'].includes(deployment.status)) {
      break;  // Fertig
    }
    
    await sleep(3000);  // 3 Sekunden warten
  }
}
```

**✅ Besser: WebSocket verwenden**
```javascript
const ws = new WebSocket(`ws://localhost:8001/api/v1/deployments/${id}/ws`);
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  updateUI(update);
  
  if (update.type === 'completed' || update.type === 'failed') {
    ws.close();
  }
};
```

### Error Handling

**Client sollte:**
- ✅ Timeout nach 15 Minuten (sehr lange Deployments)
- ✅ Retry bei Netzwerkfehlern (exponential backoff)
- ✅ User warnen wenn Cancel gefährlich ist (während APPLYING)
- ✅ Logs anzeigen bei Fehler (für Debugging)

**Backend garantiert:**
- ✅ Deployment läuft auch wenn Client disconnected
- ✅ Status wird korrekt gespeichert (DynamoDB)
- ✅ Logs werden persistent gespeichert (S3)
- ✅ Terraform State bleibt konsistent

---

## 🔒 Security Considerations

### Authorisierung

**Deployment starten:**
- ✅ User muss Owner der Architecture sein
- ✅ Oder: Admin-Rechte haben
- ✅ JWT Token validiert

**Status abfragen:**
- ✅ User muss Owner der Architecture sein (über Deployment-Architektur-Link)
- ✅ Oder: Admin

**Cancel/Destroy:**
- ✅ Nur Owner oder Admin
- ✅ Audit Log Eintrag erstellt

### Terraform State

**Sensitive Data:**
- ⚠️ Terraform State kann Secrets enthalten!
- ✅ State wird in S3 gespeichert (encrypted at rest)
- ✅ State wird NICHT über API zurückgegeben
- ✅ Nur terraform_outputs werden exposed (gefiltert)

---

## 📊 Monitoring & Observability

### Metrics (TODO: Implement)

- `deployments_started_total` - Counter
- `deployments_succeeded_total` - Counter
- `deployments_failed_total` - Counter
- `deployment_duration_seconds` - Histogram
- `deployments_active` - Gauge

### Audit Logs

Jede Deployment-Operation wird geloggt:

```json
{
  "user": "andy@example.com",
  "action": "deploy",
  "resource_type": "deployment",
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {
    "architecture_id": "123e4567-e89b-12d3-a456-426614174000",
    "terraform_version": "1.9.0"
  },
  "success": true,
  "timestamp": "2026-04-20T10:00:00Z"
}
```

---

## 🚧 Known Limitations

### Current Limitations

1. **Kein paralleles Deployment** der gleichen Architecture
   - Würde zu Terraform State Conflicts führen
   - Backend blockiert nicht → Client muss prüfen

2. **Terraform Output Größe**
   - Outputs > 400KB werden nicht gespeichert
   - Selten ein Problem, aber theoretisch möglich

3. **Logs wachsen unbegrenzt**
   - Keine automatische Cleanup-Policy
   - TODO: Alte Logs nach 30 Tagen löschen

4. **Keine Notifications**
   - User muss aktiv pollen oder WebSocket offen halten
   - TODO: Email/Slack Notifications

---

## 🎯 Future Improvements

### Geplant (kurzfristig):

- [ ] **Deployment Queuing** - Max 5 parallele Deployments
- [ ] **Better Progress Estimation** - Basierend auf historischen Daten
- [ ] **Deployment Templates** - Wiederverwendbare Configs
- [ ] **Rollback** - Automatisches Rollback bei Fehler

### Geplant (langfristig):

- [ ] **Blue/Green Deployments** - Zero-downtime Updates
- [ ] **Canary Deployments** - Gradual Rollouts
- [ ] **Drift Detection** - Terraform vs. Real State Vergleich
- [ ] **Cost Alerts** - Warnung wenn Deployment teuer wird

---

## 📖 Weitere Ressourcen

- **API Dokumentation:** [API_EXAMPLES.md](./API_EXAMPLES.md)
- **Testing Guide:** [../TESTING.md](../TESTING.md)
- **Terraform Generator:** `app/core/terraform_generator/`
- **Deployment Manager:** `app/services/deployment_manager.py`

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-04-20  
**Version:** 1.0.0
