# Báo cáo Kiểm tra & Chuẩn bị đưa Kubo lên GitHub

**Thời điểm thực hiện:** 2026-09-21  
**Trạng thái hiện tại:** Đã chuẩn bị hoàn chỉnh cục bộ, sẵn sàng để commit và push khi người dùng xác nhận đích.

---

## 1. Thống kê tệp & Dung lượng

- **Tổng số tệp:** 224 tệp
- **Tổng dung lượng:** 1.89 MiB (1,976,725 bytes)
- **Phân loại thư mục:**
  - `Kubo/app`: 20 tệp (Mã nguồn ứng dụng GUI PySide6, Agent tools, Audio I/O, bộ unit test)
  - `Kubo/packaging`: 5 tệp (`build.py`, `build.cmd`, `kubo_gui.spec`, `kubo_voice_launcher.c`, `.env.example`)
  - `work/rvc`: 190 tệp (Mã nguồn RVC inference chọn lọc, file cấu hình, i18n locale, `LICENSE`)
  - `docs`: 5 tệp tài liệu hướng dẫn (`PUBLISH-PLAN.md`, `VOICE-CREDIT-TASK.md`, `ASSETS.md`, `THIRD-PARTY.md`, `PREPARATION-REPORT.md`)
  - Thư mục gốc: `README.md`, `CREDITS.md`, `.gitignore`, `GUI-CHO-ANTIGRAVITY.md`

---

## 2. Kết quả Rà soát An toàn & Bảo mật (Secret Audit)

- **AST Syntax Check:** 134 tệp Python (`.py` và `.pyw`) được phân tích qua Python AST. Kết quả: **0 lỗi cú pháp**.
- **Quét khóa bí mật / API Keys:** Quét toàn bộ nội dung với regex nhận diện OpenAI API keys (`sk-...`), GitHub PAT, AWS Access Keys, private tokens. Kết quả: **0 khóa bí mật được phát hiện**.
- **Quét đường dẫn tuyệt đối / Thông tin cá nhân:** Đã loại bỏ hoàn toàn các đường dẫn máy phát triển cá nhân (`C:\Users\Lenovo`). Sử dụng biến môi trường chuẩn (`KUBO_BASE_PYTHON`, `KUBO_GCC`, `sys.base_prefix`, `APPDATA`, `LOCALAPPDATA`).
- **Tệp nhị phân / Model / Dữ liệu cấm:** Không có tệp `.exe`, `.dll`, `.pyd`, `.pth`, `.pt`, `.index`, `.bin`, `.wav`, `.png`, `.zip` hay tệp có dung lượng > 1 MiB nào trong kho.
- **Loại trừ tệp tạm:** Đã dọn sạch `__pycache__` và các tệp bytecode `.pyc`.

---

## 3. Xử lý Trường hợp Thiếu Dữ liệu (Graceful Degradation)

Khi người dùng clone mã nguồn về từ GitHub mà chưa có assets/model đi kèm (theo `docs/ASSETS.md`):
1. **Giao diện Avatar (`Kubo/app/avatar.py`):**
   - Khi thiếu `assets/kubo-atlas.png`, widget không crash hay hiển thị khoảng trống trong suốt vô hình.
   - Ứng dụng tự động vẽ thẻ thông báo hiển thị rõ: *"Chưa có ảnh nhân vật (assets/kubo-atlas.png) — Xem docs/ASSETS.md"*.
2. **Nút Nghe thử giọng (`Kubo/app/app.py`):**
   - Kiểm tra tồn tại của `assets/kubo-plus6.wav`. Nếu thiếu, hiển thị hộp thoại hướng dẫn bổ sung mẫu giọng thay vì báo lỗi âm thanh không rõ nguyên nhân.
3. **Tiến trình Voice Worker & Launcher (`kubo_worker.py` & `kubo_voice.py`):**
   - Kiểm tra trọng số RVC, HuBERT, RMVPE và index trước khi suy diễn. Nếu thiếu, ném ngoại lệ kèm hướng dẫn chi tiết đến `docs/ASSETS.md`.
   - `kubo_voice.py` trích xuất thông tin lỗi trực tiếp từ nhật ký `chatbot-rvc.log` và hiển thị cảnh báo lên màn hình người dùng, giải phóng ngay tiến trình mà không bị treo 90 giây.
