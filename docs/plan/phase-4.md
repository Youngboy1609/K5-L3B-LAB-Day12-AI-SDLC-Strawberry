# Kế hoạch triển khai Phase 4

[Checklist theo từng người và lệnh smoke](phase-4-tasks.md)

> Agent thực hiện từng lát theo hướng dẫn `superpowers:executing-plans`. Các mục có ô đánh dấu để nhóm theo dõi.

**Mục tiêu** Bàn giao Test Contract v1.3, benchmark, soak 10 Ngày, HUD dễ đọc và Release v1.0.0 từ cùng commit trên `main`.

**Cách ghép** Xuất phát từ tag `phase-3` (`00f7d00`). Dùng mô phỏng và schema v1.2 cho gameplay, kho và JSONL. Benchmark đo trình duyệt. Soak bước một phiên headless qua cả 10 Ngày. Giữ nhánh chung chạy được trong lúc các lát đang làm.

**Công cụ** Python 3, unittest, trình duyệt Chromium cho benchmark, Git và GitHub Releases.

## Chia việc theo file

| Người phụ trách | File và kết quả bàn giao |
|---|---|
| Hồ Trọng Nghĩa (`Youngboy1609`) | `game.contract.json`, `chonoi/contract.py`, cổng version ở `chonoi/headless.py` và `chonoi/live.py`. Ghép benchmark/soak, bật v1.3, họp retro, tổng hợp `docs/clarify.md`, `docs/ai-usage-log.md`, `AGENTS.md` và chốt commit phát hành. |
| Phạm Đăng Quang (`DanggQuangg`) | `chonoi/benchmark.py` và test benchmark. Chạy cảnh Gather thật với seed 42, đo frame trình duyệt trong 30 giây và giao lệnh cùng kết quả đo cho Minh Quân. |
| Trương Thu Hà (`TruongThuHa`) | `chonoi/web/index.html` và kiểm trình duyệt. Giữ cảnh báo thủy quái và oxy có chữ. Thêm dấu hiệu khách sắp giận và nút bật tương phản cao. Chuẩn bị demo. |
| Nguyễn Ngọc Quang (`shoxieje`), Nghĩa nhận thực hiện | `chonoi/soak.py`, `chonoi/sim/day.py`, phần truyền tùy chọn lặp kế hoạch ở `chonoi/runner.py`, `tests/test_phase4_soak.py`. Dùng một phiên Day, ghi kết quả khi Shop đóng. |
| Nguyễn Minh Quân (`nmqdhtb`) | `tests/test_phase4_contract.py`, `docs/verification/phase-4.md`, `docs/proof/phase-4/`. Kiểm CLI từ manifest, 10 Ngày tất định, hồi quy P1–P3 và ma trận theo commit bàn giao. |
| Lương Thị Hồng Hạnh (`hatrang200715`) | `README.md`, `CHANGELOG.md`, `CREDITS.md`, rà `LICENSE` và soạn `docs/release/v1.0.0.md`. Đóng gói source ZIP, thử từ ZIP và clone sạch trên macOS hoặc Linux. |

Đăng Quang và Hà thống nhất điểm bắt đầu đo trong luồng chạy Gather. Minh Quân chạy các PR trên cây ghép trước khi bật v1.3. Mỗi thành viên cập nhật file phản tư có đúng GitHub handle, tối đa 200 từ, kèm bằng chứng. Nghĩa ghi rõ phần thay Ngọc Quang trong nhật ký và ma trận. Lát soak đã được kiểm trên nền v1.2 ở commit `a623026` và sẽ chạy lại sau khi ghép v1.3.

## Việc theo mốc 30 phút

### Phút 0–5 · Chốt giao diện và ca kiểm

- [ ] Chốt `bench_cmd = python3 -m chonoi.benchmark` và `soak_cmd = python3 -m chonoi.soak`. Cả hai nhận seed, tham số độ dài và đường dẫn output như Ticket‑04. Để `contract_version` v1.2 trong lúc ghép.
- [ ] Chốt cách chuyển v1.3 về luật v1.2 tại ranh giới CLI/live để giữ cùng parser fixture, kho, input và runner. Ghi ca kiểm v1.2/v1.3 cùng seed và input cho JSONL giống từng byte.
- [ ] Dùng lại hai mở rộng Dòng lũ và Đặt trước của Phase 3, dẫn test và bằng chứng vào mục “Sáng tạo của nhóm”. Đối chiếu yêu cầu mở rộng tính cả lab. Chỉ đưa phụ đề âm thanh vào phạm vi nếu có hiệu ứng âm thanh thực tế.

### Phút 5–18 · Làm song song

