"""App entry point (M1). Registers routers; keep logic out of this file."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db.database import init_db
from app.routes import climate, dashboard, payments, sms, ussd, waste


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="EldoGrid AI", lifespan=lifespan)

for module in (waste, climate, ussd, sms, payments, dashboard):
    app.include_router(module.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
