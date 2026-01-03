# Engine Folder - Compression Tools

This folder should contain the compression engine executables required for Shrinkify to function.

## 📦 Download Required Files

**Download all engine files from Google Drive:**
[**Download Engine Folder**](https://drive.google.com/REPLACE_WITH_YOUR_LINK)

After downloading, extract and place all the following `.exe` files in this `engine/` folder:

## 📋 Required Files

### 1. **cjpeg.exe** (~1 MB)
- **Purpose**: JPEG compression using MozJPEG
- **Source**: [MozJPEG by Mozilla](https://github.com/mozilla/mozjpeg)
- **Description**: Industry-leading JPEG encoder that produces smaller files with better quality

### 2. **djpeg.exe** (~533 KB)
- **Purpose**: JPEG decompression (MozJPEG)
- **Source**: [MozJPEG by Mozilla](https://github.com/mozilla/mozjpeg)
- **Description**: Decoder for JPEG files, part of MozJPEG suite

### 3. **ffmpeg.exe** (~141 MB)
- **Purpose**: Video compression and processing
- **Source**: [FFmpeg](https://ffmpeg.org/)
- **Description**: Complete, cross-platform solution for video/audio processing

### 4. **ffprobe.exe** (~141 MB)
- **Purpose**: Video file analysis and metadata extraction
- **Source**: [FFmpeg](https://ffmpeg.org/)
- **Description**: Analyzes multimedia streams and provides detailed information

### 5. **oxipng.exe** (~1.1 MB)
- **Purpose**: PNG optimization (lossless)
- **Source**: [oxipng](https://github.com/shssoichiro/oxipng)
- **Description**: Multithreaded PNG optimizer written in Rust

### 6. **pngquant.exe** (~726 KB)
- **Purpose**: PNG quantization (lossy compression)
- **Source**: [pngquant](https://pngquant.org/)
- **Description**: Reduces PNG file sizes by converting to 8-bit with alpha channel

## 📂 Expected Folder Structure

After downloading and extracting, your `engine/` folder should look like this:

```
engine/
├── README.md          (this file)
├── cjpeg.exe         (1.0 MB)
├── djpeg.exe         (533 KB)
├── ffmpeg.exe        (141 MB)
├── ffprobe.exe       (141 MB)
├── oxipng.exe        (1.1 MB)
└── pngquant.exe      (726 KB)
```

**Total size: ~285 MB**

## ⚠️ Important Notes

- **Required**: All 6 executables are required for Shrinkify to function properly
- **Windows Only**: These are Windows executables (.exe files)
- **Antivirus**: Some antivirus software may flag these as potentially unsafe. They are safe compression tools widely used in the industry
- **Do Not Rename**: Keep the original filenames as the application expects these exact names
- **Git Ignored**: These files are intentionally excluded from the git repository due to their large size

## 🔒 Security & Verification

These tools are from trusted, open-source projects:
- MozJPEG is maintained by Mozilla
- FFmpeg is the industry standard for video processing
- oxipng and pngquant are widely-used open-source tools

If you want to compile them yourself instead of using the provided binaries, visit their respective GitHub repositories.

## 🆘 Troubleshooting

### Application won't start
- **Check**: Ensure all 6 `.exe` files are present in this folder
- **Verify**: File names are exactly as listed above (case-sensitive)

### "Tool not found" errors
- **Solution**: Re-download the engine folder and ensure all files are extracted properly

### Antivirus blocking
- **Solution**: Add the `engine/` folder to your antivirus exceptions/whitelist

## 📞 Need Help?

If you encounter issues:
1. Check that all 6 files are present
2. Verify file sizes match the approximate sizes listed
3. Make sure you're using the correct engine folder for your OS
4. Open an issue on GitHub with details about your problem

---

**Note**: The engine executables are not included in the git repository to keep it lightweight. Always download them separately from the provided link.

