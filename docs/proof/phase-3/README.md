# Bằng chứng QA Phase 3

Chạy từ gốc repo bằng Python 3.

```sh
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 docs/proof/phase-3/run_regression.py
python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out day.jsonl
python3 tools/check_team.py
```

PowerShell dùng `python` và đặt `$env:PYTHONPATH = 'tests;.'`.

`test_phase3_integration` chạy CLI thật trong các thư mục tạm. Ca bàn giao so `gather_end.data.inventory`, file kho và snapshot Quán tick 0. Ca Day kiểm cùng tick chuyển pha, Shop giữ kho, và Day 2 cấp ID mới cho fixture. Ca giá tính lại từ số thập phân thực sự đưa vào fixture sau khi trừ hao Quán.

`run_regression.py` chạy suite trên bản sao với manifest v1.1 lấy tại `92795af`. Các fixture đếm Phase 1/2 vẫn chạy với v1.1 cả khi bản mặc định đã lên v1.2. Kỳ vọng nghiệp vụ cũ giữ nguyên.

Playwright mở live Gather và Quán tại localhost ở 1280×720 và 390×700. Gather hiện một cá thể tươi và một cá thể ƯƠN. Quán hiện 5 cá linh trong kho, gồm 3 đang giữ, 1 ươn và 1 còn cấp được. Canvas xuống dòng ở viewport hẹp. Xem [ma trận kết quả](../../verification/phase-3.md).
