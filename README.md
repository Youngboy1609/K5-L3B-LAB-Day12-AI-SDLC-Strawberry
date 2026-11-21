# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

## Nhóm Strawberry · Chạy game

**Chạy từ clone sạch (macOS/Linux)**

```bash
git clone https://github.com/Youngboy1609/K5-L3B-LAB-Day12-AI-SDLC-Strawberry.git
cd K5-L3B-LAB-Day12-AI-SDLC-Strawberry
python3 -m chonoi.live --mode gather
```

Mở địa chỉ in ra trong terminal (mặc định http://127.0.0.1:8000/). Đổi `--mode gather` thành `--mode quan` để chơi buổi tối.

**Nối hai buổi qua file kho:** buổi sáng ghi kho vào `kho.json` khi kết thúc lượt, buổi tối nạp lại kho đó.

```bash
python3 -m chonoi.live --mode gather --inventory-out kho.json
python3 -m chonoi.live --mode quan --inventory kho.json
```

**Phím**

| Phím | Tác dụng |
|---|---|
| WASD hoặc mũi tên | Di chuyển |
| E | Hái rau / cập bến (sáng) · tương tác bếp, bàn (tối) |
| Space | Bắt cá |
| R | Chơi lại |
| Esc hoặc P | Tạm dừng / chơi tiếp (máy chủ ngừng bước tick thật, kể cả giờ Shop) |
| 1–9 (ở Shop) | Mua nâng cấp theo thứ tự trong danh sách |

**Chơi cả ngày** dùng lệnh `python3 -m chonoi.live --mode day --days 5`. v1.2 giữ [số đề xuất của nhóm](docs/clarify.md#preset-v11-đề-xuất-cho-p2-01) cho các ô Ticket-02 chưa cung cấp. Màn giới thiệu, kết quả và pause đều dừng mô phỏng.

**Xem thử màn hình bằng dữ liệu mẫu** (khi server đang chạy, hoặc mở thẳng file `chonoi/web/index.html`): thêm `?demo=shop`, `?demo=result`, `?demo=summary`, `?demo=pause`, `?demo=hold` (giỏ theo độ tươi) hoặc `?demo=kho` (kho quán theo độ tươi) vào địa chỉ, ví dụ http://127.0.0.1:8000/?demo=shop. Chế độ này không gửi gì lên máy chủ.

**Điểm:** `score = earned + 100 × floor(reputation)`: tổng tiền kiếm được trong ca, cộng 100 điểm cho mỗi mức uy tín tròn (uy tín làm tròn xuống).

**Chạy test**

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

**Kho v1.2 (độ tươi, Phase 3).** File kho là mảng cá thể, ví dụ `{"items":[{"id":"I1","kind":"ca_linh","fresh":99.99167}]}`. Mỗi nguyên liệu có ID riêng và độ tươi từ 0 tới 100. Độ tươi dưới 30 là ươn, đúng 30 vẫn tươi. File kiểu đếm cũ bị từ chối với mã 2. Lệnh chạy không đổi.

```bash
python3 -m chonoi.live --mode gather --inventory-out kho.json
python3 -m chonoi.live --mode quan --inventory kho.json
```

Cách nhận biết trên màn hình: buổi sáng, dòng giỏ liệt kê từng món kèm độ tươi (ví dụ `cá linh 99.9`); món ươn ghi `ƯƠN`, ô trong giỏ bị mờ và có dấu X, vạch dưới ô chuyển đỏ. Buổi tối, dòng `Còn cấp được` chỉ đếm hàng chưa ươn và chưa có khách giữ; trong ngoặc vuông là tổng tồn, số đang giữ và số ươn. Màn Buổi tối và Shop hiện tổng bàn giao, độ tươi thấp nhất và số món ươn. Với file v1.0/v1.1, HUD vẫn hiện theo số đếm như trước.

Thành viên và phân công: xem [`TEAM.md`](TEAM.md).

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

```bash
git clone <fork-của-nhóm> && cd <fork-của-nhóm>
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # smoke test
python3 -m chonoi.live --mode gather                                # chơi thử trên trình duyệt (tùy chọn)
```

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

### Sáng tạo của nhóm

- **Dòng lũ** (`flood_current`) đẩy người chơi theo dòng khi độ sâu đạt ít nhất 4. Dòng lên mỗi 900 tick, kéo dài 180 tick và báo trước 120 tick. Tốc độ đẩy là 2 đơn vị/giây. Dùng `gather.random_current: false` để tắt lịch hoặc `gather.current_direction: -1` / `1` để kiểm hướng. Xem `test_flood_current`.
- **Đặt trước** (`reservations`) công bố hai đơn theo seed vào buổi sáng của Day. Bàn được giữ từ 30 giây trước giờ đến. Giá món phục vụ đơn đặt trước nhân 1,5 sau khi khóa giá theo độ tươi. Xem `test_quan_reservations` và `test_phase3_integration`.

Mã hai mở rộng và số liệu Dòng lũ là giá trị nhóm chọn cho bản bàn giao. Xem [P3-05](docs/clarify.md).

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
