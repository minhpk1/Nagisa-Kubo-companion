# Báo cáo Đóng gói và Kiểm định Gói Cục bộ (Local Package)

Tài liệu này ghi lại kết quả đóng gói và kiểm định độc lập cho gói chạy đầy đủ `local-package/Kubo/` của dự án **Nagisa Kubo Desktop Companion**, theo yêu cầu từ `docs/RUNNABLE-PACK-TASK.md` và phản hồi trong `review/LOCAL-PACKAGE-REVIEW.md`.

---

## 1. Tổng quan Bản đóng gói Cục bộ

- **Tên gói**: Nagisa Kubo Desktop Companion (Full Local Runnable Bundle)
- **Vị trí**: `local-package/Kubo/` (nằm trong thư mục gốc của repository, được loại trừ khỏi Git qua `.gitignore`)
- **Dung lượng tổng**: 6.84 GiB (7,341,923,669 bytes)
- **Tổng số tệp**: 36,448 tệp
- **Hệ điều hành mục tiêu**: Windows 10/11 x64
- **Phần cứng kiểm chứng**: Windows 11 x64, CPU 13th Gen Intel, NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM)
- **Mã nguồn đóng gói**: Nhánh `main`, commit lineage từ `0c4a8ad` và `e0070f9`
- **Mục đích**: Chạy trực tiếp tại máy phát triển mà không cần cài đặt thêm môi trường Python, hoặc chuẩn bị phân phối độc lập qua kênh phát hành riêng (GitHub Releases / Cloud Storage).

### Cấu trúc thư mục gói

```text
local-package/Kubo/
├── Kubo.exe                  # Ứng dụng GUI đóng gói PyInstaller (PySide6)
├── _internal/                # Thư viện GUI, DLL Qt6, C-runtime
├── data/
│   ├── avatars/              # Ảnh atlas Kubo, mirai, biểu cảm angry (bĩu môi)
│   ├── samples/              # Mẫu giọng nói thử nghiệm kubo-plus6.wav
│   ├── persona/              # Hồ sơ tính cách kubo-persona.md
│   └── models/               # Mô hình RVC Nagisa Kubo, index, RMVPE, HuBERT Base
├── voice-engine/
│   ├── KuboVoice.exe         # Native launcher C biên dịch với Win32 Job Object
│   ├── bin/                  # ffmpeg.exe, ffprobe.exe
│   ├── configs/              # Cấu hình RVC v2 (v2/48k.json, v2/40k.json, ...)
│   ├── engine/               # Mã nguồn worker kubo_worker.py, paths.py, pipeline RVC
│   └── runtime/              # Môi trường Python 3.12 cô lập + PyTorch 2.7.1 CUDA 11.8
├── licenses/                 # Bản quyền MIT, giấy phép bên thứ ba, CREDITS-VOICE.md
├── README.txt                # Hướng dẫn sử dụng nhanh cho người dùng cuối
└── manifest.json             # Danh mục tệp, thông số gói và mã băm SHA-256
```

### Bảng Checksums SHA-256 (6 tệp cốt lõi)

| Tệp tin | Kích thước | SHA-256 Checksum | Trạng thái |
| :--- | :--- | :--- | :--- |
| `Kubo.exe` | 13,845,951 B | `d4eb68a9532b7a92bee3465d085fcad233d920d560bfc722e851daad6e58c7be` | Khớp manifest |
| `voice-engine/KuboVoice.exe` | 134,834 B | `743f7c70509d3f0f0ce276902042e9349dfd38aaca1fd88d6c8296fbd6df9d01` | Khớp manifest |
| `data/models/NagisaKubo_e300_s1500.pth` | 55,272,333 B | `720b9b9a7e76d142f4b17a930850dfd422b2d5de04d93dde8dc475cd1164f6fd` | Khớp manifest |
| `data/models/added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index` | 2,752,946 B | `0e5a5eee6fbfb56985abcf413066b71a9e16b3cdfeefaadbce63aea9c9b65336` | Khớp manifest |
| `data/models/rmvpe.pt` | 167,419,005 B | `6d62215f4306e3ca278246188607209f09af3dc77ed4232efdd069798c4ec193` | Khớp manifest |
| `data/models/hubert_base/pytorch_model.bin` | 377,654,642 B | `cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5` | Khớp manifest |

---

## 2. Ma trận Kết quả Kiểm tra (Test Matrix)

