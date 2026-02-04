# Historical Tracking Guide

## Overview

The flaky test detector now includes historical tracking to analyze test flakiness trends over time. This helps you:

- **Track improvements**: See if flakiness is decreasing over time
- **Identify problem tests**: Find which tests are consistently flaky
- **Make data-driven decisions**: Use trends to prioritize fixes
- **Monitor team progress**: Visualize test suite health

## Quick Start

### 1. Start the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### 2. View Your Data

The dashboard automatically displays:
- Overview metrics (total runs, failures, avg flaky rate)
- Severity distribution chart
- Flakiness trend over time
- Most flaky test commands
- Recent test runs table

## How It Works

### Data Collection

Every time the flaky test detector runs, it saves results to a SQLite database (`flaky_test_history.db`):

```python
from database import ResultsDatabase

db = ResultsDatabase()
run_id = db.save_run(
    repository="your-org/your-repo",
    test_command="pytest tests/",
    total_runs=100,
    parallelism=10,
    failures=23,
    repro_rate=0.23,
    severity="MEDIUM",
    results=[...],  # Individual test results
    pr_number=123,
    branch="feature/new-thing",
    commit_sha="abc123..."
)
```

### Database Schema

**test_runs table:**
- `id`: Unique run identifier
- `timestamp`: When the run occurred
- `repository`: GitHub repository
- `test_command`: Command executed
- `total_runs`: Number of test executions
- `parallelism`: Workers used
- `failures`: Number of failed runs
- `repro_rate`: Failure rate (0.0-1.0)
- `severity`: Classification (CRITICAL/HIGH/MEDIUM/LOW/NONE)
- `duration_seconds`: How long it took
- `pr_number`: Associated PR
- `branch`: Git branch
- `commit_sha`: Git commit

**test_results table:**
- `id`: Unique result identifier
- `run_id`: Links to test_runs
- `attempt`: Test attempt number
- `exit_code`: Process exit code
- `passed`: Boolean pass/fail
- `stdout`: Test output
- `stderr`: Error output

## Dashboard Features

### 📊 Overview Metrics

Shows at-a-glance statistics:
- Total test runs executed
- Total individual tests run
- Total failures detected
- Average flaky rate across all runs
- Count of critical and high severity runs

### 🎯 Severity Distribution

Bar chart showing breakdown of runs by severity:
- 🔴 CRITICAL (>90% failure)
- 🟠 HIGH (50-90% failure)
- 🟡 MEDIUM (10-50% failure)
- 🟢 LOW (1-10% failure)
- ✅ NONE (0% failure)

### 📈 Flakiness Trend

Line chart showing average flakiness over time:
- Daily aggregation of failure rates
- Helps identify if problems are improving or worsening
- Filter by repository and time period

### 🔥 Most Flaky Test Commands

Table showing which tests fail most often:
- Test command
- Number of times run
- Average failure rate
- Maximum failure rate recorded
- Last run timestamp

### 📋 Recent Test Runs

Detailed table of recent executions:
- Timestamp
- Repository
- Test command
- Number of runs
- Failures
- Flaky rate percentage
- Severity with emoji indicator

## Filtering Data

Use the sidebar to filter data:

**Repository Filter:**
- Select "All" to see aggregate data
- Select specific repository to see just that repo

**Time Period:**
- Slider from 7 to 90 days
- Affects all charts and tables

## Using the Database Programmatically

### Query Recent Runs

```python
from database import ResultsDatabase

db = ResultsDatabase()

# Get last 50 runs
runs = db.get_recent_runs(limit=50)

# Get runs for specific repo
repo_runs = db.get_runs_by_repository("your-org/your-repo", limit=100)

# Get specific run details
run_details = db.get_run_details(run_id=42)
```

### Analyze Trends

```python
# Get 30-day flakiness trend
trend = db.get_flakiness_trend("your-org/your-repo", days=30)

# Get most flaky tests
flaky_tests = db.get_most_flaky_commands("your-org/your-repo", limit=10)

# Get overall statistics
stats = db.get_statistics(repository="your-org/your-repo")
```

### Custom Queries

```python
import sqlite3

conn = sqlite3.connect("flaky_test_history.db")
cursor = conn.cursor()

# Custom query example: Get all runs from last week with >50% failure rate
cursor.execute("""
    SELECT repository, test_command, repro_rate, timestamp
    FROM test_runs
    WHERE timestamp >= datetime('now', '-7 days')
    AND repro_rate > 0.5
    ORDER BY repro_rate DESC
""")

results = cursor.fetchall()
conn.close()
```

