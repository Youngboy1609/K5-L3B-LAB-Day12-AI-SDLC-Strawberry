"""Phase 4 v1.3 manifest compatibility at runtime boundaries."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chonoi.contract import effective_contract_version, load_contract
from chonoi.errors import BadInput
from chonoi.live import LiveGame
from chonoi import headless


class Phase4VersionCompatibility(unittest.TestCase):
    def _manifest(self, version="1.3"):
        manifest = load_contract()
        manifest["contract_version"] = version
        manifest["bench_cmd"] = "python3 -m chonoi.benchmark"
        manifest["soak_cmd"] = "python3 -m chonoi.soak"
        return manifest

    def test_v13_manifest_keeps_public_version_and_requires_release_commands(self):
        manifest = self._manifest()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contract.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            loaded = load_contract(path)
        self.assertEqual(loaded["contract_version"], "1.3")
        self.assertEqual(effective_contract_version(loaded["contract_version"]), "1.2")
        for key in ("bench_cmd", "soak_cmd"):
            for value in ("  ", 'python "unterminated'):
                invalid = dict(manifest)
                invalid[key] = value
                with tempfile.TemporaryDirectory() as temp:
                    path = Path(temp) / "contract.json"
                    path.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.subTest(key=key, value=value), self.assertRaises(BadInput):
                        load_contract(path)

    def test_headless_v12_and_v13_are_byte_identical(self):
        for mode, ticks in (("gather", "60"), ("quan", "60"), ("day", "22200")):
            outputs = []
            for version in ("1.2", "1.3"):
                manifest = self._manifest(version)
                with tempfile.TemporaryDirectory() as temp:
                    out = Path(temp) / f"{mode}.jsonl"
                    args = ["--mode", mode, "--seed", "42", "--ticks", ticks, "--out", str(out)]
                    if mode == "day":
                        args.extend(["--days", "1"])
                    with patch("chonoi.headless.load_contract", return_value=manifest):
                        code = headless.main(args)
                    self.assertEqual(code, 0)
                    outputs.append(out.read_bytes())
            with self.subTest(mode=mode):
                self.assertEqual(outputs[0], outputs[1])

    def test_headless_accepts_v13_day_cli_shape(self):
        manifest = self._manifest()
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "day.jsonl"
            with patch("chonoi.headless.load_contract", return_value=manifest):
                code = headless.main(["--mode", "day", "--days", "1", "--seed", "42",
                                      "--ticks", "22200", "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())

    def test_live_game_keeps_declared_version_and_runs_v12_day(self):
        manifest = self._manifest()
        game = LiveGame("day", manifest["tuning"], {}, 42, days=1,
                        contract_version=manifest["contract_version"],
                        freshness=manifest["freshness"])
        self.assertEqual(game.contract_version, "1.3")
        self.assertEqual(game.session.sim.contract_version, "1.2")
        state = json.loads(game.state_json())
        self.assertEqual(state["contract_version"], "1.3")


if __name__ == "__main__":
    unittest.main()
