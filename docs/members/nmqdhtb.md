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

## Phase 4 — QA trước tích hợp

- Viết [5 test release contract](../../tests/test_phase4_contract.py): so JSONL ba mode v1.2/v1.3, kho cá thể, command manifest, soak lặp và benchmark 30 giây.
- [Ma trận và bằng chứng](../verification/phase-4.md): 202 test cũ đạt, hồi quy v1.1 187/187, mở rộng 14/14. Năm phương thức P4 chưa đạt với 7 failure vì chưa ghép v1.3/bench/soak; chưa nghiệm thu HUD, ZIP hoặc Release.
- AI sai: fixture so sánh ban đầu gửi cả hai khối cho mode độc lập, bị parser từ chối. Đọc lỗi CLI, tách khối theo mode rồi chạy lại; v1.2 thành công trước lỗi v1.3. Ca kho có đối chứng v1.2 đạt.
- Bài học: kiểm fixture hợp lệ trước khi quy lỗi runtime; ghi SHA và phân biệt kiểm API với kiểm HUD. Chờ review của Quân và bằng chứng các chủ lát để chốt AC.
