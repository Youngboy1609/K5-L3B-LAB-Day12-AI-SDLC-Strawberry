# Youngboy1609 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm.** Ở Phase 1, tôi triển khai lịch khách và giữ nguyên liệu, rồi ghép bếp vào vòng tick (`0e82ad2`, `f7d5809`). Ở Phase 3, tôi nối contract/Day v1.2 và ghép các lát kho, Gather, Quán, HUD, QA ([kế hoạch](../plan/phase-3-tasks.md), [ma trận](../verification/phase-3.md)).

- **Tôi đã hỗ trợ.** Phase 4 tôi tiếp nhận lát soak của Ngọc Quang để nhóm có thể tiếp tục tích hợp. Commit `a623026` ghi hai lượt seed 7 hoàn tất 10/10 ngày với 0 crash, kết quả gameplay trùng nhau, suite 204 passed và regression v1.1 189 passed.

- **AI sai ở đâu.** Live Day từng tạo phiên với version mặc định v1.1 dù manifest khai v1.2. Fixture v1.2 trong `test_live_day.py` bắt lỗi thiếu truyền `contract_version` ([bằng chứng Phase 3](../verification/phase-3.md)).

- **Bài học.** Khi đổi contract, kiểm cả CLI lẫn mọi đường khởi tạo live và giữ fixture cũ làm hồi quy.
