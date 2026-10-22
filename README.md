# 🏢 AI Company Base

Bộ công cụ biến Claude Code thành **một công ty có giám đốc và phòng ban**.
Bạn chỉ cần ra lệnh cho giám đốc, còn giám đốc tự chia việc cho PM, thiết kế, dev, QA...

Cài **một lần** vào máy, sau đó dùng được ở **mọi thư mục**, không phải copy gì vào từng dự án.

## Cài đặt / cập nhật

Mở PowerShell trong thư mục này và chạy:
```
powershell -ExecutionPolicy Bypass -File install.ps1
```
Script chép agent và lệnh vào `C:\Users\<bạn>\.claude\`. Sửa gì trong repo này thì chạy lại để cập nhật.
Muốn gỡ thì thêm `-Uninstall`.

## Dự án mới

1. Tạo một thư mục trống và mở nó trong Claude Code.
2. Gõ:
   ```
   /bat-dau làm web đặt bàn nhà hàng, có menu, form đặt bàn, trang admin
   ```
3. Duyệt danh sách task giám đốc đưa ra, sau đó cứ để nó chạy.

## Chuyển dự án có sẵn sang ngôn ngữ khác

1. Tạo thư mục dự án mới, chép **nguyên dự án cũ** vào thư mục con `legacy/`. AI chỉ đọc, không bao giờ sửa code cũ.
2. Mở thư mục mới trong Claude Code và gõ:
   ```
   /chuyen-doi từ PHP sang Node.js (Express), giữ nguyên database MySQL và các URL
   ```
3. AI phân tích code cũ ra 3 file trong `project-docs/`:
   - `legacy-analysis.md`: tính năng, module, database, API, các "hành vi ẩn" dễ bị mất khi port
   - `migration-map.md`: thư viện cũ tương ứng thư viện mới, thứ tự chuyển, rủi ro
   - `parity-checklist.md`: danh sách kiểm tra để bản mới chạy giống hệt bản cũ
4. Bạn duyệt bản tóm tắt. Sau đó AI chuyển từng module, QA so sánh từng mục với bản cũ.

## Làm tiếp, xem tiến độ

- Quay lại hôm sau: mở phiên mới, gõ `/bat-dau` (hoặc `/chuyen-doi`) không kèm gì. AI đọc sổ tiến độ rồi làm tiếp.
- Xem tiến độ: `/tien-do`.

Không gõ các lệnh này thì Claude vẫn là Claude bình thường. Quy trình giám đốc chỉ bật khi bạn gọi lệnh.

## Trong repo có gì

```
install.ps1                       ← cài / cập nhật / gỡ
.claude/agents/                   ← 14 nhân viên (phòng ban)
.claude/skills/bat-dau/
    SKILL.md                      ← lệnh /bat-dau
    quy-trinh.md                  ← "nội quy công ty": sơ đồ phòng ban + dây chuyền
    brief-mau.md                  ← mẫu brief dự án
.claude/skills/chuyen-doi/        ← lệnh /chuyen-doi
.claude/skills/tien-do/           ← lệnh /tien-do
```

Trong mỗi dự án, AI tự tạo:
```
project-specs/BRIEF.md     ← yêu cầu dự án
project-tasks/tasklist.md  ← danh sách task
project-docs/STATUS.md     ← sổ tiến độ (để làm tiếp qua nhiều phiên)
project-docs/              ← tài liệu kiến trúc, phân tích
app/                       ← code sản phẩm
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
  đổi dòng `name:` thành dạng `chu-thuong-gach-noi`, thêm một dòng vào bảng trong
  `.claude/skills/bat-dau/quy-trinh.md`, rồi chạy lại `install.ps1`.
- **Đổi quy trình:** sửa `quy-trinh.md`, rồi chạy lại `install.ps1`.
- **Riêng một dự án:** đặt thư mục `.claude/` trong dự án đó. Agent hoặc lệnh trùng tên trong dự án sẽ được ưu tiên hơn bản dùng chung.

## Lưu ý

- Chạy cả dây chuyền **tốn token gấp nhiều lần** so với nhờ Claude làm thẳng.
  Việc nhỏ thì cứ nói bình thường, giám đốc sẽ tự làm luôn.
- Agent con không gọi được agent con khác, nên phiên chính luôn là giám đốc.

## Bản quyền

Các file trong `.claude/agents/` (trừ `legacy-analyst.md`) lấy từ
[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) (giấy phép MIT,
xem `licenses/agency-agents-LICENSE`), chỉ đổi trường `name` để hợp với Claude Code.
