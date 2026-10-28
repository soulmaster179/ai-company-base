# Thiết kế Graphify và memory tự động toàn cục

- **Ngày tạo:** 2026-10-28
- **Trạng thái:** Chờ duyệt
- **Phạm vi:** Toolkit AI Company Base + cài đặt Claude Code toàn cục của người dùng

---

## 1. Bối cảnh & ý định

Người dùng muốn Graphify và memory setup từ `lucasrosati/claude-code-memory-setup` luôn hoạt động xuyên phiên Claude Code. Đã chọn bật cho **mọi phiên Claude Code trên máy**, không chỉ các dự án dùng AI Company Base.

Tích hợp sẽ dùng auto-memory sẵn có của Claude Code để nhớ kiến thức bền vững theo project, cộng một hook `SessionEnd` của toolkit để ghi bản ghi phiên nhỏ, giúp khôi phục việc đang làm. Graphify là phần riêng, chạy khi được gọi để lập code graph; không tự chạy mỗi session.

---

## 2. Mục tiêu, phi mục tiêu và nguyên tắc an toàn

### Mục tiêu

1. Bật `autoMemoryEnabled: true` trong user settings (`~/.claude/settings.json`) để Claude Code tự đọc/ghi auto-memory trong các phiên, theo cơ chế native.
2. Đăng ký một hook `SessionEnd` toàn cục để tạo log Markdown tóm tắt phiên từ transcript JSONL, lưu trực tiếp ngay trong dự án (`project-docs/sessions/` nếu có, hoặc `.claude/sessions/`) để lưu trữ đồng bộ cùng Git repo và không bị mất khi cài lại máy; chỉ fallback về thư mục người dùng khi thư mục làm việc không ghi được.
3. Khi bắt đầu phiên, auto-memory native tiếp tục đọc memory project tương ứng; không thêm hook tự chèn log gần đây vào mọi prompt vì có thể nạp context sai hoặc lặp dữ liệu.
4. Tạo skill `/graphify`, chạy AST-only mặc định và xuất graph vào `graphify-out/`; semantic extraction chỉ khi người dùng yêu cầu rõ.
5. Cập nhật `install.ps1` theo cách idempotent, có thể cập nhật và gỡ phần cài do toolkit quản lý mà không thay thế các thiết lập/hook khác.
6. Cập nhật README hướng dẫn bật, xem, và tắt memory/Graphify.

### Phi mục tiêu

- Không cài Obsidian, tạo vault tập trung, import chat web, hoặc tạo cron.
- Không lưu toàn bộ transcript thành bản sao riêng.
- Không dùng API key hoặc semantic LLM cho autosave; hook chỉ phân tích transcript cục bộ bằng thư viện chuẩn, không có mạng.
- Không tự chạy Graphify khi mở/kết thúc phiên hoặc trong `/bat-dau`, `/phan-tich`, `/chuyen-doi`.
- Không sửa các thay đổi dở dang đã tồn tại trong working tree ngoài phạm vi cần thiết.

### Nguyên tắc an toàn và riêng tư

- Bản ghi phiên có thể chứa nội dung prompt đầu tiên, đường dẫn file và một số lệnh shell; không ghi nội dung file hoặc kết quả tool. Đường dẫn và lệnh được giới hạn số lượng, và cần bỏ qua/che giá trị có dạng secret/token trước khi ghi.
- Lưu trữ chỉ trên máy, theo thư mục project riêng; không commit log vào repo và không gửi ra dịch vụ ngoài.
- Nếu thiếu transcript, dữ liệu không hợp lệ, hoặc hook lỗi, không chặn kết thúc phiên; chỉ ghi diagnostic không chứa nội dung prompt.
- README phải chỉ rõ cách tắt: đặt `autoMemoryEnabled: false` hoặc gỡ hook do installer thêm; không sửa/xóa hook do người dùng hay công cụ khác tạo.

---

