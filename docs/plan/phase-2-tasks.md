# Phase 2 · Task theo từng người

[Kế hoạch chung và AC](phase-2.md) · [Danh sách nhóm](../../TEAM.md) · [Câu hỏi dữ liệu chuẩn](../clarify.md)

Giữ starter Python và client trình duyệt. Mỗi file có một người phụ trách. Các nhánh dưới đây là đề xuất, tạo từ cùng mốc bàn giao `phase-1` khi có. Nếu làm trước, giữ riêng commit chuẩn bị từ `main` và đồng bộ lại trước khi tích hợp. Phase 1 và Phase 2 dùng nhánh riêng để giữ rõ regression và tag.

## Hợp đồng tích hợp để chốt lúc kickoff

| Ranh giới | Chủ phần ghi | Chốt dữ liệu và thứ tự |
|---|---|---|
| Manifest và kho | Hạnh, Nghĩa xác nhận | Version `1.1`. Số chuẩn lấy từ bảng gốc. Manifest có sáu nguyên liệu và sáu món. File kho giữ đúng `{"items": {"<kind>": <số lượng>}}`, mở rộng danh sách kind và tiếp tục ghi file cho mode độc lập. |
| `day → gather` | Nghĩa gọi, Đăng Quang ghép | Lượt mới nhận số Ngày, cấp đang áp dụng, fixture và nguồn RNG có seed. Dựng oxy/Máu đầy theo cấp có hiệu lực, đặt giỏ và bố trí quái theo Ngày. Đăng Quang giữ `GatherSim.step()`. Hạnh triển khai hàm cá, Đăng Quang gọi sau khi xét hết giờ. |
| `gather → quan` | Nghĩa gọi, Ngọc Quang nhận | `gather_end` bàn giao object `items` trong bộ nhớ. `fainted` chuyển kho rỗng và vẫn mở quán. Dựng `QuanSim` với kho thực, trạng thái tiền/uy tín và tập ID món trong kế hoạch. Hai mode độc lập vẫn dùng cờ file kho và quán độc lập dùng đủ sáu món. |
| `quan → Shop → ngày mới` | Nghĩa | Cùng tick đóng quán phát `phase_start(shop)`. Shop nhận tiền, earned, uy tín, kho dư và cấp đã mua. Mua tăng cấp ngay trong `upgrades`, chỉ sao sang `active_upgrades` khi dựng Ngày mới. Bỏ kho dư khi đóng Shop, tăng `days_completed` tại đúng bước đó. |
| Runtime → HUD | Nghĩa cung cấp, Hà đọc | Snapshot `day` có kế hoạch, tiến độ, `upgrades` và `active_upgrades`. Khi chuyển pha, snapshot ghi pha mới với `phase_tick:0`, event kết thúc giữ pha cũ. Hà đọc snapshot và sự kiện, hiển thị màn giới thiệu/kết quả của bản chơi. |

**Tick và input.** Session giữ `tick` ngoài, `sim_tick` và `phase_tick`. Một lượt `day` dùng chung trạng thái nút qua các pha. Cạnh pause được xét đầu bước. Bước vào pause chỉ tăng tick ngoài và phát `paused`. Khi pause, mọi timer và lịch đứng yên, bỏ qua buy/cạnh hành động. Cạnh resume phát `resumed` và tiếp tục gameplay ngay bước đó. Lệnh `buy` chỉ chạy ở frame có khai và được xử lý trước `shop_done`, kể cả bước cuối. Shop phát `buy_failed` khi không đủ tiền, đã tối đa hoặc lệnh chưa hỗ trợ. Bỏ qua hành động đúng kiểu ở sai pha hoặc khi extension chưa bật. `day_start → day_plan → phase_start(gather)` giữ đúng thứ tự. Dựng pha mới ở cùng tick, pha đó bắt đầu chơi từ bước kế tiếp. Giữ định dạng JSONL và sắp ID như v1.0.

