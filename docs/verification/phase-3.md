# QA Phase 3 — Nguyễn Minh Quân

Ngày kiểm: 2026-11-21. Đây là kết quả chuẩn bị QA, chưa phải nghiệm thu v1.2.

- Cây nguồn đã kiểm: `92795af5a80ff2499f396f4b6ecf0a4bb531bb9f` cộng thay đổi QA chưa commit trong lượt này.
- Nền `phase-2^{commit}` tại local: `8d01879cdcbb6c3551c82ee7c1a41aff236ebed6`, khớp kế hoạch. Không dùng SHA annotated tag object làm SHA commit.
- Manifest sản phẩm vẫn là v1.1. Test mới sao chép `chonoi/` vào thư mục tạm, đặt manifest v1.2 với `freshness` ở gốc theo đề xuất trong kế hoạch. Không mock loader/runtime, không sửa manifest khóa hoặc test cũ.
- Seed CLI: 42. Test dùng subprocess thật, snapshot mỗi tick. JSONL và log thô ở thư mục tạm, không đưa vào bài nộp.

## Kết quả chạy

| Lệnh từ gốc repo | Kết quả thực tế |
|---|---|
| `python3 docs/proof/phase-3/run_regression.py` | 112 test P1/P2 đạt với manifest v1.1 được giữ trong fixture; 5,739 s. |
| `PYTHONPATH=tests:. python3 -m unittest test_phase3_integration -v` | 12 phương thức test, 14 failure tính cả subtest, 0 error; 0,889 s. Tất cả bị chặn ở loader. |
| `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` | 124 test trong 6,563 s: 112 test cũ đạt; 12 test P3 có 14 failure tính cả subtest, 0 error. |

Ba test HTTP live ban đầu gặp `PermissionError` khi mở cổng trong sandbox. Đã chạy lại ngoài sandbox để kiểm cổng localhost; regression đủ 112/112 đạt. Không thay test để né lỗi môi trường.

## Ma trận nghiệm thu

| AC | Test / bằng chứng đã chuẩn bị | Trạng thái thực tế |
|---|---|---|
| AC-P3-01 | `test_file_handoff_preserves_identity_and_unrounded_freshness`, `test_invalid_inventory_rejected_without_replacing_output`, `test_inventory_can_exceed_basket_capacity`, `test_unfinished_gather_preserves_inventory_destination`, `test_faint_exports_empty_array_and_lifo_loss`, `test_reserved_ids_cannot_be_shared_and_day_output_is_atomic` | Chưa đạt: loader v1.2 từ chối manifest. Các ca từ chối có positive control để tránh xanh giả khi mọi payload đều bị từ chối. |
| AC-P3-02 | `test_spoiled_crossing_once_sorted_by_id`, `test_exact_threshold_still_fresh_at_tick_zero`, `test_decimal_just_above_threshold_not_rounded_to_spoiled`, `test_day_handoff_shop_freezes_and_day_two_renews_ids`, `test_price_floor_after_decay_and_items_sorted`, `test_standalone_outputs_deterministic` | Chưa xác minh gameplay: chưa đi qua loader. Giá dùng Fraction từ đúng số thập phân JSON fixture sau hao, không dùng số hiển thị đã làm tròn. |
| AC-P3-03 | Kế hoạch đã phân công; test CLI thật trong cây sao chép | Chưa có kiểm bản chơi v1.2/HUD hoặc ADR được nghiệm thu trong lượt này. |
| AC-P3-04 | Regression 112/112, fixture manifest v1.1, script tái chạy, tài liệu này | Mới hoàn tất phần chuẩn bị QA. Chưa nghiệm thu CHANGELOG, HUD, ADR và schema v1.2. |
| AC-P3-05 | Đã đối chiếu commit nền local | Chưa đối chiếu remote main/tag ứng viên với Nghĩa; chưa tạo/push tag. |

## Điểm đỏ cần bàn giao

1. `contract.py::_validate_gather`: manifest `contract_version: "1.2"` bị đưa vào tập nguyên liệu P1, báo `tuning.gather.nodes.N5: kind phải là một trong ('bong_dien_dien', 'bong_sung')`. Tái hiện bằng bất kỳ test mới; chưa kiểm được payload `I1` ở tick 0.
2. `headless.py`: điều kiện Day, buttons và buy còn chỉ nhận đúng `"1.1"`. Đây là điểm chặn tiếp theo thấy từ đọc mã, chưa phải kết quả chạy sau sửa loader.
3. `inventory.py`, Gather, Quán và Day hiện còn kho count/giỏ kind theo v1.1. Chủ các lát cần ghép schema cá thể trước khi bật v1.2. Không đổi các file này trong lát QA.

## Phần chờ chốt và kiểm tiếp

- P3-02: chưa khóa test tái cấp khi phần giữ vừa ươn, giữ lại phần còn tươi và hai đơn cạnh tranh; cần PO/chủ Quán chốt thứ tự và trạng thái trước khi viết kỳ vọng.
- P3-03: chưa yêu cầu event khởi tạo cho hàng vốn đã ươn; ca hiện tại chỉ kiểm vượt ngưỡng trong bước.
- P3-04: ca D2 kiểm cấp ID mới với cấp đơn tự động; chưa khóa ánh xạ reserved qua nhiều ngày.
- Sau ghép: chạy lại toàn bộ test mới, bổ sung khóa giá qua bếp/tay đến phục vụ, lựa chọn tươi nhất/hòa ID, fresh không hữu hạn, kiểm payload sau vòng ghi–đọc sát ngưỡng và HUD với Hà. Không xem các kiểm tra này là đã đạt.
- Chưa có review chéo của nhóm. Không merge/push bộ test đỏ như ứng viên bàn giao đạt.
