# Ma trận kiểm chứng Phase 2 — QA chuẩn bị

Nguyễn Minh Quân chuẩn bị QA, Hồ Trọng Nghĩa kiểm khi tích hợp (2026-11-21).
Kết quả chạy với dữ liệu thử chưa phải xác nhận bàn giao.

| AC | Kiểm chứng | Kết quả hiện tại |
|---|---|---|
| AC-P2-01 | Manifest sáu nguyên liệu/món, cá, Cá Sấu, thứ tự tick | Đã có test cá bơi/sinh, tuổi cá theo fixture, ngưỡng chạm Cá Sấu, recoil, thứ tự ngất và bàn giao kho. Cá và hai nguyên liệu mới được kiểm bằng dữ liệu thử v1.1. Manifest chuẩn chờ P2-01. |
| AC-P2-02 | `tests/test_phase2_day.py`, fixture smoke 3 tick | Smoke chuyển pha dùng preset thử v1.1. Kế hoạch D1–D5 và bảng giá chuẩn chờ P2-01. |
| AC-P2-03 | HUD, FPS, chữ, benchmark một ngày | Chưa kiểm. Cần bản chơi day và ghi máy đo; local không thay kết quả máy chấm. |
| AC-P2-04 | Regression P1, kiểm tất định, test mới | Bản ghép QA trên main 718cf26 đạt 100/100. Test so byte JSONL hai mode độc lập đạt. |
| AC-P2-05 | Tag remote trỏ commit main đã kiểm | Chưa chốt tag Phase 2. Chờ preset v1.1 và kiểm bản chơi day. |

Lượt QA trước tích hợp có **79/79 test P1 đạt** và **80/81 test toàn suite**.
Smoke day khi đó dừng ở CLI do chưa có `--days`. Hai mode độc lập cho JSONL
giống byte khi chạy lại cùng seed/input.

Trên bản ghép QA với main 718cf26, unittest discovery đạt **100/100** và
kiểm tra roster đạt **6 thành viên**. Smoke ba tick dùng preset v1.1 riêng.

[Fixture và hướng dẫn chạy lại](../proof/phase-2/README.md).

Smoke dựa đúng fixture trong `docs/plan/phase-2-tasks.md`: cần spawn mặc định
nằm trong bến; đối chiếu lại khi bảng chuẩn thay đổi. Kiểm thứ tự ba event khởi
đầu, snapshot pha mới ở tick 0/1/2 có phase_tick 0, event kết thúc giữ pha cũ,
và end tick 3 có days_completed 1, reason days_complete. Chưa chốt payload
chi tiết của day_plan hoặc phase_start khi tài liệu chưa định nghĩa đủ.

## Rà regression trước khi tích hợp v1.1

| Kỳ vọng hiện tại | Xử lý khi tích hợp |
|---|---|
| `test_con_03_old_and_future_modes_rejected` từ chối cả river/day | Giữ river bị từ chối, thay phần day bằng ca v1.1; chỉ đổi khi mode đã triển khai. |
| Snapshot gather mặc định: vị trí [2,0], sáu đàn cá | Đối chiếu bảng chuẩn rồi ghi lý do thay kỳ vọng. |
| Fixture bếp/bàn/menu, kind kho và giá/thời gian v1.0 | Rà lại với tuning chính thức; không thay test chỉ để xanh. |
| Thứ tự tick, cạnh nút, giữ chỗ/trừ kho, đóng ca P1 | Giữ regression trừ khi có quy tắc v1.1 thay thế rõ ràng. |

## Các ca cần thêm vào bộ test bàn giao

Pause cả ba mode và Shop; resume chạy ngay; giữ nút qua pha; buy chỉ theo frame,
buy trước shop_done; đủ/thiếu tiền, max/unsupported; active_upgrades đổi ngày kế;
Shop đóng sau 600 tick hoạt động; ngất mở quán rỗng; D1–D5; cá/quái/recoil/LIFO;
nhiều đơn giữ kho và no_dish. Chưa có test thực thi cho các mục trong đoạn này.
