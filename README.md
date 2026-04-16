# CASA Python FastAPI Backend

Minimal governance backend for the **CASA** (Cognitive Agent Safety Architecture) platform.
It exposes REST endpoints for a dashboard, boundary-stress monitoring, policy dry-runs, decision replay, and administrative policy application.

The repository ships two application modules:

| Module | Version | Description |
|--------|---------|-------------|
| `main.py` | 0.1.0 | Original API with core endpoints |
| `main_v2.py` | 0.2.0 | Extended API adding `/api/v1/` namespaced routes, `X-Request-ID` header support, and an admin policy-apply endpoint |

---

## Requirements

- Python 3.12+
- Dependencies listed in `requirements.txt`

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/dburt-proex/python-fastapi-backend.git
cd python-fastapi-backend

# 2. Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment variables
cp .env.example .env

# 5. Start the server
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

To run the v2 API instead, use:

```bash
uvicorn main_v2:app --host 0.0.0.0 --port 8080 --reload
```

The interactive API docs are available at `http://localhost:8080/docs`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Port the server listens on |
| `ALLOWED_ORIGINS` | `*` | Comma-separated list of allowed CORS origins (or `*` for all) |

## API Endpoints

### v1 (`main.py`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/dashboard` | Governance dashboard summary |
| GET | `/stress` | Boundary stress overview |
| GET | `/boundary-stress` | Alias for `/stress` |
| POST | `/policy/dryrun` | Simulate a policy change |
| GET | `/replay/{decision_id}` | Replay a past decision |
| GET | `/decision-replay/{decision_id}` | Alias for `/replay/{decision_id}` |

### v2 (`main_v2.py`)

All v1 routes are available, plus `/api/v1/` prefixed equivalents and one new admin endpoint.
All v2 endpoints accept an optional `X-Request-ID` header for request tracing.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/dashboard`, `/api/v1/dashboard` | Governance dashboard summary |
| GET | `/stress`, `/boundary-stress`, `/api/v1/boundary-stress` | Boundary stress overview |
| POST | `/policy/dryrun`, `/api/v1/policy/dryrun` | Simulate a policy change |
| GET | `/replay/{decision_id}`, `/decision-replay/{decision_id}`, `/api/v1/decision-replay/{decision_id}` | Replay a past decision |
| POST | `/api/v1/admin/policy/apply` | Apply a policy (admin) |

### Example Requests

```bash
# Health check
curl http://localhost:8080/health

# Dashboard
curl http://localhost:8080/dashboard

# Boundary stress
curl http://localhost:8080/stress

# Policy dry-run
curl -X POST http://localhost:8080/policy/dryrun \
  -H "Content-Type: application/json" \
  -d '{"policyId": "POL-102", "environment": "staging"}'

# Decision replay
curl http://localhost:8080/replay/DEC-001

# Apply policy (v2 only)
curl -X POST http://localhost:8080/api/v1/admin/policy/apply \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-123" \
  -d '{"policyId": "POL-102", "reason": "Approved after review"}'
```

## Testing

```bash
# Run the full test suite
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=term-missing
```

## Docker

```bash
# Build the image
docker build -t casa-backend .

# Run the container
docker run -p 8080:8080 casa-backend
```

## Deployment

The repository includes a `Procfile` for platforms like Heroku and a `runtime.txt` specifying Python 3.12.10.

```bash
# Heroku-style deployment
heroku create
git push heroku main
```

## Project Structure

```
├── main.py            # v1 FastAPI application
├── main_v2.py         # v2 FastAPI application
├── tests/
│   ├── test_main.py   # Tests for v1 API
│   └── test_main_v2.py# Tests for v2 API
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container build
├── Procfile           # Process runner config
├── runtime.txt        # Python version spec
├── .env.example       # Environment variable template
└── .gitignore
```

## License

See repository for license details.
