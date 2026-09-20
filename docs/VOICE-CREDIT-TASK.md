# Việc bổ sung cho Antigravity: credit pack giọng Nagisa Kubo

Chủ project yêu cầu ghi công người đã cung cấp pack giọng, theo ảnh bài đăng nguồn đã gửi. CREDITS.md đã chép thông tin nhìn thấy trong ảnh; giữ nguyên dữ liệu đó, không suy đoán tên tác giả từ tên tài khoản host.

## Cần thực hiện

1. Giữ CREDITS.md ở gốc repository và mục credit dễ thấy trong README, có link nguồn pack. Không mô tả model là do project Kubo train hoặc sở hữu.
2. Kiểm tra trang https://huggingface.co/Kuma6/Nagisa-Kubo và model card/điều khoản hiện có khi truy cập được. Trong lần chuẩn bị này công cụ duyệt không mở được trang; không coi đây là bằng chứng trang đã bị xóa. Nếu chưa xác minh tên hiển thị Discord, tiếp tục dùng ID `416975678542446592` như ảnh gốc.
3. Sửa build script để chép CREDITS.md vào bản phát hành (ví dụ licenses/CREDITS-VOICE.md), nhắc credit và nguồn trong README.txt và release notes. Làm cả khi model được tải riêng thay vì đính kèm.
4. Nếu ứng dụng có mục About/Giới thiệu, thêm tên pack và link credit tại đó. Nếu chưa có, có thể thêm mục menu “Nguồn giọng & Credit” mở tài liệu đi kèm; giữ thao tác đơn giản.
5. Ghi rõ +6 là thiết lập chuyển giọng của app. Không đổi tên pack gốc thành “model tự train của Kubo AI”.
6. Kiểm tra riêng quyền phân phối model trước khi upload lại pack. Câu “GIVE CREDIT IF YOU USE IT” là yêu cầu ghi công, không đủ để tự kết luận cho phép mọi hình thức phân phối hoặc thương mại. Nếu chưa rõ, public source và credit, để người dùng lấy model từ nguồn gốc.

## Tiêu chí hoàn thành

- README GitHub và CREDITS.md có đúng tên pack, Discord ID và link Hugging Face.
- Bộ release chứa file credit thật, không chỉ có lời hứa trong tài liệu.
- Release notes không nhận công train model hoặc ngụ ý được tác giả bảo trợ.
- Báo cáo đường dẫn file đã sửa và những thông tin nguồn chưa xác minh. Không tự nhắn tác giả hoặc liên hệ bên ngoài nếu chưa có yêu cầu riêng từ chủ project.