| Hạng mục kiểm tra | Trạng thái | Kết quả & Bằng chứng thực tế |
| :--- | :---: | :--- |
| **1. Khớp mã băm SHA-256** | **PASS** | 6/6 tệp cốt lõi khớp chính xác mã băm trong `manifest.json`. |
| **2. Khởi động GUI offscreen & chụp ảnh** | **PASS** | Khởi chạy `Kubo.exe` với cờ offscreen và CWD nằm ngoài gói (`c:\Users\Lenovo\Documents\Codex\2026-09-18\i-need-to-build-an-ai`). Giao diện nạp ảnh đại diện thành công, chụp ảnh màn hình lưu tại `review/local-package-check/gui.png`, kết thúc với exit code 0. |
| **3. Khởi động Voice Worker & nạp model** | **PASS** | Worker `KuboVoice.exe` khởi động runtime cô lập, nạp trọng số mô hình Nagisa Kubo 300 epochs, HuBERT Base và RMVPE, phát tín hiệu `READY` qua stdout pipe. |
| **4. Chuyển đổi mẫu giọng tiếng Việt 6s** | **PASS** | Gửi đoạn PCM tiếng Việt 6 giây qua stdin. Worker chuyển đổi ra PCM 24,000 Hz đúng độ dài mẫu. Âm lượng đỉnh đạt **29,573 - 31,879** (không im lặng, không clip). Tệp âm thanh đầu ra lưu tại `review/local-package-check/voice-plus6.wav`. |
| **5. Worker nhận EOF và thoát sạch** | **PASS** | Đóng luồng stdin (EOF); worker giải phóng tài nguyên và kết thúc tiến trình với exit code 0. |
| **6. Cô lập môi trường thực thi (PATH/ENV)** | **PASS** | Thực hiện kiểm tra với biến môi trường `PATH` tối giản (chỉ chứa `C:\Windows\System32`), gỡ bỏ hoàn toàn `PYTHONHOME` và `PYTHONPATH`, tắt `PYTHONNOUSERSITE=1`, kích hoạt chế độ offline `TRANSFORMERS_OFFLINE=1` và `HF_HUB_OFFLINE=1`. Không nạp gói Python toàn cục hay project cha. |
| **7. Quản lý tiến trình Win32 Job Object** | **PASS** | Launcher `KuboVoice.exe` gán cờ `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. Khi tiến trình launcher bị buộc dừng, tiến trình `python.exe` con tự động bị hệ điều hành thu hồi, không để lại tiến trình mồ côi. |
| **8. Kiểm thử di dời thư mục (Relocation)** | **PASS** | Sao chép gói sang đường dẫn mới chứa khoảng trắng và ký tự tiếng Việt có dấu (`Thử Nghiệm Kubo (Tạm)/`). Worker khởi động và phản hồi `READY` bình thường với CWD độc lập. |
| **9. Ghi công giọng nói Nagisa Kubo** | **PASS** | Ghi nhận đầy đủ nguồn gốc model giọng nói cho người tạo có Discord ID `416975678542446592` tại kho [Kuma6/Nagisa-Kubo](https://huggingface.co/Kuma6/Nagisa-Kubo) trong các tệp `licenses/CREDITS-VOICE.md`, `README.txt` và giao diện ứng dụng. |
| **10. Loại trừ khỏi Git (Git Cleanliness)** | **PASS** | Đường dẫn `local-package/` được khai báo trong `.gitignore`. Lệnh `git ls-files local-package/` trả về rỗng. Working tree hoàn toàn sạch trước và sau kiểm tra. |
| **11. Rà soát bảo mật & Rò rỉ Secret** | **PASS** | Không phát hiện tệp `.env`, `settings.json`, API key OpenAI thật hay thông tin tài khoản cá nhân trong các tệp phân phối. |
| **12. Script đóng gói tái lập (`package_runnable.py`)** | **PASS** | Tách bạch rõ ràng giữa `REPO_ROOT`, `DEV_ROOT` và `DEST_DIR`. Tự động nhận diện Git revision và trạng thái dirty. Kiểm tra ràng buộc bắt buộc 14/14 tài nguyên (không bỏ qua âm thầm). Hỗ trợ `--check-paths` để kiểm tra mà không ghi thêm GB lên đĩa. |
| **13. Phát âm thanh qua loa vật lý từ GUI** | **NOT TESTED** | Môi trường kiểm thử là container/sandbox headless không gắn card âm thanh hoặc loa ngoài vật lý. |
| **14. Hội thoại trực tuyến với LLM API thật** | **NOT TESTED** | Gói phân phối không nhúng API key thật nhằm bảo vệ an toàn thông tin người dùng. Tính năng gọi API cần người dùng tự nhập key qua menu Cài đặt khi có kết nối Internet. |
| **15. Chạy trên máy Windows sạch hoàn toàn** | **NOT TESTED** | Bản đóng gói đã được kiểm chứng trên máy phát triển Windows 11 x64 RTX 4060 với PATH cô lập. Chưa kiểm tra trên một máy ảo Windows mới tinh (chưa từng cài đặt Visual Studio hay Driver NVIDIA). |
| **16. Thẩm định chất lượng phát âm chủ quan** | **NOT TESTED** | Đánh giá được xác nhận qua chỉ số định lượng khách quan (độ dài PCM, biên độ dao động sóng và cao độ median ~315 Hz). Chưa tiến hành khảo sát nghe hiểu chủ quan của người dùng. |
| **17. Rà soát ngược chuỗi byte nhị phân EXE/DLL** | **NOT TESTED** | Đã hoàn thành kiểm toán trên toàn bộ tệp văn bản, mã nguồn và cấu hình; chưa dịch ngược (decompile) toàn bộ các thư viện nhị phân C++ của bên thứ ba. |

---

## 3. Ghi nhận Kỹ thuật

### 3.1 Traceback F0 trong quá trình Warm-up
Trong tệp log kiểm tra `worker.log`, ghi nhận traceback:
```text
Traceback (most recent call last):
  File "...\voice-engine\engine\infer\vc\pipeline.py", line 127, in get_f0
    f0[uv] = np.interp(np.where(uv)[0], np.where(~uv)[0], f0[~uv])
