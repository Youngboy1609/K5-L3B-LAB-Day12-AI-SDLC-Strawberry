# Ma trận truy vết Phase 1

Lượt kiểm lại trên nhánh `DangQuang` sau khi tích hợp phần gather của Hạnh và bộ test của QA.
Commit đã chạy `e6a3f47`. Toàn bộ 79 test đạt. [Nhật ký chạy lại](../proof/phase-1/suite-gather-fix.txt)
AC-P1-03 đến AC-P1-05 giữ kết quả của lượt QA trước, chưa được kiểm lại trong lượt này.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01 | Kiểm luật gather, quan và API live | [Suite mới](../proof/phase-1/suite-gather-fix.txt), [test luật](../../tests/test_phase1_rules.py) | **Đạt phần tự động.** F1 bị xóa ở tick 1, lần bắt lại ở tick 31 không tăng giỏ. Thiếu chỗ vẫn giữ đàn. Tiền thanh toán bằng giá cộng phần nguyên của boa khi đủ ngưỡng. Còn phần chơi thử HUD trên trình duyệt. |
| AC-P1-02 | Chạy lại headless, tất định vòng nấu, fixture lỗi và bàn giao kho | [Suite mới](../proof/phase-1/suite-gather-fix.txt), [kho quan sát](../proof/phase-1/inventory-observed.json) | Các ca đã chạy đều đạt, gồm bắt cá ở tick cuối, xuất kho và từ chối fixture giữ quá tồn. Còn kiểm riêng fixture cùng đơn ở bếp và trên tay. |
| AC-P1-03 | Đọc README và tài liệu starter | [README](../../README.md), [starter](../STARTER.md) | **Chưa đạt đầy đủ**: đã có lệnh chạy/test; README chưa tập hợp phím, công thức điểm, schema kho theo AC. Chưa kiểm clone sạch. |
| AC-P1-04 | Kiểm TEAM/team_size và dấu vết QA | [Team check](../proof/phase-1/team-check.txt), [phản tư QA](../members/nmqdhtb.md) | **Đạt một phần**: 6 thành viên khớp cấu hình. Chưa xác minh public/quyền Write, đóng góp toàn nhóm hoặc email Git liên kết tài khoản. Nhật ký AI chung còn chờ tích hợp. |
| AC-P1-05 | Kiểm tag local và điều kiện bàn giao | [Hướng dẫn bằng chứng](../proof/phase-1/README.md) | **Chưa xác minh bàn giao**: không thấy tag local tại lúc kiểm; chưa kiểm remote. Suite QA còn lỗi, chưa đủ điều kiện xác nhận tag chạy đạt trên main. |

## Lịch sử lượt QA tại b2f749c (trước tích hợp)

- Tổng 49 phương thức test: **33 đạt, 16 chưa đạt**. unittest báo **17 failures** vì test hồi oxy có hai subtest thất bại. Không có error môi trường trong lần chạy ngoài sandbox; test HTTP đạt.
- Gather: tiêu hao/hồi oxy, ngạt/ngất, hái khi cây mọc lại, giỏ đầy và bắt cá tick cuối chưa đạt. Đăng Quang/Hồng Hạnh phụ trách luật tương ứng.
- Quan: lịch khách, no_dish, giữ/trừ nguyên liệu, nấu/chín/bưng, phục vụ/thanh toán và khách bỏ đi chưa đạt. Nghĩa/Ngọc Quang phụ trách luật tương ứng. Test tắt sinh khách đạt, nhưng chưa chứng minh sinh khách hoạt động.
- Không dùng skip/expectedFailure và không sửa gameplay trong các commit QA. Các test mô tả tiêu chí đang chờ triển khai.
- Chưa bao phủ đầy đủ: nổi đúng tick ngạt, hòa khoảng cách theo ID, cooldown bắt cá, giao món đúng tick hết kiên nhẫn, đóng ca có khách ăn và fixture mâu thuẫn đơn hàng. Không coi test hiện có là đủ toàn bộ Phase 1.
- Bước tiếp theo: nhóm đọc chéo test theo PRD, chốt P1-01/schema fixture, hoàn thiện gameplay, bổ sung ca còn thiếu; chạy lại trên ứng viên main, lưu SHA/log mới rồi xác nhận HUD và tag. Không dùng bằng chứng này để tuyên bố gameplay đã hoàn thành.
