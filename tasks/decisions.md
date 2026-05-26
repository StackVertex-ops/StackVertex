# StackVertex - Architectural Decision Records (ADRs)

> Documents key technical decisions, trade-offs, and rationale.
> Format: [ADR-XXX] Title

---

## [ADR-001] JSON-First Architecture

**Date:** 2026-03-22
**Status:** ✅ Accepted
**Deciders:** Andy (Product Owner), Claude (Architect)

### Context
Need to decide on the core data model and source of truth for cloud infrastructure definitions.

### Decision
Use JSON as the **single source of truth** for all architecture definitions. Terraform/OpenTofu code is generated output, never manually edited.

### Rationale
**Pros:**
- Version control friendly (clean diffs)
- Easy to validate (JSON Schema)
- Language/tool agnostic
- Enables multiple output formats (Terraform, Pulumi, CDK, etc.)
- Human-readable and machine-parseable
- Supports metadata (decisions, evaluations, requirements)

**Cons:**
- Requires custom tooling for JSON → Terraform generation
- More abstraction layers than direct Terraform
- Initial development overhead

### Alternatives Considered
1. **Terraform as source of truth** → Rejected: Not cloud-agnostic, hard to version requirements
2. **YAML** → Rejected: Less strict, harder to validate
3. **Custom DSL** → Rejected: Too much overhead, reinventing the wheel

### Consequences
- Need to build robust JSON versioning engine
- Must create comprehensive JSON Schema definitions
- Terraform generation logic becomes critical path
- Enables future support for multiple IaC backends

---

## [ADR-002] Multi-Cloud Abstraction from Day 1

**Date:** 2026-03-22
**Status:** ✅ Accepted
**Deciders:** Andy, Claude

### Context
Should we design for AWS-only (MVP) or build multi-cloud abstractions from the start?

### Decision
Design **cloud-agnostic abstractions** from day 1, but **implement only AWS** for MVP.

### Rationale
**Pros:**
- Easier to add Azure/GCP later (no major refactoring)
- Forces cleaner architecture
- Prevents vendor lock-in
- Aligns with product vision

**Cons:**
- More upfront design work
- Temptation to over-engineer
- Slightly slower MVP delivery

### Implementation Guidelines
- Use provider-agnostic naming (e.g., `compute` not `ec2`)
- Abstract cloud-specific APIs behind interfaces
- Store cloud provider in JSON metadata
- Test abstractions with mock providers

### Consequences
- Core models must be cloud-agnostic
- AWS-specific logic isolated in `providers/aws/`
- JSON schema supports `provider` field
- Documentation explains multi-cloud roadmap

---

## [ADR-003] Requirements-Driven vs Resource-Driven UI

**Date:** 2026-03-22
**Status:** ✅ Accepted
**Deciders:** Andy, Claude

### Context
How should users build cloud architectures? Pick resources (EC2, S3) or describe requirements (public web app, high availability)?

### Decision
**Primary UX: Requirements-driven** (guided questions)
**Secondary UX: Resource-driven** (manual building blocks)

### Rationale
**Requirements-driven:**
- Better for beginners (no cloud expertise needed)
- Aligns with product USP (cloud made understandable)
- Enables smart recommendations
- Shows impact analysis before committing

**Resource-driven:**
- Faster for experts
- More control
- Fallback when guided flow doesn't fit

### Implementation
- Guided flow: Series of questions → JSON → Resources
- Manual flow: Drag-and-drop components → JSON
- Both flows produce identical JSON format
- Users can switch between modes

### Consequences
- Need to build question flow logic
- Requires decision tree for common architectures
- Must maintain component library for manual mode
- Impact analysis engine works for both modes

---

## [ADR-004] Technology Stack

**Date:** 2026-03-22 (Updated: 2026-03-22)
**Status:** ✅ Accepted
**Deciders:** Andy, Claude

