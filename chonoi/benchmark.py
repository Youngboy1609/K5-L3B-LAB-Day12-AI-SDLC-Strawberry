"""Measure the live Gather canvas in headless Chromium.

Install the optional tooling with `python3 -m pip install playwright` and
`python3 -m playwright install chromium`. Use --channel chrome or msedge
to measure an installed Chromium-based browser instead.
"""

import argparse
import json
import math
from pathlib import Path
from statistics import fmean

from .contract import load_contract
from .live import LiveGame, LiveServer


VIEWPORT = {"width": 1280, "height": 720}
START_TIMEOUT_MS = 15000

# Record completed callbacks of the game's canvas loop. The first eligible
# frame is the baseline. Menu frames and pre-restart snapshots are excluded.
FRAME_PROBE = """
(() => {
    const raf = window.requestAnimationFrame.bind(window);
    const probe = window.gatherBenchmark = {duration: 0, frames: [], stopped: false};
    window.requestAnimationFrame = callback => {
        if (callback.name !== 'frame') return raf(callback);
        return raf(timestamp => {
            callback(timestamp);
            if (!probe.duration || probe.stopped) return;
            const playing = screen === 'PLAY' && !pendingRestarts
                && snap && snap !== probe.previous && snap.mode === 'gather'
                && snap.phase === 'gather' && !snap.finished && !snap.paused && !snap.error;
            if (!playing) {
                if (probe.frames.length) {
                    probe.stopped = true;
                    probe.error = 'Gather left active gameplay at tick ' + snap?.tick
                        + ' (screen=' + screen + ', phase=' + snap?.phase
                        + ', paused=' + snap?.paused + ', finished=' + snap?.finished
                        + ', error=' + snap?.error + ')';
                }
                return;
            }
            const now = performance.now();
            if (snap !== probe.latest) {
                probe.latest = snap;
                probe.lastSnapshotAt = now;
            } else if (now - probe.lastSnapshotAt >= 5000) {
                probe.stopped = true;
                probe.error = 'Gather stopped receiving snapshots during measurement';
                return;
            }
            probe.frames.push(now);
            if (now - probe.frames[0] >= probe.duration) probe.stopped = true;
        });
    };
})();
"""


def frame_metrics(timestamps, load_ms):
    """Summarize millisecond timestamps using completed frame intervals."""
    intervals = [end - start for start, end in zip(timestamps, timestamps[1:])]
    if not intervals or any(not math.isfinite(gap) or gap <= 0 for gap in intervals):
        raise ValueError("Need at least two strictly increasing frame timestamps")
    frames = len(intervals)
    measured_s = (timestamps[-1] - timestamps[0]) / 1000
    slow_count = max(1, math.ceil(frames / 100))
    return {
        "avg_fps": frames / measured_s,
        "p1_low_fps": 1000 / fmean(sorted(intervals, reverse=True)[:slow_count]),
        "frames": frames,
        "measured_s": measured_s,
        "load_ms": load_ms,
    }


def benchmark(seed, duration, channel=None):
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError as exc:
        raise RuntimeError("Install benchmark tooling with python3 -m pip install playwright") from exc

    contract = load_contract()
    tuning = contract["tuning"]
    game = LiveGame("gather", tuning, {}, seed,
                    contract_version=contract.get("contract_version", "1.0"),
                    freshness=contract.get("freshness", tuning.get("freshness")))
    server = LiveServer(game, port=0)
    server.start()
    try:
        with sync_playwright() as playwright:
            options = {"channel": channel} if channel else {}
            browser = playwright.chromium.launch(headless=True, timeout=START_TIMEOUT_MS, **options)
            try:
                page = browser.new_page(viewport=VIEWPORT)
                page.set_default_timeout(START_TIMEOUT_MS)
                page.add_init_script(FRAME_PROBE)
                page.goto(server.url, wait_until="domcontentloaded")
                page.wait_for_function("typeof snap !== 'undefined' && snap?.mode === 'gather'")
                page.evaluate("""duration => {
                    gatherBenchmark.previous = snap;
                    gatherBenchmark.duration = duration;
                }""", duration * 1000)
                page.locator('button[data-act="play"]').click()
                page.wait_for_function("gatherBenchmark.frames.length > 0", polling=100)
                page.wait_for_function("gatherBenchmark.stopped", polling=100,
                                       timeout=duration * 1000 + START_TIMEOUT_MS)
                samples = page.evaluate("({frames: gatherBenchmark.frames, error: gatherBenchmark.error})")
                if samples.get("error"):
                    raise RuntimeError(samples["error"])
                return frame_metrics(samples["frames"], samples["frames"][0]), browser.version
            finally:
                browser.close()
    except Error as exc:
        raise RuntimeError(f"Chromium benchmark failed: {exc}") from exc
    finally:
        server.stop()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--duration", type=float, required=True, help="Measurement duration in seconds")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--channel", choices=("chrome", "msedge"), help="Use a locally installed browser")
    args = parser.parse_args(argv)
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("--duration must be finite and greater than zero")
    try:
        result, version = benchmark(args.seed, args.duration, args.channel)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Chromium {version}, {VIEWPORT['width']}x{VIEWPORT['height']} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
