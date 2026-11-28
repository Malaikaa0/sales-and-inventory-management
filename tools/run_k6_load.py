"""
Wrapper to run `k6 run tests/team/perf/load_test.js` against an isolated seeded
InventoryMS server and save summary evidence under `reports/perf/`.
"""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports" / "perf"


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    k6_exe = shutil.which("k6") or r"C:\Program Files\k6\k6.exe"
    if not Path(k6_exe).exists():
        raise RuntimeError("k6 binary not found")

    tmp_dir = Path(tempfile.mkdtemp(prefix="k6_db_"))
    db_path = tmp_dir / "k6.sqlite3"
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["DEBUG"] = "True"
    env["LOGIN_MAX_ATTEMPTS"] = "1000"
    env["SQLITE_PATH"] = str(db_path)

    py = sys.executable
    subprocess.run([py, "manage.py", "migrate", "--noinput"], cwd=BASE_DIR, env=env, check=True)
    subprocess.run([py, "manage.py", "seed_demo"], cwd=BASE_DIR, env=env, check=True)

    # Ensure target item has ample stock so load iterations don't deplete it
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE store_item SET quantity = 5000 WHERE quantity > 0")
    conn.commit()
    conn.close()

    proc = subprocess.Popen(
        [py, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    break
            except OSError:
                time.sleep(0.25)

        summary_json = REPORTS_DIR / "k6-summary.json"
        output_txt = REPORTS_DIR / "k6-output.txt"
        res = subprocess.run(
            [
                k6_exe,
                "run",
                "--env",
                f"BASE_URL={base_url}",
                "--summary-export",
                str(summary_json),
                str(BASE_DIR / "tests" / "team" / "perf" / "load_test.js"),
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        output_txt.write_text((res.stdout or "") + "\n" + (res.stderr or ""), encoding="utf-8")
        print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        sys.exit(res.returncode)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
