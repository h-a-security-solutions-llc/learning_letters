"""Script functions for linting, testing, and coverage."""

import subprocess  # nosec
import sys


def run_lint_all() -> None:
    """
    Run linters for black, isort, flake8, pylint, mypy, and bandit.
    Returns non-zero exit code if any linter fails.
    """
    failed = False

    # Auto-fix formatters (black and isort) - these modify files
    print("Running black...")
    subprocess.run(["black", "app", "tests"], check=False)  # nosec

    print("Running isort...")
    subprocess.run(["isort", "app", "tests"], check=False)  # nosec

    # flake8
    print("Running flake8...")
    result = subprocess.run(["flake8", "app", "tests"], check=False)  # nosec
    if result.returncode != 0:
        failed = True

    # pylint
    print("Running pylint...")
    result = subprocess.run(["pylint", "app"], check=False)  # nosec
    if result.returncode != 0:
        failed = True

    # mypy
    print("Running mypy...")
    result = subprocess.run(["mypy", "app"], check=False)  # nosec
    if result.returncode != 0:
        failed = True

    # bandit
    print("Running bandit...")
    result = subprocess.run(["bandit", "-c", "bandit.yml", "-r", "app"], check=False)  # nosec
    if result.returncode != 0:
        failed = True

    if failed:
        print("\n❌ Some linting checks failed!")
        sys.exit(1)
    else:
        print("\n✅ All linting checks passed!")


def run_lint() -> None:
    """
    Run linters for black, isort, flake8, pylint, mypy, and bandit on modified git files.
    """
    # Get modified files
    result = subprocess.run(  # nosec
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )

    file_list = result.stdout.strip().split("\n")
    file_list = [f for f in file_list if f and f != "pyproject.toml"]

    if not file_list:
        print("No modified files detected.")
        return

    # Filter Python files only
    python_files = [f for f in file_list if f.endswith(".py")]

    if python_files:
        print(f"Linting {len(python_files)} modified Python file(s)...")
        subprocess.run(["black", *python_files], check=False)  # nosec
        subprocess.run(["isort", *python_files], check=False)  # nosec
        subprocess.run(["flake8", *python_files], check=False)  # nosec
        subprocess.run(["pylint", *python_files], check=False)  # nosec

        # Filter app files for mypy and bandit
        app_files = [f for f in python_files if f.startswith("app/")]
        if app_files:
            subprocess.run(["mypy", *app_files], check=False)  # nosec
            subprocess.run(["bandit", "-c", "bandit.yml", *app_files], check=False)  # nosec


def run_tests() -> None:
    """Run pytest against tests in the `tests` directory."""
    subprocess.run(["pytest", "tests"], check=True)  # nosec


def run_coverage() -> None:
    """
    Run coverage against all files in the `app` directory
    and output reports.
    """
    # 1. Run pytest with coverage
    subprocess.run(  # nosec
        [
            "coverage",
            "run",
            "-m",
            "pytest",
            "tests",
        ],
        check=True,
    )

    # 2. Generate coverage report to terminal
    subprocess.run(["coverage", "report"], check=True)  # nosec

    # 3. Generate HTML coverage report
    subprocess.run(["coverage", "html"], check=True)  # nosec

    print("\nCoverage completed. HTML report generated in htmlcov/")
