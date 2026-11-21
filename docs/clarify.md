# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| P1-01 | 2026-11-21 | Mục E có bảng đầy đủ tên event và từng trường `data` cho `gather` và `quan` không, nhất là `served` và `paid`? | Bản PRD-0 đã cung cấp chưa có bảng đầy đủ. Dùng tên ở PRD và starter để ghép nội bộ. Chờ đối chiếu payload trước khi chốt test theo từng trường. | Hồ Trọng Nghĩa hỏi Anh Năm trong kickoff. |
| P1-02 | 2026-11-21 | Đóng ca khi còn khách: khách đang ăn có trả tiền không? Khách đang chờ có bị trừ uy tín không? Cộng uy tín vì boa lúc nào? | Đã đối chiếu PRD-0 mục F. Khách đang ăn trả ngay, khách chờ rời với `closing` và không bị trừ uy tín, kể cả khi vừa hết kiên nhẫn. Boa tính bằng `floor(base_price × tip_rate)` nếu đạt ngưỡng kiên nhẫn khi giao. Cộng uy tín lúc thu tiền nếu boa dương. Trường `reason` của `paid` vẫn đối chiếu ở P1-01. | Ngọc Quang nêu câu hỏi. Nghĩa đối chiếu PRD-0 khi ghép hai lát. |
| P1-03 | 2026-11-21 | Khi kiên nhẫn và giờ đóng ca cùng về 0, xử lý theo lý do nào? Làm tròn boa thế nào? | Theo PRD-0 mục F, `closing` thắng hết kiên nhẫn và không trừ uy tín. Boa dùng `floor`. Khi hai đơn cùng `order_tick`, chọn ID bàn nhỏ hơn. | Ngọc Quang nêu từ review. Nghĩa đối chiếu PRD-0 khi ghép. |
