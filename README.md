# Shrinkify 🔥

A powerful, user-friendly image and video compression tool with a beautiful dark mode interface. Compress your media files without compromising quality using industry-standard compression engines.

## ✨ Features

- **Multi-format Support**: Compress JPEG, PNG, WebP, GIF, and video files
- **Batch Processing**: Compress multiple files or entire folders at once
- **Video Compression**: Advanced video compression with H.264/H.265 codecs
- **Dark/Light Mode**: Beautiful, modern UI with theme switching
- **Real-time Progress**: Live terminal output and progress tracking
- **Quality Control**: Customizable quality settings for each format
- **Smart Optimization**: Uses best-in-class compression tools:
  - **MozJPEG** for JPEG compression
  - **pngquant** & **oxipng** for PNG optimization
  - **FFmpeg** for video compression

## 📋 Prerequisites

- Python 3.8 or higher
- Windows OS (currently)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mahostar/Shrinkify.git
cd Shrinkify
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
```

**Activate the virtual environment:**

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
.\venv\Scripts\activate.bat
```

> **Note:** If you get an execution policy error in PowerShell, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download Compression Engines

**The most important step!** Download the compression engine tools from this Google Drive link:

**📦 [Download Engine Folder]([https://drive.google.com/REPLACE_WITH_YOUR_LINK](https://drive.google.com/drive/folders/1a1G6QkbK8qCHQApnTfNoDyr6z62UrHGJ?usp=sharing))**

After downloading:
1. Extract the contents
2. Place all `.exe` files in the `engine/` folder in your project directory

The `engine/` folder should contain these files:
```
engine/
├── cjpeg.exe      (MozJPEG - JPEG compression)
├── djpeg.exe      (MozJPEG - JPEG decompression)
├── ffmpeg.exe     (Video compression)
├── ffprobe.exe    (Video analysis)
├── oxipng.exe     (PNG optimization)
└── pngquant.exe   (PNG quantization)
```

**File Sizes Reference:**
- `cjpeg.exe` - ~1 MB
- `djpeg.exe` - ~533 KB
- `ffmpeg.exe` - ~141 MB
- `ffprobe.exe` - ~141 MB
- `oxipng.exe` - ~1.1 MB
- `pngquant.exe` - ~726 KB

### 5. Run the Application

```bash
python Production-Ready-ts-darkMode.py
```

## 🎯 Usage

### Single File Compression
1. Click "Select File"
2. Choose your image or video
3. Adjust quality settings if needed
4. Click "Compress"

### Batch Compression
1. Click "Batch Compress Folder"
2. Select a folder containing images
3. Set output folder
4. Adjust settings and compress

### Video Compression
1. Click "Compress Video File"
2. Select your video file
3. Choose codec (H.264 or H.265)
4. Set CRF value (lower = better quality, larger file)
5. Compress

## ⚙️ Configuration

Settings are automatically saved in `optimizer_config.json`. You can customize:

- JPEG quality (0-100)
- PNG colors (2-256)
- WebP quality (0-100)
- Video codec preferences
- Theme preference (dark/light)

## 🛠️ Building from Source

### Create Executable

```bash
pyinstaller Shrinkify.spec
```

The executable will be created in the `dist/Shrinkify/` folder.

### Create Installer (Requires Inno Setup)

```powershell
.\compile_installer.ps1
```

## 📁 Project Structure

```
Shrinkify/
├── Production-Ready-ts-darkMode.py  # Main application
├── requirements.txt                  # Python dependencies
├── optimizer_config.json            # User settings
├── Shrinkify.spec                   # PyInstaller spec file
├── logo.ico                         # Application icon
├── engine/                          # Compression tools (download separately)
│   ├── cjpeg.exe
│   ├── djpeg.exe
│   ├── ffmpeg.exe
│   ├── ffprobe.exe
│   ├── oxipng.exe
│   └── pngquant.exe
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is provided as-is for educational and personal use.

## 🙏 Credits

This project uses the following excellent tools:
- [MozJPEG](https://github.com/mozilla/mozjpeg) - Superior JPEG compression
- [pngquant](https://pngquant.org/) - PNG quantization
- [oxipng](https://github.com/shssoichiro/oxipng) - PNG optimization
- [FFmpeg](https://ffmpeg.org/) - Video processing
- [Pillow](https://python-pillow.org/) - Python imaging library

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

Made with ❤️ by mahostar

