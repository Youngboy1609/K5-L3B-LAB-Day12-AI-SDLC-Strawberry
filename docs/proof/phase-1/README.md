# Bằng chứng QA Phase 1

Ngày: 2026-11-21 (Asia/Ho_Chi_Minh). Mã nguồn đã kiểm: `b2f749ce0db177a583464e18e6102ab6df138edc` trên `nguyen_minh_quan`, Python 3.15. Các file tài liệu/bằng chứng được bổ sung sau lần kiểm, không thay đổi gameplay/test.

## Lệnh chạy lại

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
PYTHONPATH=tests:. python3 -m unittest test_smoke_p1.Integration -v
python3 tools/check_team.py
```

- [Lượt chạy sau tích hợp](suite-gather-fix.txt) ghi 79/79 test đạt tại `e6a3f47`. Ma trận AC giữ tóm tắt lượt QA trước tích hợp.
- `inventory-smoke.txt`: cả 5 smoke tích hợp đạt, exit 0.
- `team-check.txt`: kiểm danh sách 6 thành viên đạt, exit 0.
- `inventory-observed.json`: file kho thực sự do gather xuất, không phải kho mẫu chép tay.
- `inventory-observed.txt`: fixture/input tái hiện, event gather_end và snapshot quan tick 0 lấy từ lần chạy thật.

## Tái hiện bàn giao kho

Lưu fixture và input dưới đây vào hai file tạm ngoài repo:

```json
{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}
```

```json
{"frames":[{"tick":0,"interact":true}]}
```

```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario /tmp/scenario.json --inputs /tmp/inputs.json --inventory-out /tmp/qa-inventory.json --out /tmp/qa-gather.jsonl
python3 -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory /tmp/qa-inventory.json --out /tmp/qa-quan.jsonl
```

Đối chiếu kho `{"items":{"bong_sung":2,"ca_loc":1}}` với `stock` trong snapshot quan tick 0. `test_smoke_p1.Integration` tự tạo fixture bằng thư mục tạm và kiểm quy trình tương tự.

## Phạm vi và giới hạn

Đây là bằng chứng headless/API, chưa có ảnh hoặc kiểm chơi browser. `git tag --list` không trả tag local khi kiểm; không kiểm tag remote hoặc quyền GitHub. Git đang dùng `minhquandhtb <minhquandhtb@gmail.com>`; cần chủ tài khoản xác nhận email này liên kết `nmqdhtb` để GitHub ghi nhận đóng góp.

Các test đỏ được giữ trên nhánh QA để bàn giao cho chủ gameplay. Chưa đẩy hoặc xác nhận tích hợp lên main.
