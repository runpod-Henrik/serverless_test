# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RunPod serverless function for detecting flaky tests. It clones a repository, runs a specified test command multiple times in parallel with different seeds, and returns statistics about failure rates.

## Architecture

**Main Components:**
- `worker.py`: RunPod serverless handler that orchestrates the flaky test detection
  - `handler()`: Entry point that receives job configuration via `job["input"]`
  - `run_test_once()`: Executes a single test run with custom environment variables
  - Uses `ThreadPoolExecutor` for parallel test execution

**Job Input Format:**
```json
{
  "repo": "https://github.com/user/repo",
  "test_command": "pytest tests/test_file.py",
  "runs": 50,
  "parallelism": 5
}
```

**Job Output Format:**
Returns a summary with:
- `total_runs`: Number of test executions
- `parallelism`: Parallel worker count
- `failures`: Number of failed runs
- `repro_rate`: Failure rate (0.0 to 1.0)
- `results`: Array of individual run results with exit codes and output

**Test Execution Flow:**
1. Clones the repository into a temporary directory
2. Changes working directory to the cloned repo
3. Spawns parallel workers (via `ThreadPoolExecutor`)
4. Each worker runs the test command with unique `TEST_SEED` and `ATTEMPT` environment variables
5. Collects all results and calculates failure statistics

## Development Commands

**Run tests locally:**
```bash
pytest tests/
```

**Run a specific test:**
```bash
pytest tests/test_flaky.py
```

**Format code:**
```bash
black .
```

**Start the RunPod worker locally:**
```bash
python worker.py
```

**Test with sample input:**
The `test_input.json` file contains example job configuration for testing the handler.

## Dependencies

- Python 3.12+
- `runpod`: Serverless framework integration
- `pytest`: For running test suites
- `black`: Code formatting

Install with:
```bash
pip install -r requirements.txt
```

Or using uv:
```bash
uv sync
```
