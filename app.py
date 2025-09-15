import streamlit as st  
import pandas as pd  
import time  
import plotly.express as px  
from io import BytesIO  
from datetime import datetime, timedelta  
import random  
  
# ---------------------------  
# Fixed Demo Date  
# ---------------------------  
TODAY = datetime(2025, 9, 15)  
  
# ---------------------------  
# Load Data  
# ---------------------------  
@st.cache_data  
def load_cases():  
    df = pd.read_csv("cases_data.csv", parse_dates=["Filing Date"], dayfirst=False)  
  
    # Generate realistic weekday hearing dates for Pending/Stayed  
    next_dates = []  
    for _, row in df.iterrows():  
        if row["Status"] in ["Pending", "Stayed"]:  
            while True:  
                days_ahead = random.randint(1, 30)  
                date_candidate = TODAY + timedelta(days=days_ahead)  
                if date_candidate.weekday() < 5:  # Mon-Fri only  
                    next_dates.append(date_candidate)  
                    break  
        else:  
            next_dates.append(pd.NaT)  
    df["Next Hearing Date"] = next_dates  
    return df  
  
df_cases = load_cases()  
  
# ---------------------------  
# Search Logic  
# ---------------------------  
def agentic_case_search(query, court_filter, status_filter, case_type_filter):  
    reasoning_steps = []  
    results = df_cases.copy()  
  
    reasoning_steps.append("🤖 Step 1: Received litigation search request.")  
  
    if court_filter != "All":  
        reasoning_steps.append(f"📂 Step 2: Filtering for court: {court_filter}")  
        results = results[results["Court"] == court_filter]  
  
    if status_filter != "All":  
        reasoning_steps.append(f"📌 Step 3: Filtering for status: {status_filter}")  
        results = results[results["Status"] == status_filter]  
  
    if case_type_filter != "All":  
        reasoning_steps.append(f"🏷 Step 4: Filtering for case type: {case_type_filter}")  
        results = results[results["Case Type"] == case_type_filter]  
  
    if query.strip():  
        reasoning_steps.append("🧠 Step 5: Searching in petitioner, summary, and case type...")  
        results = results[  
            results["Summary"].str.contains(query, case=False, na=False) |  
            results["Petitioner"].str.contains(query, case=False, na=False) |  
            results["Case Type"].str.contains(query, case=False, na=False)  
        ]  
  
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
# Layout  
# ---------------------------  
st.set_page_config(page_title="GNIDA Litigation Intelligence", layout="wide")  
  
st.title("⚖️ GNIDA Litigation Intelligence Platform")  
st.markdown("**A Smart AI-Powered Dashboard for Court Cases Against Greater Noida Authority**")  
st.divider()  
  
tab1, tab2 = st.tabs(["🔍 Litigation Search", "📊 Dashboard & Calendar"])  
  
# ---------------------------  
# TAB 1: Litigation Search  
# ---------------------------  
with tab1:  
    st.subheader("Search Litigation Records")  
  
    query_input = st.text_input("Enter your query", placeholder="e.g., land dispute, environmental, compensation")  
    col1, col2, col3 = st.columns(3)  
    with col1:  
        court_filter = st.selectbox("Court", ["All"] + sorted(df_cases["Court"].dropna().unique()))  
    with col2:  
        status_filter = st.selectbox("Case Status", ["All"] + sorted(df_cases["Status"].dropna().unique()))  
    with col3:  
        case_type_filter = st.selectbox("Case Type", ["All"] + sorted(df_cases["Case Type"].dropna().unique()))  
  
    if st.button("🚀 Run Search", type="primary"):  
        reasoning, results_df = agentic_case_search(query_input, court_filter, status_filter, case_type_filter)  
  
        with st.expander("🧠 Agentic Reasoning Trace"):  
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
  
# ---------------------------  
# TAB 2: Dashboard & Calendar  
# ---------------------------  
with tab2:  
    st.subheader("Litigation Analytics Dashboard")  
  
    # KPI Counters  
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)  
    kpi1.metric("Total Cases", len(df_cases))  
    kpi2.metric("Pending Cases", (df_cases['Status'] == 'Pending').sum())  
    kpi3.metric("Decided Cases", (df_cases['Status'] == 'Decided').sum())  
    kpi4.metric("Stayed Cases", (df_cases['Status'] == 'Stayed').sum())  
  
    # Charts  
    col_a, col_b = st.columns(2)  
    with col_a:  
        fig1 = px.bar(df_cases.groupby("Case Type").size().reset_index(name="Count"),  
                      x="Case Type", y="Count", title="Cases by Type", color="Count")  
        st.plotly_chart(fig1, use_container_width=True)  
    with col_b:  
        fig2 = px.pie(df_cases, names="Court", title="Cases by Court")  
        st.plotly_chart(fig2, use_container_width=True)  
  
    st.divider()  
    st.subheader("📅 Upcoming Hearing Calendar (Weekdays Only)")  
  
    # Calendar-style Gantt chart  
    cal_df = df_cases[df_cases["Next Hearing Date"].notna()].sort_values("Next Hearing Date")  
    if not cal_df.empty:  
        cal_df["Hearing"] = cal_df["Case No."] + " – " + cal_df["Petitioner"]  
        fig_cal = px.timeline(  
            cal_df,  
            x_start="Next Hearing Date",  
            x_end="Next Hearing Date",  
            y="Hearing",  
            color="Status",  
            title="Upcoming Hearings Schedule",  
        )  
        fig_cal.update_yaxes(autorange="reversed")  # earliest at top  
        fig_cal.update_layout(xaxis_title="Date", yaxis_title="Case")  
        st.plotly_chart(fig_cal, use_container_width=True)  
    else:  
        st.info("No upcoming hearings scheduled.")  
  
    st.divider()  
    st.subheader("📜 All Case Records")  
    st.dataframe(df_cases, use_container_width=True)  
