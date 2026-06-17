import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# Load database URL securely from Streamlit secrets, with localhost as a fallback
try:
    DB_URL = st.secrets["DB_URL"]
except (FileNotFoundError, KeyError):
    DB_URL = "mysql+pymysql://root:mysql@localhost/flight_app1"

engine = create_engine(
    DB_URL,
    isolation_level="AUTOCOMMIT",
    pool_pre_ping=True,
    pool_recycle=3600
)


@st.cache_data(ttl=30)
def load_dashboard_data():
    searches_query = text("""
        SELECT
            s.search_id,
            a1.iata_code AS source,
            a2.iata_code AS destination,
            CONCAT(a1.iata_code, ' -> ', a2.iata_code) AS route,
            s.travel_date,
            s.search_timestamp
        FROM searches s
        JOIN airports a1
            ON s.source_airport_id = a1.airport_id
        JOIN airports a2
            ON s.destination_airport_id = a2.airport_id
        ORDER BY s.search_timestamp DESC
    """)

    flights_query = text("""
        SELECT
            f.flight_id,
            f.search_id,
            f.airline,
            f.departure_airport,
            f.arrival_airport,
            CONCAT(f.departure_airport, ' -> ', f.arrival_airport) AS route,
            f.departure_time,
            f.arrival_time,
            f.duration_minutes,
            f.price,
            s.travel_date,
            s.search_timestamp
        FROM flights f
        JOIN searches s
            ON f.search_id = s.search_id
        ORDER BY s.search_timestamp DESC
    """)

    with engine.connect() as conn:
        conn.execute(text("SET SESSION innodb_lock_wait_timeout = 5"))
        searches = pd.read_sql(searches_query, conn)
        flights = pd.read_sql(flights_query, conn)

    return searches, flights


def filter_by_date(df, date_column, start_date, end_date):
    if df.empty:
        return df

    filtered = df.copy()
    filtered[date_column] = pd.to_datetime(filtered[date_column]).dt.date
    return filtered[
        (filtered[date_column] >= start_date)
        & (filtered[date_column] <= end_date)
    ]


def show_metric_cards(searches, flights):
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Searches", f"{len(searches):,}")
    col2.metric("Flights Saved", f"{len(flights):,}")
    col3.metric("Unique Routes", f"{searches['route'].nunique() if not searches.empty else 0:,}")

    if flights.empty or flights["price"].isna().all():
        col4.metric("Average Price", "N/A")
    else:
        col4.metric("Average Price", f"${flights['price'].mean():,.2f}")


def main():
    st.set_page_config(
        page_title="Flight Dashboard",
        page_icon="✈️",
        layout="wide"
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
        h1, h2, h3, h4, p, label {
            color: #ffffff !important;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: rgba(0, 0, 0, 0.2) !important;
            backdrop-filter: blur(10px);
        }
        
        /* Metric Cards */
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: #ffffff !important;
        }
        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Input Fields styling */
        .stMultiSelect > div > div > div, 
        .stDateInput > div > div > input {
            border-radius: 10px !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        /* Buttons styling */
        .stButton > button {
            background: linear-gradient(45deg, #00d2ff 0%, #3a7bd5 100%);
            color: white !important;
            border-radius: 30px !important;
            border: none !important;
            padding: 10px 20px !important;
            font-weight: bold !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
            transition: all 0.3s ease !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 15px rgba(0, 210, 255, 0.4) !important;
        }

        /* Dataframe/Table styling */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Flight Search Dashboard")

    try:
        searches, flights = load_dashboard_data()
    except SQLAlchemyError as e:
        st.error(f"Could not load dashboard data from MySQL: {e}")
        return

    if searches.empty:
        st.info("No search data found yet. Run the flight search app and save a few searches first.")
        return

    searches["travel_date"] = pd.to_datetime(searches["travel_date"]).dt.date
    searches["search_timestamp"] = pd.to_datetime(searches["search_timestamp"])

    if not flights.empty:
        flights["travel_date"] = pd.to_datetime(flights["travel_date"]).dt.date
        flights["search_timestamp"] = pd.to_datetime(flights["search_timestamp"])
        flights["price"] = pd.to_numeric(flights["price"], errors="coerce")
        flights["duration_minutes"] = pd.to_numeric(
            flights["duration_minutes"],
            errors="coerce"
        )

    min_date = searches["travel_date"].min()
    max_date = searches["travel_date"].max()

    with st.sidebar:
        st.header("Filters")
        start_date, end_date = st.date_input(
            "Travel date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        route_options = sorted(searches["route"].dropna().unique())
        selected_routes = st.multiselect(
            "Routes",
            route_options,
            default=route_options
        )

        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    filtered_searches = filter_by_date(
        searches,
        "travel_date",
        start_date,
        end_date
    )
    filtered_searches = filtered_searches[
        filtered_searches["route"].isin(selected_routes)
    ]

    filtered_flights = filter_by_date(
        flights,
        "travel_date",
        start_date,
        end_date
    )
    if not filtered_flights.empty:
        filtered_flights = filtered_flights[
            filtered_flights["route"].isin(selected_routes)
        ]

    show_metric_cards(filtered_searches, filtered_flights)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Searches by Travel Date")
        daily_searches = (
            filtered_searches
            .groupby("travel_date")
            .size()
            .reset_index(name="searches")
            .set_index("travel_date")
        )
        st.line_chart(daily_searches)

    with col2:
        st.subheader("Popular Routes")
        popular_routes = (
            filtered_searches["route"]
            .value_counts()
            .head(10)
            .rename_axis("route")
            .reset_index(name="searches")
            .set_index("route")
        )
        st.bar_chart(popular_routes)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Airline Frequency")
        if filtered_flights.empty:
            st.info("No saved flight rows found for the selected filters.")
        else:
            airlines = (
                filtered_flights["airline"]
                .fillna("Unknown")
                .value_counts()
                .head(10)
                .rename_axis("airline")
                .reset_index(name="flights")
                .set_index("airline")
            )
            st.bar_chart(airlines)

    with col4:
        st.subheader("Average Price by Route")
        if filtered_flights.empty or filtered_flights["price"].isna().all():
            st.info("No price data found for the selected filters.")
        else:
            price_by_route = (
                filtered_flights
                .dropna(subset=["price"])
                .groupby("route")["price"]
                .mean()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
                .set_index("route")
            )
            st.bar_chart(price_by_route)

    st.subheader("Recent Searches")
    st.dataframe(
        filtered_searches[
            ["search_id", "source", "destination", "travel_date", "search_timestamp"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Saved Flight Details")
    if filtered_flights.empty:
        st.info("No saved flight details available.")
    else:
        st.dataframe(
            filtered_flights[
                [
                    "flight_id",
                    "search_id",
                    "airline",
                    "departure_airport",
                    "arrival_airport",
                    "departure_time",
                    "arrival_time",
                    "duration_minutes",
                    "price"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )


if __name__ == "__main__":
    main()
