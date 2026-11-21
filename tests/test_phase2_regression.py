"""Kiểm tất định qua CLI hai mode độc lập; không thay kỳ vọng P1."""
from pathlib import Path
import json
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, write_json
from helpers import run_legacy_headless as run_headless


class StandaloneDeterminism(unittest.TestCase):
    def test_same_seed_inputs_produce_identical_bytes(self):
        with Workdir() as w:
            inp = write_json(w.path("inputs.json"), frames(
                {"tick": 0, "move": [1, 0], "catch": True},
                {"tick": 60, "move": [0, 0], "interact": True, "catch": True},
                {"tick": 61, "interact": False, "catch": False}))
            for mode in ("gather", "quan"):
                with self.subTest(mode=mode):
                    outputs = []
                    extra = []
                    if mode == "gather":
                        tuning = json.loads((Path(ROOT) / "game.contract.json").read_text())["tuning"]
                        fish = tuning["gather"]["fish_initial"][0]
                        scenario = write_json(w.path("gather.json"), {"gather": {
                            "player": {"pos": fish["pos"]}, "fish": [fish], "random_fish": False}})
                        extra = ["--scenario", scenario]
                    for run in (1, 2):
                        out = w.path(f"{mode}-{run}.jsonl")
                        code, err = run_headless(
                            "--mode", mode, "--seed", "42", "--ticks", "600",
                            *extra, "--inputs", inp, "--snapshot-every", "1", "--out", out)
                        self.assertEqual(code, 0, err)
                        outputs.append(Path(out).read_bytes())
                    self.assertEqual(outputs[0], outputs[1])
                    rows = read_jsonl(out)
                    self.assertEqual(rows[-1]["ticks"], 600)
                    self.assertTrue(events(rows), "Cần có event để tránh chỉ so đầu ra rỗng")


if __name__ == "__main__":
    unittest.main()
