# Ma trận kiểm chứng Phase 2 — QA chuẩn bị

Nguyễn Minh Quân, Codex hỗ trợ, 2026-11-21. Đây là bằng chứng local trên
HEAD ghi trong từng log và working tree QA chưa commit; chưa phải xác nhận bàn giao.

| AC | Kiểm chứng | Kết quả hiện tại |
|---|---|---|
| AC-P2-01 | Manifest sáu nguyên liệu/món, cá, Cá Sấu, thứ tự tick | Chưa kiểm v1.1; manifest hiện là v1.0, chờ bảng chuẩn P2-01 và module gameplay. |
| AC-P2-02 | `tests/test_phase2_day.py`, fixture smoke 3 tick | Chưa đạt: CLI từ chối `--days 1`. Test không skip/expectedFailure. Pause, Shop, nâng cấp, D1–D5 chưa kiểm. |
| AC-P2-03 | HUD, FPS, chữ, benchmark một ngày | Chưa kiểm. Cần bản chơi day và ghi máy đo; local không thay kết quả máy chấm. |
| AC-P2-04 | Regression P1, kiểm tất định, test mới | P1 và tất định xem log bên dưới; coverage P2 chưa đầy đủ. |
| AC-P2-05 | Tag remote trỏ commit main đã kiểm | Chưa xác minh remote/tag; không có thao tác push/tag trong lượt QA này. |

Kết quả lượt local: **79/79 test P1 đạt; suite mới 80/81 đạt**, một lỗi smoke day
do CLI chưa nhận --days. Team check đạt 6 thành viên. Hai cặp JSONL cùng seed/input
đều giống byte. Không sửa gameplay trong lượt này.

## Bằng chứng và cách chạy

- [Mốc 79 test P1](../proof/phase-2/baseline-p1.txt).
- [Suite sau khi thêm QA P2](../proof/phase-2/suite-phase2.txt).
- [Kiểm nhóm](../proof/phase-2/team-check.txt).
- [Hash hai lần chạy từng mode](../proof/phase-2/determinism.json).
- [Hướng dẫn chạy lại](../proof/phase-2/README.md).

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

## Các ca tiếp theo khi module sẵn sàng

Pause cả ba mode và Shop; resume chạy ngay; giữ nút qua pha; buy chỉ theo frame,
buy trước shop_done; đủ/thiếu tiền, max/unsupported; active_upgrades đổi ngày kế;
Shop đóng sau 600 tick hoạt động; ngất mở quán rỗng; D1–D5; cá/quái/recoil/LIFO;
nhiều đơn giữ kho và no_dish. Chưa có test thực thi cho các mục trong đoạn này.

## Kiểm lại sau ghép main 718cf26

[Log tích hợp](../proof/phase-2/merge-main-suite.txt): 99/100 test đạt; một lỗi
smoke day vì manifest vẫn là v1.0. CLI đã nhận --days. Team check đạt 6 thành viên.
Giải quyết xung đột nhật ký AI bằng cách giữ các dòng của cả hai nhánh; không sửa gameplay
hoặc kỳ vọng test. Các kết quả 79/79 và 80/81 ở trên là lịch sử trước tích hợp.
