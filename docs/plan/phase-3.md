# Phase 3 · Kế hoạch đổi kho và theo dõi độ tươi

**Mục tiêu** Bàn giao Test Contract v1.2 chạy qua file kho và xuyên các pha trong một ngày. Dùng tag `phase-2` (`8d01879`, 112 test đạt) làm mốc. [Việc theo từng người](phase-3-tasks.md) · [Nhóm Strawberry](../../TEAM.md)

**Cách triển khai** Giữ Python và client trình duyệt hiện tại. Chốt một biểu diễn nội bộ cho cá thể nguyên liệu, cho hai schema chạy song song theo `contract_version` trong lúc ghép. Chỉ bật mặc định v1.2 sau khi cả Gather, Quán, Day và HUD cùng chạy trên cây tích hợp.

## Lịch 35 phút

| Phút trong phase | Mốc lab | Việc cần xong | Người chốt |
|---|---|---|---|
| 0–7 | 1:55–2:02 | Chốt schema, biểu diễn số chính xác, payload mẫu và quyền sửa file. Thống nhất test giá đã chốt và xác nhận cách xử lý giữ chỗ bị ươn. | Nghĩa, Hạnh, Ngọc Quang |
| 7–20 | 2:02–2:15 | Ghép adapter và test migration trước. Làm Gather, Quán, Day và HUD song song theo giao diện đã chốt. Smoke file và smoke Day ở phút 20. | Hạnh, Minh Quân, Nghĩa |
| 20–23 | 2:15–2:18 | Standup 2–3 phút. Xử lý ngay lát làm smoke đỏ. Giữ manifest mặc định v1.1 khi hai đầu bàn giao còn lệch. | Cả nhóm |
| 23–30 | 2:18–2:25 | Ghép những lát còn lại, bật v1.2 trên ứng viên, chạy regression P1/P2 còn hiệu lực, kiểm HUD và chốt CHANGELOG, ADR, QA. | Nghĩa, Minh Quân, Hà |
| 30–35 | 2:25–2:30 | Merge ứng viên đã kiểm, xác nhận SHA trên remote `main`, gắn và push `phase-3`. | Nghĩa |

## Tác động của change request

