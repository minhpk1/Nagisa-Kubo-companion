# Nagisa Kubo — AI Desktop Companion for Windows

A Python/PySide6 desktop application featuring an interactive character on your screen, voice conversations, context-aware facial expressions, and autonomous desktop assistant tools to find, read, and launch authorized files and applications. Speech synthesis is converted locally via RVC (Retrieval-based Voice Conversion) configured at +6 semitones pitch.

**Status:** Ready for GitHub source release and standalone distribution via GitHub Releases (v1.0.0). The repository contains clean application source code, automated test suites, and reproducible packaging tools. Full binary distributions (including character art, audio, RVC voice models, and isolated PyTorch CUDA runtimes) are hosted separately via [GitHub Releases](https://github.com/minhpk1/Nagisa-Kubo-companion/releases).

---

## Quick Start — Download Pre-built Release (GitHub Releases)

For users who want to run the application immediately without installing Python, PyTorch, or manually downloading models:

1. Go to the **[Releases](https://github.com/minhpk1/Nagisa-Kubo-companion/releases)** page of this repository.
2. Download the 3 release files into the **same folder**:
   - `Kubo-v1.0.0-windows-x64.zip.001` (1.81 GiB)
   - `Kubo-v1.0.0-windows-x64.zip.002` (1.67 GiB)
   - `extract.cmd` (one-click automated Windows merge & extraction utility)
3. Double-click `extract.cmd` to automatically merge the split binary archives and extract the complete application into `Kubo\`.
4. Run `Kubo\Kubo.exe` to launch the companion!

> For full release notes, SHA-256 checksums, and technical verification details, see [docs/RELEASE-V1.0.0.md](docs/RELEASE-V1.0.0.md).

---

## Project Structure

- `Kubo/app`: Main PySide6 UI, conversational loop, Agent tools, voice worker, and unit tests.
- `Kubo/packaging`: PyInstaller build specifications, native Win32 Job Object launcher (`KuboVoice.exe`), and reproducible packaging scripts.
- `work/rvc`: Curated RVC v2 inference modules, preserving original upstream open-source licenses.
- `docs`: Asset acquisition guides, third-party licenses, and technical verification reports.

---

## Running from Source (Development Setup)

If you wish to build or run the companion directly from source code:

1. **Python Environment**: Install Python 3.12 x64 on Windows. Create a virtual environment at `Kubo/app/.venv` and install dependencies:
   ```powershell
   python -m venv Kubo/app/.venv
   .\Kubo\app\.venv\Scripts\python.exe -m pip install -r Kubo/app/requirements.txt
   ```
2. **Inference Environment**: Prepare an isolated PyTorch CUDA environment at `work/rvc-env` with verified library versions (PyTorch 2.7.1+cu118).
3. **Required Assets**: Download the necessary character sprites, audio samples, and models according to [docs/ASSETS.md](docs/ASSETS.md):
   - Nagisa Kubo RVC v2 weights (`NagisaKubo_e300_s1500.pth`) and feature index (`added_IVF68_Flat_nprobe_1_NagisaKubo_v2.index`).
   - Feature extractor: HuBERT Base (`pytorch_model.bin`, `config.json`).
   - Pitch extractor: RMVPE (`rmvpe.pt`).
   - Binaries: `ffmpeg.exe` and `ffprobe.exe`.
4. **Launch**:
   Run `Kubo/app/Launch.cmd` or start via Python:
   ```powershell
   .\Kubo\app\.venv\Scripts\python.exe Kubo/app/app.py
   ```
5. **Configuration**:
   - Open **Settings** from the right-click menu to configure your LLM API Key (OpenAI, Gemini, or compatible endpoint). No keys are ever committed to the repository.
   - Authorize directories and applications you want the Agent to access. All tool permissions default to empty for security.

---

## Building and Verification

### Source vs. Full Runnable Package

- **Git Source Repository**: Contains clean source code, test suites, and documentation (~1.9 MiB). To keep the repository lightweight and adhere to licensing best practices, Git **does not track** multi-gigabyte AI weights, character media, or Python runtimes. Users can supply their own assets via [docs/ASSETS.md](docs/ASSETS.md).
- **Full Runnable Package (`local-package/Kubo/`)**: Standalone distribution bundle (~6.84 GiB uncompressed, 36,448 files) containing `Kubo.exe`, isolated PyTorch CUDA runtime, Nagisa Kubo RVC v2 voice model, HuBERT Base, RMVPE, FFmpeg, and assets.
  - **Launch directly**: Open `local-package\Kubo\Kubo.exe`.
  - **Independent Verification Report**: Review verified test results (**PASS / FAIL / NOT TESTED**) at [docs/LOCAL-PACKAGE-REPORT.md](docs/LOCAL-PACKAGE-REPORT.md).
  - **Dry-Run Path & Asset Validation**:
    ```powershell
    python Kubo/packaging/package_runnable.py --check-paths
    ```
  - **Reproducible Re-packaging**:
    ```powershell
    # Automatically detects source assets and cleans staging
    python Kubo/packaging/package_runnable.py --clean

    # Or specify custom dev source root and output directory
    python Kubo/packaging/package_runnable.py --dev-root "path/to/dev" --output-dir "path/to/local-package/Kubo" --clean
    ```

### Running Tests
Execute unit tests from repository root:
```powershell
.\Kubo\app\.venv\Scripts\python.exe -m unittest discover -s Kubo/app -p "test_*.py"
```

---

## Voice Attribution

The **Nagisa Kubo (JP), RVC V2, 300 epochs** voice model is credited to community creator with Discord ID **`416975678542446592`**, hosted on Hugging Face at [Kuma6/Nagisa-Kubo](https://huggingface.co/Kuma6/Nagisa-Kubo). This project integrates the pre-existing voice model and does not claim to have trained the original base model. See [CREDITS.md](CREDITS.md) for full attribution details.

---

## Licenses

- Original application source code developed by the Kubo project is licensed under the [MIT License](LICENSE).
- RVC inference code is licensed under the upstream RVC Project open-source license at `work/rvc/LICENSE` (see [docs/THIRD-PARTY.md](docs/THIRD-PARTY.md)).
- Voice model attribution and terms are documented in [CREDITS.md](CREDITS.md).
