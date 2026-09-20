"""Prepare GitHub Release distribution archives for Nagisa Kubo v1.0.0.

Compresses local-package/Kubo into an optimized ZIP archive, measures size,
and automatically splits into <= 1.85 GiB chunks if it exceeds GitHub Release's
2.0 GiB limit. Generates one-click extract.cmd, merge.ps1, and SHA256SUMS.txt.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def log(msg: str):
    try:
        print(f"[RELEASE-PACK] {msg}", flush=True)
    except Exception:
        clean = msg.encode('ascii', 'replace').decode('ascii')
        print(f"[RELEASE-PACK] {clean}", flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while chunk := f.read(1048576):  # 1MB buffer
            h.update(chunk)
    return h.hexdigest()


def format_size(bytes_size: int) -> str:
    gib = bytes_size / (1024**3)
    mib = bytes_size / (1024**2)
    return f"{bytes_size:,} bytes ({gib:.2f} GiB / {mib:.1f} MiB)"


def make_zip_archive(src_dir: Path, zip_path: Path):
    """Create ZIP archive with ZIP64 support and progress logging."""
    log(f"Bắt đầu nén thư mục: {src_dir}")
    log(f"Tệp đích: {zip_path}")
    start = time.monotonic()
    
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    all_files = [f for f in src_dir.rglob('*') if f.is_file()]
    total_files = len(all_files)
    total_bytes = sum(f.stat().st_size for f in all_files)
    log(f"Tổng số tệp cần nén: {total_files:,} ({format_size(total_bytes)})")

    processed_bytes = 0
    last_log_time = time.monotonic()

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for idx, file_path in enumerate(all_files, 1):
            rel_path = file_path.relative_to(src_dir)
            # Store with 'Kubo/' root prefix inside zip
            archive_name = Path('Kubo') / rel_path
            zf.write(file_path, arcname=str(archive_name))
            processed_bytes += file_path.stat().st_size

            now = time.monotonic()
            if now - last_log_time >= 5.0 or idx == total_files:
                pct = (processed_bytes / total_bytes) * 100 if total_bytes else 100
                elapsed = now - start
                log(f"  Tiến độ: {pct:5.1f}% ({idx:,}/{total_files:,} tệp) - {elapsed:.1f}s")
                last_log_time = now

    duration = time.monotonic() - start
    zip_size = zip_path.stat().st_size
    log(f"Hoàn thành nén trong {duration:.1f}s.")
    log(f"Kích thước ban đầu : {format_size(total_bytes)}")
    log(f"Kích thước sau nén : {format_size(zip_size)}")
    log(f"Tỷ lệ nén          : {(zip_size / total_bytes * 100):.1f}%")
    return zip_size


def split_file(file_path: Path, chunk_size: int, output_dir: Path) -> list[Path]:
    """Split a large file into continuous .001, .002 chunks."""
    log(f"Phân chia tệp {file_path.name} thành các phần <= {format_size(chunk_size)}...")
    parts = []
    total_size = file_path.stat().st_size
    part_num = 1

    with file_path.open('rb') as src:
        while True:
            part_name = f"{file_path.name}.{part_num:03d}"
            part_path = output_dir / part_name
            written = 0
            
            with part_path.open('wb') as dst:
                while written < chunk_size:
                    to_read = min(1048576, chunk_size - written)
                    buf = src.read(to_read)
                    if not buf:
                        break
                    dst.write(buf)
                    written += len(buf)

            if written == 0:
                if part_path.exists():
                    part_path.unlink()
                break

            parts.append(part_path)
            log(f"  Tạo phần {part_num}: {part_name} ({format_size(written)})")
            part_num += 1

    return parts


def generate_helpers(output_dir: Path, archive_name: str, parts: list[Path]):
    """Generate extract.cmd and merge.ps1 for easy user extraction."""
    part_names = [p.name for p in parts]
    
    # 1. extract.cmd
    cmd_content = f"""@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ======================================================================
echo    NAGISA KUBO DESKTOP COMPANION v1.0.0 - TIEN ICH GIAI NEN TU DONG
echo ======================================================================
echo.

if not exist "{part_names[0]}" (
    echo [LOI] Khong tim thay tep phan doan: {part_names[0]}
    echo Vui long dam bao ban da tai du tat ca cac phan (.001, .002...) ve cung thu muc nay.
    echo.
    pause
    exit /b 1
)

