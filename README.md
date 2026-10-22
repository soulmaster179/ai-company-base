# 🏢 AI Company Base

Bộ khung dự án biến Claude Code thành **một công ty có giám đốc và phòng ban**.
Bạn chỉ cần ra lệnh cho giám đốc, còn giám đốc tự chia việc cho PM, thiết kế, dev, QA...

## Cách dùng cho dự án mới

1. **Copy cả thư mục này** thành thư mục dự án mới (hoặc bấm "Use this template" nếu bạn đưa nó lên GitHub).
2. Mở thư mục đó trong Claude Code.
3. (Tuỳ chọn) điền `project-specs/BRIEF.md`.
4. Gõ:
   ```
   /bat-dau làm web đặt bàn nhà hàng, có menu, form đặt bàn, trang admin
   ```
5. Duyệt danh sách task giám đốc đưa ra, sau đó cứ để nó chạy.

Lần sau quay lại, mở phiên mới và gõ `/bat-dau` là nó đọc sổ tiến độ rồi làm tiếp.
Muốn xem tiến độ thì gõ `/tien-do`.

## Bên trong có gì

```
CLAUDE.md                  ← "nội quy công ty": quy trình giám đốc phải theo
.claude/agents/            ← 13 nhân viên (phòng ban)
.claude/skills/bat-dau/    ← lệnh /bat-dau
.claude/skills/tien-do/    ← lệnh /tien-do
project-specs/BRIEF.md     ← yêu cầu dự án
project-tasks/             ← danh sách task (PM tạo)
project-docs/STATUS.md     ← sổ tiến độ (để làm tiếp qua nhiều phiên)
project-docs/              ← tài liệu kiến trúc
app/                       ← code sản phẩm (tạo khi bắt đầu code)
```

## Dây chuyền

```
Bạn → 👔 Giám đốc → 📋 PM chia task → (bạn duyệt) → 📐 Kiến trúc
    → 🔁 [💻 Dev làm task ↔ 📸 QA kiểm tra, tối đa 3 lần] × mỗi task
    → 👁️ Review code → 🧐 Duyệt cuối → 📚 Viết README → báo cáo bạn
```

## Tuỳ biến

- **Thêm phòng ban:** chép thêm file `.md` từ
  [agency-agents](https://github.com/msitarzewski/agency-agents) vào `.claude/agents/`,
  đổi dòng `name:` thành dạng `chu-thuong-gach-noi`, rồi thêm một dòng vào bảng trong `CLAUDE.md`.
  Ví dụ dự án marketing thì lấy thêm từ thư mục `marketing/`.
- **Bớt phòng ban:** xoá file trong `.claude/agents/` và dòng tương ứng trong `CLAUDE.md`.
- **Đổi quy trình:** sửa `CLAUDE.md`, vì đó là thứ giám đốc tuân theo.

## Lưu ý

- Chạy cả dây chuyền **tốn token gấp nhiều lần** so với nhờ Claude làm thẳng.
  Việc nhỏ thì cứ nói bình thường, giám đốc sẽ tự làm luôn.
- Agent con không gọi được agent con khác, nên phiên chính luôn là giám đốc.

## Bản quyền

Các file trong `.claude/agents/` lấy từ
[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) (giấy phép MIT,
xem `licenses/agency-agents-LICENSE`), chỉ đổi trường `name` để hợp với Claude Code.
