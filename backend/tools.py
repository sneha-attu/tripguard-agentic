import os
import random
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from amadeus import Client, ResponseError

load_dotenv()

# ---------- Amadeus Client ----------

def get_amadeus_client():
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("Amadeus credentials missing in .env")

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


# ---------- PRIMARY: Amadeus Search ----------

def search_amadeus(origin: str, destination: str, departure_date: str):

    try:
        amadeus = get_amadeus_client()

        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=1,
            currencyCode="EUR",
            max=5
        )

        print("✅ Amadeus response received")
        return response.data

    except ResponseError as error:
        print("❌ Amadeus API error:", error)
        return []


# ---------- FALLBACK: Kiwi (FREE REAL DATA) ----------

def search_kiwi(origin: str, destination: str, departure_date: str):

    try:
        formatted_date = datetime.fromisoformat(departure_date).strftime("%d/%m/%Y")

        url = "https://api.tequila.kiwi.com/v2/search"

        headers = {
            "apikey": os.getenv("KIWI_API_KEY")  # REQUIRED
        }

        params = {
            "fly_from": origin,
            "fly_to": destination,
            "date_from": formatted_date,
            "date_to": formatted_date,
            "adults": 1,
            "curr": "INR",
            "limit": 5
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        print("KIWI STATUS:", response.status_code)
        print("KIWI RAW:", response.text[:200])  # debug

        data = response.json()

        return data.get("data", [])

    except Exception as e:
        print("❌ Kiwi error:", e)
        return []
# ---------- Aviationstack Flight Search ----------

def search_real_flights(origin: str, destination: str, departure_date: str):

    try:
        url = "http://api.aviationstack.com/v1/flights"

        params = {
            "access_key": os.getenv("AVIATIONSTACK_API_KEY"),
            "dep_iata": origin,
            "arr_iata": destination,
            "limit": 10
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        print("AVIATIONSTACK RAW:", data)

        return data.get("data", [])

    except Exception as e:
        print("Aviationstack error:", e)
        return []


# ---------- Normalize + ADD PRICE ----------

def normalize_flights(raw_flights):

    normalized = []

    for flight in raw_flights:
        try:
            airline = flight.get("airline", {}).get("name", "Unknown")
            flight_number = flight.get("flight", {}).get("iata", "N/A")

            departure = flight.get("departure", {}).get("scheduled")
            arrival = flight.get("arrival", {}).get("scheduled")

            # 💡 FAKE BUT REALISTIC PRICE MODEL
            base_price = random.randint(3000, 15000)

            # Simulate airline pricing variation
            if "Emirates" in airline:
                base_price += 8000
            elif "IndiGo" in airline:
                base_price += 2000

            normalized.append({
                "flight_number": flight_number,
                "airline": airline,
                "departure_time": departure,
                "arrival_time": arrival,
                "price": float(base_price)
            })

        except Exception:
            continue

    print(f"✈️ Flights after normalization: {len(normalized)}")

    return normalized