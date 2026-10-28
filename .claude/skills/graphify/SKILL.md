---
name: graphify
description: Lập đồ thị mã nguồn bằng Graphify. Chạy phân tích AST miễn phí mặc định; chỉ dùng phân tích semantic/API key khi chủ dự án yêu cầu rõ.
---

# /graphify: Lập đồ thị mã nguồn

Yêu cầu của chủ dự án (có thể trống): $ARGUMENTS

## Nguyên tắc an toàn

- Chỉ chạy khi chủ dự án gọi `/graphify`; không tự chạy khi bắt đầu/kết thúc phiên hay trong `/bat-dau`, `/phan-tich`, `/chuyen-doi`.
- Mặc định dùng AST-only: không gửi code ra ngoài, không cần API key và không tốn phí semantic extraction.
- Không dùng semantic extraction, `ANTHROPIC_API_KEY`, `MOONSHOT_API_KEY`, `--deep`, `--wiki`, hoặc Obsidian nếu chủ dự án chưa yêu cầu rõ.
- Kết quả luôn ở `graphify-out/` trong thư mục dự án được phân tích. Không sửa source code.

## Quy trình

1. Xác định scope từ `$ARGUMENTS`. Nếu không nêu scope, dùng thư mục làm việc hiện tại (`.`). Chỉ nhận đường dẫn nằm trong thư mục làm việc; với scope bên ngoài, hỏi lại trước.
2. Kiểm tra Graphify CLI có trên `PATH` (`graphify --version`).
   - Nếu chưa có, nói rõ cần cài Python 3 rồi chạy:
     ```bash
     pip install graphifyy
     ```
     Dừng tại đây, không cố tự cài package nếu chủ dự án chưa yêu cầu.
3. Nếu chủ dự án không yêu cầu cờ khác, chạy:
   ```bash
   graphify extract . --out ./graphify-out --no-cluster
   ```
4. Nếu có `--update`, chạy cập nhật theo CLI Graphify thay vì trích xuất lại toàn bộ.
5. Nếu có `--tree`, sau khi có `graphify-out/graph.json`, chạy:
   ```bash
   graphify tree --graph ./graphify-out/graph.json --output ./graphify-out/GRAPH_TREE.html
   ```
6. Đọc `graphify-out/GRAPH_REPORT.md` nếu có. Báo ngắn gọn: scope, các output đã tạo (`graph.json`, `GRAPH_REPORT.md`, `GRAPH_TREE.html` nếu có), số liệu/điểm trung tâm được báo cáo, và đường dẫn để chủ dự án mở xem.

## Semantic extraction (chỉ khi được yêu cầu rõ)

Nếu chủ dự án yêu cầu semantic/deep/wiki/Obsidian, giải thích trước rằng Graphify có thể gọi mô hình và cần key hợp lệ; semantic extraction có thể phát sinh chi phí và gửi ngữ cảnh code tới provider được cấu hình. Chỉ chạy sau khi chủ dự án xác nhận rõ, và không hiển thị/ghi API key vào chat, file, graph output, hay log session.
