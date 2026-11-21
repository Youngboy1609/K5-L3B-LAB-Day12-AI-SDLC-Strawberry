"""Release QA: CLI thật trong cây tạm, không sửa manifest khóa của nhóm.

Chạy riêng: PYTHONPATH=tests:. python3 -m unittest test_phase4_contract -v
Các ca v1.3 phải đỏ nếu runtime chưa tích hợp; không skip hoặc mock gameplay.
"""
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

from helpers import ROOT, snapshots, read_jsonl


class ReleaseContract(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="chonoi-p4-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copytree(Path(ROOT) / "chonoi", self.root / "chonoi",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.published = json.loads((Path(ROOT) / "game.contract.json").read_text())
        self.contract = dict(self.published, contract_version="1.3")
        self.save("game.contract.json", self.contract)

    def save(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def cli(self, command, *args, timeout=60):
        result = subprocess.run([*shlex.split(command), *map(str, args)], cwd=self.root,
                                env=dict(os.environ, PYTHONPATH=str(self.root)),
                                capture_output=True, text=True, timeout=timeout)
        return result

    def ok(self, command, *args, **kwargs):
        result = self.cli(command, *args, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)

    def headless(self, mode, out, *args):
        self.ok(self.contract["headless_cmd"], "--mode", mode, "--seed", 42,
                "--ticks", 5, "--snapshot-every", 1, "--out", self.root / out, *args)

    def test_published_manifest_has_release_commands(self):
        self.assertEqual(self.published["contract_version"], "1.3")
        for key in ("bench_cmd", "soak_cmd"):
            self.assertIsInstance(self.published.get(key), str, key)
            self.assertTrue(shlex.split(self.published[key]), key)

    def test_v12_v13_jsonl_identical_for_all_modes(self):
        fixture = {
            "gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                       "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 1, "random_customers": False,
                     "random_reservations": False, "customers": []}}
        controls = self.save("inputs.json", {"frames": [
            {"tick": 0, "interact": True}, {"tick": 1, "interact": False},
            {"tick": 3, "shop_done": True}]})
        for mode in ("gather", "quan", "day"):
            with self.subTest(mode=mode):
                scenario = self.save("scenario.json", fixture if mode == "day" else {mode: fixture[mode]})
                for version in ("1.2", "1.3"):
                    self.save("game.contract.json", dict(self.contract, contract_version=version))
                    self.headless(mode, version + ".jsonl", "--scenario", scenario,
                                  "--inputs", controls)
                self.assertEqual((self.root / "1.2.jsonl").read_bytes(),
                                 (self.root / "1.3.jsonl").read_bytes())

    def test_v13_inventory_identity_and_count_rejection(self):
        scenario = self.save("gather.json", {"gather": {
            "hold": [{"id": "I7", "kind": "ca_linh", "fresh": 81.25}],
            "random_fish": False, "monsters": []}})
        controls = self.save("inputs.json", {"frames": [{"tick": 0, "interact": True}]})
        inventory = self.root / "inventory.json"
        self.headless("gather", "gather.jsonl", "--scenario", scenario,
                      "--inputs", controls, "--inventory-out", inventory)
        stock = json.loads(inventory.read_text())["items"]
        self.assertEqual(len(stock), 1)
        self.assertEqual((stock[0]["id"], stock[0]["kind"]), ("I7", "ca_linh"))
        self.assertAlmostEqual(stock[0]["fresh"], 81.25 - 0.5 / 60, places=10)
        self.ok(self.contract["headless_cmd"], "--mode", "quan", "--seed", 42,
                "--ticks", 0, "--out", self.root / "quan.jsonl", "--inventory", inventory)
        self.assertEqual(snapshots(read_jsonl(self.root / "quan.jsonl"))[0]["stock"], stock)
        self.save("inventory.json", {"items": {"ca_linh": 1}})
        target = self.root / "quan.jsonl"
        target.write_bytes(b"existing-output\n")
        result = self.cli(self.contract["headless_cmd"], "--mode", "quan", "--seed", 42,
                          "--ticks", 0, "--out", target, "--inventory", inventory)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(target.read_bytes(), b"existing-output\n")

    def test_manifest_soak_ten_days_repeatable(self):
        command = self.published.get("soak_cmd")
        self.assertIsInstance(command, str, "manifest thiếu soak_cmd")
        runs = []
        for index in range(2):
            path = self.root / f"soak-{index}.json"
            self.ok(command, "--seed", 7, "--days", 10, "--out", path, timeout=180)
            data = json.loads(path.read_text())
            self.assertEqual(set(data), {"days", "days_completed", "crashes", "duration_s", "results"})
            self.assertEqual((data["days"], data["days_completed"], data["crashes"]), (10, 10, 0))
            self.assertEqual(len(data["results"]), 10)
            self.assertEqual([r["day"] for r in data["results"]], list(range(1, 11)))
            self.assertTrue(all(len(r) == 4 for r in data["results"]))
            self.assertTrue(math.isfinite(data["duration_s"]))
            self.assertGreaterEqual(data.pop("duration_s"), 0)
            runs.append(data)
        self.assertEqual(*runs)

    def test_manifest_benchmark_real_thirty_seconds(self):
        command = self.published.get("bench_cmd")
        self.assertIsInstance(command, str, "manifest thiếu bench_cmd")
        path = self.root / "bench.json"
        self.ok(command, "--seed", 42, "--duration", 30, "--out", path, timeout=120)
        data = json.loads(path.read_text())
        self.assertEqual(set(data), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        for value in data.values():
            self.assertNotIsInstance(value, bool)
            self.assertTrue(isinstance(value, (float, int)) and math.isfinite(value))
            self.assertGreater(value, 0)
        self.assertIsInstance(data["frames"], int)
        self.assertGreaterEqual(data["measured_s"], 30)
        # Ngưỡng hiệu năng ghi theo môi trường trong ma trận, không ép CI đạt 60 FPS.


if __name__ == "__main__":
    unittest.main()
