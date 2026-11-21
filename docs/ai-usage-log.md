# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Hồ Trọng Nghĩa (`Youngboy1609`) | Codex, subagent GPT-6 Luna | Triển khai lát khách quán, giữ chỗ nguyên liệu, lịch sinh khách và kiểm fixture trên `phase1/quan-customers`. | Chưa đo. | Rà diff phát hiện fixture món vẫn chấp nhận giá `60.0` vì bằng `60` khi so sánh. Đã thêm test CLI và kiểm kiểu số nguyên theo PRD-0. |
| P1 | hatrang200715 (Hạnh) | Mistral Vibe desktop | Chốt hợp đồng `gather_actions` với Quang, viết `advance_nodes`/`try_harvest`/`try_catch` (`8f45901`), review chéo ghép `DangQuang` `ba4be00` (3 kịch bản headless + suite) | ~2,5M tokens tổng cộng dồn / ~7,6k tokens output thực sinh / ~164k context lớn nhất | AI viết fixture kiểm sai 2 lần (bỏ khối `player` của scenario; đặt player ở mặt nước → catch chặn đúng luật; xuất phát trùng bến → "docked" oan) — phát hiện nhờ chạy thật và đọc output, không tin log
