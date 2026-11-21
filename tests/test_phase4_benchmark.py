import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from chonoi.benchmark import frame_metrics, main


class GatherBenchmark(unittest.TestCase):
    def test_uses_mean_of_slowest_one_percent_of_frame_intervals(self):
        timestamps = [0]
        for gap in [16] * 99 + [32, 48]:
            timestamps.append(timestamps[-1] + gap)

        result = frame_metrics(timestamps, load_ms=250)

        self.assertEqual(result["frames"], 101)
        self.assertAlmostEqual(result["measured_s"], 1.664)
        self.assertAlmostEqual(result["avg_fps"], 101 / 1.664)
        self.assertAlmostEqual(result["p1_low_fps"], 25)
        self.assertEqual(result["load_ms"], 250)

    def test_short_sample_uses_at_least_one_interval(self):
        self.assertEqual(frame_metrics([200, 216, 236], 200)["p1_low_fps"], 50)
        with self.assertRaises(ValueError):
            frame_metrics([200], 200)

    def test_cli_writes_only_contract_fields(self):
        result = frame_metrics([200, 220, 240], 200)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bench.json"
            with patch("chonoi.benchmark.benchmark", return_value=(result, "test")) as run:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--seed", "42", "--duration", "0.04", "--out", str(output)]), 0)
            run.assert_called_once_with(42, 0.04, None)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(set(report), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
        self.assertEqual(report, result)

    def test_cli_rejects_invalid_duration(self):
        for duration in ("0", "-1", "nan", "inf"):
            with self.subTest(duration=duration), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(["--seed", "42", "--duration", duration, "--out", "unused.json"])
                self.assertEqual(error.exception.code, 2)
