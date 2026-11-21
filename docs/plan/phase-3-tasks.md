# Phase 3 · Task theo từng người

[Kế hoạch chung và AC](phase-3.md) · [Danh sách nhóm](../../TEAM.md) · Mốc chung `phase-2` (`8d01879`)

Mỗi người tạo nhánh từ cùng mốc và chỉ sửa phần mình phụ trách. Nghĩa đồng bộ các nhánh sau khi adapter vào `main`. Các ca tích hợp v1.2 chạy với manifest ở thư mục tạm đến khi công tắc chính được bật. Ưu tiên smoke ở phút 20.

## Hợp đồng dùng chung lúc kickoff

| Giao diện đề xuất | Đầu vào, đầu ra và trách nhiệm |
|---|---|
| `read_inventory(path, kinds, *, contract_version)` / `write_inventory(path, items, *, contract_version)` | Hạnh giữ chữ ký gọi cũ làm mặc định. Với v1.2, kiểm schema và trả/nhận `list[Item]`. File JSON có đúng khóa `items`. Không mở output khi dữ liệu sai. Ghi qua file tạm cùng thư mục rồi thay thế đúng một lần. |
| `validate_item_list(raw, kinds)` / `new_item(ids, kind, fresh)` | Hạnh trả mảng đã kiểm theo thứ tự đầu vào với fresh chính xác. Cấp ID qua `ids.new("I")`, dùng `ids.reserve` với fixture. Quang dùng cùng một hàm cấp ID cho mỗi đơn vị thu được. |
| `decay_items(items, amount, spoiled_below)` / `item_payload(item)` | Hạnh hao các cá thể đầu bước và trả các cá thể vừa xuống dưới ngưỡng theo ID. Bên gọi phát `spoiled {item_id,kind,location}`. Projection dùng chung cho file và JSONL, không lấy số đã xuất để tính luật. |
| `GatherSim(..., *, day=..., contract_version=...)` / `QuanSim(..., inventory=..., contract_version=...)` | Nghĩa truyền version từ manifest. Giữ ngày số nguyên và allocator xuyên ngày hiện có. `GatherSim.hold` v1.2 là mảng theo thứ tự thu, `inventory_items()` bàn giao mảng chưa mất độ tươi. `QuanSim` nhận mảng và kiểm các giữ chỗ trên kho thật. |
| `hold`/`stock`/`reserved` và sự kiện | HUD đọc cá thể `{id,kind,fresh}` và `reserved: list[str]` cho v1.2. Đếm theo kind từ kho vật lý, lấy kho khả dụng sau khi trừ ID đang giữ và loại dưới ngưỡng. JSONL giữ schema theo version, `lost` giữ LIFO, `cook_started.data.items` sắp kind rồi ID. |

## 1. Hồ Trọng Nghĩa · `Youngboy1609` · `phase3/day-and-version`

**File phụ trách** `game.contract.json`, `chonoi/contract.py`, `chonoi/scenario.py`, `chonoi/headless.py`, `chonoi/runner.py`, `chonoi/sim/day.py`, `AGENTS.md`, `CHANGELOG.md`, `docs/adr/0001-freshness-inventory.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`.

- [ ] **0–7′** Chốt chữ ký với Hạnh, Quang và Hà. Xác nhận hướng kiểm giá P3-01, hỏi P3-02 đến P3-04. Ghi quyết định chạy hai schema song song, chỗ chuyển version, kế hoạch rollback theo manifest vào ADR. Gửi payload mẫu từ bảng trên cho nhóm.
- [ ] **7–15′** Cho v1.2 qua đường chạy Day, pause và các mode độc lập hiện có. Truyền version đến parser inputs, fixture, file kho, `GatherSim`/`QuanSim` và writer. Không đổi schema của v1.0/v1.1. Trong `scenario.py`, dùng validator của Hạnh cho định dạng cá thể và của Ngọc Quang cho liên kết kho lúc dựng Quán. Trong v1.2, giá đã khóa của món quán thường là số nguyên từ 0 tới giá menu. Rà cả validator payload món và khách đang ăn để bỏ yêu cầu giá phải bằng giá menu ở phiên bản này.
- [ ] **15–20′** Bỏ gom count trong Day v1.2. Dùng chung allocator. Giữ ID của mẫu D1, cấp ID mới ở D2+, giữ kind/fresh ban đầu của mẫu. Xử lý tham chiếu lặp lại theo P3-04. Bàn giao cùng tick, Shop giữ kho dư không hao. Khi ngất mở Quán với mảng rỗng. So tick `gather_end` với snapshot Quán, kiểm bản sao kho không tạo thêm cá thể.
- [ ] **23–30′** Ghép nhánh theo thứ tự đã chốt, bật v1.2 khi smoke file/Day cùng đạt. CHANGELOG ghi breaking change, cách đổi fixture và lý do đổi các test cũ. Chốt AC, cập nhật log/retro.
- [ ] **30–35′** Kiểm suite với Minh Quân, merge ứng viên, xác nhận SHA remote và push `phase-3`. Đối chiếu main/tag sau khi push.

