"""Chạy hồi quy Phase 3 với v1.1, loại riêng test nghiệm thu v1.3."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
with tempfile.TemporaryDirectory(prefix="chonoi-p4-v11-") as directory:
    target = Path(directory)
    for name in ("chonoi", "tests", "docs", "tools"):
        shutil.copytree(ROOT / name, target / name,
                        ignore=shutil.ignore_patterns("__pycache__", "test_phase4_contract.py"))
    shutil.copy2(ROOT / "TEAM.md", target / "TEAM.md")
    result = subprocess.run([sys.executable, str(target / "docs/proof/phase-3/run_regression.py")])
    sys.exit(result.returncode)
