# Nagisa Kubo Desktop Companion v1.0.0 (Windows x64)

Phiên bản phát hành chính thức đầu tiên của **Nagisa Kubo Desktop Companion** dành cho hệ điều hành Windows 10/11 x64.

Ứng dụng tích hợp nhân vật desktop tương tác, chuyển giọng RVC cục bộ với cao độ +6, biểu cảm hoạt họa theo ngữ cảnh và bộ công cụ Agent quản lý tệp tin/ứng dụng với cơ chế kiểm soát quyền an toàn.

---

## 1. Tải về và Cài đặt

Do kích thước của gói chạy độc lập đầy đủ (bao gồm PyTorch CUDA, mô hình RVC Nagisa Kubo, HuBERT Base và RMVPE) là **3.47 GiB sau khi nén**, vượt quá giới hạn 2.0 GiB/tệp của GitHub Releases, gói phân phối được chia thành 2 phần nhị phân liên tục tiêu chuẩn.

### Danh mục tệp phát hành (Release Assets)

| Tệp tải về | Kích thước | Mã băm SHA-256 | Mô tả |
| :--- | :--- | :--- | :--- |
| **`Kubo-v1.0.0-windows-x64.zip.001`** | 1,939,865,600 B (1.81 GiB) | `44d3d20cbceab99a8e87a443e51be3949b21c783a44eed4b2943d092132c43d6` | Phần 1 của gói chạy đầy đủ |
| **`Kubo-v1.0.0-windows-x64.zip.002`** | 1,788,332,621 B (1.67 GiB) | `c3eaf24eb63ba6828b7546badfffb219492bbb1323ab554dd0425ef741657962` | Phần 2 của gói chạy đầy đủ |
| **`extract.cmd`** | 1,715 B | `321a6039fe65ef25dd06cf22d4fc1e34226a27e740cf2ae23f5b3558c422894d` | Tiện ích một chạm tự động gộp và giải nén trên Windows |
| **`SHA256SUMS.txt`** | 1,348 B | — | Danh sách mã băm kiểm tra toàn vẹn |

> **Tệp nén gộp hoàn chỉnh (Merged)**: `Kubo-v1.0.0-windows-x64.zip` (3,728,198,221 bytes / 3.47 GiB)  
> **SHA-256 Full Archive**: `0f0da46872eb39ed27d49d58dd8619064376adaf3cf36dbacf9d17d6e1688cff`

---

### Hướng dẫn Cài đặt Nhanh (Khuyến nghị)

1. Tải cả 3 tệp về **cùng một thư mục**:
   - `Kubo-v1.0.0-windows-x64.zip.001`
   - `Kubo-v1.0.0-windows-x64.zip.002`
   - `extract.cmd`
