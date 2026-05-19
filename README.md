# OverCloud

> Cloud infrastructure made understandable, versionable, and deployable.

**Status:** 🚧 In Development (Phase 0: Foundation)

---

## Vision

OverCloud transforms how developers and teams build cloud infrastructure:

- 📋 **Requirements-driven** - Describe what you need, not how to build it
- 📄 **JSON-first** - Versionable, inspectable, tool-agnostic source of truth
- 🔍 **Transparent** - See cost, security, and scalability before deploying
- ☁️ **Multi-cloud native** - Design once, deploy anywhere (AWS, Azure, GCP)
- 🎯 **Impact analysis** - Know exactly what changes when you deploy

---

## Core Principles

### 1. JSON as Source of Truth
Terraform is generated output, not manually edited. Every architecture is stored as versionable JSON with complete metadata about requirements, decisions, and evaluations.

### 2. Requirements → Decisions → Resources
Users describe **what they need** (public web app, high availability, budget constraints), and OverCloud translates that into **architectural decisions** and **cloud resources**.

### 3. Transparency Over Abstraction
No black boxes. Users see:
- Complete JSON definition
- Terraform code
- Architecture diagrams
- Cost breakdowns
- Security analysis
- Alternative approaches

### 4. Separation of Concerns
**Platform manages:** Logic, UI, JSON schemas, IaC generation, orchestration
**Customer manages:** Production data, storage, container images, secrets

---

## Project Structure

```
/
├── .claude/              # Claude Code configuration
│   ├── CLAUDE.md        # Project-specific rules & guidelines
│   ├── commands/        # Custom slash commands
│   ├── skills/          # Superpowers skills
│   └── agents/          # Agent team definitions
├── tasks/               # Task tracking (GSD framework)
│   ├── todo.md         # Current tasks
│   ├── lessons.md      # Lessons learned
│   └── decisions.md    # Architectural Decision Records (ADRs)
├── docs/                # Documentation
│   ├── architecture/   # System design documents
│   ├── json-schemas/   # JSON Schema definitions
│   ├── api/            # API documentation
│   └── user-guides/    # User guides
├── backend/             # Node.js/TypeScript backend (TBD)
├── frontend/            # Next.js frontend (TBD)
└── infrastructure/      # Platform infrastructure (TBD)
```

---

## Technology Stack

### Backend (Python)
- **Runtime:** Python 3.11+
- **Framework:** FastAPI (async, modern, type-safe)
- **Database:** DynamoDB (primary), PostgreSQL (legacy migrations)
- **ORM:** Custom DynamoDB repositories + SQLAlchemy 2.0 (legacy)
- **Validation:** Pydantic v2
- **AWS SDK:** Boto3 (DynamoDB, S3, Lambda)
- **Testing:** pytest + pytest-asyncio + httpx + moto (AWS mocking)
- **Code Quality:** Black, Ruff, mypy
- **Dependency Management:** Poetry

### Frontend (Vanilla JS)
- **Core:** HTML5, CSS3, JavaScript ES6+
- **Build Tool:** Vite (dev server + bundling)
- **Styling:** Tailwind CSS 3
- **Architecture:** Component-based (class modules)
- **State:** Custom event-driven system
- **Testing:** Vitest
- **UI Design:** Anthropic Claude.ai aesthetic

### DevOps
- **IaC:** Terraform (generated from Python)
- **CI/CD:** GitHub Actions
- **Hosting:** AWS S3 + CloudFront (frontend), AWS Lambda or ECS (backend)
- **Monitoring:** AWS CloudWatch + Sentry

---

## Development Workflow

This project uses advanced Claude Code tooling:

### Tools Integrated
1. **GSD v2** - Spec-driven development with fresh agent contexts
2. **Agent Swarm** - Multi-agent coordination for parallel development
3. **Superpowers MCP** - Structured TDD, debugging, and code review skills
4. **Vibe Kanban** - Visual orchestration and code review (Phase 2)

### Agent Team Structure
- **Team Lead** - Coordination, architecture, reviews
- **Backend Architect** - Core logic, API design
- **Frontend Engineer** - UI/UX, React components
- **DevOps Engineer** - IaC generation, cloud integrations
- **Data Architect** - JSON schemas, versioning
- **Security Auditor** - Security reviews, IAM policies
- **QA Engineer** - Testing, CI/CD

