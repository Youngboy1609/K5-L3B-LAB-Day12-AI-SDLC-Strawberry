# Ma trận kiểm chứng Phase 2

Nguyễn Minh Quân chuẩn bị QA, Hồ Trọng Nghĩa kiểm khi tích hợp (2026-11-21).
Kết quả dưới đây dùng preset v1.1 đề xuất, chờ đối chiếu bảng Ticket-02 chính thức.

| AC | Kiểm chứng | Kết quả hiện tại |
|---|---|---|
| AC-P2-01 | Manifest sáu nguyên liệu/món, cá, Cá Sấu, thứ tự tick | Manifest đề xuất có sáu nguyên liệu, sáu món, hai bếp, bốn bàn. Suite kiểm cá bơi/sinh, tuổi cá, Cá Sấu, recoil và ngất bàn giao kho rỗng. Đối chiếu số liệu chính thức theo P2-01. |
| AC-P2-02 | `tests/test_phase2_day.py`, fixture smoke 3 tick | Smoke ba tick và lượt chạy đủ D1–D5 đều dùng manifest của repo. Mua oxy và Máu đủ đúng giá, cấp áp vào D2, Cá Sấu M2 xuất hiện từ D3. |
| AC-P2-03 | HUD, FPS, chữ, benchmark một ngày | Playwright ở 1280×720 chạy đủ hai ngày với manifest đề xuất và fixture rút ngắn ca tối, gồm pause Gather/Shop, mua nâng cấp và trường hợp không đủ món. Đo ngắn khoảng 166 FPS trong Gather, bản hẹp 390 px không tràn khung. Headless đủ 22.200 tick mất trung vị 0,522 giây ở máy local. Playwright cũng kiểm cảnh báo cạn oxy và Cá Sấu, mức tăng uy tín cuối ca và món bán chạy. Số đo máy chấm còn chờ. |
| AC-P2-04 | Regression P1, kiểm tất định, test mới | Bản bàn giao preset đề xuất đạt 112/112 test, tag phase-1 đạt 79/79. Ba lần chạy day cùng seed 42 cho cùng SHA-256. |
| AC-P2-05 | Tag remote trỏ commit main đã kiểm | Bản bàn giao trên main dùng tag phase-2. Các giá trị đề xuất và khóa sự kiện còn mở được ghi trong docs/clarify.md. |

Lượt QA trước tích hợp có **79/79 test P1 đạt** và **80/81 test toàn suite**.
Smoke day khi đó dừng ở CLI do chưa có `--days`. Hai mode độc lập cho JSONL
giống byte khi chạy lại cùng seed/input.

Trên bản ghép QA với main 718cf26, unittest discovery đạt **100/100** và
kiểm tra roster đạt **6 thành viên**. Smoke ba tick dùng preset v1.1 riêng.

[Fixture và hướng dẫn chạy lại](../proof/phase-2/README.md).

Smoke dựa đúng fixture trong `docs/plan/phase-2-tasks.md`: cần spawn mặc định
nằm trong bến; đối chiếu lại khi bảng chuẩn thay đổi. Kiểm thứ tự ba event khởi
đầu, snapshot pha mới ở tick 0/1/2 có phase_tick 0, event kết thúc giữ pha cũ,
và end tick 3 có days_completed 1, reason days_complete. Chưa chốt payload
chi tiết của day_plan hoặc phase_start khi tài liệu chưa định nghĩa đủ.

## Rà regression trước khi tích hợp v1.1

| Kỳ vọng hiện tại | Xử lý khi tích hợp |
|---|---|
| `test_con_03_modes_outside_current_contract_rejected` | Từ chối river ở cả hai phiên bản, từ chối day ở v1.0. Ca v1.1 kiểm day thực tế. |
| Snapshot gather mặc định: vị trí [2,0], sáu đàn cá | Đối chiếu bảng chuẩn rồi ghi lý do thay kỳ vọng. |
| Fixture bếp/bàn/menu, kind kho và giá/thời gian v1.0 | Rà lại với tuning chính thức; không thay test chỉ để xanh. |
| Thứ tự tick, cạnh nút, giữ chỗ/trừ kho, đóng ca P1 | Giữ regression trừ khi có quy tắc v1.1 thay thế rõ ràng. |

## Lượt kiểm preset đề xuất

Benchmark local trên Windows, Python 3.11.9, Intel Core i7-12700H. Ba lượt cùng seed 42 mất 0,522 / 0,518 / 0,623 giây và đều hoàn tất một Ngày ở tick 22.200.

~~~text
python -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out day-bench.jsonl
~~~

Giữ JSONL trong thư mục tạm. SHA-256 chung là `aeee58f2260b9141b8803dd8ecf28ccf1d95a0bee4207b0345377c140190ed95`. Test bếp và test món dùng fixture riêng để hai bếp/bốn bàn trên preset mới không đổi ý nghĩa bài kiểm. Test nút lạ cũng tách theo hợp đồng vì `attack` là input hợp lệ từ v1.1.

## Việc tiếp tục ở Phase 3

Đối chiếu preset và payload còn mở theo P2-01/P2-02. Mở rộng regression qua các ca giữ nút khi đổi pha,
thiếu tiền và cấp tối đa, dùng tag `phase-2` làm mốc. Kiểm commit của tag bằng `git ls-remote --tags origin refs/tags/phase-2 'refs/tags/phase-2^{}'`.
