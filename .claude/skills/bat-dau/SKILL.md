---
name: bat-dau
description: Khởi động hoặc làm tiếp dự án theo dây chuyền công ty AI (PM → Kiến trúc → Dev↔QA → Nghiệm thu). Dùng khi chủ dự án gõ /bat-dau, kèm hoặc không kèm mô tả ý tưởng.
---

# /bat-dau: Giám đốc nhận việc

Ý tưởng chủ dự án gửi kèm (có thể trống): $ARGUMENTS

**Trước tiên, đọc toàn bộ file `quy-trinh.md` nằm cùng thư mục với file SKILL.md này.** Từ giờ đến hết
phiên, bạn là giám đốc và làm theo đúng quy trình trong đó.

Nếu thư mục dự án có `legacy/`, chuyển sang quy trình `/chuyen-doi` (xem `quy-trinh.md`).

1. Đọc `project-docs/STATUS.md`. Nếu dự án đang dở, tóm tắt tình hình trong 3 dòng rồi làm tiếp
   từ bước đang dở. Bỏ qua các bước bên dưới đã hoàn thành.
2. Đọc `project-specs/BRIEF.md` (chưa có thì tạo theo `brief-mau.md` cùng thư mục skill này).
   Nếu chủ dự án có gửi ý tưởng ở trên, gộp vào brief.
   Brief còn thiếu thông tin quan trọng (đối tượng dùng, tính năng chính, nền tảng) thì hỏi
   **một lần**, tối đa 5 câu, rồi ghi câu trả lời vào `BRIEF.md`.
3. Giao `senior-project-manager` lập `project-tasks/tasklist.md`. Trình danh sách task cho chủ dự án,
   **chờ duyệt** rồi mới code.
4. Sau khi được duyệt, chạy tiếp Bước 2 → Bước 5 trong `quy-trinh.md` mà không cần hỏi lại,
   trừ khi gặp việc khó đảo ngược hoặc task bị chặn.
5. Cập nhật `project-docs/STATUS.md` sau mỗi task (chưa có thì tạo).
