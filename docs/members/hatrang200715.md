# hatrang200715 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Chốt hợp đồng 3 hàm `gather_actions` với Quang (5/5 mục OK) — `860597a` trên `phase1/gather-actions`, ghi tại `docs/standup.md`.
  - Viết `chonoi/sim/gather_actions.py`: `advance_nodes`, `try_harvest`, `try_catch` — `8f45901`. Số liệu đọc từ tuning, hòa khoảng cách theo ID, mép bán kính tính trong, thiếu chỗ phát `hold_full` một lần.
  - Review chéo bản ghép `DangQuang` của Quang (`ba4be00`): chạy lại suite + 3 kịch bản headless (`docked`, `fainted` LIFO + kho rỗng, bắt cá tick cuối vẫn vào kho) — đúng cả 2 tuyên bố của Quang — `ffe780c`.
- Tôi đã review (kèm link): `step()` đã ghép trên `origin/DangQuang` — thứ tự tick mục 5 đúng hợp đồng.
- AI sai ở đâu và tôi phát hiện thế nào: 
  
  Script kiểm do AI viết lỗi fixture 2 lần — quên `player.pos` phải nằm trong khối `player` của scenario, và đặt player ở mặt nước khiến `try_catch` chặn đúng luật. 
  
  AI cũng từng ghi con gà "docked" vì xuất phát trùng vị trí bến. Tôi phát hiện nhờ chạy và đọc kết quả thật điểm vào `headless`, không tin log cũ.

- Điều tôi học được:
  Chốt hợp đồng dữ liệu 15 phút trước khi code giúp hai người ghép không giẫm chân.
  
  Kiểm thử phải chạy trong đúng môi trường/worktree của bản ghép, nhầm cwd là ra kết quả sai ngầm.

- Phase 3 (kèm link commit): viết adapter kho v1.2 mảng cá thể `{id,kind,fresh}` — `validate_item_list`, `new_item`, `decay_items`, `item_payload` với `Fraction` chính xác, test biên "30.025 bốn tick Quán tươi, tick kế ươn" — `a55b108` trên `phase3/inventory-freshness`. 38/38 test mới, suite 150/150.
- Phase 4: lát `phase4/package-docs` — README (test/headless/benchmark/soak, ≤3 lệnh chạy), CHANGELOG Phase 1–4 từ lịch sử có bằng chứng, `CREDITS.md` (không asset ngoài), [`docs/release/v1.0.0.md`](../release/v1.0.0.md), kiểm clone sạch + ZIP `git archive` trên macOS.
