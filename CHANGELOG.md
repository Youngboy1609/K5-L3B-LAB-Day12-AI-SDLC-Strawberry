# Changelog
## Unreleased

### Phase 3 · Kho cá thể v1.2

- Với `contract_version: "1.2"`, file kho chuyển từ `{"items":{"ca_linh":1}}` sang `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Chọn fresh theo dữ liệu của ca cần thử. Giữ ID khác rỗng và duy nhất trong kho. File đếm đưa vào bản v1.2 trả mã 2.
- Fixture v1.2 dùng mảng cá thể cho `gather.hold` và `quan.stock`. `customers[].reserved` dùng mảng ID từ kho thực tế, ví dụ `["I1"]`. Day tiếp tục nhận kho qua giỏ Gather.
- Quán cấp cá thể tươi nhất và khóa giá theo độ tươi lúc nấu. Snapshot và sự kiện bàn giao mang cùng ID và giá trị fresh.
- Dòng lũ có lịch cảnh báo, lệch vị trí theo hướng và điều khiển fixture. Đặt trước dùng lịch theo seed, giữ bàn và áp giá đơn đặt trước trước khi tính boa.
- Fixture đếm trong các test Phase 1/2 chạy với manifest v1.1 đã lưu. Các kỳ vọng cũ vẫn được kiểm bằng CLI của cây tích hợp. Xem [ADR kho và độ tươi](docs/adr/0001-freshness-inventory.md).
