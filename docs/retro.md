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
- **Điều làm tốt** Nhóm giữ schema v1.2 và so JSONL theo byte trước khi bật manifest v1.3. Cây ghép qua 217 test. Hai lượt soak đủ 10 Ngày, 0 crash và trùng kết quả. [Ma trận Phase 4](verification/phase-4.md)
- **Điều cần cải thiện** Lệnh benchmark mặc định trên máy Windows kỳ vọng một bản Chromium khác bản đã cài. Lượt đo trên PR #23 bắt lỗi mở trình duyệt. Nhóm khai phiên bản Playwright trong file phụ thuộc và cho lệnh dùng bản Chromium tương thích đã có trên máy.
- **Lỗi AI đã xác minh:** ở Phase 3, đường Live Day khởi tạo với version mặc định v1.1 trong khi contract là v1.2. Fixture v1.2 qua test live phát hiện thiếu truyền `contract_version`; kiểm tra và kết quả được ghi trong `test_live_day.py` và `docs/verification/phase-3.md`.
- **Việc tiếp theo** Nghĩa và Minh Quân xác nhận platform chạy từ clone sạch trên commit bàn giao. Mỗi thành viên kiểm lại giới hạn 200 từ và bổ sung bằng chứng cá nhân trước khi chốt hồ sơ.
