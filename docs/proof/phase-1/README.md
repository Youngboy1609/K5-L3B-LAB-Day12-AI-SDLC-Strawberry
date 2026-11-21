# Bằng chứng QA Phase 1

## Lượt bàn giao trên main

Ngày kiểm 2026-11-21 (Asia/Ho_Chi_Minh). Clone sạch fork public tại `96acf29`, Windows và Python 3.11.9. Tag `phase-1` bổ sung tài liệu kiểm chứng trên cùng phiên bản mã và test.

| Kiểm chứng | Kết quả thực tế |
|---|---|
| `$env:PYTHONPATH = 'tests;.'` rồi `python -m unittest discover -s tests` | 79/79 qua. |
| `python -m unittest test_smoke_p1.Integration` | 5/5 qua. |
| `python tools/check_team.py` và kiểm quyền trên GitHub | Đủ 6 người khớp `team_size`. Fork public, năm quyền Write, một quyền Admin. Cả 6 tài khoản có commit trên `main`. |
| Headless dùng hai tiến trình, seed 42 | Hái bông súng ở tick 1 và 3. Kho thực ghi `{"items":{"bong_sung":2}}`, quán nhận đúng ở tick 0. Khách đến tick 120, bắt đầu nấu 121, chín và bưng 361, phục vụ 501, thu tiền 1101, hết ca 1300. Kết quả là 48 nghìn, uy tín 3.2, điểm 348. Hai lần chạy `quan` cho JSONL giống từng byte. |
| Fixture mâu thuẫn | Một đơn `assigned` cùng tồn tại ở bếp và trên tay trả mã 2 trước khi ghi JSONL. |
| Playwright, `gather` ở 1280×720 | Hiện `Oxy 30s`, `Máu 3/3`, `Giỏ 12/12 · Giỏ đầy` và đồng hồ. E tại bến kết thúc với `docked`. |
| Playwright, `quan` ở 1280×720 | Khách chờ và giữ 3 cá linh, 1 bông điên điển. HUD hiện khả dụng 0 cho cả hai loại cùng tồn gốc, trạng thái “đang chờ” và số giây kiên nhẫn. E cạnh B1 phát `cook_started`, bếp sang `cooking`, đơn sang `assigned`. |

Ca headless trên dùng fixture `gather` tại `[20,0]`, hai nút bông súng cùng vị trí, `time_left_ticks:3`, với cạnh E ở frame 0 và 2. `quan` dùng kho sinh từ tiến trình đầu, vị trí `[2,8]`, `time_left_ticks:1300`, cạnh E ở frame 120, 360, 500 và vector di chuyển `[1,-6/7]` từ frame 361 đến 500. Bộ test công khai và HUD đã được kiểm ở phạm vi trên. Không có kết quả bộ chấm ẩn trong lần kiểm này.

## Bằng chứng từ các lượt QA trước

Lượt `b2f749c` trên nhánh `nguyen_minh_quan` dùng Python 3.15. Các file kho và log smoke bên dưới lưu kết quả của lượt đó. Lượt `e6a3f47` chạy lại sau khi ghép `gather` và sửa lỗi bắt trùng đàn.

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
