# OverCloud - Lessons Learned

> This file captures mistakes, corrections, and learnings throughout the project.
> Updated after every correction from the user or discovery of a better approach.

---

## 2026-03-22: Project Initialization

### Setup Phase
**Context:** Initial project setup with Claude Code tooling

**What we learned:**
- Extended CLAUDE.md is essential for maintaining project-specific context
- Tools like GSD v2, Vibe Kanban, and Superpowers prevent common AI coding pitfalls
- Agent swarm mode enables parallel development without context pollution

**Action taken:**
- Created comprehensive CLAUDE.md with OverCloud-specific rules
- Planned phased tool adoption (Superpowers → GSD → Swarm → Vibe Kanban)

**Preventive rule:**
- Always start large projects with clear rules and agent topology
- Don't skip the planning phase for tool setup

---

## 2026-03-23: Vite Configuration Mistake

### Frontend Setup
**Context:** Vite didn't find index.html, returned 404

**What went wrong:**
- First instinct: Move index.html from `src/` to root
- **MISTAKE:** This broke the planned directory structure
- Andy correctly pointed out: "Wär es nicht sinnvoller gewesen, Vite Config anzupassen statt Struktur kaputt zu machen?"

**Root cause:**
- Vite default expects `index.html` in root
- I didn't configure `root: 'src'` in `vite.config.js` initially
- Quick fix mentality instead of proper solution

**Correct solution:**
```js
// vite.config.js
export default defineConfig({
  root: 'src',  // Tell Vite where index.html is
  publicDir: '../public',
  build: { outDir: '../dist' }
})
```

**Preventive rule:**
- **NEVER move files to fix config issues** - fix the config instead!
- When tool doesn't find file: Configure the tool, don't break structure
- Think: "Is this breaking the designed architecture?" before making changes
- Always prefer: Config adjustment > File movement

**Lesson learned:**
- User knows their project structure better than AI
- Listen when user questions a "fix"
- Proper solution > Quick fix

---

## 2026-03-23: Tailwind CSS 4 - Richtige Migration (Vite Plugin)

### Frontend CSS Setup - WICHTIG: Ich hatte falsch recherchiert!
**Context:** Andy hat zu Recht gefragt ob ich mich richtig mit Tailwind 4 beschäftigen kann

**What went wrong:**
- Ich habe **blindlings** versucht PostCSS zu konfigurieren
- **FALSCH**: Tailwind 4 nutzt NICHT PostCSS bei Vite!
- Ich habe mehrfach die falsche Lösung probiert ohne richtig zu recherchieren
- Andy musste mich darauf hinweisen dass ich mir Zeit nehmen soll für richtige Recherche

**Root cause:**
- Tailwind CSS 4 hat eine **komplett neue Architektur**
- Mit Vite: Nutzt `@tailwindcss/vite` Plugin (NICHT PostCSS!)
- Ich habe nicht die offizielle Dokumentation gecheckt
- Zu schnell "gefixt" statt richtig verstanden

**KORREKTE Lösung für Tailwind CSS 4.2.2 + Vite:**

```bash
# 1. Installiere NUR diese Packages
npm install -D tailwindcss @tailwindcss/vite

# 2. KEINE PostCSS packages nötig! (postcss, autoprefixer, @tailwindcss/postcss)
# 3. KEINE tailwind.config.js nötig!
# 4. KEINE postcss.config.js nötig!
```

```js
// vite.config.js - Füge Tailwind Plugin hinzu
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),  // ✅ Das ist alles!
  ],
  // ... rest of config
})
```

```css
/* src/css/main.css - Einfacher Import */
@import "tailwindcss";

/* Optional: Custom Theme */
@theme {
  --color-primary-600: #a18072;
  /* ... */
}
```

**Preventive rule:**
- **IMMER offizielle Docs lesen** bei Major Versions
- Tailwind 4 + Vite = `@tailwindcss/vite` Plugin (kein PostCSS!)
- Nicht blindlings probieren - richtig recherchieren!
- Wenn User fragt "kannst du dich richtig damit beschäftigen" - dann TUN!

**Lesson learned:**
- Tailwind 4 ist eine **komplette Neuarchitektur**
- Vite Integration: Dedicated Plugin statt PostCSS
- Kein tailwind.config.js mehr nötig (zero-config!)
- Automatische Template Discovery
- User hat Recht wenn er sagt "mach's richtig" - nicht rumprobieren!

---

## 2026-05-17: Test Suite Complete Fix - 12 Fehler behoben

### Testing Phase nach Rechnerabsturz
**Context:** Nach Rechnerabsturz 12 FAILED Tests gefunden, alle mussten gefixt werden

