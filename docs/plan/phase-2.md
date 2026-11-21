# Kế hoạch Phase 2 · Strawberry

**Mục tiêu** Chơi trọn một vòng ngày với Test Contract v1.1. Giữ `gather` và `quan` chạy độc lập, nối hai buổi trong `day`, mua nâng cấp ở Shop và áp cấp mới từ Ngày kế tiếp. Đẩy tag `phase-2` trên `main` trước mốc **1:55**.

**Mốc chuẩn bị** `main` tại `d7c1c03` đã có `gather`, `quan`, HUD hai buổi và test QA của Phase 1. Dùng mốc này để chuẩn bị Phase 2. Khi tag `phase-1` được chốt, đối chiếu các nhánh với bản bàn giao trước khi tích hợp v1.1. [Task theo từng người](phase-2-tasks.md) · [Mốc tích hợp Phase 1](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/d7c1c031f386ef35de8a3cbe55c3300bca5357a0)

| Phút trong Phase 2 | Việc cần xong | Người chốt |
|---|---|---|
| 0–8 | Chốt file và nhánh. Xác nhận bảng chuẩn còn thiếu, báo cả nhóm trước khi đổi manifest. Chốt hợp đồng `day ↔ gather ↔ quan ↔ HUD` và tình trạng `phase-1`. | Nghĩa, cả nhóm |
| 8–20 | Làm các lát song song. Dựng chuyển pha `gather → quan → shop`; chạy smoke bằng fixture trước phút 20. Lưu kết quả thực tế và báo chỗ đang vướng. | Nghĩa, Minh Quân |
| 20–42 | Ghép cá và Cá Sấu vào `gather`, giao menu ngày cho `quan`, nối Shop/pause và HUD. Chạy lại smoke với hai mode thật. | Đăng Quang, Ngọc Quang, Nghĩa, Hà |
| 42–50 | Rà regression P1, chạy D1–D5, kiểm v1.1, đo thời gian headless một ngày và FPS bản chơi. Ghi bằng chứng trên ứng viên `main`. | Minh Quân, Hà |
| 50–55 | Chốt `verification/phase-2.md`, log AI, clarify và retro nhanh. Đẩy tag trên `main`, kiểm tag remote. Ghi mục chưa đạt nếu còn thiếu. | Nghĩa, Minh Quân |

## Tiêu chí bàn giao

- `AC-P2-01` Manifest v1.1 khớp bảng chuẩn. Có đủ sáu nguyên liệu, sáu món, hai bếp, bốn bàn. Cá bơi/sinh và Cá Sấu chạy đúng thứ tự tick, rơi nửa giỏ theo LIFO, ngất bàn giao kho rỗng.
- `AC-P2-02` `day` công bố đúng kế hoạch D1–D5, chuyển đúng pha và chỉ tính ngày hoàn tất khi đóng Shop. Pause dừng timer, cấp mua chưa tác động tới ngày đang chơi, áp ở ngày kế.
- `AC-P2-03` Có menu, các màn chuyển cảnh, Shop, pause và HUD đúng Ticket-02. Bản chơi đạt trung bình ≥ 30 FPS ở 1280×720, chữ HUD không chân ≥ 18 px. Headless một ngày không pause chạy ≤ 20 s trên máy chấm, tối đa 22.200 tick. Ghi máy đo thực tế, tách số đo local và kết quả máy chấm.
- `AC-P2-04` Smoke tích hợp và regression P1 có bằng chứng. Ghi lý do khi một kỳ vọng P1 đổi theo v1.1. `docs/verification/phase-2.md` nối AC với kết quả trên commit bàn giao. Nhật ký AI, clarify, retro và đóng góp từng người được cập nhật.
- `AC-P2-05` Tag `phase-2` có trên remote và trỏ đúng commit chạy được trên `main`. Nhóm 6 người có mục tiêu ít nhất hai mở rộng cho cả lab. Chỉ khai `extensions` và README cho phần đã làm, có bằng chứng.

**Dữ liệu cần xác nhận trước khi chốt preset** Bản Ticket-02 đã cung cấp thiếu bảng mục 1–2 và bảng khóa manifest. Lấy bảng gốc trên lab board cho số chuẩn, cá, menu, bố trí quán, kế hoạch D1–D5 và bảng nâng cấp. Khi chưa có, dùng fixture để kiểm cấu trúc vòng tick và ghi kết quả theo phạm vi đó. [Câu hỏi P2-01](../clarify.md) · [Lab board](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)