### Context
Choose technology stack for MVP development. Priorities:
1. Python for backend (ideal for cloud automation, AWS SDK, Terraform generation)
2. Vanilla JS for frontend (no framework bloat, fast loading, maintainable)
3. Modern tooling for DX (Vite, Tailwind, Poetry)

### Decision

**Backend (Python):**
- Runtime: **Python 3.11+**
- Framework: **FastAPI** (async, modern, type hints, auto-docs)
- Database: **PostgreSQL** (AWS RDS or Supabase)
- ORM: **SQLAlchemy 2.0** + **Alembic** (migrations)
- Validation: **Pydantic v2** (native FastAPI integration)
- AWS SDK: **Boto3** (EC2, S3, Lambda, IAM, CloudFormation, etc.)
- Authentication: **python-jose** (JWT) + **passlib** (password hashing)
- Testing: **pytest** + pytest-asyncio + pytest-cov + **httpx** (FastAPI testing)
- Code Quality: **Black** (formatter), **Ruff** (linter), **mypy** (type checker)
- Dependency Management: **Poetry**
- Terraform Generation: **Jinja2** templates or Python string building

**Frontend (Vanilla JS):**
- Core: **HTML5**, **CSS3**, **JavaScript ES6+**
- Build Tool: **Vite** (fast dev server, HMR, optimized builds)
- Styling: **Tailwind CSS 3** + @tailwindcss/forms + @tailwindcss/typography
- Architecture: Component-based (class-based modules or Web Components)
- State Management: Custom event-driven system (PubSub pattern)
- HTTP Client: **Fetch API** (native) + wrapper for API calls
- Testing: **Vitest** (compatible with Vite, fast)
- UI Design: Anthropic Claude.ai aesthetic (clean, minimal, professional)

**Cloud & IaC:**
- Target Cloud: **AWS** (MVP), Azure & GCP (Phase 2+)
- IaC Output: **Terraform HCL** (generated from JSON)
- Terraform Generator: Python (Jinja2 templates)
- AWS CLI: For testing and manual operations

**DevOps:**
- CI/CD: **GitHub Actions**
- Containerization: **Docker** (for backend deployment)
- Hosting:
  - Frontend: **AWS S3** + **CloudFront** (static hosting, CDN)
  - Backend: **AWS Lambda** (serverless) or **ECS Fargate** (containerized)
- Monitoring: **AWS CloudWatch** + **Sentry** (errors)
- Analytics: **PostHog** (optional)

### Rationale

**Why Python Backend:**
- ✅ **AWS SDK (Boto3):** Native, well-documented, mature
- ✅ **Terraform Generation:** Easy string/template manipulation
- ✅ **FastAPI:** Modern, async, type-safe, auto-generates OpenAPI docs
- ✅ **Cloud Automation:** Python is industry standard for DevOps/cloud
- ✅ **Lambda Support:** Can deploy backend as Lambda functions
- ✅ **Data Processing:** If we add analytics/cost optimization later, Python excels

**Why Vanilla JS Frontend:**
- ✅ **Zero Framework Bloat:** No React/Vue/Angular runtime overhead
- ✅ **Fast Loading:** Minimal bundle size (<50KB initial)
- ✅ **No Build Complexity:** Vite handles bundling, but code is simple JS
- ✅ **Easy to Understand:** No framework-specific patterns to learn
- ✅ **Long-term Maintainability:** No framework version migrations
- ✅ **Tailwind CSS:** Utility-first, professional UI without custom CSS
- ✅ **Modern Tooling:** Vite gives us HMR, dev server, optimized builds

**Why This Combo:**
- Python + Vanilla JS = **minimal dependencies**, **fast performance**, **easy deployment**
- FastAPI auto-generates OpenAPI docs → Frontend can consume typed API
- Both support modern tooling (Poetry, Vite) for great DX
- AWS-native stack (Lambda, S3, CloudFront) = **low cost**, **scalable**

### Alternatives Considered

