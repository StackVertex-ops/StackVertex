# StackVertex - Claude Code Rules & Workflows

> These rules extend Andy's global `.claude/CLAUDE.md` with StackVertex-specific guidelines

---

## 1. Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

## 2. Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

## 3. Self-Improvement Loop

- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

## 4. Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

## 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

## 6. Autonomous Bug Fixing

- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## 🎯 StackVertex-Specific Rules

### Project Vision

**StackVertex** is a platform that:
- Models cloud infrastructure from requirements (not resources)
- Stores everything as versionable JSON (source of truth)
- Generates IaC (Terraform/OpenTofu) from JSON
- Deploys and manages multi-cloud stacks
- Provides transparent impact analysis (cost, security, scalability)
- Separates platform logic from customer data

### Core Principles

#### 1. JSON-First Architecture
- **JSON is the source of truth**, not Terraform
- All decisions, components, and requirements are stored as JSON
- Terraform is generated output, never edited manually
- Every change creates a new JSON version

#### 2. Requirements-Driven Design
- Users describe WHAT they need, not HOW to build it
- System translates requirements → decisions → resources
- Show impact analysis before deployment (cost, security, scalability)
- Suggest alternatives when better options exist

#### 3. Multi-Cloud Native
- Design everything cloud-agnostic from day 1
- Use abstraction layers for AWS/Azure/GCP differences
- Never hardcode cloud-specific logic in core modules
- Plan for: AWS (MVP), Azure (Phase 2), GCP (Phase 3)

#### 4. Separation of Concerns
**Platform manages:**
- Logic, UI, JSON schemas, IaC generation, metadata, orchestration

**Customer manages:**
- Production data, storage, container images, secrets

#### 5. Transparency Over Abstraction
- Users see: JSON, architecture diagrams, Terraform code, decisions, costs
- No black boxes - everything is inspectable and versionable
- Only secrets are hidden (vault-managed)

#### 6. Security by Default
- No hardcoded credentials - always use roles (AssumeRole)
- Secrets managed like GitHub Secrets (write-only, encrypted at rest)
- Audit logs for all actions
- Least privilege principle for all IAM

---

## 📁 Project Structure Rules

### Directory Organization
```
/
├── .claude/                    # Claude Code config
│   ├── CLAUDE.md              # This file
│   ├── commands/              # Custom slash commands
│   ├── skills/                # Superpowers skills
│   └── agents/                # Agent team definitions
├── tasks/                     # Task tracking (GSD)
│   ├── todo.md               # Current tasks
│   ├── lessons.md            # Lessons learned
│   └── archive/              # Completed milestones
├── docs/                      # Architecture & specs
│   ├── architecture/         # System design docs
│   ├── json-schemas/         # JSON schema definitions
│   ├── api/                  # API documentation
│   └── user-guides/          # User documentation
├── backend/                   # Python FastAPI backend
│   ├── app/                  # Main application
│   │   ├── api/             # API endpoints (routers)
│   │   ├── core/            # Business logic
│   │   │   ├── json_engine/     # JSON versioning & storage
│   │   │   ├── iac_generator/   # Terraform generation
│   │   │   ├── deployment/      # Stack deployment (AWS SDK)
│   │   │   ├── evaluation/      # Cost/security analysis
│   │   │   └── orchestration/   # Multi-cloud orchestration
│   │   ├── models/          # SQLAlchemy models + Pydantic schemas
│   │   ├── services/        # External integrations (AWS, Terraform)
│   │   └── utils/           # Helper functions
│   ├── tests/                # pytest tests
│   ├── alembic/              # Database migrations
│   ├── pyproject.toml        # Poetry dependencies
│   └── main.py               # FastAPI entry point
├── frontend/                  # Vanilla JS frontend
│   ├── src/
│   │   ├── js/              # JavaScript modules
│   │   │   ├── components/  # UI components (class-based or functions)
│   │   │   ├── lib/         # Utilities (API client, state, etc.)
│   │   │   ├── pages/       # Page controllers
│   │   │   └── main.js      # Entry point
│   │   ├── css/             # Stylesheets
│   │   │   ├── main.css     # Tailwind imports + custom styles
│   │   │   └── components/  # Component-specific styles
│   │   └── index.html       # Main HTML template
│   ├── public/               # Static assets
│   ├── dist/                 # Build output (Vite)
│   ├── vite.config.js        # Vite configuration
│   └── tailwind.config.js    # Tailwind configuration
├── infrastructure/            # Platform infrastructure
│   ├── terraform/            # Terraform for StackVertex itself
│   └── docker/               # Container configs
└── scripts/                   # Build & deployment scripts
```

