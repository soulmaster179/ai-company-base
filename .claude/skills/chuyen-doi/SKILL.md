---
name: chuyen-doi
description: Chuyển một dự án có sẵn (đặt trong legacy/) sang ngôn ngữ hoặc framework khác, giữ nguyên hành vi. Quy trình gồm phân tích code cũ → bảng ánh xạ → chuyển từng module ↔ QA so sánh với bản cũ → nghiệm thu. Dùng khi chủ dự án gõ /chuyen-doi hoặc muốn port/viết lại dự án cũ.
---

# /chuyen-doi: Chuyển dự án sang ngôn ngữ mới

Yêu cầu của chủ dự án (có thể trống): $ARGUMENTS

**Trước tiên, đọc toàn bộ file `../bat-dau/quy-trinh.md`** (tính từ thư mục chứa file SKILL.md này,
tức thư mục skill `bat-dau` nằm cạnh). Từ giờ đến hết phiên, bạn là giám đốc theo quy trình đó.
Quy trình chuyển đổi dưới đây **thay cho Bước 1–3** của dây chuyền thường.
Nguyên tắc số 1: **bản mới phải làm được đúng những gì bản cũ làm**. Không thêm tính năng, không
"cải tiến" khi chưa được chủ dự án đồng ý.

## Bước 0: Kiểm tra đầu vào
- Đọc `project-docs/STATUS.md`. Nếu đang chuyển đổi dở, làm tiếp từ bước đang dở.
- `legacy/` phải tồn tại và có code. Nếu chưa có, hướng dẫn chủ dự án chép dự án cũ vào `legacy/` rồi dừng.
- Xác định **ngôn ngữ/framework đích**: lấy từ yêu cầu ở trên hoặc từ `project-specs/BRIEF.md`.
  Nếu chưa có thì hỏi. Hỏi luôn trong cùng một lần: có cần giữ nguyên database, URL/API, giao diện không.
  Ghi câu trả lời vào `BRIEF.md`.
- Nếu `legacy/` có `.git`, đảm bảo code cũ không bị sửa: chỉ đọc.

## Bước 1: Phân tích code cũ
Giao `legacy-analyst` tạo 3 file: `project-docs/legacy-analysis.md`, `migration-map.md`,
`parity-checklist.md`. Dự án lớn (nhiều module độc lập) có thể chia cho nhiều `legacy-analyst`
chạy song song, mỗi agent một nhóm module, rồi tự gộp lại.

Kiểm tra kết quả: mỗi tính năng có trích dẫn file nguồn chưa, có mục "Hidden behaviors" chưa.

**Trình chủ dự án** bản tóm tắt: số module, danh sách tính năng, công nghệ đích và các thư viện thay thế,
5 rủi ro lớn nhất, các câu hỏi còn mở. **Chờ duyệt** rồi mới làm tiếp.

## Bước 2: Kế hoạch và khung dự án mới
- Giao `senior-project-manager` lập `project-tasks/tasklist.md` **theo thứ tự chuyển module** trong
  `migration-map.md`. Task đầu tiên luôn là "dựng khung dự án mới chạy được + bộ test rỗng". Mỗi task ghi rõ
  các mã tính năng `F..` và gotcha `H..` mà nó phải giữ đúng.
- Giao `backend-architect` / `ux-architect` (tuỳ dự án) ghi `project-docs/architecture.md` cho bản mới.
- Code mới đặt trong `app/`.

## Bước 3: Chuyển từng module (vòng Dev ↔ QA)
Mỗi task:
1. Giao dev phù hợp, kèm: task, đường dẫn file cũ tương ứng trong `legacy/`, các mục liên quan trong
   `migration-map.md` và `parity-checklist.md`. Yêu cầu dev **viết test tái hiện các mục parity** cho module đó.
2. Giao `evidence-collector` (hoặc `api-tester` cho API) kiểm tra **so sánh với bản cũ**: chạy các mục
   parity của task trên bản mới. Nếu chạy được bản cũ an toàn thì chạy cả hai và so output.
   Phải có kết luận PASS/FAIL theo từng mục `F..`/`H..`.
3. PASS: đánh dấu `[x]` trong tasklist, tick các mục trong `parity-checklist.md`, cập nhật STATUS.md.
   FAIL: gửi lại dev kèm mục nào lệch. Tối đa 3 lần, quá thì BLOCKED và báo chủ dự án.
4. Gặp câu hỏi "code cũ xử lý X thế nào?" thì hỏi lại `legacy-analyst`, không đoán.

## Bước 4: Nghiệm thu
- Kiểm tra `parity-checklist.md`: mọi mục phải PASS hoặc được chủ dự án đồng ý bỏ qua (ghi lý do).
- Giao `code-reviewer` soát toàn bộ `app/`, rồi `reality-checker` duyệt cuối với yêu cầu:
  "bản mới có làm được mọi thứ trong legacy-analysis.md không?".
- Giao `technical-writer` viết README cho bản mới, kèm mục **"Khác biệt so với bản cũ"** (nếu có).

## Bước 5: Báo cáo
Dùng mẫu báo cáo trong `quy-trinh.md`, thêm dòng `🔁 Parity: [đạt]/[tổng] mục`.
Không xoá `legacy/`; việc đó do chủ dự án tự quyết.
