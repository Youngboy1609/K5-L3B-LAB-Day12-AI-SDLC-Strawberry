# Phase 4 · Task theo từng người

[Kế hoạch chung và AC](phase-4.md) · [Danh sách nhóm](../../TEAM.md) · Mốc chung `phase-3` (`00f7d00`)

Phase 4 có 30 phút, từ mốc 2:30 đến 3:00. Mỗi người làm trên nhánh riêng từ mốc chung, gửi SHA và lệnh đã kiểm khi bàn giao. Phần soak đã có hai commit trên `phase4/soak-day`, dùng nhánh đó khi ghép. Các mốc dưới đây tính từ lúc bắt đầu Phase 4.

## Hợp đồng chung lúc kickoff

| Điểm nối | Quy ước và người nhận |
|---|---|
| Version | Nghĩa sửa cổng version ở loader, headless và live. Manifest công bố `1.3`, runtime dùng luật v1.2 cho input, tuning, kho, mô phỏng và JSONL. Minh Quân so JSONL giữa hai bản từ cùng seed và input. |
| Benchmark | Đăng Quang giao `python3 -m chonoi.benchmark --seed 42 --duration 30 --out bench.json`. Đo cảnh Gather thật sau khi vào gameplay. Hà báo nếu đổi luồng mở màn hình hoặc nút “Chơi”. |
| Soak | Nghĩa nhận lát của Ngọc Quang, giao `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`. Kết quả mỗi ngày lấy lúc Shop đóng. Minh Quân đối chiếu hai lượt và bỏ trường thời gian thực khi so. |
| Cảnh báo | Hà đọc snapshot live. Thủy quái gần dựa vào bán kính cảnh báo, oxy thấp dựa vào bộ đếm oxy, khách sắp giận dựa vào trạng thái chờ và số tick kiên nhẫn. Đề xuất dùng 10 giây cuối cho cảnh báo khách. Giữ hành vi đơn đặt trước. |
| Bằng chứng và hồ sơ | Minh Quân giữ quyền ghi `docs/proof/phase-4/` và ma trận. Chủ lát gửi lệnh, SHA, kết quả và đường dẫn tệp đã đo. Hạnh giữ README và release notes. Mỗi người tự viết phản tư theo handle. |
| Đóng gói | Hạnh tạo ZIP theo SHA đã kiểm, Nghĩa phát hành. Xác nhận `phase-4` và tag `v1.0.0` cùng trỏ vào commit bàn giao trên `main`. |

## 1. Hồ Trọng Nghĩa · `Youngboy1609` · `phase4/contract-release`

**File phụ trách** `game.contract.json`, `chonoi/contract.py`, `chonoi/headless.py`, `chonoi/live.py`, `AGENTS.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/Youngboy1609.md`.

- [ ] **0–5′** Chốt đường gọi `bench_cmd` và `soak_cmd` với Đăng Quang và Minh Quân. Thống nhất một cách quy đổi version tại ranh giới, rà các chỗ tải manifest và dựng runtime trong headless, live và soak. Ghi quy ước đo tải trang, ngưỡng cảnh báo khách và phần mở rộng tính cả lab vào clarify.
- [ ] **5–14′** Hỗ trợ manifest v1.3 trên cây thử. Xác nhận tuning mới sử dụng cùng validator v1.2, kho vẫn là mảng cá thể, Day và mode độc lập nhận đúng input và giữ payload JSONL. Case cũ của v1.0/v1.1 chạy với manifest tương ứng. Gửi Minh Quân cách chuẩn bị hai bản v1.2/v1.3 để so theo byte.
- [ ] **14–20′** Đọc diff nhánh soak, benchmark và HUD theo file phụ trách. Chốt thứ tự ghép và bật v1.3 khi hai lệnh chạy được từ cây ghép. Nếu thiếu dữ liệu khi load live Day, kiểm ngay đường truyền version vì đây là chỗ từng lỗi ở Phase 3.
- [ ] **20–25′** Rà retro P2 cùng nhóm. Đối chiếu payload mẫu và smoke qua file/Day đã dùng ở Phase 3, ghi một lỗi AI có bằng chứng, nguyên nhân và việc cần sửa. Tổng hợp nhật ký và xác nhận ai thực hiện lát soak. Kiểm danh sách sáu phản tư, giữ các link commit của từng người.
- [ ] **25–30′** Nhận ma trận đã kiểm từ Minh Quân và ZIP cùng release notes từ Hạnh. Chốt SHA bàn giao, đối chiếu SHA với `main`, tạo hai tag cùng commit và công bố Release v1.0.0. Kiểm tải asset, mở notes và ghi đường dẫn cho nhóm demo.

