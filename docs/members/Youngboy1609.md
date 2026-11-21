# Youngboy1609 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm.** Ở Phase 1, tôi chia việc cho nhóm 6 người và phụ trách lát khách quán. Tôi dùng Codex và GPT-6 Luna để triển khai lịch khách, giữ nguyên liệu và kiểm fixture. Sau đó tôi ghép phần bếp của Ngọc Quang vào vòng tick và kiểm lại `main` với 61 test qua. [Kế hoạch `6ed9fd8`](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/6ed9fd8) · [Lát khách `0e82ad2`](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/0e82ad2) · [Tích hợp `f7d5809`](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/f7d5809)
- **Tôi đã review.** Tôi đọc diff phần bếp, đối chiếu thứ tự xử lý với PRD-0 và chạy headless từ lúc khách đến đến lúc thu tiền. Tôi kiểm cả ca hết kiên nhẫn đúng tick đóng quán. [PR #1](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/pull/1) · [PR #2](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/pull/2)
- **AI sai ở đâu và tôi phát hiện thế nào.** Mã Luna viết chấp nhận `60.0` vì Python so sánh nó bằng `60`. Tôi thêm test CLI, thấy fixture sai vẫn trả mã 0, rồi bổ sung kiểm tra kiểu số nguyên. [Test hồi quy](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/blob/fbc5624/tests/test_quan_customers.py#L68)
- **Điều tôi học được.** Hai người sửa hai file riêng vẫn có thể lệch tên trường. Lần sau tôi sẽ chốt snapshot mẫu trước khi tách nhánh và chạy thử qua `step()` ngay khi ghép.

## Phase 3

- **Tôi phụ trách** chia việc, nối contract v1.2 ở CLI và Day, sửa độ chính xác khi lưu kho, rồi ghép các phần Gather, Quán, HUD và QA. Bản sửa kho vào PR #16 và Quán thực hiện với GPT-6 Luna. [Day và contract](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/273bf4d) · [PR #16](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/pull/16)
- **Tôi review** luồng bàn giao qua file và trong Day, giá theo độ tươi và HUD loại hàng ươn khỏi kho khả dụng. [Bằng chứng Phase 3](../verification/phase-3.md)
- **AI sai ở đâu.** Live báo schema v1.2 nhưng dựng Day bằng version mặc định. Test đưa giỏ cá thể qua `LiveGame` tái hiện lỗi.
- **Điều tôi học được.** Khi đổi schema cần kiểm tất cả đường khởi tạo phiên, cả CLI lẫn live. Ca sát ngưỡng phải đi qua file, mô phỏng và màn hình.
