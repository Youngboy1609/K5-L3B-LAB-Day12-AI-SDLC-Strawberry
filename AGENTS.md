# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test trên macOS/Linux: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Test trên PowerShell: đặt `$env:PYTHONPATH = 'tests;.'` rồi chạy `python -m unittest discover -s tests -v`.
- Headless quán: `python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out quan.jsonl`. Đổi mode thành `gather` để chạy buổi sáng.
- Headless ngày với preset v1.1 đề xuất: `python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out day.jsonl`.
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather`. Mở địa chỉ in ra, dùng WASD, E, Space, R. Đổi mode thành `quan` để thử buổi tối.

- QA Phase 2: `PYTHONPATH=tests:. python3 -m unittest test_phase2_regression test_phase2_day test_phase2_fish -v`. Smoke `day` chạy trực tiếp với manifest v1.1 của repo. Cách chạy ở `docs/proof/phase-2/`.

- QA điều phối Phase 3: `PYTHONPATH=tests:. python3 -m unittest test_phase3_day_version -v`.
- QA Phase 3: `PYTHONPATH=tests:. python3 -m unittest test_phase3_integration -v`. Test v1.2 chạy trên cây tạm. Regression v1.1: `python3 docs/proof/phase-3/run_regression.py`. Xem `docs/verification/phase-3.md`.
- Soak Phase 4: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`. Kiểm riêng bằng `PYTHONPATH=tests:. python3 -m unittest test_phase4_soak -v`.
- Benchmark Phase 4: `python3 -m chonoi.benchmark --seed 42 --duration 30 --out bench.json`. Môi trường đo dùng Playwright và Chromium. Cách chạy và kiểm contract ở `docs/proof/phase-4/`.

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- Phase 1: [quyền sửa file và thứ tự tích hợp](docs/plan/phase-1-tasks.md). Kiểm cấu trúc fixture quán trong `scenario.py`; kiểm liên kết đơn, phần giữ và kho thật khi dựng `QuanSim`, trước khi mở JSONL.
- Phase 2: [quyền sửa file và thứ tự tích hợp](docs/plan/phase-2-tasks.md). `DaySession` điều phối các pha và Shop, `V11Session` xử lý pause ở mode độc lập. Khi ghép live, khởi tạo `LiveInputs(buttons=BUTTONS_V11, allow_buy=True)` để nhận lệnh mua một lần. Headless `day` bàn giao kho trong bộ nhớ và chỉ thay file JSONL đích sau khi chạy thành công.
- Phase 3: [chia file và smoke phút 20](docs/plan/phase-3-tasks.md). Truyền `contract_version` qua CLI, fixture, Day và hai engine. Giữ manifest v1.1 trong lúc ghép các lát kho cá thể và kiểm trước khi bật v1.2. [ADR kho và độ tươi](docs/adr/0001-freshness-inventory.md)
- Phase 4: [kế hoạch](docs/plan/phase-4.md) và [chia file, nghiệm thu, smoke](docs/plan/phase-4-tasks.md). Soak dùng một `DaySession`, lặp mẫu D1–D5 và lấy kết quả khi Shop đóng.
- Cấu hình Phase 2 hiện dùng `tuning.day.day_plans`, `tuning.day.shop_ticks` và `tuning.day.upgrades`. Các giá trị đề xuất trong manifest cần đối chiếu bảng chuẩn [P2-01](docs/clarify.md).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `python3 tools/check_team.py` kiểm cấu trúc `TEAM.md` và quy mô nhóm trước khi nộp.
- `python3 docs/proof/phase-3/run_regression.py` chạy lại test với manifest v1.1 trong thư mục tạm sau khi đổi schema.
