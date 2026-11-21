# Phase 1 · Task theo từng người

[Kế hoạch chung](phase-1.md) · [Danh sách nhóm và thỏa thuận](../../TEAM.md)

Tạo nhánh từ cùng commit `main` sau kickoff. Tên nhánh và file bên dưới xác định ai được sửa. Hai người ghép `step()` nhận commit từ người cùng cặp vào nhánh của mình, chạy test qua entrypoint thật rồi bàn giao một nhánh tích hợp cho mỗi mode. Nếu cần đổi file hoặc chữ ký hàm, báo chủ file và cập nhật kế hoạch trước khi cả cặp tiếp tục.

## Hợp đồng để làm song song

- **File kho.** Gốc có một khóa `items`, ánh xạ bốn mã nguyên liệu hợp lệ tới số nguyên không âm. Bên ghi bỏ lượng 0. `gather_end` bàn giao đúng giỏ cuối, kể cả kho rỗng khi ngất. Runner ghi nguyên tử khi lượt kết thúc. Chạm `--ticks` trước khi kết thúc thì giữ nguyên đường dẫn đích. `quan` nhận file mẫu `{"items":{"bong_sung":2,"ca_loc":1}}` bằng `--inventory`. [Ví dụ kho](../contracts/inventory.sample.json) · [Bộ đọc/ghi starter](../../chonoi/inventory.py)
- **Input và HUD.** UI gửi `move`, `interact`, `catch` qua giao diện live có sẵn và đọc snapshot từ cùng lớp mô phỏng với headless. HUD `gather` đọc `time_left_ticks`, oxy/Máu trong `player`, `hold_count` và `hold_capacity`. HUD `quan` đọc `time_left_ticks`, `stock`, `customers`, `stoves`, `hand`, `money` và `reputation`. Hà dùng snapshot mẫu trước khi hai mode tích hợp. Mô phỏng xử lý cạnh lên của nút tương tác/bắt cá và mọi thay đổi trạng thái. [API live](../../chonoi/live.py) · [Đầu mối payload event](../clarify.md)

### Quyền cập nhật kho, đơn và bếp ở `quan`

Theo starter, `stock` là tồn vật lý. Đề xuất giữ ý nghĩa đó trong headless. **Kho khả dụng theo từng loại bằng `stock[kind]` trừ tổng `customer.reserved[kind]` của các đơn `reserved`**. Nếu khách giữ hai `bong_sung` từ kho mẫu, snapshot vẫn có `stock.bong_sung = 2`, còn HUD hiển thị khả dụng bằng 0. Hà tính phần hiển thị từ snapshot. Các trạng thái `assigned`, `served` và `unfulfillable` có phần giữ rỗng.

| Thời điểm | Ai ghi | Trạng thái sau thao tác |
|---|---|---|
| Nạp fixture | Nghĩa | Dựng tồn vật lý từ file hoặc `scenario.stock`. Cấp phần giữ còn thiếu theo `order_tick`, rồi ID bàn. Kiểm công thức, tổng giữ không quá tồn, liên kết đơn–bếp–tay và timer. Fixture sai trả mã 2 trước khi ghi output. |
| Đến lịch khách, cuối tick | Nghĩa | Dựa trên kho khả dụng để chọn món bằng `Streams`. Ghi đơn `reserved` và phần giữ đúng công thức. Tồn vật lý chưa đổi. |
| `interact` tại bếp idle | Ngọc Quang | Chọn đơn `reserved` cũ nhất, trừ đúng phần giữ khỏi `stock` một lần, xóa phần giữ, chuyển đơn sang `assigned` và đặt payload vào bếp. |
| Bưng và phục vụ | Ngọc Quang | Bếp giao món cho tay trống. Bàn chỉ nhận đúng `order_id`. Khi giao, bàn sang `eating`, đơn sang `served`, tay trống và boa được chốt theo kiên nhẫn còn lại sau khi đếm tick. |
| Ăn xong, hết kiên nhẫn hoặc đóng ca | Ngọc Quang | Tính tiền/uy tín đúng lý do rồi xóa khách khỏi bàn. Xóa phần giữ thô và dọn món thuộc đơn trong bếp hoặc trên tay. Tồn vật lý chỉ đổi lúc bắt đầu nấu. |

Nghĩa là người duy nhất nối `QuanSim.step()`. Sau khi giảm timer ca, kiên nhẫn và ăn, gọi `advance_stoves(sim, events)` để giảm timer nấu, tăng `ready_ticks` cho món đã chín từ đầu tick và chuyển món vừa chín sang `ready`. Sau di chuyển, gọi `interact(sim, events)` khi có cạnh lên. Tiếp đó gọi `settle_customers(sim, events)` để thu tiền, dọn bàn/món và phát `quan_end` nếu hết ca. Nghĩa chỉ xét sinh khách ở cuối tick nếu ca còn giờ. Thứ tự cho phép giao món ngay tick kiên nhẫn về 0 hoặc hết ca.