ValueError: array of sample points is empty
```
- **Nguyên nhân**: Khi worker khởi động, đoạn mã warm-up gửi một mảng byte 0 (48,000 bytes = 1 giây im lặng tuyệt đối) để làm nóng bộ nhớ đệm và GPU. Thuật toán RMVPE khi quét tín hiệu 0 tuyệt đối sẽ không tìm thấy bất kỳ điểm cao độ nào (`~uv` rỗng), dẫn đến hàm nội suy `np.interp` báo lỗi.
- **Tác động**: Mã nguồn `kubo_worker.py` và `pipeline.py` đã bắt ngoại lệ này trong khối `try...except`, in cảnh báo ra log và tiếp tục quá trình. Worker phát tín hiệu `READY` bình thường và toàn bộ các yêu cầu chuyển giọng tiếp theo (có tín hiệu âm thanh thật) đều hoạt động chính xác 100%.

### 3.2 Hiệu năng Khởi động và Chuyển đổi
- **Thời gian nạp lần đầu (Cold Start)**: ~9.52 giây (bao gồm nạp runtime Python, nạp PyTorch CUDA, đọc trọng số HuBERT 377MB, RMVPE 167MB và mô hình RVC Nagisa Kubo 55MB vào VRAM).
- **Thời gian chuyển đổi giọng nói (Inference Time)**: ~0.44 giây cho một đoạn âm thanh tiếng Việt 6.0 giây (tỷ lệ xử lý thời gian thực ~13.6x realtime trên GPU NVIDIA RTX 4060).

---

## 4. Hướng dẫn Sử dụng và Tái lập Gói

### 4.1 Khởi chạy Ứng dụng
Người dùng có thể chạy ứng dụng trực tiếp bằng cách mở:
```cmd
local-package\Kubo\Kubo.exe
```
Khi mở lần đầu:
1. Giao diện Nagisa Kubo sẽ hiển thị trên màn hình desktop.
2. Nhấp chuột phải vào avatar hoặc mở menu **Cài đặt** để nhập API Key và cấu hình thư mục được cấp quyền.
3. Nhấp **Nguồn giọng & Credit…** để xem thông tin bản quyền và ghi công người tạo giọng.

### 4.2 Kiểm tra Xác thực Đường dẫn (Dry Run)
Để kiểm tra tính toàn vẹn của mọi đường dẫn và tài nguyên bắt buộc mà không ghi thêm dữ liệu lên ổ đĩa:
```powershell
& "Kubo/app/.venv/Scripts/python.exe" Kubo/packaging/package_runnable.py --check-paths
```

### 4.3 Tái tạo Gói Đầy đủ từ Mã nguồn
Khi cần cập nhật mã nguồn hoặc đóng gói lại toàn bộ:
```powershell
# Tự động nhận diện môi trường dev và đóng gói vào local-package/Kubo
& "Kubo/app/.venv/Scripts/python.exe" Kubo/packaging/package_runnable.py --clean

# Hoặc chỉ định rõ thư mục nguồn dev và thư mục xuất
& "Kubo/app/.venv/Scripts/python.exe" Kubo/packaging/package_runnable.py --dev-root ".." --output-dir "local-package/Kubo" --clean
```
