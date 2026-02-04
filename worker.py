import os
import subprocess
import tempfile
import shlex
import shutil
import random
import runpod
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_test_once(cmd_list, env_overrides, attempt):
    env = os.environ.copy()
    env.update(env_overrides)
    try:
        result = subprocess.run(
            cmd_list, capture_output=True, text=True, env=env, timeout=300
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
    except Exception as e:
        return {
            "attempt": attempt,
            "exit_code": None,
            "stdout": "",
            "stderr": f"ERROR: {str(e)}",
            "passed": False,
        }


def handler(job):
    """
    Expected input:
    {
      "repo": "https://github.com/runpod-Henrik/serverless_test",
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

    # Validate input parameters
    if not repo:
        raise ValueError("Repository URL is required")
    if not test_command:
        raise ValueError("Test command is required")
    if runs < 1 or runs > 1000:
        raise ValueError("Runs must be between 1 and 1000")
    if parallelism < 1 or parallelism > 50:
        raise ValueError("Parallelism must be between 1 and 50")

    # Validate repo URL (basic check for https:// or git@)
    if not (repo.startswith("https://") or repo.startswith("git@")):
        raise ValueError(f"Invalid repository URL: {repo}")

    workdir = tempfile.mkdtemp()
    results = []
    original_cwd = os.getcwd()

    try:
        # Clone repo - using list arguments to prevent command injection
        try:
            subprocess.run(
                ["git", "clone", repo, workdir],
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Repository clone timed out after 5 minutes")

        os.chdir(workdir)

        # Install dependencies if requirements.txt exists
        if os.path.exists("requirements.txt"):
            try:
                subprocess.run(
                    ["pip", "install", "-q", "-r", "requirements.txt"],
                    check=True,
                    capture_output=True,
                    timeout=300
                )
            except subprocess.CalledProcessError as e:
                # Log but don't fail - some tests might not need all dependencies
                print(f"Warning: Failed to install dependencies: {e.stderr}")

        # Parse test command safely
        test_command_list = shlex.split(test_command)

        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            futures = []
            for i in range(runs):
                env_overrides = {
                    "TEST_SEED": str(random.randint(1, 1_000_000)),
                    "ATTEMPT": str(i),
                }
                futures.append(
                    executor.submit(run_test_once, test_command_list, env_overrides, i)
                )
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    # Handle exceptions from worker threads
                    results.append({
                        "attempt": len(results),
                        "exit_code": None,
                        "stdout": "",
                        "stderr": f"WORKER ERROR: {str(e)}",
                        "passed": False,
                    })
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Clean up temporary directory
        try:
            shutil.rmtree(workdir)
        except Exception as e:
            print(f"Warning: Failed to clean up temporary directory: {e}")
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