## Automatic Data Collection

To automatically save results, integrate with your worker or test scripts:

```python
# In worker.py or local_test.py
from database import ResultsDatabase
import time

start_time = time.time()

# ... run tests ...

duration = time.time() - start_time

# Save results
db = ResultsDatabase()
db.save_run(
    repository=repository,
    test_command=test_command,
    total_runs=len(results),
    parallelism=parallelism,
    failures=len([r for r in results if not r["passed"]]),
    repro_rate=repro_rate,
    severity=severity,
    results=results,
    duration_seconds=duration,
    pr_number=pr_number,  # Optional
    branch=branch,        # Optional
    commit_sha=commit_sha # Optional
)
```

## Data Export

### Export to CSV

```python
import pandas as pd
from database import ResultsDatabase

db = ResultsDatabase()
runs = db.get_recent_runs(limit=1000)

df = pd.DataFrame(runs)
df.to_csv("test_runs_export.csv", index=False)
```

### Export to JSON

```python
import json
from database import ResultsDatabase

db = ResultsDatabase()
runs = db.get_recent_runs(limit=1000)

with open("test_runs_export.json", "w") as f:
    json.dump(runs, f, indent=2, default=str)
```

## Dashboard Customization

The dashboard is built with Streamlit and can be easily customized:

### Add New Charts

Edit `dashboard.py` and add your own visualizations:

```python
import plotly.express as px

# Example: Scatter plot of runs vs failures
fig = px.scatter(
    df_runs,
    x="total_runs",
    y="failures",
    color="severity",
    title="Runs vs Failures"
)
st.plotly_chart(fig, use_container_width=True)
```

### Add Filters

```python
# Add test command filter
test_commands = df_runs["test_command"].unique()
selected_command = st.sidebar.selectbox("Test Command", ["All"] + list(test_commands))
```

### Add Custom Metrics

```python
# Calculate and display custom metrics
avg_duration = df_runs["duration_seconds"].mean()
st.metric("Avg Duration", f"{avg_duration:.1f}s")
```

## Best Practices

1. **Run the dashboard regularly**: Check trends weekly or after significant changes
2. **Set up alerts**: Monitor for increases in flakiness
3. **Track progress**: Use trends to validate that fixes are working
4. **Share with team**: Use dashboard URLs to discuss flaky tests in meetings
5. **Clean old data**: Periodically archive or delete very old runs

## Database Maintenance

### Backup Database

```bash
cp flaky_test_history.db flaky_test_history_backup_$(date +%Y%m%d).db
```

### Clear Old Data

```python
from database import ResultsDatabase
import sqlite3

conn = sqlite3.connect("flaky_test_history.db")
cursor = conn.cursor()

# Delete runs older than 90 days
cursor.execute("""
    DELETE FROM test_runs
    WHERE timestamp < datetime('now', '-90 days')
""")

# Delete orphaned test results
cursor.execute("""
    DELETE FROM test_results
    WHERE run_id NOT IN (SELECT id FROM test_runs)
""")

conn.commit()
conn.close()
```

### Vacuum Database

```bash
sqlite3 flaky_test_history.db "VACUUM;"
```

## Troubleshooting

### Dashboard won't start

```bash
# Install missing dependencies
pip install streamlit plotly pandas

# Check if port 8501 is available
lsof -i :8501

# Try a different port
streamlit run dashboard.py --server.port 8502
```

### No data showing

- Run some tests first to populate the database
- Check that `flaky_test_history.db` exists
- Verify database has tables: `sqlite3 flaky_test_history.db ".tables"`

### Database locked error

- Close other connections to the database
- Make sure only one process is writing at a time
- Use `with ResultsDatabase() as db:` for proper connection handling

## Integration with CI/CD

To automatically collect data from CI runs, add to your workflow:

```yaml
- name: Save results to database
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    python scripts/save_results.py \
      --results flaky_test_results.json \
      --repository ${{ github.repository }} \
      --pr ${{ github.event.pull_request.number }} \
      --branch ${{ github.head_ref }} \
      --commit ${{ github.sha }}
```

## Future Enhancements

Potential additions to the tracking system:
- Email alerts for severe flakiness
- Slack integration for dashboard summaries
- API for programmatic access
- Comparison mode (compare two time periods)
- Test-specific drill-down pages
- Export to Grafana/Prometheus

## Support

For questions about historical tracking:
- Check this guide first
- Review `database.py` for available queries
- Look at `dashboard.py` for customization examples
- Open an issue on GitHub
