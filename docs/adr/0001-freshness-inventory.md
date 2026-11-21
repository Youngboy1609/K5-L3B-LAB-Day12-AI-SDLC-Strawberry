# ADR-0001 · Kho theo cá thể từ Test Contract v1.2

- Trạng thái đề xuất triển khai, chờ chạy smoke với cả hai đầu bàn giao
- Ngày 2026-11-21 · Hồ Trọng Nghĩa

## Bối cảnh

Ở `phase-2`, Gather chuyển giỏ thành `{kind: count}` rồi bàn giao cho Quán. Ticket‑03 yêu cầu giữ ID và độ tươi của từng cá thể qua file, giữa hai pha và trong fixture nhiều ngày. Quán cần kiểm phần giữ trên kho thật lúc mở ca. Snapshot và JSONL phải đủ chính xác để kiểm ngưỡng 30.

## Quyết định

1. Dùng chung version từ manifest cho CLI, scenario, runtime và file kho. Bản chạy v1.2 chỉ nhận `{"items":[{"id":"I1","kind":"ca_linh","fresh":100}]}`. Kho rỗng là `{"items":[]}`. Đọc file đếm trong v1.2 trả mã 2. Các phiên bản trước tiếp tục dùng kho đếm.
2. Giữ một biểu diễn nội bộ cho cá thể do adapter của Hạnh cung cấp. Fresh lưu chính xác khi tính hao và giá. File kho và JSONL dùng cùng cách xuất fresh. Với sức chứa giỏ hoặc bộ đếm không liên quan độ tươi, dùng kiểu số của validator hiện có.
3. Gather giữ thứ tự lấy trong giỏ để xử lý LIFO. Day dùng `IdAllocator` chung qua các pha. D1 giữ ID fixture. Từ D2, tái tạo các cá thể theo thứ tự mảng với ID mới, kind và fresh ban đầu. Theo đề xuất P3-04, ánh xạ lại các tham chiếu giữ chỗ trỏ vào cá thể của giỏ mẫu. Quán kiểm mọi tham chiếu còn lại với tồn kho thực.
4. Mở Quán ở cùng tick với `gather_end`. Quán hao kho từ bước kế tiếp. Shop giữ kho dư để xuất snapshot và bỏ kho khi đóng. Day ghi JSONL qua file tạm để lỗi lúc khởi tạo pha sau vẫn giữ được file đích cũ.
5. Dùng `freshness` ở gốc manifest v1.2 và đưa cấu hình đã kiểm vào tuning của mô phỏng. Bật v1.2 sau smoke bàn giao bằng cả file và bộ nhớ. Giá theo P3-01 được khóa lúc bắt đầu nấu. [Các điểm làm rõ](../clarify.md)

## Lựa chọn đã cân nhắc

- Chuyển tất cả các lát và manifest trong một lần giúp giảm thời gian giữ hai schema. Cách này buộc các nhánh phải hoàn thành cùng mốc và làm khó việc tìm lỗi ở ranh giới bàn giao.
- Ghép adapter và đường chuyển version trước cho phép Gather, Quán và HUD chạy thử trên cùng giao diện. Trong lúc đó, manifest v1.1 tiếp tục chạy các mode đã bàn giao. Chi phí là phải kiểm cả đường v1.1 và v1.2 cho đến khi chốt bản tích hợp.

## Hệ quả và kiểm chứng

| Lát | Thay đổi cần ghép và bằng chứng |
|---|---|
| Adapter | `inventory.py` và `jsonl.py` kiểm schema, xuất kho nguyên tử và giữ fresh gần ngưỡng khi đọc lại. |
| Gameplay | Gather cấp ID, hao giỏ và rơi theo LIFO. Quán hao kho, kiểm giữ chỗ và tính giá. Hai đầu nhận cùng cá thể từ Day. |
| Điều phối | CLI, scenario và runner chuyển version. Với fixture trả mã 2 ở pha sau, smoke phải cho thấy file đích hiện có giữ nguyên. |
| UI và QA | Live/HUD đọc schema theo version. Chạy smoke phút 20, test hồi quy và ma trận theo [kế hoạch Phase 3](../plan/phase-3.md). |

Giữ tag `phase-2` làm bản chạy v1.1 để kiểm hồi quy và quay về nếu phiên bản tích hợp có lỗi. File kho còn thuộc schema nào thì đọc bằng phiên bản tương ứng. Việc cập nhật fixture sang v1.2 cần ID duy nhất và số fresh có căn cứ.