- [ ] **Soak.** Thêm ca Day 5 → 6 xác nhận kế hoạch quay về D1 và giữ tiền, tổng thu, uy tín, cấp nâng cấp và bộ cấp ID. Tạo `DaySession` một lần, bật lặp D1–D5 riêng cho soak, lấy `day` từ sự kiện `shop_end` và điểm từ `end_row()`. Bot hái một lượt rồi về bến để kho có ID thực. Cho Quán và Shop chạy bằng timer chuẩn. Chạy `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` hai lần. So `days`, `days_completed`, `crashes` và `results`, bỏ `duration_s` khi so. Kỳ vọng 10 kết quả, đúng thứ tự, 0 crash.
- [ ] **Benchmark.** Bật live Gather với seed 42 trên localhost trong một Chromium headless, cố định viewport 1280×720. Đo từ lúc điều hướng tới trang game đến khung gameplay đầu tiên và dùng `requestAnimationFrame` lấy khoảng cách khung hình trong đủ 30 giây. Tính trung bình theo số frame/thời gian, lấy nghịch đảo khoảng cách trung bình của 1% khung chậm nhất. Chạy `python3 -m chonoi.benchmark --seed 42 --duration 30 --out bench.json`. JSON có đúng `avg_fps,p1_low_fps,frames,measured_s,load_ms`. Ghi hệ điều hành, trình duyệt và đối chiếu mốc 60 FPS, 30 FPS, 10 giây bằng số đo thật.
- [ ] **HUD.** Đọc trạng thái bằng dữ liệu runtime có sẵn. Kiểm ba fixture thủy quái gần, oxy thấp và khách chờ với kiên nhẫn còn ít. Cả ba cảnh báo phải nhận ra từ chữ/biểu tượng khi bật tương phản cao. Thử tắt/bật và kiểm ở 1280×720 và cửa sổ hẹp. Ghi cách bật chế độ vào README.
- [ ] **Bản chạy.** Chuẩn bị ba lệnh từ clone sạch gồm clone, cd và chạy `python3 -m chonoi.live --mode day`. Ghi môi trường, phím, test, headless, bench và soak. Đối chiếu ảnh, âm thanh, canvas và các tài sản có thật trong cây Git với CREDITS/LICENSE.

### Phút 18–25 · Ghép và nghiệm thu

- [ ] Ghép Day/soak, benchmark và HUD. Chạy smoke các lệnh khi contract lên v1.3 và kiểm kho vẫn là mảng cá thể. Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` và `python3 docs/proof/phase-3/run_regression.py`.
- [ ] Lưu `bench.json`, `soak.json` và bằng chứng cảnh báo cần thiết trong `docs/proof/phase-4/`. Chạy đo từ cây ứng viên. Ghi lệnh, môi trường, kết quả và phần đã đo/chưa đo. Ma trận nối từng AC với bằng chứng. Để log và ZIP dùng thử trong thư mục tạm.
- [ ] Rà hành động retro P2 về payload mẫu và smoke trên cây ghép. Dẫn ca file kho và live Day của Phase 3 để đối chiếu. Ghi một lỗi AI thật, cách nhóm tái hiện, bài học, hành động tiếp theo và người phụ trách.

### Phút 25–30 · Đóng gói và phát hành

- [ ] Chốt ứng viên trên `main` sau khi kiểm bản clone sạch macOS/Linux. Tạo ZIP bằng `git archive --format=zip --prefix=chonoi-1.0.0/ -o <thư-mục-tạm>/chonoi-1.0.0.zip <commit-bàn-giao>`, giải nén rồi chạy theo README.
- [ ] Gắn `phase-4` và `v1.0.0` vào đúng commit bàn giao. Tạo GitHub Release `v1.0.0` với ZIP, điểm mới, cách chạy và giới hạn đã biết. Kiểm SHA của `main` và cả hai tag trên GitHub cùng asset tải được.
- [ ] Demo sau khi hết giờ build. Chơi Gather → Quán → Shop, chạy test, chỉ phân công và bằng chứng đóng góp rồi mở ma trận truy vết. Nếu quay video, MP4 dưới 5 phút.

## Ma trận nghiệm thu dự kiến

| AC | Bằng chứng phải có |
|---|---|
| AC-P4-01 · Contract, bench và soak | Manifest v1.3 có hai lệnh. `bench.json` đúng năm trường. Hai lượt soak 10 Ngày kết thúc đủ, 0 crash và kết quả gameplay giống nhau. |
| AC-P4-02 · Clone sạch và cảnh báo | Smoke macOS/Linux tối đa ba lệnh. Ba cảnh báo và tương phản cao có bằng chứng trình duyệt. |
| AC-P4-03 · Hồi quy và truy vết | Suite P1–P3, so JSONL v1.2/v1.3, ma trận và log bằng chứng khớp commit. |
| AC-P4-04 · Đóng gói | ZIP chạy được, release notes, CHANGELOG, CREDITS, LICENSE và SHA của `phase-4` / `v1.0.0` trên GitHub. |
| AC-P4-05 · Retro và từng thành viên | Retro rà việc P2, dẫn lỗi AI có bằng chứng, đủ sáu phản tư có link đóng góp. |
| AC-P4-06 · Mở rộng cả lab | Dòng lũ và Đặt trước giữ hành vi, có test hồi quy và dẫn bằng chứng từ README. |
