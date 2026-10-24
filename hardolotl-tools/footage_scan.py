"""
Footage scanner for long Minecraft recordings.

For every video in a folder it produces:
  - contact sheets (one frame every N seconds, timestamped) so the footage can be reviewed at a glance
  - a transcript (.srt) of the mic track, using faster-whisper
  - a list of "loud moments" on the mic track (laughs, screams, reactions) with the words said around them
  - report.md that ties everything together, per file

Usage (Windows, from a terminal):
  python footage_scan.py --probe "D:\\Footage\\Hardolotl3"
  python footage_scan.py "D:\\Footage\\Hardolotl3" --out "D:\\Footage\\scan" --mic-track 1
"""

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".flv", ".ts"}
SAMPLE_RATE = 16000


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(map(str, cmd))}\n{result.stderr[-2000:]}")
    return result.stdout


def fmt_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def srt_time(seconds):
    ms = int(round(seconds * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


def probe(video):
    data = json.loads(run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,codec_name,channels",
        "-of", "json", str(video),
    ]))
    duration = float(data["format"]["duration"])
    audio = [s for s in data["streams"] if s["codec_type"] == "audio"]
    return duration, audio


def list_videos(folder):
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in VIDEO_EXTS)


def probe_mode(folder, out):
    """Print audio tracks and export a 20s sample of each so the mic track can be identified by ear."""
    videos = list_videos(folder)
    if not videos:
        sys.exit(f"No videos found in {folder}")
    video = videos[0]
    duration, audio = probe(video)
    out.mkdir(parents=True, exist_ok=True)
    start = min(600, duration / 3)
    print(f"\n{video.name}  ({fmt_time(duration)})")
    for i, stream in enumerate(audio):
        sample = out / f"track_{i}_sample.wav"
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-t", "20", "-i", str(video),
             "-map", f"0:a:{i}", str(sample)])
        print(f"  audio track {i}: {stream.get('codec_name')}, {stream.get('channels')}ch  -> {sample}")
    print("\nListen to the samples. The one with only your voice is the --mic-track number.")


def extract_frames(video, frames_dir, interval):
    frames_dir.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", f"fps=1/{interval},scale=320:-2",
         "-q:v", "5", str(frames_dir / "f_%05d.jpg")])
    return sorted(frames_dir.glob("f_*.jpg"))


