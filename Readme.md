# ASCII Video Converter

Convert any video into high-quality ASCII art directly on your Android device using Termux. Designed for performance, simplicity, and complete offline processing.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Settings](#settings)
- [Updating](#updating)
- [Troubleshooting](#troubleshooting)
- [Output Directory](#output-directory)
- [Credits](#credits)
- [Support](#support)
- [License](#license)

---

## Features

- Convert videos into high-quality ASCII-rendered animations frame by frame.
- Multi-core rendering for faster processing.
- Adjustable **Grid Size** and **Font Size**.
- Built-in Android file picker.
- Automatic dependency installation.
- Automatic GitHub update checker.
- Rollback to previously installed releases.
- Completely offline after installation.

---

## Requirements

- Android device
- Termux (F-Droid version recommended)
- Approximately **200 MB** of free storage

---

## Installation

Clone the repository.

```bash
git clone https://github.com/best-of-binary/Ascii_generator.git
```

Copy the launcher and installer to your Termux home directory.

```bash
cp Ascii_generator/ascii Ascii_generator/setup.sh ~/
```

Make both files executable.

```bash
chmod +x ~/ascii ~/setup.sh
```

Run the installer.

```bash
bash ~/setup.sh
```

The installer automatically installs:

- Python
- OpenCV
- NumPy
- FFmpeg
- Termux:API

Existing packages are detected automatically and skipped.

---

## Usage

Launch the application.

```bash
./ascii
```

On first launch:

1. Grant storage permission.

```bash
termux-setup-storage
```

2. Install the **Termux:API** application from F-Droid.

3. Select **Select Video**.

4. Choose your input video.

5. Enter an output filename.

6. Wait for rendering and compression to finish.

Your converted video will be saved to:

```text
/storage/emulated/0/ASCII/OUTPUT/
```

---

## Settings

### Grid Size

Controls the size of each ASCII glyph.

- Smaller value = Higher detail
- Larger value = Faster rendering

### Font Size

Adjusts the size of ASCII characters within each grid cell.

### Rollback

Restore any previously installed version of the application.

---

## Updating

The application automatically checks GitHub Releases whenever it starts.

When an update is available, you'll be shown:

- Latest version
- Release notes
- **Update Now**
- **Later**

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied running `./ascii` or `./setup.sh` | `chmod +x ~/ascii ~/setup.sh` |
| File picker doesn't open | Install the **Termux:API** application from F-Droid |
| `ffmpeg` not found | Run `bash ~/setup.sh` again |
| Slow rendering | Increase **Grid Size** or convert shorter videos |

---

## Output Directory

```text
/storage/emulated/0/ASCII/OUTPUT/
```

---

## Credits

Developed by **@best_of_binary**

---

## Support

If you find this project useful and would like to support future development, consider following me on Instagram.

**Instagram:** https://www.instagram.com/best_of_binary

---

## License

This project is licensed under the hentai License.
