# Ma trận truy vết Phase 1

Ngày kiểm: 2026-11-21 (Asia/Ho_Chi_Minh). QA: Nguyễn Minh Quân (`nmqdhtb`), có Codex hỗ trợ.
Commit đã chạy: `b2f749ce0db177a583464e18e6102ab6df138edc`, nhánh `nguyen_minh_quan`.
Đây là bằng chứng trên nhánh QA, chưa phải xác nhận bàn giao trên `main` hoặc tag.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | Chạy test luật gather/quan và API live | [Suite](../proof/phase-1/suite.txt), [test luật](../../tests/test_phase1_rules.py) | **Chưa đạt**: 8 phương thức gather và 8 phương thức quan thất bại; luật tương ứng còn TODO. API live đạt nhưng chưa chơi thử và xác nhận HUD trên browser. |
| AC-P1-02 | Smoke headless, tất định, đầu vào sai, bàn giao kho giữa hai tiến trình | [Suite](../proof/phase-1/suite.txt), [5 smoke kho](../proof/phase-1/inventory-smoke.txt), [kho quan sát](../proof/phase-1/inventory-observed.json), [event và snapshot tick 0](../proof/phase-1/inventory-observed.txt) | **Đạt một phần**: smoke kho, test contract hiện có đạt. Kho tick 0 đúng `bong_sung=2, ca_loc=1`. Test tất định vòng nấu chưa đạt vì chưa có món được bưng. Chưa kiểm fixture giữ quá tồn hoặc cùng đơn ở bếp/tay do schema cần chốt. |
| AC-P1-03 | Đọc README và tài liệu starter | [README](../../README.md), [starter](../STARTER.md) | **Chưa đạt đầy đủ**: đã có lệnh chạy/test; README chưa tập hợp phím, công thức điểm, schema kho theo AC. Chưa kiểm clone sạch. |
| AC-P1-04 | Kiểm TEAM/team_size và dấu vết QA | [Team check](../proof/phase-1/team-check.txt), [phản tư QA](../members/nmqdhtb.md) | **Đạt một phần**: 6 thành viên khớp cấu hình. Chưa xác minh public/quyền Write, đóng góp toàn nhóm hoặc email Git liên kết tài khoản. Nhật ký AI chung còn chờ tích hợp. |
| AC-P1-05 | Kiểm tag local và điều kiện bàn giao | [Hướng dẫn bằng chứng](../proof/phase-1/README.md) | **Chưa xác minh bàn giao**: không thấy tag local tại lúc kiểm; chưa kiểm remote. Suite QA còn lỗi, chưa đủ điều kiện xác nhận tag chạy đạt trên main. |

## Đánh giá ngắn

- Tổng 49 phương thức test: **33 đạt, 16 chưa đạt**. unittest báo **17 failures** vì test hồi oxy có hai subtest thất bại. Không có error môi trường trong lần chạy ngoài sandbox; test HTTP đạt.
- Gather: tiêu hao/hồi oxy, ngạt/ngất, hái khi cây mọc lại, giỏ đầy và bắt cá tick cuối chưa đạt. Đăng Quang/Hồng Hạnh phụ trách luật tương ứng.
- Quan: lịch khách, no_dish, giữ/trừ nguyên liệu, nấu/chín/bưng, phục vụ/thanh toán và khách bỏ đi chưa đạt. Nghĩa/Ngọc Quang phụ trách luật tương ứng. Test tắt sinh khách đạt, nhưng chưa chứng minh sinh khách hoạt động.
- Không dùng skip/expectedFailure và không sửa gameplay trong các commit QA. Các test mô tả tiêu chí đang chờ triển khai.
- Chưa bao phủ đầy đủ: nổi đúng tick ngạt, hòa khoảng cách theo ID, cooldown bắt cá, giao món đúng tick hết kiên nhẫn, đóng ca có khách ăn và fixture mâu thuẫn đơn hàng. Không coi test hiện có là đủ toàn bộ Phase 1.
- Bước tiếp theo: nhóm đọc chéo test theo PRD, chốt P1-01/schema fixture, hoàn thiện gameplay, bổ sung ca còn thiếu; chạy lại trên ứng viên main, lưu SHA/log mới rồi xác nhận HUD và tag. Không dùng bằng chứng này để tuyên bố gameplay đã hoàn thành.
