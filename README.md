# KrushiRakshak AI — Project Root

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd KrushiRakshak

# 2. Copy and configure environment files
cp backend/.env backend/.env          # already provided — edit API keys
cp frontend/.env.local.example frontend/.env.local

# 3. Spin up everything
docker-compose up --build

# 4. Open in browser
#   Frontend:       http://localhost:3000
#   Farmer App:     http://localhost:3000/farmer
#   Officer Panel:  http://localhost:3000/officer
#   Admin Center:   http://localhost:3000/admin
#   API Docs:       http://localhost:8000/api/docs
#   Health Check:   http://localhost:8000/api/health
```

## Project Structure

```
KrushiRakshak/
├── backend/               FastAPI (Python 3.11)
│   ├── app/
│   │   ├── api/           Route modules (health, farmer, officer, admin)
│   │   ├── db/            SQLAlchemy models + PostgreSQL connection
│   │   ├── ml/            Model loading / inference wrappers
│   │   ├── models/        Pydantic schemas
│   │   └── services/      Business logic (risk_engine, disease_detection, weather, advisory)
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/              Next.js 14 (App Router) + TypeScript + Tailwind
│   ├── app/
│   │   ├── farmer/        Farmer mobile-first UI
│   │   ├── officer/       District officer dashboard
│   │   └── admin/         Government command center
│   ├── components/        Shared component library
│   └── Dockerfile
├── ml-training/           Standalone training scripts + notebooks
└── docker-compose.yml
```

## Tech Stack

| Layer      | Technology |
|------------|------------|
| Backend    | FastAPI + SQLAlchemy + PostgreSQL |
| Frontend   | Next.js 14 App Router + TypeScript + Tailwind CSS |
| ML         | PyTorch (ResNet50) + scikit-learn + XGBoost |
| Maps       | MapLibre GL (scaffolded, ready to wire up) |
| DevOps     | Docker Compose |
