# Kiểm chứng Phase 3

Kiểm ngày 2026-11-21. Cây tích hợp gồm Day/contract, kho và Gather từ PR #16, Quán do Nghĩa thực hiện với GPT-6 Luna, HUD từ PR #18 và QA từ PR #17. Kết quả chuẩn bị tại commit `e8c7e47` ghi riêng lượt chạy trước khi có runtime v1.2.

| Tiêu chí | Bằng chứng | Kết quả |
|---|---|---|
| AC-P3-01 · Schema và bàn giao kho | `test_inventory_v12` và `test_phase3_integration`. CLI so file kho với `gather_end.data.inventory` và kho Quán tick 0. Kiểm file đếm trả mã 2, giữ đầu ra cũ khi fixture sai, và kho vượt sức chứa giỏ. | Đạt. Smoke trên manifest bàn giao cho cùng `I1 / ca_linh / 99.991666666666667` ở cả ba đầu ra. |
| AC-P3-02 · Luật và ngưỡng | `test_gather_freshness`, `test_quan_freshness` và `test_phase3_integration`. Kiểm vượt ngưỡng, ưu tiên cá thể tươi nhất và ID, thay phần giữ vừa ươn, khóa giá sau hao, ID mới ở Day 2, giữ độ tươi trong Shop và thứ tự LIFO. | Đạt. Hai lượt Day seed 42 kết thúc đúng 22.200 tick và sinh JSONL giống từng byte. |
| AC-P3-03 · HUD và thay đổi schema | [ADR kho](../adr/0001-freshness-inventory.md), [thứ tự tích hợp](../plan/phase-3-tasks.md), `test_live_day` và smoke Playwright tại 1280×720 và 390×700. | Đạt. Gather hiện hàng ươn, Quán lọc hàng đang giữ và hàng ươn. Live Day hiện đơn R1/R2 và đưa giỏ qua Quán khi cập bến. |
| AC-P3-04 · Hồi quy và hồ sơ | [CHANGELOG](../../CHANGELOG.md), [clarify](../clarify.md), [nhật ký AI](../ai-usage-log.md), [retro](../retro.md) và [cách chạy QA](../proof/phase-3/README.md). | 202/202 test với manifest v1.2 và 187/187 test trên cây manifest v1.1. Kiểm danh sách 6 thành viên đạt. |
| AC-P3-05 · Mở rộng và tag | `test_flood_current`, `test_quan_reservations` và `test_phase3_integration`. | Dòng lũ báo trước ở tick 780, bắt đầu tick 900, kết thúc tick 1080. Đặt trước qua test công bố, giữ bàn, đến, xử lý khi thiếu hàng và phục vụ. Mốc bàn giao `phase-3`. |

SHA-256 của JSONL chạy Day seed 42 là `2a2cb3c154961bcdbb9881ec87ea0c051dbc45143f6e26e9c16f111344c40598`.

Dùng mã mở rộng và thông số Dòng lũ nhóm đã chốt ở P3-05. Các ô của preset Phase 2 thiếu bảng gốc vẫn dùng giá trị nhóm đề xuất P2-01. [Các câu hỏi làm rõ](../clarify.md)