2. Nhấp đúp chuột vào tệp **`extract.cmd`**.
   - Tiện ích sẽ tự động dùng lệnh nhị phân của Windows để ghép thành file `Kubo-v1.0.0-windows-x64.zip` và giải nén ra thư mục `Kubo\`.
   - Không yêu cầu cài đặt thêm 7-Zip hay WinRAR.
3. Mở thư mục `Kubo\` và nhấp đúp vào **`Kubo.exe`** để bắt đầu sử dụng!

---

### Hướng dẫn Gộp Thủ công (Nâng cao)

Nếu muốn gộp và giải nén bằng dòng lệnh hoặc công cụ riêng:

```cmd
:: Mở Command Prompt (cmd) tại thư mục chứa các file đã tải:
copy /b Kubo-v1.0.0-windows-x64.zip.001 + Kubo-v1.0.0-windows-x64.zip.002 Kubo-v1.0.0-windows-x64.zip
```

Sau khi gộp xong, bạn có thể nhấp chuột phải vào `Kubo-v1.0.0-windows-x64.zip` chọn **Extract All...** (hoặc dùng 7-Zip / WinRAR / NanaZip).

---

## 2. Các Thành phần Đã kiểm định (Verified Features)

- [x] **Giao diện PySide6 Desktop Companion**: Nhân vật hiển thị trên desktop, kéo thả di chuyển vị trí, menu chuột phải (Cài đặt, Giọng nói, Thoát).
- [x] **Hệ thống Biểu cảm Tự động**: Render atlas ảnh Kubo và biểu cảm theo ngữ cảnh (bĩu môi, vui vẻ, bình thường).
- [x] **Bộ chuyển giọng RVC v2 Cục bộ**: Nạp sẵn mô hình Nagisa Kubo 300 epochs, cao độ +6 pitch, HuBERT Base và RMVPE.
- [x] **Trình quản lý tiến trình an toàn (Win32 Job Object)**: `KuboVoice.exe` đảm bảo tự động thu hồi sạch tiến trình Python ngầm khi đóng ứng dụng, chống treo tiến trình mồ côi.
- [x] **Cô lập môi trường**: Không xung đột với các phiên bản Python khác đã cài trên máy.
- [x] **Bảo mật**: 0 API key nhúng ngầm, 0 cấu hình cá nhân. Quyền truy cập tệp tin và ứng dụng của Agent mặc định ở trạng thái rỗng và người dùng toàn quyền cấp/hủy qua UI.

---

## 3. Những Phần Chưa Kiểm chứng (Unverified Aspects)

Người dùng và cộng đồng cần lưu ý các điểm chưa được kiểm chứng đầy đủ trong bản phát hành này:

1. **Phát âm thanh ra loa ngoài vật lý**:
   - Trong quá trình đóng gói và kiểm thử tự động trên môi trường phát triển headless, hệ thống đã kiểm tra tính toàn vẹn của dữ liệu sóng âm PCM (độ dài chính xác, biên độ đỉnh 29,573 - 31,879 non-silent, không clip).
   - Chưa tiến hành thẩm âm trực tiếp qua card âm thanh và loa vật lý.
2. **Phiên hội thoại trực tiếp với LLM API thật**:
   - Bản phát hành không kèm bất kỳ API key nào vì lý do bảo mật.
   - Để trò chuyện, người dùng cần có kết nối Internet và tự nhập API key (OpenAI / Gemini hoặc dịch vụ tương thích) trong menu **Cài đặt**.
3. **Môi trường Windows trắng tinh (Clean Machine)**:
   - Bản phân phối đã được kiểm tra trên Windows 11 x64 với cấu hình PATH tối giản (`C:\Windows\System32`) và tắt hoàn toàn user-site.
   - Chưa được kiểm định trên một máy ảo Windows mới cài đặt hoàn toàn chưa từng cài driver NVIDIA hoặc Visual C++ Redistributables.
4. **Khả năng tương thích GPU ngoài NVIDIA**:
   - Bộ runtime RVC hiện tại tối ưu cho NVIDIA GPU qua CUDA 11.8. Trên các máy không có GPU NVIDIA (chỉ dùng CPU hoặc GPU tích hợp), quá trình chuyển giọng có thể chạy ở chế độ CPU chậm hơn hoặc cần cấu hình bổ sung.

---

## 4. Ghi công Bản quyền & Giấy phép (Credits & Licenses)

### Mô hình Giọng nói Nagisa Kubo
- **Tác giả Voice Pack**: Ghi nhận công lao người tạo mô hình có Discord ID `416975678542446592` trong bài đăng nguồn do người dùng cung cấp.
- **Nguồn lưu trữ**: [Kuma6/Nagisa-Kubo](https://huggingface.co/Kuma6/Nagisa-Kubo) trên Hugging Face.
- **Cấu hình**: RVC v2, 300 epochs, pitch +6, index 0.75, RMS mix 0.25, protect 0.33.
- Dự án tích hợp và tinh chỉnh tham số để đồng hành cùng nhân vật, không tự nhận là bên đã huấn luyện (train) mô hình gốc.

### Giấy phép Phần mềm
- Mã nguồn ứng dụng do dự án Kubo phát triển được phát hành theo [MIT License](LICENSE).
- Mô-đun suy luận RVC tuân theo giấy phép gốc của RVC Project tại `work/rvc/LICENSE`.
- Chi tiết đầy đủ xem tại [CREDITS.md](CREDITS.md) và [docs/THIRD-PARTY.md](docs/THIRD-PARTY.md).
