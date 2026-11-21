# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| P1 | Hạnh | Chốt hợp đồng 3 hàm `gather_actions` với Quang (5/5 mục OK); viết `gather_actions.py`; review chéo ghép `DangQuang` `ba4be00`: suite 32 test OK + 3 kịch bản headless (`docked`, `fainted`, bắt tick cuối) đều đúng | Quang đẩy nhánh `DangQuang` sau review đúng; chờ ghép gather tích hợp | — |

## Chốt hợp đồng gather_actions (Hạnh ↔ Quang, 2026-11-21)

Quang duyệt các mục 1–4. Mục 5 cần thêm bước xử lý sinh tồn ngay sau move.

1. **advance_nodes** — OK. Hạnh chuyển bộ đếm `regrow_ticks` và event `node_regrown` sang hàm mới. Khi ghép, Quang thay vòng lặp cũ bằng đúng một lời gọi. Nút vừa mọc có thể được hái ngay trong tick đó.
2. **Hồi chiêu bắt cá** — OK. `step()` giảm `catch_cd_ticks` đầu tick. `try_catch()` chỉ đặt lại hồi chiêu khi bắt thành công.
3. **Kiểm tra mặt nước** — OK. Khi E vừa được nhấn, Quang xét cập bến trước, rồi kiểm tra độ sâu sau khi di chuyển trước khi gọi `try_harvest`. Hạnh có thể dựa vào điều kiện này, không kiểm lại trong `try_harvest`.
4. **Thiếu chỗ** — OK. Nếu giỏ thiếu chỗ cho toàn bộ sản lượng, phát `hold_full` một lần, giữ nguyên giỏ và nút hoặc đàn cá, giữ nguyên hồi chiêu.
5. **Thứ tự chốt trong `step()`** — giảm bộ đếm → `advance_nodes` → di chuyển → oxy/ngạt/ngất → cập bến → `try_harvest` → `try_catch` → hết giờ. Ngất kết thúc tick ngay. Nếu vẫn chơi, lượt bắt hợp lệ ở tick cuối được tính vào kho.
