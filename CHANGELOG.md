# Changelog
## Unreleased

### Phase 4 · Đóng gói v1.3 (so sánh hai bản, soak)

- Manifest công bố `contract_version: "1.3"` nhưng runtime vẫn dùng luật v1.2 cho input, tuning, kho, mô phỏng và JSONL; cách so hai bản v1.2/v1.3 theo byte từ cùng seed do QA giữ. (nhánh `phase4/contract-release`, `fe7f39f`)
- CLI mới `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`: một `DaySession` duy nhất cho cả lượt, lặp D1–D5 đến 10 ngày, thu `day, earned, reputation, score` lúc `shop_end`, hai lượt cùng seed trùng dữ liệu gameplay. (`a623026` trên `phase4/soak-day`, đã ghép `adaaf3a`)
- CLI benchmark FPS cảnh Gather (nhánh `phase4/gather-benchmark`, ghép cùng Phase 4); lệnh xem [README](README.md).
- HUD tương phản cao và ba cảnh báo (lát `phase4/accessible-hud`); README mô tả theo bảng hợp đồng Phase 4, cần khớp lại tên điều khiển khi nhánh ghép.
- README, `CREDITS.md` và [`docs/release/v1.0.0.md`](docs/release/v1.0.0.md) soạn cho Release v1.0.0 (lát `phase4/package-docs`).

### Phase 3 · Kho cá thể v1.2

- Với `contract_version: "1.2"`, file kho chuyển từ `{"items":{"ca_linh":1}}` sang `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Chọn fresh theo dữ liệu của ca cần thử. Giữ ID khác rỗng và duy nhất trong kho. File đếm đưa vào bản v1.2 trả mã 2.
- Fixture v1.2 dùng mảng cá thể cho `gather.hold` và `quan.stock`. `customers[].reserved` dùng mảng ID từ kho thực tế, ví dụ `["I1"]`. Day tiếp tục nhận kho qua giỏ Gather.
- Quán cấp cá thể tươi nhất và khóa giá theo độ tươi lúc nấu. Snapshot và sự kiện bàn giao mang cùng ID và giá trị fresh.
- Dòng lũ có lịch cảnh báo, lệch vị trí theo hướng và điều khiển fixture. Đặt trước dùng lịch theo seed, giữ bàn và áp giá đơn đặt trước trước khi tính boa.
- Fixture đếm trong các test Phase 1/2 chạy với manifest v1.1 đã lưu. Các kỳ vọng cũ vẫn được kiểm bằng CLI của cây tích hợp. Xem [ADR kho và độ tươi](docs/adr/0001-freshness-inventory.md).

### Phase 2 · Day, cá bơi, HUD ngày

- Phiên Day nối Gather → Quán → Shop: `778e196` (`chonoi/sim/day.py`), Shop đọc nâng cấp thật, HUD chạy `--mode day` (`354c395`), pause Esc/P dừng tick thật (`d4f903c`).
- Cá bơi và sinh đàn: `maybe_spawn_fish` + `age_ticks` (`b1d6be9`); `GatherSim(..., advance_fish=...)` seam cho Phase 3; giữ age v1.1 và chặn nguyên liệu mới theo version (`cda6b26`).
- Preset v1.1 tạm thời cho các ô Ticket-02 chưa cung cấp (`389d51a`); quái vật bám quy tắc chạm và đẩy lùi (`844074a`).

### Phase 1 · Luật Gather đầu tiên

- `advance_nodes`, `try_harvest`, `try_catch` theo hợp đồng chốt với quan sát viên thứ hai — `860597a` (hợp đồng 5/5 mục), `8f45901` (lát 2): bộ đếm mọc lại + event `node_regrown`, hồi chiêu bắt cá chỉ đặt lại khi bắt được, `hold_full` phát một lần.
- Quy tắc sinh tồn (oxy, ngộp nước, ngất) — `08ce87e`; sự kiện thu hoạch đọc hệ số từ hợp đồng, không hard-code (`a6ffbe3`); tránh bắt trùng cá (`e6a3f47`).
- README có cách chạy từ clone sạch, phím, công thức điểm (`a43581d`); ma trận nghiệm thu ở [`docs/verification/`](docs/verification).