**Số chuẩn còn thiếu.** Dùng những luật và số đã ghi rõ trong Ticket-02. Chờ bảng gốc cho preset, menu D1–D5, các cấp và giá Shop. Fixture nhỏ để kiểm luồng chuyển pha hoặc dừng timer có thể dùng trước. Gắn nhãn kiểm cấu trúc nếu chưa đối chiếu số chuẩn.

## Sáu đầu việc

### 1. Hồ Trọng Nghĩa · `Youngboy1609` · `phase2/day-session`

**File phụ trách** `chonoi/runner.py`, `chonoi/headless.py`, `chonoi/inputs.py`, `chonoi/scenario.py`, `chonoi/sim/day.py` mới nếu cần tách vòng ngày, `AGENTS.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md` cùng nhóm.

- [ ] **0–8′** Chốt bảng chuẩn với Hạnh. Chốt với hai người ghép gameplay cách truyền stock, tập ID món, cấp đang áp dụng và số Ngày. Cung cấp snapshot/fixture mẫu cho Hà và Minh Quân.
- [ ] **8–20′** Thêm `--mode day`, `--days` chỉ nhận `1–5` cho mode này. Dùng schema fixture v1.1, phạm vi cờ kho theo mode và lần lượt dựng ba pha. Xuất `day_start`, `day_plan`, snapshot đổi pha và `days_completed`; thử smoke chuyển pha bên dưới.
- [ ] **20–42′** Thêm pause cả ba mode, buy một lần theo frame, Shop tự đóng sau 600 tick hoạt động, đóng sớm và nâng cấp hiệu lực từ Ngày sau. Duy trì `0 ≤ money ≤ earned`, uy tín và điểm. Kiểm dữ liệu tĩnh trước khi ghi output, kiểm khách/bếp/món theo kho thực khi mở quán trong `day`. Fixture day cấm `quan.stock` và `quan.reputation`.
- [ ] **42–55′** So timeline cùng Minh Quân, đối chiếu bản chạy UI với Hà, chốt `main`, tổng hợp log và chỉ gắn tag vào commit có bằng chứng. [AC-P2-02, 04, 05](phase-2.md#tiêu-chí-bàn-giao)

### 2. Phạm Đăng Quang · `DanggQuangg` · `phase2/gather-monsters`

**File phụ trách** `chonoi/sim/gather.py`, `chonoi/sim/gather_monsters.py` nếu tách luật Cá Sấu.

- [ ] **0–8′** Đọc `GatherSim.step()` bản đã ghép Phase 1. Chốt với Hạnh cách nạp số Ngày và gọi hàm cá, chốt với Nghĩa dữ liệu fixture quái. Đăng Quang giữ quyền sửa vòng tick `gather`.
- [ ] **8–20′** M1 tuần tra `[60,24] → [64,24]`. Từ Ngày 3 thêm M2 `[85,18] → [89,18]`. `gather` độc lập dùng bố trí Ngày 1. Chặn depth `[10,30]`, patrol 1 m/s, phát hiện khi người chơi ở d ≥ 10 và cách ≤ 10 m, chase 3 m/s. Thoát chase khi cách > 16 m hoặc người chơi lên d < 10. Fixture `monsters[]` thay mặc định và dùng ID đã chốt.
- [ ] **20–42′** Sau bơi/ngạt, cập nhật quái rồi xét tối đa một hit ở bán kính 1,5 m, hòa theo ID. Trừ Máu, rơi `floor(len(hold)/2)` theo LIFO, đặt bất tử 90 tick. Recoil 60 bước từ bước sau, lùi 2/60 m mỗi bước theo hướng xa người chơi đã chốt, dùng +x nếu trùng tâm và chặn biên. Hết Máu thì phát ngất và kết thúc ngay. Ghép thứ tự bến → hái → bắt → hết giờ → cá bơi/sinh. Kiểm biên chase, bất tử và recoil với Minh Quân. [AC-P2-01, 02](phase-2.md#tiêu-chí-bàn-giao)

### 3. Lương Thị Hồng Hạnh · `hatrang200715` · `phase2/fish-and-tuning`

**File phụ trách** `game.contract.json`, `chonoi/contract.py`, `chonoi/inventory.py`, `chonoi/sim/gather_fish.py` mới. Tiếp tục giữ `chonoi/sim/gather_actions.py` nếu cần cập nhật bắt cá.

- [ ] **0–8′** Kiểm các hàm hái/bắt đã ghép trên `main` với Đăng Quang. Cùng Nghĩa đối chiếu bảng P2-01. Hạnh giữ preset. Các lát khác gửi giá trị đã đối chiếu và khóa cần dùng cho Hạnh.
- [ ] **8–20′** Cập nhật manifest/validator theo v1.1 khi có bảng. Thêm `ca_keo` và `keo_neo` vào chỗ đọc kho và validation dùng chung. Giữ cách ghi kho đếm và cách bỏ lượng 0. Chuẩn bị hàm cá với `Streams`, ID và danh sách fixture.
- [ ] **20–42′** Làm tuổi cá, bơi và sinh theo số chuẩn. `random_fish:false` giữ cá fixture đứng yên, tắt cá mặc định và lịch sinh. Khi bật cờ, mảng fixture thay đàn ban đầu và vẫn bơi/sinh. Bàn giao hàm cho Đăng Quang gọi sau bước bắt cá và khi còn giờ. Phối hợp Ngọc Quang kiểm toàn bộ menu/giá/thời gian và Minh Quân kiểm đầu ra tất định. [AC-P2-01, 04](phase-2.md#tiêu-chí-bàn-giao)

### 4. Nguyễn Ngọc Quang · `shoxieje` · `phase2/quan-day-menu`

**File phụ trách** `chonoi/sim/quan.py`, `chonoi/sim/quan_service.py`.

- [ ] **0–8′** Chốt với Nghĩa cách truyền tập ID món từ kế hoạch và stats đầu ca. Giữ hợp đồng `stock`, `reserved`, `order_status`, `patience_ticks_left`, `eat_ticks_left`, `base_price` đã ghép ở P1.
- [ ] **8–20′** Dùng bếp, bàn và menu từ tuning. Kiểm hai bếp, bốn bàn, chọn bàn trống và ID theo PRD. Trong `day`, lọc theo ID món trong kế hoạch trước khi lọc kho khả dụng. Số suất chỉ dùng tính mục tiêu thu gom. Quán độc lập dùng cả sáu món.
- [ ] **20–42′** Kiểm nhiều đơn giữ chung tồn vật lý, chọn đúng đơn, không bán sai món và nhận đủ stats bàn giao. Quán hết ca chốt tiền/uy tín/tiền ca, khách đã phục vụ/bỏ đi và boa để Hà hiển thị. Giữ `quan_end` một lần và thứ tự tick cũ. [AC-P2-01, 02, 04](phase-2.md#tiêu-chí-bàn-giao)

### 5. Trương Thu Hà · `TruongThuHa` · `phase2/day-hud`

**File phụ trách** `chonoi/live.py`, `chonoi/web/index.html`, `README.md`, `CREDITS.md` nếu dùng asset ngoài.

- [ ] **0–8′** Chốt snapshot mẫu và dữ liệu báo cáo cuối ca. Nếu HUD P1 đang ở nhánh riêng, xác định commit làm nền trước khi chỉnh tiếp.
- [ ] **8–32′** Làm menu Chơi/Thoát, DayIntro 4 giây hoặc bỏ qua bằng phím, EveningIntro, DayResult, Shop, pause Esc/P và Summary. Các màn UI đọc trạng thái, hiển thị đúng ngữ cảnh của pha và gửi lệnh qua live. Pause phải tác động vào session để dừng cả Shop. Giữ intro/kết quả ở lớp trình bày để headless chỉ có ba pha gameplay.
- [ ] **32–50′** Rà HUD sáng (oxy, Máu, giờ, sâu, giỏ, cần lấy, hồi bắt, cảnh báo/gợi ý) và HUD tối (giờ, tiền/uy tín, bàn, bếp, tay, kho khả dụng). Chơi thật ở 1280×720, đo FPS và chữ ≥ 18 px, gửi ảnh và kết quả cho Minh Quân. Cập nhật lệnh README cho `day`, giữ hướng dẫn hai mode độc lập. [AC-P2-03, 04](phase-2.md#tiêu-chí-bàn-giao)

### 6. Nguyễn Minh Quân · `nmqdhtb` · `phase2/qa`

**File phụ trách** `tests/test_phase2_*.py`, các test regression P1 cần sửa theo v1.1, `docs/verification/phase-2.md`, `docs/proof/phase-2/`.

- [ ] **0–8′** Đánh dấu nhóm test P1 theo luật còn hiệu lực và theo số/kỳ vọng đã đổi. Test cũ từ chối `day` là ca cần cập nhật vì mode mới. Ghi lý do cho thay đổi tương tự với số bếp/bàn/menu, vị trí hoặc timer khi bảng chuẩn xác nhận chúng đổi.
- [ ] **8–20′** Chạy smoke độc lập bằng hai mode sẵn có và smoke `day` bên dưới ngay khi CLI nhận mode. Ghi SHA, kết quả, tick/snapshot bị lệch, và phần còn chờ module của nhóm.
- [ ] **20–50′** Kiểm pause trong Shop, resume chạy ngay, nút giữ qua pha, chi đủ giá và thiếu tiền, buy trước đóng Shop, áp cấp từ Ngày sau, D1–D5, ngất vẫn sang quán rỗng, cá/quái theo tick, đơn giữ chỗ và `no_dish`. Chạy hai lần cùng seed và so byte. Chạy regression P1, benchmark local, lưu bằng chứng thật và đối chiếu SHA tag. [AC-P2-01 đến 05](phase-2.md#tiêu-chí-bàn-giao)

## Smoke ở phút 20 và kiểm bàn giao

Fixture `p2-day-smoke.json` đặt nhân vật ở vị trí xuất phát mặc định trong bến, quán đóng sau một bước và tắt cá tự sinh. Nếu bảng chuẩn đổi vị trí xuất phát, fixture phải đặt người chơi vào bến đúng tọa độ chuẩn.

```json
{"day":{"money":200,"earned":200},"gather":{"random_fish":false},"quan":{"time_left_ticks":1}}
```

Fixture `p2-day-inputs.json`:

```json
{"frames":[{"tick":0,"interact":true},{"tick":1,"interact":false},{"tick":2,"shop_done":true}]}
```

```bash
python3 -m chonoi.headless --mode day --seed 42 --days 1 --scenario p2-day-smoke.json --inputs p2-day-inputs.json --ticks 3 --snapshot-every 1 --out p2-day-smoke.jsonl
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 tools/check_team.py
```

Kỳ vọng của smoke là `day_start`, `day_plan` và `phase_start(gather)` ở tick 0. Bàn giao quán tick 1, Shop tick 2, đóng Shop tick 3. Snapshot chuyển pha có `phase_tick:0`, dòng cuối `days_completed:1` và `reason:"days_complete"`. Bài kiểm mua nâng cấp dùng giá chính thức sau khi đối chiếu P2-01.

Đo một ngày đầy đủ bằng `--mode day --days 1 --ticks 22200` với một seed ghi rõ, không pause. Lưu thời gian thực, thông số máy, tick cuối và kết quả. Trên PowerShell đặt `$env:PYTHONPATH = 'tests;.'` trước khi chạy unittest. Khi chốt bản bàn giao trên `main`, chạy lại suite, đối chiếu bằng chứng với commit được test rồi xác nhận `phase-2` tồn tại trên remote.
