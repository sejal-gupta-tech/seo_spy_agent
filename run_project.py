#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUIREMENTS_FILE = ROOT / "requirements.txt"
DEFAULT_VENV_NAME = "venv"
ALT_VENV_NAME = ".venv"
STAMP_FILE_NAME = ".requirements.sha256"


def log(message: str) -> None:
    print(f"[bootstrap] {message}")


def detect_venv_dir() -> Path:
    for candidate in (ROOT / DEFAULT_VENV_NAME, ROOT / ALT_VENV_NAME):
        if candidate.exists():
            return candidate
    return ROOT / DEFAULT_VENV_NAME


def venv_python(venv_dir: Path) -> Path:
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def requirements_hash() -> str:
    return hashlib.sha256(REQUIREMENTS_FILE.read_bytes()).hexdigest()


def read_stamp(stamp_path: Path) -> str:
    if not stamp_path.exists():
        return ""
    return stamp_path.read_text(encoding="utf-8").strip()


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> None:
    log("Running: " + " ".join(str(part) for part in command))
    subprocess.run(command, cwd=ROOT, env=env or build_child_env(), check=True)


def capture_command(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env or build_child_env(),
        text=True,
        capture_output=True,
        check=False,
    )


def build_child_env() -> dict[str, str]:
    env = os.environ.copy()
    cache_root = ROOT / ".cache"
    cache_root.mkdir(exist_ok=True)
    (cache_root / "pip").mkdir(exist_ok=True)
    env.setdefault("XDG_CACHE_HOME", str(cache_root))
    env.setdefault("PIP_CACHE_DIR", str(cache_root / "pip"))
    return env


def ensure_venv(venv_dir: Path) -> Path:
    python_path = venv_python(venv_dir)
    if python_path.exists():
        log(f"Using existing virtual environment: {venv_dir.name}")
        return python_path

    log(f"Creating virtual environment: {venv_dir.name}")
    run_command([sys.executable, "-m", "venv", str(venv_dir)])
    return python_path


def install_requirements(python_path: Path) -> None:
    run_command([str(python_path), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])


def ensure_requirements_installed(python_path: Path, venv_dir: Path) -> None:
    stamp_path = venv_dir / STAMP_FILE_NAME
    current_hash = requirements_hash()
    if (
        read_stamp(stamp_path) == current_hash
        and requirements_match(python_path)
        and pip_check_passes(python_path)
    ):
        log("Pinned requirements already installed. Skipping package install.")
        return

    log("Installing or updating project requirements.")
    install_requirements(python_path)
    run_command([str(python_path), "-m", "pip", "check"])
    stamp_path.write_text(current_hash + "\n", encoding="utf-8")


def requirements_match(python_path: Path) -> bool:
    verification_script = """
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys

requirements_file = Path(sys.argv[1])
problems = []

for raw_line in requirements_file.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    if "==" not in line:
        problems.append(f"Unsupported requirement format: {line}")
        continue
    package_name, expected_version = [part.strip() for part in line.split("==", 1)]
    try:
        actual_version = version(package_name)
    except PackageNotFoundError:
        problems.append(f"Missing package: {package_name}")
        continue
    if actual_version != expected_version:
        problems.append(
            f"Version mismatch for {package_name}: expected {expected_version}, found {actual_version}"
        )

if problems:
    print("\\n".join(problems))
    raise SystemExit(1)
"""
    result = capture_command([str(python_path), "-c", verification_script, str(REQUIREMENTS_FILE)])
    if result.returncode == 0:
        return True

    if result.stdout.strip():
        log(result.stdout.strip())
    if result.stderr.strip():
        log(result.stderr.strip())
    return False


def pip_check_passes(python_path: Path) -> bool:
    result = capture_command([str(python_path), "-m", "pip", "check"])
    if result.returncode == 0:
        return True

    if result.stdout.strip():
        log(result.stdout.strip())
    if result.stderr.strip():
        log(result.stderr.strip())
    return False


def run_smoke_checks(python_path: Path) -> None:
    log("Running local smoke checks.")
    smoke_script = """
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.report_generator import generate_pdf_report

client = TestClient(app)

openapi_response = client.get("/openapi.json")
assert openapi_response.status_code == 200, openapi_response.text

invalid_response = client.post("/analyze-url", json={"url": "not-a-url"})
assert invalid_response.status_code == 400, invalid_response.text

task_id = generate_pdf_report("<html><body><h1>Smoke Test</h1></body></html>")
pdf_path = Path("reports") / f"{task_id}.pdf"
html_path = Path("reports") / f"{task_id}.html"

assert pdf_path.exists() or html_path.exists(), "Report generation did not produce output."

if pdf_path.exists():
    pdf_path.unlink()
if html_path.exists():
    html_path.unlink()

print("SMOKE_CHECKS_OK")
"""
    run_command([str(python_path), "-c", smoke_script])


def run_live_check(python_path: Path, url: str) -> None:
    log(f"Running live analysis check against {url}")
    live_script = """
import asyncio
from pathlib import Path
import sys

from app.models.schema import FinalResponse
from app.services.scraper import analyze_url


async def main() -> None:
    result = await analyze_url(sys.argv[1])
    if "error" in result:
        raise RuntimeError(result["error"])

    validated = FinalResponse(**result)
    report_url = validated.report_url or ""
    print(f"LIVE_CHECK_OK report_url={report_url}")

    if report_url.startswith("/download-report/"):
        task_id = report_url.rsplit("/", 1)[-1]
        reports_dir = Path("reports")
        pdf_path = reports_dir / f"{task_id}.pdf"
        html_path = reports_dir / f"{task_id}.html"
        if pdf_path.exists():
            print(f"REPORT_FILE={pdf_path}")
        elif html_path.exists():
            print(f"REPORT_FILE={html_path}")


asyncio.run(main())
"""
    run_command([str(python_path), "-c", live_script, url], env=build_child_env())


def start_server(python_path: Path, host: str, port: int) -> None:
    log(f"Starting API server on http://{host}:{port}")
    os.execvpe(
        str(python_path),
        [
            str(python_path),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            host,
            "--port",
            str(port),
        ],
        build_child_env(),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap, verify, and run the SEO Spy Agent project."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Bootstrap the environment and run smoke checks without starting the server.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip the local smoke checks before starting the server.",
    )
    parser.add_argument(
        "--live-url",
        help="Run a full live analysis against the given URL after smoke checks.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for the uvicorn server.")
    parser.add_argument("--port", type=int, default=8000, help="Port for the uvicorn server.")
    return parser.parse_args()


def main() -> None:
    if not REQUIREMENTS_FILE.exists():
        raise SystemExit(f"Missing requirements file: {REQUIREMENTS_FILE}")

    args = parse_args()

    log(f"Detected operating system: {platform.system()}")
    venv_dir = detect_venv_dir()
    python_path = ensure_venv(venv_dir)
    ensure_requirements_installed(python_path, venv_dir)

    if not args.skip_smoke:
        run_smoke_checks(python_path)

    if args.live_url:
        run_live_check(python_path, args.live_url)

    if args.check_only:
        log("Checks completed successfully.")
        return

    start_server(python_path, args.host, args.port)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
