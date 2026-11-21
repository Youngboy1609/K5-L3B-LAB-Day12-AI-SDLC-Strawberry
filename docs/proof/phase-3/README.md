# Bằng chứng QA Phase 3

Chạy từ gốc repo bằng Python 3:

```sh
python3 docs/proof/phase-3/run_regression.py
PYTHONPATH=tests:. python3 -m unittest test_phase3_integration -v
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

PowerShell: đặt `$env:PYTHONPATH = 'tests;.'`, dùng `python` thay `python3`.

`run_regression.py` sao chép mã/test cũ và manifest `fixtures/contract-v1.1.json` vào thư mục tạm, bỏ riêng test P3 rồi chạy discovery. Không thay manifest sản phẩm. Fixture v1.1 là bản nguyên vẹn từ cây nguồn `92795af`; các giá trị vẫn mang trạng thái đề xuất P2-01 như kế hoạch.

Test P3 tự dựng fixture, manifest v1.2 và subprocess CLI trong thư mục tạm riêng cho từng test. Không skip khi v1.2 chưa được hỗ trợ. Dữ liệu thử `freshness` lấy từ kế hoạch Phase 3; chưa chứng nhận đây là contract chính thức. Không lưu JSONL/log thô vào repo.

Lượt 2026-11-21: regression **112/112 đạt**. Suite P3 **12 test, 14 failure** (có subtest), tất cả bị chặn ở loader v1.2. Full suite cuối: **124 test, 14 failure, 0 error**, 6,563 s. Ma trận và giới hạn tại [verification](../../verification/phase-3.md).
