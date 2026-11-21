# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Hồ Trọng Nghĩa (`Youngboy1609`) | Codex, subagent GPT-6 Luna | Triển khai lát khách quán, giữ chỗ nguyên liệu, lịch sinh khách và kiểm fixture trên `phase1/quan-customers`. | Chưa đo. | Rà diff phát hiện fixture món vẫn chấp nhận giá `60.0` vì bằng `60` khi so sánh. Đã thêm test CLI và kiểm kiểu số nguyên theo PRD-0. |