**Bàn giao** SHA ứng viên đã ghép, cách tái chạy AC, link tag `phase-4`, link Release v1.0.0 và trạng thái từng điểm còn vướng.

## 2. Lương Thị Hồng Hạnh · `hatrang200715` · `phase4/package-docs`

**File phụ trách** `README.md`, `CHANGELOG.md`, `CREDITS.md`, rà `LICENSE`, `docs/release/v1.0.0.md`, `docs/members/hatrang200715.md`.

- [ ] **0–5′** Đối chiếu cây Git để liệt kê asset thật và nguồn. Cây Phase 3 có `CREDITS.md` dạng mẫu và chưa có `LICENSE` riêng được theo dõi. Tra cứu thông tin từ repo gốc, báo Nghĩa nếu thiếu căn cứ về giấy phép. Lấy yêu cầu chạy benchmark từ Đăng Quang và cách bật tương phản từ Hà.
- [ ] **5–15′** Soạn README với quy trình chạy tối đa ba lệnh trên macOS/Linux, yêu cầu Python, phím chơi, test, headless, benchmark và soak. Ghi phụ thuộc đo benchmark tách riêng khỏi đường chạy game. Dẫn test Dòng lũ và Đặt trước trong mục “Sáng tạo của nhóm”. Cập nhật CHANGELOG theo từng phase từ lịch sử có bằng chứng.
- [ ] **15–25′** Thử đúng lệnh README từ clone sạch của cây ứng viên và từ ZIP giải nén, dùng macOS hoặc Linux. Mở trang live và kiểm vào được một lượt chơi. Gửi Minh Quân hệ điều hành, phiên bản Python, lệnh, SHA và kết quả. Nếu thiếu máy macOS/Linux thì ghi rõ nền tảng đã kiểm thực tế.
- [ ] **25–30′** Tạo ZIP từ đúng SHA bàn giao bằng `git archive`, kiểm giải nén có `game.contract.json`, mã chạy, README và hồ sơ cần thiết. Gửi ZIP và notes cho Nghĩa. Notes nêu điểm mới, lệnh chạy và giới hạn có căn cứ từ ma trận.

**Bàn giao** ZIP chạy được, SHA hoặc checksum của ZIP, kết quả clone sạch và `docs/release/v1.0.0.md`.

## 3. Phạm Đăng Quang · `DanggQuangg` · `phase4/gather-benchmark`

**File phụ trách** `chonoi/benchmark.py`, `tests/test_phase4_benchmark.py`, `docs/members/DanggQuangg.md`. Nếu cần marker trình duyệt, thống nhất với Hà để Hà cập nhật `chonoi/web/index.html`.

- [ ] **0–5′** Chốt cảnh Gather thực, seed 42, viewport 1280×720 và một tiến trình Chromium headless. Xác nhận điểm bắt đầu đo là vào trang live, kết thúc load khi có khung gameplay đầu tiên. Rà đường chạy local đã có trước khi để benchmark phụ thuộc vào API mới.
- [ ] **5–14′** Dựng server cổng tạm, mở trình duyệt bằng seed nhận từ CLI, vào game, chờ snapshot Gather hợp lệ rồi lấy thời điểm của các frame trong khoảng đo. Tính FPS theo số frame và thời gian thực. Tính 1% low từ trung bình các khoảng frame chậm nhất, tối thiểu một khoảng. Đóng browser và server bằng cleanup kể cả khi lỗi.
- [ ] **14–18′** Kiểm tính toán với bộ khoảng thời gian mẫu và kiểm đường gọi ngắn tạo đúng năm trường `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`. Kiểm duration không dương được báo lỗi. Gửi Hạnh hướng dẫn cài browser nếu cần cho benchmark.
- [ ] **18–25′** Chạy đủ 30 giây trên ứng viên. Gửi Minh Quân file JSON, SHA, lệnh, hệ điều hành, viewport và phiên bản Chromium. Báo riêng từng mốc đạt/chưa đạt gồm avg ≥ 60 FPS, 1% low ≥ 30 FPS và load ≤ 10 giây. Lưu số đo thực tế vào bằng chứng.
- [ ] **25–30′** Đối chiếu lại bench sau đổi version hoặc HUD. Tạo phản tư `docs/members/DanggQuangg.md` có link commit và ca kiểm cụ thể.

