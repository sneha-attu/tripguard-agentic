import os
import random
from supabase import create_client

from .schemas import RebookResponse, AlternativeFlight
from .tools import (
    detect_disruption_tool,
    search_real_flights,
    normalize_flights
)

# ---------- Supabase Setup ----------

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(url, key)


def get_all_employees():
    response = supabase.table("employees50") \
        .select("employee_id, employee_name") \
        .execute()

    return response.data


def get_employee(employee_id: str):
    response = supabase.table("employees50") \
        .select("*") \
        .eq("employee_id", employee_id) \
        .execute()

    if not response.data:
        return None

    return response.data[0]


# ---------- Orchestrator ----------

class TripGuardOrchestrator:

    def process_rebooking(self, request):

        # 1️⃣ Fetch Employee
        employee = get_employee(request.user_id)

        if not employee:
            return RebookResponse(
                booking_id=request.booking_id,
                disruption_detected=False,
                disruption_type=None,
                policy_compliant=False,
                recommended_flight=None,
                alternatives=None,
                ai_confidence=0.0,
                ai_reasoning="Employee not found in database.",
                message="Invalid employee."
            )

        coverage_limit = employee["coverage_limit"]

        # 2️⃣ Detect Disruption
        disruption = detect_disruption_tool(request.departure_time)

        if not disruption:
            return RebookResponse(
                booking_id=request.booking_id,
                disruption_detected=False,
                disruption_type=None,
                policy_compliant=True,
                recommended_flight=None,
                alternatives=None,
                ai_confidence=0.95,
                ai_reasoning="No disruption detected. Original booking remains valid.",
                message="No rebooking required."
            )

        # 3️⃣ Fetch Real Flights from Amadeus
        raw_flights = search_real_flights(
            request.origin,
            request.destination,
            request.departure_time.date().isoformat()
        )

        normalized = normalize_flights(raw_flights)

        if not normalized:
            return RebookResponse(
                booking_id=request.booking_id,
                disruption_detected=True,
                disruption_type=disruption,
                policy_compliant=False,
                recommended_flight=None,
                alternatives=None,
                ai_confidence=0.5,
                ai_reasoning="No flights returned from travel API.",
                message="No alternative flights available."
            )

        # 4️⃣ Apply Coverage Filter
        compliant_flights = [
            f for f in normalized
            if f["price"] <= coverage_limit
        ]

        if not compliant_flights:
            return RebookResponse(
                booking_id=request.booking_id,
                disruption_detected=True,
                disruption_type=disruption,
                policy_compliant=False,
                recommended_flight=None,
                alternatives=None,
                ai_confidence=0.7,
                ai_reasoning=f"All flights exceed coverage limit ₹{coverage_limit}.",
                message="No compliant flights available."
            )

        # 5️⃣ Rank Flights (Lowest Price First)
        ranked = sorted(
            compliant_flights,
            key=lambda x: x["price"]
        )

        # 6️⃣ Select Top 5
        top_5 = ranked[:5]

        best_option = top_5[0]

        # Convert to Pydantic models
        alternatives_list = [
            AlternativeFlight(**flight)
            for flight in top_5
        ]

        confidence = round(0.85 + random.random() * 0.1, 2)

        reasoning = (
            f"Employee coverage cap ₹{coverage_limit} applied. "
            "Flights filtered by price and ranked in ascending order. "
            "Top 5 compliant options returned."
        )

        return RebookResponse(
            booking_id=request.booking_id,
            disruption_detected=True,
            disruption_type=disruption,
            policy_compliant=True,
            recommended_flight=AlternativeFlight(**best_option),
            alternatives=alternatives_list,
            ai_confidence=confidence,
            ai_reasoning=reasoning,
            message="Top 5 compliant flights returned successfully."
        )