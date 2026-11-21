# nmqdhtb — phản tư cá nhân

Bản nháp do Codex hỗ trợ theo yêu cầu của Nguyễn Minh Quân; Quân cần đọc lại trước khi bàn giao.

- Phần QA đã tạo: [8 test gather](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/fc431af), [9 test quan](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/commit/b2f749c). Commit đang ở local, link khả dụng sau khi push.
- Kiểm chứng: [ma trận AC](../verification/phase-1.md). Lượt kiểm trước tích hợp có 33/49 phương thức đạt; 16 chưa đạt vì gameplay còn TODO. Không sửa luật hoặc che lỗi bằng skip.
- Review: chưa có bằng chứng review của người khác; cần hai cặp gameplay đọc chéo test trước khi gộp.
- AI sai: Codex ban đầu tự tạo nhánh QA thay vì dùng nhánh có sẵn. Sau khi được nhắc, commit đã chuyển nguyên vẹn sang `nguyen_minh_quan`.
- Bài học rút ra từ lần kiểm: phân biệt smoke khung với kiểm luật hoàn chỉnh; báo lỗi kèm fixture, tick và trạng thái. Không tuyên bố đạt khi test chỉ kiểm một phần luồng.
- Nhật ký AI cá nhân: Codex hỗ trợ viết test, chạy lệnh và soạn bằng chứng cho ba commit QA. Model/token/chi phí: không có số liệu xác minh; chờ Nghĩa tích hợp vào nhật ký chung.

## Phase 2 — chuẩn bị QA độc lập

- Thêm test smoke vòng ngày theo kế hoạch và kiểm tất định hai mode độc lập.
- Giữ fixture và hướng dẫn chạy tại `docs/proof/phase-2/`; ma trận ở `docs/verification/phase-2.md`.
- Smoke đầu tiên báo thiếu \`--days\`. Lúc tích hợp, Nghĩa nối smoke với runtime v1.1 bằng dữ liệu thử để kiểm chuyển pha.
- Chờ nhóm review test và bảng P2-01 trước khi chốt kỳ vọng số liệu.

## Phase 3 — QA kho cá thể và độ tươi

- Chuẩn bị 12 test tích hợp CLI thật trên cây tạm, giữ manifest v1.1 để regression tái chạy độc lập.
- Regression 112/112 đạt; test v1.2 đang đỏ tại loader, chưa xác minh được gameplay. Xem [ma trận](../verification/phase-3.md).
- Bài học: ca đầu vào sai cần chạy payload hợp lệ trước, tránh báo đạt khi runtime từ chối mọi dữ liệu của phiên bản mới.
- Chưa khóa yêu cầu tái cấp còn mơ hồ P3-02; chưa có review chéo hoặc nghiệm thu HUD/remote tag. Đây là bản nháp cần Quân đọc lại.
