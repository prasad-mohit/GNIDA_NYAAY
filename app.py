import streamlit as st  
import pandas as pd  
import time  
import plotly.express as px  
from io import BytesIO  
from datetime import datetime, timedelta  
import random  
from streamlit_calendar import calendar  
  
# ---------------------------  
# Demo Date  
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
  
# Dictionary to store assignments  
if "assignments" not in st.session_state:  
    st.session_state.assignments = {}  
  
# ---------------------------  
# Search Logic  
# ---------------------------  
def agentic_case_search(query, court_filter, status_filter, case_type_filter):  
    reasoning_steps = []  
    results = df_cases.copy()  
  
    reasoning_steps.append("🤖 Step 1: Received litigation search request.")  
  
    if court_filter != "All":  
        results = results[results["Court"] == court_filter]  
        reasoning_steps.append(f"📂 Filtered by Court: {court_filter}")  
  
    if status_filter != "All":  
        results = results[results["Status"] == status_filter]  
        reasoning_steps.append(f"📌 Filtered by Status: {status_filter}")  
  
    if case_type_filter != "All":  
        results = results[results["Case Type"] == case_type_filter]  
        reasoning_steps.append(f"🏷 Filtered by Case Type: {case_type_filter}")  
  
    if query.strip():  
        results = results[  
            results["Summary"].str.contains(query, case=False, na=False) |  
            results["Petitioner"].str.contains(query, case=False, na=False) |  
            results["Case Type"].str.contains(query, case=False, na=False)  
        ]  
        reasoning_steps.append("🧠 Applied text search filter.")  
  
    reasoning_steps.append(f"✅ Found {len(results)} matching cases.")  
    return reasoning_steps, results  
  
# ---------------------------  
# Excel Download  
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
# TAB 1: Search  
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
  
with tab2:  
    st.subheader("Litigation Analytics Dashboard")  
  
    # KPI Counters  
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)  
    kpi1.metric("Total Cases", len(df_cases))  
    kpi2.metric("Pending Cases", (df_cases['Status'] == 'Pending').sum())  
    kpi3.metric("Decided Cases", (df_cases['Status'] == 'Decided').sum())  
    kpi4.metric("Stayed Cases", (df_cases['Status'] == 'Stayed').sum())  
  
    # Charts with fixed y-axis ticks  
    col_a, col_b = st.columns(2)  
    with col_a:  
        fig1 = px.bar(  
            df_cases.groupby("Case Type").size().reset_index(name="Count"),  
            x="Case Type", y="Count", title="Cases by Type", color="Count"  
        )  
        fig1.update_yaxes(dtick=1)  # force whole numbers  
        st.plotly_chart(fig1, use_container_width=True)  
    with col_b:  
        fig2 = px.pie(df_cases, names="Court", title="Cases by Court")  
        st.plotly_chart(fig2, use_container_width=True)  
  
    st.divider()  
    st.subheader("📅 Upcoming Hearing Calendar (Weekdays Only)")  
  
    # Prepare hearing events  
    cal_df = df_cases[df_cases["Next Hearing Date"].notna()].sort_values("Next Hearing Date")  
    cal_df["Hearing"] = cal_df["Case No."] + " – " + cal_df["Petitioner"]  
  
    # Plotly timeline as calendar substitute  
    fig_cal = px.timeline(  
        cal_df,  
        x_start="Next Hearing Date",  
        x_end="Next Hearing Date",  
        y="Hearing",  
        color="Status",  
        title="Upcoming Hearings",  
        hover_data=["Court", "Case Type", "Summary"]  
    )  
    fig_cal.update_yaxes(autorange="reversed")  # earliest on top  
    fig_cal.update_xaxes(dtick="D1", tickformat="%d-%b")  # daily ticks  
    st.plotly_chart(fig_cal, use_container_width=True)  
  
    # Case selection for details  
    selected_case = st.selectbox("Select a case to view details", cal_df["Case No."].unique())  
    if selected_case:  
        case_data = df_cases[df_cases["Case No."] == selected_case].iloc[0]  
        st.markdown(f"### 📄 Case Details: {selected_case}")  
        st.write(f"**Court:** {case_data['Court']}")  
        st.write(f"**Petitioner:** {case_data['Petitioner']}")  
        st.write(f"**Case Type:** {case_data['Case Type']}")  
        st.write(f"**Filing Date:** {case_data['Filing Date'].strftime('%d %b %Y')}")  
        st.write(f"**Status:** {case_data['Status']}")  
        st.write(f"**Summary:** {case_data['Summary']}")  
        st.write(f"**Next Hearing:** {case_data['Next Hearing Date'].strftime('%d %b %Y')}")  
  
        # Assignment inputs  
        st.markdown("#### 🗂 Assign to Department & Individual")  
        department = st.selectbox("Select Department", ["Legal", "Land Acquisition", "Environment", "Infrastructure"])  
        individual = st.text_input("Assign to Officer Name")  
  
        if st.button("✅ Save Assignment"):  
            st.session_state.assignments[selected_case] = {"Department": department, "Officer": individual}  
            st.success(f"Assigned {selected_case} to {department} → {individual}")  
  
        if selected_case in st.session_state.assignments:  
            st.info(f"Current Assignment: {st.session_state.assignments[selected_case]['Department']} → {st.session_state.assignments[selected_case]['Officer']}")  
