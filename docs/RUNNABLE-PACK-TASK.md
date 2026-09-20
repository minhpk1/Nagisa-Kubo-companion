# Việc bổ sung cho Antigravity: tạo thư mục Kubo chạy đầy đủ

## Yêu cầu của người dùng

Người dùng muốn đưa các file cần thiết để chạy vào một thư mục hoàn chỉnh. Hãy thực hiện việc sao chép và kiểm thử, không chỉ viết hướng dẫn hoặc tạo thư mục trống. Làm trên bản sao; không di chuyển/xóa dữ liệu app đang dùng hay backup.

## Đầu ra

Tạo `Kubo-github/local-package/Kubo/` gồm:

```text
Kubo.exe
_internal/
data/
  avatars/
  samples/
  persona/
  models/
voice-engine/
licenses/
README.txt
manifest.json
```

Thư mục này dùng để chạy tại máy và chuẩn bị gói tải riêng. Nó không thuộc nội dung commit source. Giữ nguyên quy tắc ignore `local-package/`; không dùng git add -f để đưa model, runtime hoặc EXE vào Git. Người dùng yêu cầu gom dữ liệu cục bộ, chưa phải yêu cầu upload công khai model/media.

## Nguồn dữ liệu có sẵn

Từ project cha của Kubo-github:

- `Kubo/release/Kubo/`: bộ EXE/runtime đã được kiểm tra offline. Kiểm tra lại bản thực tế trước khi lấy; không coi báo cáo cũ là bằng chứng cho file mới.
- `Kubo/app/assets/`: kubo-atlas.png, angry.png (bĩu môi), kubo-plus6.wav.
- `Kubo/app/kubo-persona.md`: tính cách hiện tại. So sánh với bản source trong repo để chọn phiên bản đã chốt, không ghi đè tùy tiện.
- `Kubo/voice/NagisaKubo/Nagisa Kubo/`: NagisaKubo_e300_s1500.pth và added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index.
- `work/rvc/assets/`: RMVPE và bộ HuBERT hiện dùng.
- `work/rvc`: mã inference, cấu hình, FFmpeg/FFprobe nếu luồng chạy cần.

Ưu tiên sao chép toàn bộ bundle release đã kiểm chứng làm nền, rồi đồng bộ các bản sửa mới bằng build có thể tái lập. Không trộn file EXE cũ với thư viện/mã worker mới mà không kiểm tra. Nếu source GitHub có thay đổi chưa có trong release, build lại đúng source hoặc ghi rõ revision khác nhau; không tự nhận gói phản ánh commit mới nhất.

## Công việc cụ thể

1. Kiểm kê file thật sự được nạp khi chạy GUI và chuyển giọng. Đảm bảo mọi model/tokenizer/config/DLL/codec và thư viện bắc cầu cần đều đi kèm. Không chỉ chép file PTH/index hoặc Kubo.exe riêng lẻ.
2. Giữ đúng model Kubo, +6, RMVPE, index 0.75, RMS 0.25, protect 0.33. Không thay bằng marin hoặc model khác để làm gói chạy được.
3. Gói phải có runtime của riêng nó; không tham chiếu bắt buộc tới work/rvc-env, Python của Codex, tài khoản Lenovo hoặc project cha. Không chép nguyên venv và mặc định coi nó portable.
4. Không kèm API key, .env thật, registry/settings cá nhân, quyền thư mục/app đã lưu, log hội thoại, backup hoặc dữ liệu train không phục vụ inference. Người dùng nhập key qua UI, tự cấp quyền thư mục khi chạy.
5. Thêm CREDITS.md vào `licenses/CREDITS-VOICE.md`; README.txt ghi người tạo pack, Discord ID `416975678542446592` và nguồn Kuma6/Nagisa-Kubo. Giữ giấy phép phần mềm và thông tin nguồn; không nhận công train model gốc.
6. Tạo manifest từ chính file cuối cùng: checksum, dung lượng, phiên bản, commit source nếu có. Thêm script đóng gói dưới Kubo/packaging để lần sau lặp lại được, không chỉ vá thủ công bundle.
7. Cập nhật README GitHub phân biệt source thiếu dữ liệu và gói chạy đầy đủ cục bộ. Chỉ thêm link tải khi đã có link thật. Hoàn thiện hướng dẫn setup source riêng; không bỏ qua vì EXE đã chạy.

## Kiểm tra bắt buộc

- Chép gói thật sang thư mục thử có dấu/khoảng trắng; không chỉ tạo junction về bản cũ. Chạy với cwd khác.
- Kubo.exe mở được, hiện avatar, ảnh bĩu môi và phát mẫu +6.
- Worker chạy từ bundle: READY → chuyển mẫu tiếng Việt → đúng độ dài/không im lặng → dừng sạch. Không bổ sung đường dẫn project cha vào PATH để vượt bài kiểm tra.
- Kiểm tra GUI frozen gọi worker, lỗi thiếu model và hủy lúc nạp/chuyển giọng; không bỏ lại Python con.
- Kiểm tra mặc định quyền Agent rỗng cho người dùng mới, đọc/mở chỉ trong phạm vi được cấp.
- Chạy máy sạch nếu có. Nếu chưa có, ghi NOT TESTED; chạy trên máy phát triển không chứng minh chạy mọi máy.
- Hội thoại vẫn cần Internet/API và driver GPU phù hợp. Không nhúng credential thật để demo. Ghi rõ phép thử trực tuyến nào chưa thực hiện.
- Kiểm tra git status và git ls-files: `local-package/` phải không có trong staged/tracked files.

## Nếu tiếp tục đưa gói lên GitHub Releases

Không upload runtime/model vào Git history. Trước khi phát hành public, kiểm tra quyền phân phối ảnh/model; credit không tự thay thế quyền phân phối. Nếu chưa rõ, giữ gói đầy đủ cục bộ và báo phần nào chưa thể phân phối. Không tự liên hệ tác giả hoặc upload dữ liệu ra dịch vụ khác.

Khi người dùng đã chọn phát hành gói được phép chia sẻ, đo kích thước nén, tuân thủ giới hạn từng release asset (đã khảo sát dưới 2 GiB/file; xác minh lại lúc upload), chia archive nếu cần và kèm checksum/hướng dẫn tải đủ các phần.

## Bàn giao

Trả đường dẫn Kubo.exe chạy thật trong local-package, dung lượng toàn gói, nguồn/revision, danh sách file thiếu nếu còn, kết quả PASS/FAIL/NOT TESTED và báo cáo riêng. Không kết luận hoàn tất nếu mới tạo cấu trúc mà chưa đưa dữ liệu vào hoặc nếu vẫn phụ thuộc project cha.
