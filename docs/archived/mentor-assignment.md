Xây dựng 1 Python CLI tên costctl quản lý AWS resource y như những gì đang làm tay trong W6, gồm những tính năng list theo tag, tính cost, terminate, tag.

Source template: https://github.com/TechX-Corp/xbrain-costctl-starter

Template đã có sẵn cho các bạn:
•⁠  ⁠CLI scaffolding (argparse, dispatch, ./costctl.py --help chạy được)
•⁠  ⁠Utility helpers (parse_kv, tags_to_dict, tags_match, confirm)
•⁠  ⁠25 test cases đóng vai trò spec — chính là "đề bài"

Phần các bạn implement: command logic (function body). Mở file commands/*_cmd.py — mỗi file đều có module docstring ghi rõ what to build, AWS APIs to call, expected output format, và cách verify. Đọc docstring trước khi code.


Quick start với source trên:
  gh repo fork TechX-Corp/xbrain-costctl-starter --clone --fork-name g<N>-costctl   [ <N> là số nhóm của bạn ]
  cd g<N>-costctl
  make install-dev
  make test            # baseline: 10 pass (helpers), 15 fail (specs cần implement)
  ./costctl.py --help


Required: implement command ⁠ list ⁠ + ít nhất 2 trong các command sau:
•⁠  ⁠cost --tag k=v --days N
•⁠  ⁠terminate <type> --id <id>     (confirm y/N mặc định)
•⁠  ⁠tag <type> --id <id> --set k=v

Stretch (optional, không bắt buộc):
•⁠  ⁠clean --tag purpose=practice --apply       (bulk terminate by tag, dry-run mặc định)
•⁠  ⁠idle --threshold 5 --hours 24              (Trusted Advisor cho idle EC2, tự viết)
•⁠  ⁠migrate-gp3 --apply --volume-id <id>       (gp2 → gp3 EBS migration)

Goal: make test → 25/25 passing.


Submit:
•⁠  ⁠Push lên repo public của các em lên ​link​ 
•⁠  ⁠README: thay <N> = số nhóm, replace sample_output bằng output thật từ account của các em
•⁠  ⁠REFLECTIONS.md: ≥ 2 câu trả lời (prompt có trong README)
•⁠  ⁠Tag: git tag w6-sidechallenge-v1 && git push --tags
•⁠  ⁠Reply thread này theo format:
    G<N> — <repo-url> — X/25 tests passing — implemented: list, cost, terminate