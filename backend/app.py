from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import RebookRequest
from services import TripGuardOrchestrator, get_all_employees

app = FastAPI(title="TripGuard Enterprise API")

# ---------- CORS (IMPORTANT FOR FRONTEND) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Root ----------
@app.get("/")
def root():
    return {"message": "TripGuard Agentic Backend Running 🚀"}


# ---------- Employees Endpoint ----------
@app.get("/employees")
def employees():
    try:
        data = get_all_employees()
        return data
    except Exception as e:
        print("Employees API error:", e)
        return []


# ---------- Rebook Endpoint ----------
@app.post("/rebook")
def rebook_trip(request: RebookRequest):

    try:
        orchestrator = TripGuardOrchestrator()

        result = orchestrator.process_rebooking(request)

        return result

    except Exception as e:
        print("Rebooking error:", e)

        return {
            "booking_id": request.booking_id,
            "disruption_detected": False,
            "disruption_type": None,
            "policy_compliant": False,
            "recommended_flight": None,
            "alternatives": None,
            "ai_confidence": 0.0,
            "ai_reasoning": "System error occurred.",
            "message": "Internal server error"
        }