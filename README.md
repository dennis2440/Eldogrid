# EldoGrid AI

Smart urban-rural circular ecosystem for Eldoret: waste -> compost -> farmers -> climate alerts -> city dashboard.

## Run it (first time)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # already done if you used the scaffold script
python -m app.db.seed             # creates eldogrid.db with demo data
uvicorn app.main:app --reload
```

Open http://localhost:8000 (dashboard) and http://localhost:8000/docs (interactive API docs).

## Who owns what

| Folder / file | Owner |
|---|---|
| app/main.py, app/config.py, app/db/schema.sql, app/db/database.py, routes/dashboard.py, services/inventory.py | M1 Backend |
| static/ | M2 Frontend |
| routes/waste.py, routes/climate.py, services/classifier.py, services/risk_model.py, services/advice.py | M3 AI/Logic |
| routes/ussd.py, routes/sms.py, routes/payments.py, services/sms_client.py | M4 Telephony |
| app/db/seed.py, app/fixtures.py, docs/, README.md | M5 Integration |

Rules: never commit `.env` or `*.db`. Work on a branch, open a PR, never push to `main`.
API shapes are defined in `docs/api_contract.md`. Change the contract only after telling the team.
