"""
Setup (one time):
    pip install yt-dlp imageio-ffmpeg

Run the window version:
    python yt_downloader.py

Run from the command line instead:
    python yt_downloader.py "LINK" --audio
    python yt_downloader.py "LINK" --video
"""

# I made this cuz i hate spotify

import argparse
import queue
import shutil
import sys
import threading
from pathlib import Path

import yt_dlp

# ---------------------------------------------------------------------------
# Core logic (no window needed, so it can also run from the command line)
# ---------------------------------------------------------------------------

QUALITY_CHOICES = ["Best available", "1080p", "720p", "480p"]


# you need to run:
# pip install yt-dlp imageio-ffmpeg
def find_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def quality_to_height(quality):
    digits = "".join(ch for ch in str(quality) if ch.isdigit())
    return int(digits) if digits else None


def build_options(mode, folder, quality="Best available", progress_hook=None):
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg was not found. Run: pip install imageio-ffmpeg"
        )

    options = {
        "outtmpl": str(Path(folder) / "%(title)s.%(ext)s"),
        "noplaylist": True,          # one video only!!!!!!!!!
        "windowsfilenames": True,    # remove characters Windows doesn't allow
        "ffmpeg_location": ffmpeg,
        "quiet": True,
        "no_warnings": True,
    }
    if progress_hook:
        options["progress_hooks"] = [progress_hook]

    if mode == "audio":
        options["format"] = "bestaudio/best"
        options["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "FFmpegMetadata"},
        ]
    else:
        height = quality_to_height(quality)
        limit = f"[height<=?{height}]" if height else ""
        options["format"] = (
            f"bv*[ext=mp4]{limit}+ba[ext=m4a]/b[ext=mp4]{limit}/bv*{limit}+ba/b{limit}"
        )
        options["merge_output_format"] = "mp4"

    return options

# returns the downloaded vid's file path
def download(url, mode, folder, quality="Best available", on_progress=None, on_status=None):
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("Please paste a full link that starts with http:// or https://")

    folder = Path(folder).expanduser()
    folder.mkdir(parents=True, exist_ok=True)

    def hook(d):
        if d.get("status") == "downloading" and on_progress:
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                on_progress(min(100.0, d.get("downloaded_bytes", 0) * 100.0 / total))
        elif d.get("status") == "finished" and on_status:
            on_status("Download finished. Converting the file...")

    options = build_options(mode, folder, quality, hook)
    if on_status:
        on_status("Getting video information...")

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as error:
        # Keep the message short and readable.
        message = str(error).replace("ERROR: ", "").strip().splitlines()[0]
        raise RuntimeError(message) from None

    # After conversion the file name can change (for example .webm -> .mp3).
    downloads = info.get("requested_downloads") or []
    if downloads and downloads[0].get("filepath"):
        return downloads[0]["filepath"]
    return yt_dlp.YoutubeDL(options).prepare_filename(info)


# ---------------------------------------------------------------------------
# Window version
# ---------------------------------------------------------------------------

