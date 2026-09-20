# Kế hoạch cho Antigravity hỗ trợ đưa Kubo lên GitHub

## Phạm vi

Làm việc trong thư mục Kubo-github đã chuẩn bị. Không chạy git add tại project cha: nơi đó có backup, runtime, audio và dữ liệu cá nhân. Không sửa/xóa bản Kubo đang sử dụng. Bản này chưa có remote, chưa được publish và chưa có dữ liệu giọng/ảnh đi kèm.

## 1. Hoàn thiện mã nguồn có thể bàn giao

- Thực hiện `VOICE-CREDIT-TASK.md`: giữ credit pack trong README/CREDITS, đưa credit vào bản phát hành và xác minh điều khoản nguồn trước khi phân phối lại model.

- Đọc README, ASSETS và THIRD-PARTY; kiểm kê import/file cần của RVC được chọn lọc. Bổ sung mã cần thiết có giấy phép, không chép cả work hay các venv.
- Sửa script build không còn đường dẫn Lenovo/Codex. BASE_PYTHON đã đổi sang biến môi trường hoặc sys.base_prefix; vẫn phải xác minh runtime thực tế, GCC, phiên bản thư viện và đường dữ liệu.
- Chốt dependency GUI/inference trong môi trường sạch; tạo lock/constraints và script setup rõ ràng. Không coi việc copy site-packages từ máy phát triển là tái lập build.
- Kiểm tra khả năng khởi động thiếu assets/model: thông báo rõ, tránh crash im lặng. Không thay giọng +6 bằng marin để vượt test.
- Giữ quyền thư mục mặc định rỗng cho bản EXE, giữ cơ chế giới hạn file/app. Chạy kiểm tra nguồn và bản frozen sau thay đổi.
- Ghi provenance RVC (commit nếu xác minh được, thay đổi cục bộ) và giấy phép đi kèm. Chủ project chọn giấy phép mã riêng; không tự cấp quyền cho nội dung không thuộc sở hữu.

## 2. Kiểm tra chính thư mục sắp commit

- Kiểm tra cả nội dung lẫn tên file: key/token thật, .env, registry/settings, đường dẫn tài khoản, nội dung hội thoại, file media/model/binary lớn. Không in giá trị secret vào báo cáo.
- Xem git status/diff và danh sách staged trước commit. Không dùng git add từ project cha, không đính kèm backup hay release vào Git.
- .gitignore là lớp phòng ngừa, không xóa bí mật khỏi file đã tracked/history. Nếu phát hiện credential đã công khai, xử lý thu hồi riêng.
- Viết báo cáo kiểm tra gồm file count, dung lượng, các test và phần chưa kiểm chứng. Thư mục chuẩn bị hiện chưa phải sản phẩm chạy độc lập.

## 3. Chốt đích GitHub và upload

Sau khi chuẩn bị xong bản reviewable, hỏi người dùng tài khoản/tổ chức, tên repository, public/private và lựa chọn giấy phép nếu chưa có. Đề xuất private cho lần đầu nhưng không tự quyết định độ hiển thị. Không cần hỏi lại nếu người dùng đã chỉ định rõ.

Dùng đăng nhập GitHub có sẵn hoặc hướng dẫn đăng nhập chính thức; không yêu cầu dán token vào chat. Tạo repository/remote đúng đích đã xác nhận, commit mã đã kiểm tra rồi push. Không force-push hoặc ghi đè repo có sẵn. Nếu tạo PR, ghi rõ nội dung và kết quả kiểm tra. Trả link repository và commit đã đẩy để người dùng xem.

## 4. Bản tải EXE — tách khỏi source

Chỉ làm sau khi bản release đã kiểm tra và người dùng muốn phân phối. Giữ cả Kubo.exe, _internal, data, voice-engine; không upload riêng EXE. Loại model/media không có quyền phân phối, mô tả rõ gói nào người dùng phải tự cung cấp.

Mỗi asset của GitHub Releases phải dưới 2 GiB; Git thông thường chặn file trên 100 MiB. Vì gói runtime hiện nhiều GB, đo kích thước sau nén và chia archive thành các phần nhỏ hơn 2 GiB nếu cần, kèm checksum và hướng dẫn tải đủ các phần. Không lách bằng commit runtime/model vào Git. Không tạo release chỉ có source ZIP rồi gọi đó là bộ EXE.

Nguồn: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github

Gắn nhãn prerelease/bản thử nghiệm khi chưa kiểm tra máy sạch hoặc hội thoại thật. Việc đạt thử nghiệm offline không chứng minh API hoạt động cho mọi tài khoản.

## Tiêu chí bàn giao

- Repo đúng tên và độ hiển thị người dùng chọn; không có secret, backup, venv, runtime lớn.
- README mô tả đúng cách chuẩn bị assets/model, setup, chạy, build và hạn chế.
- Có bằng chứng test và thông tin nguồn RVC/giấy phép; không tuyên bố portable khi chưa thử máy sạch.
- Nếu chưa upload vì thiếu đích hoặc quyền đăng nhập: báo rõ đã chuẩn bị tới đâu, hỏi đúng thông tin thiếu; không tuyên bố đã lên GitHub.
