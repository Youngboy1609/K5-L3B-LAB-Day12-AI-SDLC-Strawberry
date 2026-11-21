"""Chạy test P1/P2 với manifest v1.1 được giữ lại, trong thư mục tạm."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
with tempfile.TemporaryDirectory(prefix="chonoi-p3-regression-") as directory:
    target = Path(directory)
    for name in ("chonoi", "tests", "docs", "tools"):
        shutil.copytree(ROOT / name, target / name,
                        ignore=shutil.ignore_patterns("__pycache__", "test_phase3_integration.py"))
    shutil.copy2(ROOT / "TEAM.md", target / "TEAM.md")
    shutil.copy2(Path(__file__).parent / "fixtures/contract-v1.1.json", target / "game.contract.json")
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                            cwd=target, env=dict(os.environ, PYTHONPATH=os.pathsep.join((str(target / "tests"), str(target)))))
    sys.exit(result.returncode)
