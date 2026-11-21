# Kiểm chứng Phase 4

Ngày kiểm 2026-11-21. Cây chạy `6e3e1ff2088676dc787cd620612649c846976c16` gồm các PR #19–#23, contract v1.3 và điều chỉnh chọn Chromium đã có trên máy. Kết quả QA ban đầu nằm ở [PR #19](https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry/pull/19).

| AC | Bằng chứng | Kết quả |
|---|---|---|
| AC-P4-01 · Contract, benchmark và soak | Chạy hai lệnh khai trong manifest. [bench.json](../proof/phase-4/bench.json) · [soak.json](../proof/phase-4/soak.json) | Benchmark Windows, Chromium 149.0.7827.55, 1280×720. Avg 60,0035 FPS, 1% low 53,9007 FPS, tải 140,5 ms, 1.801 frame trong 30,0149 giây. Hai lượt soak seed 7 đều hoàn tất 10/10 Ngày, 0 crash và các trường gameplay khớp nhau. |
| AC-P4-02 · Bản chạy và cảnh báo | Clone sạch và ZIP giải nén trên Windows, Python 3.11.9. Live trả HTTP 200 và đi Gather → Quán → Shop. Hạnh đã ghi kết quả macOS ở nhánh đóng gói. | Ba cảnh báo có chữ hiện khi bật tương phản cao trên live Gather và Quán ở 1280×720 và 390×700. Kết quả macOS thuộc cây trước khi ghép. WSL Ubuntu trên máy kiểm lỗi khi gắn ổ đĩa. |
| AC-P4-03 · Hồi quy và truy vết | `python -m unittest discover -s tests -v`, `python docs/proof/phase-4/run_v11_regression.py`. [Lệnh tái chạy](../proof/phase-4/README.md) | 217/217 trên v1.3, 197/197 trên cây dùng manifest v1.1. JSONL của Gather, Quán và Day giống từng byte giữa v1.2 và v1.3 với cùng fixture. |
| AC-P4-04 · Phát hành | [CHANGELOG](../../CHANGELOG.md) · [Release notes](../release/v1.0.0.md) · [CREDITS](../../CREDITS.md) | Đã kiểm ZIP giải nén. Còn đẩy tag `phase-4` và công bố GitHub Release `v1.0.0` cùng ZIP. |
| AC-P4-05 · Retro và phản tư | [Retro](../retro.md) · [Clarify](../clarify.md) · [Nhật ký AI](../ai-usage-log.md) · [Phản tư](../members/) | Đã rà lại hành động P2, lỗi truyền version của live Day và cách kiểm. Có sáu hồ sơ cá nhân. Các file của Đăng Quang, Hạnh, Minh Quân và Ngọc Quang còn vượt giới hạn 200 từ khi đếm phần nội dung. |
| AC-P4-06 · Mở rộng | `test_flood_current` và `test_quan_reservations`. [README](../../README.md) | Các test Dòng lũ và Đặt trước qua trong suite v1.3. |

Ca smoke bản Windows kiểm cùng cá thể `I1` khi chuyển Gather sang Quán, sau đó đóng Shop và nhận `days_complete`. Nhóm vẫn cần demo trực tiếp hoặc MP4 dưới 5 phút cho phần trình bày.
