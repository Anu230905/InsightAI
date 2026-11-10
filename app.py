


import streamlit as st
import pandas as pd
import plotly.express as px
import json

from backend.database import DataEngine
from backend.quality import DataQualityDoctor
from backend.cleaning import DataCleaningLab
from backend.sql_analytics import SQLAnalytics
from backend.nl_sql import NaturalLanguageSQL
from backend.visualization import VisualizationStudio
from backend.root_cause import RootCauseAnalyzer
from backend.what_if import WhatIfSimulator
from backend.report_generator import AIReportGenerator
from backend.agentic_engine import AgenticDataAnalyst


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="InsightAI - Data Intelligence",
    page_icon="📊",
    layout="wide"
)


# ==================================================
# SESSION STATE
# ==================================================

default_states = {
    "engine": None,
    "cleaned_df": None,
    "cleaning_report": None,
    "quality_report": None,
    "sql_result": None,
    "nl_sql_query": None,
    "nl_sql_result": None,
    "viz_fig": None,
    "root_cause_result": None,
    "simulated_df": None,
    "simulation_report": None,
    "ai_report": None,
    "ai_report_summary": None,
    "agent_result": None
}

for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# STYLING
# ==================================================


# ==================================================
# STYLING - IMPROVED VISIBILITY
# ==================================================

