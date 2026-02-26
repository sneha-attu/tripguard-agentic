import os
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
from amadeus import Client, ResponseError

# Load environment variables
load_dotenv()


# ---------- Amadeus Client Factory ----------

def get_amadeus_client():
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "Amadeus credentials missing. Check AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in .env"
        )

    return Client(
        client_id=client_id,
        client_secret=client_secret
    )


# ---------- Disruption Detection ----------

def detect_disruption_tool(departure_time: datetime):

    now = datetime.now(timezone.utc)

    if departure_time.tzinfo is None:
        departure_time = departure_time.replace(tzinfo=timezone.utc)

    if departure_time < now:
        return "cancellation"

    if random.random() < 0.3:
        return "delay"

    return None


# ---------- Real Flight Search (Amadeus) ----------

def search_real_flights(origin: str, destination: str, departure_date: str):

    try:
        amadeus = get_amadeus_client()

        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=1,
            currencyCode="EUR",   # REQUIRED for sandbox
            max=5
        )

        return response.data

    except ResponseError as error:
        print("Amadeus API error:", error)
        return []
# ---------- Normalize Flight Data ----------

def normalize_flights(raw_flights):

    normalized = []

    for flight in raw_flights:
        try:
            price = float(flight["price"]["total"])

            segment = flight["itineraries"][0]["segments"][0]

            normalized.append({
                "flight_number": segment["carrierCode"],
                "airline": flight["validatingAirlineCodes"][0],
                "departure_time": segment["departure"]["at"],
                "arrival_time": segment["arrival"]["at"],
                "price": price
            })

        except Exception:
            continue

    return normalized