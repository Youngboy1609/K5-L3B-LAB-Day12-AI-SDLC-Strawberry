# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| P1-01 | 2026-11-21 | Mục E có bảng đầy đủ tên event và từng trường `data` cho `gather` và `quan` không, nhất là `served` và `paid`? | Bản PRD-0 đã cung cấp chưa có bảng đầy đủ. Dùng tên ở PRD và starter để ghép nội bộ. Chờ đối chiếu payload trước khi chốt test theo từng trường. | Hồ Trọng Nghĩa hỏi Anh Năm trong kickoff. |
| P1-02 | 2026-11-21 | Đóng ca khi còn khách: khách đang ăn có trả tiền không? Khách đang chờ có bị trừ uy tín không? Boa ăn vào uy tín lúc nào? | Giả định lát 4: khách đang ăn trả `price + tip` (event `paid`, `reason:"closed"`); khách chờ ra về (`customer_left`, `reason:"closed"`), không trừ uy tín; món của họ bị dọn (`dish_discarded`). Boa chốt lúc `served` nếu kiên nhẫn còn lại ≥ `tip_min_patience_ratio`, cộng `tip_reputation` lúc `paid`. Đổi được trong `chonoi/sim/quan_service.py` khi PO trả lời. | Ngọc Quang đề xuất, chờ Nghĩa/Anh Năm chốt. |