**Backend Alternatives:**
1. **Node.js + NestJS** → Rejected: Python better for AWS SDK + Terraform
2. **Node.js + Hono** → Rejected: Too minimal, Python better for cloud
3. **Go** → Rejected: Steeper learning curve, less AWS SDK maturity
4. **Django** → Rejected: Too heavy, FastAPI better for APIs

**Frontend Alternatives:**
1. **React + Next.js** → Rejected: Overkill for our UI, bundle size too large
2. **Vue.js** → Rejected: Still a framework, adds complexity
3. **Svelte** → Rejected: Great, but Vanilla JS even simpler
4. **Alpine.js + HTMX** → Considered: Good for server-side rendering, but we need SPA-like UX

**Why Not Full-Stack Framework (e.g., Django + Django Templates):**
- We need SPA-like UX (instant feedback, no page reloads)
- API-first approach allows future mobile app
- Separation of concerns (Python backend, JS frontend)

### Consequences

**Positive:**
- ✅ Lean stack, minimal dependencies
- ✅ Fast development (FastAPI auto-docs, Vite HMR)
- ✅ Easy deployment (Python → Lambda, JS → S3)
- ✅ Low cost (serverless, static hosting)
- ✅ Python perfect for cloud automation
- ✅ No framework lock-in on frontend

**Challenges:**
- ⚠️ Need to build UI component system from scratch (but Tailwind helps)
- ⚠️ No React ecosystem (but we don't need it)
- ⚠️ Manual state management (but custom PubSub is simple)

**Implementation Notes:**
- Use Poetry for Python dependency management
- Use Vite for frontend build tooling
- Create reusable JS component classes (e.g., `ArchitectureBuilder`, `CostEstimator`)
- Use Tailwind UI patterns for professional look
- FastAPI → OpenAPI → TypeScript types (optional, for type safety in JS)

### Migration Path (If Needed Later)
- Frontend can be rewritten in React/Vue without changing backend
- Backend API is framework-agnostic (REST + OpenAPI)
- Terraform generation logic is pure Python (reusable in any stack)

---

## [ADR-005] Agent Team Topology

**Date:** 2026-03-22
**Status:** ✅ Accepted
**Deciders:** Claude (based on GSD + Swarm best practices)

### Context
How to structure Claude Code agent teams for efficient parallel development?

### Decision

**Team Structure:**
1. **Team Lead** (main session) - Coordination, architecture, reviews
2. **Backend Architect** - Core logic, API design
3. **Frontend Engineer** - UI/UX, React components
4. **DevOps Engineer** - IaC generation, cloud integrations
5. **Data Architect** - JSON schemas, versioning
6. **Security Auditor** - Security reviews, IAM
7. **QA Engineer** - Testing, CI/CD

**Workflow:**
- Lead assigns tasks to specialists
- Specialists work in isolated contexts (GSD fresh sessions)
- Communication via `/send-message`
- Lead reviews all PRs before merge

### Rationale
- **Prevents context rot:** Each agent has focused context
- **Parallel execution:** Multiple features simultaneously
- **Expertise separation:** Each agent has domain knowledge
- **Quality gates:** Security + QA review everything

### Tools Integration
- **GSD v2:** Fresh contexts per task
- **Agent Swarm:** Native Claude Code team coordination
- **Vibe Kanban:** Visual management (Phase 2)
- **Superpowers:** TDD + code review skills

### Consequences
- Main session must coordinate effectively
- Need clear task dependencies
- Document inter-agent decisions
- Use `tasks/decisions.md` for shared knowledge

---

## Template for Future ADRs

## [ADR-XXX] Title

**Date:** YYYY-MM-DD
**Status:** 🔄 Proposed | ✅ Accepted | ❌ Rejected | ⚠️ Deprecated
**Deciders:** Who made this decision?

### Context
What problem are we solving?

### Decision
What did we decide?

### Rationale
Why did we choose this? Pros/cons?

### Alternatives Considered
What else did we look at?

### Consequences
What does this mean for the project?

---
