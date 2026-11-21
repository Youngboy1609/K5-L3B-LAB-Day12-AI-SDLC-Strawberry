# shoxieje — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): lát 4 `quan` trên nhánh `phase1/quan-service` — `chonoi/sim/quan_service.py` (`advance_stoves`, `interact`, `settle_customers`) và `tests/test_quan_service.py` (18 ca: trừ kho chỉ lúc bắt đầu nấu, chọn đối tượng theo khoảng cách/bếp trước/id, giao đúng đơn, giao ở tick kiên nhẫn về 0, ăn xong trả tiền + boa, khách bỏ đi dọn món không hoàn nguyên liệu, kẹp uy tín, đóng ca có khách ăn).
- Tôi đã review (kèm link): (cập nhật sau khi Nghĩa ghép vào `step()`.)
- AI sai ở đâu và tôi phát hiện thế nào: AI không mở được PRD-0 trên lab board nên phải dựa vào bảng quyền ghi trong `docs/plan/phase-1-tasks.md`; các chỗ đoán (đóng ca, boa → uy tín) ghi ở `docs/clarify.md` P1-02 để PO chốt.
- Điều tôi học được: chốt hợp đồng dữ liệu (trường của khách, payload món) ngay đầu file giúp hai lát làm song song mà không chờ nhau.

## Nhật ký dùng AI (gửi Nghĩa tổng hợp)
- Claude Code: đọc kế hoạch + starter, viết `quan_service.py` và unit test, chạy suite `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → 49 test OK.
