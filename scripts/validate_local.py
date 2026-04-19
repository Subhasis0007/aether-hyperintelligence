from __future__ import annotations

import argparse
import py_compile
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOLUTION_FILE = REPO_ROOT / "aether-hyperintelligence.sln"
SDK_PYTHON_DIR = REPO_ROOT / "sdk" / "python"
SDK_FILES = [
    SDK_PYTHON_DIR / "aether_sdk" / "client.py",
    SDK_PYTHON_DIR / "aether_sdk" / "models.py",
    SDK_PYTHON_DIR / "aether_sdk" / "__init__.py",
]


@dataclass(frozen=True)
class ValidationStep:
    name: str
    status: str


def _run_command(command: list[str], cwd: Path) -> None:
    print("")
    print(f"$ {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def _python_executable() -> str:
    return sys.executable or "python"


def _validate_dotnet() -> None:
    if shutil.which("dotnet") is None:
        raise RuntimeError("dotnet is not installed or is not available on PATH.")

    if not SOLUTION_FILE.exists():
        raise RuntimeError(f"Solution file not found: {SOLUTION_FILE}")

    print("\n[dotnet] Restoring solution")
    _run_command(["dotnet", "restore", SOLUTION_FILE.name], REPO_ROOT)

    print("\n[dotnet] Building solution with warnings as errors")
    _run_command(["dotnet", "build", SOLUTION_FILE.name, "--no-restore", "/warnaserror"], REPO_ROOT)

    print("\n[dotnet] Running tests")
    _run_command(["dotnet", "test", SOLUTION_FILE.name, "--no-build"], REPO_ROOT)


def _validate_python_sdk() -> None:
    python_executable = _python_executable()

    if not SDK_PYTHON_DIR.exists():
        raise RuntimeError(f"Python SDK directory not found: {SDK_PYTHON_DIR}")

    print("\n[python-sdk] Checking Python")
    _run_command([python_executable, "--version"], SDK_PYTHON_DIR)

    print("\n[python-sdk] Installing SDK in editable mode")
    _run_command([python_executable, "-m", "pip", "install", "-e", "."], SDK_PYTHON_DIR)

    print("\n[python-sdk] Compiling SDK sources")
    for sdk_file in SDK_FILES:
        py_compile.compile(str(sdk_file), doraise=True)
        print(f"compiled {sdk_file.relative_to(REPO_ROOT)}")

    print("\n[python-sdk] Compiling test files")
    for test_file in sorted((SDK_PYTHON_DIR / "tests").glob("test_*.py")):
        py_compile.compile(str(test_file), doraise=True)
        print(f"compiled {test_file.relative_to(REPO_ROOT)}")

    print("\n[python-sdk] Running unittest suite")
    _run_command([python_executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], SDK_PYTHON_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the AETHER local developer baseline.")
    parser.add_argument("--skip-dotnet", action="store_true", help="Skip .NET restore, build, and test validation.")
    parser.add_argument("--skip-python-sdk", action="store_true", help="Skip Python SDK validation.")
    args = parser.parse_args()

    steps: list[ValidationStep] = []

    print("AETHER local validation")
    print(f"Repository root: {REPO_ROOT}")

    try:
        if not args.skip_dotnet:
            _validate_dotnet()
            steps.append(ValidationStep("dotnet solution", "passed"))

        if not args.skip_python_sdk:
            _validate_python_sdk()
            steps.append(ValidationStep("python sdk", "passed"))
    except (RuntimeError, subprocess.CalledProcessError, py_compile.PyCompileError) as exc:
        print("")
        print(f"[FAIL] {exc}")
        return 1

    print("")
    print("Validation summary")
    for step in steps:
        print(f"- {step.name}: {step.status}")

    if not steps:
        print("- no validation steps were selected")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