st.markdown("""
<style>

/* Main application */
.stApp {
    background-color: #F8FAFC;
    color: #1E293B;
}

/* Main content area */
[data-testid="stMain"] {
    background-color: #F8FAFC;
}

/* Main content spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Main headings */
h1, h2, h3, h4 {
    color: #1E3A5F !important;
    font-weight: 700 !important;
}

/* Paragraphs and normal text */
p, label, span, li {
    color: #334155;
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: #EAF0F7 !important;
    min-width: 250px;
}

/* Sidebar text visibility */
[data-testid="stSidebar"] * {
    color: #243B53 !important;
}

/* Sidebar title */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #17365D !important;
    font-weight: 700 !important;
}

/* Sidebar navigation */
[data-testid="stSidebar"] label {
    color: #334155 !important;
    font-weight: 500;
}

/* Sidebar radio buttons */
[data-testid="stSidebar"] [role="radiogroup"] label {
    color: #334155 !important;
    font-size: 14px;
}

/* Input fields */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
}

/* Select boxes */
[data-baseweb="select"] {
    background-color: #FFFFFF !important;
}

/* Buttons */
.stButton > button {
    background-color: #2563EB;
    color: #FFFFFF !important;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1rem;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #1D4ED8;
    color: #FFFFFF !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    padding: 15px;
    border-radius: 10px;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: #FFFFFF;
    border-radius: 10px;
}

/* Responsive headings */
h1 {
    font-size: clamp(1.5rem, 3vw, 2.4rem) !important;
    overflow-wrap: anywhere;
}

/* Responsive layout */
@media (max-width: 700px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# COMMON FUNCTIONS
# ==================================================

def get_original_data():
    if st.session_state.engine is None:
        return None
    return st.session_state.engine.get_data()


def get_analysis_data(use_cleaned=False):
    if use_cleaned and st.session_state.cleaned_df is not None:
        return st.session_state.cleaned_df.copy()
    return get_original_data()


def require_dataset():
    if st.session_state.engine is None:
        st.warning("Please upload a dataset in Phase 1 first.")
        return False
    return True


def reset_analysis_results():
    keys = [
        "cleaned_df", "cleaning_report", "quality_report",
        "sql_result", "nl_sql_query", "nl_sql_result",
        "viz_fig", "root_cause_result", "simulated_df",
        "simulation_report", "ai_report",
        "ai_report_summary", "agent_result"
    ]
    for key in keys:
        st.session_state[key] = None


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

st.sidebar.title("📊 InsightAI")
st.sidebar.caption(
    "Agentic Data Intelligence and Decision Support System"
)
st.sidebar.divider()

pages = [
    "Phase 1 - Dataset Upload",
    "Phase 2 - Data Quality Doctor",
    "Phase 3 - Data Cleaning",
    "Phase 4 - SQL Analytics",
    "Phase 5 - Natural Language SQL",
    "Phase 6 - Visualization Studio",
    "Phase 7 - Root Cause Analysis",
    "Phase 8 - What-If Simulation",
    "Phase 9 - AI Report Generator",
    "Phase 10 - Agentic AI Analyst"
]

page = st.sidebar.radio("Navigate Modules", pages)

st.sidebar.divider()

if st.session_state.engine is None:
    st.sidebar.warning("No dataset uploaded")
else:
    st.sidebar.success("Dataset loaded")

st.sidebar.caption(
    "InsightAI | Data Intelligence & Decision Support"
)


# ==================================================
# PHASE 1 - DATASET UPLOAD AND PROFILING
# ==================================================

if page == "Phase 1 - Dataset Upload":

    st.title("📁 Dataset Upload & Profiling")
    st.write(
        "Upload your CSV or Excel dataset to begin analysing data."
    )

    uploaded_file = st.file_uploader(
        "Choose your dataset",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is not None:

        if st.button("Upload and Analyse Dataset", type="primary"):

            try:
                engine = DataEngine()

                engine.load_file(
                    uploaded_file.getvalue(),
                    uploaded_file.name
                )

                old_engine = st.session_state.engine
                st.session_state.engine = engine

                if old_engine is not None:
                    try:
                        old_engine.close()
                    except Exception:
                        pass

                reset_analysis_results()
                st.success("Dataset uploaded successfully!")

            except Exception as error:
                st.error(f"Dataset upload failed: {error}")

    if st.session_state.engine is not None:

        try:
            summary = st.session_state.engine.get_summary_stats()

            st.divider()
            st.subheader("Dataset Overview")

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Rows", f"{summary['row_count']:,}")
            col2.metric("Total Columns", len(summary["columns"]))
            col3.metric(
                "Columns with Missing Values",
                len(summary["missing_values"])
            )

            st.subheader("Column Information")
            st.dataframe(summary["columns"], use_container_width=True)

            st.subheader("Missing Values")

            missing_df = pd.DataFrame(
                list(summary["missing_values"].items()),
                columns=["Column", "Missing Values"]
            )

            if missing_df.empty:
                st.success("No missing values found.")
            else:
                st.dataframe(missing_df, use_container_width=True)

            st.subheader("Dataset Preview")
            st.dataframe(
                st.session_state.engine.get_preview(limit=10),
                use_container_width=True
            )

        except Exception as error:
            st.error(f"Could not display dataset summary: {error}")


# ==================================================
# PHASE 2 - DATA QUALITY DOCTOR
# ==================================================

elif page == "Phase 2 - Data Quality Doctor":

    st.title("🩺 Data Quality Doctor")
    st.write(
        "Identify missing values, duplicates, formatting issues, "
        "outliers and invalid values."
    )

    if require_dataset():

        if st.button("Run Data Quality Analysis", type="primary"):

            try:
                doctor = DataQualityDoctor()
                st.session_state.quality_report = doctor.analyze(
                    get_original_data()
                )
                st.success("Data quality analysis completed!")

            except Exception as error:
                st.error(f"Analysis failed: {error}")

        report = st.session_state.quality_report

        if report is not None:

            st.subheader("1. Missing Values")
            missing = report.get("missing_values", {})

            if missing:
                st.dataframe(
                    pd.DataFrame(
                        list(missing.items()),
                        columns=["Column", "Missing Count"]
                    ),
                    use_container_width=True
                )
            else:
                st.success("No missing values detected.")

            st.subheader("2. Duplicate Records")
            st.metric("Duplicate Rows", report.get("duplicates", 0))

            st.subheader("3. Formatting Issues")
            formatting = report.get("formatting_issues", {})
            st.write(formatting if formatting else "No formatting issues detected.")

            st.subheader("4. Numerical Outliers")
            outliers = report.get("outliers", {})
            st.write(outliers if outliers else "No outliers detected.")

            st.subheader("5. Invalid Values")
            invalid = report.get("invalid_values", {})
            st.write(invalid if invalid else "No invalid values detected.")


# ==================================================
# PHASE 3 - DATA CLEANING
# ==================================================

elif page == "Phase 3 - Data Cleaning":

    st.title("🧹 Data Cleaning & Repair Lab")
    st.write("Clean missing values, duplicates, text and invalid values.")

    if require_dataset():

        original_df = get_original_data()

        missing_strategy = st.selectbox(
            "Missing Value Strategy",
            ["mean", "median", "mode", "drop", "leave"]
        )

        remove_duplicates = st.checkbox(
            "Remove duplicate rows", value=True
        )

        trim_text = st.checkbox(
            "Remove leading and trailing spaces", value=True
        )

        text_case = st.selectbox(
            "Text Standardization",
            ["Keep original", "lowercase", "uppercase", "title"]
        )

        fix_invalid = st.checkbox(
            "Handle invalid sales values", value=True
        )

        if st.button("Clean Dataset", type="primary"):

            try:
                cleaner = DataCleaningLab()

                cleaned_df, report = cleaner.clean(
                    original_df,
                    missing_strategy=missing_strategy,
                    remove_duplicates=remove_duplicates,
                    trim_text=trim_text,
                    text_case=text_case,
                    fix_invalid=fix_invalid
                )

                st.session_state.cleaned_df = cleaned_df
                st.session_state.cleaning_report = report

                # Clear results based on an older cleaned dataset.
                for key in [
                    "root_cause_result", "simulated_df",
                    "simulation_report", "ai_report",
                    "ai_report_summary", "agent_result",
                    "viz_fig"
                ]:
                    st.session_state[key] = None

                st.success("Dataset cleaning completed!")

            except Exception as error:
                st.error(f"Cleaning failed: {error}")

        cleaned_df = st.session_state.cleaned_df
        report = st.session_state.cleaning_report

        if cleaned_df is not None and report is not None:

            st.subheader("Cleaning Summary")

            col1, col2, col3 = st.columns(3)

            col1.metric("Original Rows", report.get("original_rows", 0))
            col2.metric("Cleaned Rows", report.get("cleaned_rows", 0))
            col3.metric(
                "Duplicates Removed",
                report.get("duplicates_removed", 0)
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Missing Values Filled",
                report.get("missing_values_filled", 0)
            )
            col2.metric("Rows Dropped", report.get("rows_dropped", 0))
            col3.metric(
                "Invalid Values Handled",
                report.get("invalid_values_fixed", 0)
            )

            st.subheader("Original Dataset")
            st.dataframe(original_df.head(10), use_container_width=True)

            st.subheader("Cleaned Dataset")
            st.dataframe(cleaned_df.head(10), use_container_width=True)

            st.write(
                "Remaining Missing Values:",
                report.get("remaining_missing_values", {})
            )

            st.download_button(
                "Download Cleaned Dataset",
                data=cleaned_df.to_csv(index=False).encode("utf-8"),
                file_name="cleaned_dataset.csv",
                mime="text/csv"
            )


# ==================================================
# PHASE 4 - SQL ANALYTICS STUDIO
# ==================================================

elif page == "Phase 4 - SQL Analytics":

    st.title("💻 SQL Analytics Studio")
    st.write("Analyse your uploaded dataset using DuckDB SQL.")

    if require_dataset():

        analytics = SQLAnalytics(st.session_state.engine)
        df = get_original_data()

        try:
            st.metric(
                "Total Records",
                f"{analytics.get_row_count():,}"
            )
            st.subheader("Available Columns")
            st.dataframe(analytics.get_columns(), use_container_width=True)
        except Exception as error:
            st.error(f"Could not retrieve SQL information: {error}")

        st.divider()
        st.subheader("Quick Analytics")

        numeric_columns = df.select_dtypes(include="number").columns.tolist()
        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        if numeric_columns:

            aggregation = st.selectbox(
                "Aggregation",
                ["SUM", "AVG", "MIN", "MAX", "COUNT"]
            )

            selected_column = st.selectbox(
                "Numerical Column",
                numeric_columns
            )

            group_column = st.selectbox(
                "Group By (Optional)",
                ["None"] + categorical_columns
            )

            top_n = st.number_input(
                "Number of Results",
                min_value=1,
                max_value=100,
                value=10
            )

            if st.button("Run Quick Analytics"):

                try:
                    quoted_column = (
                        '"' + selected_column.replace('"', '""') + '"'
                    )

                    query = (
                        f"SELECT {aggregation}({quoted_column}) AS result "
                        f"FROM uploaded_data"
                    )

                    if group_column != "None":

                        quoted_group = (
                            '"' + group_column.replace('"', '""') + '"'
                        )

                        query = (
                            f"SELECT {quoted_group}, "
                            f"{aggregation}({quoted_column}) AS result "
                            f"FROM uploaded_data "
                            f"GROUP BY {quoted_group} "
                            f"ORDER BY result DESC "
                            f"LIMIT {int(top_n)}"
                        )

                    st.session_state.sql_result = analytics.execute_query(query)
                    st.success("Quick analytics completed!")

                except Exception as error:
                    st.error(f"Query failed: {error}")

        else:
            st.info("No numerical columns available.")

        st.divider()
        st.subheader("Custom SQL Query")

        query = st.text_area(
            "Write your SQL query",
            value="SELECT * FROM uploaded_data LIMIT 10",
            height=140
        )

        if st.button("Execute SQL Query", type="primary"):

            try:
                st.session_state.sql_result = analytics.execute_query(query)
                st.success("SQL query executed successfully!")
            except Exception as error:
                st.error(f"SQL execution failed: {error}")

        if st.session_state.sql_result is not None:

            st.subheader("Query Results")
            st.dataframe(
                st.session_state.sql_result,
                use_container_width=True
            )

            st.download_button(
                "Download SQL Results",
                data=st.session_state.sql_result.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="sql_results.csv",
                mime="text/csv"
            )


# ==================================================
# PHASE 5 - NATURAL LANGUAGE TO SQL
# ==================================================

elif page == "Phase 5 - Natural Language SQL":

    st.title("🤖 Natural Language to SQL")
    st.write(
        "Ask questions in simple English and let the local AI "
        "generate SQL queries."
    )

    st.info("Requires Ollama and qwen2.5:1.5b.")

    if require_dataset():

        question = st.text_area(
            "Ask a question about your dataset",
            placeholder="Example: What is the total sales amount?"
        )

        if st.button("Generate SQL and Analyse", type="primary"):

            if not question.strip():
                st.warning("Please enter a question.")
            else:
                try:
                    nl_sql = NaturalLanguageSQL(st.session_state.engine)

                    with st.spinner("Generating SQL using local AI..."):
                        generated_sql = nl_sql.generate_sql(question)

                    st.subheader("Generated SQL")
                    st.code(generated_sql, language="sql")

                    analytics = SQLAnalytics(st.session_state.engine)

                    with st.spinner("Executing SQL query..."):
                        result = analytics.execute_query(generated_sql)

                    st.session_state.nl_sql_query = generated_sql
                    st.session_state.nl_sql_result = result

                    st.success("Analysis completed!")
                    st.dataframe(result, use_container_width=True)

                    st.download_button(
                        "Download Results",
                        data=result.to_csv(index=False).encode("utf-8"),
                        file_name="ai_analysis_results.csv",
                        mime="text/csv"
                    )

                except Exception as error:
                    st.error(f"Natural language analysis failed: {error}")

        if st.session_state.nl_sql_query:
            with st.expander("View Previous Generated SQL"):
                st.code(st.session_state.nl_sql_query, language="sql")

            if st.session_state.nl_sql_result is not None:
                st.dataframe(
                    st.session_state.nl_sql_result,
                    use_container_width=True
                )


# ==================================================
# PHASE 6 - VISUALIZATION STUDIO
# ==================================================

elif page == "Phase 6 - Visualization Studio":

    st.title("📈 Smart Visualization Studio")
    st.write("Create interactive charts from your dataset.")

    if require_dataset():

        use_cleaned = st.checkbox(
            "Use cleaned dataset",
            value=False
        )

        viz_df = get_analysis_data(use_cleaned)

        if viz_df is None or viz_df.empty:
            st.warning("No data available.")
        else:

            studio = VisualizationStudio(viz_df)
            numeric_columns = studio.get_numeric_columns()
            categorical_columns = studio.get_categorical_columns()

            chart_type = st.selectbox(
                "Chart Type",
                ["Bar", "Line", "Pie", "Scatter", "Histogram", "Box"]
            )

            x_column = None
            y_column = None
            color_column = None
            aggregation = "Sum"

            if chart_type in ["Bar", "Line", "Pie"]:

                if categorical_columns:
                    x_column = st.selectbox(
                        "Category / X-axis",
                        categorical_columns
                    )

                if numeric_columns:
                    y_column = st.selectbox(
                        "Numerical Y-axis",
                        numeric_columns
                    )

                    aggregation = st.selectbox(
                        "Aggregation",
                        ["Sum", "Average", "Count", "Minimum", "Maximum"]
                    )

            elif chart_type == "Scatter":

                if len(numeric_columns) >= 2:

                    x_column = st.selectbox(
                        "X-axis",
                        numeric_columns,
                        key="scatter_x"
                    )

                    y_options = [
                        col for col in numeric_columns
                        if col != x_column
                    ]

                    y_column = st.selectbox(
                        "Y-axis",
                        y_options,
                        key="scatter_y"
                    )

                    color_column = st.selectbox(
                        "Color Category (Optional)",
                        ["None"] + categorical_columns
                    )

                else:
                    st.warning("Scatter requires two numerical columns.")

            elif chart_type == "Histogram":

                if numeric_columns:
                    x_column = st.selectbox(
                        "Numerical Column",
                        numeric_columns
                    )
                else:
                    st.warning("No numerical columns found.")

            elif chart_type == "Box":

                if numeric_columns:

                    y_column = st.selectbox(
                        "Numerical Column",
                        numeric_columns
                    )

                    x_column = st.selectbox(
                        "Category (Optional)",
                        ["None"] + categorical_columns
                    )

            if st.button("Generate Visualization", type="primary"):

                try:
                    fig = None

                    if chart_type in ["Bar", "Line", "Pie"]:

                        if x_column is not None and y_column is not None:
                            fig = studio.create_chart(
                                chart_type,
                                x=x_column,
                                y=y_column,
                                aggregation=aggregation
                            )

                    elif chart_type == "Scatter":

                        if x_column is not None and y_column is not None:
                            fig = studio.create_chart(
                                chart_type,
                                x=x_column,
                                y=y_column,
                                color=(
                                    None
                                    if color_column in [None, "None"]
                                    else color_column
                                )
                            )

                    elif chart_type == "Histogram":

                        if x_column is not None:
                            fig = studio.create_chart(
                                chart_type,
                                x=x_column
                            )

                    elif chart_type == "Box":

                        if y_column is not None:
                            fig = studio.create_chart(
                                chart_type,
                                x=(
                                    None
                                    if x_column == "None"
                                    else x_column
                                ),
                                y=y_column
                            )

                    if fig is not None:
                        st.session_state.viz_fig = fig
                    else:
                        st.warning("Please select valid chart columns.")

                except Exception as error:
                    st.error(f"Visualization failed: {error}")

            if st.session_state.viz_fig is not None:
                st.subheader("Generated Chart")
                st.plotly_chart(
                    st.session_state.viz_fig,
                    use_container_width=True
                )


# ==================================================
# PHASE 7 - ROOT CAUSE ANALYSIS
# ==================================================

elif page == "Phase 7 - Root Cause Analysis":

    st.title("🔍 Root Cause Analysis Engine")

    st.write(
        "Explore numerical relationships and compare groups "
        "to identify factors associated with a selected metric."
    )

    st.info(
        "Statistical associations do not prove cause and effect."
    )

    if require_dataset():

        use_cleaned = st.checkbox(
            "Use cleaned dataset",
            value=False
        )

        analysis_df = get_analysis_data(use_cleaned)
        analyzer = RootCauseAnalyzer(analysis_df)

        numeric_columns = analyzer.get_numeric_columns()

        if not numeric_columns:
            st.warning("No numerical columns are available.")
        else:

            target_column = st.selectbox(
                "Target Metric",
                numeric_columns
            )

            direction = st.selectbox(
                "Group Comparison Direction",
                ["Both", "High", "Low"]
            )

            min_group_size = st.slider(
                "Minimum Group Size",
                1, 50, 5
            )

            if st.button("Run Root Cause Analysis", type="primary"):

                try:
                    st.session_state.root_cause_result = analyzer.analyze(
                        target_column=target_column,
                        direction=direction,
                        min_group_size=min_group_size
                    )
                    st.success("Analysis completed!")

                except Exception as error:
                    st.error(f"Analysis failed: {error}")

            result = st.session_state.root_cause_result

            if result is not None:

                st.subheader("Target Metric Overview")

                col1, col2, col3 = st.columns(3)

                col1.metric("Mean", f"{result['overall_mean']:,.2f}")
                col2.metric("Median", f"{result['overall_median']:,.2f}")
                col3.metric(
                    "Records",
                    f"{result['row_count']:,}"
                )

                st.subheader("Key Findings")

                for finding in result.get("findings", []):
                    st.info(finding)

                numeric_result = result.get(
                    "numeric_analysis",
                    pd.DataFrame()
                )

                st.subheader("Numerical Relationship Analysis")

                if not numeric_result.empty:

                    st.dataframe(
                        numeric_result,
                        use_container_width=True
                    )

                    if {
                        "feature", "correlation"
                    }.issubset(numeric_result.columns):

                        fig = px.bar(
                            numeric_result,
                            x="feature",
                            y="correlation",
                            title="Numerical Feature Correlations"
                        )

                        st.plotly_chart(fig, use_container_width=True)

                    st.download_button(
                        "Download Numerical Analysis",
                        data=numeric_result.to_csv(
                            index=False
                        ).encode("utf-8"),
                        file_name="numerical_analysis.csv",
                        mime="text/csv"
                    )

                else:
                    st.info("No numerical relationships available.")

                category_result = result.get(
                    "categorical_analysis",
                    pd.DataFrame()
                )

                st.subheader("Categorical Group Comparison")

                if not category_result.empty:

                    st.dataframe(
                        category_result,
                        use_container_width=True
                    )

                    if {
                        "group", "mean"
                    }.issubset(category_result.columns):

                        fig = px.bar(
                            category_result,
                            x="group",
                            y="mean",
                            title="Average Metric by Group"
                        )

                        st.plotly_chart(fig, use_container_width=True)

                    st.download_button(
                        "Download Categorical Analysis",
                        data=category_result.to_csv(
                            index=False
                        ).encode("utf-8"),
                        file_name="categorical_analysis.csv",
                        mime="text/csv"
                    )

                else:
                    st.info("No categorical comparisons available.")


# ==================================================
# PHASE 8 - WHAT-IF SIMULATION
# ==================================================

elif page == "Phase 8 - What-If Simulation":

    st.title("🧪 What-If Simulation Engine")

    st.write(
        "Explore how changing numerical values affects "
        "calculated metrics."
    )

    st.info(
        "This is a numerical scenario simulation, not a "
        "predictive forecasting or causal model."
    )

    if require_dataset():

        use_cleaned = st.checkbox(
            "Use cleaned dataset",
            value=False
        )

        simulation_df = get_analysis_data(use_cleaned)

        if simulation_df is None or simulation_df.empty:
            st.warning("No data available.")
        else:

            simulator = WhatIfSimulator(simulation_df)
            numeric_columns = simulator.get_numeric_columns()

            if not numeric_columns:
                st.warning("No numerical columns available.")
            else:

                column = st.selectbox(
                    "Select Numerical Column",
                    numeric_columns
                )

                change_type = st.selectbox(
                    "Adjustment Type",
                    ["Percentage", "Fixed Value"]
                )

                if change_type == "Percentage":

                    change_value = st.number_input(
                        "Percentage Increase",
                        min_value=0.0,
                        value=10.0,
                        step=1.0
                    )

                else:

                    change_value = st.number_input(
                        "Fixed Amount to Add",
                        value=10.0,
                        step=1.0
                    )

                aggregation = st.selectbox(
                    "Calculation",
                    ["Sum", "Average", "Minimum", "Maximum", "Count"]
                )

                if st.button("Run Simulation", type="primary"):

                    try:
                        simulated_df, report = simulator.simulate(
                            column=column,
                            change_type=change_type,
                            change_value=change_value,
                            aggregation=aggregation
                        )

                        st.session_state.simulated_df = simulated_df
                        st.session_state.simulation_report = report

                        st.success("Simulation completed!")

                    except Exception as error:
                        st.error(f"Simulation failed: {error}")

                report = st.session_state.simulation_report

                if report is not None:

                    st.subheader("Simulation Results")

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Original Value",
                        f"{report['original_value']:,.2f}"
                        if pd.notna(report['original_value'])
                        else "N/A"
                    )

                    col2.metric(
                        "Simulated Value",
                        f"{report['simulated_value']:,.2f}"
                        if pd.notna(report['simulated_value'])
                        else "N/A"
                    )

                    col3.metric(
                        "Difference",
                        f"{report['difference']:,.2f}"
                        if pd.notna(report['difference'])
                        else "N/A",
                        delta=(
                            f"{report['percentage_change']:.2f}%"
                            if report["percentage_change"] is not None
                            else None
                        )
                    )

                    comparison_df = pd.DataFrame({
                        "Scenario": ["Original", "Simulated"],
                        "Value": [
                            report["original_value"],
                            report["simulated_value"]
                        ]
                    })

                    fig = px.bar(
                        comparison_df,
                        x="Scenario",
                        y="Value",
                        title=f"{aggregation} of {column}"
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    st.subheader("Simulated Dataset Preview")

                    simulated_df = st.session_state.simulated_df

                    if simulated_df is not None:

                        st.dataframe(
                            simulated_df.head(20),
                            use_container_width=True
                        )

                        st.download_button(
                            "Download Simulated Dataset",
                            data=simulated_df.to_csv(
                                index=False
                            ).encode("utf-8"),
                            file_name="simulated_dataset.csv",
                            mime="text/csv"
                        )


# ==================================================
# PHASE 9 - AI REPORT GENERATOR
# ==================================================

elif page == "Phase 9 - AI Report Generator":

    st.title("📄 AI Report Generator")

    st.write(
        "Generate a structured analytical report "
        "from your dataset using local GenAI."
    )

    st.info(
        "Requires Ollama and qwen2.5:1.5b."
    )

    if require_dataset():

        use_cleaned = st.checkbox(
            "Generate report using cleaned dataset",
            value=False
        )

        report_df = get_analysis_data(use_cleaned)

        if report_df is None or report_df.empty:
            st.warning("No data is available.")
        else:

            col1, col2 = st.columns(2)

            col1.metric("Dataset Records", f"{len(report_df):,}")
            col2.metric("Dataset Columns", len(report_df.columns))

            st.caption(
                "The AI receives dataset statistics, not every row."
            )

            if st.button("Generate AI Report", type="primary"):

                try:
                    generator = AIReportGenerator()

                    with st.spinner("Generating analytical report..."):

                        summary = generator.create_dataset_summary(
                            report_df
                        )

                        report = generator.generate_report(
                            report_df
                        )

                    st.session_state.ai_report = report
                    st.session_state.ai_report_summary = summary

                    st.success("Report generated successfully!")

                except Exception as error:
                    st.error(f"Report generation failed: {error}")

            report = st.session_state.ai_report

            if report is not None:

                st.subheader("Generated Analytical Report")
                st.markdown(report)

                st.download_button(
                    "Download Report as TXT",
                    data=report,
                    file_name="InsightAI_Analysis_Report.txt",
                    mime="text/plain"
                )

                summary = st.session_state.ai_report_summary

                if summary is not None:

                    st.download_button(
                        "Download Dataset Summary as JSON",
                        data=json.dumps(
                            summary,
                            indent=4,
                            default=str
                        ),
                        file_name="InsightAI_Dataset_Summary.json",
                        mime="application/json"
                    )


# ==================================================
# PHASE 10 - AGENTIC AI DATA ANALYST
# ==================================================

elif page == "Phase 10 - Agentic AI Analyst":

    st.title("🧠 Agentic AI Data Analyst")

    st.write(
        "Ask complex questions about your dataset. "
        "The AI agent can select and execute multiple "
        "approved analysis tools before preparing an answer."
    )

    st.info(
        "Powered by local Ollama and qwen2.5:1.5b. "
        "The agent uses a controlled set of read-only tools."
    )

    if require_dataset():

        st.subheader("Ask Your AI Agent")

        question = st.text_area(
            "Enter your analysis request",
            placeholder=(
                "Example: Analyse my dataset, identify its "
                "data quality issues, and explain the statistics "
                "of the sales column."
            ),
            height=130
        )

        st.caption(
            "The agent can inspect the dataset, calculate "
            "numerical statistics, run data quality checks "
            "and execute approved read-only SQL queries."
        )

        if st.button(
            "Start Agentic Analysis",
            type="primary"
        ):

            if not question.strip():

                st.warning("Please enter a question.")

            else:

                try:

                    agent = AgenticDataAnalyst(
                        db_engine=st.session_state.engine,
                        model="qwen2.5:1.5b",
                        max_steps=4
                    )

                    with st.spinner(
                        "InsightAI agent is planning and analysing..."
                    ):

                        result = agent.analyse(question)

                    st.session_state.agent_result = result

                    st.success(
                        "Agentic analysis completed!"
                        if result["completed"]
                        else "Agent reached its step limit."
                    )

                except Exception as error:

                    st.error(
                        f"Agentic analysis failed: {error}"
                    )

        result = st.session_state.agent_result

        if result is not None:

            st.divider()

            st.subheader("Agent's Final Answer")

            st.markdown(result["answer"])

            st.subheader("Agent Execution History")

            steps = result.get("steps", [])

            if steps:

                for step in steps:

                    with st.expander(
                        f"Step {step['step']} - {step['tool']}"
                    ):

                        st.write(
                            "**Reason:**",
                            step["reason"]
                        )

                        st.write("**Arguments:**")

                        st.json(step["arguments"])

                        st.write("**Tool Result:**")

                        st.json(step["result"])

            else:

                st.info(
                    "The agent answered without calling an analysis tool."
                )

            st.download_button(
                "Download Agent Analysis",
                data=(
                    "INSIGHTAI - AGENTIC ANALYSIS\n\n"
                    + "QUESTION:\n"
                    + question
                    + "\n\nFINAL ANSWER:\n"
                    + result["answer"]
                    + "\n\nEXECUTION HISTORY:\n"
                    + json.dumps(
                        steps,
                        indent=4,
                        default=str
                    )
                ),
                file_name="InsightAI_Agentic_Analysis.txt",
                mime="text/plain"
            )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#64748B;">
        <p><b>InsightAI</b> | Data Intelligence & Decision Support</p>
        <p>Python | Streamlit | Pandas | DuckDB | Plotly | Ollama</p>
        <p>10 Development Phases</p>
    </div>
    """,
    unsafe_allow_html=True
)