echo [1/2] Dang gop cac phan chia nho thanh tep zip hoan chinh...
echo     Dung lenh Windows binary copy de gop...
copy /b "{archive_name}.001" + "{archive_name}.002" "{archive_name}" >nul

if errorlevel 1 (
    echo [LOI] Gop tep that bai! Vui long kiem tra dung luong o dia con trong (can khoang 4 GB).
    pause
    exit /b 1
)
echo     Gop tep hoan tat: {archive_name}

echo.
echo [2/2] Dang giai nen thu muc Kubo vao thu muc hien tai...
powershell -NoProfile -Command "Expand-Archive -Path '{archive_name}' -DestinationPath '.' -Force"

if errorlevel 1 (
    echo [CANH BAO] PowerShell Expand-Archive gap su co hoac file qua lon.
    echo Ban co the mo truc tiep tep '{archive_name}' bang Windows Explorer hoac 7-Zip de giai nen.
) else (
    echo     Giai nen thanh cong vao thu muc 'Kubo\\'!
)

echo.
echo ======================================================================
echo HOAN TAT!
echo Ban co the chay ung dung bang cach mo: Kubo\\Kubo.exe
echo ======================================================================
echo.
pause
"""
    (output_dir / "extract.cmd").write_text(cmd_content, encoding='utf-8')

    # 2. merge.ps1
    ps1_content = f"""# Script gop va xac minh checksum tu dong bang PowerShell
$ErrorActionPreference = "Stop"
$archiveName = "{archive_name}"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " NAGISA KUBO DESKTOP COMPANION v1.0.0 - POWERSHELL VERIFY & MERGE" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$parts = Get-ChildItem -Filter "$archiveName.*" | Sort-Object Name
if ($parts.Count -eq 0) {{
    Write-Error "Khong tim thay cac tep phan doan $archiveName.001, $archiveName.002..."
}}

Write-Host "Tim thay $($parts.Count) phan phan doan:" -ForegroundColor Green
foreach ($p in $parts) {{
    Write-Host "  - $($p.Name) ($([math]::Round($p.Length / 1GB, 2)) GB)"
}}

Write-Host "`nDang gop thanh $archiveName..." -ForegroundColor Yellow
$outStream = [System.IO.File]::Create((Join-Path $PSScriptRoot $archiveName))
try {{
    foreach ($p in $parts) {{
        Write-Host "  Dang doc $($p.Name)..."
        $inStream = [System.IO.File]::OpenRead($p.FullName)
        try {{
            $inStream.CopyTo($outStream)
        }} finally {{
            $inStream.Close()
        }}
    }}
}} finally {{
    $outStream.Close()
}}

Write-Host "Gop hoan tat. Dang tinh ma bam SHA-256 cua tep gop..." -ForegroundColor Yellow
$hash = (Get-FileHash -Path (Join-Path $PSScriptRoot $archiveName) -Algorithm SHA256).Hash
Write-Host "SHA-256: $hash" -ForegroundColor Green

