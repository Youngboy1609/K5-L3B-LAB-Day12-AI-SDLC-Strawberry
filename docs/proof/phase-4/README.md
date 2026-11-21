# Bằng chứng QA Phase 4

Mốc mã, môi trường, ma trận và lỗi: [verification](../../verification/phase-4.md).

```sh
PYTHONPATH=tests:. python3 -m unittest test_phase4_contract -v
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 docs/proof/phase-4/run_v11_regression.py
PYTHONPATH=tests:. python3 -m unittest test_flood_current test_quan_reservations -v
```

`run_v11_regression.py` gọi script Phase 3 trong cây tạm, chỉ loại test release v1.3 vừa thêm; không đổi script/lược bỏ ca hồi quy cũ. Lệnh Phase 3 trực tiếp nay sẽ thu thêm test P4, nên không thể coi toàn bộ discovery trên manifest v1.1 là test v1.1.

`v12-positive.log` là ca kho của `ReleaseContract` chạy với manifest tạm đặt v1.2 để chứng minh fixture hợp lệ. Ba mode trong ca so byte cũng chạy v1.2 trước v1.3. Log dài, JSONL và ZIP thử giữ ở `/tmp/chonoi-p4-qa/`; các log kết quả được lưu tại đây để review. Chưa có `bench.json`/`soak.json` vì module và command chưa được ghép; không tạo tệp giả.
