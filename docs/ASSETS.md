# Dữ liệu không có trong Git

Đợt chuẩn bị này chủ động không đưa bitmap, mẫu âm thanh hoặc model vào repository. Chủ sở hữu quyết định dữ liệu nào được phép phát hành sau khi kiểm tra nguồn/quyền phân phối.

Đường dẫn app đang dùng:

- Kubo/app/assets/kubo-atlas.png — atlas 3x3 nhân vật.
- Kubo/app/assets/angry.png — ảnh bĩu môi thay biểu cảm giận.
- Kubo/app/assets/kubo-plus6.wav — mẫu nghe thử.
- Kubo/voice/NagisaKubo/Nagisa Kubo/NagisaKubo_e300_s1500.pth.
- Kubo/voice/NagisaKubo/Nagisa Kubo/added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index.
- work/rvc/assets/weights và assets/indices — bản model/index cho chạy source.
- work/rvc/assets/rmvpe/rmvpe.pt.
- work/rvc/assets/hubert_base/ — config.json, preprocessor_config.json, pytorch_model.bin theo runtime đang dùng.
- work/rvc/ffmpeg.exe, và ffprobe.exe nếu đường xử lý cần probe.

Build hiện còn sao chép mẫu +4/+5 và mirai-atlas nếu có. Antigravity cần loại tài nguyên không dùng hoặc mô tả rõ tài nguyên tùy chọn, thay vì buộc tải thêm ảnh Mirai.

Không tự chọn link model khác hoặc train lại: giữ đúng model/index và thiết lập +6 đã kiểm chứng. Nếu không có quyền phân phối, cung cấp hướng dẫn người dùng tự bổ sung dữ liệu thay vì đưa lên Releases.
