import json
import os
import random
import shlex
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal

import runpod

FrameworkType = Literal["python", "go", "typescript-jest", "typescript-vitest", "javascript-mocha", "unknown"]


def detect_framework(repo_path: str) -> FrameworkType:
    """Detect test framework from repository files."""
    # Check for Go
    if os.path.exists(os.path.join(repo_path, "go.mod")):
        return "go"

    # Check for Node.js/TypeScript
    package_json = os.path.join(repo_path, "package.json")
    if os.path.exists(package_json):
        try:
            with open(package_json) as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "jest" in deps:
                    return "typescript-jest"
                elif "vitest" in deps:
                    return "typescript-vitest"
                elif "mocha" in deps:
                    return "javascript-mocha"
        except Exception:
            pass

    # Check for Python
    if os.path.exists(os.path.join(repo_path, "requirements.txt")) or \
       os.path.exists(os.path.join(repo_path, "pyproject.toml")) or \
       os.path.exists(os.path.join(repo_path, "setup.py")):
        return "python"

    return "unknown"


def install_dependencies(framework: FrameworkType, repo_path: str) -> None:
    """Install dependencies based on detected framework."""
    install_commands = {
        "python": ["pip", "install", "-q", "-r", "requirements.txt"],
        "go": ["go", "mod", "download"],
        "typescript-jest": ["npm", "install", "--silent"],
        "typescript-vitest": ["npm", "install", "--silent"],
        "javascript-mocha": ["npm", "install", "--silent"],
    }

    # Check if dependency file exists
    dependency_files = {
        "python": "requirements.txt",
        "go": "go.mod",
        "typescript-jest": "package.json",
        "typescript-vitest": "package.json",
        "javascript-mocha": "package.json",
    }

    if framework not in install_commands:
        print(f"Framework {framework} detected but no dependency installation configured")
        return

    dep_file = dependency_files[framework]
    if not os.path.exists(os.path.join(repo_path, dep_file)):
        print(f"No {dep_file} found, skipping dependency installation")
        return

    try:
        print(f"Installing {framework} dependencies...")
        subprocess.run(
            install_commands[framework],
            check=True,
            capture_output=True,
            timeout=300,
        )
        print(f"✓ Installed {framework} dependencies")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install dependencies: {e.stderr}")
    except subprocess.TimeoutExpired:
        print("Warning: Dependency installation timed out")


def get_seed_env_var(framework: FrameworkType, seed_value: int) -> dict[str, str]:
    """Get appropriate environment variable for seeding tests."""
    seed_vars = {
        "python": {"TEST_SEED": str(seed_value)},
        "go": {"GO_TEST_SEED": str(seed_value)},
        "typescript-jest": {"JEST_SEED": str(seed_value)},
        "typescript-vitest": {"VITE_TEST_SEED": str(seed_value)},
        "javascript-mocha": {"MOCHA_SEED": str(seed_value)},
        "unknown": {"TEST_SEED": str(seed_value)},  # Fallback
    }
    return seed_vars.get(framework, {"TEST_SEED": str(seed_value)})


def run_test_once(
    cmd_list: list[str], env_overrides: dict[str, str], attempt: int
) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(env_overrides)
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, env=env, timeout=300)
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


def handler(job: dict[str, Any]) -> dict[str, Any]:
    """
    Expected input:
    {
      "repo": "https://github.com/runpod-Henrik/serverless_test",
      "test_command": "pytest tests/test_flaky.py",
      "runs": 50,
      "parallelism": 5,
      "framework": "python"  # Optional: auto-detect if not provided
    }
    """
    inp = job["input"]
    repo = inp["repo"]
    test_command = inp["test_command"]
    runs = int(inp.get("runs", 10))
    parallelism = int(inp.get("parallelism", 4))
    framework_override = inp.get("framework")  # Optional explicit framework

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
    detected_framework: FrameworkType = "unknown"

    try:
        # Clone repo - using list arguments to prevent command injection
        try:
            print(f"Cloning repository: {repo}")
            subprocess.run(
                ["git", "clone", repo, workdir],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            print("✓ Repository cloned successfully")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("Repository clone timed out after 5 minutes") from e

        os.chdir(workdir)

        # Detect or use explicit framework
        if framework_override:
            # User provided explicit framework
            if framework_override in ("python", "go", "typescript-jest", "typescript-vitest", "javascript-mocha"):
                detected_framework = framework_override
            else:
                detected_framework = "unknown"
            print(f"Using explicit framework: {detected_framework}")
        else:
            detected_framework = detect_framework(workdir)
            print(f"Detected framework: {detected_framework}")

        # Install dependencies
        install_dependencies(detected_framework, workdir)

        # Parse test command safely
        test_command_list = shlex.split(test_command)

        print(f"Running {runs} tests with parallelism {parallelism}...")

        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            futures = []
            for i in range(runs):
                seed = random.randint(1, 1_000_000)
                env_overrides = get_seed_env_var(detected_framework, seed)
                env_overrides["ATTEMPT"] = str(i)
                futures.append(executor.submit(run_test_once, test_command_list, env_overrides, i))
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    # Handle exceptions from worker threads
                    results.append(
                        {
                            "attempt": len(results),
                            "exit_code": None,
                            "stdout": "",
                            "stderr": f"WORKER ERROR: {str(e)}",
                            "passed": False,
                        }
                    )

        print("✓ Completed all test runs")

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
        "framework": detected_framework,
        "failures": len(failures),
        "repro_rate": round(len(failures) / runs, 3),
        "results": sorted(results, key=lambda r: r["attempt"]),
    }
    return summary


runpod.serverless.start({"handler": handler})
