"""
Cut analyzer for finished edits.

Detects every cut in an exported video and produces:
  - shot sheets: the middle frame of every shot, labelled with shot number, start time and duration
  - shots.csv: start / end / duration of every shot
  - a transcript (.srt) of the full mix (voice-over + reactions)
  - report.md: pacing stats per 30s window plus every shot with the words spoken over it

Usage (Windows):
  python cut_scan.py "D:\\Exports\\Hardolotl1.mp4"
  python cut_scan.py "D:\\Exports\\Hardolotl1.mp4" --threshold 0.25 --model medium
"""

import argparse
import csv
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from footage_scan import SAMPLE_RATE, fmt_time, load_font, probe, run, transcribe, write_srt


def detect_cuts(video, threshold):
    """Return the times (seconds) where ffmpeg's scene score exceeds the threshold."""
    result = run_stderr(["ffmpeg", "-hide_banner", "-i", str(video), "-an", "-vf",
                         f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", result)]


def run_stderr(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:])
    return result.stderr


def build_shots(cuts, duration, min_len):
    bounds = [0.0]
    for t in cuts:
        if t - bounds[-1] >= min_len:
            bounds.append(t)
    bounds.append(duration)
    return [{"n": i + 1, "start": a, "end": b, "dur": b - a} for i, (a, b) in enumerate(zip(bounds, bounds[1:]))]


def grab_frame(video, t, path):
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
         "-vf", "scale=320:-2", "-q:v", "5", str(path)])


def build_shot_sheets(video, shots, sheets_dir, cols=6, rows=5):
    sheets_dir.mkdir(parents=True, exist_ok=True)
    font = load_font(18)
    per_sheet = cols * rows
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(0, len(shots), per_sheet):
            chunk = shots[i:i + per_sheet]
            images = []
            for shot in chunk:
                path = Path(tmp) / f"{shot['n']:05d}.jpg"
                grab_frame(video, shot["start"] + shot["dur"] / 2, path)
                images.append(Image.open(path) if path.exists() else None)
            w, h = next(im.size for im in images if im)
            sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
            draw = ImageDraw.Draw(sheet)
            for k, (shot, im) in enumerate(zip(chunk, images)):
                x, y = (k % cols) * w, (k // cols) * h
                if im:
                    sheet.paste(im, (x, y))
                label = f"#{shot['n']} {fmt_time(shot['start'])} {shot['dur']:.1f}s"
                draw.rectangle([x, y, x + 200, y + 24], fill=(0, 0, 0))
                draw.text((x + 5, y + 2), label, fill=(255, 230, 0), font=font)
            sheet.save(sheets_dir / f"shots_{i // per_sheet + 1:03d}.jpg", quality=80)


def main():
    parser = argparse.ArgumentParser(description="Detect every cut in a finished edit and report its pacing.")
    parser.add_argument("video")
    parser.add_argument("--out", help="Output folder (default: <video name>_cuts next to the video)")
    parser.add_argument("--threshold", type=float, default=0.3, help="Scene-change sensitivity, lower = more cuts (0.2-0.4)")
    parser.add_argument("--min-shot", type=float, default=0.15, help="Ignore cuts closer than this many seconds")
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--language", default="ar")
    parser.add_argument("--no-transcript", action="store_true")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. Install with:  winget install Gyan.FFmpeg")

    video = Path(args.video)
    out = Path(args.out) if args.out else video.with_name(video.stem + "_cuts")
    out.mkdir(parents=True, exist_ok=True)
    duration, _ = probe(video)

    print("Detecting cuts ...")
    shots = build_shots(detect_cuts(video, args.threshold), duration, args.min_shot)
    print(f"  {len(shots)} shots")

    print("Building shot sheets ...")
    build_shot_sheets(video, shots, out / "sheets")

    segments = []
    if not args.no_transcript:
        from faster_whisper import WhisperModel
        print("Transcribing ...")
        wav = out / "mix.wav"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-ac", "1", "-ar", str(SAMPLE_RATE), str(wav)])
        segments = transcribe(WhisperModel(args.model, device=args.device), wav, args.language)
        write_srt(segments, out / f"{video.stem}.srt")
        wav.unlink(missing_ok=True)

    with open(out / "shots.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["shot", "start", "end", "duration_s", "words"])
        for s in shots:
            s["words"] = " ".join(seg["text"] for seg in segments if seg["end"] > s["start"] and seg["start"] < s["end"])
            writer.writerow([s["n"], f"{s['start']:.2f}", f"{s['end']:.2f}", f"{s['dur']:.2f}", s["words"]])

    durs = np.array([s["dur"] for s in shots])
    report = [
        f"# Cut analysis: {video.name}\n",
        f"- length: {fmt_time(duration)}",
        f"- shots: {len(shots)}  |  cuts per minute: {len(shots) / (duration / 60):.1f}",
        f"- shot length: avg {durs.mean():.2f}s, median {np.median(durs):.2f}s, "
        f"shortest {durs.min():.2f}s, longest {durs.max():.2f}s",
        f"- shots under 1s: {(durs < 1).sum()}  |  1-3s: {((durs >= 1) & (durs < 3)).sum()}  |  "
        f"3s+: {(durs >= 3).sum()}\n",
        "## Pacing per 30 seconds\n",
        "| window | shots | avg shot |",
        "|---|---|---|",
    ]
    for w in range(0, int(duration), 30):
        in_win = [s for s in shots if w <= s["start"] < w + 30]
        if in_win:
            report.append(f"| {fmt_time(w)} | {len(in_win)} | {np.mean([s['dur'] for s in in_win]):.2f}s |")
    report.append("\n## Every shot\n")
    for s in shots:
        report.append(f"- #{s['n']} **{fmt_time(s['start'])}** {s['dur']:.2f}s  {s['words']}")
    (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nDone. Results in {out}")


if __name__ == "__main__":
    main()
