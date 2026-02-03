import os
import subprocess
import tempfile
import json
import random
import runpod
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_test_once(cmd, env_overrides, attempt):
    env = os.environ.copy()
    env.update(env_overrides)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, env=env, timeout=300
        )
        return {
            "attempt": attempt,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "attempt": attempt,
            "exit_code": None,
            "stdout": "",
            "stderr": "TIMEOUT",
            "passed": False,
        }


def handler(job):
    """
    Expected input:
    {
      "repo": "https://github.com/org/project.git",
      "test_command": "pytest tests/test_flaky.py",
      "runs": 50,
      "parallelism": 5
    }
    """
    inp = job["input"]
    repo = inp["repo"]
    test_command = inp["test_command"]
    runs = int(inp.get("runs", 10))
    parallelism = int(inp.get("parallelism", 4))
    workdir = tempfile.mkdtemp()
    results = []
    # Clone repo
    subprocess.run(f"git clone {repo} {workdir}", shell=True, check=True)
    os.chdir(workdir)
    with ThreadPoolExecutor(max_workers=parallelism) as executor:
        futures = []
        for i in range(runs):
            env_overrides = {
                "TEST_SEED": str(random.randint(1, 1_000_000)),
                "ATTEMPT": str(i),
            }
            futures.append(
                executor.submit(run_test_once, test_command, env_overrides, i)
            )
        for future in as_completed(futures):
            results.append(future.result())
    failures = [r for r in results if not r["passed"]]
    summary = {
        "total_runs": runs,
        "parallelism": parallelism,
        "failures": len(failures),
        "repro_rate": round(len(failures) / runs, 3),
        "results": sorted(results, key=lambda r: r["attempt"]),
    }
    return summary


runpod.serverless.start({"handler": handler})
