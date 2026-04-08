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

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase credentials missing in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------- Employee Services ----------

def get_all_employees():
    try:
        response = supabase.table("employees50") \
            .select("*") \
            .execute()

        print("DATA FROM DB:", response.data)

        # map only needed fields
        return [
            {
                "employee_id": emp["employee_id"],
                "employee_name": emp["employee_name"]
            }
            for emp in response.data
        ]

    except Exception as e:
        print("ERROR FETCHING EMPLOYEES:", e)
        return []


def get_employee(employee_id: str):
    try:
        response = supabase.table("employees50") \
            .select("*") \
            .eq("employee_id", employee_id) \
            .execute()

        if not response.data:
            print("⚠️ Employee not found:", employee_id)
            return None

        return response.data[0]

    except Exception as e:
        print("❌ ERROR FETCHING EMPLOYEE:", e)
        return None


# ---------- Orchestrator ----------

class TripGuardOrchestrator:

    def process_rebooking(self, request):

        try:
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

            coverage_limit = employee.get("coverage_limit", 0)

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

            # 3️⃣ Fetch Flights
            raw_flights = search_real_flights(
                request.origin,
                request.destination,
                request.departure_time.date().isoformat()
            )

            print("✈️ Raw flights fetched:", len(raw_flights))

            normalized = normalize_flights(raw_flights)

            print("🔄 Normalized flights:", len(normalized))

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
                if f.get("price", 0) <= coverage_limit
            ]

            print("💰 Compliant flights:", len(compliant_flights))

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

            # 5️⃣ Rank Flights
            ranked = sorted(
                compliant_flights,
                key=lambda x: x["price"]
            )

            # 6️⃣ Top 5
            top_5 = ranked[:5]
            best_option = top_5[0]

            alternatives_list = [
                AlternativeFlight(**flight)
                for flight in top_5
            ]

            confidence = round(0.85 + random.random() * 0.1, 2)

            reasoning = (
                f"Employee coverage cap ₹{coverage_limit} applied. "
                "Flights filtered and ranked by lowest price. "
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

        except Exception as e:
            print("🔥 CRITICAL ERROR IN ORCHESTRATOR:", e)

            return RebookResponse(
                booking_id=request.booking_id,
                disruption_detected=False,
                disruption_type=None,
                policy_compliant=False,
                recommended_flight=None,
                alternatives=None,
                ai_confidence=0.0,
                ai_reasoning=str(e),
                message="Internal system error occurred."
            )