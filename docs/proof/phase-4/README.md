# Bằng chứng QA Phase 4

Môi trường, kết quả đã đo và phạm vi kiểm có trong [ma trận Phase 4](../../verification/phase-4.md). Kết quả trước khi tích hợp nằm tại [PR #19](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/pull/19).

```sh
python3 -m pip install -r requirements-benchmark.txt
python3 -m playwright install chromium
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 docs/proof/phase-4/run_v11_regression.py
python3 -m chonoi.benchmark --seed 42 --duration 30 --out bench.json
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

PowerShell đặt `$env:PYTHONPATH = 'tests;.'` và dùng `python`. Benchmark và ca QA tương ứng cần Playwright và Chromium. `run_v11_regression.py` dùng manifest v1.1 trong cây tạm và bỏ riêng ca nghiệm thu manifest v1.3.

Đối chiếu hai lượt soak bằng `days`, `days_completed`, `crashes` và `results`. Thời gian thực nằm riêng ở `duration_s`. `bench.json` lưu số đo theo môi trường kiểm.