4. **Bộ Kiểm thử Đơn vị (`test_avatar.py`):**
   - `test_bundled_atlas` tự động kiểm tra xem tệp atlas có tồn tại không. Nếu thiếu trong bản clone GitHub, test sẽ gọi `skipTest("Thiếu dữ liệu assets/kubo-atlas.png (xem docs/ASSETS.md)")`, không báo sai kết quả (FAIL hoặc giả vờ PASS).
   - Khi chạy `python -m unittest discover -s Kubo/app`: Toàn bộ **37 test** đều đạt (**OK, 2 skipped**: 1 test symlink do quyền tài khoản Windows và 1 test atlas do không kèm nhị phân).

---

## 4. Thực hiện Ghi công Pack Giọng (Voice Credit Task)

Theo chỉ dẫn tại `docs/VOICE-CREDIT-TASK.md`:
1. **`CREDITS.md` tại gốc kho lưu trữ:**
   - Ghi nhận đầy đủ nguồn pack: **Nagisa Kubo (JP) (RVC V2 300 Epochs)**.
   - Ghi công Discord ID: `416975678542446592` (`<@416975678542446592>`) theo bài đăng gốc.
   - Đường dẫn Hugging Face: [Kuma6/Nagisa-Kubo](https://huggingface.co/Kuma6/Nagisa-Kubo).
   - Tuyên bố minh bạch: Project Kubo Desktop tích hợp model này, **không tự nhận đã train model gốc**. Thiết lập cao độ +6 là cấu hình chuyển giọng của ứng dụng.
2. **`README.md`:** Có mục credit nổi bật với đầy đủ thông tin và liên kết.
3. **Menu Ứng dụng (`Kubo/app/app.py`):**
   - Bổ sung mục menu `Nguồn giọng & Credit…` mở hộp thoại thông tin credit trực quan trong ứng dụng.
4. **Script Đóng gói (`Kubo/packaging/build.py`):**
   - Tự động sao chép `CREDITS.md` thành `licenses/CREDITS-VOICE.md` trong bản phân phối phát hành.
   - Bổ sung thông tin credit vào `README.txt` và `THIRD-PARTY-LICENSES.txt`.
5. **Xác minh Trang Nguồn:**
   - Đã kiểm tra liên kết `https://huggingface.co/Kuma6/Nagisa-Kubo`: Trang đang hoạt động công khai, tài khoản sở hữu là `Kuma6` (tên hiển thị Shira Zemach), ngày khởi tạo 11/10/2023. Ghi chú yêu cầu: "GIVE CREDIT IF YOU USE IT". Giấy phép trên Hugging Face ghi "unknown".

---

## 5. Những Việc Chưa Kiểm Chứng & Giới Hạn

1. **Chưa thử nghiệm build sạch hoàn toàn trên máy mới (Clean Machine):**
   - Bản build phát hành mới được thử nghiệm và nghiệm thu trên máy phát triển Windows 11 x64, GPU NVIDIA RTX 4060 Laptop (8GB VRAM). Chưa kiểm chứng trên máy không có sẵn runtime Python hoặc Visual C++ Redistributable.
2. **Xác thực tác giả model:**
   - Mối quan hệ giữa Discord ID `416975678542446592` và tài khoản Hugging Face `Kuma6` chưa được xác minh độc lập (chỉ căn cứ theo ảnh bài đăng của người dùng).
3. **Quyền phân phối lại Model:**
   - Yêu cầu "GIVE CREDIT IF YOU USE IT" là yêu cầu ghi công, chưa xác định rõ quyền phân phối lại dạng nhị phân thương mại. Vì vậy, kho Git chỉ chứa mã nguồn và tài liệu hướng dẫn người dùng tự tải model từ nguồn chính thức.