def run_window():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("Link to Audio or Video")
    root.geometry("560x360")
    root.resizable(False, False)

    url_var = tk.StringVar()
    mode_var = tk.StringVar(value="audio")
    quality_var = tk.StringVar(value="720p")
    folder_var = tk.StringVar(value=str(Path.home() / "Downloads"))
    status_var = tk.StringVar(value="Paste a link to begin.")
    messages = queue.Queue()

    frame = ttk.Frame(root, padding=18)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Video link").grid(row=0, column=0, sticky="w")
    url_entry = ttk.Entry(frame, textvariable=url_var, width=62)
    url_entry.grid(row=1, column=0, columnspan=3, sticky="we", pady=(2, 12))

    ttk.Label(frame, text="Save as").grid(row=2, column=0, sticky="w")
    options_row = ttk.Frame(frame)
    options_row.grid(row=3, column=0, columnspan=3, sticky="w", pady=(2, 12))
    ttk.Radiobutton(options_row, text="Audio only (MP3)", variable=mode_var, value="audio").pack(side="left")
    ttk.Radiobutton(options_row, text="Video (MP4)", variable=mode_var, value="video").pack(side="left", padx=(16, 8))
    quality_box = ttk.Combobox(options_row, textvariable=quality_var, values=QUALITY_CHOICES,
                               width=14, state="readonly")
    quality_box.pack(side="left")

    ttk.Label(frame, text="Save to folder").grid(row=4, column=0, sticky="w")
    ttk.Entry(frame, textvariable=folder_var, width=50).grid(row=5, column=0, columnspan=2, sticky="we", pady=(2, 12))

    def choose_folder():
        chosen = filedialog.askdirectory(initialdir=folder_var.get())
        if chosen:
            folder_var.set(chosen)

    ttk.Button(frame, text="Browse...", command=choose_folder).grid(row=5, column=2, padx=(8, 0), pady=(2, 12))

    download_button = ttk.Button(frame, text="Download")
    download_button.grid(row=6, column=0, sticky="w")

    progress = ttk.Progressbar(frame, length=520, mode="determinate", maximum=100)
    progress.grid(row=7, column=0, columnspan=3, sticky="we", pady=(14, 4))
    ttk.Label(frame, textvariable=status_var, wraplength=520).grid(row=8, column=0, columnspan=3, sticky="w")

    ttk.Label(
        frame,
        text="Only download content you own, have permission for, or that is licensed for it.",
        foreground="#666666", wraplength=520,
    ).grid(row=9, column=0, columnspan=3, sticky="w", pady=(14, 0))

    def update_quality_state(*_):
        quality_box.configure(state="readonly" if mode_var.get() == "video" else "disabled")

    mode_var.trace_add("write", update_quality_state)
    update_quality_state()

    def worker(url, mode, folder, quality):
        try:
            path = download(
                url, mode, folder, quality,
                on_progress=lambda p: messages.put(("progress", p)),
                on_status=lambda s: messages.put(("status", s)),
            )
            messages.put(("done", path))
        except Exception as error:  # show any problem in the window
            messages.put(("error", str(error)))

    def start_download():
        if not url_var.get().strip():
            messagebox.showinfo("Missing link", "Please paste a video link first.")
            return
        download_button.configure(state="disabled")
        progress["value"] = 0
        status_var.set("Starting...")
        threading.Thread(
            target=worker,
            args=(url_var.get(), mode_var.get(), folder_var.get(), quality_var.get()),
            daemon=True,
        ).start()

    download_button.configure(command=start_download)

    def check_messages():
        # The window is only updated from here, cuz the download runs in another thread
        try:
            while True:
                kind, value = messages.get_nowait()
                if kind == "progress":
                    progress["value"] = value
                    status_var.set(f"Downloading... {value:.0f}%")
                elif kind == "status":
                    status_var.set(value)
                elif kind == "done":
                    progress["value"] = 100
                    status_var.set(f"Saved: {value}")
                    download_button.configure(state="normal")
                elif kind == "error":
                    progress["value"] = 0
                    status_var.set(f"Could not download: {value}")
                    download_button.configure(state="normal")
        except queue.Empty:
            pass
        root.after(100, check_messages)

    check_messages()
    url_entry.focus()
    root.mainloop()


# ---------------------------------------------------------------------------
# Command line version
# ---------------------------------------------------------------------------

def run_command_line(args):
    mode = "audio" if args.audio else "video"
    quality = f"{args.quality}p" if args.quality else "Best available"
    last = {"pct": -10}

    def show_progress(pct):
        if pct - last["pct"] >= 10:
            last["pct"] = pct
            print(f"  {pct:.0f}%")

    try:
        path = download(args.url, mode, args.out, quality, show_progress, print)
    except Exception as error:
        print(f"Could not download: {error}")
        return 1
    print(f"Saved: {path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Download a video as MP3 or MP4.")
    parser.add_argument("url", nargs="?", help="video link (leave empty to open the window)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--audio", action="store_true", help="save as MP3 (default)")
    group.add_argument("--video", action="store_true", help="save as MP4")
    parser.add_argument("--quality", type=int, help="maximum video height, for example 720")
    parser.add_argument("--out", default=str(Path.home() / "Downloads"), help="folder to save in")
    args = parser.parse_args()

    if args.url:
        if not args.audio and not args.video:
            args.audio = True
        sys.exit(run_command_line(args))
    run_window()


if __name__ == "__main__":
    main()
