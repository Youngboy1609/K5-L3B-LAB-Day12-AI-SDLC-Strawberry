# TruongThuHa — phản tư cá nhân

## Phase 1
- **Tôi đã làm:** HUD quán và HUD buổi sáng trong `chonoi/web/index.html` ([f421f18](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/f421f18), [73d583e](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/73d583e)), sửa theo review ([b788ae8](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/b788ae8)); README chạy từ clone sạch ([a43581d](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/a43581d)). Gộp qua [PR #5](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/pull/5).
- **Review:** nhận review của Nghĩa trên [PR #5](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/pull/5), sửa lọc kho theo `order_status` và trạng thái khách `waiting`/`eating`, trả lời kèm ảnh chơi thử. Trong Phase 1 tôi chưa review PR của bạn khác.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  1. Claude Code để dòng "Kho khả dụng" dài bị cắt mất "bông súng" và cắt tên món trong bảng khách. Tôi phát hiện khi chơi thử với màn dựng sẵn và so từng trường.
  2. HUD dựng theo snapshot mẫu đoán trước nên lọc kho theo `state` thay vì `order_status`. Nghĩa phát hiện khi review; tôi merge `main` và thử lại với code thật (test 61/61 OK).
- **Điều tôi học được:** HUD chỉ đọc snapshot nên phải đối chiếu tên trường với code thật; luôn chơi thử trước khi commit; làm trên nhánh riêng, tạo PR và kiểm tra đúng repo đích trước khi gửi.

## Phase 2 (đang làm, nhánh `phase2/day-hud`)
- Menu Chơi/Thoát, khung màn chuyển cảnh, cảnh báo oxy, chữ HUD ≥ 18px, bộ đếm FPS ([7b159ff](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/7b159ff)); sửa chữ đè/cắt ở cửa sổ hẹp ([651010f](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/651010f)). Đang chờ Nghĩa chốt hợp đồng để làm Shop và pause.