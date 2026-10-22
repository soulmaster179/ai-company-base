---
name: tien-do
description: Báo cáo tiến độ dự án hiện tại từ STATUS.md và tasklist.md. Dùng khi chủ dự án gõ /tien-do hoặc hỏi "tới đâu rồi".
---

# /tien-do: Báo cáo tiến độ

Đọc `project-docs/STATUS.md` và `project-tasks/tasklist.md` trong thư mục dự án, đếm số task
`[x]` / `[ ]` / BLOCKED, rồi báo cáo theo "Mẫu báo cáo tiến độ" ở cuối file `../bat-dau/quy-trinh.md`
(tính từ thư mục chứa file SKILL.md này). Nếu có `project-docs/parity-checklist.md` thì thêm dòng
`🔁 Parity: [đạt]/[tổng] mục`. Không giao việc, không sửa code.
Nếu chưa có tasklist, nói dự án chưa bắt đầu và gợi ý gõ `/bat-dau <ý tưởng>` hoặc `/chuyen-doi`.
