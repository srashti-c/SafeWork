# SafeWork

## Run it (easiest: Docker)
1. Install Docker Desktop.
2. In this folder run:  `docker compose up --build`
3. Open http://localhost:8000/docs  (interactive API page)
4. Check http://localhost:8000/health and http://localhost:8000/health/db

## Run without Docker (uses a local SQLite file, fine for early development)
```
cd backend
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
# open backend/.env and set:  DATABASE_URL=sqlite:///./dev.db
uvicorn app.main:app --reload
```

## Run tests
```
cd backend
pytest
```