## 3. Các hướng tiếp cận

### A. Auto-memory native + SessionEnd local log + Graphify skill (**được chọn**)

Bật auto-memory native toàn cục; hook SessionEnd lưu bản ghi phiên nhỏ vào storage riêng theo project; thêm skill Graphify thủ công.

- **Ưu điểm:** Memory được Claude Code hỗ trợ trực tiếp, ít phụ thuộc; log hỗ trợ resume; không tốn API ngoài subscription/session; Graphify độc lập.
- **Đánh đổi:** Auto-memory native lưu theo project, không tự hợp nhất kiến thức chung giữa mọi project. Session log không phải bản ghi đầy đủ và có thể bỏ qua phiên ngắn/không có transcript.

### B. Sao chép nguyên bộ upstream Obsidian

Cài vault, lệnh `/save`, `/resume`, `/memorize`, script import và Graphify.

- **Loại:** Thêm phụ thuộc Obsidian/Python và luồng vault riêng; trùng vai trò với auto-memory native, tăng rủi ro lưu trữ nội dung nhạy cảm.

### C. Chỉ bật auto-memory native

Không thêm hook hay Graphify.

- **Loại:** An toàn và gọn nhất, nhưng không cung cấp nhật ký phiên bổ trợ hoặc Graphify mà người dùng muốn.

---

## 4. Cách triển khai dự kiến

1. Thêm `.claude/skills/graphify/SKILL.md` với cách kiểm tra CLI, AST-only mặc định, cập nhật graph, tùy chọn semantic có xác nhận rõ, và báo cáo output.
2. Thêm script autosave cục bộ, chỉ dùng Python standard library, đọc JSON từ stdin và transcript JSONL được Claude Code cung cấp. Ghi log tối thiểu (timestamp, session id, end reason, cwd/project, tóm tắt prompt mở đầu đã lọc, tối đa 20 đường dẫn file và 10 lệnh đã lọc); không ghi tool output hay nội dung file. Lưu trong `~/.claude/ai-company-memory/<project-id>/sessions/` hoặc một layout an toàn tương đương.
3. Nâng cấp `install.ps1` để:
   - Cài skill và script vào `~/.claude/`.
   - Đọc/merge user `settings.json`, bật `autoMemoryEnabled`, và thêm hook `SessionEnd` dùng script đã cài.
   - Chỉ quản lý đúng hook có dấu nhận diện riêng; chạy lặp không tạo duplicate.
   - Khi uninstall, chỉ gỡ hook/script/skill do toolkit sở hữu; giữ nguyên cấu hình khác. Nếu settings hiện có không đọc được hoặc hook xung đột, dừng với thông báo thay vì ghi đè.
   - Phát hiện Python chưa có và báo hook autosave không hoạt động/đưa hướng dẫn; auto-memory native vẫn bật.
4. Cập nhật `README.md` mô tả lưu trữ, dữ liệu log, giới hạn memory theo project, Graphify và cách opt out.
5. Bổ sung ignore cho `graphify-out/cache/`; không tự ignore toàn bộ `graphify-out/` nếu các output graph/báo cáo hữu ích cần commit.

---

## 5. Kiểm chứng

- Test script autosave với payload giả lập: phiên hợp lệ, thiếu transcript, JSONL lỗi, project path chứa khoảng trắng, và prompt/lệnh chứa chuỗi giống secret.
- Chạy installer trong môi trường thử với settings có sẵn và hooks khác: xác nhận merge, không trùng hook, và uninstall không xóa settings/hook không thuộc toolkit.
- Kiểm tra JSON bằng PowerShell parser, xác nhận `autoMemoryEnabled` và hook `SessionEnd` đúng schema.
- Xác nhận `/graphify` được cài vào thư mục user Claude và AST-only không yêu cầu API key.
- Kiểm tra git diff/status để đảm bảo giữ nguyên các thay đổi có sẵn.
