import streamlit as st  
import pandas as pd  
import time  
import plotly.express as px  
from io import BytesIO  
from datetime import datetime, timedelta  
import random  
from streamlit_calendar import calendar  
  
# ---------------------------  
# Fixed "Today" for Demo  
# ---------------------------  
TODAY = datetime(2025, 9, 15)  
  
# ---------------------------  
# Load Data  
# ---------------------------  
@st.cache_data  
def load_cases():  
    df = pd.read_csv("cases_data.csv", parse_dates=["Filing Date"], dayfirst=False)  
  
    # Auto-generate Next Hearing Date for Pending/Stayed cases  
    next_dates = []  
    for _, row in df.iterrows():  
        if row["Status"] in ["Pending", "Stayed"]:  
            # Random date between 1 and 30 days from TODAY  
            days_ahead = random.randint(1, 30)  
            next_dates.append(TODAY + timedelta(days=days_ahead))  
        else:  
            next_dates.append(pd.NaT)  
    df["Next Hearing Date"] = next_dates  
    return df  
  
df_cases = load_cases()  
  
# ---------------------------  
# Agentic Search  
# ---------------------------  
def agentic_case_search(query, court_filter, status_filter, case_type_filter):  
    reasoning_steps = []  
    results = df_cases.copy()  
  
    reasoning_steps.append("🤖 Step 1: Received litigation search request.")  
  
    if court_filter != "All":  
        reasoning_steps.append(f"📂 Step 2: Filtering for court: {court_filter}")  
        results = results[results["Court"] == court_filter]  
    else:  
        reasoning_steps.append("📂 Step 2: Searching across all courts.")  
  
    if status_filter != "All":  
        reasoning_steps.append(f"📌 Step 3: Filtering for status: {status_filter}")  
        results = results[results["Status"] == status_filter]  
    else:  
        reasoning_steps.append("📌 Step 3: Including all statuses.")  
  
    if case_type_filter != "All":  
        reasoning_steps.append(f"🏷 Step 4: Filtering for case type: {case_type_filter}")  
        results = results[results["Case Type"] == case_type_filter]  
    else:  
        reasoning_steps.append("🏷 Step 4: Including all case types.")  
  
    if query.strip():  
        reasoning_steps.append("🧠 Step 5: Matching query against petitioner, summary, and case type...")  
        results = results[  
            results["Summary"].str.contains(query, case=False, na=False) |  
            results["Petitioner"].str.contains(query, case=False, na=False) |  
            results["Case Type"].str.contains(query, case=False, na=False)  
        ]  
    else:  
        reasoning_steps.append("🧠 Step 5: No query text provided.")  
  
    if results.empty:  
        reasoning_steps.append("⚠️ Step 6: No matching cases found.")  
    else:  
        reasoning_steps.append(f"✅ Step 6: Found {len(results)} matching cases.")  
  
    return reasoning_steps, results  
  
# ---------------------------  
# Download Helper  
# ---------------------------  
def download_excel(df):  
    output = BytesIO()  
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:  
        df.to_excel(writer, index=False, sheet_name='Cases')  
    return output.getvalue()  
  
# ---------------------------  
# Streamlit Layout  
# ---------------------------  
st.set_page_config(page_title="GNIDA Litigation Dashboard", layout="wide")  
st.title("⚖️ GNIDA Litigation Analytics & Case Search")  
st.markdown("*Agentic AI powered dashboard for court cases & disputes*")  
st.divider()  
  
# --- KPI Counters ---  
col1, col2, col3, col4 = st.columns(4)  
with col1:  
    st.metric("Total Cases", len(df_cases))  
with col2:  
    st.metric("Pending Cases", (df_cases['Status'] == 'Pending').sum())  
with col3:  
    st.metric("Decided Cases", (df_cases['Status'] == 'Decided').sum())  
with col4:  
    st.metric("Stayed Cases", (df_cases['Status'] == 'Stayed').sum())  
  
st.divider()  
  
# --- Charts ---  
chart_col1, chart_col2 = st.columns(2)  
  
with chart_col1:  
    fig1 = px.bar(df_cases.groupby("Case Type").size().reset_index(name="Count"),  
                  x="Case Type", y="Count", title="Cases by Type", color="Count")  
    st.plotly_chart(fig1, use_container_width=True)  
  
with chart_col2:  
    fig2 = px.pie(df_cases, names="Court", title="Cases by Court")  
    st.plotly_chart(fig2, use_container_width=True)  
  
st.divider()  
  
# --- Search Filters ---  
st.subheader("🔍 Search & Filter Cases")  
col1, col2, col3, col4 = st.columns(4)  
with col1:  
    query_input = st.text_input("Search Text", placeholder="e.g., land dispute, environmental...")  
with col2:  
    court_filter = st.selectbox("Court", ["All"] + sorted(df_cases["Court"].dropna().unique()))  
with col3:  
    status_filter = st.selectbox("Case Status", ["All"] + sorted(df_cases["Status"].dropna().unique()))  
with col4:  
    case_type_filter = st.selectbox("Case Type", ["All"] + sorted(df_cases["Case Type"].dropna().unique()))  
  
if st.button("🚀 Run Search"):  
    reasoning, results_df = agentic_case_search(query_input, court_filter, status_filter, case_type_filter)  
  
    with st.expander("🧠 Agentic Reasoning Trace", expanded=True):  
        for step in reasoning:  
            st.markdown(step)  
            time.sleep(0.05)  
  
    st.subheader(f"📊 Search Results ({len(results_df)} cases)")  
    if not results_df.empty:  
        st.dataframe(results_df, use_container_width=True)  
        st.download_button("⬇️ Download Results as Excel", data=download_excel(results_df),  
                           file_name="litigation_search_results.xlsx")  
    else:  
        st.warning("No matching litigation records found.")  
  
st.divider()  
  
# --- Hearing Calendar ---  
st.subheader("📅 Upcoming Hearing Calendar (Visual)")  
  
# Prepare calendar events  
events = []  
for _, row in df_cases[df_cases["Next Hearing Date"].notna()].iterrows():  
    events.append({  
        "title": f"{row['Case No.']} – {row['Petitioner']}",  
        "start": row["Next Hearing Date"].strftime("%Y-%m-%d"),  
        "end": row["Next Hearing Date"].strftime("%Y-%m-%d"),  
        "color": "red" if row["Status"] == "Pending" else "orange"  
    })  
  
calendar_options = {  
    "initialView": "dayGridMonth",  
    "headerToolbar": {  
        "left": "prev,next today",  
        "center": "title",  
        "right": "dayGridMonth,timeGridWeek"  
    }  
}  
  
calendar(events=events, options=calendar_options)  
  
st.divider()  
  
# --- All Cases ---  
st.subheader("📜 All Case Records")  
st.dataframe(df_cases, use_container_width=True)  