| Ranh giới | Ở tag Phase 2 | Khi chạy v1.2 |
|---|---|---|
| Manifest, loader, CLI | Kho đếm, một số điểm gọi kiểm riêng `"1.1"` | Đề xuất đặt `freshness` ở gốc `game.contract.json` với `{initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25, spoiled_below:30}`. Nghĩa chốt đường nạp và truyền cấu hình qua `contract.py`, `runner.py`, `scenario.py` và hai CLI. Day, pause, Shop và sáu nguyên liệu của v1.1 vẫn dùng được. |
| File kho và fixture | `{"items":{"ca_linh":3}}`, giỏ là mảng kind, giữ chỗ theo số lượng | Kho `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Giỏ/kho dùng cá thể. Khách `reserved` dùng mảng ID tham chiếu kho. File đếm ở v1.2 trả mã 2. Fixture v1.0/v1.1 giữ theo phiên bản cũ để chạy hồi quy. |
| Gather và Day | `hold_to_items()` gom giỏ khi cập bến, ngất hoặc chuyển ca | Giỏ giữ thứ tự lấy để rơi LIFO. Cấp ID một lần cho mỗi cá thể, tiếp tục qua mọi ngày bằng `DaySim.ids`. Chuyển Quán cùng tick, giữ độ tươi và ID đến bước kế. D1 giữ ID fixture. D2+ cấp ID mới theo thứ tự mảng và dùng lại kind/fresh ban đầu. |
| Quán và Shop | Trừ công thức theo count. Shop lưu kho dư theo kind | Kho thô hao trước khi xét bếp. Phát hết `spoiled` theo ID, rồi xử lý giữ chỗ bị ươn. Loại hàng ươn khỏi tập có thể cấp, vẫn giữ vật lý. Bếp tiêu thụ đúng cá thể đã giữ và khóa `base_price` theo công thức P3-01. Shop giữ nguyên độ tươi và bỏ kho dư khi đóng. |
| JSONL, HUD và kiểm thử | Các nhánh HUD có chỗ gọi trực tiếp `Object.keys(stock)` và đếm `hold` như chuỗi kind. JSONL làm tròn float ở xuất. | HUD nhận cả hai dạng theo phiên bản, hiện ID/loại/độ tươi hoặc nhãn ươn. `hold`, `stock` và `reserved` xuất đúng schema. `cook_started.data.items` sắp kind rồi ID, trường `lost` theo LIFO. Phép làm tròn để hiển thị tách khỏi phép so ngưỡng và tính giá. |

## Quyết định đổi schema

- Bộ đọc chọn schema từ `contract_version`. Giữ v1.0/v1.1 trong giai đoạn chuyển và chạy thử v1.2 bằng manifest riêng trong thư mục tạm. Khi bật v1.2, bộ đọc trả mã 2 cho kho count, khóa lạ, ID trùng/rỗng, kind lạ và fresh sai kiểu, ngoài miền hoặc không hữu hạn. Không suy độ tươi hay sinh ID từ file count lúc nạp. CHANGELOG ghi cách sửa fixture cũ bằng ID duy nhất và độ tươi đã biết.
- Biểu diễn nội bộ `Item = {id: str, kind: str, fresh: Fraction}`. Đọc phần thập phân `fresh` chính xác từ JSON, gồm cả số không biểu diễn đúng trên lưới 1/240. Nếu parser dùng `Decimal`, giữ chính xác riêng `fresh` và chuyển các trường số khác về kiểu mà validator hiện tại dùng. Ở 60 tick/s, trừ đúng 1/120 mỗi bước Gather và 1/240 mỗi bước Quán, lấy max với 0. `fresh < 30` là ươn, `fresh == 30` vẫn tươi. Phát `spoiled` đúng một lần lúc từ `>= 30` sang `< 30`. Chốt nhánh bằng số nội bộ, kể cả phép `floor`.
- Dùng chung cách xuất số `fresh` cho file, snapshot và payload. Khi phân số không có dạng thập phân hữu hạn, xuất số JSON với độ chính xác đủ giữ phía ngưỡng và kiểm lại tại bước decay kế tiếp sau khi đọc file. Không đưa fresh qua nhánh làm tròn float 3 chữ số của `chonoi/jsonl.py`. Giỏ luôn giữ thứ tự lấy. File kho dùng `ids.sort_by_id`. Khi mở Quán độc lập, không áp sức chứa giỏ lên file kho.
- Quán ưu tiên cá thể tươi nhất rồi ID nhỏ hơn. Kiểm và đánh dấu các giữ chỗ tường minh trước. Cấp cho đơn thiếu `reserved` theo `order_tick` rồi ID bàn. Giữ chỗ là tham chiếu, không tạo bản sao vật lý. Kiểm đầy đủ công thức, ID tồn tại, hàng chưa ươn và ID chưa thuộc đơn khác. Kiểm quan hệ với kho thật lúc khởi tạo Quán trong Day. Khi sai trả mã 2 và giữ file đích cũ theo quy tắc đang dùng.
- Thứ tự merge **adapter + kiểm migration → Gather + Quán + HUD → tích hợp Day và hai mode CLI → bật manifest v1.2 → kiểm, tag**. Giữ các PR độc lập theo file. Nghĩa ghi quyết định và hệ quả vào `docs/adr/0001-freshness-inventory.md` trước khi bật v1.2.

## Cần chốt trong 7 phút kickoff

- **P3-01 đã chốt cho nhóm.** Lúc bắt đầu nấu, `base_price = floor(menu_price × sum(fresh) / (100 × số cá thể))`. Tính trên đúng cá thể bếp tiêu thụ, sau hao tươi và tái cấp của tick đó. Hai cá thể được tính với trọng số như nhau, kể cả cùng loại. Khóa kết quả từ bắt đầu nấu đến lúc khách trả. Xem ví dụ và nhánh đặt trước ở [clarify](../clarify.md).
- **P3-02** Xác nhận khi phần giữ của khách thường vừa ươn, thứ tự tái cấp, cách giữ lại phần còn tươi, và event/trạng thái nếu không đủ. Hành vi đã rõ là phát toàn bộ `spoiled` theo ID trước khi tái cấp và chỉ chọn cá thể chưa ươn. Ghi kết quả xác nhận và fixture có hai đơn cạnh tranh vào `docs/clarify.md`.
- **P3-03** Ở đầu bước đã có fixture `fresh < 30` thì loại khỏi tập có thể cấp. Xin xác nhận việc có phát event ngay tại khởi tạo hay chỉ phát khi vượt ngưỡng. Các test ở phút 20 dùng trường hợp vượt ngưỡng trong bước, như ví dụ đề.
- **P3-04** Nếu fixture Day lặp lại có `quan.customers[].reserved` trỏ thẳng vào giỏ mẫu, xác nhận D2+ có đổi các tham chiếu theo bản đồ ID cũ → ID mới của giỏ. Nếu áp ánh xạ, chỉ ánh xạ ID thực sự thuộc mẫu ban đầu. ID lạ vẫn trả mã 2. Smoke lặp ngày có thể bỏ `reserved` để kiểm cấp tự động.
- Cả lab nhóm 6 người cần ít nhất hai mở rộng. Ưu tiên lõi 35 phút. Hai ứng viên là **Dòng lũ** và **Đặt trước**. Trước khi nhận làm, Nghĩa lấy mã `extensions` chính thức và thông số `gather.current`. Chỉ khai mã sau khi có test và bằng chứng. Không để các nhánh mở rộng sửa chung file khi lát lõi còn mở. [Việc theo từng người](phase-3-tasks.md#mở-rộng-sau-khi-lõi-xanh)

## Tiêu chí bàn giao

| AC | Bằng chứng và điều kiện đạt |
|---|---|
| AC-P3-01 | File Gather → Quán và bàn giao trong Day giữ ID, kind và fresh. Kho count, ID trùng và trường sai trả mã 2. Xuất kho nguyên tử, giữ file đích nếu chưa kết thúc, ngất xuất mảng rỗng. |
| AC-P3-02 | `spoiled` đúng tick/thứ tự ID. Tái cấp đúng thứ tự, giá chốt đúng công thức P3-01 và đúng phép floor, vật phẩm mất theo LIFO, vết JSONL và HOLD/STOCK trong HUD khớp schema. |
| AC-P3-03 | ADR và phân công ghi tác động, thứ tự merge, cùng mốc bàn giao. Kiểm cả bản chơi và headless trên commit ứng viên. |
| AC-P3-04 | CHANGELOG ghi breaking change và cách đổi fixture. Regression còn hiệu lực đạt, giải thích thay kỳ vọng nếu có. `docs/verification/phase-3.md` nối AC với kết quả và đính bằng chứng cần thiết trong `docs/proof/phase-3/`. Cập nhật clarify, AI log, retro và phản tư cá nhân. |
| AC-P3-05 | Tag `phase-3` trên remote trỏ vào đúng commit `main` đã kiểm trước mốc 2:30. Mục mở rộng chỉ khai nếu qua test và có bằng chứng. |