Write-Host "`nBan co the chay extract.cmd hoac giai nen $archiveName vao thu muc mong muon." -ForegroundColor Cyan
"""
    (output_dir / "merge.ps1").write_text(ps1_content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Chuẩn bị gói phân phối GitHub Releases cho Kubo v1.0.0")
    parser.add_argument("--src-dir", type=str, default=None, help="Thư mục local-package/Kubo nguồn")
    parser.add_argument("--output-dir", type=str, default=None, help="Thư mục xuất dist-release/v1.0.0")
    parser.add_argument("--split-size-mb", type=int, default=1850, help="Ngưỡng chia nhỏ file (MB), mặc định 1850 MB (~1.81 GiB)")
    parser.add_argument("--skip-zip", action="store_true", help="Bỏ qua bước nén nếu file zip đã tồn tại")
    args = parser.parse_args()

    file_path = Path(__file__).resolve()
    base_dir = file_path.parents[2]

    if base_dir.name == 'Kubo-github':
        repo_root = base_dir
    elif (base_dir / 'Kubo-github').is_dir():
        repo_root = base_dir / 'Kubo-github'
    else:
        repo_root = base_dir

    # Detect src_dir (local-package/Kubo)
    if args.src_dir:
        src_dir = Path(args.src_dir).resolve()
    elif (repo_root / 'local-package' / 'Kubo').is_dir():
        src_dir = repo_root / 'local-package' / 'Kubo'
    elif (base_dir / 'local-package' / 'Kubo').is_dir():
        src_dir = base_dir / 'local-package' / 'Kubo'
    else:
        src_dir = repo_root / 'local-package' / 'Kubo'

    # Detect output_dir (dist-release/v1.0.0)
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        output_dir = repo_root / 'dist-release' / 'v1.0.0'
    output_dir.mkdir(parents=True, exist_ok=True)

    archive_name = "Kubo-v1.0.0-windows-x64.zip"
    zip_path = output_dir / archive_name
    split_bytes = args.split_size_mb * 1024 * 1024

    log("=" * 70)
    log("CHUẨN BỊ BẢN PHÂN PHỐI GITHUB RELEASES - NAGISA KUBO v1.0.0")
    log("=" * 70)
    log(f"Thư mục nguồn  : {src_dir}")
    log(f"Thư mục phát hành: {output_dir}")
    log(f"Tên tệp lưu trữ: {archive_name}")
    log(f"Ngưỡng chia file: {format_size(split_bytes)}")
    log("=" * 70)

    if not (src_dir / 'Kubo.exe').is_file():
        log(f"LỖI: Không tìm thấy Kubo.exe trong {src_dir}.")
        sys.exit(1)

    # 1. Zip compression
    if args.skip_zip and zip_path.is_file():
        log(f"Bỏ qua bước nén; sử dụng file zip hiện có: {zip_path} ({format_size(zip_path.stat().st_size)})")
        zip_size = zip_path.stat().st_size
    else:
        zip_size = make_zip_archive(src_dir, zip_path)

    # 2. Check if splitting is needed (GitHub limit: 2 GiB = 2,147,483,648 bytes)
    parts = []
    github_limit = 2 * (1024**3)
    if zip_size > split_bytes or zip_size > github_limit:
        log(f"Dung lượng tệp ({format_size(zip_size)}) vượt ngưỡng {format_size(split_bytes)}.")
        log("Tiến hành phân đoạn tệp thành các phần nhỏ hơn 2 GiB cho GitHub Releases...")
        parts = split_file(zip_path, split_bytes, output_dir)
        generate_helpers(output_dir, archive_name, parts)
    else:
        log(f"Dung lượng tệp ({format_size(zip_size)}) nằm trong giới hạn 2 GiB; không cần chia nhỏ.")

    # 3. Calculate SHA-256 for all release assets
    log("Tính toán bảng mã băm SHA-256...")
    checksum_lines = []
    checksum_dict = {}

    # Hash the parts or the whole zip
    if parts:
        for p in parts:
            h = sha256_file(p)
            checksum_lines.append(f"{h}  {p.name}  ({format_size(p.stat().st_size)})")
            checksum_dict[p.name] = {"sha256": h, "size": p.stat().st_size}

    h_full = sha256_file(zip_path)
    checksum_lines.append(f"{h_full}  {zip_path.name}  ({format_size(zip_size)}) [FULL MERGED ARCHIVE]")
    checksum_dict[zip_path.name] = {"sha256": h_full, "size": zip_size}

    # Hash internal core components
    core_files = [
        src_dir / 'Kubo.exe',
        src_dir / 'voice-engine' / 'KuboVoice.exe',
        src_dir / 'data' / 'models' / 'NagisaKubo_e300_s1500.pth',
        src_dir / 'data' / 'models' / 'added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index',
        src_dir / 'data' / 'models' / 'rmvpe.pt',
        src_dir / 'data' / 'models' / 'hubert_base' / 'pytorch_model.bin',
    ]
    for cf in core_files:
        if cf.is_file():
            rel = cf.relative_to(src_dir)
            h = sha256_file(cf)
            checksum_lines.append(f"{h}  [INNER] {rel}  ({format_size(cf.stat().st_size)})")

    sha_file = output_dir / "SHA256SUMS.txt"
    sha_file.write_text("\n".join(checksum_lines) + "\n", encoding='utf-8')
    log(f"Đã tạo {sha_file.name}.")

    log("=" * 70)
    log("TỔNG KẾT TỆP PHÁT HÀNH TRONG dist-release/v1.0.0/:")
    for f in output_dir.glob('*'):
        if f.is_file():
            log(f"  - {f.name:40s} : {format_size(f.stat().st_size)}")
    log("=" * 70)


if __name__ == '__main__':
    main()