## 2. Lương Thị Hồng Hạnh · `hatrang200715` · `phase3/inventory-freshness`

**File phụ trách** `chonoi/inventory.py`, `chonoi/jsonl.py`, `tests/test_inventory_v12.py` mới.

- [ ] **0–7′** Viết test cho file mảng hợp lệ gồm fresh `0`, `30`, `97.5`, `100` và kho rỗng. Từ chối file count, id trùng, id rỗng, kind lạ, bool, NaN/vô hạn và fresh ngoài miền. Giữ test đọc file count bằng v1.1.
- [ ] **7–15′** Làm adapter theo bảng giao diện. Dùng số hữu tỉ chính xác cho fresh và số hao. Test fresh `30` → ươn sau một tick ở Gather. Test `30.025` → một tick Gather → ghi/đọc kho → bốn tick Quán vẫn ở nhánh tươi, bước Quán kế tiếp mới ươn. Cho file và snapshot tick 0 xuất cùng độ chính xác fresh.
- [ ] **15–20′** Kiểm writer giữ file đích khi phát sinh lỗi ghi và xuất sắp `I2` trước `I10`. Chạy `python -m unittest test_inventory_v12 -v`, bàn giao adapter và test cho Nghĩa merge trước.
- [ ] **20–30′** Pair với Đăng Quang và Minh Quân ở smoke file. So giá trị file với snapshot Quán, đảm bảo kho có thể lớn hơn giới hạn giỏ. Nếu có thời gian, giúp Hà kiểm kho quá hạn và nguyên liệu mới trong HUD.

## 3. Phạm Đăng Quang · `DanggQuangg` · `phase3/gather-freshness`

**File phụ trách** `chonoi/sim/gather.py`, `chonoi/sim/gather_actions.py`, `chonoi/sim/gather_monsters.py`, `tests/test_gather_freshness.py` mới.

- [ ] **0–7′** Viết test thứ tự đầu bước, bắt cá hoặc hái tạo nhiều ID, và rơi LIFO khi có hit hoặc ngất. Dùng cá thể fresh `30` để xác nhận `spoiled` tick 1.
- [ ] **7–16′** Hao tươi sau đồng hồ/cooldown/hồi nút và trước di chuyển/ngạt/quái. Hái/bắt cấp fresh 100 cho mỗi đơn vị, giữ nguyên lượng theo tuning. Hàng vừa thu không hao ngay trong tick đó. Giữ thứ tự bến → hái → bắt → hết giờ → cá bơi/sinh.
- [ ] **16–20′** Khi bị hit, `lost` là các cá thể bỏ từ cuối giỏ, kể cả hàng ươn. Khi ngất, bỏ các cá thể còn lại theo LIFO rồi phát `faint` và `gather_end(fainted)` với `{"items":[]}`. Khi cập bến hoặc hết giờ, bàn giao cá thể còn lại. Chạy `python -m unittest test_gather_freshness test_gather_monsters -v`.
- [ ] **20–30′** Ghép với Nghĩa và Hạnh. So `gather_end.data.inventory` với file, kiểm tick-limit giữ file cũ. Báo sớm nếu phát sinh nhu cầu sửa `runner.py` để Nghĩa thực hiện.

## 4. Nguyễn Ngọc Quang · `shoxieje` · `phase3/quan-freshness`

**File phụ trách** `chonoi/sim/quan.py`, `chonoi/sim/quan_service.py`, `tests/test_quan_freshness.py` mới.

