# Thành phần bên thứ ba

Credit riêng cho pack giọng Nagisa Kubo nằm trong [CREDITS.md](../CREDITS.md). Không gộp tác giả model với tác giả phần mềm RVC. Giữ Discord ID được ghi trong bài đăng gốc và liên kết nguồn pack; chưa xác minh tên hiển thị hiện tại.

Mã trong work/rvc lấy từ bản làm việc cục bộ của Retrieval-based Voice Conversion WebUI:
https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

Giữ nguyên LICENSE gốc tại work/rvc/LICENSE. Đây là bản chọn lọc có thay đổi cục bộ, không tuyên bố trùng upstream HEAD. Trước khi publish cần ghi lại commit nguồn và mô tả thay đổi có thể xác định; không bịa revision khi chưa xác minh.

Các phụ thuộc gồm PySide6/Qt, PyTorch, Transformers, NumPy/SciPy, sounddevice/PortAudio, FFmpeg và các gói inference bắc cầu. Khi phân phối binary, thu thập đúng thông tin giấy phép từ phiên bản và cấu hình thực sự đóng gói; bảng tóm tắt tên giấy phép không thay thế các thông báo cần đi kèm.

Không áp dụng tự động một LICENSE duy nhất cho model, ảnh, audio hoặc toàn bộ thư viện. Chủ project cần chọn giấy phép cho phần mã do mình sở hữu trước khi gắn nhãn open source.
