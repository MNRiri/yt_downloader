# Link to Audio or Video

A small Python app that downloads a video from a link and saves it as an **MP3** (audio only, good for listening to music) or an **MP4** (the video itself). It has a simple window, and it can also run from the command line.

## Setup (one time)

```bash
pip install yt-dlp imageio-ffmpeg
```

You need Python 3 installed. On Windows, tick "Add Python to PATH" during the Python setup.

## Run the window version

```bash
python yt_downloader.py
```

Paste a link, choose **Audio only (MP3)** or **Video (MP4)**, pick a folder, and click Download.

## Run from the command line instead

```bash
python yt_downloader.py "LINK" --audio
python yt_downloader.py "LINK" --video
```

Other options: `--quality 720` sets the maximum video height, and `--out "FOLDER"` sets where the file is saved. If you give a link without `--audio` or `--video`, it saves an MP3. The default folder is your Downloads folder.

## What it does

- Downloads one video at a time. It never downloads a whole playlist by accident.
- Audio is saved as MP3 at 192 kbps.
- Video is saved as MP4, and you can limit the quality (for example 720p) to keep files smaller.
- The window keeps working while a download runs, and shows a progress bar.
- Shows a short, readable message if something goes wrong, such as a bad link.

## How it works

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) does the downloading.
- [ffmpeg](https://ffmpeg.org/) converts the file. It comes bundled through the `imageio-ffmpeg` package, so you do not need to install it yourself.
- The window is built with Tkinter, and the download runs in a separate thread so the window does not freeze.

## Troubleshooting

- **Downloads suddenly stop working:** sites change often, so update the downloader with `pip install -U yt-dlp`.
- **"ffmpeg was not found":** run `pip install imageio-ffmpeg`.
- **"No module named tkinter" on Linux:** install it with your package manager, for example `sudo apt install python3-tk`.

## About

Made as a personal learning project to practice working with external libraries, threads, and a simple desktop interface in Python.