**What we learned:**

1. **Pydantic Field Aliasing ist komplex in FastAPI**
   - Problem: `type` Feld mit `alias="organisation_type"` führt zu KeyError
   - Root Cause: FastAPI serialisiert mit `by_alias=True` → nutzt Alias statt Feldname
   - Lösung: Explizites Mapping besser als Alias-Magic
   - Regel: Bei DB/API Field-Unterschieden → explizite Mapping-Funktion

2. **JWT Token Uniqueness braucht mehr als Timestamps**
   - Problem: Identische Tokens bei schnellen Requests (gleiche Sekunde)
   - Root Cause: Timestamps haben nur Sekunden-Präzision
   - Lösung: `jti` (JWT ID mit UUID) + `iat` (issued at) hinzufügen
   - Bonus: Token-Revocation jetzt möglich
   - Regel: Immer `jti` für Token-Uniqueness verwenden

3. **DynamoDB unterstützt kein Python float - nur Decimal**
   - Problem: `TypeError: float * Decimal` nicht unterstützt
   - Root Cause: Tests übergeben float, aber DynamoDB braucht Decimal
   - Lösung: Defensive Konvertierung am Funktions-Eingang
   - Regel: Alle Geld/Preis-Berechnungen immer mit Decimal, Auto-Convert bei Input

4. **pytest.approx() ist nicht Decimal-kompatibel**
   - Problem: `pytest.approx()` erwartet float, bekommt aber Decimal
   - Lösung: `float(result["tax"]) == pytest.approx(13.30, rel=0.01)`
   - Regel: Decimal-Werte in Tests explizit zu float konvertieren

5. **Repository Method Signatures beachten**
   - Problem: `update(user_id, status="inactive")` schlägt fehl
   - Root Cause: Repository erwartet `update(id, updates_dict)`
   - Lösung: `update(user_id, {"status": "inactive"})`
   - Regel: Repository-Pattern → immer dict für updates

6. **TestClient Cookie Persistence zwischen Tests**
   - Problem: Cookies bleiben zwischen Tests bestehen
   - Lösung: `client.cookies.clear()` vor Security-Tests
   - Regel: Bei Test-Isolation explizit State clearen, nicht implicit verlassen

7. **Pydantic Schema Validation - 422 Errors**
   - Problem: `auth_provider` Feld existiert nicht im Register-Schema
   - Root Cause: Veraltete Fixtures mit nicht-existierenden Feldern
   - Lösung: Schema mit Code abgleichen, nur valide Felder verwenden
   - Regel: Bei 422 Errors → Schema-Definition checken

8. **Pytest Fixture Parameters müssen explizit sein**
   - Problem: `NameError: name 'client' is not defined` in Tests
   - Root Cause: Tests nutzten globales `client` statt Fixture-Parameter
   - Lösung: `client` zu allen Test-Methoden als Parameter hinzufügen
   - Regel: Nie globale Variablen in Tests → immer Fixtures verwenden

**Action taken:**
- 8 Dateien geändert, ~200 Zeilen Code
- 3 umfassende Dokumentationen erstellt (40+ Seiten)
- CHANGELOG und README aktualisiert
- Alle 12 Tests gefixed → 643 PASSED, 0 FAILED ✅

**Preventive rules:**
- **Pydantic:** Explizites Mapping > Alias-Magic (weniger Überraschungen)
- **JWT:** Immer `jti` (UUID) für Token-Uniqueness
- **DynamoDB:** Defensive Decimal-Konvertierung bei allen numerischen Inputs
- **Tests:** Decimal → float für pytest.approx()
- **Repositories:** Dict für updates, nicht keyword args
- **Test-Isolation:** Explizit clearen (cookies, cache, state)
- **Fixtures:** Parameter-basiert, nicht global
- **Schema-Validierung:** Bei 422 → Schema-Definition checken

**Documentation created:**
- `docs/TESTING_BEST_PRACTICES.md` (25 Seiten, 10 Kapitel)
- `docs/SESSION_2026-05-17_TEST_FIXES.md` (15 Seiten Details)
- `docs/EXECUTIVE_SUMMARY_2026-05-17.md` (Executive Summary)

**Impact:**
- 100% Test-Pass-Rate erreicht
- Production Ready Status
- Umfassende Testing-Guidelines für Team

---

## Template for Future Entries

### [Date]: [Topic/Feature]

**Context:** What were we trying to do?

**What went wrong / What we learned:**
- Specific issue or insight

**Root cause:**
- Why did it happen?

**Action taken:**
- How did we fix it?

**Preventive rule:**
- How do we prevent this in the future?

---
