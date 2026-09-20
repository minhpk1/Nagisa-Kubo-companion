# Kubo — trợ lý AI desktop cho Windows

Ứng dụng Python/PySide6 với nhân vật trên desktop, hội thoại giọng nói, biểu cảm theo văn bản và công cụ tìm/đọc/mở file hoặc ứng dụng được cấp quyền. Giọng trả lời đi qua RVC cục bộ; cấu hình dự án hiện dùng cao độ +6.

**Trạng thái:** bản chuẩn bị mã nguồn để đưa lên GitHub. Chưa phải bản clone về chạy ngay: không kèm ảnh, audio, model, môi trường Python hoặc EXE. Các thành phần này cần được cung cấp riêng với quyền sử dụng phù hợp. Bản build Windows đã được thử offline trên máy phát triển; chưa xác nhận trên máy sạch hoặc phiên hội thoại trực tuyến từ EXE.

## Cấu trúc

- `Kubo/app`: giao diện, hội thoại, công cụ Agent, worker và kiểm tra tự động.
- `Kubo/packaging`: script/cấu hình đóng gói Windows; còn cần xác minh build sạch.
- `work/rvc`: phần mã RVC hiện dùng được chọn lọc, giữ giấy phép gốc; không phải toàn bộ WebUI/train.
- `docs`: tài nguyên cần bổ sung, việc chuẩn bị publish và thông tin bên thứ ba.

Giữ cấu trúc này khi build: mã hiện tại sử dụng thư mục project gốc để tìm work/rvc và các môi trường. Không di chuyển riêng app mà chưa cập nhật đường dẫn.

## Chạy từ mã nguồn — sau khi bổ sung dữ liệu

1. Chuẩn bị Python 3.12 x64 trên Windows; tạo môi trường GUI ở `Kubo/app/.venv`, cài `Kubo/app/requirements.txt`.
2. Chuẩn bị môi trường inference ở `work/rvc-env` với phiên bản thư viện đã kiểm chứng. Các file requirments của upstream là tài liệu tham khảo, chưa phải lockfile tối thiểu cho gói này.
3. Bổ sung dữ liệu theo `docs/ASSETS.md`. Không chỉ có model Kubo: còn cần HuBERT, RMVPE và FFmpeg.
4. Mở `Kubo/app/Launch.cmd`. Khi chưa có môi trường GUI, launcher có thể cần tải thư viện. Nhập API key qua Cài đặt, không commit key.
5. Cấp đúng thư mục/app muốn dùng trong Cài đặt. RVC lỗi thì phiên dừng; không tự thay bằng giọng nền.

Ảnh và chuyển giọng chạy cục bộ; hội thoại cần dịch vụ trực tuyến phù hợp và có thể phát sinh phí. Tắt micro/ẩn cửa sổ không kết thúc phiên; dùng Ngắt kết nối hoặc Thoát.

## Build và kiểm tra

Ưu tiên bộ `Kubo.exe` cùng `_internal`, `data`, `voice-engine`; không đưa các thư mục build này vào Git. Script ở `Kubo/packaging` là điểm bắt đầu, không cam kết build từ môi trường sạch trước khi hoàn thành `docs/PUBLISH-PLAN.md`. `KUBO_BASE_PYTHON` và `KUBO_GCC` có thể chỉ định Python gốc và GCC khi build; không cần đường dẫn tài khoản người phát triển.

Kiểm tra source: chạy Python trong môi trường GUI với `-m unittest discover -s Kubo/app -p "test_*.py"` từ thư mục gốc. Một số kiểm tra cần dữ liệu riêng; ghi rõ thiếu dữ liệu, không giả báo đạt.

## Credit giọng Kubo

Pack **Nagisa Kubo (JP), RVC V2, 300 epochs** được ghi công cho người tạo có Discord ID `416975678542446592` trong bài đăng nguồn do người dùng cung cấp. Pack được lưu trên [Kuma6/Nagisa-Kubo](https://huggingface.co/Kuma6/Nagisa-Kubo). Project này tích hợp model có sẵn, không tự nhận đã train model gốc. Xem [CREDITS.md](CREDITS.md) để biết nguồn và thông tin xác minh.

## Giấy phép

Mã nguồn do dự án Kubo phát triển được phát hành theo [MIT License](LICENSE).
Mã nguồn RVC được giữ theo giấy phép gốc tại `work/rvc/LICENSE`; xem [docs/THIRD-PARTY.md](docs/THIRD-PARTY.md).
Ghi công và điều khoản pack giọng Nagisa Kubo được lưu tại [CREDITS.md](CREDITS.md). Dự án không khẳng định quyền sở hữu hay phân phối hình ảnh/giọng/mô hình gốc của nhân vật (xem [docs/ASSETS.md](docs/ASSETS.md)).
