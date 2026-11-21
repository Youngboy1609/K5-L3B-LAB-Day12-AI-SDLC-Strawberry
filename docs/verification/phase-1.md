# Ma trận truy vết Phase 1

Lượt bàn giao trên `main` ngày 2026-11-21. Mốc mã đã kiểm trên clone sạch là `96acf29`. Commit gắn tag `phase-1` bổ sung ma trận và bằng chứng, giữ nguyên mã và test đã kiểm. [Kết quả và lệnh tái hiện](../proof/phase-1/README.md#lượt-bàn-giao-trên-main)

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | Chạy bộ test luật và chơi thử hai mode qua browser ở 1280×720 | [Test luật](../../tests/test_phase1_rules.py), [kết quả HUD](../proof/phase-1/README.md#lượt-bàn-giao-trên-main) | **Đạt trong phạm vi đã kiểm.** Suite 79/79. HUD sáng hiện giờ, Máu, oxy và giỏ đầy. HUD tối trừ đúng nguyên liệu đã giữ, hiện món, kiên nhẫn, bếp và món trên tay. E cập bến hoặc khởi động bếp theo mode. |
| AC-P1-02 | Chạy hai tiến trình headless, đối chiếu JSONL, file kho, lỗi fixture và tính tất định | [Lượt bàn giao](../proof/phase-1/README.md#lượt-bàn-giao-trên-main), [kho quan sát](../proof/phase-1/inventory-observed.json) | **Đạt các ca đã chạy.** Smoke kho 5/5. Quán nhận rau đã hái và thu 48 nghìn. Hai lượt cùng seed cho JSONL giống từng byte. Fixture bếp và tay cùng giữ một đơn trả mã 2 trước khi ghi output. Payload chưa có trong bản PRD-0 vẫn theo dõi ở [P1-01](../clarify.md). |
| AC-P1-03 | Đọc hướng dẫn và khởi chạy repo mới clone | [README](../../README.md), [ví dụ kho](../contracts/inventory.sample.json) | **Đạt nội dung hướng dẫn.** README có ba lệnh từ clone sạch, phím, công thức điểm, lệnh test, schema và kho mẫu. Đã chạy trên clone sạch bằng Windows/Python 3.11.9. macOS/Linux chưa được thử trực tiếp. |
| AC-P1-04 | Đối chiếu fork, collaborator, TEAM, lịch sử commit và nhật ký | [TEAM](../../TEAM.md), [dấu vết nhóm](../proof/phase-1/README.md#lượt-bàn-giao-trên-main), [nhật ký AI](../ai-usage-log.md) | **Đạt một phần.** Fork public có năm thành viên quyền Write và một trưởng nhóm quyền Admin. Cả 6 tài khoản có commit trên `main` và khớp `team_size`. Repo hiện có 2/6 bản phản tư. Nhật ký AI chung chưa phủ đủ các thành viên. |
| AC-P1-05 | Đối chiếu tag remote với commit bàn giao trên `main` | [Tag phase-1](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/tree/phase-1), [bằng chứng](../proof/phase-1/README.md#lượt-bàn-giao-trên-main) | **Đạt về bản bàn giao kỹ thuật.** Tag trỏ tới commit trên `main` chứa ma trận và bản chạy đã kiểm. Mốc thời gian 1:00 chưa được xác nhận. |

## Lịch sử lượt QA tại b2f749c (trước tích hợp)

Lượt QA đầu trên `nguyen_minh_quan` có 33/49 phương thức đạt khi luật hai mode còn thiếu. Sau tích hợp, PR #6 giữ các test ban đầu và bổ sung ca bắt lại cùng đàn. [Kết quả trung gian `e6a3f47`](../proof/phase-1/suite-gather-fix.txt)