### File Naming Conventions
- **Python Files:** `snake_case.py` (e.g., `json_engine.py`, `terraform_generator.py`)
- **Python Classes:** `PascalCase` in code (e.g., `class ArchitectureSchema`)
- **JavaScript Files:** `kebab-case.js` (e.g., `api-client.js`, `architecture-builder.js`)
- **JavaScript Classes:** `PascalCase` in code (e.g., `class ArchitectureBuilder`)
- **CSS Files:** `kebab-case.css` (e.g., `architecture-builder.css`)
- **HTML Files:** `kebab-case.html` (e.g., `index.html`, `dashboard.html`)
- **Tests:**
  - Python: `test_*.py` or `*_test.py` (e.g., `test_json_engine.py`)
  - JavaScript: `*.test.js` or `*.spec.js`
- **JSON Schemas:** `kebab-case.schema.json`
- **Docs:** `kebab-case.md`

---

## 🧠 Agent Team Topology

### Team Lead (Main Session)
- Coordinates all agents
- Makes architectural decisions
- Reviews all PRs
- Manages task dependencies

### Specialist Agents
1. **Backend Architect** - Core business logic, API design
2. **Frontend Engineer** - UI/UX, React components
3. **DevOps Engineer** - IaC generation, deployment, cloud integrations
4. **Data Architect** - JSON schemas, versioning, data models
5. **Security Auditor** - Security reviews, IAM policies, audit logs
6. **QA Engineer** - Testing, validation, CI/CD

### Agent Communication
- Use `/send-message` for cross-agent coordination
- Document decisions in `tasks/decisions.md`
- Always tag the relevant agent in task descriptions

---

## 🎨 UI/UX Standards

### Design System
- Use **shadcn/ui** + **Tailwind CSS** for components
- Follow **Anthropic Claude.ai aesthetic** (clean, minimal, professional)
- Color palette: Neutral base + accent color (TBD)
- Typography: System fonts, clear hierarchy
- Spacing: Consistent 8px grid

### UI Principles
1. **Progressive Disclosure** - Show complexity gradually
2. **Instant Feedback** - Real-time impact analysis
3. **Visual Hierarchy** - Important info stands out
4. **Accessibility First** - WCAG 2.1 AA compliance
5. **Mobile-Responsive** - Desktop-first, mobile-friendly

### Component Standards
- Every component has: PropTypes/TypeScript types, JSDoc comments, Storybook story (later)
- Use React Server Components where possible (Next.js 14+)
- Optimize for performance (memoization, lazy loading)

---

## 🏗️ Development Workflow (GSD Framework)

### Phase 1: Research
1. Understand requirements
2. Research existing solutions
3. Identify technical constraints
4. Document findings in `tasks/research.md`

### Phase 2: Planning
1. Write detailed spec in `docs/specs/`
2. Create JSON schemas
3. Design API contracts
4. Plan database models
5. Get approval before implementation

### Phase 3: Implementation
1. Use TDD where critical (core business logic)
2. Write tests first for new features
3. Implement in small, atomic commits
4. Self-review before marking complete

### Phase 4: Validation
1. Run all tests
2. Manual testing in dev environment
3. Code review (by Security Auditor for sensitive code)
4. Update documentation
5. Mark task complete only after all checks pass

---

## 🔐 Security Rules

### Secrets Management
- NEVER commit secrets to git
- Use `.env.local` for local development (in `.gitignore`)
- Production secrets in AWS Secrets Manager / Azure Key Vault
- All secrets encrypted at rest, write-only in UI

### Cloud Access
- Always use IAM roles (AssumeRole), never access keys
- Implement least privilege policies
- Rotate credentials regularly (automated)
- Log all cloud API calls

### API Security
- JWT authentication for all API endpoints
- Rate limiting (per user + per IP)
- Input validation (Zod schemas)
- CORS policies (whitelist only)

---

## 📊 JSON Schema Rules

### Versioning
- Every schema has a `version` field (semver)
- Breaking changes require major version bump
- Migrations for existing data
- Document changes in `CHANGELOG.md`

### Structure
```json
{
  "version": "1.0.0",
  "metadata": { /* tracking info */ },
  "requirements": { /* what user wants */ },
  "decisions": { /* why we chose X */ },
  "architecture": { /* components & relationships */ },
  "evaluation": { /* cost, security, etc */ }
}
```

### Validation
- Use JSON Schema Draft 2020-12
- Validate on save + on load
- Provide clear error messages
- Support partial validation for drafts

---

## 🚀 Deployment Rules

