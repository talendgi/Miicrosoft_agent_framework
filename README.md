# Workflow Studio

Visual ETL workflow builder with a React Flow canvas and a Python backend.

## What is included

- `Canvas` for drag-and-drop workflow composition
- `Connections` manager for source and destination systems
- `Pipelines` library for saved flows
- `Monitoring` view for execution history and node outputs
- Python backend with persistent JSON storage and executor registry

## Run locally

Backend:

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Notes

- Executors are intentionally separated into small classes to keep the design SOLID-friendly.
- The backend stores connections, pipelines, and runs in `backend/data/studio.json`.
- The UI is wired for the sample executors: `mysql_source`, `transform_data`, `check_table_exists`, and `load_data`.
