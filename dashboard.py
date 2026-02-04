"""
Streamlit dashboard for viewing flaky test history.
Run with: streamlit run dashboard.py
"""
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database import ResultsDatabase

# Page config
st.set_page_config(
    page_title="Flaky Test Detector Dashboard",
    page_icon="🔍",
    layout="wide",
)

# Initialize database
@st.cache_resource
def get_db():
    return ResultsDatabase()


db = get_db()

# Header
st.title("🔍 Flaky Test Detector Dashboard")
st.markdown("**Track and analyze flaky test patterns over time**")

# Sidebar
st.sidebar.header("Filters")

# Get unique repositories
recent_runs = db.get_recent_runs(limit=1000)
repositories = sorted(list(set(run["repository"] for run in recent_runs)))

if not repositories:
    st.warning("No test runs recorded yet. Run some tests to see data here!")
    st.stop()

selected_repo = st.sidebar.selectbox("Repository", ["All"] + repositories)
days_back = st.sidebar.slider("Days of history", 7, 90, 30)

# Filter data
if selected_repo == "All":
    filtered_runs = recent_runs
    repo_filter = None
else:
    filtered_runs = [r for r in recent_runs if r["repository"] == selected_repo]
    repo_filter = selected_repo

# Calculate date filter
cutoff_date = datetime.now() - timedelta(days=days_back)
filtered_runs = [
    r
    for r in filtered_runs
    if datetime.fromisoformat(r["timestamp"]) > cutoff_date
]

# Overview metrics
st.header("📊 Overview")

stats = db.get_statistics(repository=repo_filter)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Runs", stats["total_runs"])

with col2:
    st.metric("Total Tests", f"{stats['total_tests']:,}")

with col3:
    st.metric("Total Failures", f"{stats['total_failures']:,}")

with col4:
    avg_rate = stats["avg_repro_rate"] or 0
    st.metric("Avg Flaky Rate", f"{avg_rate*100:.1f}%")

with col5:
    critical = stats["critical_runs"] or 0
    high = stats["high_runs"] or 0
    st.metric("🔴 Critical + High", critical + high)

# Severity distribution
st.header("🎯 Severity Distribution")

severity_data = {
    "Severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"],
    "Count": [
        stats["critical_runs"] or 0,
        stats["high_runs"] or 0,
        stats["medium_runs"] or 0,
        stats["low_runs"] or 0,
        stats["none_runs"] or 0,
    ],
    "Color": ["#ff0000", "#ff9500", "#ffcc00", "#00ff00", "#00ff00"],
}

fig_severity = px.bar(
    severity_data,
    x="Severity",
    y="Count",
    color="Severity",
    color_discrete_map={
        "CRITICAL": "#ff0000",
        "HIGH": "#ff9500",
        "MEDIUM": "#ffcc00",
        "LOW": "#00ff00",
        "NONE": "#00ff00",
    },
)
fig_severity.update_layout(showlegend=False)
st.plotly_chart(fig_severity, use_container_width=True)

# Flakiness over time
st.header("📈 Flakiness Trend")

if repo_filter:
    trend_data = db.get_flakiness_trend(repo_filter, days=days_back)
else:
    # Aggregate across all repos
    trend_data = []
    for repo in repositories:
        repo_trend = db.get_flakiness_trend(repo, days=days_back)
        trend_data.extend(repo_trend)

if trend_data:
    df_trend = pd.DataFrame(trend_data)
    df_trend["date"] = pd.to_datetime(df_trend["date"])

    # Group by date if multiple repos
    if not repo_filter:
        df_trend = (
            df_trend.groupby("date")
            .agg(
                {
                    "avg_repro_rate": "mean",
                    "num_runs": "sum",
                    "flaky_runs": "sum",
                }
            )
            .reset_index()
        )

    fig_trend = go.Figure()

    fig_trend.add_trace(
        go.Scatter(
            x=df_trend["date"],
            y=df_trend["avg_repro_rate"] * 100,
            mode="lines+markers",
            name="Avg Flaky Rate (%)",
            line=dict(color="#ff9500", width=2),
        )
    )

    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Average Flaky Rate (%)",
        hovermode="x unified",
    )

    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No trend data available for selected period")

# Most flaky tests
st.header("🔥 Most Flaky Test Commands")

if repo_filter:
    flaky_commands = db.get_most_flaky_commands(repo_filter, limit=10)

    if flaky_commands:
        df_flaky = pd.DataFrame(flaky_commands)
        df_flaky["avg_repro_rate"] = (df_flaky["avg_repro_rate"] * 100).round(1)
        df_flaky["max_repro_rate"] = (df_flaky["max_repro_rate"] * 100).round(1)

        st.dataframe(
            df_flaky[
                ["test_command", "run_count", "avg_repro_rate", "max_repro_rate"]
            ].rename(
                columns={
                    "test_command": "Test Command",
                    "run_count": "Runs",
                    "avg_repro_rate": "Avg Flaky Rate (%)",
                    "max_repro_rate": "Max Flaky Rate (%)",
                }
            ),
            use_container_width=True,
        )
    else:
        st.info("No flaky tests found")
else:
    st.info("Select a specific repository to see flaky test commands")

# Recent runs
st.header("📋 Recent Test Runs")

if filtered_runs:
    df_runs = pd.DataFrame(filtered_runs[:50])

    # Format columns
    df_runs["timestamp"] = pd.to_datetime(df_runs["timestamp"]).dt.strftime(
        "%Y-%m-%d %H:%M"
    )
    df_runs["repro_rate"] = (df_runs["repro_rate"] * 100).round(1)

    # Add emoji to severity
    severity_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "NONE": "✅",
    }
    df_runs["severity"] = df_runs["severity"].apply(
        lambda x: f"{severity_emoji.get(x, '')} {x}"
    )

    st.dataframe(
        df_runs[
            [
                "timestamp",
                "repository",
                "test_command",
                "total_runs",
                "failures",
                "repro_rate",
                "severity",
            ]
        ].rename(
            columns={
                "timestamp": "Timestamp",
                "repository": "Repository",
                "test_command": "Test Command",
                "total_runs": "Runs",
                "failures": "Failures",
                "repro_rate": "Flaky Rate (%)",
                "severity": "Severity",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No runs found for selected filters")

# Footer
st.markdown("---")
st.markdown("🤖 **Flaky Test Detector** | Powered by RunPod")