### MVP Focus (Phase 1)
- AWS only
- 2-3 blueprints (web app, API, static site)
- Basic cost estimation
- Single region
- Manual approval for deployments

### Later Phases
- Multi-cloud (Azure, GCP)
- Advanced blueprints (microservices, serverless, Kubernetes)
- Automated cost optimization
- Multi-region
- Blue/green deployments

### Deployment Safety
- Always dry-run first (Terraform plan)
- Show diff to user before applying
- Rollback capability on failure
- Keep old stacks for 7 days (configurable)

---

## 📝 Task Management (GSD + TodoWrite)

### Task Structure
- **Title:** Clear, action-oriented
- **Description:** Context, requirements, acceptance criteria
- **Status:** pending | in_progress | completed
- **Owner:** Which agent is responsible
- **Dependencies:** Blocked by which tasks
- **Estimated Time:** Realistic estimate

### Task Files
- `tasks/todo.md` - Current sprint tasks
- `tasks/lessons.md` - Lessons learned (updated after mistakes)
- `tasks/decisions.md` - Architectural decisions (ADRs)
- `tasks/archive/` - Completed milestones

### Commit Messages
- Format: `[scope] imperative verb: description`
- Examples:
  - `[backend] Add JSON versioning engine`
  - `[frontend] Build architecture builder UI`
  - `[docs] Document JSON schema v1.0.0`
  - `[security] Implement AssumeRole for AWS`

---

## 🧪 Testing Standards

### Coverage Requirements
- **Core business logic:** 90%+ coverage
- **API endpoints:** 80%+ coverage
- **UI components:** 60%+ coverage (critical paths)
- **Utilities:** 100% coverage

### Test Types
1. **Unit Tests** - Isolated functions (Jest/Vitest)
2. **Integration Tests** - API + database interactions
3. **E2E Tests** - Critical user flows (Playwright)
4. **Contract Tests** - API consumers (Pact)

### Test Rules
- Tests must be fast (<500ms per test)
- No flaky tests (auto-retry max 3x, then investigate)
- Mock external services (AWS SDK, etc.)
- Use fixtures for complex test data

---

## 🎓 Code Quality Standards

### Python
- **Type Hints:** Always use (Python 3.11+ syntax)
- **Formatter:** Black (line length 100)
- **Linter:** Ruff (fast, modern, replaces Flake8 + isort)
- **Type Checker:** mypy (strict mode)
- **Docstrings:** Google style for all public functions/classes
- **Import Order:** Standard library → Third-party → Local (Ruff handles this)
- **Max File Length:** 500 lines (split if larger)

```python
# Good example
from typing import Optional
from pydantic import BaseModel

def generate_terraform(architecture: dict, provider: str = "aws") -> str:
    """Generate Terraform HCL code from architecture JSON.

    Args:
        architecture: Architecture definition matching our JSON schema
        provider: Cloud provider (aws, azure, gcp)

    Returns:
        Terraform HCL code as string

    Raises:
        ValidationError: If architecture is invalid
    """
    ...
```

### JavaScript (ES6+)
- **Modern Syntax:** Use ES6+ features (const/let, arrow functions, destructuring)
- **Modules:** ES6 modules (import/export)
- **Formatter:** Prettier (via Vite/ESLint)
- **Linter:** ESLint (standard config)
- **Documentation:** JSDoc for public APIs
- **Max File Length:** 400 lines

```javascript
// Good example
/**
 * Fetch architecture from API
 * @param {string} architectureId - UUID of architecture
 * @returns {Promise<Object>} Architecture definition
 */
export async function fetchArchitecture(architectureId) {
  const response = await fetch(`/api/architectures/${architectureId}`);
  if (!response.ok) throw new Error('Failed to fetch architecture');
  return await response.json();
}
```

### CSS/Tailwind
- **Primary:** Tailwind utility classes
- **Custom CSS:** Only when Tailwind insufficient
- **CSS Modules:** Not needed (Tailwind handles scoping via HTML)
- **Naming:** BEM convention for custom classes (if needed)
- **Max Specificity:** Avoid deep nesting (max 3 levels)

### Comments
- **JSDoc/Docstrings** for all public APIs
- Explain **WHY**, not WHAT
- Comment complex algorithms
- Remove dead code immediately
- TODO comments must have owner + date: `# TODO(andy, 2026-03-22): Fix cost calculation`

---

## 🚦 Performance Rules

### Frontend
- Lighthouse score: 90+ (Performance, Accessibility, Best Practices)
- First Contentful Paint: <1.5s
- Time to Interactive: <3s
- Bundle size: <200KB (initial)

