# Changelog
## Unreleased

### Phase 3 · Kho cá thể v1.2

- Khi bật `contract_version: "1.2"`, file kho chuyển từ `{"items":{"ca_linh":1}}` sang `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Chọn fresh theo dữ liệu của ca cần thử. Giữ ID khác rỗng và duy nhất trong kho. File đếm đưa vào bản v1.2 trả mã 2.
- Fixture v1.2 dùng mảng cá thể cho `gather.hold` và `quan.stock`. `customers[].reserved` dùng mảng ID từ kho thực tế, ví dụ `["I1"]`. Day tiếp tục nhận kho qua giỏ Gather.
- Bản tích hợp đổi version khi adapter, Gather, Quán và HUD đã ghép. Dùng tag `phase-2` để chạy lại fixtures v1.1. Xem [ADR kho và độ tươi](docs/adr/0001-freshness-inventory.md).
