# AI Pulse

AI Pulse helps a company understand how well its people use AI at work, team by team.

- **Employees** sign in, pick their organization, and take a short diagnostic. Questions adapt to their job role and seniority. One open-ended answer is scored by an LLM.
- **Each employee** gets a personal report: maturity level, risks, and next steps for their role.
- **Company admins** see a dashboard of AI maturity by department and the top risks across the company.
- Some users (consultants, group-company HR) belong to **more than one organization** and choose one after login.

This codebase was started by a previous developer who has since left. It runs, but it is unfinished, and we are not confident in all of it.

## Stack

- Backend: Python, FastAPI, SQLAlchemy (SQLite by default)
- Frontend: React (Vite)
- AI: any OpenAI-compatible chat completions endpoint, or mock mode with canned responses

## Run it locally

Backend:

```bash
cd backend
pip install -r requirements.txt
python -m app.seed          # creates demo data, password for all users: pulse123
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Tests:

```bash
cd backend
python -m pytest
```

Use Python 3.12 or 3.13 for the pinned dependencies. A virtual environment is recommended:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Demo accounts (password `pulse123`)

| Email | Organization(s) | Role |
|---|---|---|
| asha@northwind.test | Northwind Logistics | Admin |
| meera@bluepeak.test | Bluepeak Retail | Admin |
| ravi@consult.test | Both | Employee at Northwind, admin at Bluepeak |
| priya@northwind.test | Northwind Logistics | Employee (Support) |
| dev@northwind.test | Northwind Logistics | Employee (Engineering, lead) |

## AI mode

`AI_MODE=mock` (default) returns canned model responses from `backend/data/mock_ai_responses.json`. Like a real model, they are not always well-formed.

`AI_MODE=live` calls `LLM_API_URL` with `LLM_API_KEY` and `LLM_MODEL`.

## Assessment implementation

### Findings and fixes

- Organization selection now verifies that the authenticated user belongs to the requested organization.
- Dashboard access requires an admin membership whose organization matches the requested organization. Cross-organization access returns `403`.
- Dashboard department averages use completed employees' per-employee averages rather than all membership rows.
- Departments with fewer than five completed respondents are redacted. Their scores and risks are not returned to leadership.
- Employees can delete the diagnostic responses and report for the currently selected organization with `DELETE /reports/me`. The operation is scoped to the authenticated membership and is idempotent.
- Diagnostic submissions must contain exactly the applicable questions, with non-empty answers. Retaking a diagnostic replaces the previous responses instead of duplicating them.
- AI output is validated against a score range, required reason, and allowed risk flags. Invalid model output is rejected rather than saved.
- Seniority filtering uses an explicit junior-to-lead order rather than alphabetical string comparison.
- The frontend dashboard is now a usable table with loading and error states, and employees can use the deletion control from their report.

### Client request

The small-group rule is implemented by redacting departments with fewer than five employees who have responses. Redacted departments expose only their name and completion count; they do not expose scores, maturity levels, or risks. Risks from redacted departments are excluded from `top_risks`.

Deletion is scoped to the currently selected organization. This is intentional for multi-organization users: deleting a report for one client does not unexpectedly delete the user's separate report for another client. The database is queried again for every report and dashboard request, so deleted responses disappear immediately.

### Original feature: personalized action plan

The report now includes a deterministic action plan derived from the employee's actual risk flags. It turns risks such as customer-data sharing or unreviewed output into a priority, reason, and concrete action. This helps employees improve instead of only receiving a score, and it does not send an additional employee response to an LLM.

### Tests

The backend tests cover organization isolation, unauthorized organization selection, employee dashboard access, small-group redaction, deletion and idempotency, personalized action plans, role-specific questions, and malformed AI responses. The frontend is verified with the production Vite build.

### Deliberately left

This assessment implementation is not a claim that every production concern is complete. The following remain deliberate follow-up work:

- Password hashing should be migrated from SHA-256 to Argon2 or bcrypt, with a migration path for existing users.
- Production deployment needs rate limiting, structured audit logging, monitoring, secure secret management, and environment-specific CORS.
- SQLite and the simple `create_all` startup setup are retained for local assessment simplicity; a production deployment should use migrations and a managed database.
- Demo passwords and mock data are for local use only.
- The live LLM provider's retention, residency, and contractual privacy terms must be confirmed before sending employee answers to it.
- The project does not yet include account recovery, email verification, or a full administrative user-management workflow.

### AI tool usage

I used AI tools to inspect the repository, trace authorization paths, draft focused tests, review edge cases, and improve the frontend states. One AI-generated interpretation was wrong: it initially treated the existing cross-organization dashboard test as evidence that authorization worked. Inspecting the route showed that the test was actually asserting a successful response for an unauthorized organization, so the test was changed to expect `403` and the missing membership checks were implemented.