### Backend
- API response time: <200ms (p95)
- Database queries: <50ms (p95)
- Use caching (Redis) for frequently accessed data
- Implement pagination (max 100 items per page)

---

## 🆘 When Things Break

### Debug Process
1. Read error message carefully
2. Check logs (CloudWatch, Sentry)
3. Reproduce locally
4. Isolate root cause (binary search)
5. Fix + add test to prevent regression
6. Document in `tasks/lessons.md`

### Rollback Strategy
- Keep previous deployment active
- Switch DNS/load balancer back
- Investigate issue in non-prod
- Deploy fix as new version

---

## 🎯 Success Criteria

### MVP Launch Checklist
- [ ] 3 working blueprints (web app, API, static site)
- [ ] JSON schema v1.0.0 finalized
- [ ] AWS integration working (VPC, EC2, S3, Lambda)
- [ ] Terraform generation accurate
- [ ] Cost estimation within 20% accuracy
- [ ] UI/UX matches design system
- [ ] Security audit passed
- [ ] Documentation complete
- [ ] 10 beta users onboarded successfully

### Long-Term Goals
- Multi-cloud support (Azure, GCP)
- 20+ blueprints
- AI-powered optimization recommendations
- Team collaboration features
- Marketplace for community blueprints

---

## 📚 Learning Resources

### Required Reading
- AWS Well-Architected Framework
- Terraform Best Practices
- JSON Schema Specification
- React Server Components (Next.js 14+)

### Inspiration
- [Pulumi](https://pulumi.com) - Programmatic IaC
- [Vercel](https://vercel.com) - Deployment UX
- [Railway](https://railway.app) - Simplicity
- [Terraform Cloud](https://cloud.hashicorp.com/products/terraform) - IaC management

---

## 🛠️ Tools & Frameworks

### Backend (Python)
- **Runtime:** Python 3.11+
- **Framework:** FastAPI (async, modern, type hints)
- **Database:** PostgreSQL (AWS RDS or Supabase)
- **ORM:** SQLAlchemy 2.0 + Alembic (migrations)
- **Validation:** Pydantic v2 (native FastAPI integration)
- **AWS SDK:** Boto3 (EC2, S3, Lambda, IAM, etc.)
- **Authentication:** python-jose (JWT), passlib (password hashing)
- **Testing:** pytest + pytest-asyncio + pytest-cov + httpx
- **Code Quality:** Black (formatter), Ruff (linter), mypy (type checker)
- **Dependency Management:** Poetry

### Frontend (Vanilla JS + Modern Tooling)
- **Core:** HTML5, CSS3, JavaScript (ES6+)
- **Build Tool:** Vite (fast dev server + bundling)
- **Styling:** Tailwind CSS 3 + @tailwindcss/forms
- **Architecture:** Component-based (Web Components or class-based modules)
- **State Management:** Custom event-driven system (no framework bloat)
- **HTTP Client:** Fetch API (native) + wrapper for API calls
- **Testing:** Vitest (compatible with Vite)
- **UI Inspiration:** Anthropic Claude.ai aesthetic (clean, minimal, professional)

### Cloud & IaC
- **Target Cloud:** AWS (MVP), Azure & GCP (later phases)
- **IaC Output:** Terraform HCL (generated from JSON)
- **Terraform Generator:** Python (Jinja2 templates or direct string building)
- **AWS CLI:** For testing and manual operations

### DevOps
- **CI/CD:** GitHub Actions
- **Containerization:** Docker (for backend deployment)
- **Hosting Options:**
  - **Frontend:** AWS S3 + CloudFront (static hosting)
  - **Backend:** AWS Lambda (serverless) or ECS Fargate (containerized)
- **Monitoring:** AWS CloudWatch + Sentry (errors)
- **Analytics:** PostHog (optional)

---

## 📞 Communication Protocols

### With User (Andy)
- Always respond in **German** (unless code/docs require English)
- Be direct, no fluff
- Explain trade-offs clearly
- Ask when uncertain, don't guess
- Proactively suggest improvements

### Between Agents
- Use `/send-message` in agent teams
- Tag relevant agent (@backend, @frontend, etc.)
- Keep messages concise, actionable
- Document decisions in shared files

---

## 🎉 End Goal

Build a platform that makes cloud infrastructure:
✅ **Understandable** - Visual, transparent, documented
✅ **Versionable** - Track every change, rollback anytime
✅ **Evaluable** - Know cost/security before deploying
✅ **Multi-cloud** - Switch providers without rewriting
✅ **Professional** - Enterprise-ready UI/UX and security

**This is a long-term project. Build it right, not fast.**

---

Last updated: 2026-03-22