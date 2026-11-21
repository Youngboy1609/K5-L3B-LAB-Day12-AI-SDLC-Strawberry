# Retro nhóm

## Rà hành động đã chốt ở Phase 2 (mở đầu retro)

- **Hành động đã chốt:** trước khi tách nhánh Phase 3, thống nhất payload mẫu và ca chuyển pha dựa trên tag `phase-2`, rồi smoke trên cây đã ghép trước khi merge.
- **Kết quả:** đã có ca tích hợp qua kho, Day và live; `docs/verification/phase-3.md` ghi kết quả JSONL Day seed 42 giống từng byte và test liên quan. Kiểm tra ban đầu chưa bao phủ mọi đường khởi tạo live. HUD/Live Day còn dùng version mặc định v1.1 dù khai v1.2. Test live Day với fixture v1.2 bắt được lỗi trước khi chốt Phase 3. Bổ sung truyền version và ca hồi quy sớm hơn là việc cần làm.

## Phase 2 (nhanh)

- Điều tốt — Giao diện dùng chung giữa headless và bản chơi giúp nhóm kiểm chuyển pha, pause và Shop ngay khi ghép. Fixture ba tick phát hiện thiếu runtime sớm, ca 5 ngày xác minh các nâng cấp từ ngày kế tiếp.
- Điều tệ — Bản trích Ticket-02 thiếu bảng cân bằng và ví dụ payload. Các nhánh từng dùng khác tên trường hoặc nhận nhầm dữ liệu của phiên bản kia. Cần đối chiếu preset đề xuất với bảng gốc khi có.
- Hành động Phase 3 — Chốt payload mẫu và ca chuyển pha dựa trên tag `phase-2` trước khi chia nhánh, rồi chạy smoke trên cây ghép trước khi merge.

## Phase 3

- Payload cá thể dùng chung giúp ghép kho, Gather và Day khi v1.2 mới chạy thử. Smoke đọc lại file bắt được việc làm tròn fresh sát ngưỡng 30.
- PR HUD khai báo v1.2 nhưng phiên chơi Day vẫn mặc định dùng v1.1. Ca dựng live Day với fixture v1.2 bắt được chỗ thiếu tham số.
- Khi đổi phiên bản, giữ manifest cũ trong fixture hồi quy và thêm ca chung cho cả CLI lẫn live ngay từ lúc thống nhất cách truyền version.

## Phase 4 (cuối)
- **Phạm vi bằng chứng tại handoff:** lát soak được tích hợp ở `a623026` (`adaaf3a` trong nhánh này). Commit ghi nhận hai lượt seed 7 hoàn tất 10/10 ngày, 0 crash, kết quả gameplay bằng nhau khi bỏ `duration_s`, suite 204 passed và regression manifest v1.1 189 passed. Các số liệu này lấy từ commit đó, chưa chạy lại trong lần cập nhật hồ sơ.
- **Còn chờ:** benchmark 30 giây và `bench.json`, HUD/contrast mode cùng ba cảnh báo, clone sạch, ZIP, tag `phase-4`, GitHub Release `v1.0.0`, ma trận Phase 4 và kiểm chứng trên SHA bàn giao. Chưa kết luận đạt các mục này.
- **Lỗi AI đã xác minh:** ở Phase 3, đường Live Day khởi tạo với version mặc định v1.1 trong khi contract là v1.2. Fixture v1.2 qua test live phát hiện thiếu truyền `contract_version`; kiểm tra và kết quả được ghi trong `test_live_day.py` và `docs/verification/phase-3.md`.
- **Việc tiếp theo:** hoàn thành từng AC trên cùng ứng viên, lưu artifact và lệnh thực chạy, rồi rà đóng góp từng thành viên từ commit/bằng chứng trước khi viết kết luận retro cuối. Chưa ghi đánh giá chéo, số liệu cá nhân hoặc hỗ trợ đồng đội nếu chưa có bằng chứng.
