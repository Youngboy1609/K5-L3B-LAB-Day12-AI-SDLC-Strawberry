# nmqdhtb — phản tư cá nhân

Bản nháp do Codex hỗ trợ theo yêu cầu của Nguyễn Minh Quân; Quân cần đọc lại trước khi bàn giao.

- Phần QA đã tạo: [8 test gather](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/fc431af), [9 test quan](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/b2f749c). Commit đang ở local, link khả dụng sau khi push.
- Kiểm chứng: [ma trận AC](../verification/phase-1.md). Lượt kiểm trước tích hợp có 33/49 phương thức đạt; 16 chưa đạt vì gameplay còn TODO. Không sửa luật hoặc che lỗi bằng skip.
- Review: chưa có bằng chứng review của người khác; cần hai cặp gameplay đọc chéo test trước khi gộp.
- AI sai: Codex ban đầu tự tạo nhánh QA thay vì dùng nhánh có sẵn. Sau khi được nhắc, commit đã chuyển nguyên vẹn sang `nguyen_minh_quan`.
- Bài học rút ra từ lần kiểm: phân biệt smoke khung với kiểm luật hoàn chỉnh; báo lỗi kèm fixture, tick và trạng thái. Không tuyên bố đạt khi test chỉ kiểm một phần luồng.
- Nhật ký AI cá nhân: Codex hỗ trợ viết test, chạy lệnh và soạn bằng chứng cho ba commit QA. Model/token/chi phí: không có số liệu xác minh; chờ Nghĩa tích hợp vào nhật ký chung.
