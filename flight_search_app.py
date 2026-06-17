import streamlit as st
import requests
import json
from datetime import datetime

API_KEY = "161819f2defb33b044905155db46df5fb41a093509224e706bc5880b21952101"

from sqlalchemy import create_engine
import pymysql

engine = create_engine(
    'mysql+pymysql://root:mysql@localhost/flight_app'
)

def save_search(origin, destination, travel_date):

    conn = engine.raw_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "INSERT IGNORE INTO airports(iata_code) VALUES(%s)",
            (origin.upper(),)
        )

        cursor.execute(
            "INSERT IGNORE INTO airports(iata_code) VALUES(%s)",
            (destination.upper(),)
        )

        conn.commit()

        cursor.execute(
            "SELECT airport_id FROM airports WHERE iata_code=%s",
            (origin.upper(),)
        )
        source_id = cursor.fetchone()[0]

        cursor.execute(
            "SELECT airport_id FROM airports WHERE iata_code=%s",
            (destination.upper(),)
        )
        dest_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO searches(
                source_airport_id,
                destination_airport_id,
                travel_date
            )
            VALUES(%s,%s,%s)
        """, (
            source_id,
            dest_id,
            str(travel_date)
        ))

        conn.commit()

        return cursor.lastrowid

    except Exception as e:

        conn.rollback()
        raise e

    finally:

        cursor.close()
        conn.close()

def save_flight(
search_id,
airline,
dep_airport,
arr_airport,
dep_time,
arr_time,
duration,
price
):

    conn = engine.raw_connection()
    cursor = conn.cursor()

    try:

        dep_time = datetime.strptime(
            dep_time,
            "%Y-%m-%d %H:%M"
        )

        arr_time = datetime.strptime(
            arr_time,
            "%Y-%m-%d %H:%M"
        )

        duration = int(duration)

        price = float(price)

        cursor.execute("""
            INSERT INTO flights(
                search_id,
                airline,
                departure_airport,
                arrival_airport,
                departure_time,
                arrival_time,
                duration_minutes,
                price
            )
            VALUES(
                %s,%s,%s,%s,
                %s,%s,%s,%s
            )
        """, (
            search_id,
            airline,
            dep_airport,
            arr_airport,
            dep_time,
            arr_time,
            duration,
            price
        ))

        conn.commit()

    except Exception as e:

        conn.rollback()
        print("DB ERROR:", e)

    finally:

        cursor.close()
        conn.close()
def fetch_flights(origin, destination, date):
    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_flights",
        "api_key": API_KEY,
        "departure_id": origin.upper(),
        "arrival_id": destination.upper(),
        "outbound_date": date,
        "type": 2,
        "currency": "USD"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        if "error" in data:
            return f"API Error:\n{data['error']}"

        flights = data.get("best_flights", [])

        if not flights:
            flights = data.get("other_flights", [])

        search_id = save_search(
        origin,
        destination,
        date
        )


        if not flights:
            return (
                "No flights found.\n\n"
                "Debug Response:\n"
                + json.dumps(data, indent=2)[:3000]
            )

        result = "✈️ Available Flights\n\n"

        for i, flight in enumerate(flights[:5], start=1):

            total_duration = flight.get("total_duration", "N/A")
            price = flight.get("price", "N/A")

            segments = flight.get("flights", [])

            if not segments:
                continue

            first = segments[0]
            last = segments[-1]

            airline = first.get("airline", "Unknown")

            dep_airport = first.get(
                "departure_airport", {}
            ).get("id", origin.upper())

            dep_time = first.get(
                "departure_airport", {}
            ).get("time", "N/A")

            arr_airport = last.get(
                "arrival_airport", {}
            ).get("id", destination.upper())

            arr_time = last.get(
                "arrival_airport", {}
            ).get("time", "N/A")

            save_flight(
            search_id,
            airline,
            dep_airport,
            arr_airport,
            dep_time,
            arr_time,
            total_duration,
            price
            )
            result += (
                f"{i}. {airline}\n"
                f"   From: {dep_airport} ({dep_time})\n"
                f"   To:   {arr_airport} ({arr_time})\n"
                f"   Duration: {total_duration} mins\n"
                f"   Price: {price}\n\n"
            )

        return result

    except Exception as e:
        return f"Error: {str(e)}"
        return f"Error: {str(e)}"

st.set_page_config(
page_title="Flight Search",
page_icon="✈️",
layout="centered"
)

# Custom CSS for UI enhancements
st.markdown("""
    <style>
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white;
    }
    
    /* Headers and Text */
    h1, h2, h3, p, label {
        color: #ffffff !important;
    }
    
    /* Input Fields styling */
    .stTextInput > div > div > input, 
    .stDateInput > div > div > input {
        border-radius: 10px !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        padding: 12px 20px !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus, 
    .stDateInput > div > div > input:focus {
        border-color: #00d2ff !important;
        background-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 0 10px rgba(0, 210, 255, 0.5) !important;
    }

    /* Buttons styling */
    .stButton > button {
        background: linear-gradient(45deg, #00d2ff 0%, #3a7bd5 100%);
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        padding: 12px 30px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 20px rgba(0, 210, 255, 0.4) !important;
    }

    /* Text Area (Results) styling */
    .stTextArea > div > div > textarea {
        background-color: rgba(255, 255, 255, 0.85) !important;
        color: #111 !important;
        border-radius: 15px !important;
        border: none !important;
        padding: 20px !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 15px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
    }
    
    /* Warning message styling */
    .stAlert {
        background-color: rgba(255, 107, 107, 0.9) !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛫 Real-Time Flight Information")

st.write(
"Enter source airport, destination airport, and travel date "
"to retrieve flight details."
)

origin = st.text_input(
"Origin IATA Code",
placeholder="MAA"
)

destination = st.text_input(
"Destination IATA Code",
placeholder="DEL"
)

date = st.date_input(
"Date (YYYY-MM-DD)",value=None
)

if st.button("Search Flights"):


    if not origin or not destination or not date:
        st.warning("Please fill all fields.")
    else:
        with st.spinner("Fetching flights..."):
            result = fetch_flights(origin, destination, date)

        st.text_area(
            "Flight Results",
            value=result,
            height=400
        )

