import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
from pathlib import Path
import subprocess
import shutil
import threading
from queue import Queue
import json
import time
import math
import ctypes
from ctypes import wintypes

# --- Constants & Themes ---
CONFIG_FILE = "optimizer_config.json"

LIGHT_THEME = {
    "bg": "#f4f5f7",
    "panel_bg": "#ffffff",
    "header_bg": "#f8f9fa",
    "fg": "#2c3e50",
    "fg_secondary": "#6c757d",
    "accent": "#007bff",
    "btn_bg": "#007bff",
    "btn_fg": "#ffffff",
    "btn_batch": "#28a745",
    "btn_video": "#6f42c1",
    "entry_bg": "#f8f9fa",
    "border": "#dee2e6",
    "terminal_bg": "#1e1e1e",
    "terminal_fg": "#00FF00"
}

DARK_THEME = {
    "bg": "#121212",
    "panel_bg": "#1e1e1e",
    "header_bg": "#252525",
    "fg": "#ffffff",
    "fg_secondary": "#b0b0b0",
    "accent": "#bb86fc",
    "btn_bg": "#bb86fc",
    "btn_fg": "#000000",
    "btn_batch": "#03dac6",
    "btn_video": "#bb86fc",
    "entry_bg": "#2d2d2d",
    "border": "#444444",
    "terminal_bg": "#000000",
    "terminal_fg": "#00FF00"
}

class EnterpriseMediaOptimizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Shrinkify")
        self.root.geometry("1280x900")
        
        # --- Theme State ---
        self.config = self.load_config()
        self.is_dark_mode = self.config.get("dark_mode", False)
        self.theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        
        self.root.configure(bg=self.theme["bg"])

        # --- Styles ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.update_styles()

        # --- Variables: Image ---
        self.single_image_path = tk.StringVar()
        self.single_output_folder = tk.StringVar()
        self.single_quality = tk.IntVar(value=85)

        self.batch_input_folder = tk.StringVar()
        self.batch_output_folder = tk.StringVar()
        self.batch_quality = tk.IntVar(value=85)
        self.copy_videos_in_image_batch = tk.BooleanVar(value=True)
        self.image_compression_mode = tk.StringVar(value="auto")

        self.original_size = tk.StringVar(value="N/A")
        self.compressed_size = tk.StringVar(value="N/A")
        self.compression_details = tk.StringVar(value="Ready for processing...")

        # --- Variables: Video ---
        self.video_input_folder = tk.StringVar()
        self.video_output_folder = tk.StringVar()
        self.video_compression_mode = tk.StringVar(value="auto")
        self.skip_small_videos = tk.BooleanVar(value=True)
        self.use_hardware_accel = tk.BooleanVar(value=True)
        self.convert_ts_to_mp4 = tk.BooleanVar(value=False)
        self.unify_extension = tk.BooleanVar(value=False)
        self.target_extension = tk.StringVar(value=".mp4")

        # --- System State ---
        self.is_processing = False
        self.compression_queue = Queue()

        # Engine Configuration (PyInstaller compatible)
        if getattr(sys, 'frozen', False):
            # If running as EXE, look next to the EXE
            base_path = Path(sys.executable).parent
        else:
            # If running as script, look next to the script
            base_path = Path(__file__).parent
            
        self.engine_dir = base_path / "engine"
        self.has_ffmpeg = self.check_tool_availability('ffmpeg.exe')
        self.has_ffprobe = self.check_tool_availability('ffprobe.exe')
        self.has_mozjpeg = self.check_tool_availability('cjpeg.exe')
        self.has_oxipng = self.check_tool_availability('oxipng.exe')
        self.has_pngquant = self.check_tool_availability('pngquant.exe')

        # --- Hardware Acceleration Detection ---
        self.hw_accel_type = self.detect_hardware_acceleration()

        # --- UI Setup ---
        self.setup_ui()
        
        # Apply dark title bar if in dark mode on startup
        if self.is_dark_mode:
            self.root.after(100, lambda: self.set_native_dark_mode(True))

    # =========================================================================
    # CONFIG & THEME UTILITIES
    # =========================================================================

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"dark_mode": False}

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"dark_mode": self.is_dark_mode}, f)
        except:
            pass

    def update_styles(self):
        """Update ttk styles for the current theme."""
        bg = self.theme["bg"]
        fg = self.theme["fg"]
        accent = self.theme["accent"]
        panel_bg = self.theme["panel_bg"]

        self.style.configure("TProgressbar", thickness=20, background=accent, troughcolor=self.theme["entry_bg"])
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", background=self.theme["btn_bg"], foreground=self.theme["btn_fg"])
        self.style.configure("Horizontal.TSeparator", background=self.theme["border"])

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        self.save_config()
        self.update_styles()
        self.apply_theme()
        
        # Update toggle button text and color
        theme_text = "🌙 Dark Mode" if not self.is_dark_mode else "☀️ Light Mode"
        self.theme_btn.config(text=theme_text, bg=self.theme["accent"], fg="white" if not self.is_dark_mode else "black")

    def set_native_dark_mode(self, dark_mode=True):
        """Enable native Immersive Dark Mode for the Windows title bar."""
        if os.name != 'nt':
            return
            
        try:
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 11+) or 19 (older Windows 10)
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            
            # Need window handle (HWND)
            self.root.update()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            
            # If GetParent returns 0, try GetAncestor or use winfo_id directly
            if not hwnd:
                hwnd = self.root.winfo_id()
                
            value = ctypes.c_int(1 if dark_mode else 0)
            
            # Try attribute 20 (Windows 11)
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 
                ctypes.byref(value), ctypes.sizeof(value)
            )
            
            # Fallback for older Win10 builds (attribute 19)
            if res != 0:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 19, ctypes.byref(value), ctypes.sizeof(value)
                )
        except Exception as e:
            print(f"Failed to set title bar theme: {e}")

    def apply_theme(self):
        """Recursively update all widgets in the application."""
        self.root.configure(bg=self.theme["bg"])
        self.set_native_dark_mode(self.is_dark_mode)
        self._apply_theme_recursive(self.root)

    def _apply_theme_recursive(self, parent):
        for widget in parent.winfo_children():
            w_type = widget.winfo_class()
            
            try:
                if w_type == 'Frame':
                    # Special check for panels vs background frames
                    if hasattr(widget, 'is_panel') and widget.is_panel:
                        widget.configure(bg=self.theme["panel_bg"], highlightthickness=0)
                    elif hasattr(widget, 'is_header') and widget.is_header:
                        widget.configure(bg=self.theme["header_bg"], highlightthickness=0)
                    else:
                        widget.configure(bg=self.theme["panel_bg"], highlightthickness=0)
                
                elif w_type == 'Label':
                    if hasattr(widget, 'is_header') and widget.is_header:
                        widget.configure(bg=self.theme["header_bg"], fg=self.theme["fg"])
                    elif hasattr(widget, 'is_stats') and widget.is_stats:
                        widget.configure(bg=self.theme["panel_bg"])
                    else:
                        current_fg = widget.cget('fg')
                        # Preserve special colors like red/green for stats
                        if current_fg in ['#dc3545', '#28a745']:
                            widget.configure(bg=self.theme["panel_bg"])
                        else:
                            widget.configure(bg=self.theme["panel_bg"], fg=self.theme["fg"])
                
                elif w_type == 'Button':
                    if hasattr(widget, 'btn_type'):
                        if widget.btn_type == 'batch':
                            widget.configure(bg=self.theme["btn_batch"], fg="black" if self.is_dark_mode else "white", 
                                           activebackground=self.theme["btn_batch"])
                        elif widget.btn_type == 'video':
                            widget.configure(bg=self.theme["btn_video"], fg="black" if self.is_dark_mode else "white",
                                           activebackground=self.theme["btn_video"])
                        elif widget.btn_type == 'primary':
                            widget.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
                                           activebackground=self.theme["btn_bg"])
                    else:
                        widget.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
                                       activebackground=self.theme["btn_bg"])
                
                elif w_type == 'Entry':
                    widget.configure(bg=self.theme["entry_bg"], fg=self.theme["fg"], 
                                     insertbackground=self.theme["fg"], 
                                     disabledbackground=self.theme["entry_bg"],
                                     disabledforeground=self.theme["fg_secondary"],
                                     relief=tk.FLAT)
                
                elif w_type == 'Text':
                    if hasattr(widget, 'is_terminal') and widget.is_terminal:
                        widget.configure(bg=self.theme["terminal_bg"], fg=self.theme["terminal_fg"])
                    else:
                        widget.configure(bg=self.theme["entry_bg"], fg=self.theme["fg"])
                
                elif w_type == 'Scale':
                    widget.configure(bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                                     troughcolor=self.theme["accent"], 
                                     activebackground=self.theme["accent"],
                                     highlightthickness=0)
                
                elif w_type == 'Checkbutton':
                    widget.configure(bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                                     activebackground=self.theme["panel_bg"], 
                                     activeforeground=self.theme["fg"],
                                     selectcolor=self.theme["panel_bg"],
                                     highlightthickness=0,
                                     relief=tk.FLAT)
                
                elif w_type == 'Radiobutton':
                    widget.configure(bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                                     activebackground=self.theme["panel_bg"], 
                                     activeforeground=self.theme["fg"],
                                     selectcolor=self.theme["panel_bg"],
                                     highlightthickness=0,
                                     relief=tk.FLAT)
                
                elif w_type == 'Labelframe':
                    widget.configure(bg=self.theme["panel_bg"], fg=self.theme["fg"])
                
            except Exception as e:
                pass 

            self._apply_theme_recursive(widget)


    # =========================================================================
    # CORE UTILITIES
    # =========================================================================

    def check_tool_availability(self, tool_name):
        """Check if an external compression tool is available in the local engine folder."""
        tool_path = self.engine_dir / tool_name
        return tool_path.exists()

    def detect_hardware_acceleration(self):
        """Detect available hardware acceleration (NVENC, QSV, AMF)."""
        if not self.has_ffmpeg:
            return None
        try:
            ffmpeg_path = str(self.engine_dir / 'ffmpeg.exe')
            result = subprocess.run([ffmpeg_path, '-hide_banner', '-encoders'],
                                    capture_output=True, text=True, encoding='utf-8', timeout=5)
            output = result.stdout
            if 'h264_nvenc' in output: return 'nvenc'
            elif 'h264_qsv' in output: return 'qsv'
            elif 'h264_amf' in output: return 'amf'
        except:
            pass
        return None

    def format_bytes(self, size):
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0: return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    def log_to_video_terminal(self, message):
        """Thread-safe logging to the video terminal."""
        self.root.after(0, lambda: self.video_stats_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.video_stats_text.see(tk.END))
        print(message)

    def log_to_image_terminal(self, message):
        """Thread-safe logging to the image terminal."""
        self.root.after(0, lambda: self.image_stats_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.image_stats_text.see(tk.END))
        print(message)

    def analyze_image(self, image_path):
        """Analyze image to determine optimal compression strategy."""
        try:
            img = Image.open(image_path)
            file_size = os.path.getsize(image_path)
            width, height = img.size
            mode = img.mode
            format_type = img.format or Path(image_path).suffix.lower().replace('.', '').upper()
            
            # Calculate image complexity (simple heuristic based on file size vs dimensions)
            pixels = width * height
            bytes_per_pixel = file_size / pixels if pixels > 0 else 0
            
            # Higher bytes per pixel = more complex/detailed image
            if bytes_per_pixel > 3:
                complexity = "high"
            elif bytes_per_pixel > 1:
                complexity = "medium"
            else:
                complexity = "low"
            
            return {
                'width': width,
                'height': height,
                'pixels': pixels,
                'mode': mode,
                'format': format_type,
                'file_size': file_size,
                'bytes_per_pixel': bytes_per_pixel,
                'complexity': complexity
            }
        except Exception as e:
            return None

    def get_profile_settings(self, mode, complexity="medium"):
        """Get compression settings based on profile and image complexity."""
        # Profile definitions: (target_reduction%, quality_floor, quality_ceiling)
        profiles = {
            'fast': {'reduction': 0.25, 'floor': 75, 'ceiling': 90},
            'balanced': {'reduction': 0.40, 'floor': 65, 'ceiling': 85},
            'quality': {'reduction': 0.25, 'floor': 80, 'ceiling': 95},
            'maximum': {'reduction': 0.60, 'floor': 45, 'ceiling': 75},
            'auto': {'reduction': 0.35, 'floor': 60, 'ceiling': 90}  # Will be adjusted
        }
        
        settings = profiles.get(mode, profiles['balanced'])
        
        # For AUTO mode, adjust based on complexity
        if mode == 'auto':
            if complexity == 'high':
                settings = {'reduction': 0.30, 'floor': 70, 'ceiling': 92}
            elif complexity == 'low':
                settings = {'reduction': 0.50, 'floor': 55, 'ceiling': 85}
        
        return settings

    def find_optimal_quality(self, image_path, output_path, target_size, min_quality, max_quality, ext):
        """Binary search to find optimal quality that achieves target size."""
        import tempfile
        
        best_quality = max_quality
        best_size = float('inf')
        
        low, high = min_quality, max_quality
        iterations = 0
        max_iterations = 8  # Limit iterations for speed
        
        while low <= high and iterations < max_iterations:
            mid = (low + high) // 2
            iterations += 1
            
            # Create temp file to test compression
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                img = Image.open(image_path)
                if ext in ['.jpg', '.jpeg']:
                    img = img.convert('RGB')
                    img.save(tmp_path, format='JPEG', quality=mid, optimize=True, progressive=True)
                elif ext == '.png':
                    img.save(tmp_path, format='PNG', optimize=True, compress_level=9)
                    # PNG quality is controlled differently
                    os.remove(tmp_path)
                    return max_quality  # For PNG, just use max quality
                elif ext == '.webp':
                    img.save(tmp_path, format='WEBP', quality=mid, method=6)
                else:
                    img.save(tmp_path, quality=mid)
                
                current_size = os.path.getsize(tmp_path)
                
                if current_size <= target_size:
                    # We achieved target, but can we do better quality?
                    if mid > best_quality or current_size < best_size:
                        best_quality = mid
                        best_size = current_size
                    low = mid + 1  # Try higher quality
                else:
                    high = mid - 1  # Need more compression
                
                os.remove(tmp_path)
            except Exception as e:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                break
        
        return best_quality

    def compress_image_intelligent(self, input_path, output_path, mode):
        """Intelligently compress an image based on its characteristics."""
        try:
            # Analyze the image
            metadata = self.analyze_image(input_path)
            if not metadata:
                return None, "Analysis failed"
            
            original_size = metadata['file_size']
            ext = Path(input_path).suffix.lower()
            
            # Get profile settings
            settings = self.get_profile_settings(mode, metadata['complexity'])
            target_reduction = settings['reduction']
            quality_floor = settings['floor']
            quality_ceiling = settings['ceiling']
            
            target_size = int(original_size * (1 - target_reduction))
            
            self.log_to_image_terminal(f"[SCAN] {metadata['width']}x{metadata['height']} | {metadata['complexity'].upper()} complexity")
            self.log_to_image_terminal(f"[SIZE] Original: {self.format_bytes(original_size)}")
            self.log_to_image_terminal(f"[TARGET] Aiming for {self.format_bytes(target_size)} ({int(target_reduction*100)}% reduction)")
            
            # Find optimal quality
            optimal_quality = self.find_optimal_quality(
                input_path, output_path, target_size, 
                quality_floor, quality_ceiling, ext
            )
            
            self.log_to_image_terminal(f"[DECISION] Using Quality: {optimal_quality}")
            
            # Apply compression with optimal quality
            method = "PIL"
            success = False
            
            if ext in ['.jpg', '.jpeg']:
                if self.has_mozjpeg and self.compress_jpeg_mozjpeg(input_path, output_path, optimal_quality):
                    method = "MozJPEG"
                    success = True
                else:
                    img = Image.open(input_path)
                    self.compress_image_pil(img, output_path, ext, optimal_quality)
                    success = True
            
            elif ext == '.png':
                # For PNG, try pngquant first for lossy, then oxipng for lossless
                if mode in ['maximum', 'balanced'] and self.has_pngquant:
                    if self.compress_png_pngquant(input_path, output_path, optimal_quality):
                        method = "PNGQuant"
                        success = True
                
                if not success and self.has_oxipng:
                    if self.compress_png_oxipng(input_path, output_path):
                        method = "OxiPNG"
                        success = True
                
                if not success:
                    img = Image.open(input_path)
                    self.compress_image_pil(img, output_path, ext, optimal_quality)
                    success = True
            
            elif ext == '.webp':
                img = Image.open(input_path)
                img.save(output_path, format='WEBP', quality=optimal_quality, method=6, optimize=True)
                method = "WebP"
                success = True
            
            else:
                img = Image.open(input_path)
                self.compress_image_pil(img, output_path, ext, optimal_quality)
                success = True
            
            if success and os.path.exists(output_path):
                new_size = os.path.getsize(output_path)
                
                # Check if we actually saved space
                if new_size >= original_size:
                    # Just copy original if compression didn't help
                    shutil.copy2(input_path, output_path)
                    new_size = original_size
                    self.log_to_image_terminal(f"[WARN] No savings. Keeping original.")
                    return original_size, new_size, "Copy", optimal_quality, 0
                
                saved = original_size - new_size
                reduction = (saved / original_size) * 100
                
                return original_size, new_size, method, optimal_quality, reduction
            
            return None, "Compression failed"
            
        except Exception as e:
            self.log_to_image_terminal(f"[ERR] {str(e)}")
            return None, str(e)


    def compress_single_image(self):
        if self.is_processing: return
        if not self.single_image_path.get() or not self.single_output_folder.get():
            messagebox.showerror("Error", "Select image and output folder.")
            return

        self.is_processing = True
        self.single_compress_btn.config(state='disabled', text="Processing...")
        self.compression_details.set("Optimizing...")
        threading.Thread(target=self._compress_single_worker, daemon=True).start()

    def _compress_single_worker(self):
        try:
            src = self.single_image_path.get()
            orig_size = os.path.getsize(src)
            self.root.after(0, self.original_size.set, self.format_bytes(orig_size))

            fname = Path(src).stem
            ext = Path(src).suffix.lower()
            dest = os.path.join(self.single_output_folder.get(), f"{fname}{ext}")

            method = "PIL"
            
            if ext in ['.jpg', '.jpeg']:
                if self.has_mozjpeg and self.compress_jpeg_mozjpeg(src, dest, self.single_quality.get()):
                    method = "MozJPEG"
                else:
                    img = Image.open(src)
                    dest = self.compress_image_pil(img, dest, ext, self.single_quality.get())
            
            elif ext == '.png':
                success = False
                if self.has_pngquant and self.single_quality.get() < 95:
                    if self.compress_png_pngquant(src, dest, self.single_quality.get()):
                        method = "PNGQuant"
                        success = True
                
                if not success and self.has_oxipng:
                    if self.compress_png_oxipng(src, dest):
                        method = "OxiPNG"
                        success = True
                
                if not success:
                    img = Image.open(src)
                    dest = self.compress_image_pil(img, dest, ext, self.single_quality.get())
            else:
                img = Image.open(src)
                dest = self.compress_image_pil(img, dest, ext, self.single_quality.get())

            new_size = os.path.getsize(dest)
            self.root.after(0, self.compressed_size.set, self.format_bytes(new_size))

            saved = orig_size - new_size
            percent = (saved / orig_size) * 100

            details = f"Method: {method} | Quality: {self.single_quality.get()}% | Saved: {self.format_bytes(saved)} ({percent:.2f}%)"
            self.root.after(0, self.compression_details.set, details)
            self.root.after(0, messagebox.showinfo, "Success", "Image optimized successfully.")

        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", str(e))
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.single_compress_btn.config(state='normal', text="Compress Single Image"))

    def compress_batch(self):
        if self.is_processing: return
        if not self.batch_input_folder.get() or not self.batch_output_folder.get():
            messagebox.showerror("Error", "Select image and output folder.")
            return
        
        if self.batch_input_folder.get() == self.batch_output_folder.get():
            messagebox.showerror("Error", "Input and Output folders must be different.")
            return

        self.is_processing = True
        self.batch_compress_btn.config(state='disabled', text="Processing...")
        self.image_stats_text.delete(1.0, tk.END)
        
        mode = self.image_compression_mode.get()
        self.log_to_image_terminal("[INIT] Starting Image Optimization Engine...")
        self.log_to_image_terminal(f"[PATH] Input: {self.batch_input_folder.get()}")
        self.log_to_image_terminal(f"[PATH] Output: {self.batch_output_folder.get()}")
        self.log_to_image_terminal(f"[MODE] Profile: {mode.upper()}")
        self.log_to_image_terminal("-" * 60)
        
        threading.Thread(target=self._compress_batch_worker, daemon=True).start()

    def _compress_batch_worker(self):
        try:
            img_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}
            vid_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ts'}
            
            in_dir = Path(self.batch_input_folder.get())
            out_dir = Path(self.batch_output_folder.get())
            out_dir.mkdir(parents=True, exist_ok=True)

            all_files = [f for f in in_dir.iterdir() if f.is_file()]
            image_files = [f for f in all_files if f.suffix.lower() in img_exts]
            video_files = [f for f in all_files if f.suffix.lower() in vid_exts]

            if not image_files and not video_files:
                self.root.after(0, messagebox.showwarning, "Warning", "No supported files found.")
                return

            # --- Handle Video Copying ---
            videos_copied = 0
            if self.copy_videos_in_image_batch.get() and video_files:
                video_dest_folder = out_dir / "your_videos"
                video_dest_folder.mkdir(exist_ok=True)
                self.log_to_image_terminal(f"\n[VIDEO] Found {len(video_files)} videos. Moving to 'your_videos'...")
                
                for v_file in video_files:
                    try:
                        shutil.copy2(v_file, video_dest_folder / v_file.name)
                        videos_copied += 1
                    except Exception as e:
                        self.log_to_image_terminal(f"[ERR] Failed to copy {v_file.name}: {e}")
                
                self.log_to_image_terminal(f"[DONE] Moved {videos_copied} videos.")

            # --- Handle Image Compression ---
            total_files = len(image_files)
            self.root.after(0, lambda: self.progress.configure(maximum=total_files, value=0))
            self.log_to_image_terminal(f"\n[SCAN] Found {total_files} images to optimize.")
            self.log_to_image_terminal("-" * 60)

            total_orig = 0
            total_new = 0
            stats = {}
            mode = self.image_compression_mode.get()
            start_time = time.time()
            
            compressed = 0
            failed = 0

            for idx, f in enumerate(image_files):
                self.root.after(0, self.progress_label.config, {'text': f"Processing: {f.name}"})
                self.log_to_image_terminal(f"\n[IMAGE] Processing [{idx + 1}/{total_files}]: {f.name}")
                
                try:
                    dest = out_dir / f.name
                    
                    # Use intelligent compression
                    result = self.compress_image_intelligent(str(f), str(dest), mode)
                    
                    if result and len(result) == 5:
                        orig_size, new_size, method, quality, reduction = result
                        total_orig += orig_size
                        total_new += new_size
                        stats[method] = stats.get(method, 0) + 1
                        compressed += 1
                        
                        self.log_to_image_terminal(f"[DONE] {self.format_bytes(orig_size)} -> {self.format_bytes(new_size)} (Saved {reduction:.1f}%)")
                        self.log_to_image_terminal(f"[ENGINE] {method} @ Quality {quality}")
                    else:
                        # Fallback: just copy
                        shutil.copy2(f, dest)
                        size = os.path.getsize(f)
                        total_orig += size
                        total_new += size
                        failed += 1
                        self.log_to_image_terminal(f"[WARN] Could not compress. Copied original.")
                        
                except Exception as e:
                    self.log_to_image_terminal(f"[ERR] {str(e)}")
                    failed += 1
                    
                self.root.after(0, lambda v=idx+1: self.progress.configure(value=v))

            # Final Summary
            duration = time.time() - start_time
            saved = total_orig - total_new
            percent = (saved / total_orig) * 100 if total_orig > 0 else 0
            
            self.log_to_image_terminal("\n" + "=" * 60)
            self.log_to_image_terminal("[COMPLETE] Image Optimization Finished!")
            self.log_to_image_terminal(f"[TIME] Total Duration: {duration:.1f}s")
            self.log_to_image_terminal(f"[STAT] Images Processed: {compressed} | Failed: {failed}")
            if videos_copied > 0:
                self.log_to_image_terminal(f"[STAT] Videos Moved: {videos_copied}")
            self.log_to_image_terminal(f"[SIZE] {self.format_bytes(total_orig)} -> {self.format_bytes(total_new)}")
            self.log_to_image_terminal(f"[SAVED] {self.format_bytes(saved)} ({percent:.1f}% reduction)")
            
            methods_str = ", ".join([f"{k}: {v}" for k,v in stats.items()])
            self.log_to_image_terminal(f"[ENGINES] {methods_str}")
            self.log_to_image_terminal("=" * 60)

            self.root.after(0, self.progress_label.config, {'text': "Optimization Complete!"})
            
            # Show summary messagebox
            summary = f"Optimization Complete!\n\n"
            summary += f"Images: {compressed} processed, {failed} failed\n"
            if videos_copied > 0:
                summary += f"Videos: {videos_copied} moved\n"
            summary += f"\nTotal Saved: {self.format_bytes(saved)} ({percent:.1f}%)\n"
            summary += f"Time: {duration:.1f} seconds"
            
            self.root.after(0, messagebox.showinfo, "Success", summary)

        except Exception as e:
            self.log_to_image_terminal(f"[FATAL] {str(e)}")
            self.root.after(0, messagebox.showerror, "Error", str(e))
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.batch_compress_btn.config(state='normal', text="Start Image Optimization"))


    def compress_jpeg_mozjpeg(self, input_path, output_path, quality):
        """Compress JPEG using MozJPEG"""
        try:
            cjpeg_path = str(self.engine_dir / 'cjpeg.exe')
            cmd = [cjpeg_path, '-quality', str(quality), '-optimize',
                   '-progressive', '-outfile', output_path, input_path]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except:
            return False

    def compress_png_oxipng(self, input_path, output_path):
        """Compress PNG using OxiPNG"""
        try:
            shutil.copy2(input_path, output_path)
            oxipng_path = str(self.engine_dir / 'oxipng.exe')
            cmd = [oxipng_path, '-o', '6', '-i', '0', '--strip', 'safe', output_path]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except:
            return False

    def compress_png_pngquant(self, input_path, output_path, quality):
        """Compress PNG using pngquant"""
        try:
            pngquant_path = str(self.engine_dir / 'pngquant.exe')
            quality_min = max(1, quality - 15)
            cmd = [pngquant_path, '--quality', f'{quality_min}-{quality}',
                   '--output', output_path, input_path]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except:
            return False

    def compress_image_pil(self, img, output_path, extension, quality):
        """Fallback compression using PIL/Pillow"""
        if extension in ['.jpg', '.jpeg']:
            img = img.convert('RGB')
            img.save(output_path, format='JPEG', quality=quality,
                     optimize=True, progressive=True, subsampling='4:2:0')
        elif extension == '.png':
            if quality < 95:
                img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=256)
            img.save(output_path, format='PNG', optimize=True, compress_level=9)
        elif extension == '.webp':
            img.save(output_path, format='WEBP', quality=quality, method=6, optimize=True)
        elif extension in ['.bmp']:
            img = img.convert('RGB')
            output_path = str(Path(output_path).with_suffix('.jpg'))
            img.save(output_path, format='JPEG', quality=quality, optimize=True, progressive=True)
        elif extension in ['.tiff', '.tif']:
            img.save(output_path, format='TIFF', compression='tiff_lzw')
        else:
            img = img.convert('RGB')
            output_path = str(Path(output_path).with_suffix('.jpg'))
            img.save(output_path, format='JPEG', quality=quality, optimize=True)
        return output_path

    def calculate_optimal_settings(self, metadata, mode):
        width = metadata['width']
        height = metadata['height']
        fps = metadata['fps']
        source_bitrate = metadata['bitrate']

        should_downscale = False
        is_portrait = height > width

        if max(width, height) > 3840:
            should_downscale = True
            orientation = "Portrait" if is_portrait else "Landscape"
            self.log_to_video_terminal(f"[WARN] High Resolution ({orientation}) Detected. Downscaling to 1080p for GPU compatibility.")

        # Determine resolution category
        if width >= 3840 or height >= 2160: res_cat = '4k'
        elif width >= 1920 or height >= 1080: res_cat = '1080p'
        elif width >= 1280 or height >= 720: res_cat = '720p'
        else: res_cat = 'default'

        # Calculate source quality indicator (bits per pixel per frame)
        pixels = width * height
        bpp = (source_bitrate / (pixels * fps)) if (pixels > 0 and fps > 0) else 0
        
        # Determine source quality level
        # High quality: bpp > 0.15, Medium: 0.08-0.15, Low: < 0.08
        if bpp > 0.15:
            source_quality = "high"
        elif bpp > 0.08:
            source_quality = "medium"
        else:
            source_quality = "low"

        # For AUTO mode, dynamically adjust based on source quality
        if mode == 'auto':
            self.log_to_video_terminal(f"[ANALYZE] Source Quality: {source_quality.upper()} (BPP: {bpp:.3f})")
            
            if source_quality == 'low':
                # Poor quality source - be very gentle, minimal compression
                mode = 'quality'  # Use quality preset
                self.log_to_video_terminal("[DECISION] Low quality source detected. Using gentle compression.")
            elif source_quality == 'medium':
                # Medium quality - use balanced compression
                mode = 'balanced'
                self.log_to_video_terminal("[DECISION] Medium quality source. Using balanced compression.")
            else:
                # High quality source - can compress more aggressively
                mode = 'balanced'
                self.log_to_video_terminal("[DECISION] High quality source. Using standard compression.")

        crf_map = {
            'fast': {'4k': 23, '1080p': 23, '720p': 23, 'default': 23},
            'balanced': {'4k': 20, '1080p': 20, '720p': 21, 'default': 22},
            'quality': {'4k': 18, '1080p': 18, '720p': 19, 'default': 20},
            'maximum': {'4k': 28, '1080p': 28, '720p': 30, 'default': 30}
        }

        crf = crf_map[mode][res_cat]
        
        # For low quality sources, use even lower CRF (better quality)
        if source_quality == 'low':
            crf = max(crf - 3, 15)  # Lower CRF = better quality
            self.log_to_video_terminal(f"[ADJUST] CRF reduced to {crf} to preserve quality")
        
        preset_map = {'fast': 'veryfast', 'balanced': 'medium', 'quality': 'slow', 'maximum': 'slow'}
        preset = preset_map[mode]

        target_fps = fps
        if mode == 'maximum' and fps > 30: target_fps = 30

        audio_bitrate = min(metadata.get('audio_bitrate', 128000), 128000)
        if mode == 'maximum': audio_bitrate = 96000

        # Adjust reduction factor based on source quality
        reduction_factors = {'fast': 0.80, 'balanced': 0.70, 'quality': 0.85, 'maximum': 0.50}
        factor = reduction_factors[mode]
        
        # For low quality sources, don't compress as much
        if source_quality == 'low':
            factor = min(factor + 0.15, 0.95)  # Less reduction
            self.log_to_video_terminal(f"[ADJUST] Reduction factor set to {int(factor*100)}% to preserve quality")

        max_bitrate = 0
        buf_size = 0

        if source_bitrate > 100000:
            target_bitrate = int(source_bitrate * factor)
            max_bitrate = target_bitrate
            buf_size = target_bitrate * 2
            self.log_to_video_terminal(f"[INFO] Source Bitrate: {source_bitrate//1000} kbps")
            self.log_to_video_terminal(f"[DECISION] Capping output to {max_bitrate//1000} kbps")
        else:
            self.log_to_video_terminal("[INFO] Low/Unknown bitrate. Using CRF only.")

        return {
            'crf': crf, 'preset': preset, 'target_fps': target_fps,
            'audio_bitrate': audio_bitrate // 1000, 'use_fps_filter': target_fps != fps,
            'max_bitrate': max_bitrate, 'buf_size': buf_size,
            'should_downscale': should_downscale, 'is_portrait': is_portrait,
            'source_quality': source_quality
        }




    # =========================================================================
    # UI CONSTRUCTION
    # =========================================================================

    def setup_ui(self):
        # Main Layout: Split View
        main_container = tk.Frame(self.root, bg=self.theme["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Left Panel: Image Compression
        left_panel = tk.Frame(main_container, bg=self.theme["panel_bg"], relief=tk.RIDGE, bd=1)
        left_panel.is_panel = True
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Right Panel: Video Compression
        right_panel = tk.Frame(main_container, bg=self.theme["panel_bg"], relief=tk.RIDGE, bd=1)
        right_panel.is_panel = True
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # --- Setup Panels ---
        self.setup_image_panel(left_panel)
        self.setup_video_panel(right_panel)

        # Status Bar (Bottom)
        self.setup_status_bar()

    def setup_status_bar(self):
        status_frame = tk.Frame(self.root, bg=self.theme["header_bg"], height=35)
        status_frame.is_header = True
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Theme Toggle
        theme_text = "🌙 Dark Mode" if not self.is_dark_mode else "☀️ Light Mode"
        self.theme_btn = tk.Button(status_frame, text=theme_text, command=self.toggle_theme,
                                   bg=self.theme["accent"], fg="white" if not self.is_dark_mode else "black",
                                   font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, cursor="hand2")
        self.theme_btn.pack(side=tk.RIGHT, padx=10, pady=5)

        tools = []
        tools.append(f"Pillow (✓)")
        if self.has_mozjpeg: tools.append("MozJPEG (✓)")
        if self.has_oxipng: tools.append("OxiPNG (✓)")
        if self.has_pngquant: tools.append("PNGQuant (✓)")
        
        if self.has_ffmpeg:
            hw = f"({self.hw_accel_type.upper()})" if self.hw_accel_type else "(CPU)"
            tools.append(f"FFmpeg {hw} (✓)")
        else:
            tools.append("FFmpeg (Missing)")

        status_text = "Active Engines: " + " | ".join(tools)
        lbl = tk.Label(status_frame, text=status_text, font=("Segoe UI", 9),
                 bg=self.theme["header_bg"], fg=self.theme["fg_secondary"], padx=10, pady=5)
        lbl.is_header = True
        lbl.pack(side=tk.LEFT)

    def setup_image_panel(self, parent):
        # Header
        header = tk.Label(parent, text="IMAGE OPTIMIZATION (AI-POWERED)", font=("Segoe UI", 12, "bold"),
                          bg=self.theme["header_bg"], fg=self.theme["fg"], pady=10, relief=tk.FLAT)
        header.is_header = True
        header.pack(fill=tk.X)

        content = tk.Frame(parent, bg=self.theme["panel_bg"], padx=20, pady=20)
        content.is_panel = True
        content.pack(fill=tk.BOTH, expand=True)

        # --- Input Section ---
        self.create_file_input(content, "Source Folder:", self.batch_input_folder, self.browse_batch_input)
        self.create_file_input(content, "Output Folder:", self.batch_output_folder, self.browse_batch_output)

        # Settings Group
        settings_frame = tk.LabelFrame(content, text="Configuration", font=("Segoe UI", 9, "bold"), 
                                       bg=self.theme["panel_bg"], fg=self.theme["fg"], padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=15)

        # Compression Profile
        tk.Label(settings_frame, text="Compression Profile:", font=("Segoe UI", 9), 
                 bg=self.theme["panel_bg"], fg=self.theme["fg"]).pack(anchor="w")
        modes_frame = tk.Frame(settings_frame, bg=self.theme["panel_bg"])
        modes_frame.pack(fill=tk.X, pady=5)

        modes = [("Auto", "auto"), ("Fast", "fast"), ("Balanced", "balanced"), 
                 ("Quality", "quality"), ("Max", "maximum")]
        for text, val in modes:
            tk.Radiobutton(modes_frame, text=text, variable=self.image_compression_mode, value=val,
                           bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                           activebackground=self.theme["panel_bg"], activeforeground=self.theme["fg"],
                           selectcolor=self.theme["panel_bg"],
                           font=("Segoe UI", 9), cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

        # Toggles
        tk.Checkbutton(settings_frame, text="Move found videos to 'your_videos' folder", 
                       variable=self.copy_videos_in_image_batch,
                       bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                       activebackground=self.theme["panel_bg"], activeforeground=self.theme["fg"],
                       selectcolor=self.theme["panel_bg"],
                       font=("Segoe UI", 9), cursor="hand2").pack(anchor="w", pady=(5, 0))

        # Terminal / Process Log
        tk.Label(content, text="Process Log:", font=("Segoe UI", 9, "bold"), 
                 bg=self.theme["panel_bg"], fg=self.theme["fg"]).pack(anchor="w")
        self.image_stats_text = tk.Text(content, height=12, font=("Consolas", 9),
                                        bg=self.theme["terminal_bg"], fg=self.theme["terminal_fg"], 
                                        relief=tk.FLAT, padx=10, pady=10)
        self.image_stats_text.is_terminal = True
        self.image_stats_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Progress
        self.progress = ttk.Progressbar(content, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(10, 5))
        self.progress_label = tk.Label(content, text="Ready", font=("Segoe UI", 8), 
                                       bg=self.theme["panel_bg"], fg=self.theme["fg_secondary"])
        self.progress_label.pack(anchor="w")

        # Action
        self.batch_compress_btn = tk.Button(content, text="Start Image Optimization", command=self.compress_batch,
                                            bg=self.theme["btn_batch"], fg="white", font=("Segoe UI", 10, "bold"),
                                            relief=tk.FLAT, padx=15, pady=10, cursor="hand2")
        self.batch_compress_btn.btn_type = 'batch'
        self.batch_compress_btn.pack(pady=15, fill=tk.X)


    def setup_video_panel(self, parent):
        # Header
        header = tk.Label(parent, text="VIDEO TRANSCODING (AI-POWERED)", font=("Segoe UI", 12, "bold"),
                          bg=self.theme["header_bg"], fg=self.theme["fg"], pady=10, relief=tk.FLAT)
        header.is_header = True
        header.pack(fill=tk.X)

        content = tk.Frame(parent, bg=self.theme["panel_bg"], padx=20, pady=20)
        content.is_panel = True
        content.pack(fill=tk.BOTH, expand=True)

        if not self.has_ffmpeg:
            tk.Label(content, text="[ERROR] FFmpeg not detected. Video features disabled.",
                     bg="#f8d7da", fg="#721c24", padx=10, pady=10).pack(fill=tk.X)
            return

        # Inputs
        self.create_file_input(content, "Source Folder:", self.video_input_folder, self.browse_video_input)
        self.create_file_input(content, "Output Folder:", self.video_output_folder, self.browse_video_output)

        # Settings Group
        settings_frame = tk.LabelFrame(content, text="Configuration", font=("Segoe UI", 9, "bold"), bg=self.theme["panel_bg"], fg=self.theme["fg"], padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=15)

        # Modes
        tk.Label(settings_frame, text="Compression Profile:", font=("Segoe UI", 9), bg=self.theme["panel_bg"], fg=self.theme["fg"]).pack(anchor="w")
        modes_frame = tk.Frame(settings_frame, bg=self.theme["panel_bg"])
        modes_frame.pack(fill=tk.X, pady=5)

        modes = [("Auto", "auto"), ("Fast", "fast"), ("Balanced", "balanced"), ("Quality", "quality"), ("Max", "maximum")]
        for text, val in modes:
            tk.Radiobutton(modes_frame, text=text, variable=self.video_compression_mode, value=val,
                           bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                           activebackground=self.theme["panel_bg"], activeforeground=self.theme["fg"],
                           selectcolor=self.theme["entry_bg"],
                           font=("Segoe UI", 9), cursor="hand2").pack(side=tk.LEFT, padx=(0, 10))

        # Toggles
        tk.Checkbutton(settings_frame, text="Copy videos smaller than 5MB directly", variable=self.skip_small_videos,
                       bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                       activebackground=self.theme["panel_bg"], activeforeground=self.theme["fg"],
                       selectcolor=self.theme["entry_bg"],
                       font=("Segoe UI", 9), cursor="hand2").pack(anchor="w", pady=(5, 0))

        if self.hw_accel_type:
            tk.Checkbutton(settings_frame, text=f"Enable Hardware Acceleration ({self.hw_accel_type.upper()})",
                           variable=self.use_hardware_accel, bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                           activebackground=self.theme["panel_bg"], activeforeground=self.theme["fg"],
                           selectcolor=self.theme["entry_bg"],
                           font=("Segoe UI", 9), cursor="hand2").pack(anchor="w")

        tk.Checkbutton(settings_frame, text="Convert .ts to MP4 before compressing",
                       variable=self.convert_ts_to_mp4, bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                       activebackground=self.theme["panel_bg"], activeforeground=self.theme["fg"],
                       selectcolor=self.theme["entry_bg"],
                       font=("Segoe UI", 9), cursor="hand2").pack(anchor="w")

        # Unify Extensions Frame
        unify_frame = tk.Frame(settings_frame, bg=self.theme["panel_bg"])
        unify_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Checkbutton(unify_frame, text="Unify video extensions to:", 
                       variable=self.unify_extension,
                       bg=self.theme["panel_bg"], fg=self.theme["fg"], 
                       activebackground=self.theme["panel_bg"], activeforeground=self.theme["fg"],
                       selectcolor=self.theme["entry_bg"],
                       font=("Segoe UI", 9), cursor="hand2").pack(side=tk.LEFT)
                       
        ext_combo = ttk.Combobox(unify_frame, textvariable=self.target_extension, 
                                 values=[".mp4", ".mkv", ".mov", ".avi", ".webm"], 
                                 width=6, state="readonly", font=("Segoe UI", 9))
        ext_combo.pack(side=tk.LEFT, padx=5)


        # Terminal
        tk.Label(content, text="Process Log:", font=("Segoe UI", 9, "bold"), bg=self.theme["panel_bg"], fg=self.theme["fg"]).pack(anchor="w")
        self.video_stats_text = tk.Text(content, height=15, font=("Consolas", 9),
                                        bg=self.theme["terminal_bg"], fg=self.theme["terminal_fg"], relief=tk.FLAT, padx=10, pady=10)
        self.video_stats_text.is_terminal = True
        self.video_stats_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Video Progress
        self.video_progress = ttk.Progressbar(content, mode='determinate')
        self.video_progress.pack(fill=tk.X, pady=(10, 5))
        self.video_progress_label = tk.Label(content, text="Ready", font=("Segoe UI", 8), bg=self.theme["panel_bg"], fg=self.theme["fg_secondary"])
        self.video_progress_label.pack(anchor="w")

        # Action
        self.video_compress_btn = tk.Button(content, text="Start Video Optimization", command=self.compress_videos_batch,
                                            bg=self.theme["btn_video"], fg="white", font=("Segoe UI", 10, "bold"),
                                            relief=tk.FLAT, padx=15, pady=10, cursor="hand2")
        self.video_compress_btn.btn_type = 'video'
        self.video_compress_btn.pack(pady=15, fill=tk.X)

    def create_file_input(self, parent, label_text, variable, command):
        frame = tk.Frame(parent, bg=self.theme["panel_bg"])
        frame.is_panel = True
        frame.pack(fill=tk.X, pady=5)
        tk.Label(frame, text=label_text, font=("Segoe UI", 9), bg=self.theme["panel_bg"], fg=self.theme["fg"], width=12, anchor="w").pack(side=tk.LEFT)
        entry = tk.Entry(frame, textvariable=variable, font=("Segoe UI", 9), bg=self.theme["entry_bg"], fg=self.theme["fg"], insertbackground=self.theme["fg"], relief=tk.FLAT)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=3)
        btn = tk.Button(frame, text="Browse", command=command, bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
                  font=("Segoe UI", 8), relief=tk.FLAT, cursor="hand2")
        btn.btn_type = 'primary'
        btn.pack(side=tk.LEFT)



    # =========================================================================
    # VIDEO LOGIC
    # =========================================================================

    def get_video_metadata(self, video_path):
        try:
            ffprobe_path = str(self.engine_dir / 'ffprobe.exe')
            cmd = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=30)
            data = json.loads(result.stdout)

            video_stream = next((s for s in data.get('streams', []) if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in data.get('streams', []) if s['codec_type'] == 'audio'), None)

            if not video_stream: return None

            fps_str = video_stream.get('r_frame_rate', '30/1')
            try:
                num, den = map(int, fps_str.split('/'))
                fps = num / den if den != 0 else 30
            except: fps = 30

            bitrate = int(video_stream.get('bit_rate', 0))
            if bitrate == 0:
                bitrate = int(data.get('format', {}).get('bit_rate', 0))

            duration = float(data.get('format', {}).get('duration', 0))
            if bitrate == 0 and duration > 0:
                size_bits = os.path.getsize(video_path) * 8
                bitrate = int(size_bits / duration)

            return {
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': round(fps, 2),
                'codec': video_stream.get('codec_name', 'unknown'),
                'bitrate': bitrate,
                'duration': duration,
                'has_audio': audio_stream is not None,
                'audio_codec': audio_stream.get('codec_name', 'none') if audio_stream else 'none',
                'audio_bitrate': int(audio_stream.get('bit_rate', 128000)) if audio_stream and 'bit_rate' in audio_stream else 128000
            }
        except Exception as e:
            self.log_to_video_terminal(f"[ERROR] Metadata read failed: {e}")
            return None

    def calculate_optimal_settings(self, metadata, mode):
        width = metadata['width']
        height = metadata['height']
        fps = metadata['fps']
        source_bitrate = metadata['bitrate']

        should_downscale = False
        is_portrait = height > width

        if max(width, height) > 3840:
            should_downscale = True
            orientation = "Portrait" if is_portrait else "Landscape"
            self.log_to_video_terminal(f"[WARN] High Resolution ({orientation}) Detected. Downscaling to 1080p for GPU compatibility.")

        # Determine resolution category
        if width >= 3840 or height >= 2160: res_cat = '4k'
        elif width >= 1920 or height >= 1080: res_cat = '1080p'
        elif width >= 1280 or height >= 720: res_cat = '720p'
        else: res_cat = 'default'

        # Calculate source quality indicator (bits per pixel per frame)
        pixels = width * height
        bpp = (source_bitrate / (pixels * fps)) if (pixels > 0 and fps > 0) else 0
        
        # Determine source quality level
        # High quality: bpp > 0.15, Medium: 0.08-0.15, Low: < 0.08
        if bpp > 0.15:
            source_quality = "high"
        elif bpp > 0.08:
            source_quality = "medium"
        else:
            source_quality = "low"

        # For AUTO mode, dynamically adjust based on source quality
        if mode == 'auto':
            self.log_to_video_terminal(f"[ANALYZE] Source Quality: {source_quality.upper()} (BPP: {bpp:.3f})")
            
            if source_quality == 'low':
                # Poor quality source - be very gentle, minimal compression
                mode = 'quality'  # Use quality preset
                self.log_to_video_terminal("[DECISION] Low quality source detected. Using gentle compression.")
            elif source_quality == 'medium':
                # Medium quality - use balanced compression
                mode = 'balanced'
                self.log_to_video_terminal("[DECISION] Medium quality source. Using balanced compression.")
            else:
                # High quality source - can compress more aggressively
                mode = 'balanced'
                self.log_to_video_terminal("[DECISION] High quality source. Using standard compression.")

        crf_map = {
            'fast': {'4k': 23, '1080p': 23, '720p': 23, 'default': 23},
            'balanced': {'4k': 20, '1080p': 20, '720p': 21, 'default': 22},
            'quality': {'4k': 18, '1080p': 18, '720p': 19, 'default': 20},
            'maximum': {'4k': 28, '1080p': 28, '720p': 30, 'default': 30}
        }

        crf = crf_map[mode][res_cat]
        
        # For low quality sources, use even lower CRF (better quality)
        if source_quality == 'low':
            crf = max(crf - 3, 15)  # Lower CRF = better quality
            self.log_to_video_terminal(f"[ADJUST] CRF reduced to {crf} to preserve quality")
        
        preset_map = {'fast': 'veryfast', 'balanced': 'medium', 'quality': 'slow', 'maximum': 'slow'}
        preset = preset_map[mode]

        target_fps = fps
        if mode == 'maximum' and fps > 30: target_fps = 30

        audio_bitrate = min(metadata.get('audio_bitrate', 128000), 128000)
        if mode == 'maximum': audio_bitrate = 96000

        # Adjust reduction factor based on source quality
        reduction_factors = {'fast': 0.80, 'balanced': 0.70, 'quality': 0.85, 'maximum': 0.50}
        factor = reduction_factors[mode]
        
        # For low quality sources, don't compress as much
        if source_quality == 'low':
            factor = min(factor + 0.15, 0.95)  # Less reduction
            self.log_to_video_terminal(f"[ADJUST] Reduction factor set to {int(factor*100)}% to preserve quality")

        max_bitrate = 0
        buf_size = 0

        if source_bitrate > 100000:
            target_bitrate = int(source_bitrate * factor)
            max_bitrate = target_bitrate
            buf_size = target_bitrate * 2
            self.log_to_video_terminal(f"[INFO] Source Bitrate: {source_bitrate//1000} kbps")
            self.log_to_video_terminal(f"[DECISION] Capping output to {max_bitrate//1000} kbps")
        else:
            self.log_to_video_terminal("[INFO] Low/Unknown bitrate. Using CRF only.")

        return {
            'crf': crf, 'preset': preset, 'target_fps': target_fps,
            'audio_bitrate': audio_bitrate // 1000, 'use_fps_filter': target_fps != fps,
            'max_bitrate': max_bitrate, 'buf_size': buf_size,
            'should_downscale': should_downscale, 'is_portrait': is_portrait,
            'source_quality': source_quality
        }


    def create_temp_downscaled_file(self, input_path, temp_path, is_portrait):
        ffmpeg_path = str(self.engine_dir / 'ffmpeg.exe')
        scale_filter = 'scale=-2:1920' if is_portrait else 'scale=1920:-2'
        cmd = [
            ffmpeg_path, '-y', '-hwaccel', 'auto', '-i', input_path,
            '-vf', scale_filter, '-c:v', 'libx264', '-preset', 'ultrafast',
            '-crf', '20', '-c:a', 'copy', temp_path
        ]
        return cmd

    def build_ffmpeg_command(self, input_path, output_path, metadata, settings, force_cpu=False):
        ffmpeg_path = str(self.engine_dir / 'ffmpeg.exe')
        cmd = [ffmpeg_path, '-y', '-i', input_path]
        use_hw = self.use_hardware_accel.get() and self.hw_accel_type and not force_cpu

        if use_hw:
            if self.hw_accel_type == 'nvenc':
                cmd.extend(['-c:v', 'h264_nvenc', '-preset', 'p4', '-cq', str(settings['crf'])])
            elif self.hw_accel_type == 'qsv':
                cmd.extend(['-c:v', 'h264_qsv', '-preset', settings['preset'], '-global_quality', str(settings['crf'])])
            elif self.hw_accel_type == 'amf':
                cmd.extend(['-c:v', 'h264_amf', '-quality', 'balanced', '-qp_i', str(settings['crf'])])
        else:
            cmd.extend(['-c:v', 'libx264', '-crf', str(settings['crf']), '-preset', settings['preset']])

        if settings['max_bitrate'] > 0:
            cmd.extend(['-maxrate', str(settings['max_bitrate']), '-bufsize', str(settings['buf_size'])])

        if settings['use_fps_filter']:
            cmd.extend(['-r', str(settings['target_fps'])])

        cmd.extend(['-movflags', '+faststart', '-pix_fmt', 'yuv420p'])

        if metadata['has_audio']:
            cmd.extend(['-c:a', 'aac', '-b:a', f"{settings['audio_bitrate']}k"])
        else:
            cmd.extend(['-an'])

        cmd.append(output_path)
        return cmd

    def compress_videos_batch(self):
        if self.is_processing:
            messagebox.showwarning("Busy", "Operation in progress.")
            return

        if not self.video_input_folder.get() or not self.video_output_folder.get():
            messagebox.showerror("Error", "Please select input and output folders.")
            return

        if self.video_input_folder.get() == self.video_output_folder.get():
            messagebox.showerror("Error", "Input and Output folders must be different.")
            return

        self.is_processing = True
        self.video_compress_btn.config(state='disabled', text="Processing...")
        self.video_stats_text.delete(1.0, tk.END)
        self.log_to_video_terminal("[INIT] Starting Video Optimization Engine...")
        self.log_to_video_terminal(f"[PATH] Input: {self.video_input_folder.get()}")
        self.log_to_video_terminal(f"[PATH] Output: {self.video_output_folder.get()}")
        self.log_to_video_terminal("-" * 60)

        thread = threading.Thread(target=self._compress_videos_worker, daemon=True)
        thread.start()

    def _compress_videos_worker(self):
        try:
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv', '.ts'}
            input_folder = Path(self.video_input_folder.get())
            output_folder = Path(self.video_output_folder.get())
            output_folder.mkdir(parents=True, exist_ok=True)

            temp_work_folder = output_folder / "_temp_work"
            temp_work_folder.mkdir(exist_ok=True)

            video_files = [f for f in input_folder.iterdir() if f.is_file() and f.suffix.lower() in video_extensions]

            if not video_files:
                self.root.after(0, messagebox.showwarning, "Warning", "No video files found.")
                return

            total_files = len(video_files)
            self.root.after(0, lambda: self.video_progress.configure(maximum=total_files, value=0))

            total_orig = 0
            total_comp = 0
            skipped = 0
            compressed = 0
            failed = 0
            mode = self.video_compression_mode.get()

            for idx, video_path in enumerate(video_files):
                self.log_to_video_terminal(f"\n[VIDEO] Processing [{idx + 1}/{total_files}]: {video_path.name}")

                try:
                    original_size = os.path.getsize(video_path)
                    total_orig += original_size

                    # Determine output extension
                    if self.unify_extension.get() and self.target_extension.get():
                        target_ext = self.target_extension.get()
                        output_filename = video_path.stem + target_ext
                        self.log_to_video_terminal(f"[UNIFY] Target Extension: {target_ext}")
                    else:
                        output_filename = video_path.name
                        if video_path.suffix.lower() == '.ts' and self.convert_ts_to_mp4.get():
                            output_filename = video_path.stem + '.mp4'

                    output_path = output_folder / output_filename

                    if self.skip_small_videos.get() and original_size < 5 * 1024 * 1024:
                        ffmpeg_path = str(self.engine_dir / 'ffmpeg.exe')
                        # If skipping, but unification is on, we still need to convert if extension doesn't match
                        if self.unify_extension.get() and video_path.suffix.lower() != target_ext:
                            self.log_to_video_terminal(f"[CONVERT] File < 5MB but needs extension change. converting...")
                            # Simple remux/convert for small files
                            convert_cmd = [ffmpeg_path, '-y', '-i', str(video_path), '-c', 'copy', str(output_path)]
                            subprocess.run(convert_cmd, capture_output=True)
                        elif video_path.suffix.lower() == '.ts' and self.convert_ts_to_mp4.get():
                             # Convert TS small files if requested
                             self.log_to_video_terminal(f"[CONVERT] TS File < 5MB. Converting to MP4...")
                             convert_cmd = [ffmpeg_path, '-y', '-i', str(video_path), '-c', 'copy', str(output_path)]
                             subprocess.run(convert_cmd, capture_output=True)
                        else:
                             shutil.copy2(video_path, output_path)
                             self.log_to_video_terminal(f"[SKIP] File < 5MB. Copied/Converted.")
                        
                        if output_path.exists():
                             total_comp += os.path.getsize(output_path)
                             skipped += 1
                    else:
                        current_input_path = str(video_path)
                        is_temp_file = False

                        # Handle explicit TS conversion OR generic extension unification via temp file
                        # User strictly wants "convert then compress" workflow for reliability
                        needs_pre_conversion = False
                        
                        if video_path.suffix.lower() == '.ts' and self.convert_ts_to_mp4.get():
                            needs_pre_conversion = True
                        elif self.unify_extension.get() and self.target_extension.get():
                            # Enforce temp conversion for Unify as well
                            needs_pre_conversion = True
                        
                        if needs_pre_conversion:
                            target_temp_ext = self.target_extension.get() if self.unify_extension.get() else '.mp4'
                            temp_conv_path = temp_work_folder / (video_path.stem + '_temp' + target_temp_ext)
                            
                            self.log_to_video_terminal(f"[PRE-PROC] Standardizing container to {target_temp_ext}...")
                            
                            ffmpeg_path = str(self.engine_dir / 'ffmpeg.exe')
                            # Try remuxing primarily (fast, lossless container swap)
                            convert_cmd = [ffmpeg_path, '-y', '-i', str(video_path), '-c', 'copy', '-map', '0', str(temp_conv_path)]
                            
                            # If input is TS and output is MP4, add bitstream filter for safety
                            if video_path.suffix.lower() == '.ts' and target_temp_ext == '.mp4':
                                convert_cmd = [ffmpeg_path, '-y', '-i', str(video_path), '-c', 'copy', '-bsf:a', 'aac_adtstoasc', str(temp_conv_path)]
                                
                            proc = subprocess.run(convert_cmd, capture_output=True)
                            
                            if temp_conv_path.exists() and os.path.getsize(temp_conv_path) > 0:
                                current_input_path = str(temp_conv_path)
                                is_temp_file = True
                                self.log_to_video_terminal("[DONE] Standardization complete.")
                            else:
                                self.log_to_video_terminal("[WARN] Standardization failed (likely codec incompatibility). Using original.")

                        self.log_to_video_terminal("[SCAN] Analyzing metadata...")
                        metadata = self.get_video_metadata(current_input_path)

                        if not metadata:
                            self.log_to_video_terminal("[FAIL] Metadata read error. Skipping.")
                            failed += 1
                            continue

                        self.log_to_video_terminal(f"[INFO] {metadata['width']}x{metadata['height']} | {metadata['fps']} FPS | {metadata['codec']}")
                        self.log_to_video_terminal(f"[SIZE] Original: {self.format_bytes(original_size)}")

                        settings = self.calculate_optimal_settings(metadata, mode)

                        if settings['should_downscale']:
                            temp_file_path = temp_work_folder / f"temp_{video_path.name}"
                            self.log_to_video_terminal(f"[PROC] Creating 1080p intermediate file...")
                            downscale_cmd = self.create_temp_downscaled_file(current_input_path, str(temp_file_path), settings['is_portrait'])
                            subprocess.run(downscale_cmd, capture_output=True)

                            if temp_file_path.exists() and os.path.getsize(temp_file_path) > 0:
                                # Clean up previous temp file if it existed
                                if is_temp_file:
                                    try: os.remove(current_input_path)
                                    except: pass
                                
                                current_input_path = str(temp_file_path)
                                is_temp_file = True
                                self.log_to_video_terminal("[DONE] Intermediate file created.")
                            else:
                                self.log_to_video_terminal("[WARN] Intermediate creation failed. Attempting direct.")

                        attempts = 0
                        max_attempts = 3
                        success_compression = False
                        comp_size = 0
                        duration = 0

                        while attempts < max_attempts:
                            attempts += 1
                            if attempts > 1:
                                self.log_to_video_terminal(f"[RETRY] Shot {attempts}/{max_attempts} - Increasing compression...")
                                # Dynamically increase compression
                                settings['crf'] += 4 
                                if settings['max_bitrate'] > 0:
                                    settings['max_bitrate'] = int(settings['max_bitrate'] * 0.8)
                                    settings['buf_size'] = int(settings['max_bitrate'] * 2)
                                else:
                                    # If no bitrate cap, force one based on previous failure
                                    pixels = metadata['width'] * metadata['height']
                                    target_bpp = 0.07 if attempts == 2 else 0.05
                                    settings['max_bitrate'] = int(pixels * metadata['fps'] * target_bpp)
                                    settings['buf_size'] = settings['max_bitrate'] * 2

                            cmd = self.build_ffmpeg_command(current_input_path, str(output_path), metadata, settings, force_cpu=False)


                            self.log_to_video_terminal(f"[SETT] CRF: {settings['crf']} | Preset: {settings['preset']} {'| Cap: ' + str(settings['max_bitrate']//1000) + 'k' if settings['max_bitrate'] > 0 else ''}")
                            self.log_to_video_terminal(f"[BUSY] Compressing (Attempt {attempts})...")

                            start_time = time.time()
                            process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

                            if process.returncode != 0:
                                self.log_to_video_terminal(f"[WARN] Encoding error. Retrying with CPU...")
                                cmd_cpu = self.build_ffmpeg_command(current_input_path, str(output_path), metadata, settings, force_cpu=True)
                                process = subprocess.run(cmd_cpu, capture_output=True, text=True, encoding='utf-8')

                            duration = time.time() - start_time

                            if output_path.exists() and os.path.getsize(output_path) > 0:
                                comp_size = os.path.getsize(output_path)
                                if comp_size < original_size:
                                    success_compression = True
                                    break
                                else:
                                    self.log_to_video_terminal(f"[WARN] Result larger than source: {self.format_bytes(comp_size)}")
                                    if attempts < max_attempts:
                                        try: os.remove(output_path)
                                        except: pass
                            else:
                                self.log_to_video_terminal("[FAIL] Output empty. Breaking loop.")
                                break

                        if is_temp_file:
                            try: os.remove(current_input_path)
                            except: pass

                        if success_compression:
                            reduction = ((original_size - comp_size) / original_size) * 100
                            total_comp += comp_size
                            compressed += 1
                            self.log_to_video_terminal(f"[DONE] Finished in {duration:.1f}s")
                            self.log_to_video_terminal(f"[STAT] {self.format_bytes(original_size)} -> {self.format_bytes(comp_size)} (Saved {reduction:.1f}%)")
                        else:
                            self.log_to_video_terminal("[GIVEUP] Could not reduce size after 3 shots. Reverting to original.")
                            # If Unify is on, we must at least remux to the target extension
                            if self.unify_extension.get() and video_path.suffix.lower() != target_ext:
                                self.log_to_video_terminal(f"[UNIFY] Remuxing original to {target_ext}...")
                                ffmpeg_path = str(self.engine_dir / 'ffmpeg.exe')
                                remux_cmd = [ffmpeg_path, '-y', '-i', str(video_path), '-c', 'copy', '-map', '0', str(output_path)]
                                subprocess.run(remux_cmd, capture_output=True)
                            else:
                                shutil.copy2(video_path, output_path)
                            
                            comp_size = os.path.getsize(output_path) if output_path.exists() else original_size
                            total_comp += comp_size
                            self.log_to_video_terminal(f"[STAT] Kept original size: {self.format_bytes(comp_size)}")

                except Exception as e:
                    failed += 1
                    self.log_to_video_terminal(f"[ERR] {str(e)}")

                self.root.after(0, lambda v=idx+1: self.video_progress.configure(value=v))

            try: temp_work_folder.rmdir()
            except: pass

            total_reduction = ((total_orig - total_comp) / total_orig * 100) if total_orig > 0 else 0

            summary = (f"\n{'='*60}\n"
                       f"FINAL REPORT\n"
                       f"{'='*60}\n"
                       f"Total: {total_files} | Compressed: {compressed} | Skipped: {skipped} | Failed: {failed}\n"
                       f"Original: {self.format_bytes(total_orig)}\n"
                       f"Final: {self.format_bytes(total_comp)}\n"
                       f"Saved: {self.format_bytes(total_orig - total_comp)} ({total_reduction:.1f}%)\n"
                       f"{'='*60}\n")

            self.log_to_video_terminal(summary)
            self.root.after(0, lambda: self.video_progress_label.config(text="Batch Completed"))
            self.root.after(0, messagebox.showinfo, "Complete", "Video optimization batch finished.")

        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Batch failed: {str(e)}")
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.video_compress_btn.config(state='normal', text="Start Video Optimization"))

    # =========================================================================
    # HELPERS
    # =========================================================================

    def browse_single_image(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.gif *.webp *.tiff"), ("All", "*.*")])
        if f: self.single_image_path.set(f)

    def browse_single_output(self):
        f = filedialog.askdirectory()
        if f: self.single_output_folder.set(f)

    def browse_batch_input(self):
        f = filedialog.askdirectory()
        if f: self.batch_input_folder.set(f)

    def browse_batch_output(self):
        f = filedialog.askdirectory()
        if f: self.batch_output_folder.set(f)

    def browse_video_input(self):
        f = filedialog.askdirectory()
        if f: self.video_input_folder.set(f)

    def browse_video_output(self):
        f = filedialog.askdirectory()
        if f: self.video_output_folder.set(f)

if __name__ == "__main__":
    import threading
    import itertools
    import ctypes

    # Fix for Windows Taskbar Icon:
    # Forces Windows to use the application icon instead of the Python interpreter icon.
    try:
        myappid = 'enterprise.media.optimizer.shrinkify.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

    class SplashScreen:
        def __init__(self, root, on_complete):
            self.root = root
            self.on_complete = on_complete
            
            # Configure Root for Splash
            self.root.overrideredirect(True)
            self.root.configure(bg="#121212")
            
            # Center Splash
            width, height = 400, 300
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")

            # --- UI Elements ---
            
            # Logo
            try:
                # Assuming logo.ico is in the same folder
                logo_path = os.path.join(os.path.dirname(__file__), "logo.ico")
                if os.path.exists(logo_path):
                    self.logo_img = Image.open(logo_path).resize((80, 80), Image.Resampling.LANCZOS)
                    from PIL import ImageTk
                    self.tk_logo = ImageTk.PhotoImage(self.logo_img)
                    tk.Label(self.root, image=self.tk_logo, bg="#121212").pack(pady=(30, 10))
            except Exception as e:
                print(f"Logo load error: {e}")

            # Title: Golden, Bold
            tk.Label(self.root, text="Shrinkify", font=("Segoe UI", 24, "bold"), 
                     bg="#121212", fg="#FFD700").pack(pady=5)

            # Status Message
            self.status_label = tk.Label(self.root, text="Getting started...", font=("Segoe UI", 10), 
                                         bg="#121212", fg="#aaaaaa")
            self.status_label.pack(pady=(20, 5))

            # Rotating Dots
            self.spinner_label = tk.Label(self.root, text="●", font=("Segoe UI", 14), 
                                          bg="#121212", fg="#007bff")
            self.spinner_label.pack()

            # --- State ---
            self.is_running = True
            
            # Start Animation and Logic
            self.animate_spinner()
            threading.Thread(target=self.run_checks, daemon=True).start()

        def animate_spinner(self):
            if not self.is_running: return
            
            try:
                if not self.root.winfo_exists():
                    self.is_running = False
                    return

                # Simple rotation effect characters
                chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                if not hasattr(self, 'spinner_idx'): self.spinner_idx = 0
                
                text = chars[self.spinner_idx]
                self.spinner_label.config(text=text)
                self.spinner_idx = (self.spinner_idx + 1) % len(chars)
                
                if self.is_running:
                    self.root.after(80, self.animate_spinner)
            except (tk.TclError, RuntimeError):
                self.is_running = False

        def update_status(self, text):
            if not self.is_running: return
            try:
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.status_label.config(text=text))
            except (tk.TclError, RuntimeError):
                pass

        def run_checks(self):
            print("\n" + "="*50)
            print("SHRINKIFY ENGINE STARTUP SCAN")
            print("="*50)

            # 1. Getting Started
            self.update_status("Getting started...")
            time.sleep(0.4) 

            # 2. Starting Engine (Scan)
            self.update_status("Starting engine...")
            print("[SCAN] Checking engine directory...")
            
            # PyInstaller compatible path scan
            if getattr(sys, 'frozen', False):
                base_path = Path(sys.executable).parent
            else:
                base_path = Path(__file__).parent
                
            engine_dir = base_path / "engine"
            if engine_dir.exists():
                 print(f"[OK] Engine Check: Folder found at {engine_dir}")
            else:
                 print("[ERR] Engine Check: Folder NOT found!")

            tools = ['ffmpeg.exe', 'ffprobe.exe', 'cjpeg.exe', 'oxipng.exe', 'pngquant.exe']
            for tool in tools:
                tool_path = engine_dir / tool
                if tool_path.exists():
                    print(f"[OK] Tool Found: {tool}")
                else:
                    print(f"[MISSING] Tool: {tool}")
            
            time.sleep(0.5)

            # 3. Opening GUI
            self.update_status("Opening Gui...")
            print("[INIT] Loading Interface...")
            time.sleep(0.3) 

            # Finish
            self.is_running = False
            self.root.after(0, self.finish)

        def finish(self):
            self.root.destroy()
            self.on_complete()

    def launch_main_app():
        main_root = tk.Tk()
        main_root.title("Shrinkify")  
        main_root.geometry("1280x900")
        
        # Set Icon for main app
        try:
            ico_path = os.path.join(os.path.dirname(__file__), "logo.ico")
            if os.path.exists(ico_path):
                main_root.iconbitmap(ico_path)
        except: pass

        app = EnterpriseMediaOptimizer(main_root)
        
        # Ensure title is set correctly in app __init__ too, or override here
        main_root.title("Shrinkify")
        
        main_root.mainloop()

    # Launch Sequence
    splash_root = tk.Tk()
    
    # Set Icon for splash
    try:
        ico_path = os.path.join(os.path.dirname(__file__), "logo.ico")
        if os.path.exists(ico_path):
            splash_root.iconbitmap(ico_path)
    except: pass
            
    splash = SplashScreen(splash_root, launch_main_app)
    splash_root.mainloop()