- [ ] **0–7′** Viết test hai đơn tranh cùng loại cá thể, hòa độ tươi chọn ID nhỏ hơn, đơn cùng `order_tick` ưu tiên bàn ID nhỏ hơn. Test fixture giữ ID trùng giữa đơn, ID lạ, ID ươn hoặc công thức thiếu đều trả lỗi.
- [ ] **7–16′** Sau đồng hồ/timer, giảm fresh kho thô, phát hết `spoiled` theo ID rồi mới xử lý các phần giữ vừa ươn. Dùng thứ tự và nhánh thiếu hàng đã chốt ở P3-02. Khách thường chỉ được gọi món khi còn đủ cá thể chưa ươn và chưa giữ. Giữ nguyên hành vi hai bếp/bốn bàn.
- [ ] **16–20′** Lúc bắt đầu nấu, tiêu thụ đúng ID giữ, khóa giá theo công thức P3-01 và xuất `cook_started.data.items` sắp kind rồi ID. Giữ giá khóa tới lúc giao và tính boa. Bếp/tay lưu payload món như trước. Kiểm hàm giá với 40k và fresh `100/50` → `30k`. Với 85k, fresh `60/59.99` → `50k`, fresh `60/60` → `51k`. Các số là fresh ngay lúc nấu. Kiểm thanh toán dùng giá đã khóa và giao đúng tick hết kiên nhẫn/đóng ca. Chạy `python -m unittest test_quan_freshness test_quan_service -v`.
- [ ] **20–30′** Pair smoke bàn giao. Đối chiếu toàn bộ giá và trường `reserved` của khách trong JSONL. Nếu câu trả lời về tái cấp đến muộn, báo Nghĩa. Chạy các ca giá đã chốt và kiểm fixture base_price v1.2 nhận giá đã giảm do fresh.

## 5. Trương Thu Hà · `TruongThuHa` · `phase3/freshness-hud`

**File phụ trách** `chonoi/live.py`, `chonoi/web/index.html`, `README.md`, phần bổ sung UI trong `tests/test_live_day.py`.

- [ ] **0–7′** Dùng snapshot mẫu trong bảng giao diện. Chuẩn bị ca giỏ có cá thể fresh `30` và `29.99`, cùng kho có cá thể đang giữ và bị ươn.
- [ ] **7–16′** Live truyền version đúng tới file kho, fixture và phiên Day. HUD buổi sáng hiện loại/độ tươi hoặc nhãn ươn của cá thể trong giỏ. Buổi tối hiện kho vật lý và kho còn cấp được sau khi loại cá thể ươn và ID giữ. EveningIntro vẫn hiện tổng số bàn giao và món nấu được khi kho chuyển sang mảng. Shop hiển thị kho dư giữ nguyên fresh.
- [ ] **16–20′** Chạy `python -m unittest test_live test_live_day test_live_pause -v`. Chơi thử ở 1280×720 với fixture dưới ngưỡng, xác nhận pause đứng yên và độ tươi hiện đúng. Kiểm cửa sổ hẹp để dòng kho đọc được.
- [ ] **20–30′** Chạy lại trình duyệt trên ứng viên đã ghép. Gửi kết quả cho Minh Quân. README cập nhật lệnh chạy và cách nhận biết kho v1.2, chỉ ghi mở rộng có bằng chứng thực tế.

## 6. Nguyễn Minh Quân · `nmqdhtb` · `phase3/freshness-qa`

**File phụ trách** `tests/test_phase3_integration.py` mới, fixture tích hợp cần thiết trong `docs/proof/phase-3/`, `docs/verification/phase-3.md`. Sửa test P1/P2 cũ sau khi chốt lý do cùng chủ file.

- [ ] **0–7′** Ghi SHA nền `8d01879`. Chuẩn bị test ngưỡng, smoke file và smoke trong Day. Giữ tập regression v1.1 chạy với manifest cũ trong thư mục tạm. Không xoá kiểm tra vì đổi version.
- [ ] **7–20′** Kiểm CLI ghi và đọc lại file kho. `fresh:100` ở tick 0 rồi cập bến ở frame 0. Dòng event cuối Gather, file kho và snapshot Quán tick 0 có cùng `I1/kind/fresh` sau hao Gather. Kiểm v1.2 từ chối kho count mã 2. Kiểm `fresh:30` phát đúng `spoiled` ở tick 1. Kiểm Day bàn giao cùng tick, giữ độ tươi tại pha mới, cấp ID mới ở D2, kho Shop không hao.
- [ ] **20–23′** Chạy smoke trên cây đã ghép, báo từng điểm đỏ theo file/payload/tick. Nếu lỗi schema, dừng bật v1.2 và pair cùng lát đang chặn.
- [ ] **23–30′** Thêm ca giữ lại khi hàng vừa ươn, giá `floor` gần biên, LIFO, file đích có sẵn và kết quả tất định hai lần. Chạy full suite. Ma trận ghi lệnh, seed, SHA, AC, số test, kết quả thực tế. Giữ fixture và tóm tắt cần để chạy lại, để JSONL/log thô ở thư mục tạm.
- [ ] **30–35′** Đối chiếu SHA của ứng viên đã kiểm, SHA trên `main` và SHA tag với Nghĩa. Ghi trạng thái từng tiêu chí còn vướng, không đánh dấu đạt chỉ vì có kế hoạch.

