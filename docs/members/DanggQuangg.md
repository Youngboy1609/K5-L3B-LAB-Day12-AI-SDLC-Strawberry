# Phản tư của Phạm Đăng Quang

Tôi phụ trách vòng tick Gather, từ luật sinh tồn đến cá, Cá Sấu và độ tươi của giỏ. Khi ghép độ tươi, tôi kiểm thứ tự hồi nút, hao tươi và thu hoạch để nguyên liệu mới giữ đúng độ tươi trong tick vừa thu. Tôi cũng kiểm sự kiện bị đánh và ngất để đồ rơi theo thứ tự nhặt sau rơi trước. [Gather Phase 3](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/pull/16)

Ở Phase 4, tôi đo cảnh Gather thật qua nút **Chơi** và dùng các khoảng giữa khung gameplay để tính FPS. Lượt đo Chrome headless 30 giây tại 1280×720 cho 59,91 FPS trung bình, 46,05 FPS ở 1% low và 849,9 ms tới khung đầu. Tôi ghi trung bình thấp hơn mốc 60 dù số này làm tròn nguyên thành 60. [Commit benchmark và test](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/cb175b5)

Ca chạy ngắn tạo được JSON. Lượt 30 giây đầu dừng khi điều kiện ghi nhận gameplay mất hiệu lực. Sau khi rà cách canvas tiếp tục vẽ từ snapshot gần nhất, tôi chỉnh phép đo để chấp nhận gián đoạn ngắn, đồng thời đặt giới hạn khi luồng snapshot ngừng cập nhật. Lượt chạy lại hoàn thành đủ thời lượng.

Với lệnh mặc định trên Chromium Headless Shell 159.0.8154.6, tôi tách vòng chờ trạng thái của Playwright khỏi nhịp render. Lượt đo 30,0155 giây ghi nhận 1.801 khung, 60,002 FPS trung bình, 53,916 FPS ở 1% low và 196,3 ms tới khung đầu.
