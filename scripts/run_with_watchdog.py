# Run tests under a faulthandler watchdog so real stalls show a traceback.
import faulthandler
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))

targets = sys.argv[1:-1] if len(sys.argv) > 2 else ["backend/tests"]
timeout = int(sys.argv[-1]) if len(sys.argv) > 2 else 120

if not targets:
    sys.exit("usage: run_with_watchdog.py <pytest targets...> <timeout-seconds>")


def watchdog():
    import time

    time.sleep(timeout)
    sys.stderr.write(f"\n===== WATCHDOG: still running after {timeout}s =====\n")
    sys.stderr.flush()
    faulthandler.dump_traceback()
    os._exit(3)


threading.Thread(target=watchdog, daemon=True).start()

import pytest  # noqa: E402

report = os.path.join(HERE, "..", "pytest-report.xml")
try:
    code = pytest.main(
        [
            *targets,
            "-q",
            "-p",
            "no:cacheprovider",
            "--no-header",
            "--tb=short",
            "-rf",
            f"--junit-xml={report}",
        ]
    )
except BaseException as exc:  # noqa: BLE001 - diagnostics only
    import traceback

    traceback.print_exc()
    code = 99

sys.stdout.flush()
sys.stderr.flush()
# APScheduler keeps non-daemon worker threads alive, so leave explicitly.
os._exit(int(code))