See [.claude/CLAUDE.md](./.claude/CLAUDE.md) for complete development guidelines.

---

## Current Status

### ✅ Completed
- [x] Project foundation & directory structure
- [x] Extended CLAUDE.md with OverCloud-specific rules
- [x] JSON Schema v1.0.0 definition
- [x] Architectural Decision Records (ADRs)
- [x] Task management setup (GSD)
- [x] Backend authentication & authorization (JWT, RBAC)
- [x] Infrastructure Designer (Visual Canvas + Terraform Generation)
- [x] Live Cost Calculation
- [x] CIDR Calculator
- [x] Admin System (SuperAdmin, Auditor, Support roles)
- [x] Hybrid Pricing Model (Base Fee + AWS Markup %)
- [x] Voucher/Gutscheinsystem (10%-100% Rabatt)
- [x] Pricing-Page mit Kostenrechner
- [x] Billing System mit Invoice Generation
- [x] **DynamoDB Migration** (Single Table Design für neue Features)
- [x] **Review System** (5-Sterne-Bewertungen mit Spam Detection & Admin Moderation)
- [x] **Feedback System** (Anonyme Bug Reports mit Screenshot-Upload zu S3)
- [x] **FAQ System** (Kategorien, Search, Drag&Drop-Reordering, View Tracking)
- [x] **245 Tests** (244 passing, 1 skipped) - Reviews, Feedback, FAQ vollständig getestet

### 🔄 In Progress
- [ ] Stripe Payment Integration
- [ ] Multi-Cloud Support (Azure, GCP)
- [ ] Real-time Collaboration (WebSockets)

### 📋 Next Steps
- [ ] Technical specification for MVP
- [ ] Backend scaffolding (NestJS + Prisma)
- [ ] Frontend scaffolding (Next.js + shadcn/ui)
- [ ] JSON versioning engine
- [ ] Basic Terraform generator

---

## MVP Scope (Phase 1)

**Target:** Minimum Viable Product for early users

- **Cloud Provider:** AWS only
- **Blueprints:** 3 core patterns
  1. Web Application (VPC + EC2 + RDS + ALB)
  2. API Service (Lambda + API Gateway + DynamoDB)
  3. Static Website (S3 + CloudFront)
- **Features:**
  - Guided architecture builder (question flow)
  - Manual component builder (drag-and-drop)
  - JSON versioning
  - Basic cost estimation (±20% accuracy)
  - Terraform generation
  - Single deployment per architecture
- **Limits:**
  - Single region only
  - No multi-cloud
  - Manual deployment approval
  - No Blue/Green deployments

---

## Long-Term Roadmap

### Phase 2: Multi-Cloud
- Azure support
- GCP support
- Cloud cost comparison
- Migration tools

### Phase 3: Advanced Features
- AI-powered optimization recommendations
- Team collaboration
- Blue/Green deployments
- Multi-region support
- Advanced blueprints (microservices, Kubernetes)

### Phase 4: Ecosystem
- Community blueprint marketplace
- Plugin system
- Terraform Cloud integration
- GitOps workflows

---

## Documentation

### Development & Guidelines
- **[CLAUDE.md](./.claude/CLAUDE.md)** - Development rules & guidelines
- **[tasks/todo.md](./tasks/todo.md)** - Current tasks
- **[tasks/decisions.md](./tasks/decisions.md)** - Architectural decisions

### Testing
- **[Testing Best Practices](./docs/TESTING_BEST_PRACTICES.md)** - Comprehensive testing guide (10 chapters)
- **[Session Summary: Test Fixes](./docs/SESSION_2026-05-17_TEST_FIXES.md)** - Complete test suite fix documentation

### Technical Documentation
- **[CHANGELOG.md](./CHANGELOG.md)** - All changes, bugfixes, and features
- **[Developer's Encyclopedia](./docs/encyclopedia/)** - Complete technical documentation (3 parts, 250+ pages)
- **[JSON Schemas](./docs/json-schemas/)** - JSON Schema definitions

---

## Contributing

This project is currently in early development. Contributions will be welcome in the future.

---

## License

TBD

---

## Contact

**Project Lead:** Andy Schwarz

---

**Last Updated:** 2026-05-17