**Bàn giao** Lệnh benchmark chạy được, test tính FPS và file `bench.json` đo từ bản bàn giao.

## 4. Nguyễn Ngọc Quang · `shoxieje` · Lát soak do Nghĩa nhận

**Nhánh và file** `phase4/soak-day`. File `chonoi/soak.py`, `chonoi/sim/day.py`, tham số lặp kế hoạch trong `chonoi/runner.py`, `tests/test_phase4_soak.py`. Phản tư của Ngọc Quang dùng bằng chứng phần bạn đã làm hoặc đã hỗ trợ thật.

- [x] **Chuẩn bị và triển khai** Tạo đúng một `DaySession` cho toàn lượt, bật lặp D1–D5 riêng cho soak và giữ số ngày thực tăng đến 10. Bot đi tới nút hái rồi cập bến. Quán và Shop chạy đến hết timer. Thu `day`, `earned`, `reputation`, `score` khi nhận `shop_end`.
- [x] **Kiểm trước khi ghép** Ca D5 → D6 giữ tiền, tổng thu, uy tín, nâng cấp và ID. Hai lượt CLI seed 7 đều 10/10 Ngày, 0 crash và trùng các trường gameplay sau khi bỏ `duration_s`. Kết quả ở commit local `a623026`, chạy trên nền manifest v1.2.
- [ ] **18–25′** Nghĩa đưa nhánh vào cây ghép. Minh Quân gọi từ `soak_cmd` của manifest v1.3, kiểm đúng năm trường cấp gốc và bốn trường mỗi kết quả ngày. Kiểm đủ 10 kết quả theo thứ tự, 0 crash, so hai lượt. Ghi file `soak.json` từ ứng viên vào hồ sơ.
- [ ] **25–30′** Nghĩa cập nhật nhật ký và ma trận về người thực hiện thực tế. Ngọc Quang gửi phản tư và bằng chứng liên quan tới phần Quán hoặc việc hỗ trợ đã làm để giữ đúng ghi nhận cá nhân.

**Bàn giao** Commit `a623026`, `test_phase4_soak`, hai lượt đo v1.3 và tóm tắt so sánh từ Minh Quân.

## 5. Trương Thu Hà · `TruongThuHa` · `phase4/accessible-hud`

**File phụ trách** `chonoi/web/index.html`, `docs/members/TruongThuHa.md`. Chuyển nội dung README cho Hạnh và fixture/bằng chứng trình duyệt cho Minh Quân.

- [ ] **0–5′** Rà cảnh báo Gather hiện có và bảng khách. Chốt ba trạng thái kiểm gồm trong bán kính thủy quái, oxy dưới 25%, một khách chờ còn ≤ 10 giây. Chuẩn bị ca đối chứng khi ra khỏi bán kính, oxy hồi và khách đang ăn.
- [ ] **5–14′** Bổ sung điều khiển tương phản cao có nhãn rõ, dùng được bằng bàn phím. Áp màu nền/chữ tương phản cho HUD và viền hoặc biểu tượng cho cảnh báo. Hiện khách sắp giận bằng chữ bên cạnh bàn hoặc trong bảng khách. Bảo đảm trạng thái vẫn đọc được khi người chơi phân biệt màu kém.
- [ ] **14–18′** Chơi thử ba cảnh báo khi bật tương phản cao. Kiểm kích thước 1280×720 và 390×700, phản hồi nút bật/tắt, chữ đủ chỗ và pause hoạt động. Giữ cảnh báo ẩn khi hết điều kiện. Gửi bản ghi thao tác và ảnh cần thiết cho Minh Quân.
- [ ] **18–25′** Chạy lại trên tree v1.3 qua Gather → Quán → Shop. Kiểm cảnh báo lúc timer thật đi qua ngưỡng. Gửi Hạnh tên điều khiển và cách bật để README khớp giao diện. Kiểm phụ đề khi có hiệu ứng âm thanh trong bản nộp.
- [ ] **25–30′** Chuẩn bị demo dưới 5 phút nếu quay video. Dùng một lượt có thể đi hết ba pha, trỏ tới số test, phân công và ma trận bằng chứng.

**Bàn giao** PR HUD, kết quả của ba cảnh báo ở tương phản cao, hướng dẫn cho README và kịch bản demo.

## 6. Nguyễn Minh Quân · `nmqdhtb` · `phase4/release-qa`

**File phụ trách** `tests/test_phase4_contract.py`, `docs/proof/phase-4/`, `docs/verification/phase-4.md`, `docs/members/nmqdhtb.md`.

