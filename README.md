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
## Tải Bản Phát Hành Sẵn Dùng (GitHub Releases)

Đối với người dùng muốn tải bản chạy ngay mà không cần chuẩn bị môi trường Python hoặc tải thủ công các mô hình AI:
1. Truy cập mục **Releases** của repository: tải trọn bộ bản phát hành **v1.0.0**.
2. Tải 3 tệp về **cùng một thư mục**:
   - `Kubo-v1.0.0-windows-x64.zip.001` (1.81 GiB)
   - `Kubo-v1.0.0-windows-x64.zip.002` (1.67 GiB)
   - `extract.cmd` (tiện ích tự động gộp & giải nén cho Windows)
3. Nhấp đúp chuột vào `extract.cmd` để tự động ghép nhị phân và giải nén thành thư mục `Kubo\`.
4. Mở `Kubo\Kubo.exe` để trải nghiệm ứng dụng ngay lập tức!

Chi tiết ghi chú phát hành, bảng mã băm SHA-256 và danh sách lưu ý kiểm định xem tại [docs/RELEASE-V1.0.0.md](docs/RELEASE-V1.0.0.md).

## Build và kiểm tra

Ưu tiên bộ `Kubo.exe` cùng `_internal`, `data`, `voice-engine`; không đưa các thư mục build này vào Git. Script ở `Kubo/packaging` là điểm bắt đầu, không cam kết build từ môi trường sạch trước khi hoàn thành `docs/PUBLISH-PLAN.md`. `KUBO_BASE_PYTHON` và `KUBO_GCC` có thể chỉ định Python gốc và GCC khi build; không cần đường dẫn tài khoản người phát triển.

Kiểm tra source: chạy Python trong môi trường GUI với `-m unittest discover -s Kubo/app -p "test_*.py"` từ thư mục gốc. Một số kiểm tra cần dữ liệu riêng; ghi rõ thiếu dữ liệu, không giả báo đạt.

### Phân biệt Mã nguồn Git và Gói chạy đầy đủ (Local Package)

- **Mã nguồn trên Git**: Kho Git chỉ lưu trữ mã nguồn ứng dụng, bộ kiểm thử và tài liệu hướng dẫn (~1.9 MiB). Để giữ kho gọn nhẹ và tôn trọng bản quyền, Git **không lưu trữ** các model AI, ảnh nhân vật, tệp âm thanh hay runtime Python nặng nhiều GB. Người dùng tự chuẩn bị hoặc tải dữ liệu theo [docs/ASSETS.md](docs/ASSETS.md).
- **Gói chạy đầy đủ (`local-package/Kubo/`)**: Bản đóng gói độc lập đầy đủ (~6.84 GiB, 36,448 tệp) bao gồm sẵn `Kubo.exe`, runtime PyTorch CUDA, mô hình RVC Nagisa Kubo +6, HuBERT, RMVPE, FFmpeg và toàn bộ assets. Gói này dùng để chạy thử nghiệm trực tiếp trên máy hoặc chuẩn bị phát hành riêng ngoài Git. Thư mục `local-package/` được loại trừ trong `.gitignore` và không bao giờ commit vào Git.
  - **Khởi chạy ứng dụng ngay**: Mở `local-package\Kubo\Kubo.exe`.
  - **Báo cáo kiểm định độc lập**: Xem kết quả kiểm thử thực tế với phân định rõ **PASS / FAIL / NOT TESTED** tại [docs/LOCAL-PACKAGE-REPORT.md](docs/LOCAL-PACKAGE-REPORT.md).
  - **Kiểm tra xác thực đường dẫn gói (Dry Run)**:
    ```powershell
    python Kubo/packaging/package_runnable.py --check-paths
    ```
  - **Tái tạo gói từ mã nguồn**:
    ```powershell
    # Tự động nhận diện nguồn dev cha và biên dịch lại GUI
    python Kubo/packaging/package_runnable.py --clean

    # Hoặc chỉ định rõ thư mục dev và thư mục xuất
    python Kubo/packaging/package_runnable.py --dev-root "path/to/dev" --output-dir "path/to/local-package/Kubo" --clean
    ```

## Credit giọng Kubo

Pack **Nagisa Kubo (JP), RVC V2, 300 epochs** được ghi công cho người tạo có Discord ID `416975678542446592` trong bài đăng nguồn do người dùng cung cấp. Pack được lưu trên [Kuma6/Nagisa-Kubo](https://huggingface.co/Kuma6/Nagisa-Kubo). Project này tích hợp model có sẵn, không tự nhận đã train model gốc. Xem [CREDITS.md](CREDITS.md) để biết nguồn và thông tin xác minh.

## Giấy phép

Mã nguồn do dự án Kubo phát triển được phát hành theo [MIT License](LICENSE).
Mã nguồn RVC được giữ theo giấy phép gốc tại `work/rvc/LICENSE`; xem [docs/THIRD-PARTY.md](docs/THIRD-PARTY.md).
Ghi công và điều khoản pack giọng Nagisa Kubo được lưu tại [CREDITS.md](CREDITS.md). Dự án không khẳng định quyền sở hữu hay phân phối hình ảnh/giọng/mô hình gốc của nhân vật (xem [docs/ASSETS.md](docs/ASSETS.md)).
