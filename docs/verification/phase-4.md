# QA Phase 4 — Nguyễn Minh Quân (`nmqdhtb`)

Ngày kiểm: 2026-11-21. Mã được kiểm: `3ffa2cfc38b4b9b5d73b66e9c7fcb3c5e410300a` cộng các tệp QA chưa commit trong lần bàn giao này. Đây là QA trước tích hợp, chưa nghiệm thu Release. Không sửa manifest, runtime hoặc test của các lát khác.

Môi trường: macOS 26.6 arm64, Python 3.15.2. Ba test HTTP cần được phép mở cổng localhost; lượt sandbox ban đầu lỗi `PermissionError`, lượt chạy lại ngoài sandbox không còn lỗi HTTP.

## Kết quả thực chạy

| Kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Suite sau thêm QA P4 | 207 phương thức; 202 đạt, 5 phương thức P4 chưa đạt (7 failure tính subtest), không error | [full.log](../proof/phase-4/full.log) |
| QA P4 riêng | 5 phương thức, 7 failure; không skip | [phase4.log](../proof/phase-4/phase4.log) |
| Hồi quy v1.1 | 187/187 đạt, cây tạm loại test nghiệm thu v1.3 | [regression-v11-isolated.log](../proof/phase-4/regression-v11-isolated.log) |
| Dòng lũ + Đặt trước | 14/14 đạt | [extensions.log](../proof/phase-4/extensions.log) |
| Đối chứng fixture kho trên v1.2 | 1/1 đạt; cùng ca bàn giao ID/fresh và từ chối kho đếm | [v12-positive.log](../proof/phase-4/v12-positive.log) |

## Ma trận nghiệm thu

| AC | Trạng thái | Bằng chứng và phần còn thiếu |
|---|---|---|
| AC-P4-01 | Chưa đạt | Manifest vẫn v1.2, thiếu `bench_cmd`/`soak_cmd`; chưa có module benchmark/soak trong cây. Chưa thể tạo số đo thật hoặc so hai lượt 10 Ngày. |
| AC-P4-02 | Chưa nghiệm thu | Chưa nhận bằng chứng ba cảnh báo, tương phản cao ở hai viewport từ Hà; chưa nhận clone sạch từ Hạnh. Test HTTP đạt chỉ chứng minh API live. |
| AC-P4-03 | Đạt phần hồi quy, chưa đạt toàn bộ | Suite cũ 202 đạt, v1.1 187 đạt. Ba ca so JSONL chạy v1.2 thành công rồi dừng ở validator v1.3; chưa so được byte. |
| AC-P4-04 | Chưa nghiệm thu | Chưa có SHA phát hành, ZIP smoke hoặc xác minh tag/asset remote trong lượt này. Nghĩa/Hạnh bàn giao để QA kiểm tiếp. |
| AC-P4-05 | Chưa nghiệm thu | Phản tư Quân được bổ sung; retro P4 còn mẫu trống. Chưa xác minh đủ sáu phản tư và đóng hành động P2. |
| AC-P4-06 | Đạt test, thiếu hồ sơ | 14 test Dòng lũ/Đặt trước đạt; cần Hạnh dẫn bằng chứng trong README bàn giao. |

## Lỗi gửi chủ lát

- Nghĩa: `game.contract.json` chưa lên v1.3, chưa có hai command. Chạy `PYTHONPATH=tests:. python3 -m unittest test_phase4_contract -v` để tái hiện.
- Nghĩa: khi chỉ đổi version sang v1.3 trên cây tạm, cả Gather/Quán/Day và bàn giao kho trả mã 2: `tuning.gather.nodes.N5: kind phải là một trong ('bong_dien_dien', 'bong_sung')`. Cổng version chưa dùng validator/runtime v1.2. Fixture v1.2 của ba mode đã chạy thành công trước bước v1.3.
- Đăng Quang/Nghĩa: cần ghép benchmark/soak rồi chạy lại bằng command của manifest. Không dùng số đo từ cây khác thay cho ứng viên.
- Khi bật v1.3, rà helper `run_legacy_headless` (hiện chỉ chuyển cây tạm khi version đúng `1.2`) và test P3 ghim version `1.2`; chủ tích hợp cập nhật tính tương thích có lý do, không sửa để che lỗi gameplay.

## Giới hạn test

Test P4 so 5 tick mỗi mode, có kho cá thể và chuyển Gather → Quán → Shop; không thay thế soak dài. Soak kiểm năm trường gốc, bốn trường mỗi ngày, thứ tự 1–10 và tính lặp; tên ba trường kết quả ngày ngoài `day` cần đối chiếu Ticket-04 khi được bàn giao (repo chưa có bản gốc). Benchmark kiểm schema/thời lượng/số frame; ngưỡng 60 FPS, 1% low 30 FPS, load 10 giây phải ghi theo số đo và môi trường thật. Chưa xác minh giao diện trình duyệt, ZIP hay GitHub Release.