## Smoke phút 20 trên Windows

Chạy trên cây tích hợp đã có manifest v1.2 thử. Phần này dùng thư mục tạm để không đưa inventory/JSONL vào bài nộp.

~~~powershell
$env:PYTHONPATH = 'tests;.'
$smokeDir = Join-Path ([IO.Path]::GetTempPath()) ("chonoi-p3-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $smokeDir | Out-Null
'{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":100}],"random_fish":false,"monsters":[]}}' |
    Set-Content -Encoding ascii -Path "$smokeDir\gather.json"
'{"gather":{"hold":[{"id":"I1","kind":"ca_linh","fresh":30}],"random_fish":false,"monsters":[]}}' |
    Set-Content -Encoding ascii -Path "$smokeDir\threshold.json"
'{"frames":[{"tick":0,"interact":true}]}' | Set-Content -Encoding ascii -Path "$smokeDir\inputs.json"
'{"items":{"ca_linh":1}}' | Set-Content -Encoding ascii -Path "$smokeDir\old.json"
python -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario "$smokeDir\gather.json" --inputs "$smokeDir\inputs.json" --inventory-out "$smokeDir\kho.json" --out "$smokeDir\gather.jsonl"
if ($LASTEXITCODE -ne 0) { throw "Gather chưa ghi được file kho" }
python -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory "$smokeDir\kho.json" --out "$smokeDir\quan.jsonl"
if ($LASTEXITCODE -ne 0) { throw "Quán chưa đọc được file kho mới" }
python -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario "$smokeDir\threshold.json" --out "$smokeDir\threshold.jsonl"
if ($LASTEXITCODE -ne 0) { throw "Ca ngưỡng fresh chưa chạy được" }
python -m chonoi.headless --mode quan --seed 42 --ticks 0 --inventory "$smokeDir\old.json" --out "$smokeDir\rejected.jsonl"
if ($LASTEXITCODE -ne 2 -or (Test-Path "$smokeDir\rejected.jsonl")) { throw "Kho v1.1 không bị từ chối đúng cách" }
python -m unittest test_phase3_integration -v
~~~

Ba lệnh đầu trả 0. `kho.json.items` có đúng cá thể `I1,ca_linh` với fresh xấp xỉ `99.99167`. `gather_end.data.inventory.items` và snapshot Quán tick 0 giữ cùng ID/kind/fresh. Event `spoiled` ở tick 1 có `{item_id:"I1",kind:"ca_linh",location:"hold"}`. Phần tích hợp Day kiểm thêm `gather_end` và `phase_start(quan)` cùng tick, `phase_tick:0`, và Quán chỉ bắt đầu hao ở bước sau.

## Mở rộng sau khi lõi xanh

- **Dòng lũ** · Đăng Quang, sau khi nhánh Gather lõi vào `main`. Nhận bảng thông số `interval_ticks,duration_ticks,warning_ticks,min_depth,speed` và mã extension từ Nghĩa. Kiểm `random_current:false`, hướng cố định `-1/1`, pause và đếm tick hoạt động đầu/cuối.
- **Đặt trước** · Ngọc Quang, sau khi nhánh Quán lõi vào `main`. Hai đơn từ seed, hai bàn khác nhau, lượt giữ bàn 30 giây và xử lý trước khách thường. Kiểm đến cùng tick theo ID, các lý do fail, không phạt uy tín lặp, giá nhân 1,5 rồi mới tính boa, và chỉ kiểm thất bại cháy khi có mở rộng cháy. Hà đọc `reservations[]` trong HUD sau khi schema được chốt, Minh Quân kiểm bằng chứng. Nếu lõi vượt mốc phút 20, để cả hai mở rộng sang lượt tiếp theo trên nền tag.