def load_font(size):
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_contact_sheets(frames, interval, sheets_dir, stem, cols=6, rows=5):
    sheets_dir.mkdir(parents=True, exist_ok=True)
    font = load_font(22)
    per_sheet = cols * rows
    sheets = []
    for sheet_idx in range(math.ceil(len(frames) / per_sheet)):
        chunk = frames[sheet_idx * per_sheet:(sheet_idx + 1) * per_sheet]
        first = Image.open(chunk[0])
        w, h = first.size
        sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
        draw = ImageDraw.Draw(sheet)
        for k, frame_path in enumerate(chunk):
            x, y = (k % cols) * w, (k // cols) * h
            sheet.paste(Image.open(frame_path), (x, y))
            # fps=1/N samples the middle of each N-second window
            t = (sheet_idx * per_sheet + k) * interval + interval / 2
            label = fmt_time(t)
            draw.rectangle([x, y, x + 110, y + 28], fill=(0, 0, 0))
            draw.text((x + 6, y + 2), label, fill=(255, 230, 0), font=font)
        start_t = sheet_idx * per_sheet * interval
        path = sheets_dir / f"{stem}_{sheet_idx + 1:03d}_{fmt_time(start_t).replace(':', '-')}.jpg"
        sheet.save(path, quality=80)
        sheets.append(path)
    return sheets


def extract_mic(video, mic_track, wav_path):
    run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-map", f"0:a:{mic_track}",
         "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(wav_path)])


def loud_moments(wav_path, sensitivity):
    with wave.open(str(wav_path), "rb") as wf:
        samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    n_sec = len(samples) // SAMPLE_RATE
    if n_sec == 0:
        return []
    rms = np.sqrt(np.mean(samples[:n_sec * SAMPLE_RATE].reshape(n_sec, SAMPLE_RATE) ** 2, axis=1))
    db = 20 * np.log10(rms + 1e-9)
    # Seconds where the mic is clearly louder than its usual speaking level
    voiced = db[db > -45]
    if len(voiced) == 0:
        return []
    threshold = max(np.percentile(voiced, 100 - sensitivity), -30)
    hot = np.where(db > threshold)[0]
    events = []
    for sec in hot:
        if events and sec - events[-1]["end"] <= 3:
            events[-1]["end"] = int(sec)
            events[-1]["peak_db"] = max(events[-1]["peak_db"], float(db[sec]))
        else:
            events.append({"start": int(sec), "end": int(sec), "peak_db": float(db[sec])})
    return events


def transcribe(model, wav_path, language):
    segments, _ = model.transcribe(str(wav_path), language=language, vad_filter=True, beam_size=5)
    return [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]


def write_srt(segments, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segments, 1):
            f.write(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n\n")


def words_near(segments, start, end, pad=6):
    return " ".join(s["text"] for s in segments if s["end"] >= start - pad and s["start"] <= end + pad)


def main():
    parser = argparse.ArgumentParser(description="Scan long gameplay footage into contact sheets, transcripts and loud moments.")
    parser.add_argument("folder", help="Folder with the video files")
    parser.add_argument("--out", help="Output folder (default: <folder>/scan)")
    parser.add_argument("--probe", action="store_true", help="Only list audio tracks and export samples to find the mic track")
    parser.add_argument("--mic-track", type=int, default=1, help="Audio track index that holds only your mic (see --probe)")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between contact-sheet frames")
    parser.add_argument("--model", default="large-v3", help="faster-whisper model: large-v3 (GPU), medium, small (CPU)")
    parser.add_argument("--device", default="auto", help="auto, cuda or cpu")
    parser.add_argument("--language", default="ar")
    parser.add_argument("--sensitivity", type=float, default=3.0, help="Percent of loudest voiced seconds to flag (higher = more moments)")
    parser.add_argument("--no-transcript", action="store_true", help="Skip Whisper (faster, loud moments only)")
    args = parser.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("ffmpeg/ffprobe not found. Install with:  winget install Gyan.FFmpeg  then reopen the terminal.")

    folder = Path(args.folder)
    out = Path(args.out) if args.out else folder / "scan"

    if args.probe:
        probe_mode(folder, out / "probe")
        return

    model = None
    if not args.no_transcript:
        from faster_whisper import WhisperModel
        print(f"Loading Whisper model {args.model} ...")
        model = WhisperModel(args.model, device=args.device)

    videos = list_videos(folder)
    if not videos:
        sys.exit(f"No videos found in {folder}")
    out.mkdir(parents=True, exist_ok=True)
    all_moments = []
    report = ["# Footage scan\n"]

    for n, video in enumerate(videos, 1):
        stem = video.stem
        print(f"\n[{n}/{len(videos)}] {video.name}")
        duration, audio = probe(video)
        work = out / stem
        work.mkdir(parents=True, exist_ok=True)

        print("  frames + contact sheets ...")
        frames = extract_frames(video, work / "_frames", args.interval)
        sheets = build_contact_sheets(frames, args.interval, out / "sheets", stem)
        shutil.rmtree(work / "_frames", ignore_errors=True)

        segments, events = [], []
        if args.mic_track < len(audio):
            wav_path = work / "mic.wav"
            print("  mic audio ...")
            extract_mic(video, args.mic_track, wav_path)
            events = loud_moments(wav_path, args.sensitivity)
            if model:
                print("  transcribing ...")
                segments = transcribe(model, wav_path, args.language)
                write_srt(segments, work / f"{stem}.srt")
            wav_path.unlink(missing_ok=True)
        else:
            print(f"  ! file has {len(audio)} audio tracks, mic track {args.mic_track} missing - skipped audio")

        with open(work / "moments.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["file", "start", "end", "peak_db", "words"])
            for e in events:
                e["file"] = video.name
                e["words"] = words_near(segments, e["start"], e["end"])
                writer.writerow([video.name, fmt_time(e["start"]), fmt_time(e["end"]), f"{e['peak_db']:.1f}", e["words"]])
                all_moments.append(e)

        report.append(f"\n## {video.name}  ({fmt_time(duration)})\n")
        report.append(f"- contact sheets: {len(sheets)} (one frame every {args.interval}s)")
        report.append(f"- spoken segments: {len(segments)}, loud moments: {len(events)}\n")
        for e in events:
            report.append(f"- **{fmt_time(e['start'])}** ({e['peak_db']:.0f} dB) {e['words']}")

    top = sorted(all_moments, key=lambda e: e["peak_db"], reverse=True)[:60]
    report.insert(1, "\n## Top 60 loudest reactions (all files)\n")
    for i, e in enumerate(top):
        report.insert(2 + i, f"- {e['file']} **{fmt_time(e['start'])}** ({e['peak_db']:.0f} dB) {e['words']}")
    (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nDone. Open {out / 'report.md'} and the {out / 'sheets'} folder.")


if __name__ == "__main__":
    main()
