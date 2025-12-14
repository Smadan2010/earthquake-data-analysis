import streamlit as st
import pandas as pd
import pydeck as pdk
from sqlalchemy import create_engine

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Earthquake Dashboard", layout="wide")

# ---------------- DB CONNECTION ----------------
engine = create_engine(
    "mysql+pymysql://root:2028@localhost:3306/capstones"
)

st.title(" Global Seismic Trends: Data-Driven Earthquake Insights.")
st.subheader("🌍 Earthquake Data Analysis Dashboard")

# ---------------- SIDEBAR ----------------
st.sidebar.title("Navigation")

category = st.sidebar.radio(
    "Select Category",
    ["All Data", "Data Analysis"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

# Year filter
years = pd.read_sql(
    "SELECT DISTINCT year FROM earthquake ORDER BY year", engine
)["year"].dropna().tolist()

year_filter = st.sidebar.selectbox("Select Year", ["All"] + years)

# Magnitude slider
min_mag, max_mag = pd.read_sql(
    "SELECT MIN(mag) AS min_mag, MAX(mag) AS max_mag FROM earthquake", engine
).iloc[0]

mag_range = st.sidebar.slider(
    "Magnitude Range",
    float(min_mag), float(max_mag),
    (float(min_mag), float(max_mag))
)

# ---------------- KPI CARDS ----------------
kpi_df = pd.read_sql(f"""
SELECT
    COUNT(*) AS total_eq,
    ROUND(AVG(mag),2) AS avg_mag,
    MAX(mag) AS max_mag,
    SUM(tsunami) AS tsunami_events
FROM earthquake
WHERE mag BETWEEN {mag_range[0]} AND {mag_range[1]}
""", engine)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Earthquakes", kpi_df.total_eq[0])
c2.metric("Avg Magnitude", kpi_df.avg_mag[0])
c3.metric("Max Magnitude", kpi_df.max_mag[0])
c4.metric("Tsunami Events", kpi_df.tsunami_events[0])

st.markdown("---")

queries = {
    "1. Top 10 strongest earthquakes (mag)": """
        SELECT *
        FROM earthquake
        ORDER BY mag DESC
        LIMIT 10;
    """,

    "2. Top 10 deepest earthquakes (depth)": """
        SELECT *
        FROM earthquake
        ORDER BY depth DESC
        LIMIT 10;
    """,

    "3. Shallow earthquakes < 50 km and mag > 7.5": """
        SELECT *
        FROM earthquake
        WHERE depth < 50 AND mag > 7.5;
    """,

    "5. Average magnitude per magnitude type (magType)": """
        SELECT magType, AVG(mag) AS avg_mag
        FROM earthquake
        GROUP BY magType;
    """,

    "6. Year with most earthquakes": """
        SELECT year , COUNT(*) AS EQ_count
        FROM earthquake
        GROUP BY year
        ORDER BY year DESC
        LIMIT 1;
    """,

    "7. Month with highest number of earthquakes": """
        SELECT month, COUNT(*) AS EQ_count
        FROM earthquake
        GROUP BY month
        ORDER BY EQ_count DESC
        LIMIT 1;
    """,

    "8. Day of week with most earthquakes": """
        SELECT day_of_week, COUNT(*) AS day_count
        FROM earthquake
        GROUP BY day_of_week
        ORDER BY day_count DESC
        LIMIT 1;
    """,

    "9. Count of earthquakes per hour of day": """
        SELECT EXTRACT(HOUR FROM time) AS hour_of_day,
               COUNT(*) AS EQ_count
        FROM earthquake
        GROUP BY hour_of_day
        ORDER BY hour_of_day;
    """,

    "10. Most active reporting network (net)": """
        SELECT net, COUNT(*) AS net_count
        FROM earthquake
        GROUP BY net
        ORDER BY net_count DESC
        LIMIT 1;
    """,

    "14. Reviewed vs automatic earthquakes": """
        SELECT status, COUNT(*) AS count
        FROM earthquake
        WHERE status IN ('reviewed','automatic')
        GROUP BY status;
    """,

    "15. Count by earthquake type": """
        SELECT type, COUNT(*) AS count
        FROM earthquake
        GROUP BY type;
    """,

    "16. Number of earthquakes by datatype (types)": """
        SELECT types, COUNT(*) AS type_count
        FROM earthquake
        GROUP BY types
        ORDER BY types ASC;
    """,

    "18. Events with high station coverage (nst > avg)": """
        SELECT *
        FROM earthquake
        WHERE nst > (
            SELECT AVG(nst)
            FROM earthquake
            WHERE nst IS NOT NULL
        );
    """,

    "19. Tsunami triggered earthquakes per year": """
        SELECT year, COUNT(*) AS tsunami_count
        FROM earthquake
        WHERE tsunami = 1
        GROUP BY year;
    """,

    "20. Count earthquakes by alert levels": """
        SELECT alert, COUNT(*) AS alert_count
        FROM earthquake
        WHERE alert IS NOT NULL
        GROUP BY alert
        ORDER BY alert_count DESC;
    """,

    "21. Top 5 countries with highest average magnitude": """
        SELECT country, AVG(mag) AS avg_mag
        FROM earthquake
        WHERE year >= (SELECT MAX(year) FROM earthquake)
        GROUP BY country
        ORDER BY avg_mag DESC
        LIMIT 5;
    """,

    "22. Countries with both shallow and deep earthquakes in same month": """
        SELECT country, month
        FROM earthquake
        GROUP BY country, month
        HAVING
            SUM(CASE WHEN depth < 70 THEN 1 ELSE 0 END) > 0
        AND SUM(CASE WHEN depth > 70 THEN 1 ELSE 0 END) > 0;
    """,

    "24. Top 3 most seismically active regions": """
        SELECT country,
               COUNT(*) AS No_of_count,
               AVG(mag) AS avg_magnitude
        FROM earthquake
        GROUP BY country
        ORDER BY No_of_count DESC, avg_magnitude DESC
        LIMIT 3;
    """,

    "25. Avg depth near equator (+-5 latitude)": """
        SELECT country, ROUND(AVG(depth),2) AS avg_depth
        FROM earthquake
        WHERE ABS(latitude) <= 5
        GROUP BY country;
    """,

    "27. Avg magnitude difference (tsunami vs non-tsunami)": """
        SELECT
            ROUND(AVG(CASE WHEN tsunami = 1 THEN mag END),2) AS with_tsunami,
            ROUND(AVG(CASE WHEN tsunami = 0 THEN mag END),2) AS without_tsunami,
            ROUND(
                AVG(CASE WHEN tsunami = 1 THEN mag END)
              - AVG(CASE WHEN tsunami = 0 THEN mag END),2
            ) AS magnitude_difference
        FROM earthquake;
    """,

    "28. Lowest data reliability (gap >120 & rms >0.6)": """
        SELECT *
        FROM earthquake
        WHERE gap > 120 AND rms > 0.6
        ORDER BY gap DESC, rms DESC;
    """,

    "30. Regions with highest deep focus earthquakes (>300km)": """
        SELECT latitude, longitude, place, depth, mag
        FROM earthquake
        WHERE depth > 300;
    """
}

# ---------------- ALL DATA ----------------
if category == "All Data":
    st.subheader("📊 All Earthquake Data")
    df = pd.read_sql("SELECT * FROM earthquake LIMIT 1000;", engine)
    st.dataframe(df, use_container_width=True)

# ---------------- DATA ANALYSIS ----------------
else:
    st.subheader("📈 Data Analysis")

    task = st.selectbox("Choose Question", list(queries.keys()))

    if st.button("Run Query"):
        df = pd.read_sql(queries[task], engine)

        # Apply filters safely
        if year_filter != "All" and "year" in df.columns:
            df = df[df["year"] == year_filter]

        if "mag" in df.columns:
            df = df[df["mag"].between(mag_range[0], mag_range[1])]

        # ---------- TABLE (TOP) ----------
        st.subheader("📋 Result Table")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")

        # ---------- CHART & MAP (BOTTOM) ----------
        left_col, right_col = st.columns(2)

        # LEFT → CHART
        with left_col:
            st.subheader("📊 Chart")
            num_cols = df.select_dtypes("number").columns
            if len(num_cols) > 0:
                st.bar_chart(df[num_cols[0]])
            else:
                st.info("No numeric data for chart")

        # RIGHT → MAP
        with right_col:
            st.subheader("🗺️ Map")
            if {"latitude", "longitude"}.issubset(df.columns):
                st.pydeck_chart(
                    pdk.Deck(
                        initial_view_state=pdk.ViewState(
                            latitude=df["latitude"].mean(),
                            longitude=df["longitude"].mean(),
                            zoom=2,
                        ),
                        layers=[
                            pdk.Layer(
                                "ScatterplotLayer",
                                data=df,
                                get_position="[longitude, latitude]",
                                get_radius=20000,
                                get_fill_color=[255, 80, 80],
                                pickable=True,
                            )
                        ],
                        tooltip={
                            "text": "Place: {place}\nMag: {mag}\nDepth: {depth}"
                        }
                    )
                )
            else:
                st.info("Map not applicable for this query")