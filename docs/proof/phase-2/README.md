# Bằng chứng QA Phase 2

Các log ghi base HEAD và working tree QA chưa commit. Không coi SHA nền là commit
đã chứa test mới. Khi bàn giao, chạy lại và ghi SHA ứng viên thực tế.

```bash
PYTHONPATH=tests:. python3 -m unittest test_phase2_regression -v
PYTHONPATH=tests:. python3 -m unittest test_phase2_day -v
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 tools/check_team.py
python3 -m chonoi.headless --mode day --seed 42 --days 1 --scenario docs/proof/phase-2/fixtures/p2-day-smoke.json --inputs docs/proof/phase-2/fixtures/p2-day-inputs.json --ticks 3 --snapshot-every 1 --out /tmp/p2-day-smoke.jsonl
```

Test day hiện dự kiến fail vì chưa triển khai; vẫn nằm trong discovery để thấy
khoảng thiếu. Không khai toàn suite xanh trước khi gameplay hỗ trợ.

`gather-{1,2}.jsonl.gz`, `quan-{1,2}.jsonl.gz` (giải nén trước khi so hash) chạy seed 42, 600 tick, snapshot mỗi tick,
với `fixtures/determinism-inputs.json`. Hash và thông tin môi trường ở determinism.json.
Đây là kiểm tất định ngắn hai mode v1.0, chưa chứng minh tất định day/cá/quái v1.1.
Test tự động bổ sung có fixture bắt cá để bảo đảm có event ở gather.
