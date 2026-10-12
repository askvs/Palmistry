#!/usr/bin/env python3
# Master verification: backend tests, frontend lint, and production build.
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def get_python_executable():
    venv_win = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    venv_unix = ROOT_DIR / ".venv" / "bin" / "python"
    if venv_win.exists():
        return str(venv_win)
    if venv_unix.exists():
        return str(venv_unix)
    return sys.executable


def get_npm_executable():
    return "npm.cmd" if os.name == "nt" else "npm"


def run_step(title, cmd, cwd):
    print(f"\n{'='*70}")
    print(f">> RUNNING: {title}")
    print(f"   Command : {' '.join(cmd)}")
    print(f"   Workdir : {cwd}")
    print(f"{'='*70}\n")
    start = time.time()
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), check=False)
        duration = round(time.time() - start, 2)
        if proc.returncode == 0:
            print(f"\n[PASS] {title} succeeded in {duration}s")
            return True, duration
        else:
            print(f"\n[FAIL] {title} failed with exit code {proc.returncode} in {duration}s")
            return False, duration
    except Exception as exc:
        duration = round(time.time() - start, 2)
        print(f"\n[ERROR] {title} encountered an error: {exc}")
        return False, duration


def main():
    print(f"Palmistry & Tarot Platform — Master Verification Suite")
    print(f"Repository Root: {ROOT_DIR}")

    python_exec = get_python_executable()
    npm_exec = get_npm_executable()

    steps = [
        ("Backend Tests (pytest)", [python_exec, "-m", "pytest", "tests"], BACKEND_DIR),
        ("Frontend Lint (eslint)", [npm_exec, "run", "lint"], FRONTEND_DIR),
        ("Frontend Build (next build)", [npm_exec, "run", "build"], FRONTEND_DIR),
    ]

    results = []
    all_passed = True

    for title, cmd, cwd in steps:
        passed, duration = run_step(title, cmd, cwd)
        results.append((title, passed, duration))
        if not passed:
            all_passed = False

    print("\n" + "#" * 70)
    print("VERIFICATION SUMMARY")
    print("#" * 70)
    for title, passed, duration in results:
        status = "PASSED" if passed else "FAILED"
        mark = "PASS" if passed else "FAIL"
        print(f"  [{mark:^4}] {title:<32} : {status:<8} ({duration}s)")
    print("#" * 70)

    if all_passed:
        print("\nAll checks PASSED! Platform is healthy and ready for next task.\n")
        sys.exit(0)
    else:
        print("\nSome checks FAILED! Please fix the reported issues before proceeding.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