## Sáu đầu việc

### 1. Hồ Trọng Nghĩa · `Youngboy1609` · `phase1/quan-customers`

**File phụ trách** `chonoi/sim/quan.py`, `chonoi/scenario.py`, `TEAM.md`, `game.contract.json` phần thông tin nhóm, `AGENTS.md`, `docs/clarify.md`, `docs/ai-usage-log.md`.

- [ ] **0–15′** Kiểm quyền Write và tài khoản Git của từng người. Chốt bảng quyền ghi ở trên với Ngọc Quang, cung cấp snapshot mẫu cho Hà, hỏi mục P1-01. Dùng `docs/contracts/inventory.sample.json` cho quán trong lúc `gather` đang viết.
- [ ] **15–45′** Dựng khách fixture và kiểm mâu thuẫn theo mục D. Tính kho khả dụng, dùng `random_customers`, giữ phần đặt chỗ và sinh khách theo `phase_tick`. Chỉ phát `no_dish` khi có bàn trống trong lượt sinh khách và không có món đủ nguyên liệu. Ghép ba hàm của Ngọc Quang vào `step()` theo thứ tự đã chốt.
- [ ] **45–60′** Kiểm chứng snapshot fixture `--ticks 0`, lịch khách khi rút ngắn ca, và hai lần chạy cùng seed. Tích hợp lên `main`, tổng hợp nhật ký AI theo người, cập nhật `AGENTS.md` với lệnh thật, kiểm bằng chứng và đẩy tag. Báo cả nhóm trước khi thay đổi hợp đồng. [AC-P1-01, 02, 04, 05](phase-1.md#điều-kiện-bàn-giao)

### 2. Phạm Đăng Quang · `DanggQuangg` · `phase1/gather-survival`

**File phụ trách** `chonoi/sim/gather.py`.

- [ ] **0–15′** Chốt với Hạnh ba hàm nhận `sim, events`: `advance_nodes`, `try_harvest`, `try_catch`. Quang giữ `GatherSim.step()`, phần cooldown tổng, cập bến và kết thúc lượt.
- [ ] **15–45′** Tính lặn/nổi từ vị trí đầu và cuối tick. Hồi/trừ oxy theo độ sâu cuối tick. Phát event chuyển bề mặt, cạn oxy, ngạt và ngất theo thứ tự. Khi ngất, tạo `lost` theo LIFO, dọn giỏ và kết thúc ngay. Ghép `advance_nodes` đầu tick, `try_harvest` sau nhánh cập bến và `try_catch` trước hết giờ.
- [ ] **Trước 45′** Chạy fixture cạn oxy ở tick `t` và ngạt ở `t+59`, nổi đúng bước đáng lẽ ngạt, ngất rồi ghi kho rỗng. Review bước chọn đối tượng và sức chứa của Hạnh. Gửi nhánh `gather` đã ghép cho Nghĩa. [AC-P1-01 và 02](phase-1.md#điều-kiện-bàn-giao)

### 3. Lương Thị Hồng Hạnh · `hatrang200715` · `phase1/gather-actions`

**File phụ trách** `chonoi/sim/gather_actions.py` mới.

- [ ] **0–15′** Chốt với Quang dữ liệu đọc/ghi của ba hàm. Dùng `sim.nodes`, `sim.fish`, `sim.hold`, `sim.catch_cd_ticks`, vị trí, độ sâu và tuning có sẵn.
- [ ] **15–45′** Giảm timer mọc lại theo ID. Hái nút sẵn gần nhất ở mặt nước. Bắt đàn gần nhất dưới nước khi hết hồi chiêu. Tính cả mép bán kính, hòa theo ID. Chỉ thêm toàn bộ sản lượng khi đủ chỗ. Thiếu chỗ thì giữ nguyên nút hoặc đàn và không đặt lại hồi chiêu. Bàn giao ba hàm cho Quang ghép.
- [ ] **Trước 45′** Kiểm nút mọc lại và hái cùng tick, hai đàn cùng khoảng cách, giữ nguyên đàn khi sản lượng vượt chỗ, lần bắt hợp lệ ở tick hết giờ được ghi vào kho. Review đường `docked` và `fainted` với Quang. [AC-P1-01 và 02](phase-1.md#điều-kiện-bàn-giao)

### 4. Nguyễn Ngọc Quang · `shoxieje` · `phase1/quan-service`

**File phụ trách** `chonoi/sim/quan_service.py` mới.

- [ ] **0–15′** Chốt bảng quyền ghi cùng Nghĩa và dùng khách fixture với `random_customers:false` để làm bếp ngay. Chốt payload món `{order_id,dish_id,base_price}`.
- [ ] **15–45′** Viết `advance_stoves`, `interact`, `settle_customers`. Chọn một đối tượng theo khoảng cách, ưu tiên bếp khi hòa rồi theo ID. Xử lý bếp idle/cooking/ready, tay một món, giao đúng đơn, tính boa, thu tiền, kẹp uy tín và dọn ca theo mục F. Bàn giao hàm cho Nghĩa ghép.
- [ ] **Trước 45′** Chạy fixture giao món ở tick kiên nhẫn về 0, khách ăn xong, khách chờ bỏ đi, và đóng ca có khách ăn. Kiểm món bị dọn khi khách đi, kho chỉ trừ khi bắt đầu nấu và không hoàn nguyên liệu đã nấu. Theo dõi mốc đẩy tag cùng Nghĩa. [AC-P1-01 và 02](phase-1.md#điều-kiện-bàn-giao)

### 5. Trương Thu Hà · `TruongThuHa` · `phase1/hud`

**File phụ trách** `chonoi/web/index.html`, `README.md`, `CREDITS.md` nếu thêm asset.

- [ ] **0–15′** Lấy snapshot mẫu từ hai cặp. Chốt điều khiển WASD/mũi tên, `E`, `Space` và `R` của starter. Dùng kho trống và kho có phần giữ để dựng HUD.
- [ ] **15–45′** Hoàn chỉnh HUD hai mode. Quán hiển thị thời gian, kho khả dụng, món gọi, kiên nhẫn, bếp, món trên tay, tiền và uy tín. Buổi sáng hiện thời gian, oxy, Máu và giỏ. Ghi README cách chạy từ clone sạch tối đa 3 lệnh, phím, công thức `earned + 100 × floor(reputation)`, một lệnh test, schema kho và link file mẫu.
- [ ] **45–55′** Chơi thử hai mode trên browser, thực hiện hái/bắt và một vòng nấu–bưng–giao. Gửi Quân ảnh và commit để đưa vào bằng chứng HUD. Ghi nguồn tài sản nếu có. [AC-P1-01, 03 và 05](phase-1.md#điều-kiện-bàn-giao)

### 6. Nguyễn Minh Quân · `nmqdhtb` · `phase1/qa`

**File phụ trách** `tests/test_phase1_rules.py` mới, `docs/verification/phase-1.md`, `docs/proof/phase-1/`.

- [ ] **0–15′** Đọc test starter và gắn AC cho các ca cần thêm. Dùng `tests/helpers.py` để chạy headless hộp đen. Chuẩn bị fixture độc lập và giữ các test có sẵn.
- [ ] **15–45′** Test biên gather và quan ở các đầu việc trên. Test fixture giữ quá tồn và bếp/tay giữ cùng đơn trả mã 2, không có output. Kiểm `stock` trước và sau nấu, một ca khách giữ nguyên liệu rồi bỏ đi, và hai lần chạy cùng seed cho dữ liệu giống từng byte. Gửi lỗi kèm fixture, tick và dòng event cho chủ file.
- [ ] **45–55′** Chạy suite và smoke bàn giao kho trên ứng viên `main`. Đối chiếu `stock` tick 0 bằng `{"bong_sung":2,"ca_loc":1}`. Ghi SHA bản chạy, lệnh và kết quả đạt/chưa đạt theo AC. Lưu nhật ký `.txt` và kho mẫu thu được vào proof. Repo bỏ qua `.jsonl` theo mặc định, nên trích các dòng cần đối chiếu vào proof `.txt`. [Toàn bộ AC](phase-1.md#điều-kiện-bàn-giao)

## Lệnh ghép và bàn giao

Mỗi người bàn giao commit có nội dung của lát mình trong Phase 1, ghi `docs/members/<handle>.md` và gửi phần nhật ký AI cho Nghĩa. Giữ lịch sử tác giả khi gộp nhánh để đối chiếu tối thiểu 3 commit có nội dung/người trong cả lab. Nhánh ngắn và đọc chéo diff là cách nhóm dự kiến dùng. [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)

```bash
python3 tools/check_team.py
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
PYTHONPATH=tests:. python3 -m unittest test_smoke_p1.Integration -v
```

Trên PowerShell, đặt `$env:PYTHONPATH = 'tests;.'` trước khi chạy hai lệnh `unittest`. Smoke trong `test_smoke_p1.Integration` gọi `gather` và `quan` bằng hai tiến trình đúng Test Contract mục G. Sau khi bổ sung proof, chạy lại suite ở `HEAD` cuối trên `main`. Nghĩa kiểm `git status -sb` và `git rev-parse HEAD`, đẩy `main`, tạo `git tag -a phase-1 -m "Phase 1"`, rồi `git push origin phase-1`. Đối chiếu commit của tag bằng `git rev-parse 'phase-1^{commit}'` và `git ls-remote --tags origin phase-1 'phase-1^{}'`. [Git Tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging#_sharing_tags)
