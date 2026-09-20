# Nagisa Kubo Desktop Companion v1.0.0 (Windows x64)

The first official release of **Nagisa Kubo Desktop Companion** for Windows 10/11 x64.

An interactive desktop AI companion featuring character animations, local RVC v2 voice conversion with +6 pitch, context-aware emotional expressions, and autonomous desktop assistant tools with granular user permission controls.

---

## 1. Download and Installation

Due to the size of the complete standalone package (including isolated Python 3.12 runtime, PyTorch CUDA 11.8, Nagisa Kubo RVC v2 model, HuBERT Base, and RMVPE) being **3.47 GiB after compression**, which exceeds GitHub Releases' 2.0 GiB per-file limit, the release bundle is split into two standard continuous binary parts.

### Release Assets

| Filename | Size | SHA-256 Checksum | Description |
| :--- | :--- | :--- | :--- |
| **`Kubo-v1.0.0-windows-x64.zip.001`** | 1,939,865,600 B (1.81 GiB) | `44d3d20cbceab99a8e87a443e51be3949b21c783a44eed4b2943d092132c43d6` | Part 1 of full runnable bundle |
| **`Kubo-v1.0.0-windows-x64.zip.002`** | 1,788,332,621 B (1.67 GiB) | `c3eaf24eb63ba6828b7546badfffb219492bbb1323ab554dd0425ef741657962` | Part 2 of full runnable bundle |
| **`extract.cmd`** | 1,715 B | `321a6039fe65ef25dd06cf22d4fc1e34226a27e740cf2ae23f5b3558c422894d` | One-click Windows merge and auto-extract utility |
| **`SHA256SUMS.txt`** | 1,348 B | — | Complete SHA-256 checksum verification list |

> **Full Merged Archive**: `Kubo-v1.0.0-windows-x64.zip` (3,728,198,221 bytes / 3.47 GiB)  
> **SHA-256 Full Archive**: `0f0da46872eb39ed27d49d58dd8619064376adaf3cf36dbacf9d17d6e1688cff`

---

### Quick Installation (Recommended)

1. Download all 3 files into the **same folder**:
   - `Kubo-v1.0.0-windows-x64.zip.001`
   - `Kubo-v1.0.0-windows-x64.zip.002`
   - `extract.cmd`
2. Double-click **`extract.cmd`**.
   - The utility will automatically binary-merge the split parts into `Kubo-v1.0.0-windows-x64.zip` using native Windows commands and extract it into a `Kubo\` folder.
   - No 7-Zip or WinRAR installation is required.
3. Open the `Kubo\` folder and double-click **`Kubo.exe`** to start the app!

---

### Manual Merge & Extraction (Advanced)

If you prefer to merge and extract using command prompt or third-party archivers:

```cmd
:: Open Command Prompt (cmd) in the folder containing downloaded files:
copy /b Kubo-v1.0.0-windows-x64.zip.001 + Kubo-v1.0.0-windows-x64.zip.002 Kubo-v1.0.0-windows-x64.zip
```

After merging, you can right-click `Kubo-v1.0.0-windows-x64.zip` and select **Extract All...** (or use 7-Zip / WinRAR / NanaZip).

---

## 2. Verified Features

- [x] **PySide6 Desktop Companion UI**: Interactive character on desktop, draggable window positioning, right-click context menu (Settings, Voice Credits, Quit).
- [x] **Context-Aware Expression Engine**: Renders character atlas and dynamic emotional sprite changes (happy, angry/pouting, neutral).
- [x] **Local RVC v2 Voice Conversion**: Pre-loaded with Nagisa Kubo 300-epoch voice model, +6 semitones pitch, HuBERT Base feature extractor, and RMVPE pitch detection.
- [x] **Safe Process Lifecycle Management (Win32 Job Object)**: `KuboVoice.exe` uses `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` to guarantee all child background Python processes terminate cleanly upon closing, preventing orphaned background tasks.
- [x] **Environment Isolation**: Bundled isolated runtime; zero interference with any existing system Python versions.
- [x] **Privacy & Security**: Zero bundled API keys, zero personal configurations. Agent file and application access permissions default to empty, giving users full control via Settings UI.

---

## 3. Unverified Aspects & Important Notes

Please note the following technical boundaries and unverified aspects before running:

1. **Physical Speaker Audio Playback**:
   - Automated testing on the development environment verified raw PCM wave data generation, correct sample duration, and non-silent amplitude (peak 29,573 - 31,879 without clipping).
   - Audio output through physical external speakers has not been live-audited in the headless build pipeline.
2. **Live Online Conversational Sessions**:
   - The release bundle includes zero API keys for security and privacy.
   - For live chat, an Internet connection and a user-provided API key (OpenAI, Gemini, or compatible endpoint) configured via the **Settings** menu are required.
3. **Clean-Room Windows Environment**:
   - The package was verified on Windows 11 x64 with a minimal isolated PATH (`C:\Windows\System32`) and user-site disabled.
   - It has not been tested on a freshly installed bare-metal Windows OS lacking Visual C++ Redistributables or graphics drivers.
4. **NVIDIA CUDA GPU Requirement**:
   - The bundled RVC engine is optimized for NVIDIA GPUs with CUDA 11.8. On machines without an NVIDIA GPU (running pure CPU or integrated graphics), voice conversion may operate noticeably slower or require CPU fallback tuning.

---

## 4. Credits & Licenses

### Nagisa Kubo Voice Model
- **Voice Pack Creator**: Original model credit belongs to Discord ID **`416975678542446592`**, originally shared in community sources.
- **Upstream Repository**: Hosted at [Kuma6/Nagisa-Kubo](https://huggingface.co/Kuma6/Nagisa-Kubo) on Hugging Face.
- **Configuration**: RVC v2, 300 epochs, pitch +6, index rate 0.75, RMS mix rate 0.25, protect rate 0.33.
- This project integrates and optimizes parameters for desktop companion usage and does not claim to have trained the original base model.

### Software Licenses
- Application source code developed by the Kubo project is licensed under the [MIT License](LICENSE).
- RVC inference components preserve the original upstream RVC Project open-source license (`work/rvc/LICENSE`).
- For complete terms and attribution, see [CREDITS.md](CREDITS.md) and [docs/THIRD-PARTY.md](docs/THIRD-PARTY.md).
