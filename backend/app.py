from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from .schemas import RebookRequest, RebookResponse
from .services import TripGuardOrchestrator, get_all_employees

load_dotenv()

app = FastAPI(
    title="TripGuard Enterprise API",
    version="2.0",
    description="DB-backed Agentic Travel Disruption Engine"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = TripGuardOrchestrator()


@app.get("/")
def root():
    return {"message": "TripGuard DB-Backed Backend Running 🚀"}


@app.get("/employees")
def employees():
    return get_all_employees()


@app.post("/rebook", response_model=RebookResponse)
def rebook_trip(request: RebookRequest):
    return orchestrator.process_rebooking(request)