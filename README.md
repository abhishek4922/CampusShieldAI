# 🛡️ CampusShield AI

> **Safer digital experiences for students and institutions — simple, explainable, effective.**

CampusShield AI is a production-ready, privacy-first SaaS security platform designed for higher education.
It provides explainable phishing detection, consent-first identity verification, privacy-preserving analytics,
and a digital hygiene AI companion — all within a multi-campus, tenant-isolated architecture.

---

## Architecture Overview

```
Internet → Nginx (SSL) → [Next.js Frontend | FastAPI Backend | ML Microservice]
                                        ↓               ↓
                                  PostgreSQL         Redis
                              (Multi-tenant DB)   (Cache/Rate-limit)
```

Five core microservices:
| Service         | Technology              | Port  |
|-----------------|-------------------------|-------|
| Frontend        | Next.js 14 + TypeScript | 3000  |
| Backend API     | FastAPI + PostgreSQL     | 8000  |
| ML Microservice | FastAPI + scikit-learn   | 8001  |
| Database        | PostgreSQL 16            | 5432  |
| Cache           | Redis 7                  | 6379  |
| Monitoring      | Prometheus + Grafana     | 9090/3001 |

---

## Quick Start (Docker)

```bash
# 1. Clone and configure environment
cp .env.example .env
# Edit .env with your secrets

# 2. Start all services
docker-compose up --build -d

# 3. Run database migrations
docker-compose exec backend alembic upgrade head

# 4. Access the platform
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/docs
# ML Docs:   http://localhost:8001/docs
# Metrics:   http://localhost:9090
```

---

## Project Structure

```
campusshield/
├── backend/          # FastAPI core API (auth, RBAC, scans, analytics)
├── ml_service/       # ML microservice (phishing detection, risk scoring)
├── frontend/         # Next.js dashboard (student, admin, security roles)
├── nginx/            # Reverse proxy + SSL termination
└── infrastructure/   # Prometheus, Grafana, Kubernetes manifests
```

---

## Key Design Decisions

- **No raw PII storage**: Email bodies, subjects, and sender names are never persisted.
  Only extracted feature vectors and risk scores are stored.
- **Tenant isolation**: Every database query is scoped by `campus_id`.
- **Differential privacy**: Analytics snapshots are computed with DP noise (ε-differential privacy)
  before any aggregate is written, preventing re-identification.
- **Audit-only logs**: The `audit_logs` table is enforced insert-only at the database level via PostgreSQL rules.
- **Explainability first**: Every phishing alert includes human-readable signal weights and a
  plain-language explanation of why the message was flagged.

---

## AMD Optimization

The ML microservice is designed to fully utilize AMD EPYC CPUs:
- `joblib` parallel inference with `n_jobs=-1` (all cores)
- `threadpoolctl` to tune BLAS/OpenBLAS thread counts
- Container resource limits tuned for NUMA-aware memory allocation
- Compatible with AMD ROCm for GPU-accelerated transformer inference

See `ml_service/app/pipeline/amd_optimizer.py` for details.

---

## Security Posture

- HTTPS-only (Nginx terminates TLS)
- JWT with 15-min access + 7-day refresh tokens
- bcrypt password hashing (cost factor 12)
- Per-IP rate limiting via Redis
- CSRF protection via double-submit cookies
- RBAC: student / admin / security roles with middleware enforcement
- Secure cookie flags (HttpOnly, SameSite=Strict, Secure)

---

## License

MIT — Built for academic and competition purposes.
