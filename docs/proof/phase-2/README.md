# Chạy lại QA Phase 2

\`\`\`bash
PYTHONPATH=tests:. python3 -m unittest test_phase2_regression test_phase2_day -v
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 tools/check_team.py
\`\`\`

Smoke kiểm chuyển Gather → Quán → Shop ở tick 1/2/3. Khi manifest còn v1.0,
test chạy parser và runtime với một preset v1.1 chỉ dùng trong test. Khi
manifest chuyển lên v1.1, test gọi CLI theo manifest thật.

Regression chạy hai lần cùng seed và input cho từng mode độc lập rồi
so trực tiếp byte JSONL trong thư mục tạm. Xem kết quả ở
[ma trận Phase 2](../../verification/phase-2.md).