- [ ] **0–5′** Lấy mốc `00f7d00`. Chuẩn bị ma trận AC-P4-01…06 theo [kế hoạch chung](phase-4.md#ma-trận-nghiệm-thu-dự-kiến). Chốt nơi giữ fixture và các tệp bắt buộc để mỗi chủ lát bàn giao đúng chỗ.
- [ ] **5–18′** Viết test chạy theo hai lệnh khai ở gốc manifest. So JSONL Gather, Quán và Day bằng cùng seed, fixture và input giữa v1.2/v1.3. Thử kho đếm phải trả mã 2 và kho cá thể bàn giao giữ nguyên ID/fresh. Kiểm cấu trúc, độ dài và tính lặp của soak. Kiểm benchmark đúng trường, thời lượng và số frame dương.
- [ ] **18–23′** Chạy smoke v1.3 và hai lượt soak ở seed 7. Chạy suite và hồi quy với manifest v1.1. Báo lỗi theo SHA, lệnh, input và sai lệch thấy được để chủ lát sửa. Ghi kết quả cảnh báo dựa trên thao tác thực tế của Hà.
- [ ] **23–27′** Nhận `bench.json` đo đủ 30 giây và `soak.json`. Ghi SHA cây chạy, môi trường, số đo thật, cách so hai lượt và bằng chứng clone sạch. Nếu commit sau chỉ bổ sung bằng chứng, kiểm diff mã/tuning và chạy smoke lại trên commit bàn giao. Giữ JSONL dài, log và ZIP thử ngoài bài nộp.
- [ ] **27–30′** Đối chiếu SHA đã kiểm với Nghĩa, ghi từng AC đạt/chưa đạt và lý do. Kiểm hai tag cùng trỏ vào đúng commit bàn giao và asset Release khớp ZIP đã smoke.

**Bàn giao** Ma trận có kết quả từng AC, số test, lệnh, SHA và link đến bản đo, HUD, clone sạch và Release.

## Smoke phút 20 trên PowerShell

```powershell
$env:PYTHONPATH = 'tests;.'
$smoke = Join-Path ([IO.Path]::GetTempPath()) ("chonoi-p4-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $smoke | Out-Null

python -m chonoi.soak --seed 7 --days 10 --out "$smoke\soak-1.json"
if ($LASTEXITCODE -ne 0) { throw 'Soak lần 1 lỗi' }
python -m chonoi.soak --seed 7 --days 10 --out "$smoke\soak-2.json"
if ($LASTEXITCODE -ne 0) { throw 'Soak lần 2 lỗi' }
$a = Get-Content -Raw "$smoke\soak-1.json" | ConvertFrom-Json
$b = Get-Content -Raw "$smoke\soak-2.json" | ConvertFrom-Json
$gameplay = 'days','days_completed','crashes','results'
if ($a.days_completed -ne 10 -or $a.crashes -ne 0 -or
    (($a | Select-Object $gameplay | ConvertTo-Json -Depth 6) -ne
     ($b | Select-Object $gameplay | ConvertTo-Json -Depth 6))) {
    throw 'Soak chưa đủ 10 Ngày, bị crash hoặc lệch kết quả'
}

python -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out "$smoke\day.jsonl"
if ($LASTEXITCODE -ne 0) { throw 'Day headless lỗi' }
python -m chonoi.benchmark --seed 42 --duration 30 --out "$smoke\bench.json"
if ($LASTEXITCODE -ne 0) { throw 'Benchmark lỗi' }
python -m unittest discover -s tests -v
```

Sau smoke, chạy `python docs/proof/phase-3/run_regression.py` để đối chiếu v1.1. Day seed 42 kết thúc một ngày, benchmark có đúng năm trường và hai lượt soak khớp dữ liệu gameplay. Hà có thể kiểm HUD trên máy khác trong lúc Đăng Quang đo FPS.

## Mở rộng và demo

- Tính Dòng lũ và Đặt trước của Phase 3 vào hai mở rộng của cả lab. Minh Quân kiểm lại `test_flood_current` và `test_quan_reservations`. Hạnh dẫn bằng chứng hiện có trong README. `leaderboard` là việc tùy chọn sau khi bản phát hành đạt các AC lõi.
- Sau 3:00, Hà mở một lượt Gather → Quán → Shop. Minh Quân mở kết quả test và ma trận. Nghĩa chỉ các commit đóng góp và thứ tự ghép. Định dạng có thể là demo trực tiếp hoặc MP4 dưới 5 phút.
