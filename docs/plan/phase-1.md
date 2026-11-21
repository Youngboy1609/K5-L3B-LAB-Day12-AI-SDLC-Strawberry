# Kế hoạch Phase 1 · Strawberry

**Mục tiêu** Hai buổi `gather` và `quan` chơi riêng được, có HUD đọc được và nối qua file kho. Bàn giao trên `main` theo Test Contract v1.0, đẩy tag `phase-1` trước mốc 1:00.

**Cách làm** Giữ starter Python, preset v1.0 và trình chơi thử có sẵn. Sáu nhánh từ cùng mốc `main`, mỗi file một người phụ trách. Đọc [task theo từng người](phase-1-tasks.md) để lấy lệnh, quyền sửa file và tiêu chí bàn giao.

| Phút của phase | Việc cần xong | Người chốt |
|---|---|---|
| 0–15 | Xác nhận quyền Write của 5 thành viên còn lại, tên repo theo mẫu đề, vai và nhánh. Chốt file kho, snapshot HUD, quyền cập nhật đơn và thứ tự tick. Hỏi payload event còn thiếu. | Nghĩa, cả nhóm |
| 15–45 | Viết bốn lát gameplay, HUD và test song song. `quan` dùng kho mẫu, HUD dùng snapshot mẫu. Standup phút 20. Hai cặp ghép thử từng mode trước phút 45. | Từng người, Quang ghép `gather`, Nghĩa ghép `quan` |
| 45–55 | Tích hợp lên `main`, chạy test, smoke kho hai tiến trình và chơi thử hai mode. Điền ma trận AC, lưu bằng chứng chạy thật và rà README. | Nghĩa, Quân, Hà |
| 55–60 | Kiểm tra commit bàn giao, đẩy `phase-1`, xác nhận tag trên remote. Nếu còn mục thiếu, ghi kết quả chưa đạt, giữ bản chạy được và chuyển phase đúng giờ. | Nghĩa, Ngọc Quang nhắc mốc |

## Điều kiện bàn giao

- `AC-P1-01` Hai mode chơi được và HUD đủ trường. Kiểm các biên nguy hiểm gồm ngất, giỏ đầy, phục vụ đúng tick hết kiên nhẫn và đóng ca.
- `AC-P1-02` Headless v1.0 giữ kết quả tất định, fixture mâu thuẫn trả mã 2 trước khi tạo output, smoke hai tiến trình bàn giao đúng file kho.
- `AC-P1-03` README có tối đa 3 lệnh chạy từ clone sạch trên macOS/Linux, phím điều khiển, công thức điểm và một lệnh test. Schema kho và ví dụ có chỗ tra cứu.
- `AC-P1-04` Fork public có đủ quyền Write, `TEAM.md` khớp `team_size`, có bằng chứng commit theo người, ma trận kiểm chứng, nhật ký AI, làm rõ yêu cầu và phản tư được cập nhật theo tiến độ.
- `AC-P1-05` Tag `phase-1` trỏ tới commit chạy được trên `main`. Nếu đã thêm sáng tạo, README ghi mục riêng và có test xác nhận headless giữ đúng lõi.

Rủi ro lớn nhất là xử lý sai thứ tự tick và trừ nguyên liệu hai lần. Chốt bảng quyền ghi trong kickoff và giữ smoke kho chạy sớm. Hai hướng mở rộng cho cả lab là trang trí bối cảnh sông/chợ và lời thoại hướng dẫn của Má Tư trong UI. Đưa vào backlog sau khi lõi ổn, ghi nguồn asset và kiểm headless nếu triển khai.

Các phase sau lập lại backlog khi ticket mở. Phase 2 chạy smoke ở phút 20 của phase. Phase 3 có phân tích tác động và ADR. Phase 4 dành thời gian cho benchmark, đóng gói, retro và Release `v1.0.0`. [Repo gốc](https://github.com/VinUni-AI20k/K5-L3B-LAB-Day12-AI-SDLC) · [Lab board](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)
