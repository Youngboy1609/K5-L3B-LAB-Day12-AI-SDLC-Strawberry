# Retro nhóm

## Phase 2 (nhanh)

- Điều tốt — Giao diện dùng chung giữa headless và bản chơi giúp nhóm kiểm chuyển pha, pause và Shop ngay khi ghép. Fixture ba tick phát hiện thiếu runtime sớm, ca 5 ngày xác minh các nâng cấp từ ngày kế tiếp.
- Điều tệ — Bản trích Ticket-02 thiếu bảng cân bằng và ví dụ payload. Các nhánh từng dùng khác tên trường hoặc nhận nhầm dữ liệu của phiên bản kia. Cần đối chiếu preset đề xuất với bảng gốc khi có.
- Hành động Phase 3 — Chốt payload mẫu và ca chuyển pha dựa trên tag `phase-2` trước khi chia nhánh, rồi chạy smoke trên cây ghép trước khi merge.

## Phase 3

- Payload cá thể dùng chung giúp ghép kho, Gather và Day khi v1.2 mới chạy thử. Smoke đọc lại file bắt được việc làm tròn fresh sát ngưỡng 30.
- PR HUD khai báo v1.2 nhưng phiên chơi Day vẫn mặc định dùng v1.1. Ca dựng live Day với fixture v1.2 bắt được chỗ thiếu tham số.
- Khi đổi phiên bản, giữ manifest cũ trong fixture hồi quy và thêm ca chung cho cả CLI lẫn live ngay từ lúc thống nhất cách truyền version.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
